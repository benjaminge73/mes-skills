#!/usr/bin/env python3
"""Relève les passages Markdown à relire après une branche : ceux qui citent un nom touché.

Pourquoi un script : après une modification de code, les docs qui citent
l'ancien nom (une fonction renommée, une constante changée, un fichier déplacé)
deviennent fausses sans que rien ne le signale. Relire tous les Markdown du
dépôt pour le voir coûte cher ; ce script ne sort que les lignes qui citent un
nom touché par ``git diff <base>...HEAD``.

Ce qu'il relève comme noms :
- les chemins modifiés, ajoutés ou supprimés par la branche, et les anciens
  chemins des fichiers renommés (le diff est lu sans détection de renommage :
  un renommage y est une suppression suivie d'un ajout) ;
- le nom de base d'un fichier, sauf s'il est générique (``SKILL.md``,
  ``CLAUDE.md``, ``README.md``) : ceux-là ne se cherchent que par leur chemin
  complet relatif à la racine ; à la racine du dépôt, ils n'ont aucun terme ;
- les symboles Python de premier niveau retirés (renommage compris), dont la
  signature change, et les constantes MAJUSCULES dont la valeur change. On les
  compare entre le merge-base de ``<base>`` et ``HEAD`` (``git merge-base``, le
  point de branchement) et ``HEAD:<chemin>``, par le module ``ast``. Pourquoi le
  merge-base : si la base avance après le branchement, comparer à sa pointe
  ferait ressortir ce que seule la base a changé, comme un renommage fait sur
  ``main`` que la branche n'a jamais touché.

Chaque terme se cherche dans les ``*.md`` suivis par git, avec des bornes de
mot : ``deploy.py`` ne matche pas ``test_deploy.py``. Les ``*.md`` sous un
dossier nommé ``out/`` ne sont pas lus, et il n'y a pas de drapeau pour les
relire. ``--exclure`` ajoute des globs d'exclusion, testés sur le chemin relatif
ou sur le nom de base.

Sortie : un JSON sur la sortie standard ::

    {"base": ..., "termes": [...],
     "passages": [{"fichier", "ligne", "texte", "termes", "extrait_diff",
                   "ligne_modifiee_dans_la_branche"}, ...],
     "passages_omis": N}

``texte`` : la ligne qui cite un terme, plus deux lignes avant et deux après.
``extrait_diff`` : les hunks du diff qui portent un des termes du passage,
borné à 4 000 caractères. ``ligne_modifiee_dans_la_branche`` : vrai si la ligne
figure parmi les lignes ajoutées par la branche. ``passages_omis`` : le nombre
de passages au-delà de ``--max-passages`` (défaut 200), jamais une liste tronquée
en silence. Ordre : fichier, puis ligne.

Usage : qualite-doc.py lecteurs --base <ref> [--racine .] [--exclure <glob>…]
                                [--max-passages N]
Code 0 : rapport rendu. Code 2 : erreur d'usage, de git, ou fichier Python
illisible dans la base ou dans HEAD ; le message nommé part sur la sortie d'erreur.

Sous-commande ``juger`` : pour chaque passage relevé par ``lecteurs``, ``claude``
(modèle fixé par la constante ``MODELE``) répond si le passage est encore exact
après le changement, selon ``grille-doc.md`` (à côté de ce dossier, dans
``_partage/``). Le score de faute d'un vote vaut ``confiance`` si ``exact`` est
faux, sinon ``1 - confiance`` ; on retient le plus haut des ``--votes`` (le plus
pessimiste). Un passage est douteux si son score atteint ``--seuil``. Un passage
qui ne peut être jugé n'est jamais compté exact. L'exécutable ``claude`` se
désigne par la variable ``QUALITE_DOC_CLAUDE`` (défaut : ``claude`` du PATH).

Usage : qualite-doc.py juger --entree <passages.json> [--votes N] [--seuil S]
                             [--max-cout D]
Codes de ``juger`` : 0 ok ; 2 usage ou entrée illisible ; 3 juge indisponible ;
4 plafond ``--max-cout`` atteint (le JSON partiel part sur la sortie standard, avec
``passages_non_juges``) ; 5 modèle servi autre que ``MODELE``.

Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

GENERIQUES = frozenset({"SKILL.md", "CLAUDE.md", "README.md"})
DOSSIER_IGNORE = "out"
CONTEXTE = 2
MAX_EXTRAIT = 4000
MAX_PASSAGES = 200
CONSTANTE = re.compile(r"[A-Z][A-Z0-9_]*")
ENTETE_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

# ``juger`` : le modèle vit en une seule constante, vérifiée dans ``modelUsage`` de chaque réponse.
MODELE = "claude-haiku-5-5"
# Seuil de départ : le plus haut qui signalait les 3 fautes vérifiées du jeu étiqueté lors du
# POC (prompt minimal). Avec la grille livrée, trois rejeux réels (2026-10-15) en ont signalé
# 1 à 2 sur 3 : les scores d'un même passage varient de ±0,2 d'un appel à l'autre. Recalibré
# par le plan 2 après 14 nuits de veille, sur les passages qu'il aura étiquetés.
SEUIL_DOUTE = 0.45
VOTES_DEFAUT = 2
DELAI_JUGE = 120  # secondes par appel de claude
VARIABLE_CLAUDE = "QUALITE_DOC_CLAUDE"
GRILLE = Path(__file__).resolve().parent.parent / "grille-doc.md"
CODE_OK = 0
CODE_USAGE = 2
CODE_JUGE_INDISPONIBLE = 3
CODE_PLAFOND_COUT = 4
CODE_MODELE_INATTENDU = 5


class ErreurQualite(Exception):
    """Erreur d'usage, de git ou de lecture : message nommé, code de sortie 2."""


