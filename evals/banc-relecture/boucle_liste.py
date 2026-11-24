#!/usr/bin/env python3
"""Boucle d'amélioration de la liste de relecture (étape 7 du plan « Refonte des plugins par la checklist »).

Relève les lignes candidates (une remarque retenue que la chaîne a manquée, vue dans deux étapes de la même catégorie),
mesure chacune sur le jeu de validation (43 cas), et ne l'ajoute que si le rappel monte sans que le bruit dépasse celui
de l'A/A (deux relectures identiques, mesurées une fois).

Usage : boucle_liste.py --section NOM [--plafond-mois 5] [--dry-run] [--cron]
Codes : 0 rien à ajouter, une PR en cours, ou un souci signalé en ligne ; 10 une ligne ajoutée (PR ouverte) ;
        1 erreur réelle (jeu absent, git, gh ou état en échec) ; 3 plafond du mois atteint, ou budget restant sous le coût
        d'une mesure complète ; 5 bilan de Q2 pas encore passé.
--cron : sort en 0 ([SILENT] ou une ligne de message), sauf pour une erreur réelle (code 1, une ligne). Une exception
        inattendue devient une ligne et un 0 : jamais de trace Python dans le cron.

Quota du fournisseur (HTTP 402, « out of extra usage », plafond de dépense) : le texte du service passe tel quel dans
la sortie, une seule fois ; ensuite [SILENT] jusqu'au premier succès. Rien n'est compté contre le plafond.

Trois écritures, trois lieux :
  - l'état (coût par mois, dernière mesure complète, mesures faites, base, décisions sur les candidats, quota) vit dans
    `$BANC_DONNEES/etat-boucle-<section>.json`, hors du dépôt : c'est lui qui fait foi ;
  - le journal `journal-checklist.md` porte la trace de chaque décision, et la PR en emporte la copie ;
  - la PR ouverte porte la ligne, le bump de version et le journal.
Le cron tourne dans un worktree neuf d'origin/main : son journal de travail ne porte pas les entrées non mergées, d'où
l'état. Une PR ouverte n'est pas une décision définitive : au passage suivant son état est lu sur GitHub. Une seule PR
de la boucle est en vol à la fois.

Journal : une section `## NOM` par liste ou par plan, des entrées `### AAAA-MM-JJ — titre` dont les puces ont une clé
fixe (`- Ligne candidate : …`, `- Décision : …`, `- PR : …`, etc.). Ce format est l'interface que P3 réutilise
(`--section Enquête`) : ne pas le changer sans lui.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import banc

PLAFOND_MOIS = 5.0
CODE_OK, CODE_PR, CODE_ERREUR, CODE_PLAFOND, CODE_BILAN = 0, 10, 1, 3, 5
SILENCE = "[SILENT]"
ICI = Path(__file__).resolve().parent
DEPOT = ICI.parents[1]
JOURNAL = ICI / "journal-checklist.md"
JOURNAL_REL = "evals/banc-relecture/journal-checklist.md"
LISTE_REL = "plugins/plans-notion/skills/_partage/listes/relecture-code.md"
PLUGIN_JSON = "plugins/plans-notion/.claude-plugin/plugin.json"
RACINE_WORKTREES = Path.home() / "repos" / "worktrees" / "mes-skills"
AUTEUR_PR = "benjaminge73"
CAS_VALIDATION = "cas-ref-validation.json"
REF_VALIDATION = "ref-validation.json"
LETTRES = "ABCDEFGH"
POIDS = {"oui": 1.0, "partiel": 0.5, "non": 0.0}
RE_QUOTA = re.compile(r"402|out of extra usage|plafond de dépense|spending (?:cap|limit)|usage limit", re.I)

RE_BILAN = re.compile(r"^Bilan de Q2 : (\d{4}-\d{2}-\d{2})\s*$", re.M)
RE_ENTREE = re.compile(r"^### (\d{4}-\d{2}-\d{2})\b")
RE_BASE = re.compile(r"^- Mesure de base : rappel ([\d.]+) ; bruit ([\d.]+) ; liste ([0-9a-f]{64})\s*$")
RE_AA = re.compile(r"^- Bruit A/A : ([\d.]+)\s*$")
RE_CANDIDAT = re.compile(r"^- Ligne candidate : (.+?)\s*$")
RE_CATEGORIE = re.compile(r"^- Catégorie : ([A-H])\s*$")
RE_LISTE_MESUREE = re.compile(r"^- Liste mesurée : ([0-9a-f]{64})\s*$")
RE_DECISION_RETENUE = re.compile(r"^- Décision : (retenue)\s*$")
RE_DECISION_REFUSEE = re.compile(r"^- Décision : (refusée)\s*$")
RE_PR_OUVERTE = re.compile(r"^- PR : (https://\S+)\s*$")
RE_PR_ECHEC = re.compile(r"^- PR : (échec)\b")

# Statuts d'un candidat dans l'état. « en vol » : PR ouverte, pas encore mergée (pas une décision définitive).
STATUTS_TRAITES = {"refusée", "mergée", "fermée", "en vol"}
# Contrôles de PR rouges, tels que `gh pr view --json statusCheckRollup` les rend.
ROUGES = {"FAILURE", "ERROR", "TIMED_OUT", "STARTUP_FAILURE", "ACTION_REQUIRED"}


@dataclass(frozen=True)
class Mesure:
    rappel: float
    bruit: float
    cout: float


@dataclass(frozen=True)
class Candidat:
    categorie: str
    ligne: str


@dataclass(frozen=True)
class Resultat:
    code: int
    lignes: list
    silencieux: bool = False
    reelle: bool = False


class QuotaAtteint(Exception):
    pass


class Souci(RuntimeError):
    """Un échec. `reelle` : erreur d'outil ou de configuration (cron : code 1). `cout` : dépense déjà faite."""

    def __init__(self, message, *, reelle=False, cout=0.0):
        super().__init__(message)
        self.reelle = reelle
        self.cout = cout


