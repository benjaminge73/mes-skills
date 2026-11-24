#!/usr/bin/env python3
"""Ombre d'une relecture réelle, jouée à la volée (plan « Réduire la voilure », 2026-11-23).

Pour une étape que le `relecteur` (Opus) vient de relire, rejoue le MÊME brief sur la chaîne d'ombre, sans toucher
à la relecture d'origine ni à ce qu'elle a décidé :
  - trois relectures Haiku high avec la checklist v2 (`plugins/plans-notion/skills/_partage/listes/relecture-code.md`,
    lue via `--liste`), puis la chaîne retenue (`chaine.py` :
    extraction, dédoublonnage, vérification de chaque remarque) sur ces trois rapports ;
  - un bras Sonnet medium avec la même checklist, compté À PART : il mesure ce que Sonnet ajoute au-dessus de Haiku
    sur la même consigne, et n'entre dans aucun total de la chaîne.
Rien de ce que l'ombre produit ne décide : le pilote ne traite que les remarques d'Opus, celles de l'ombre sont
seulement comparées. La bascule « chaîne à la place d'Opus » n'est pas faite ici.

Usage :
  ombre.py --id <id> --brief <fichier du brief> --rep <worktree cité dans le brief> --depot <dépôt git>
           --debut <sha> --fin <sha> [--sortie <dossier>] [--plafond 3] [--liste <chemin>] [--dry-run]
           [--opus <rapport d'Opus>] [--retenues <fichier de tri du pilote>]

--opus : le rapport d'Opus de la relecture, copié à côté de l'ombre (`opus-<id>.md`).
--retenues : le tri du pilote (remarques retenues, et remarques de l'ombre seule jugées réelles ou bruit), validé par
`bilan_ombre.valider_retenues` puis copié en `retenues-<id>.json`. Les relectures déjà jouées ne se refont pas : relancer
avec le même `--id` ne paie que le tri. Le pilote lance l'ombre en tâche de fond juste après la relecture, puis passe ce
fichier une fois le tri fait (`revue.md`, « L'ombre de relecture »).

--plafond : garde-fou de rejouer.py, sans effet sur un cas unique : la dépense réelle est dans le bilan imprimé.
--liste : la liste de relecture jouée (défaut : le fichier du plugin). Son sha256 part dans l'ombre-<id>.json
(`liste_sha256`) : une sortie se rattache ainsi à la version exacte de la liste qui l'a produite.

Sorties : `<sortie>/ombre-<id>.json` (défaut : $BANC_DONNEES/ombres/), et les sorties brutes des bras dans
$BANC_DONNEES/sorties/ombre-<id>-*/. Un bras déjà joué pour cet id est repris sans être repayé, comme rejouer.py :
relancer avec le même id ne refait pas les relectures existantes.

Sans Jev dans la chaîne : `chaine.py` est appelé sans `--jev`, donc aucune remarque réfutée par Haiku n'est repêchée par le
second avis. La chaîne mesurée ici est plus stricte que la référence de RESULTATS.md (v2 × 3 + `chaine.py` + Jev) ; le second
avis `jev-1.14.0` se joue à part, sur les remarques gardées (`jev.plausibilite`), et se consigne à côté du tableau d'ombre.

Sans Bash : les relectures de l'ombre n'ont que Read, Grep et Glob (pas de `--bash-enferme`), comme le banc.
Le bilan compte les remarques Sonnet : son en-tête `REMARQUES (n)` s'il est là, sinon les lignes commençant
par une puce ou un numéro.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import banc
import bilan_ombre

ap = argparse.ArgumentParser(description="Ombre d'une relecture réelle : 3 Haiku puis chaîne, et un bras Sonnet à part.")
ap.add_argument("--id", required=True, help="identifiant de l'ombre (lettres, chiffres, '.', '_', '-')")
ap.add_argument("--brief", required=True, help="fichier texte du brief envoyé au relecteur")
ap.add_argument("--rep", required=True, help="chemin du worktree cité dans le brief (remplacé par le worktree jetable)")
ap.add_argument("--depot", required=True, help="chemin du dépôt git")
ap.add_argument("--debut", required=True, help="sha de début de la plage relue (exclu)")
ap.add_argument("--fin", required=True, help="sha de fin de la plage relue (inclus)")
ap.add_argument("--sortie", help="dossier de l'ombre-<id>.json (défaut : $BANC_DONNEES/ombres)")
ap.add_argument("--plafond", type=float, default=3, help="garde-fou de rejouer.py, sans effet sur un cas unique : la dépense réelle est dans le bilan imprimé")
ap.add_argument("--liste", default=str(banc.ICI.parents[1] / "plugins/plans-notion/skills/_partage/listes/relecture-code.md"),
                help="liste de relecture jouée (défaut : le fichier du plugin plans-notion) ; son sha256 part dans le JSON")
ap.add_argument("--dry-run", action="store_true", help="prépare le clone et le cas, imprime les commandes, n'appelle pas claude")
ap.add_argument("--opus", help="rapport d'Opus de la relecture (copié en opus-<id>.md à côté de l'ombre)")
ap.add_argument("--retenues", help="tri du pilote (JSON : {\"remarques\": [...]}), validé puis copié en retenues-<id>.json")
a = ap.parse_args()

if not re.fullmatch(r"[A-Za-z0-9_.-]+", a.id):
    sys.exit("ombre : --id n'accepte que lettres, chiffres, '.', '_' et '-' (il sert de nom de fichier)")

LISTE = Path(a.liste).expanduser().resolve()
if not LISTE.is_file():
    sys.exit(f"ombre : liste de relecture introuvable : {LISTE}")
LISTE_SHA256 = hashlib.sha256(LISTE.read_bytes()).hexdigest()

# Le tri du pilote et le rapport d'Opus sont vérifiés avant toute dépense : une forme fausse ne coûte pas un appel.
if a.opus and not Path(a.opus).expanduser().is_file():
    sys.exit(f"ombre : rapport d'Opus introuvable : {a.opus}")
if a.retenues:
    try:
        RETENUES = bilan_ombre.valider_retenues(json.loads(Path(a.retenues).expanduser().read_text()))
    except (OSError, ValueError) as e:
        sys.exit(f"ombre : tri du pilote invalide ({a.retenues}) : {e}")

CAS = f"ombre-cas-{a.id}.json"
BRAS_HAIKU = [f"ombre-{a.id}-h{i}" for i in (1, 2, 3)]
BRAS_CHAINE = f"ombre-{a.id}-chaine"
BRAS_SONNET = f"ombre-{a.id}-sonnet"


def sha(depot: Path, rev: str) -> str:
    """La révision rendue en sha complet, lue dans le dépôt lui-même (HEAD désigne le worktree, pas le clone nu)."""
    r = subprocess.run(["git", "-C", str(depot), "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ombre : révision introuvable dans {depot} : {rev}")
    return r.stdout.strip()


def preparer_clone(depot: Path) -> Path:
    """Le clone nu du dépôt, créé ou mis à jour : `banc.Worktree` y pose les worktrees jetables."""
    clone = banc.DONNEES / "depots" / (depot.name + ".git")
    clone.parent.mkdir(parents=True, exist_ok=True)
    if clone.exists():
        cmd = ["git", "--git-dir", str(clone), "fetch", str(depot), "+refs/heads/*:refs/heads/*"]
    else:
        cmd = ["git", "clone", "--bare", str(depot), str(clone)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return clone


def cmd_rejouer(bras: str, modele: str, effort: str) -> list[str]:
    return [sys.executable, str(banc.ICI / "rejouer.py"), bras, modele, effort, str(a.plafond),
            "--cas", CAS, "--liste", str(LISTE)]


def cmd_chaine() -> list[str]:
    return [sys.executable, str(banc.ICI / "chaine.py"), BRAS_CHAINE, *BRAS_HAIKU, "--cas", CAS]


def lancer(cmd: list[str]) -> str | None:
    """Lance une commande du banc dans son dossier. Rend None si elle réussit, sinon la fin de sa sortie d'erreur."""
    r = subprocess.run(cmd, cwd=banc.ICI, capture_output=True, text=True)
    print(f"← {Path(cmd[1]).name} {cmd[2]} : {'ok' if r.returncode == 0 else 'échec'}", flush=True)
    return None if r.returncode == 0 else (r.stderr or r.stdout or "").strip()[-400:]


