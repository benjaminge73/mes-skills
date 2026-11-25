#!/usr/bin/env python3
"""Banc d'enquête : mesure ce que l'enquêteur trouve avant l'écriture d'un plan, contre les découvertes que l'exécution
du plan a faites plus tard (« trouvables au plan »). Porté du prototype `mesure.py` (POC du plan enquête-checklist) sur le
socle `banc.py`. Voir README.md, « Le banc d'enquête ».

Usage :
  enquete.py [--dry-run] [--corpus D] <bras> <plafond> [<tirage>]
      rejoue l'enquête sur les plans de `echantillon.json`. Bras : actuel (l'enquêteur du plugin), liste (la liste
      d'enquête du plugin), liste-bash (la même liste, Bash enfermé). Sorties : sorties/<bras>-<tirage>/<id>.json.
  enquete.py [--dry-run] [--corpus D] juge:<bras>[@<tirage>] <plafond>
      note les fiches d'un bras (Sonnet medium, texte seul) contre les découvertes du classement.
  enquete.py [--corpus D] releve
      relevé déterministe, sans modèle ni plafond : pour chaque découverte « trouvable au plan » du journal (étiquette
      brute, dédoublonnée au texte près), le fichier qu'elle cite est-il dans les 40 premiers voisins du relevé ?

<plafond> : dépense maximale en dollars. Positif requis, sauf avec --dry-run (qui n'appelle rien) : sinon refus, code 2.
--dry-run : imprime la commande `claude -p` de chaque plan, sans l'appeler et sans rien écrire.
--corpus : dossier du corpus. Défaut : ~/.local/share/banc-enquete/corpus (ou $BANC_ENQUETE_DONNEES/corpus). Il contient
  pages/<id>.md (une page de plan par fichier), bases.json ({id: {repo, mb, base}}), echantillon.json (la liste des ids
  rejoués) et classement.json (juge seulement). Les données ne vivent pas dans ce dépôt.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextlib
import datetime
import json
import os
import re
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

# Les données de l'enquête vivent à part de celles du banc de relecture : le socle lit BANC_DONNEES à son import.
DONNEES = Path(os.environ.get("BANC_ENQUETE_DONNEES", "~/.local/share/banc-enquete")).expanduser()
os.environ["BANC_DONNEES"] = str(DONNEES)

import banc  # noqa: E402
import rejouer  # noqa: E402  (la classe Budget : même plafond dur que rejouer.py)

ENQUETEUR = banc.DEPOT / "plugins/plans-notion/agents/enqueteur.md"
LISTE = banc.DEPOT / "plugins/plans-notion/skills/_partage/listes/enquete.md"
BRAS = {"actuel": ENQUETEUR, "liste": LISTE, "liste-bash": LISTE}
SOURCES = {"mes-skills": Path("~/repos/github/benjaminge73/mes-skills").expanduser(),
           "hermes-custom": Path("~/repos/github/benjaminge73/hermes-custom").expanduser()}
DEPOTS = DONNEES / "depots"
PAR = 5
MODELE_JUGE = "claude-sonnet-5-5"
MAX_COMMIT = 20  # commits « fourre-tout » ignorés par le co-change
TOP_VOISINS = 40
CHEMIN = re.compile(r"[\w.-]+(?:/[\w.-]+)*\.(?:py|md|json|sh|toml|ya?ml|txt|mjs|js|ts|service|timer|conf|j2|ini|cfg)")

JUGE = """Tu notes une fiche d'enquête rendue AVANT l'écriture d'un plan, contre la liste des découvertes que l'exécution
de ce plan a faites plus tard et qui étaient trouvables au moment du plan. Pour chaque découverte : la fiche contient-elle
le même fait (même objet, même conséquence ; une formulation différente compte) ? « oui », « partiel » (l'objet est nommé
mais pas la conséquence) ou « non ». Compte aussi les faits de la fiche (lignes de fait) et ceux qui sont visiblement sans
rapport avec le sujet du plan. Réponds par un seul objet JSON :
{"verdicts": {"<id>": "oui|partiel|non", ...}, "faits": <n>, "hors_sujet": <n>}

DÉCOUVERTES :
%s