def une_ligne(texte) -> str:
    return " ".join(str(texte).split())


# --- Journal : lecture et écriture, sans état caché -----------------------------------------------------------------

def bilan_q2(texte: str) -> str | None:
    m = RE_BILAN.search(texte)
    return m.group(1) if m else None


def lignes_section(texte: str, section: str) -> list[str] | None:
    """Les lignes de `## <section>` jusqu'à la section suivante, ou None si elle n'existe pas."""
    lignes = texte.split("\n")
    debut = next((i + 1 for i, l in enumerate(lignes) if l.startswith("## ") and l[3:].strip() == section), None)
    if debut is None:
        return None
    fin = next((j for j in range(debut, len(lignes)) if lignes[j].startswith("## ")), len(lignes))
    return lignes[debut:fin]


def dernier(lignes: list[str], regex: re.Pattern) -> tuple | None:
    """Les groupes de la dernière ligne qui correspond : la plus récente l'emporte."""
    trouve = None
    for l in lignes:
        m = regex.match(l)
        if m:
            trouve = m.groups()
    return trouve


def _blocs(texte: str):
    """Les entrées du journal (chaque `### ` ou `## ` ouvre un bloc) : une liste de lignes par entrée."""
    bloc = []
    for l in texte.split("\n"):
        if l.startswith("## ") or l.startswith("### "):
            yield bloc
            bloc = []
        bloc.append(l)
    yield bloc


def ajouter_entree(texte: str, section: str, date: str, titre: str, puces: list[str]) -> str:
    """Ajoute une entrée à la fin de sa section, avant la section suivante."""
    lignes = texte.split("\n")
    debut = next((i for i, l in enumerate(lignes) if l.startswith("## ") and l[3:].strip() == section), None)
    if debut is None:
        raise Souci(f"section « {section} » absente du journal", reelle=True)
    fin = next((j for j in range(debut + 1, len(lignes)) if lignes[j].startswith("## ")), len(lignes))
    k = fin
    while k > debut + 1 and not lignes[k - 1].strip():
        k -= 1
    lignes[k:k] = ["", f"### {date} — {titre}", *puces]
    return "\n".join(lignes)


def inserer_ligne(liste: str, categorie: str, ligne: str) -> str:
    """Ajoute une ligne numérotée à la fin de la catégorie (lettre A à H) de la liste de relecture."""
    lignes = liste.split("\n")
    debut = next((i for i, l in enumerate(lignes) if l.startswith(f"{categorie}. ")), None)
    if debut is None:
        raise Souci(f"catégorie {categorie} absente de la liste de relecture")
    fin = len(lignes)
    for j in range(debut + 1, len(lignes)):
        if re.match(r"[A-Z]\. ", lignes[j]) or lignes[j].startswith("Rends le verdict"):
            fin = j
            break
    k = fin
    while k > debut + 1 and not lignes[k - 1].strip():
        k -= 1
    n = sum(1 for l in lignes[debut:k] if re.match(r"\s+\d+\. ", l)) + 1
    lignes[k:k] = [f"   {n}. {ligne}"]
    return "\n".join(lignes)


def mesure_depuis_jugement(jugement: dict, ref: dict, cout: float) -> Mesure:
    """Rappel pondéré (oui 1, partiel 0,5, non 0) et bruit moyen par relecture, à partir du jugement de juge.py."""
    num = den = 0.0
    bruit = 0
    for cas, items in ref.items():
        j = jugement.get(cas)
        if j is None or "erreur" in j or "ref" not in j:
            raise Souci(f"juge sans jugement pour le cas {cas}")
        matchs = {x["n"]: x["match"] for x in j["ref"]}
        den += len(items)
        num += sum(POIDS.get(matchs.get(o["n"], "non"), 0.0) for o in items)
        bruit += sum(1 for e in j.get("extras", []) if e.get("verdict") != "réelle")
    n = len(ref)
    return Mesure(rappel=num / den if den else 0.0, bruit=bruit / n if n else 0.0, cout=round(cout, 4))


# --- Candidats : regroupement des remarques retenues ---------------------------------------------------------------

def normaliser(resume: str) -> str:
    """Clé de regroupement : casse, ponctuation et espaces ignorées."""
    return " ".join(re.sub(r"[^\w\s]", " ", str(resume).casefold()).split())


