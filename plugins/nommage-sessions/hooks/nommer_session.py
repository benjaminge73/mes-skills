#!/usr/bin/env python3
"""Hooks UserPromptSubmit et PostToolUse : nomme la session « [Projet - Lieu] sujet ».

Le hook lit sur stdin le JSON de Claude Code (``session_id``, ``prompt``, ``cwd``,
``transcript_path``, ``session_title`` quand un titre personnalisé existe) et
répond, quand il a quelque chose à poser, par
``{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": …}}``.

- **Le dossier de projet n'est pas celui du lancement.** Benjamin lance ses sessions
  depuis la racine du VPS ou le dossier qui regroupe ses projets ; la session choisit
  son dossier de travail quelques secondes plus tard. Seuls ``UserPromptSubmit`` et
  ``SessionStart`` peuvent poser un titre : le hook ``PostToolUse`` (matcher des outils
  de fichiers et de shell) se contente donc de **repérer** le premier dossier de projet
  touché (racine git du fichier lu/écrit ou du ``cwd`` après un ``cd``), et le note
  dans l'état de la session ; le titre est corrigé au message suivant.
- **Projet** : le nom du dépôt GitHub (URL du remote ``origin``, sans ``.git``) du
  dossier repéré ; même nom sur le Mac, le VPS et le cloud, worktrees compris. À défaut
  de remote, le nom du dépôt local. Un dossier non git directement sous le dossier de
  lancement compte aussi. Ni la racine, ni le dossier personnel, ni le dossier de
  lancement lui-même (sauf s'il est un dépôt) ne sont un projet. Première lettre en
  majuscule ; un alias facultatif (``alias.json`` dans le dossier de données :
  ``{"hermes-custom": "Hermes"}``) remplace le nom du dépôt.
- **Sans dossier de projet** : le crochet porte un sujet de 3 mots au plus (donné par
  Haiku, sinon les 3 premiers mots du titre) : ``[Trois mots - Lieu]``. Dès qu'un
  projet est repéré, ce préfixe — et lui seul, jamais un titre que l'utilisateur a
  écrit — est remplacé par ``[Projet - Lieu]`` suivi du sujet.
- **Lieu** : ``Cloud`` si ``CLAUDE_CODE_REMOTE`` vaut ``true``, ``Mac`` sur
  macOS, ``VPS`` pour tout autre poste. ``NOMMAGE_SESSIONS_LIEU`` impose une
  valeur.
- **Titre déjà là** (personnalisé, ou généré et lu dans le transcript) : s'il
  commence par « [ » sans être notre préfixe, on n'y touche pas (y compris l'ancien
  format « [Projet] ») ; sinon on le préfixe.
- **Aucun titre** : au premier vrai message (pas une commande « / »), on demande
  un sujet court à Haiku par ``claude -p``. Une seule tentative par session : si elle
  échoue — CLI non connectée, réseau, délai —, le titre natif généré ensuite sera
  préfixé au message suivant.

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
    "sans crochets, sans ponctuation finale. Ajoute sur une seconde ligne le même sujet "
    "en 3 mots au plus."
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


def racine_projet(chemin: str, lancement: str | None = None) -> str | None:
    """Dossier de projet qui contient ``chemin`` : racine git, ou premier dossier sous le lancement."""
    p = Path(chemin)
    while not p.is_dir() and p != p.parent:
        p = p.parent
    if not p.is_dir():
        return None
    maison = Path.home()
    racine = _sortie_git(str(p), "rev-parse", "--show-toplevel")
    if racine and Path(racine) not in (Path("/"), maison):
        return racine
    if lancement:
        try:
            reste = p.resolve().relative_to(Path(lancement).resolve())
        except ValueError:
            return None
        if reste.parts and not reste.parts[0].startswith("."):
            return str(Path(lancement).resolve() / reste.parts[0])
    return None


def nom_projet(dossier: str) -> str:
    nom = depot_github(dossier)
    if not nom:
        commun = _sortie_git(dossier, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if commun:
            depot = Path(commun)
            if depot.name == ".git":
                depot = depot.parent
            nom = depot.name.removesuffix(".git")
    nom = nom or Path(dossier).name or "session"
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


def trois_mots(texte: str) -> str:
    return " ".join(texte.split()[:3])


def _nettoyer(ligne: str) -> str:
    return ligne.strip(" \"'«»`*[]").rstrip(".!?:;")


def sujet_par_haiku(prompt: str) -> tuple[str, str] | None:
    """``(sujet, sujet en 3 mots)`` demandés à Haiku, ou ``None`` s'il échoue."""
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
    lignes = [_nettoyer(l) for l in r.stdout.splitlines() if l.strip()]
    lignes = [l for l in lignes if l]
    if not lignes:
        return None
    sujet = lignes[0][:LONGUEUR_MAX_SUJET].strip()
    court = trois_mots(lignes[1]) if len(lignes) > 1 else trois_mots(sujet)
    return (sujet, court) if sujet else None


