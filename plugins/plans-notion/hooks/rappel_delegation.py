#!/usr/bin/env python3
"""Hook PostToolUse (ExitPlanMode) : rappelle de déléguer chaque étape à l'``executant``.

Le hook lit sur stdin le JSON de Claude Code et prend le texte du plan dans
``tool_input.plan``. Rappel : code 0, et sur stdout
``hookSpecificOutput.additionalContext``, qui s'ajoute au contexte de la session.
Si le plan cite une page Notion (``notion.so`` ou ``app.notion.com``), le plan est
déjà suivi par ``plans-notion`` : silence. Le hook ne bloque jamais : toute erreur
(JSON illisible, champ absent) donne code 0 et sortie vide.
"""
from __future__ import annotations

import json
import sys

MARQUEURS_NOTION = ("notion.so", "app.notion.com")
RAPPEL = ("Plan natif approuvé : charge le skill `plans-notion:deleguer-a-haiku` "
          "et délègue chaque étape à l'`executant`.")


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        plan = donnees["tool_input"]["plan"]
        if not isinstance(plan, str):
            return 0
        if any(marqueur in plan.lower() for marqueur in MARQUEURS_NOTION):
            return 0
    except Exception:  # garde-fou cassé : on ne rend rien, on ne bloque rien
        return 0
    sortie = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": RAPPEL}}
    print(json.dumps(sortie, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