class ErreurJuge(Exception):
    """Juge indisponible (code 3) ou modèle servi inattendu (code 5) : message nommé, pas de trace."""

    def __init__(self, message: str, code: int = CODE_JUGE_INDISPONIBLE):
        super().__init__(message)
        self.code = code


@dataclass
class Morceau:
    """Un hunk du diff : ses lignes brutes, en-tête ``@@`` compris, et les lignes ajoutées."""

    lignes: list[str]
    ajoutees: set[int] = field(default_factory=set)

    def changees(self) -> list[str]:
        return [ligne[1:] for ligne in self.lignes[1:] if ligne.startswith(("+", "-"))]


def git_brut(racine: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(racine), *args], capture_output=True)
    except OSError as e:
        raise ErreurQualite(f"git introuvable : {e}") from e


def git(racine: Path, *args: str) -> str:
    r = git_brut(racine, *args)
    if r.returncode != 0:
        detail = r.stderr.decode("utf-8", "replace").strip()
        raise ErreurQualite(f"git {' '.join(args)} a échoué (code {r.returncode}) : {detail}")
    return r.stdout.decode("utf-8", "replace")


def racine_du_depot(racine: Path) -> Path:
    if not racine.is_dir():
        raise ErreurQualite(f"racine introuvable : {racine}")
    r = git_brut(racine, "rev-parse", "--show-toplevel")
    if r.returncode != 0:
        raise ErreurQualite(f"pas un dépôt git : {racine}")
    return Path(r.stdout.decode("utf-8", "replace").strip())


def terme_borne(terme: str) -> re.Pattern:
    """Bornes de mot : pas de caractère de mot juste avant, pas de mot ni de tiret juste après."""
    return re.compile(r"(?<!\w)" + re.escape(terme) + r"(?![\w-])")


def termes_de_chemin(chemin: str) -> set[str]:
    p = PurePosixPath(chemin)
    if p.name in GENERIQUES:
        return {chemin} if len(p.parts) > 1 else set()
    return {chemin, p.name}


def morceaux(sortie: str) -> list[Morceau]:
    lignes = sortie.split("\n")
    if lignes and lignes[-1] == "":
        lignes.pop()
    rendus: list[Morceau] = []
    courant: Morceau | None = None
    nouveau = 0
    for ligne in lignes:
        m = ENTETE_HUNK.match(ligne)
        if m:
            courant = Morceau([ligne])
            rendus.append(courant)
            nouveau = int(m.group(1))
        elif courant is not None:
            courant.lignes.append(ligne)
            if ligne.startswith("+"):
                courant.ajoutees.add(nouveau)
                nouveau += 1
            elif not ligne.startswith(("-", "\\")):
                nouveau += 1
    return rendus