def regrouper(remarques: list[tuple[str, dict]]) -> list[Candidat]:
    """`remarques` : (identifiant de l'étape, remarque). Une catégorie vue dans deux étapes distinctes, quel que soit le
    libellé de ses remarques, donne un candidat : la ligne est le résumé qui revient dans le plus d'étapes (à égalité, le
    premier vu). Une étape compte une fois. Sans catégorie valide, le regroupement se fait sur le résumé normalisé, et le
    candidat a `categorie` vide : il n'a pas de lettre où s'insérer, donc il n'est jamais mesuré."""
    par_cat: dict[str, dict] = {}
    sans_cat: dict[str, list] = {}
    for etape, r in remarques:
        resume = une_ligne(r.get("resume", ""))
        if r.get("origine") != "opus" or not resume:
            continue
        cat = r.get("categorie")
        norm = normaliser(resume)
        if cat in list(LETTRES):
            g = par_cat.setdefault(cat, {"etapes": set(), "resumes": {}})
            g["etapes"].add(etape)
            g["resumes"].setdefault(norm, [set(), resume])[0].add(etape)
        else:
            sans_cat.setdefault(norm, [set(), resume])[0].add(etape)
    sortie = []
    for cat, g in par_cat.items():
        if len(g["etapes"]) >= 2:
            _, resume = max(g["resumes"].values(), key=lambda v: len(v[0]))
            sortie.append(Candidat(categorie=cat, ligne=resume[:200]))
    for etapes, resume in sans_cat.values():
        if len(etapes) >= 2:
            sortie.append(Candidat(categorie="", ligne=resume[:200]))
    return sortie


# --- État des candidats et des PR ---------------------------------------------------------------------------------

def definir_candidat(etat: dict, ligne: str, **champs) -> dict:
    candidats = dict(etat.get("candidats") or {})
    candidats[ligne] = {**candidats.get(ligne, {}), **champs}
    return {**etat, "candidats": candidats}


def en_vol(etat: dict) -> list[tuple[str, dict]]:
    return [(l, r) for l, r in (etat.get("candidats") or {}).items() if r.get("statut") == "en vol"]


def retenues_en_attente(etat: dict, sha: str) -> list[tuple[str, dict]]:
    """Les lignes retenues dont la PR a échoué, mesurées sur cette liste : à réessayer sans remesure."""
    return [(l, r) for l, r in (etat.get("candidats") or {}).items()
            if r.get("statut") == "retenue" and r.get("liste") == sha and r.get("categorie") in list(LETTRES)]


def traites(etat: dict) -> set[str]:
    """Les lignes qu'on ne remesure pas : refusées, mergées, fermées, ou PR encore ouverte."""
    return {l for l, r in (etat.get("candidats") or {}).items() if r.get("statut") in STATUTS_TRAITES}


def importer_journal(sec: list[str] | None, etat: dict) -> dict:
    """Les décisions du journal que l'état ne porte pas encore : refusée, PR ouverte, PR en échec. L'état fait foi : une
    ligne déjà dans l'état n'est jamais réécrite par le journal. La dernière entrée du journal l'emporte sur les autres."""
    if not sec:
        return etat
    importes: dict[str, dict] = {}
    for bloc in _blocs("\n".join(sec)):
        ligne = dernier(bloc, RE_CANDIDAT)
        if not ligne or ligne[0] == "aucune":
            continue
        champs = {}
        cat, liste = dernier(bloc, RE_CATEGORIE), dernier(bloc, RE_LISTE_MESUREE)
        if cat:
            champs["categorie"] = cat[0]
        if liste:
            champs["liste"] = liste[0]
        pr = dernier(bloc, RE_PR_OUVERTE)
        if dernier(bloc, RE_DECISION_REFUSEE):
            importes[ligne[0]] = {**champs, "statut": "refusée"}
        elif pr:
            importes[ligne[0]] = {**champs, "statut": "en vol", "pr": pr[0]}
        elif dernier(bloc, RE_PR_ECHEC) and dernier(bloc, RE_DECISION_RETENUE):
            importes[ligne[0]] = {**champs, "statut": "retenue"}
    candidats = dict(etat.get("candidats") or {})
    for ligne, rec in importes.items():
        candidats.setdefault(ligne, rec)
    return {**etat, "candidats": candidats}


def classer_pr(d: dict) -> str:
    """L'état d'une PR tel que `gh pr view --json state,statusCheckRollup` le rend : mergée, fermée, rouge, ouverte."""
    etat = str(d.get("state") or "").upper()
    if etat == "MERGED":
        return "mergée"
    if etat == "CLOSED":
        return "fermée"
    if etat != "OPEN":
        raise Souci(f"état de PR inconnu : {etat!r}", reelle=True)
    valeurs = [str(c.get("conclusion") or c.get("state") or "").upper()
               for c in (d.get("statusCheckRollup") or []) if isinstance(c, dict)]
    return "rouge" if any(v in ROUGES for v in valeurs) else "ouverte"


def chemin_interdit(chemin: Path, depot: Path) -> bool:
    """Un worktree de PR ne peut ni égaler le dépôt de lancement, ni le contenir, ni être dedans : `_retirer` effacerait
    ce qui s'y trouve."""
    c, d = Path(chemin).resolve(), Path(depot).resolve()
    return c == d or c in d.parents or d in c.parents


def base_connue(etat: dict, sec: list[str] | None, sha: str):
    """La base (rappel, bruit, bruit A/A) de cette liste : dans l'état, sinon dans le journal. None si pas encore mesurée."""
    b = etat.get("base") or {}
    if b.get("liste") == sha and b.get("bruit_aa") is not None:
        return float(b["rappel"]), float(b["bruit"]), float(b["bruit_aa"])
    if not sec:
        return None
    base = None
    for l in sec:
        g = dernier([l], RE_BASE)
        if g and g[2] == sha:
            base = (float(g[0]), float(g[1]))
    aa = dernier(sec, RE_AA)
    if base is None or aa is None:
        return None
    return base[0], base[1], float(aa[0])


# --- Coût, mesures, état --------------------------------------------------------------------------------------------

