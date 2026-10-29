#!/usr/bin/env python3
"""Hook UserPromptSubmit : nomme la session « [Projet - Lieu] sujet ».

Le hook lit sur stdin le JSON de Claude Code (``session_id``, ``prompt``, ``cwd``,
``transcript_path``, ``session_title`` quand un titre personnalisé existe) et
répond, quand il a quelque chose à poser, par
``{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": …}}``.

- **Projet** : le nom du dépôt GitHub, lu dans l'URL du remote ``origin`` (la
  dernière partie du chemin, sans ``.git``) ; il ne dépend ni du dossier ni du
  worktree, donc il est le même sur le Mac, le VPS et le cloud. À défaut de
  remote, le nom du dépôt local (``--git-common-dir``), puis celui du dossier
  courant. Première lettre en majuscule ; un alias facultatif (fichier
  ``alias.json`` à côté du marqueur : ``{"hermes-custom": "Hermes"}``) remplace
  le nom du dépôt.
- **Lieu** : ``Cloud`` si ``CLAUDE_CODE_REMOTE`` vaut ``true``, ``Mac`` sur
  macOS, ``VPS`` pour tout autre poste. ``NOMMAGE_SESSIONS_LIEU`` impose une
  valeur.
- **Titre déjà là** (personnalisé, ou généré et lu dans le transcript) : s'il
  commence par « [ », on n'y touche pas (y compris l'ancien format « [Projet] ») ;
  sinon on le préfixe.
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
import platform
import re
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


def _sortie_git(cwd: str, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def depot_github(cwd: str) -> str | None:
    """Nom du dépôt d'après l'URL de ``origin`` (https, ssh, ou proxy du cloud)."""
    url = _sortie_git(cwd, "remote", "get-url", "origin")
    if not url:
        return None
    dernier = re.split(r"[/:]", url.rstrip("/"))[-1]
    return dernier.removesuffix(".git") or None


def nom_projet(cwd: str) -> str:
    nom = depot_github(cwd)
    if not nom:
        commun = _sortie_git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if commun:
            depot = Path(commun)
            if depot.name == ".git":
                depot = depot.parent
            nom = depot.name.removesuffix(".git")
    nom = nom or Path(cwd).name or "session"
    alias = alias_projets().get(nom)
    if alias:
        return alias
    return nom[:1].upper() + nom[1:]


def alias_projets() -> dict:
    try:
        brut = json.loads((dossier_donnees() / "alias.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in brut.items() if isinstance(v, str)} if isinstance(brut, dict) else {}


def lieu() -> str:
    force = (os.environ.get("NOMMAGE_SESSIONS_LIEU") or "").strip()
    if force:
        return force
    if os.environ.get("CLAUDE_CODE_REMOTE") == "true":
        return "Cloud"
    return "Mac" if platform.system() == "Darwin" else "VPS"


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


def dossier_donnees() -> Path:
    return Path(os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".claude" / "nommage-sessions")


def marqueur(session_id: str) -> Path:
    return dossier_donnees() / f"{session_id}.haiku-tente"


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

    etiquette = f"{nom_projet(entree.get('cwd') or os.getcwd())} - {lieu()}"
    titre = entree.get("session_title") or titre_du_transcript(entree.get("transcript_path"))
    if titre:
        if not titre.startswith("["):
            repondre(f"[{etiquette}] {titre}")
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
        repondre(f"[{etiquette}] {sujet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