def version(racine: Path, ref: str, chemin: str) -> str | None:
    if git_brut(racine, "cat-file", "-e", f"{ref}:{chemin}").returncode != 0:
        return None
    return git(racine, "cat-file", "blob", f"{ref}:{chemin}")


def symboles(source: str, chemin: str, ref: str) -> dict[str, tuple[str, str]]:
    """Symboles de premier niveau : nom -> (genre, signature ou valeur)."""
    try:
        arbre = ast.parse(source, filename=f"{ref}:{chemin}")
    except SyntaxError as e:
        raise ErreurQualite(
            f"{chemin} n'est pas du Python lisible dans {ref} (ligne {e.lineno} : {e.msg})") from e
    rendus: dict[str, tuple[str, str]] = {}
    for noeud in arbre.body:
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = ast.unparse(noeud.args)
            if noeud.returns is not None:
                sig += " -> " + ast.unparse(noeud.returns)
            rendus[noeud.name] = ("def", sig)
        elif isinstance(noeud, ast.ClassDef):
            parents = [ast.unparse(b) for b in noeud.bases] + [ast.unparse(k) for k in noeud.keywords]
            rendus[noeud.name] = ("class", ", ".join(parents))
        elif isinstance(noeud, ast.Assign):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name) and CONSTANTE.fullmatch(cible.id):
                    rendus[cible.id] = ("const", ast.dump(noeud.value))
        elif (isinstance(noeud, ast.AnnAssign) and noeud.value is not None
              and isinstance(noeud.target, ast.Name) and CONSTANTE.fullmatch(noeud.target.id)):
            rendus[noeud.target.id] = ("const", ast.dump(noeud.value))
    return rendus


def termes_de_symboles(racine: Path, fusion: str, chemin: str) -> set[str]:
    """Noms de premier niveau retirés ou dont la signature (ou la valeur) change.

    ``fusion`` est le merge-base de la base et de HEAD : la version « avant » est
    lue à ce commit-là, et non à la pointe de la base, pour ne relever que ce que
    la branche a changé.
    """
    avant = version(racine, fusion, chemin)
    apres = version(racine, "HEAD", chemin)
    ancien = symboles(avant, chemin, fusion) if avant is not None else {}
    nouveau = symboles(apres, chemin, "HEAD") if apres is not None else {}
    return {nom for nom, valeur in ancien.items() if nouveau.get(nom) != valeur}


def fichiers_md(racine: Path, exclure: list[str]) -> list[str]:
    noms = git(racine, "ls-files", "-z", "--", "*.md").split("\0")
    retenus = []
    for chemin in sorted(n for n in noms if n):
        parties = PurePosixPath(chemin).parts
        if DOSSIER_IGNORE in parties[:-1]:
            continue
        if any(fnmatch.fnmatchcase(chemin, g) or fnmatch.fnmatchcase(parties[-1], g) for g in exclure):
            continue
        retenus.append(chemin)
    return retenus


def lignes_de(racine: Path, chemin: str) -> list[str]:
    try:
        texte = (racine / chemin).read_bytes().decode("utf-8", "replace")
    except OSError as e:
        raise ErreurQualite(f"fichier suivi illisible dans l'arbre : {chemin} ({e.strerror})") from e
    lignes = texte.split("\n")
    if lignes and lignes[-1] == "":
        lignes.pop()
    return lignes


def extrait_diff(diffs: dict[str, list[Morceau]], termes: list[str]) -> str:
    regs = [terme_borne(t) for t in termes]
    blocs: list[str] = []
    for chemin in sorted(diffs):
        entete = False
        for morceau in diffs[chemin]:
            cibles = [chemin, *morceau.changees()]
            if any(r.search(c) for r in regs for c in cibles):
                if not entete:
                    blocs.append(f"diff --git a/{chemin} b/{chemin}")
                    entete = True
                blocs.extend(morceau.lignes)
    texte = "\n".join(blocs)
    if len(texte) > MAX_EXTRAIT:
        marque = "\n[… extrait tronqué]"
        texte = texte[: MAX_EXTRAIT - len(marque)] + marque
    return texte


