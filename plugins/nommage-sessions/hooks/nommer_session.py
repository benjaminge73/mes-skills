#!/usr/bin/env python3
"""Hook UserPromptSubmit : nomme la session « [Projet] sujet ».

Le hook lit sur stdin le JSON de Claude Code (``session_id``, ``prompt``, ``cwd``,
``transcript_path``, ``session_title`` quand un titre personnalisé existe) et
répond, quand il a quelque chose à poser, par
``{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": …}}``.

- **Projet** : le nom du dépôt git, lu par ``--git-common-dir`` pour qu'un
  worktree porte le nom du dépôt et non celui de son dossier ; hors dépôt, le
  nom du dossier courant.
- **Titre déjà là** (personnalisé, ou généré et lu dans le transcript) : s'il
  commence par « [ », on n'y touche pas ; sinon on le préfixe.
- **Aucun titre** : au premier vrai message (pas une commande « / »), on demande
  un sujet court à Haiku par ``claude -p``. Une seule tentative par session
  (fichier marqueur) : si elle échoue — CLI non connectée, réseau, délai —, le
  titre natif généré ensuite sera préfixé au message suivant.

Au moindre doute (JSON illisible, git absent), le hook sort en 0 sans rien
écrire : un nommage raté ne bloque jamais une session.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

GARDE_RECURSION = "NOMMAGE_SESSIONS_INTERNE"
DELAI_HAIKU = 30
LONGUEUR_MAX_SUJET = 60
CONSIGNE_HAIKU = (
    "Tu nommes des sessions de travail d'un développeur. Réponds uniquement par un "
    "titre de 2 à 6 mots en français qui dit le sujet de la demande, sans guillemets, "
    "sans crochets, sans ponctuation finale."
)


def nom_projet(cwd: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        r = None
    if r is not None and r.returncode == 0 and r.stdout.strip():
        depot = Path(r.stdout.strip())
        if depot.name == ".git":
            depot = depot.parent
        return depot.name.removesuffix(".git")
    return Path(cwd).name or "session"


def titre_du_transcript(chemin: str | None) -> str | None:
    """Dernier titre (personnalisé ou généré) écrit dans le transcript JSONL."""
    if not chemin:
        return None
    titre = None
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                if '-title"' not in ligne:
                    continue
                try:
                    entree = json.loads(ligne)
                except ValueError:
                    continue
                if entree.get("type") == "custom-title":
                    titre = entree.get("customTitle") or titre
                elif entree.get("type") == "ai-title":
                    titre = entree.get("aiTitle") or titre
    except OSError:
        return None
    return titre


def sujet_par_haiku(prompt: str) -> str | None:
    claude = shutil.which("claude")
    if not claude:
        return None
    env = dict(os.environ, **{GARDE_RECURSION: "1"})
    try:
        r = subprocess.run(
            [claude, "-p", "--model", "haiku", "--no-session-persistence",
             "--setting-sources", "", "--strict-mcp-config", "--tools", "",
             "--system-prompt", CONSIGNE_HAIKU],
            input=prompt[:2000], capture_output=True, text=True,
            timeout=DELAI_HAIKU, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    lignes = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    if not lignes:
        return None
    sujet = lignes[0].strip(" \"'«»`*[]").rstrip(".!?:;")
    return sujet[:LONGUEUR_MAX_SUJET].strip() or None


def marqueur(session_id: str) -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".claude" / "nommage-sessions"
    return Path(base) / f"{session_id}.haiku-tente"


def repondre(titre: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "sessionTitle": titre}}, ensure_ascii=False))


def main() -> int:
    if os.environ.get(GARDE_RECURSION):
        return 0
    try:
        entree = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(entree, dict):
        return 0

    projet = nom_projet(entree.get("cwd") or os.getcwd())
    titre = entree.get("session_title") or titre_du_transcript(entree.get("transcript_path"))
    if titre:
        if not titre.startswith("["):
            repondre(f"[{projet}] {titre}")
        return 0

    prompt = (entree.get("prompt") or "").strip()
    session_id = entree.get("session_id")
    if not prompt or prompt.startswith("/") or not session_id:
        return 0
    deja = marqueur(session_id)
    if deja.exists():
        return 0
    try:
        deja.parent.mkdir(parents=True, exist_ok=True)
        deja.touch()
    except OSError:
        return 0
    sujet = sujet_par_haiku(prompt)
    if sujet:
        repondre(f"[{projet}] {sujet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
