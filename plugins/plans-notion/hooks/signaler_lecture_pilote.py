#!/usr/bin/env python3
"""Hook PostToolUse (Read|Bash|Grep|notion-fetch) : signale au pilote une lecture trop grosse.

Le pilote relit son contexte à chaque tour : une sortie d'outil de plus de
``SEUIL_CARACTERES`` caractères doit être déléguée à un sous-agent. Le hook rappelle
ce geste par ``hookSpecificOutput.additionalContext``, sans jamais bloquer.

- Le pilote se reconnaît à l'absence de la clé ``agent_id`` dans l'entrée : un
  sous-agent la porte. Dans un sous-agent : silence.
- Taille : la longueur de ``tool_response`` si c'est une chaîne ; sinon la longueur
  de sa sérialisation JSON (``ensure_ascii=False``), ce qui couvre Bash, Grep et les
  résultats MCP sans dépendre de leur forme exacte.
- Entrée illisible ou sans ``tool_response`` : code 0 et sortie vide.

Le hook ne bloque jamais.
"""
from __future__ import annotations

import json
import sys

# 2026-10-12 : première valeur, à revoir sur mesure (indicateur « La suite »).
SEUIL_CARACTERES = 20000
RAPPEL = ("Lecture de {n} caractères dans le contexte du pilote : elle sera relue à chaque tour. "
          "Délègue la suivante (`_partage/lecture-deleguee.md`).")


def _taille(reponse) -> int:
    if isinstance(reponse, str):
        return len(reponse)
    return len(json.dumps(reponse, ensure_ascii=False))


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if "agent_id" in donnees:  # un sous-agent porte la clé : pas le pilote
            return 0
        if "tool_response" not in donnees:
            return 0
        n = _taille(donnees["tool_response"])
    except Exception:  # entrée illisible : on ne rend rien, on ne bloque rien
        return 0
    if n <= SEUIL_CARACTERES:
        return 0
    sortie = {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                     "additionalContext": RAPPEL.format(n=n)}}
    print(json.dumps(sortie, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