def cout_du_mois(etats: list[dict], mois: str) -> float:
    """Le coût cumulé du mois (AAAA-MM), toutes sections confondues."""
    return sum(float((e.get("couts") or {}).get(mois, 0.0)) for e in etats)


def ajouter_cout(etat: dict, mois: str, cout: float) -> dict:
    couts = dict(etat.get("couts") or {})
    couts[mois] = round(float(couts.get(mois, 0.0)) + cout, 4)
    return {**etat, "couts": couts}


def enregistrer_mesure(etat: dict, bras: str, m: Mesure, mois: str) -> dict:
    """Une mesure complète (bras et juge) : son coût, son résultat (pour ne jamais la repayer), et la dernière dépense
    connue d'une mesure, qui sert de seuil au budget du passage suivant."""
    mesures = {**(etat.get("mesures") or {}), bras: {"rappel": m.rappel, "bruit": m.bruit, "cout": m.cout}}
    etat = ajouter_cout(etat, mois, m.cout)
    etat = {**etat, "mesures": mesures, "cout_mesure": m.cout}
    if etat.get("quota") == "signalé":
        etat = {**etat, "quota": "levé"}
    return etat


# --- Ce qu'on écrit dans la PR -----------------------------------------------------------------------------------

def bump_patch(texte: str) -> str:
    """La version de plugin.json, patch + 1. Sans bump, `plugin update` répond « déjà à jour » (règle de mes-skills)."""
    d = json.loads(texte)
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(d.get("version", "")))
    if not m:
        raise Souci(f"version illisible dans plugin.json : {d.get('version')!r}")
    d["version"] = f"{m[1]}.{m[2]}.{int(m[3]) + 1}"
    return json.dumps(d, indent=2, ensure_ascii=False) + "\n"


def titre_pr(c: Candidat) -> str:
    return f"chore(banc-relecture): ligne {c.categorie} ajoutée à la liste de relecture"


def message_commit(c: Candidat, iso: str) -> str:
    return (f"{titre_pr(c)}\n\nMesurée par boucle_liste.py ({iso}) sur le jeu de validation : {c.ligne}\n\n"
            "Eval-cas: aucun — ligne mesurée par le banc\n")


def corps_pr(c: Candidat, iso: str) -> str:
    return "\n".join([
        "Doc : sans objet — ligne de la liste de relecture ajoutée par la boucle mesurée, aucun effet visible",
        "Evals: revue-hors-plan — la liste de relecture de code",
        "",
        f"Ajoutée le {iso} par boucle_liste.py, catégorie {c.categorie} : {c.ligne}",
        "Mesurée sur le jeu de validation (43 cas) : rappel monté, bruit sous celui de l'A/A. Se défait par un revert.",
        "",
    ])


# --- Dépendances réelles (non jouées par les tests) -----------------------------------------------------------------

def _lancer(argv, cwd=None, env=None):
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)


def _sha8(texte: str) -> str:
    return hashlib.sha256(texte.encode()).hexdigest()[:8]


def _erreur_de(d: dict):
    e = d.get("erreur") or (d.get("result") if d.get("is_error") else None)
    return str(e) if e else None


def _cout_de(d: dict) -> float:
    try:
        return float(d.get("total_cost_usd") or 0)
    except (TypeError, ValueError):
        return 0.0