def lecteurs(base: str, racine_arg: Path, exclure: list[str], max_passages: int) -> dict:
    racine = racine_du_depot(racine_arg)
    if git_brut(racine, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}").returncode != 0:
        raise ErreurQualite(f"base introuvable dans ce dépôt : {base}")

    fusion = git(racine, "merge-base", base, "HEAD").strip()
    modifies = [c for c in git(racine, "diff", "--no-renames", "--name-only", "-z",
                               f"{base}...HEAD").split("\0") if c]
    diffs = {
        chemin: morceaux(git(racine, "--literal-pathspecs", "diff", "--no-renames", "--no-color",
                             "--no-ext-diff", "-U3", f"{base}...HEAD", "--", chemin))
        for chemin in modifies
    }

    termes: set[str] = set()
    for chemin in modifies:
        termes |= termes_de_chemin(chemin)
        if chemin.endswith(".py"):
            termes |= termes_de_symboles(racine, fusion, chemin)
    ordre = sorted(termes)
    regs = [(t, terme_borne(t)) for t in ordre]

    trouves: list[tuple[str, int, list[str], list[str], bool]] = []
    for chemin in fichiers_md(racine, exclure):
        lignes = lignes_de(racine, chemin)
        ajoutees = set().union(*(m.ajoutees for m in diffs.get(chemin, [])))
        for i, ligne in enumerate(lignes, start=1):
            hits = [t for t, r in regs if r.search(ligne)]
            if hits:
                trouves.append((chemin, i, lignes, hits, i in ajoutees))

    passages = []
    for chemin, i, lignes, hits, modifiee in trouves[:max_passages]:
        passages.append({
            "fichier": chemin,
            "ligne": i,
            "texte": "\n".join(lignes[max(0, i - 1 - CONTEXTE): i + CONTEXTE]),
            "termes": hits,
            "extrait_diff": extrait_diff(diffs, hits),
            "ligne_modifiee_dans_la_branche": modifiee,
        })
    return {
        "base": base,
        "termes": ordre,
        "passages": passages,
        "passages_omis": len(trouves) - len(passages),
    }


def lire_grille() -> str:
    try:
        return GRILLE.read_text(encoding="utf-8")
    except OSError as e:
        raise ErreurQualite(f"grille de relecture illisible : {GRILLE} ({e.strerror})") from e


def lire_entree(chemin: Path) -> list[dict]:
    """Passages de ``juger`` : le rapport de ``lecteurs`` (clé ``passages``) ou une liste nue."""
    try:
        donnee = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ErreurQualite(f"entrée illisible : {chemin} ({e})") from e
    passages = donnee.get("passages") if isinstance(donnee, dict) else donnee
    if not isinstance(passages, list) or not all(
            isinstance(p, dict) and all(k in p for k in ("fichier", "ligne", "texte")) for p in passages):
        raise ErreurQualite(f"entrée hors format : {chemin} (attendu : un rapport de lecteurs "
                            "ou une liste de passages)")
    return passages


def trouver_claude() -> str:
    valeur = os.environ.get(VARIABLE_CLAUDE)
    if valeur:
        trouve = shutil.which(valeur)
        if trouve is None:
            raise ErreurJuge(f"juge indisponible : {VARIABLE_CLAUDE} désigne {valeur}, "
                             "qui n'est pas un exécutable")
    else:
        trouve = shutil.which("claude")
        if trouve is None:
            raise ErreurJuge("juge indisponible : claude est absent du PATH")
    # Relatif, il serait résolu depuis le dossier temporaire où claude est lancé.
    return os.path.abspath(trouve)


def prompt_du_passage(grille: str, passage: dict) -> str:
    termes = ", ".join(passage.get("termes") or [])
    return (f"{grille}\n\n## Passage\n\nFichier : {passage['fichier']}, ligne {passage['ligne']}\n\n"
            f"{passage['texte']}\n\n## Termes\n\n{termes}\n\n"
            f"## Extrait du diff\n\n{passage.get('extrait_diff', '')}\n")


