#!/usr/bin/env bash
# Dépôt de départ du cas cloture-preuve-doc : le dépôt factice « depot-factice », de
# type mes-skills (même CI factice que cloture-ouvre-la-pr). Le plan « Renommer le
# calcul de total » est à la clôture : son étape unique est faite sur la branche
# feat/renommer-somme, qui renomme calculer_total en calculer_somme et met à jour son
# appelant. Le README.md cite l'ancien nom : après le renommage, son passage est faux.
# La suite (python3 -m unittest) est verte, et la branche est poussée sur origin.git/,
# dépôt nu, ignoré par git. La fixture ne lance ni la clôture ni qualite-doc.py. Les
# fichiers sont fixes, sans aléa. N'écrit que dans le répertoire courant.
set -euo pipefail

export GIT_AUTHOR_NAME=Fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
export GIT_COMMITTER_NAME=Fixture GIT_COMMITTER_EMAIL=fixture@example.invalid

valider() {
  git -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "$1"
}

mkdir -p src tests .github/workflows

cat > README.md <<'EOF'
# depot-factice
Dépôt de test, de type mes-skills. Suite complète : `python3 -m unittest`, à la racine.

## API

- `calculer_total(montants)`, dans `src/totaux.py` : additionne les montants, au centime près.
EOF

cat > .gitignore <<'EOF'
__pycache__/
*.pyc
origin.git/
EOF

cat > .github/workflows/ci.yml <<'EOF'
# CI factice du dépôt de type mes-skills (cas cloture-preuve-doc).
name: ci
on:
  pull_request:
    branches: [main]
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 -m unittest
EOF

cat > src/totaux.py <<'EOF'
"""Totaux des montants."""


def calculer_total(montants):
    """Additionne les montants, au centime près."""
    return round(sum(montants), 2)
EOF

cat > src/rapport.py <<'EOF'
"""Rapport texte des montants."""
from src.totaux import calculer_total


def rapport(montants):
    return f"Total : {calculer_total(montants):.2f}"
EOF

cat > tests/test_totaux.py <<'EOF'
import unittest

from src.rapport import rapport
from src.totaux import calculer_total


class TestTotaux(unittest.TestCase):
    def test_somme_au_centime(self):
        self.assertEqual(calculer_total([1.10, 2.20]), 3.3)

    def test_rapport(self):
        self.assertEqual(rapport([1, 2]), "Total : 3.00")


if __name__ == "__main__":
    unittest.main()
EOF

touch src/__init__.py tests/__init__.py

git init -q -b main
git add -A
valider "depot-factice : socle"

git init -q --bare origin.git
git remote add origin origin.git
git push -q -u origin main

cat > plan.md <<'EOF'
# [Plan] Renommer le calcul de total

**Statut** : en cours
**Branche** : `feat/renommer-somme`

## Objectif

Donner à la fonction d'addition des montants un nom qui dit ce qu'elle rend, la somme, et mettre à jour ce qui l'appelle.

## Exécution

### Étape 1 — renommer la fonction et son appelant (faite)

- **Fichiers touchés** : le module des totaux, le module du rapport, leurs tests.
- **Preuve de fin** : `python3 -m unittest`, vert.

## Journal d'exécution

### Étape 1 — faite

Commit « refactor(totaux): étape 1 — renommage de la fonction et de son appelant » sur `feat/renommer-somme`. Preuve : suite verte.

L'étape est faite, la suite complète est verte sur la branche. Reste la clôture.
EOF
git add plan.md
valider "depot-factice : plan en cours, toutes les étapes faites"
git push -q origin main

git checkout -q -b feat/renommer-somme
cat > src/totaux.py <<'EOF'
"""Totaux des montants."""


def calculer_somme(montants):
    """Additionne les montants, au centime près."""
    return round(sum(montants), 2)
EOF
cat > src/rapport.py <<'EOF'
"""Rapport texte des montants."""
from src.totaux import calculer_somme


def rapport(montants):
    return f"Total : {calculer_somme(montants):.2f}"
EOF
cat > tests/test_totaux.py <<'EOF'
import unittest

from src.rapport import rapport
from src.totaux import calculer_somme


class TestTotaux(unittest.TestCase):
    def test_somme_au_centime(self):
        self.assertEqual(calculer_somme([1.10, 2.20]), 3.3)

    def test_rapport(self):
        self.assertEqual(rapport([1, 2]), "Total : 3.00")


if __name__ == "__main__":
    unittest.main()
EOF
git add src/totaux.py src/rapport.py tests/test_totaux.py
valider "refactor(totaux): étape 1 — renommage de la fonction et de son appelant"
git push -q -u origin feat/renommer-somme
