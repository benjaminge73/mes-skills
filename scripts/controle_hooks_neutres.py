"""Contrôle des hooks PreToolUse qui couvrent Bash : rendent 0 et muets sur ``ls``.

Découverte : ``plugins/*/hooks/hooks.json`` et la clé ``hooks`` de chaque
``plugin.json`` (inline, ou chemin vers un fichier). Un groupe ``PreToolUse``
couvre Bash si son ``matcher`` (regex entière) accepte ``Bash`` ; un groupe sans
``matcher`` ou au ``matcher`` vide couvre tous les outils. Un script n'est joué
qu'une fois, même déclaré sous deux matchers.

Contrôle : chaque commande découverte reçoit sur stdin un appel Bash ``ls``, comme
Claude Code le fait. Elle doit rendre 0 et n'écrire ni sur stdout ni sur stderr.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

# Charge telle que Claude Code l'envoie à un hook PreToolUse : des hooks lisent aussi
# session_id et cwd (refuser_relecture_regles.py sort sans session_id). « / » : un cwd existant,
# hors de tout dépôt, pour qu'aucun hook ne lise l'état d'un projet.
COMMANDE_NEUTRE = json.dumps({
    "session_id": "controle-neutre",
    "cwd": "/",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "ls"},
})
DELAI_SECONDES = 30
_SCRIPT = re.compile(r'\$\{CLAUDE_PLUGIN_ROOT\}/([^"\s]+)')


def _couvre_bash(matcher) -> bool:
    if matcher in (None, "", "*"):
        return True
    try:
        return re.fullmatch(matcher, "Bash") is not None
    except re.error:
        return False


def _commandes_pretool_bash(hooks: dict) -> list[str]:
    commandes = []
    for groupe in hooks.get("PreToolUse", []):
        if not isinstance(groupe, dict) or not _couvre_bash(groupe.get("matcher")):
            continue
        for entree in groupe.get("hooks", []):
            if isinstance(entree, dict) and entree.get("type") == "command" \
                    and isinstance(entree.get("command"), str):
                commandes.append(entree["command"])
    return commandes


def _hooks_du_manifeste(plugin: Path) -> dict:
    manifeste = plugin / ".claude-plugin" / "plugin.json"
    if not manifeste.is_file():
        return {}
    valeur = json.loads(manifeste.read_text(encoding="utf-8")).get("hooks")
    if isinstance(valeur, str):  # chemin relatif à la racine du plugin
        valeur = json.loads((plugin / valeur).read_text(encoding="utf-8")).get("hooks", {})
    return valeur if isinstance(valeur, dict) else {}


def _hooks_du_fichier(plugin: Path) -> dict:
    fichier = plugin / "hooks" / "hooks.json"
    if not fichier.is_file():
        return {}
    hooks = json.loads(fichier.read_text(encoding="utf-8")).get("hooks", {})
    return hooks if isinstance(hooks, dict) else {}


def _script(commande: str) -> str:
    trouve = _SCRIPT.search(commande)
    return trouve.group(1) if trouve else commande


def decouvrir(racine: Path) -> list[tuple[str, str]]:
    """Renvoie ``(nom du plugin, commande)`` pour chaque hook PreToolUse couvrant Bash."""
    trouves: list[tuple[str, str]] = []
    vus: set[tuple[str, str]] = set()
    for plugin in sorted((racine / "plugins").glob("*")):
        if not plugin.is_dir():
            continue
        commandes = _commandes_pretool_bash(_hooks_du_fichier(plugin))
        commandes += _commandes_pretool_bash(_hooks_du_manifeste(plugin))
        for commande in commandes:
            cle = (plugin.name, _script(commande))
            if cle not in vus:
                vus.add(cle)
                trouves.append((plugin.name, commande))
    return trouves


def controle_neutre(racine: Path) -> list[str]:
    """Renvoie une ligne par hook qui ne rend pas 0 muet sur ``ls``. Liste vide : rien à dire."""
    violations: list[str] = []
    for nom, commande in decouvrir(racine):
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(racine / "plugins" / nom)}
        try:
            r = subprocess.run(commande, shell=True, input=COMMANDE_NEUTRE, capture_output=True,
                               text=True, timeout=DELAI_SECONDES, env=env)
        except subprocess.TimeoutExpired:
            violations.append(f"{nom} : {_script(commande)} ne rend pas dans {DELAI_SECONDES} s")
            continue
        sortie = len(r.stdout) + len(r.stderr)
        if r.returncode != 0 or sortie:
            violations.append(
                f"{nom} : {_script(commande)} rend {r.returncode} et écrit {sortie} caractère(s) sur ls")
    return violations
