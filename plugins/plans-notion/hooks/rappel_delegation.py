#!/usr/bin/env python3
"""Hook PostToolUse (ExitPlanMode) : rappelle de déléguer chaque étape à l'``executant``.

Le hook lit sur stdin le JSON de Claude Code. Le texte du plan est cherché dans
l'ordre : ``tool_input.plan`` (chaîne), sinon le fichier désigné par
``tool_input.planFilePath`` ou ``tool_response.planFilePath``, s'il existe et se
lit. Rappel : code 0, et sur stdout ``hookSpecificOutput.additionalContext``, qui
s'ajoute au contexte de la session.

- Si le texte trouvé cite une page Notion (``notion.so`` ou ``app.notion.com``),
  le plan est déjà suivi par ``plans-notion`` : silence.
- Si aucun texte n'est trouvable mais que l'entrée est un JSON valide, le rappel
  part quand même : PostToolUse ne part que si ExitPlanMode a réussi, donc un
  plan a été approuvé.
- JSON illisible, ou erreur : code 0 et sortie vide.

Le hook ne bloque jamais.
"""
from __future__ import annotations

import json
import sys

MARQUEURS_NOTION = ("notion.so", "app.notion.com")
RAPPEL = ("Plan natif approuvé : charge le skill `plans-notion:deleguer-a-haiku` "
          "et délègue chaque étape à l'`executant`.")


def _objet(valeur) -> dict:
    return valeur if isinstance(valeur, dict) else {}


def _chemin_du_plan(donnees: dict):
    entree = _objet(donnees.get("tool_input"))
    chemin = entree.get("planFilePath")
    if isinstance(chemin, str) and chemin:
        return chemin
    chemin = _objet(donnees.get("tool_response")).get("planFilePath")
    return chemin if isinstance(chemin, str) and chemin else None


def _texte_du_plan(donnees) -> str:
    donnees = _objet(donnees)
    plan = _objet(donnees.get("tool_input")).get("plan")
    if isinstance(plan, str) and plan.strip():
        return plan
    chemin = _chemin_du_plan(donnees)
    if chemin is None:
        return ""
    try:
        with open(chemin, encoding="utf-8") as fichier:
            return fichier.read()
    except (OSError, ValueError):  # fichier absent ou illisible : pas de texte
        return ""


def main() -> int:
    try:
        texte = _texte_du_plan(json.load(sys.stdin))
    except Exception:  # entrée illisible : on ne rend rien, on ne bloque rien
        return 0
    if any(marqueur in texte.lower() for marqueur in MARQUEURS_NOTION):
        return 0
    sortie = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": RAPPEL}}
    print(json.dumps(sortie, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
