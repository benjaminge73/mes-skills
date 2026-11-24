#!/bin/bash
# Dépôt de départ du cas « relecteur-liste-cochee ». N'écrit que dans le répertoire
# courant (l'espace de travail de l'essai), jamais ailleurs.
#
# Situation : le pilote fait relire l'étape 1 par le relecteur. Le diff est propre :
#   - C0 « chore: état de départ » : le squelette, sans remise.
#   - C1 « feat(remise): étape 1 — remise de fidélité » : la remise (10 % au-delà
#     de 100 €, strictement) et ses trois tests (200, 100, 50). La suite est verte.
# Réaction voulue du relecteur : un rapport qui ouvre par le bloc « Liste parcourue »
# (A à H, puis « Hors liste »), chaque case « rien » ou des numéros R<n>, et un verdict
# en toutes lettres. Sur ce diff, toutes les cases sont « rien ». Lecture seule.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.invalid"
git config commit.gpgsign false

printf '__pycache__/\n*.pyc\n' > .gitignore
mkdir -p src tests
: > src/__init__.py
: > tests/__init__.py

cat > README.md <<'DOC'
# Remises

Calcul de la remise de fidélité. Tests : `python3 -m unittest`.
DOC

git add -A
git commit -q -m "chore: état de départ"

cat > src/remise.py <<'PY'
"""Remise de fidélité sur les commandes."""

SEUIL = 100
TAUX = 0.10


def appliquer_remise(montant):
    """Le montant après remise : 10 % de remise au-delà de 100 €, strictement."""
    if montant > SEUIL:
        return round(montant * (1 - TAUX), 2)
    return montant
PY

cat > tests/test_remise.py <<'PY'
import unittest

from src import remise


class TestRemise(unittest.TestCase):
    def test_dix_pour_cent_au_dela_de_100_euros(self):
        self.assertEqual(remise.appliquer_remise(200), 180)

    def test_pas_de_remise_a_exactement_100_euros(self):
        self.assertEqual(remise.appliquer_remise(100), 100)

    def test_pas_de_remise_en_dessous_de_100_euros(self):
        self.assertEqual(remise.appliquer_remise(50), 50)


if __name__ == "__main__":
    unittest.main()
PY

git add -A
git commit -q -m "feat(remise): étape 1 — remise de fidélité"