class Dependances:
    """Le journal, l'état et les PR passent par des fichiers et git ; les mesures par le banc. `sh` est remplaçable."""

    def __init__(self, journal: Path = JOURNAL, sh=None, racine: Path = RACINE_WORKTREES):
        self.journal = journal
        self.sh = sh or _lancer
        self.racine = racine
        self._liste = None

    def lire_journal(self) -> str:
        return self.journal.read_text()

    def ecrire_journal(self, texte: str) -> None:
        self.journal.write_text(texte)

    def etat_chemin(self, section: str) -> Path:
        return banc.DONNEES / f"etat-boucle-{section.casefold().replace(' ', '-')}.json"

    def lire_etat(self, section: str) -> dict:
        return _lire_etat_fichier(self.etat_chemin(section))

    def ecrire_etat(self, section: str, etat: dict) -> None:
        f = self.etat_chemin(section)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(etat, ensure_ascii=False, indent=2))

    def etats_tous(self) -> list[dict]:
        return [_lire_etat_fichier(f) for f in sorted(banc.DONNEES.glob("etat-boucle-*.json"))]

    def jeu_present(self) -> bool:
        return (banc.DONNEES / REF_VALIDATION).is_file() and (banc.DONNEES / CAS_VALIDATION).is_file()

    def liste_texte(self) -> str:
        """La liste telle qu'elle est sur origin/main : c'est elle que la boucle mesure et amende."""
        if self._liste is None:
            f = self.sh(["git", "-C", str(DEPOT), "fetch", "--quiet", "origin", "main"], None, None)
            if f.returncode != 0:
                raise Souci(f"fetch de origin/main en échec : {une_ligne(f.stderr)[-200:]}", reelle=True)
            r = self.sh(["git", "-C", str(DEPOT), "show", f"origin/main:{LISTE_REL}"], None, None)
            if r.returncode != 0:
                raise Souci(f"liste de relecture illisible sur origin/main : {une_ligne(r.stderr)[-200:]}", reelle=True)
            self._liste = r.stdout
        return self._liste

    def liste_sha(self) -> str:
        return hashlib.sha256(self.liste_texte().encode()).hexdigest()

    def liste_avec(self, candidat: Candidat) -> str:
        return inserer_ligne(self.liste_texte(), candidat.categorie, candidat.ligne)

    def mesurer(self, liste: str, bras: str, budget: float) -> Mesure:
        """Une relecture Haiku high sur les 43 cas, puis le juge. Coûte de l'argent : le cron seul l'appelle.

        Le dossier de sorties du bras est vidé d'abord : rejouer.py ne rejoue pas les cas déjà présents, donc un bras
        réutilisé compterait des rapports d'une autre liste, et un coût déjà compté. Une erreur porte la dépense faite.
        Des sorties incomplètes (le budget a coupé le rejeu) s'arrêtent avant le juge, coût journalisé."""
        dossier = banc.DONNEES / "listes-boucle"
        dossier.mkdir(parents=True, exist_ok=True)
        fichier = dossier / f"{bras}.md"
        fichier.write_text(liste)
        sorties_dir = banc.DONNEES / "sorties" / bras
        shutil.rmtree(sorties_dir, ignore_errors=True)
        r = self.sh([sys.executable, str(banc.ICI / "rejouer.py"), bras, "claude-haiku-5-5", "high",
                     f"{budget:.2f}", "--cas", CAS_VALIDATION, "--liste", str(fichier)], banc.ICI, None)
        sorties, illisibles = {}, []
        for f in sorted(sorties_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text())
            except (OSError, ValueError):
                illisibles.append(f.name)
                continue
            if isinstance(d, dict):
                sorties[f.stem] = d
            else:
                illisibles.append(f.name)
        cout = sum(_cout_de(d) for d in sorties.values())
        for d in sorties.values():
            erreur = _erreur_de(d)
            if erreur and RE_QUOTA.search(erreur):
                raise QuotaAtteint(erreur[:300])
        if illisibles:
            raise Souci(f"sortie illisible pour {bras} : {', '.join(illisibles)[:200]}", cout=cout)
        en_erreur = sorted(k for k, d in sorties.items() if _erreur_de(d))
        if en_erreur:
            raise Souci(f"cas en erreur pour {bras} : {', '.join(en_erreur)[:200]}", cout=cout)
        if r.returncode != 0 or not sorties:
            raise Souci(f"rejouer.py en échec pour {bras} : {une_ligne(r.stderr or r.stdout)[-300:]}", cout=cout)
        attendus = len(banc.charger(CAS_VALIDATION))
        if len(sorties) < attendus:
            raise Souci(f"sorties incomplètes pour {bras} : {len(sorties)} sur {attendus}, juge non appelé", cout=cout)
        j = self.sh([sys.executable, str(banc.ICI / "juge.py"), f"{bras}.json", bras, "--ref", REF_VALIDATION],
                    banc.ICI, None)
        m = re.search(r"coût juge ([\d.]+)", j.stdout or "")
        cout += float(m.group(1)) if m else 0.0
        if j.returncode != 0:
            raise Souci(f"juge.py en échec pour {bras} : {une_ligne(j.stderr or j.stdout)[-300:]}", cout=cout)
        try:
            return mesure_depuis_jugement(banc.charger(f"jugements/{bras}.json"), banc.charger(REF_VALIDATION), cout)
        except Souci as s:
            s.cout = cout
            raise
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise Souci(f"jugement illisible pour {bras} : {une_ligne(e)}", cout=cout)

    def candidats(self) -> list[Candidat]:
        """Remarques retenues par Opus seul (la chaîne les a manquées), regroupées par catégorie (voir regrouper)."""
        remarques = []
        for f in sorted((banc.DONNEES / "ombres").glob("retenues-*.json")):
            d = json.loads(f.read_text())
            for r in d.get("remarques", []):
                remarques.append((d.get("id", f.name), r))
        return regrouper(remarques)

    def etat_pr(self, url: str) -> dict:
        """L'état d'une PR de la boucle, lu sur GitHub. Aucune écriture."""
        r = self.sh(["gh", "pr", "view", url, "--json", "state,statusCheckRollup"], None, None)
        if r.returncode != 0:
            raise Souci(f"gh pr view en échec : {une_ligne(r.stderr or r.stdout)[-200:]}", reelle=True)
        try:
            d = json.loads(r.stdout)
        except ValueError:
            raise Souci("gh pr view : réponse illisible", reelle=True)
        if not isinstance(d, dict):
            raise Souci("gh pr view : réponse qui n'est pas un objet", reelle=True)
        return d

    def _run(self, argv, quoi, cwd=None, env=None, reelle=False):
        r = self.sh(argv, cwd, env)
        if r.returncode != 0:
            raise Souci(f"{quoi} en échec : {une_ligne((r.stderr or '') or (r.stdout or ''))[-200:]}", reelle=reelle)
        return r

    def _retirer(self, chemin: Path) -> None:
        try:
            if chemin.exists():
                self.sh(["git", "-C", str(DEPOT), "worktree", "remove", "--force", str(chemin)], None, None)
            if chemin.exists():
                shutil.rmtree(chemin, ignore_errors=True)
            self.sh(["git", "-C", str(DEPOT), "worktree", "prune"], None, None)
        except OSError:
            pass

    def ouvrir_pr(self, candidat: Candidat, iso: str) -> str:
        """Une PR prête qui ajoute la ligne, dans son propre worktree depuis origin/main, retiré à la fin.

        Ordre : garde du chemin, worktree, ligne, bump, copie du journal, garde Doc et sélection des évals (en local,
        comme la CI), commit, garde de veille (en local, comme la CI), puis push, `gh pr create` (sans --draft : la CI
        merge au vert). Une garde qui refuse arrête avant push."""
        chemin = self.racine / f"boucle-liste-pr-{iso}"
        if chemin_interdit(chemin, DEPOT):
            raise Souci(f"worktree de PR refusé : {chemin} recouvre le dépôt de lancement ; rien n'est effacé",
                        reelle=True)
        branche = f"chore/boucle-liste-{iso}"
        git = ["git", "-C", str(DEPOT)]
        try:
            self._run(git + ["fetch", "--quiet", "origin", "main"], "fetch de origin/main", reelle=True)
            self._retirer(chemin)
            self.sh(git + ["branch", "-D", branche], None, None)  # reste d'un passage antérieur, s'il y en a
            self._run(git + ["worktree", "add", "-b", branche, str(chemin), "origin/main"],
                      "création du worktree", reelle=True)
            liste = chemin / LISTE_REL
            liste.write_text(inserer_ligne(liste.read_text(), candidat.categorie, candidat.ligne))
            plugin = chemin / PLUGIN_JSON
            plugin.write_text(bump_patch(plugin.read_text()))
            (chemin / JOURNAL_REL).write_text(self.journal.read_text())
            corps = corps_pr(candidat, iso)
            self._run([sys.executable, str(chemin / "scripts" / "garde_doc_pr.py")], "garde de la ligne Doc",
                      cwd=chemin, env={**os.environ, "PR_BODY": corps, "PR_AUTHOR": AUTEUR_PR})
            fichiers = chemin / "fichiers-touches.txt"
            fichiers.write_text("\n".join([LISTE_REL, PLUGIN_JSON]) + "\n")
            self._run([sys.executable, str(chemin / "scripts" / "evals_selection.py"), "--plugin", "plans-notion",
                       "--fichiers", str(fichiers), "--labels", ""], "sélection des évals", cwd=chemin,
                      env={**os.environ, "PR_BODY": corps})
            dans_wt = ["git", "-C", str(chemin)]
            self._run(dans_wt + ["add", "--", LISTE_REL, PLUGIN_JSON, JOURNAL_REL], "git add")
            self._run(dans_wt + ["commit", "-q", "-m", message_commit(candidat, iso)], "commit")
            veille = self.sh([sys.executable, str(chemin / "scripts" / "check_veille.py"), "--racine", str(chemin),
                              "--base", "origin/main", "--aujourdhui", iso], chemin, None)
            if veille.returncode == 1:
                raise Souci(f"garde de veille refusée : {une_ligne(veille.stdout or veille.stderr)[-200:]}")
            if veille.returncode != 0:
                raise Souci(f"garde de veille en panne : {une_ligne(veille.stderr or veille.stdout)[-200:]}",
                            reelle=True)
            self._run(dans_wt + ["push", "-q", "-u", "origin", branche], "push de la branche", reelle=True)
            r = self._run(["gh", "pr", "create", "--base", "main", "--head", branche, "--title", titre_pr(candidat),
                           "--body", corps], "gh pr create", cwd=chemin, reelle=True)
            lignes = (r.stdout or "").strip().splitlines()
            url = lignes[-1].strip() if lignes else ""
            if not url.startswith("https://"):
                raise Souci("gh pr create n'a pas rendu d'URL", reelle=True)
            return url
        except (OSError, ValueError) as e:
            raise Souci(f"ouverture de PR : {une_ligne(e)}", reelle=True)
        finally:
            self._retirer(chemin)