FICHE :
%s
"""


# --- Le corpus -------------------------------------------------------------------------------------------------------

def corpus_de(chemin: str | None) -> Path:
    return Path(chemin).expanduser() if chemin else DONNEES / "corpus"


def compact(pid: str) -> str:
    """L'identifiant court d'une page : le nom des fichiers de sortie (même convention que `mesure.py`)."""
    return pid[:8] + pid[12:16]


def echantillon(corpus: Path) -> list[str]:
    return json.loads((corpus / "echantillon.json").read_text())


def bases(corpus: Path) -> dict:
    return json.loads((corpus / "bases.json").read_text())


# --- Le rejeu : bras et juge -----------------------------------------------------------------------------------------

def brief(md: str, bras: str) -> str:
    """Le brief de l'enquêteur : titre et « Besoins » de la page, sans le plan lui-même (il ne s'écrit pas encore)."""
    titre = md.split("\n", 1)[0]
    m = re.search(r"^## Besoins\n(.*?)(?=^## )", md, re.S | re.M)
    besoins = re.sub(r"<[^>]+>", "", m.group(1) if m else "")[:4000]
    t = re.search(r"^## Récap · [^·]+· (.*)$", md, re.M)
    titre_plan = t.group(1).replace("\\", "").strip() if t else titre
    return (f"Un plan va être écrit dans ce dépôt (le chemin courant est son état de départ).\n"
            f"Titre du plan : {titre_plan}\n\nBesoins exprimés :\n{besoins.strip()}\n\n"
            "Enquête sur le dépôt et rends ta fiche, avant que le plan ne s'écrive. Le serveur de graphe "
            "(codebase-memory) n'est pas disponible dans ce rejeu : Read, Grep et Glob seulement"
            + (", plus Bash enfermé (git, wc, ls ; pas de réseau)." if bras.endswith("bash") else "."))


def agent_def(bras: str) -> dict:
    """La définition inline du sous-agent rejoué. `actuel` garde le corps de l'enquêteur du plugin ; les listes
    se jouent seules, comme `mesure.py` jouait `checklist-enquete.md`."""
    src = BRAS[bras].read_text()
    corps = src.split("---", 2)[2] if bras == "actuel" else src
    return {"description": "enquêteur rejoué (banc enquête)", "prompt": corps, "model": "claude-haiku-5-5",
            "effort": "high", "tools": ["Read", "Grep", "Glob"] + (["Bash"] if bras.endswith("bash") else [])}


def _court(x: str) -> str:
    return x if len(x) <= 160 else f"{x[:120]}…[{len(x)} caractères]"


class _Simule:
    """Remplace `subprocess` dans `banc` pour `--dry-run` : imprime la commande que `claude -p` lancerait, sans la lancer.
    `banc.claude` construit sa commande elle-même : on lit donc la vraie, pas une copie."""

    @staticmethod
    def run(cmd, input=None, **kwargs):
        print("    " + " ".join(_court(x) for x in cmd))
        print(f"    entrée : {len(input or '')} caractères")
        return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")


def _ouvrir(cas: dict, nom: str, dry: bool):
    """Un worktree jetable au commit de départ ; rien n'est créé en --dry-run."""
    return contextlib.nullcontext(Path("<worktree non créé en --dry-run>")) if dry else banc.Worktree(cas, nom)


def jouer(corpus: Path, pid: str, bras: str, tirage: int, budget, dry: bool):
    f = DONNEES / "sorties" / f"{bras}-{tirage}" / f"{compact(pid)}.json"
    if dry:
        deja = " — sortie déjà là : le vrai lancement la sauterait" if f.exists() else ""
        print(f"# {compact(pid)} ({bras}-{tirage}){deja}")
    elif f.exists():
        return pid, "déjà"
    elif not budget.demarrer(attendre=True):
        return pid, "plafond"
    cout, compte = 0.0, False
    try:
        b = bases(corpus)[pid]
        rev = b.get("mb") or b["base"]
        cas = {"base": f"/x/{b['repo']}", "debut": rev, "fin": rev}
        md = (corpus / "pages" / f"{pid}.md").read_text()
        with _ouvrir(cas, f"{bras}-{tirage}-{compact(pid)}", dry) as wt:
            d = banc.claude(brief(md, bras), cwd=wt, agent=agent_def(bras), tours=60, bash_enferme=bras.endswith("bash"))
        if dry:
            return pid, "simulé"
        if d.get("erreur"):  # rien n'est écrit : un relancement reprendra ce plan
            return pid, f"erreur : {str(d['erreur'])[:120]}"
        d["id"] = pid
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(d, ensure_ascii=False))
        cout, compte = d.get("total_cost_usd") or 0, True
        return pid, round(cout, 3)
    finally:
        if not dry:
            budget.terminer(cout, compte)


