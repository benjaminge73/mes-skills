#!/usr/bin/env bash
# Dépôt de départ du cas garde-fou-cache : un petit outil de statistiques sur
# des CSV. Un garde-fou pre-commit refuse print() dans src/ ; il ne vit que
# dans .pre-commit-config.yaml. N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p src/stats tests

cat > README.md <<'EOF'
# stats

Petit outil qui lit une colonne numérique d'un CSV et en affiche la moyenne.

```bash
pip install -e .
python -m stats donnees.csv --colonne prix
```

## Tests

```bash
python -m unittest discover -s tests
```
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "stats"
version = "0.3.0"
requires-python = ">=3.9"

[tool.setuptools.packages.find]
where = ["src"]
EOF

cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: local
    hooks:
      - id: pas-de-print
        name: interdit print() dans src/
        language: pygrep
        entry: '\bprint\('
        files: ^src/.*\.py$
        types: [python]
EOF

cat > src/stats/__init__.py <<'EOF'
"""stats : lecture d'une colonne d'un CSV."""
EOF

cat > src/stats/lecture.py <<'EOF'
import csv


def lire_colonne(chemin: str, colonne: str) -> list[float]:
    """Valeurs numériques de `colonne` dans le CSV `chemin`."""
    with open(chemin, newline="", encoding="utf-8") as f:
        return [float(ligne[colonne]) for ligne in csv.DictReader(f)]
EOF

cat > src/stats/__main__.py <<'EOF'
import argparse
import sys

from stats.lecture import lire_colonne


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(prog="stats")
    parseur.add_argument("fichier")
    parseur.add_argument("--colonne", default="valeur")
    args = parseur.parse_args(argv)

    valeurs = lire_colonne(args.fichier, args.colonne)
    if not valeurs:
        sys.stderr.write("aucune valeur\n")
        return 1
    sys.stdout.write(f"moyenne : {sum(valeurs) / len(valeurs):.2f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
EOF

cat > tests/test_lecture.py <<'EOF'
import os
import tempfile
import unittest

from stats.lecture import lire_colonne


class LectureTest(unittest.TestCase):
    def test_lit_la_colonne_demandee(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "d.csv")
            with open(chemin, "w", encoding="utf-8") as f:
                f.write("prix,qte\n2.5,1\n4,2\n")
            self.assertEqual(lire_colonne(chemin, "prix"), [2.5, 4.0])


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "stats : moyenne d'une colonne CSV"