def _lire_etat_fichier(f: Path) -> dict:
    if not f.is_file():
        return {}
    try:
        d = json.loads(f.read_text())
    except (OSError, ValueError) as e:
        raise Souci(f"état illisible ({f.name}) : {une_ligne(e)}", reelle=True)
    if not isinstance(d, dict):
        raise Souci(f"état illisible ({f.name}) : pas un objet", reelle=True)
    return d


# --- Décision -------------------------------------------------------------------------------------------------------

def _plafond_atteint(cout: float, plafond: float) -> Resultat:
    return Resultat(CODE_PLAFOND, [f"plafond atteint : {cout:.2f} dollars ce mois-ci (plafond {plafond:g}) ; "
                                   "arrêt avant la mesure suivante"])


def _budget_insuffisant(reste: float, seuil: float) -> Resultat:
    return Resultat(CODE_PLAFOND, [f"budget restant {reste:.2f} dollars ce mois-ci, sous le coût d'une mesure complète "
                                   f"({seuil:.2f}) : rien n'est lancé"])


def _a_mesurer(etat: dict, deps) -> list[Candidat]:
    """Les candidats à mesurer : ni déjà traités, ni sans catégorie (pas de lettre où les insérer)."""
    deja = traites(etat)
    return [c for c in deps.candidats() if c.categorie in list(LETTRES) and c.ligne not in deja]


