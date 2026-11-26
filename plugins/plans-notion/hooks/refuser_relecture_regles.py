#!/usr/bin/env python3
"""Hooks PreToolUse, PostToolUse (Read, Bash) et PreCompact : refuse la relecture exacte d'une règle.

Un fichier de règles est un fichier du plugin sous ``plans-notion/…/skills/``. Le
pilote qui le relit à l'identique, dans la même session, ne gagne rien : le contenu
est déjà dans son contexte, et il le paie à chaque tour.

- PostToolUse inscrit une lecture, et seulement une lecture qui a abouti (l'événement
  ne vient que sur un outil réussi). Une lecture interrompue, refusée par une
  permission ou par un autre hook, n'est donc jamais inscrite.
- PreToolUse ne fait que consulter : il refuse la répétition exacte d'un fichier
  inchangé (décision ``deny`` sur stdout, code 0). Il n'écrit rien.
- Clé d'une lecture : pour Read, le chemin absolu et la plage (``offset``, ``limit``) ;
  pour Bash, le dossier du shell (``cwd``) et la commande exacte. Le fichier est pris à
  sa date de modification : une lecture passe si la clé est nouvelle ou si le fichier a changé.
- Un chemin relatif se résout contre ``cwd``. Sans ``cwd``, un chemin relatif n'est
  pas compté : au moindre doute, le hook laisse passer.
- Bash ne compte qu'une commande de lecture (``cat``, ``sed`` sans ``-i``, ``head``,
  ``tail``, ``awk``, ``grep``, ``less``, ``nl``, ``rtk read``) sans écriture ni entrée
  redirigée (pas de ``>``, ``<``, backtick, ``$(``, ni ``tee``), sans option qui lit un
  autre fichier (``grep -f``, ``sed -f``, ``awk -f``), et dont chaque fichier existant
  lu est une règle, sans argument variable (glob, tilde, ``$``, accolades), sans dossier
  lu, et sans ``grep`` récursif (``-r``). Une commande qui lit aussi un autre fichier, qui exécute un script,
  ou qui fait autre chose n'est jamais refusée.
- Le pilote se reconnaît à l'absence de ``agent_id`` : un sous-agent n'inscrit rien et
  n'est jamais refusé.
- ``PreCompact`` vide la liste de la session : après une compaction, la relecture passe.
- Limite acceptée : un ``/rewind`` garde la liste (les lectures annulées restent inscrites).
- État : ``~/.cache/plans-notion/lectures/<session>.json``, ``{"<clé>": {"appel": n,
  "mtime": t}}``. ``appel`` est le rang de la lecture inscrite dans la session (1, 2…),
  pas le numéro d'appel d'outil. ``session_id`` est assaini : il ne sort pas du dossier.
- Entrée illisible, état illisible, erreur quelconque : code 0 et sortie vide. Le hook
  ne bloque que sur une répétition reconnue.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path, PurePosixPath

LECTURES_BASH = {"cat", "sed", "head", "tail", "awk", "grep", "less", "nl"}
SEPARATEURS = re.compile(r"&&|\|\||[;|\n]")
AFFECTATION = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
OPTION_D_ECRITURE = re.compile(r"^-[A-Za-z]*i|^--in-place")  # sed -i, sed -ni, awk -i inplace
OPTION_DE_FICHIER = re.compile(r"^-[A-Za-z]*f|^--file")  # grep -f, sed -f, awk -f : lit un autre fichier
OPTION_RECURSIVE = re.compile(r"^-[A-Za-z]*[rR]|^--recursive|^--dereference-recursive")  # grep -r : lit un arbre
MOTIF_VARIABLE = re.compile(r"[*?\[{~$]")  # glob, accolades, tilde, variable : le contenu lu n'est pas fixe


def _est_regle(chemin: Path) -> bool:
    """Vrai pour un chemin sous ``plans-notion/…/skills/`` : un fichier de règles du plugin."""
    parties = PurePosixPath(chemin).parts
    return any(p == "plans-notion" and "skills" in parties[i + 1:] for i, p in enumerate(parties))


def _absolu(chemin: str, cwd) -> Path | None:
    """Chemin absolu normalisé ; un relatif se résout contre ``cwd``, sans ``cwd`` il n'est pas résolu."""
    if os.path.isabs(chemin):
        return Path(os.path.normpath(chemin))
    if cwd:
        return Path(os.path.normpath(os.path.join(cwd, chemin)))
    return None


def _est_lecture(commande: str) -> bool:
    """Vrai si chaque segment de la commande ne fait que lire. Au moindre doute, faux."""
    if any(signe in commande for signe in (">", "<", "`", "$(")):
        return False
    for segment in SEPARATEURS.split(commande):
        try:
            mots = shlex.split(segment)
        except ValueError:
            return False
        while mots and AFFECTATION.match(mots[0]):
            mots.pop(0)
        if not mots:
            return False
        programme = mots[0]
        if programme == "rtk":
            if len(mots) < 2 or mots[1] != "read":
                return False
        elif programme not in LECTURES_BASH:
            return False
        if programme in ("sed", "awk") and any(OPTION_D_ECRITURE.match(m) or m == "inplace" for m in mots):
            return False
        if programme in ("grep", "sed", "awk") and any(OPTION_DE_FICHIER.match(m) for m in mots):
            return False
        if programme == "grep" and any(OPTION_RECURSIVE.match(m) for m in mots):
            return False
    return True