def appeler_juge(exe: str, prompt: str) -> tuple[str, float]:
    """Un vote : rend (texte ``result``, coût en dollars). Lancé hors du dépôt, prompt sur stdin."""
    with tempfile.TemporaryDirectory(prefix="qualite-doc-juge-") as dossier:
        try:
            r = subprocess.run(
                [exe, "-p", "--model", MODELE, "--output-format", "json", "--tools", "",
                 "--strict-mcp-config", "--setting-sources", "project", "--max-turns", "1"],
                input=prompt.encode("utf-8"), capture_output=True, cwd=dossier, timeout=DELAI_JUGE)
        except subprocess.TimeoutExpired as e:
            raise ErreurJuge(f"juge indisponible : claude n'a pas répondu en {DELAI_JUGE} s") from e
        except OSError as e:
            raise ErreurJuge(f"juge indisponible : {exe} ne se lance pas ({e.strerror})") from e
        if r.returncode != 0:
            detail = r.stderr.decode("utf-8", "replace").strip()[:500]
            raise ErreurJuge(f"juge indisponible : claude a rendu le code {r.returncode} ({detail})")
        try:
            sortie = json.loads(r.stdout.decode("utf-8", "replace"))
        except json.JSONDecodeError as e:
            raise ErreurJuge("juge indisponible : claude a rendu une sortie qui n'est pas du JSON") from e
    if not isinstance(sortie, dict):
        raise ErreurJuge("juge indisponible : réponse de claude hors format (pas un objet JSON)")
    if sortie.get("is_error"):
        raise ErreurJuge("juge indisponible : claude signale une erreur (is_error)")
    modeles = sortie.get("modelUsage")
    servis = set(modeles) if isinstance(modeles, dict) else set()
    if servis != {MODELE}:
        raise ErreurJuge(f"modèle servi inattendu : {sorted(servis) or 'aucun'} au lieu de {MODELE}",
                         CODE_MODELE_INATTENDU)
    cout = sortie.get("total_cost_usd")
    if isinstance(cout, bool) or not isinstance(cout, (int, float)):
        raise ErreurJuge("juge indisponible : réponse de claude sans coût lisible (total_cost_usd)")
    texte = sortie.get("result")
    return (texte if isinstance(texte, str) else ""), float(cout)


def premier_objet_json(texte: str) -> dict | None:
    decodeur = json.JSONDecoder()
    for i, car in enumerate(texte):
        if car != "{":
            continue
        try:
            objet, _ = decodeur.raw_decode(texte, i)
        except json.JSONDecodeError:
            continue
        if isinstance(objet, dict):
            return objet
    return None


def vote_de(texte: str) -> dict:
    """Score de faute d'un vote ; une réponse illisible compte douteuse (1,0), jamais exacte."""
    objet = premier_objet_json(texte)
    exact = objet.get("exact") if objet else None
    confiance = objet.get("confiance") if objet else None
    valide = (isinstance(exact, bool) and isinstance(confiance, (int, float))
              and not isinstance(confiance, bool) and 0 <= confiance <= 1)
    if not valide:
        return {"score": 1.0, "exact": False, "confiance": None, "raison": "réponse illisible"}
    confiance = float(confiance)
    score = confiance if not exact else 1 - confiance
    return {"score": score, "exact": exact, "confiance": confiance,
            "raison": str(objet.get("raison", ""))}


