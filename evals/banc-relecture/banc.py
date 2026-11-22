"""Socle commun du banc de relecture : emplacement des données, lancement de `claude -p` isolé, worktrees jetables.

Les données (jeu de cas, clones des dépôts relus, sorties, jugements) ne vivent PAS dans ce dépôt public :
elles contiennent des briefs, des rapports et du code d'autres dépôts. Elles sont sous `BANC_DONNEES`
(défaut : ~/.local/share/banc-relecture). Voir README.md, « Les données ».
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ICI = Path(__file__).resolve().parent
DEPOT = ICI.parent.parent
DONNEES = Path(os.environ.get("BANC_DONNEES", "~/.local/share/banc-relecture")).expanduser()
RELECTEUR = DEPOT / "plugins" / "plans-notion" / "agents" / "relecteur.md"
# Ce qu'un relecteur rejoué peut lancer : lire, chercher, et des commandes git ou shell sans effet de bord.
# Pas de tests rejoués : un test exécute le code relu, donc du contenu non fiable.
LECTURE = ["Read", "Grep", "Glob", "Bash(git show:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git grep:*)",
           "Bash(git status:*)", "Bash(git rev-parse:*)", "Bash(ls:*)", "Bash(wc:*)"]


def charger(nom: str):
    """Un fichier JSON du dossier de données."""
    return json.loads((DONNEES / nom).read_text())


def corps_relecteur() -> str:
    """La consigne du relecteur sans son en-tête YAML : c'est elle que chaque bras rejoue."""
    return RELECTEUR.read_text().split("---", 2)[2]


def claude(prompt: str, *, cwd: str | Path = "/tmp", modele: str = "claude-haiku-5-5", effort: str | None = None,
           outils: str = "", tours: int = 3, agent: dict | None = None, delai: int = 1800) -> dict:
    """Un appel `claude -p` isolé des réglages et plugins du poste (`--setting-sources project`,
    `--strict-mcp-config`) ; rend le JSON de sortie, ou {"erreur": ...}.

    `agent` : définition inline d'un sous-agent (consigne, modèle, effort) ; sinon modèle et outils directs.
    Les relecteurs lisent du code et des briefs venus d'autres dépôts : du contenu non fiable. Pas de
    `bypassPermissions` donc, mais une liste blanche en lecture seule (`LECTURE`) ; en mode `-p`, tout autre appel est
    refusé d'office, sans question. Aucun outil d'écriture : Edit, Write et NotebookEdit sont toujours refusés."""
    cmd = ["claude", "-p", "--setting-sources", "project", "--strict-mcp-config", "--output-format", "json",
           "--permission-mode", "default", "--allowedTools", ",".join(LECTURE),
           "--disallowedTools", "Edit,Write,NotebookEdit,WebFetch,WebSearch", "--max-turns", str(tours)]
    if agent:
        cmd += ["--agents", json.dumps({"relecteur-banc": agent}), "--agent", "relecteur-banc"]
    else:
        cmd += ["--model", modele, "--tools", outils]
        if effort:
            cmd += ["--effort", effort]
    try:
        # Le prompt passe par l'entrée standard : `--tools` et `--disallowedTools` prennent une liste de valeurs et
        # avaleraient un prompt placé derrière eux en argument.
        r = subprocess.run(cmd, input=prompt, cwd=cwd, capture_output=True, text=True, timeout=delai)
        return json.loads(r.stdout)
    except Exception as e:  # sortie illisible, délai dépassé : le bras note l'erreur et continue
        return {"erreur": repr(e)[:500]}


def json_dans(texte: str):
    """Le premier objet JSON d'un texte de modèle, ou None."""
    m = re.search(r"\{.*\}", texte or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None


class Worktree:
    """Un worktree détaché au commit relu, retiré à la sortie. Le clone vient de `DONNEES/depots/<dépôt>.git`."""

    def __init__(self, cas: dict, nom: str):
        self.git = DONNEES / "depots" / (Path(cas["base"]).name + ".git")
        self.chemin = DONNEES / "worktrees" / nom
        self.fin = cas["fin"]

    def __enter__(self) -> Path:
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "--git-dir", str(self.git), "worktree", "add", "--detach", str(self.chemin), self.fin],
                       capture_output=True, check=True)
        return self.chemin

    def __exit__(self, *exc):
        subprocess.run(["git", "--git-dir", str(self.git), "worktree", "remove", "--force", str(self.chemin)], capture_output=True)


def objectif(cas: dict, n: int = 1500) -> str:
    """L'objectif d'étape recopié dans le brief d'origine (à défaut, le début du brief)."""
    m = re.search(r"OBJECTIF[^:]*:\s*(.{0,%d})" % n, cas["prompt"], re.S)
    return m.group(1) if m else cas["prompt"][:n]