def _arguments(commande: str) -> list[str] | None:
    """Arguments de chaque segment de la commande : sans affectation, sans programme, sans ``read`` de rtk."""
    arguments = []
    for segment in SEPARATEURS.split(commande):
        try:
            mots = shlex.split(segment)
        except ValueError:
            return None
        while mots and AFFECTATION.match(mots[0]):
            mots.pop(0)
        if not mots:
            continue
        programme, reste = mots[0], mots[1:]
        if programme == "rtk" and reste[:1] == ["read"]:
            reste = reste[1:]
        arguments.extend(reste)
    return arguments


def _fichiers_existants(commande: str, cwd) -> list[Path] | None:
    """Fichiers existants que la commande désigne (arguments non-options), ou ``None`` si doute."""
    arguments = _arguments(commande)
    if arguments is None:
        return None
    existants = []
    for mot in arguments:
        if MOTIF_VARIABLE.search(mot):  # glob, tilde, variable : ce qui est lu n'est pas fixe
            return None
        if mot.startswith("-"):
            continue
        chemin = _absolu(mot, cwd)
        if chemin is None:  # argument relatif sans dossier de départ : on ne sait pas ce qu'il désigne
            return None
        if chemin.is_dir():  # un dossier lu entraîne tout son contenu
            return None
        if chemin.is_file():
            existants.append(chemin)
    return existants


def _inspection(donnees: dict):
    """``(clé, cible, chemins)`` pour une lecture de règle, ou ``None`` si l'appel n'est pas à compter.

    ``cible`` est ce que le message de refus nomme : le chemin (Read) ou la commande (Bash).
    """
    outil = donnees.get("tool_name")
    entree = donnees.get("tool_input") or {}
    cwd = donnees.get("cwd") if isinstance(donnees.get("cwd"), str) else None
    if outil == "Read":
        brut = entree.get("file_path")
        chemin = _absolu(brut, cwd) if isinstance(brut, str) else None
        if chemin is None or not _est_regle(chemin):
            return None
        bornes = []
        if entree.get("offset") is not None:
            bornes.append(f"à partir de la ligne {entree['offset']}")
        if entree.get("limit") is not None:
            bornes.append(f"{entree['limit']} lignes")
        cible = f"{chemin} ({', '.join(bornes)})" if bornes else str(chemin)
        cle = "Read " + json.dumps([str(chemin), entree.get("offset"), entree.get("limit")])
        return cle, cible, [chemin]
    if outil == "Bash":
        commande = entree.get("command")
        if not isinstance(commande, str) or not _est_lecture(commande):
            return None
        fichiers = _fichiers_existants(commande, cwd)
        if not fichiers or not all(_est_regle(p) for p in fichiers):
            return None
        cle = "Bash " + json.dumps([cwd, commande])
        return cle, f"la commande `{commande}`", fichiers
    return None


def _fichier_d_etat(session: str) -> Path:
    nom = re.sub(r"[^A-Za-z0-9_-]", "_", session)[:120]
    return Path.home() / ".cache" / "plans-notion" / "lectures" / f"{nom}.json"


def _lire_etat(fichier: Path) -> dict:
    try:
        etat = json.loads(fichier.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return etat if isinstance(etat, dict) else {}


def _ecrire_etat(fichier: Path, etat: dict) -> None:
    fichier.parent.mkdir(parents=True, exist_ok=True)
    provisoire = fichier.with_name(fichier.name + ".tmp")
    provisoire.write_text(json.dumps(etat, ensure_ascii=False), encoding="utf-8")
    os.replace(provisoire, fichier)


def _refus(cible: str, appel: int) -> dict:
    raison = (f"Refusé : {cible} déjà lu à l'appel {appel} de cette session, inchangé : "
              "relis ton contexte. Une autre plage, ou le fichier après modification, passe.")
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny",
                                   "permissionDecisionReason": raison}}


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if not isinstance(donnees, dict):
            return 0
        session = donnees.get("session_id")
        if not isinstance(session, str) or not session:
            return 0
        fichier = _fichier_d_etat(session)
        evenement = donnees.get("hook_event_name")
        if evenement == "PreCompact":
            fichier.unlink(missing_ok=True)
            return 0
        if "agent_id" in donnees:  # un sous-agent porte la clé : il n'inscrit rien, il n'est jamais refusé
            return 0
        if evenement not in ("PreToolUse", "PostToolUse"):
            return 0
        inspection = _inspection(donnees)
        if inspection is None:
            return 0
        cle, cible, chemins = inspection
        if not all(p.is_file() for p in chemins):
            return 0
        mtime = max(p.stat().st_mtime for p in chemins)
        etat = _lire_etat(fichier)
        if evenement == "PreToolUse":
            deja = etat.get(cle)
            if isinstance(deja, dict) and deja.get("mtime") == mtime:
                print(json.dumps(_refus(cible, deja.get("appel")), ensure_ascii=False))
            return 0
        # PostToolUse : l'outil a abouti, la lecture s'inscrit.
        rang = max((v.get("appel", 0) for v in etat.values() if isinstance(v, dict)), default=0) + 1
        etat[cle] = {"appel": rang, "mtime": mtime}
        _ecrire_etat(fichier, etat)
    except Exception:  # garde-fou cassé : on ne bloque rien
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