def juger(passages: list[dict], votes: int, seuil: float, max_cout: float | None) -> tuple[dict, int]:
    """Fait voter le juge sur chaque passage ; rend (rapport, code de sortie)."""
    exe = trouver_claude()
    grille = lire_grille()
    jugés: list[tuple[dict, list[dict]]] = []
    cout = 0.0
    for passage in passages:
        urnes: list[dict] = []
        for _ in range(votes):
            if max_cout is not None and cout >= max_cout:
                break  # plafond atteint : pas d'appel de plus, ce passage reste non jugé
            texte, cout_appel = appeler_juge(exe, prompt_du_passage(grille, passage))
            cout += cout_appel
            urnes.append(vote_de(texte))
        if len(urnes) < votes:
            break
        jugés.append((passage, urnes))
    non_juges = len(passages) - len(jugés)

    verdicts = []
    for passage, urnes in jugés:
        retenu = max(urnes, key=lambda v: v["score"])  # le plus haut : le plus pessimiste
        verdicts.append({
            "fichier": passage["fichier"],
            "ligne": passage["ligne"],
            "score": retenu["score"],
            "exact": retenu["exact"],
            "raison": retenu["raison"],
            "votes": [{"score": v["score"], "exact": v["exact"], "confiance": v["confiance"]}
                      for v in urnes],
        })
    douteux = [{"fichier": v["fichier"], "ligne": v["ligne"], "score": v["score"], "raison": v["raison"]}
               for v in verdicts if v["score"] >= seuil]
    rapport = {
        "modele": MODELE,
        "votes": votes,
        "seuil": seuil,
        "verdicts": verdicts,
        "douteux": douteux,
        "cout_total": cout,
        "passages_non_juges": non_juges,
    }
    return rapport, (CODE_PLAFOND_COUT if non_juges else CODE_OK)


def commande_juger(ap: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if args.votes < 1:
        ap.error("--votes doit être supérieur ou égal à 1")
    if not 0 <= args.seuil <= 1:
        ap.error("--seuil doit être compris entre 0 et 1")
    if args.max_cout is not None and args.max_cout < 0:
        ap.error("--max-cout doit être supérieur ou égal à 0")
    try:
        passages = lire_entree(args.entree)
        rapport, code = juger(passages, args.votes, args.seuil, args.max_cout)
    except ErreurJuge as e:
        print(f"qualite-doc : {e}", file=sys.stderr)
        return e.code
    except ErreurQualite as e:
        print(f"qualite-doc : {e}", file=sys.stderr)
        return CODE_USAGE
    if code == CODE_PLAFOND_COUT:
        print(f"qualite-doc : plafond --max-cout atteint, {rapport['passages_non_juges']} "
              "passage(s) non jugé(s)", file=sys.stderr)
    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    return code


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="qualite-doc.py",
                                 description="Relève les passages Markdown à relire après une branche.")
    sous = ap.add_subparsers(dest="commande", required=True, metavar="commande")
    lec = sous.add_parser("lecteurs", help="passages Markdown qui citent un nom touché par la branche")
    lec.add_argument("--base", required=True, help="réf de base de la comparaison (ex. origin/main)")
    lec.add_argument("--racine", type=Path, default=Path("."), help="dossier du dépôt (défaut : .)")
    lec.add_argument("--exclure", action="extend", nargs="+", default=[], metavar="GLOB",
                     help="glob(s) de *.md à ne pas lire (chemin relatif ou nom de base)")
    lec.add_argument("--max-passages", type=int, default=MAX_PASSAGES, metavar="N",
                     help=f"nombre maximal de passages rendus (défaut : {MAX_PASSAGES})")
    jug = sous.add_parser("juger", help="fait juger par claude si chaque passage est encore exact")
    jug.add_argument("--entree", required=True, type=Path, metavar="FICHIER",
                     help="rapport de lecteurs (JSON) ou liste nue de passages")
    jug.add_argument("--votes", type=int, default=VOTES_DEFAUT, metavar="N",
                     help=f"votes par passage (défaut : {VOTES_DEFAUT})")
    jug.add_argument("--seuil", type=float, default=SEUIL_DOUTE, metavar="S",
                     help=f"score à partir duquel un passage est douteux (défaut : {SEUIL_DOUTE})")
    jug.add_argument("--max-cout", type=float, default=None, metavar="D",
                     help="plafond de coût en dollars (défaut : illimité)")
    args = ap.parse_args(argv)
    if args.commande == "juger":
        return commande_juger(ap, args)
    if args.max_passages < 0:
        ap.error("--max-passages doit être supérieur ou égal à 0")
    try:
        rapport = lecteurs(args.base, args.racine, args.exclure, args.max_passages)
    except ErreurQualite as e:
        print(f"qualite-doc : {e}", file=sys.stderr)
        return CODE_USAGE
    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    return CODE_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