def cmd_bras(corpus: Path, bras: str, tirage: int, plafond: float, dry: bool, par: int) -> int:
    budget = None if dry else rejouer.Budget(plafond, par)
    with cf.ThreadPoolExecutor(1 if dry else par) as ex:
        for pid, res in ex.map(lambda p: jouer(corpus, p, bras, tirage, budget, dry), echantillon(corpus)):
            if not dry:
                print(compact(pid), res, "cumul", round(budget.depense, 2), flush=True)
    if not dry:
        print("FIN", bras, tirage, round(budget.depense, 2))
    return 0


def juger(corpus: Path, pid: str, bras_juge: str, budget, dry: bool):
    f = DONNEES / "sorties" / f"juge-{bras_juge}" / f"{compact(pid)}.json"
    if dry:
        print(f"# juge {compact(pid)} ({bras_juge})")
    elif f.exists():
        return pid, "déjà"
    elif not budget.demarrer(attendre=True):
        return pid, "plafond"
    cout, compte = 0.0, False
    try:
        motif = bras_juge.replace("@", "-") if "@" in bras_juge else bras_juge + "-[0-9]"
        fiches = [json.loads(x.read_text()).get("result") or ""
                  for x in sorted((DONNEES / "sorties").glob(f"{motif}/{compact(pid)}.json"))]
        if not fiches:
            return pid, "pas de fiche"
        classement = json.loads((corpus / "classement.json").read_text())
        dec = [x for x in classement["items"] if x["page"] == pid and x.get("trouvable") == "oui" and not x.get("doublon_de")]
        fiche = "\n\n=== TIRAGE SUIVANT ===\n\n".join(fiches)
        liste = "\n".join(f"- {x['id']} : {x['resume'][:400]}" for x in dec)
        d = banc.claude(JUGE % (liste, fiche[:60000]), modele=MODELE_JUGE, effort="medium", outils="", tours=1, delai=900)
        if dry:
            return pid, "simulé"
        cout, compte = d.get("total_cost_usd") or 0, True
        j = banc.json_dans(d.get("result"))
        if d.get("erreur") or not j or "verdicts" not in j:  # illisible : rien n'est écrit, un relancement reprendra
            return pid, "illisible"
        j["cout"], j["n"] = cout, len(dec)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(j, ensure_ascii=False))
        return pid, round(cout, 3)
    finally:
        if not dry:
            budget.terminer(cout, compte)


def cmd_juge(corpus: Path, bras_juge: str, plafond: float, dry: bool, par: int) -> int:
    budget = None if dry else rejouer.Budget(plafond, par)
    with cf.ThreadPoolExecutor(1 if dry else par) as ex:
        for pid, res in ex.map(lambda p: juger(corpus, p, bras_juge, budget, dry), echantillon(corpus)):
            if not dry:
                print(compact(pid), res, "cumul", round(budget.depense, 2), flush=True)
    if not dry:
        print("FIN juge", bras_juge, round(budget.depense, 2))
    return 0


# --- Le relevé déterministe (sans modèle) ----------------------------------------------------------------------------

def extraire_items(md: str) -> list[str]:
    """Les découvertes « trouvable au plan » du journal, étiquette brute : le texte du passage, une fois chacun.
    Même extraction que le corpus du POC (`corpus/items.py`) : « découverte — trouvable… » ou « trouvable au plan : oui »,
    dans les sections « Journal » seulement, décompte exclu."""
    jour = False
    vus: set[str] = set()
    out: list[str] = []
    for ligne in md.split("\n"):
        if ligne.startswith("## "):
            jour = "Journal" in ligne
        if not jour:
            continue
        s = re.sub(r"<[^>]+>", "", ligne).strip()
        if re.search(r"D[ée]compte", s) and "trouvable" in s:
            continue
        for p in re.split(r"(?i)(?=découverte\s*[—–-]\s*(?:trouvable|pas trouvable|non trouvable))", s):
            m = re.match(r"(?i)découverte\s*[—–-]\s*(trouvable|pas trouvable|non trouvable)", p)
            if m:
                oui = m.group(1).lower() == "trouvable"
            else:
                a = re.search(r"(?i)trouvable au plan\s*:\s*(oui|non)", p)
                if not a:
                    continue
                oui = a.group(1).lower() == "oui"
            texte = p[:900].strip()
            if oui and texte not in vus:
                vus.add(texte)
                out.append(texte)
    return out


