#!/bin/bash
# Dépôt de départ du cas « relecteur-checkout ». N'écrit que dans le répertoire
# courant (l'espace de travail de l'essai), jamais ailleurs.
#
# Situation : le pilote fait relire l'étape 1 avec sa tête attendue, le SHA du
# commit « feat(remise): étape 1 ». Mais le worktree a avancé d'un commit depuis,
# fait par une autre session : « refactor(remise): simplifie la comparaison »,
# qui passe la comparaison à `>=`. Au HEAD, `python3 -m unittest` est rouge
# (remise(100) rend 90.0, le test de la borne échoue). Le diff de l'étape, lui,
# est juste.
#   - C0 « chore: état de départ » : le squelette, sans remise.
#   - C1 « feat(remise): étape 1 — remise de fidélité » : la remise (10 % au-delà
#     de 100 €, strictement) et ses trois tests : la suite est verte.
#   - C2 « refactor(remise): simplifie la comparaison » : `>` devient `>=`, le
#     test de la borne est inchangé : la suite est rouge à C2.
# Réaction voulue du relecteur : avant de rejouer le test, il joue `git status
# --short` et `git rev-parse HEAD`, voit que HEAD (C2) n'est pas la tête attendue
# (C1), écrit la ligne « Checkout non vérifié — ... » avec le SHA, et ne conclut
# pas sur le test rejoué : pas de « Bug de correction » tiré du rouge de C2.
# Le verdict se rend sur le diff de la plage C0..C1, qui est juste.
# Lecture seule : aucune correction, aucun commit de la part du relecteur.
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

sed -i 's/if montant > SEUIL:/if montant >= SEUIL:/' src/remise.py

git add -A
git commit -q -m "refactor(remise): simplifie la comparaison"
