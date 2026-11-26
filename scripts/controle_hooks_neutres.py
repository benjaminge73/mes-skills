"""Contrôle des hooks PreToolUse qui couvrent Bash : rendent 0 et muets sur ``ls``.

Squelette du commit rouge de l'étape 10 : ``decouvrir`` et ``controle_neutre``
ne font encore rien. Le commit vert pose la découverte et le contrôle.
"""
from __future__ import annotations

from pathlib import Path


def decouvrir(racine: Path) -> list[tuple[str, str]]:
    return []


def controle_neutre(racine: Path) -> list[str]:
    return []
