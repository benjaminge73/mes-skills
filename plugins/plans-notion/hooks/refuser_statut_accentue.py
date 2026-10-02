#!/usr/bin/env python3
"""Hook PreToolUse (notion-update-page, notion-create-pages) : refuse un ``Statut`` accentué.

Les valeurs du champ ``Statut`` des pages de plan sont écrites sans accent ; une
valeur accentuée (« exécuté ») crée une option fantôme dans la base Notion.
Refus : code 2, motif et valeurs admises sur stderr. Permis : code 0, sans sortie.
Entrée illisible : code 0 avec un mot sur stderr (un garde-fou cassé ne bloque rien).
"""
from __future__ import annotations

import json
import sys
import unicodedata

ADMISES = ("brouillon", "en revue", "valide", "en cours", "a merger", "execute", "archive")


def _textes(valeur):
    """Toutes les chaînes d'une valeur de propriété (texte brut ou objet Notion imbriqué)."""
    if isinstance(valeur, str):
        yield valeur
    elif isinstance(valeur, dict):
        for v in valeur.values():
            yield from _textes(v)
    elif isinstance(valeur, list):
        for v in valeur:
            yield from _textes(v)


def _accentue(texte: str) -> bool:
    return any(unicodedata.combining(c) for c in unicodedata.normalize("NFD", texte))


def _proprietes(entree: dict):
    props = entree.get("properties")
    if isinstance(props, dict):
        yield props
    for page in entree.get("pages") or []:
        if isinstance(page, dict) and isinstance(page.get("properties"), dict):
            yield page["properties"]


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        fautifs = [t for props in _proprietes(donnees.get("tool_input") or {})
                   if "Statut" in props
                   for t in _textes(props["Statut"]) if _accentue(t)]
    except Exception as erreur:
        print(f"refuser_statut_accentue : entrée ignorée ({type(erreur).__name__}: {erreur})",
              file=sys.stderr)
        return 0
    if fautifs:
        print(f"Refusé : la propriété `Statut` ne prend pas d'accent (reçu : {', '.join(fautifs)}). "
              f"Valeurs admises : {', '.join(ADMISES)}.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