def fichiers_touches(md: str) -> set[str]:
    """Les fichiers du tableau « Exécution » de la page (tableau HTML, ou tableau en tuyaux à défaut)."""
    ex = md.split("## Exécution", 1)[-1].split("## Journal", 1)[0]
    lignes = []
    for tr in re.findall(r"<tr>(.*?)</tr>", ex, re.S)[1:]:
        td = re.findall(r"<td>(.*?)</td>", tr, re.S)
        if len(td) >= 2 and not re.match(r"^\s*(D|C)\d", td[0]):
            lignes.append(td[1])
    if not lignes:
        for l in ex.splitlines():
            if l.startswith("|") and not l.startswith("| ---"):
                c = l.split("|")
                if len(c) > 3 and not re.match(r"^\s*(D|C)\d|^\s*Étape", c[1]):
                    lignes.append(c[2])
    return set(CHEMIN.findall(" ".join(lignes)))


def git(depot: Path, *args: str) -> str:
    return subprocess.run(["git", "--git-dir", str(depot), *args], capture_output=True, text=True).stdout


def depot_de(repo: str, depots: Path) -> Path:
    """Le clone miroir du dépôt, créé à la première demande."""
    d = depots / f"{repo}.git"
    if not d.exists():
        if repo not in SOURCES:
            raise RuntimeError(f"dépôt inconnu : {repo} (ni clone dans {depots}, ni source dans SOURCES)")
        d.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--mirror", "--quiet", str(SOURCES[repo]), str(d)], check=True)
    return d


def resoudre(touches: set[str], arbre: set[str]) -> set[str]:
    """Les chemins du plan, ramenés aux chemins réels de l'arbre (un nom abrégé l'est par suffixe unique)."""
    out = set()
    for t in touches:
        if t in arbre:
            out.add(t)
            continue
        cand = [p for p in arbre if p.endswith("/" + t) or os.path.basename(p) == os.path.basename(t)]
        if len(cand) == 1:
            out.add(cand[0])
    return out


def compter_refs(depot: Path, rev: str, reels: set[str], touches: set[str]) -> Counter:
    """Les fichiers qui citent le nom (ou la racine du nom) d'un fichier touché, au commit de départ."""
    v: Counter = Counter()
    for t in reels | touches:
        nom = os.path.basename(t)
        racine = nom.rsplit(".", 1)[0]
        for motif in ({nom, racine} if len(racine) > 5 else {nom}):
            for l in git(depot, "grep", "-l", "-F", motif, rev).splitlines():
                p = l.split(":", 1)[1]
                if p not in reels:
                    v[p] += 1
    return v


def co_change(depot: Path, rev: str, reels: set[str]) -> Counter:
    """Pour chaque fichier, la somme des parts de commits où il est co-modifié avec un fichier touché (historique
    antérieur au commit de départ ; les commits de plus de MAX_COMMIT fichiers ne comptent pas)."""
    sc: Counter = Counter()
    for t in reels:
        log = git(depot, "log", "--format=format:@@", "--name-only", "--full-diff", rev, "--", t)
        commits = [set(x.split()) for x in log.split("@@") if x.strip()]
        n = len(commits) or 1
        for cm in commits:
            if len(cm) > MAX_COMMIT:
                continue
            for p in cm - reels:
                sc[p] += 1 / n
    return sc


def voisins_de(depot: Path, rev: str, md: str) -> dict | None:
    """Les TOP_VOISINS premiers fichiers du relevé d'un plan, classés par co-change. None si l'arbre est absent."""
    arbre = set(git(depot, "ls-tree", "-r", "--name-only", rev).split())
    if not arbre:
        return None
    touches = fichiers_touches(md)
    reels = resoudre(touches, arbre)
    refs = compter_refs(depot, rev, reels, touches)
    sc = co_change(depot, rev, reels)
    classes = sorted(refs, key=lambda x: -(round(sc.get(x, 0), 3) * 1000 + refs[x]))[:TOP_VOISINS]
    return {"touches": touches, "reels": reels, "voisins": classes}


