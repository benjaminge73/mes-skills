#!/usr/bin/env python3
"""Hook SessionStart : rappelle la méthode à charger dans une session lancée par Hermes.

Hermes lance Claude Code avec la variable ``HERMES_SESSION`` : ``code`` pour une
session qui exécute un plan, ``revue`` pour une session qui relit sans rien
écrire. Si la variable vaut l'une de ces deux valeurs, le hook rend sur stdout
``hookSpecificOutput.additionalContext`` : une consigne courte qui nomme ce qu'il
faut charger. Le texte vit ici, et nulle part ailleurs.

- Variable absente, vide ou autre valeur : silence (sortie vide, code 0).
- Entrée stdin illisible : code 0 et sortie vide, même si la variable est posée.

Le hook ne bloque jamais. Contrat avec hermes-custom : une seule variable,
``HERMES_SESSION``, valeur ``code`` ou ``revue``.
"""
from __future__ import annotations

import json
import os
import sys

CONSIGNES = {
    "code": ("Session Hermes `code` : avant de toucher au plan, charge le skill "
             "`plans-notion:deleguer-a-haiku` (sa section « Avant le plan », puis la "
             "délégation de chaque étape à l'`executant`)."),
    "revue": ("Session Hermes `revue` : la lecture se délègue "
              "(`_partage/lecture-deleguee.md`) et l'agent `plans-notion:enqueteur` mène "
              "l'investigation. Aucune délégation d'écriture dans cette session."),
}


def main() -> int:
    try:
        json.load(sys.stdin)
    except Exception:  # entrée illisible : on ne rend rien, on ne bloque rien
        return 0
    consigne = CONSIGNES.get(os.environ.get("HERMES_SESSION", ""))
    if consigne is None:
        return 0
    sortie = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": consigne}}
    print(json.dumps(sortie, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