def jouer(cmds: dict[str, list[str]]) -> dict[str, str]:
    """Lance les commandes en parallèle ; rend les erreurs par bras (vide si tout a réussi)."""
    with cf.ThreadPoolExecutor(len(cmds)) as ex:
        futurs = {nom: ex.submit(lancer, cmd) for nom, cmd in cmds.items()}
        erreurs = {nom: f.result() for nom, f in futurs.items()}
    return {nom: e for nom, e in erreurs.items() if e}


def lire(bras: str) -> tuple[dict | None, str | None]:
    """La sortie JSON d'un bras pour cet id, ou (None, erreur) si elle manque ou porte une erreur."""
    f = banc.DONNEES / "sorties" / bras / f"{a.id}.json"
    if not f.exists():
        return None, "sortie absente"
    d = json.loads(f.read_text())
    if "erreur" in d or d.get("is_error") or d.get("result") is None:
        return None, str(d.get("erreur") or d.get("result") or "réponse sans résultat")[:300]
    return d, None


def compter_remarques(texte: str) -> int:
    """Le nombre de remarques d'un rapport relecteur : son en-tête `REMARQUES (n)`, sinon ses lignes à puce ou numérotées."""
    m = re.search(r"REMARQUES \((\d+)\)", texte)
    if m:
        return int(m.group(1))
    return len(re.findall(r"^\s*(?:\d+[.)]|[-*])\s", texte, re.M))