def executer(section, deps, aujourdhui, plafond=PLAFOND_MOIS, dry_run=False) -> Resultat:
    texte = deps.lire_journal()
    bilan = bilan_q2(texte)
    if bilan is None or bilan > aujourdhui.isoformat():
        return Resultat(CODE_BILAN, ["bilan de Q2 pas encore passé : la ligne « Bilan de Q2 : AAAA-MM-JJ » "
                                     "manque au journal"], silencieux=True)
    sec = lignes_section(texte, section)
    if sec is None:
        return Resultat(CODE_ERREUR, [f"section « {section} » absente du journal"], reelle=True)
    if not deps.jeu_present():
        return Resultat(CODE_ERREUR, ["jeu de validation absent (ref-validation.json ou "
                                      "cas-ref-validation.json dans BANC_DONNEES)"], reelle=True)
    cout = cout_du_mois(deps.etats_tous(), aujourdhui.strftime("%Y-%m"))
    if cout >= plafond:
        return _plafond_atteint(cout, plafond)
    if dry_run:
        etat = importer_journal(sec, deps.lire_etat(section))
        return Resultat(CODE_OK, [f"dry-run : aucune mesure, aucune PR ; candidats à mesurer : "
                                  f"{len(_a_mesurer(etat, deps))}"])
    try:
        return _boucle(section, deps, aujourdhui, plafond)
    except QuotaAtteint as q:
        return _quota(section, deps, aujourdhui, str(q))
    except Souci as s:
        return Resultat(CODE_ERREUR, [f"souci : {s}"], reelle=s.reelle)


def _quota(section, deps, aujourdhui, texte_service: str) -> Resultat:
    etat = deps.lire_etat(section)
    if etat.get("quota") == "signalé":
        return Resultat(CODE_ERREUR, ["quota du fournisseur toujours atteint : rien mesuré, rien compté"],
                        silencieux=True)
    deps.ecrire_etat(section, {**etat, "quota": "signalé"})
    return Resultat(CODE_ERREUR, [f"{une_ligne(texte_service)} — quota du fournisseur atteint : "
                                  "rien mesuré, rien compté contre le plafond"])


def _boucle(section, deps, aujourdhui, plafond) -> Resultat:
    iso, mois = aujourdhui.isoformat(), aujourdhui.strftime("%Y-%m")
    texte = deps.lire_journal()
    sec = lignes_section(texte, section)
    liste = deps.liste_texte()
    sha = deps.liste_sha()
    deps.ecrire_etat(section, importer_journal(sec, deps.lire_etat(section)))

    def changer_etat(fn):
        deps.ecrire_etat(section, fn(deps.lire_etat(section)))

    def ecrire(titre, puces):
        """Une entrée au journal (la PR en emporte la copie). Le coût et les mesures vont à l'état, avant."""
        deps.ecrire_journal(ajouter_entree(deps.lire_journal(), section, iso, titre, puces))

    def cout_courant():
        return cout_du_mois(deps.etats_tous(), mois)

    def arret():
        """Le plafond du mois, puis le budget restant face au coût d'une mesure complète connue (défaut prudent, en
        l'absence de mesure connue : le plafond entier, donc une mesure ne part qu'en début de mois)."""
        c = cout_courant()
        if c >= plafond:
            return _plafond_atteint(c, plafond)
        reste = plafond - c
        connu = deps.lire_etat(section).get("cout_mesure")
        seuil = float(connu) if connu is not None else plafond
        if reste < seuil:
            return _budget_insuffisant(reste, seuil)
        return None

    def en_cache(bras):
        return bras in (deps.lire_etat(section).get("mesures") or {})

    def mesurer(liste_, bras, titre):
        """Une mesure faite n'est jamais repayée : elle reste dans l'état, sous son nom de bras."""
        if en_cache(bras):
            e = deps.lire_etat(section)["mesures"][bras]
            return Mesure(rappel=float(e["rappel"]), bruit=float(e["bruit"]), cout=float(e.get("cout", 0.0)))
        try:
            m = deps.mesurer(liste_, bras, plafond - cout_courant())
        except Souci as s:
            changer_etat(lambda e: ajouter_cout(e, mois, s.cout))
            ecrire(f"{titre} en échec", [f"- Souci : {une_ligne(s)[:200]}", f"- Coût : {s.cout:.3f} dollars"])
            raise
        changer_etat(lambda e: enregistrer_mesure(e, bras, m, mois))
        return m

    def ouvrir(c):
        """Ouvre la PR d'une ligne retenue ; un échec est noté (la ligne reste réessayable) puis remonté."""
        try:
            url = deps.ouvrir_pr(c, iso)
        except Souci as s:
            changer_etat(lambda e: definir_candidat(e, c.ligne, statut="retenue", categorie=c.categorie, liste=sha))
            ecrire("PR non ouverte", [f"- Ligne candidate : {c.ligne}", f"- Catégorie : {c.categorie}",
                                      f"- Liste mesurée : {sha}", "- Décision : retenue",
                                      f"- PR : échec — {une_ligne(s)[:300]}"])
            raise
        changer_etat(lambda e: definir_candidat(e, c.ligne, statut="en vol", pr=url, categorie=c.categorie, liste=sha))
        ecrire("PR ouverte", [f"- Ligne candidate : {c.ligne}", f"- Catégorie : {c.categorie}", f"- PR : {url}"])
        return Resultat(CODE_PR, [f"ligne ajoutée à la catégorie {c.categorie} : {c.ligne} — PR {url}"])

    # 1. Les PR déjà ouvertes : leur état est lu sur GitHub. Une PR ouverte fait attendre toute la boucle.
    for ligne, rec in en_vol(deps.lire_etat(section)):
        statut = classer_pr(deps.etat_pr(rec["pr"]))
        if statut == "mergée":
            changer_etat(lambda e, l=ligne: definir_candidat(e, l, statut="mergée"))
            continue
        if statut == "ouverte":
            return Resultat(CODE_OK, [], silencieux=True)
        if statut == "rouge":
            return Resultat(CODE_OK, [f"PR en échec : {rec['pr']} (ligne « {ligne[:80]} ») : rien n'est mesuré "
                                      "ni ouvert tant qu'elle est rouge"])
        changer_etat(lambda e, l=ligne: definir_candidat(e, l, statut="fermée"))
        ecrire("PR fermée sans merge", [f"- Ligne candidate : {ligne}", f"- PR : {rec['pr']}",
                                        "- Souci : fermée sans être mergée ; la ligne ne revient pas sans décision humaine"])
        return Resultat(CODE_OK, [f"PR fermée sans merge : {rec['pr']} (ligne « {ligne[:80]} ») : décision humaine, "
                                  "rien n'est rouvert"])

    # 2. Une PR échouée sur cette liste se réessaie d'abord, sans rien remesurer.
    for ligne, rec in retenues_en_attente(deps.lire_etat(section), sha):
        return ouvrir(Candidat(categorie=rec["categorie"], ligne=ligne))

    # 3. La base : deux relectures identiques, mesurées une fois par liste ; le bruit A/A en vient.
    base = base_connue(deps.lire_etat(section), sec, sha)
    if base is None:
        s8 = _sha8(liste)

        def puces_base(m):
            return [f"- Mesure de base : rappel {m.rappel:.3f} ; bruit {m.bruit:.3f} ; liste {sha}",
                    f"- Coût : {m.cout:.3f} dollars"]

        bras1, bras2 = f"base-{s8}-1", f"base-{s8}-2"
        if (r := arret()) is not None:
            return r
        if en_cache(bras1):
            m1 = mesurer(liste, bras1, "mesure de base, bras 1")   # déjà payé : lu dans l'état, rien ne part
        else:
            m1 = mesurer(liste, bras1, "mesure de base, bras 1")
            ecrire("mesure de base, bras 1", puces_base(m1))
        if (r := arret()) is not None:
            return r
        m2 = mesurer(liste, bras2, "mesure de base, bras 2")
        aa = abs(m1.bruit - m2.bruit)
        ecrire("mesure de base, bras 2 et bruit A/A", puces_base(m2) + [f"- Bruit A/A : {aa:.3f}"])
        changer_etat(lambda e: {**e, "base": {"liste": sha, "rappel": m2.rappel, "bruit": m2.bruit, "bruit_aa": aa}})
        base = (m2.rappel, m2.bruit, aa)
    rappel_base, bruit_base, bruit_aa = base

    # 4. Les candidats, un à un : chacun contre la base, dans le budget.
    for c in _a_mesurer(deps.lire_etat(section), deps):
        if (r := arret()) is not None:
            return r
        liste_c = deps.liste_avec(c)
        m = mesurer(liste_c, f"cand-{_sha8(liste_c)}", f"candidat « {c.ligne[:60]} »")
        gain, hausse = m.rappel - rappel_base, m.bruit - bruit_base
        retenue = gain > 0 and hausse <= bruit_aa
        ecrire(f"candidat « {c.ligne[:60]} »", [
            f"- Ligne candidate : {c.ligne}", f"- Catégorie : {c.categorie}", f"- Liste mesurée : {sha}",
            f"- Mesure : rappel {m.rappel:.3f} ; bruit {m.bruit:.3f} ; gain {gain:+.3f} ; hausse de bruit {hausse:+.3f}",
            f"- Décision : {'retenue' if retenue else 'refusée'}", f"- Coût : {m.cout:.3f} dollars"])
        if not retenue:
            changer_etat(lambda e: definir_candidat(e, c.ligne, statut="refusée", categorie=c.categorie, liste=sha))
            continue
        return ouvrir(c)
    return Resultat(CODE_OK, [], silencieux=True)