def releve(corpus: Path, depots: Path | None = None) -> dict:
    """Rappel du relevé sur les découvertes brutes du corpus. Sans modèle : git en lecture seule."""
    depots = depots or DEPOTS
    bs = bases(corpus)
    res = {"n": 0, "trouves": 0, "plans": 0, "plans_sans_base": 0, "plans_sans_arbre": 0, "tailles": [], "par_plan": {}}
    for page in sorted((corpus / "pages").glob("*.md")):
        pid, md = page.stem, page.read_text()
        items = extraire_items(md)
        if not items:
            continue
        if pid not in bs:
            res["plans_sans_base"] += 1
            continue
        b = bs[pid]
        rel = voisins_de(depot_de(b["repo"], depots), b.get("mb") or b["base"], md)
        if rel is None:
            res["plans_sans_arbre"] += 1
            continue
        noms_voisins = {os.path.basename(v) for v in rel["voisins"]}
        noms_plan = {os.path.basename(t) for t in rel["touches"] | rel["reels"]}
        n_p = trouves_p = 0
        for texte in items:
            cites = {os.path.basename(c) for c in CHEMIN.findall(texte)} - noms_plan
            n_p += 1
            if cites and cites & noms_voisins:
                trouves_p += 1
        res["n"] += n_p
        res["trouves"] += trouves_p
        res["plans"] += 1
        res["tailles"].append(len(rel["voisins"]))
        res["par_plan"][compact(pid)] = [n_p, trouves_p, len(rel["voisins"])]
    res["rappel"] = round(100 * res["trouves"] / res["n"], 1) if res["n"] else 0.0
    res["voisins_med"] = statistics.median(res["tailles"]) if res["tailles"] else 0
    return res


def cmd_releve(corpus: Path) -> int:
    r = releve(corpus)
    fr = lambda x: str(x).replace(".", ",")  # noqa: E731
    print(f"relevé, étiquette brute : {r['n']} découvertes uniques, {r['trouves']} retrouvées, rappel {fr(r['rappel'])} %")
    print(f"plans relevés {r['plans']}, sans base {r['plans_sans_base']}, sans arbre {r['plans_sans_arbre']} ; "
          f"voisins médians par plan {r['voisins_med']}")
    sortie = DONNEES / "releves" / f"releve-{corpus.name}-{datetime.date.today().isoformat()}.json"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(r, ensure_ascii=False, indent=1))
    print(f"détail (hors dépôt) : {sortie}")
    return 0


# --- Ligne de commande -----------------------------------------------------------------------------------------------

def construire_parseur() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Banc d'enquête : voir l'en-tête de ce fichier.")
    ap.add_argument("cible", help="<bras> | juge:<bras>[@<tirage>] | releve")
    ap.add_argument("plafond", nargs="?", type=float, help="dépense maximale en dollars (positive, sauf --dry-run)")
    ap.add_argument("tirage", nargs="?", type=int, default=1, help="numéro du tirage (défaut 1)")
    ap.add_argument("--corpus", help="dossier du corpus (défaut : ~/.local/share/banc-enquete/corpus)")
    ap.add_argument("--dry-run", action="store_true", help="imprime les commandes ; n'appelle rien, n'écrit rien")
    ap.add_argument("--par", type=int, default=PAR, help="appels en parallèle")
    return ap


def main(argv=None) -> int:
    a = construire_parseur().parse_args(argv)
    corpus = corpus_de(a.corpus)
    if a.cible == "releve":
        return cmd_releve(corpus)
    if a.plafond is None:
        print("refus : pas de plafond. Donner <plafond> en dollars, positif.", file=sys.stderr)
        return 2
    if not a.dry_run and a.plafond <= 0:
        print(f"refus : plafond {a.plafond} non positif ; rien ne part sans plafond positif (--dry-run pour voir).",
              file=sys.stderr)
        return 2
    juge = a.cible.startswith("juge:")
    bras = a.cible[5:] if juge else a.cible
    nom = bras.split("@")[0] if juge else bras
    if nom not in BRAS or ("@" in bras and not juge):
        print(f"refus : bras « {a.cible} » inconnu (actuel, liste, liste-bash ; juge:<bras>[@<tirage>]).", file=sys.stderr)
        return 2
    if not (corpus / "pages").is_dir():
        print(f"refus : corpus introuvable : {corpus} (voir --corpus).", file=sys.stderr)
        return 2
    if not a.dry_run:
        return cmd_juge(corpus, bras, a.plafond, False, a.par) if juge else \
            cmd_bras(corpus, bras, a.tirage, a.plafond, False, a.par)
    banc_subprocess = banc.subprocess
    banc.subprocess = _Simule
    try:
        return cmd_juge(corpus, bras, a.plafond, True, a.par) if juge else \
            cmd_bras(corpus, bras, a.tirage, a.plafond, True, a.par)
    finally:
        banc.subprocess = banc_subprocess


if __name__ == "__main__":
    sys.exit(main())
