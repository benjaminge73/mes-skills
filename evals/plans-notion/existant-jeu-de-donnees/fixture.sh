#!/usr/bin/env bash
# Dépôt de départ du cas existant-jeu-de-donnees : un moteur antifraude dont la
# règle de vélocité est à mesurer. Un générateur de transactions existe déjà
# (scripts/gen_transactions.py, `make data`) mais son CSV est ignoré par git :
# data/ ne contient que .gitkeep. N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p antifraude scripts data tests

cat > README.md <<'EOF'
# antifraude

Règles de détection de fraude sur des transactions par carte.

## Tests

```bash
python3 -m unittest discover -s tests
```
EOF

cat > .gitignore <<'EOF'
data/*.csv
__pycache__/
EOF

: > data/.gitkeep

cat > Makefile <<'EOF'
.PHONY: data test

data:
	python3 scripts/gen_transactions.py --n 5000 --out data/transactions_sample.csv

test:
	python3 -m unittest discover -s tests
EOF

cat > antifraude/__init__.py <<'EOF'
"""antifraude : règles de détection."""
EOF

cat > antifraude/velocite.py <<'EOF'
def declenche(horodatages: list[int], seuil: int = 5, fenetre_s: int = 60) -> bool:
    """Vrai si une carte fait au moins `seuil` transactions dans une fenêtre de `fenetre_s` secondes.

    `horodatages` : secondes écoulées, triées, pour une même carte.
    """
    for i in range(len(horodatages) - seuil + 1):
        if horodatages[i + seuil - 1] - horodatages[i] < fenetre_s:
            return True
    return False
EOF

cat > scripts/gen_transactions.py <<'EOF'
#!/usr/bin/env python3
"""Engendre un jeu de transactions synthétique, reproductible (graine fixe)."""
import argparse
import csv
import random


def main() -> None:
    parseur = argparse.ArgumentParser()
    parseur.add_argument("--n", type=int, default=1000)
    parseur.add_argument("--out", required=True)
    args = parseur.parse_args()

    hasard = random.Random(42)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(["carte", "horodatage", "montant_centimes", "fraude"])
        for i in range(args.n):
            carte = f"carte-{hasard.randint(1, max(2, args.n // 8))}"
            ecrivain.writerow([carte, i * 7 + hasard.randint(0, 6), hasard.randint(200, 20000), int(hasard.random() < 0.01)])


if __name__ == "__main__":
    main()
EOF

cat > tests/test_velocite.py <<'EOF'
import unittest

from antifraude.velocite import declenche


class VelociteTest(unittest.TestCase):
    def test_cinq_transactions_en_moins_d_une_minute_declenchent(self):
        self.assertTrue(declenche([0, 10, 20, 30, 40]))

    def test_transactions_espacees_ne_declenchent_pas(self):
        self.assertFalse(declenche([0, 100, 200, 300, 400]))


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "antifraude : règle de vélocité et générateur de transactions"