def main(argv=None, *, deps=None, aujourdhui=None) -> int:
    ap = argparse.ArgumentParser(description="Boucle d'amélioration de la liste de relecture : une ligne mesurée, "
                                             "ajoutée par PR seulement si elle passe.")
    ap.add_argument("--section", required=True, help="section du journal (« Code » pour la liste de relecture)")
    ap.add_argument("--plafond-mois", type=float, default=PLAFOND_MOIS,
                    help="dépense maximale par mois, toutes sections confondues (défaut 5)")
    ap.add_argument("--dry-run", action="store_true",
                    help="vérifie bilan, jeu, plafond et quota, sans rien mesurer ni ouvrir de PR")
    ap.add_argument("--cron", action="store_true", help="sort en 0 (sauf erreur réelle, 1) : [SILENT] ou une ligne")
    a = ap.parse_args(argv)
    deps = deps if deps is not None else Dependances()
    aujourdhui = aujourdhui or datetime.date.today()
    try:
        r = executer(a.section, deps, aujourdhui, a.plafond_mois, a.dry_run)
    except Souci as s:
        r = Resultat(CODE_ERREUR, [f"souci : {s}"], reelle=s.reelle)
    except OSError as e:
        r = Resultat(CODE_ERREUR, [f"journal ou état illisible : {une_ligne(e)}"], reelle=True)
    except Exception as e:  # noqa: BLE001 : en cron, rien ne sort en trace Python
        if not a.cron:
            raise
        r = Resultat(CODE_ERREUR, [f"exception inattendue : {type(e).__name__} : {une_ligne(e)[:200]}"])
    if a.cron:
        if r.silencieux or not r.lignes:
            print(SILENCE)
        else:
            for l in r.lignes:
                print(l)
        return CODE_ERREUR if r.reelle else 0
    for l in r.lignes:
        print(l)
    return r.code


if __name__ == "__main__":
    sys.exit(main())