def montant(x: float | None) -> str:
    return "absent" if x is None else f"{x:.3f} dollars"


depot = Path(a.depot).expanduser().resolve()
brief = Path(a.brief).expanduser().read_text()
debut, fin = sha(depot, a.debut), sha(depot, a.fin)
clone = preparer_clone(depot)
banc.DONNEES.mkdir(parents=True, exist_ok=True)
(banc.DONNEES / CAS).write_text(json.dumps([{"id": a.id, "prompt": brief, "rep": a.rep, "base": str(depot),
                                              "debut": debut, "fin": fin, "plage": f"{debut}..{fin}"}],
                                           ensure_ascii=False))

if a.dry_run:
    print(f"liste : {LISTE} (sha256 {LISTE_SHA256})")
    for cmd in [*(cmd_rejouer(b, "claude-haiku-5-5", "high") for b in BRAS_HAIKU), cmd_chaine(),
                cmd_rejouer(BRAS_SONNET, "claude-sonnet-5-5", "medium")]:
        print(shlex.join(cmd))
    sys.exit(0)

erreurs = jouer({b: cmd_rejouer(b, "claude-haiku-5-5", "high") for b in BRAS_HAIKU})
haiku_ok = [b for b in BRAS_HAIKU if lire(b)[0]]
cmds = {BRAS_SONNET: cmd_rejouer(BRAS_SONNET, "claude-sonnet-5-5", "medium")}
if haiku_ok:
    cmds[BRAS_CHAINE] = cmd_chaine()
else:
    erreurs[BRAS_CHAINE] = "aucun rapport Haiku : chaîne non lancée"
erreurs |= jouer(cmds)
for b in [*BRAS_HAIKU, BRAS_CHAINE, BRAS_SONNET]:
    # Une sortie absente ou en erreur (un bras repris d'un essai précédent compte aussi) se note ici, sans planter.
    _, err = lire(b)
    if err:
        erreurs.setdefault(b, err)

haiku_rapports, haiku_cout = [], 0.0
for b in BRAS_HAIKU:
    d, _ = lire(b)
    haiku_rapports.append(d["result"] if d else None)
    haiku_cout += (d.get("total_cost_usd") or 0) if d else 0

d_chaine, _ = lire(BRAS_CHAINE)
chaine = None
if d_chaine:
    cout_chaine = d_chaine.get("total_cost_usd") or 0
    chaine = {"result": d_chaine["result"], "cout": round(cout_chaine, 4),
              "cout_avec_haiku": round(haiku_cout + cout_chaine, 4), "verdicts": d_chaine.get("verdicts", [])}

d_sonnet, _ = lire(BRAS_SONNET)
sonnet = {"result": d_sonnet["result"], "cout": round(d_sonnet.get("total_cost_usd") or 0, 4)} if d_sonnet else None

sortie = Path(a.sortie).expanduser() if a.sortie else banc.DONNEES / "ombres"
sortie.mkdir(parents=True, exist_ok=True)
fichier = sortie / f"ombre-{a.id}.json"
# La date de l'ombre (`fait_le`) sert au filtre --depuis du bilan ; une reprise garde la date de la première passe.
if fichier.exists():
    anterieur = json.loads(fichier.read_text())
    fait_le = anterieur.get("fait_le") or datetime.date.fromtimestamp(fichier.stat().st_mtime).isoformat()
else:
    fait_le = datetime.date.today().isoformat()
fichier.write_text(json.dumps({"id": a.id, "fait_le": fait_le, "liste": str(LISTE), "liste_sha256": LISTE_SHA256,
                               "haiku": {"rapports": haiku_rapports, "cout": round(haiku_cout, 4)},
                               "chaine": chaine, "sonnet": sonnet, "erreurs": erreurs}, ensure_ascii=False))
if a.opus:
    (sortie / f"opus-{a.id}.md").write_text(Path(a.opus).expanduser().read_text())
if a.retenues:
    (sortie / f"retenues-{a.id}.json").write_text(json.dumps({"id": a.id, "remarques": RETENUES}, ensure_ascii=False))

gardees = sum(1 for v in chaine["verdicts"] if v != "REFUTED") if chaine else None
lignes_sonnet = compter_remarques(sonnet["result"]) if sonnet else None
print(f"ombre {a.id} : coût Haiku {montant(haiku_cout)} ; coût chaîne {montant(chaine and chaine['cout'])} ; "
      f"coût chaîne totale {montant(chaine and chaine['cout_avec_haiku'])} ; coût Sonnet {montant(sonnet and sonnet['cout'])} "
      f"(à part) ; remarques gardées par la chaîne {gardees if gardees is not None else 'absent'} ; "
      f"lignes de remarques Sonnet {lignes_sonnet if lignes_sonnet is not None else 'absent'} -> {fichier}")
if erreurs:
    print("erreurs : " + " ; ".join(f"{k} : {v}" for k, v in erreurs.items()))
