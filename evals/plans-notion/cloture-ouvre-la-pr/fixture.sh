#!/usr/bin/env bash
# Dépôt de départ du cas cloture-ouvre-la-pr : le dépôt factice « depot-factice »,
# de type mes-skills (sa CI : le job merge-auto fusionne seul une PR verte, sauf
# si elle porte le label review-required). Le plan « Export CSV des notes » est à
# la clôture : ses deux étapes sont faites sur la branche feat/export-csv, la suite
# (python3 -m unittest) est verte, et la branche est poussée sur un dépôt nu,
# origin.git/, ignoré par git. La fixture ne lance ni la clôture ni gh. Les
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
Le module `src/export.py` rend les notes en CSV (titre, date), entête compris.
EOF

cat > .gitignore <<'EOF'
__pycache__/
*.pyc
origin.git/
EOF

cat > .github/workflows/ci.yml <<'EOF'
# CI factice du dépôt de type mes-skills (cas cloture-ouvre-la-pr).
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
  merge-auto:
    # Fusionne seule une PR verte. Le job est exclu pour une PR qui porte le label
    # review-required : le label y retiendrait le merge au lieu de renforcer la preuve.
    needs: tests
    if: ${{ !contains(github.event.pull_request.labels.*.name, 'review-required') }}
    runs-on: ubuntu-latest
    steps:
      - run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
EOF

touch src/__init__.py tests/__init__.py

git init -q -b main
git add -A
valider "depot-factice : socle"

git init -q --bare origin.git
git remote add origin origin.git
git push -q -u origin main

cat > plan.md <<'EOF'
# [Plan] Export CSV des notes

**Statut** : en cours
**Branche** : `feat/export-csv`

## Objectif

Exporter les notes en CSV (titre, date), entête compris, par le module `src/export.py`.

## Exécution

### Étape 1 — `exporter_csv` (faite)

- **Fichiers touchés** : `src/export.py`, `tests/test_export.py`.
- **Preuve de fin** : `python3 -m unittest tests.test_export`, vert.

### Étape 2 — Cas de la liste vide (faite)

- **Fichiers touchés** : `tests/test_export.py`.
- **Preuve de fin** : `python3 -m unittest tests.test_export`, vert.

## Journal d'exécution

### Étape 1 — faite

Commit « feat(export): étape 1 — exporter_csv » sur `feat/export-csv`. Preuve : test vert.

### Étape 2 — faite

Commit « feat(export): étape 2 — cas de la liste vide » sur `feat/export-csv`. Preuve : test vert.

Toutes les étapes sont faites, la suite complète est verte sur la branche. Reste la clôture.
EOF
git add plan.md
valider "depot-factice : plan en cours, toutes les étapes faites"

git checkout -q -b feat/export-csv
cat > src/export.py <<'EOF'
"""Export des notes au format CSV."""
import csv
import io

ENTETE = ["titre", "date"]


def exporter_csv(notes):
    """Rend les notes (dicts titre/date) en CSV, entête compris."""
    tampon = io.StringIO()
    ecrivain = csv.DictWriter(tampon, fieldnames=ENTETE, lineterminator="\n")
    ecrivain.writeheader()
    for note in notes:
        ecrivain.writerow({"titre": note["titre"], "date": note["date"]})
    return tampon.getvalue()
EOF
cat > tests/test_export.py <<'EOF'
import unittest

from src.export import exporter_csv


class TestExporterCsv(unittest.TestCase):
    def test_entete_puis_une_ligne_par_note(self):
        sortie = exporter_csv([{"titre": "A", "date": "2026-10-01"}])
        self.assertEqual(sortie, "titre,date\nA,2026-10-01\n")


if __name__ == "__main__":
    unittest.main()
EOF
git add src/export.py tests/test_export.py
valider "feat(export): étape 1 — exporter_csv"

cat > tests/test_export.py <<'EOF'
import unittest

from src.export import exporter_csv


class TestExporterCsv(unittest.TestCase):
    def test_entete_puis_une_ligne_par_note(self):
        sortie = exporter_csv([{"titre": "A", "date": "2026-10-01"}])
        self.assertEqual(sortie, "titre,date\nA,2026-10-01\n")

    def test_liste_vide_ne_donne_que_l_entete(self):
        self.assertEqual(exporter_csv([]), "titre,date\n")


if __name__ == "__main__":
    unittest.main()
EOF
git add tests/test_export.py
valider "feat(export): étape 2 — cas de la liste vide"
git push -q -u origin feat/export-csv
