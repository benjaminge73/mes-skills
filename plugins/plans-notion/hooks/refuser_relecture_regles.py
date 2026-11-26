#!/usr/bin/env python3
"""Hook PreToolUse (Read, Bash) et PreCompact : refuse la relecture exacte d'une règle déjà lue.

Un fichier de règles est un fichier du plugin sous ``plans-notion/…/skills/``. Le
pilote qui le relit à l'identique, dans la même session, ne gagne rien : le contenu
est déjà dans son contexte, et il le paie à chaque tour. Le hook garde, par session,
les lectures déjà faites et refuse la répétition exacte d'un fichier inchangé.

- Clé d'une lecture : pour Read, le chemin et la plage (``offset``, ``limit``) ; pour
  Bash, la commande exacte. Le fichier est pris à sa date de modification : une
  lecture passe et s'inscrit si la clé est nouvelle ou si le fichier a changé.
- Bash ne compte que les commandes qui lisent (``cat``, ``sed`` sans ``-i``, ``head``,
  ``tail``, ``awk``, ``grep``, ``less``, ``nl``, ``rtk read``) sans écriture (pas de
  ``>``, pas de ``tee``). Une commande qui exécute un script, ou qui fait autre chose,
  n'est jamais refusée.
- Le pilote se reconnaît à l'absence de ``agent_id`` : un sous-agent n'est jamais refusé.
- ``PreCompact`` vide la liste de la session : après une compaction, la relecture passe.
- Refus : décision ``deny`` sur stdout, code 0. Permis : code 0, sans sortie.
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


def _est_regle(chemin: str) -> bool:
    """Vrai pour un chemin sous ``plans-notion/…/skills/`` : un fichier de règles du plugin."""
    parties = PurePosixPath(chemin).parts
    return any(p == "plans-notion" and "skills" in parties[i + 1:] for i, p in enumerate(parties))


def _est_lecture(commande: str) -> bool:
    """Vrai si chaque segment de la commande ne fait que lire. Au moindre doute, faux."""
    if any(signe in commande for signe in (">", "`", "$(")):
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
    return True


def _inspection(donnees: dict):
    """``(clé, cible, chemins)`` pour une lecture de règle, ou ``None`` si l'appel n'est pas à compter.

    ``cible`` est ce que le message de refus nomme : le chemin (Read) ou la commande (Bash).
    """
    outil = donnees.get("tool_name")
    entree = donnees.get("tool_input") or {}
    if outil == "Read":
        chemin = entree.get("file_path")
        if not isinstance(chemin, str) or not _est_regle(chemin):
            return None
        plage = f"{chemin} (plage {entree.get('offset')}+{entree.get('limit')})"
        cle = "Read " + json.dumps([chemin, entree.get("offset"), entree.get("limit")])
        return cle, plage, [Path(chemin)]
    if outil == "Bash":
        commande = entree.get("command")
        if not isinstance(commande, str) or not _est_lecture(commande):
            return None
        try:
            mots = shlex.split(commande)
        except ValueError:
            return None
        chemins = [Path(m) for m in mots if _est_regle(m)]
        return ("Bash " + commande, f"la commande `{commande}`", chemins) if chemins else None
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
        if donnees.get("hook_event_name") == "PreCompact":
            fichier.unlink(missing_ok=True)
            return 0
        if "agent_id" in donnees:  # un sous-agent porte la clé : jamais refusé
            return 0
        inspection = _inspection(donnees)
        if inspection is None:
            return 0
        cle, cible, chemins = inspection
        if not all(p.is_file() for p in chemins):
            return 0
        mtime = max(p.stat().st_mtime for p in chemins)
        etat = _lire_etat(fichier)
        deja = etat.get(cle)
        if isinstance(deja, dict) and deja.get("mtime") == mtime:
            print(json.dumps(_refus(cible, deja.get("appel")), ensure_ascii=False))
            return 0
        rang = max((v.get("appel", 0) for v in etat.values() if isinstance(v, dict)), default=0) + 1
        etat[cle] = {"appel": rang, "mtime": mtime}
        _ecrire_etat(fichier, etat)
    except Exception:  # garde-fou cassé : on ne bloque rien
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