def dossier_donnees() -> Path:
    return Path(os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".claude" / "nommage-sessions")


def fichier_etat(session_id: str) -> Path:
    return dossier_donnees() / f"{session_id}.json"


def lire_etat(session_id: str) -> dict:
    try:
        etat = json.loads(fichier_etat(session_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return etat if isinstance(etat, dict) else {}


def ecrire_etat(session_id: str, etat: dict) -> bool:
    try:
        fichier_etat(session_id).parent.mkdir(parents=True, exist_ok=True)
        fichier_etat(session_id).write_text(json.dumps(etat, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return False
    return True


def repondre(titre: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "sessionTitle": titre}}, ensure_ascii=False))


def chemins_de_l_outil(entree: dict) -> list[str]:
    outil = entree.get("tool_input")
    chemins = []
    if isinstance(outil, dict):
        for cle in ("file_path", "path", "notebook_path"):
            if isinstance(outil.get(cle), str) and outil[cle].startswith("/"):
                chemins.append(outil[cle])
    if entree.get("cwd"):
        chemins.append(entree["cwd"])
    return chemins


def reperer_projet(entree: dict, etat: dict) -> bool:
    """Pose ``etat["projet"]`` d'après les chemins de l'entrée ; vrai si on l'a trouvé."""
    for chemin in chemins_de_l_outil(entree):
        dossier = racine_projet(chemin, etat.get("lancement"))
        if dossier:
            etat["projet"] = nom_projet(dossier)
            return True
    return False


def apres_outil(entree: dict) -> int:
    session_id = entree.get("session_id")
    if not session_id:
        return 0
    etat = lire_etat(session_id)
    if etat.get("projet"):
        return 0
    etat.setdefault("lancement", entree.get("cwd") or os.getcwd())
    if reperer_projet(entree, etat) or not fichier_etat(session_id).exists():
        ecrire_etat(session_id, etat)
    return 0


def main() -> int:
    if os.environ.get(GARDE_RECURSION):
        return 0
    try:
        entree = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(entree, dict):
        return 0
    if entree.get("hook_event_name") == "PostToolUse":
        return apres_outil(entree)

    session_id = entree.get("session_id")
    etat = lire_etat(session_id) if session_id else {}
    etat.setdefault("lancement", entree.get("cwd") or os.getcwd())
    if not etat.get("projet"):
        reperer_projet({"cwd": entree.get("cwd") or os.getcwd()}, etat)
    if session_id and not fichier_etat(session_id).exists():
        ecrire_etat(session_id, etat)
    where = lieu()
    projet = etat.get("projet")

    def prefixe() -> str:
        return f"[{projet or etat.get('court') or 'Session'} - {where}]"

    titre = entree.get("session_title") or titre_du_transcript(entree.get("transcript_path"))
    if titre:
        ancien = etat.get("prefixe")
        if ancien and titre.startswith(ancien):
            if projet and ancien != prefixe():
                sujet = etat.get("sujet") or titre[len(ancien):].strip()
                nouveau = f"{prefixe()} {sujet}".strip()
                etat["prefixe"] = prefixe()
                if session_id:
                    ecrire_etat(session_id, etat)
                repondre(nouveau)
        elif not titre.startswith("["):
            etat["sujet"] = titre
            etat["court"] = trois_mots(titre)
            nouveau = f"{prefixe()} {titre}" if projet else prefixe()
            etat["prefixe"] = prefixe()
            if session_id:
                ecrire_etat(session_id, etat)
            repondre(nouveau)
        return 0

    prompt = (entree.get("prompt") or "").strip()
    if not prompt or prompt.startswith("/") or not session_id or etat.get("haiku"):
        return 0
    etat["haiku"] = True
    if not ecrire_etat(session_id, etat):
        return 0
    resultat = sujet_par_haiku(prompt)
    if resultat:
        etat["sujet"], etat["court"] = resultat
        etat["prefixe"] = prefixe()
        ecrire_etat(session_id, etat)
        repondre(f"{prefixe()} {etat['sujet']}" if projet else prefixe())
    return 0


if __name__ == "__main__":
    sys.exit(main())
