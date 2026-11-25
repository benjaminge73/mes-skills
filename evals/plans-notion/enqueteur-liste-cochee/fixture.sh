#!/usr/bin/env bash
# Dépôt de départ du cas enqueteur-liste-cochee : `src.remise.appliquer_remise` a un
# appelant direct (`caisse/panier.py`), des tests directs, un test de consommateur
# (`tests/test_panier.py`), et deux documents qui citent le seuil de 100 € (`CLAUDE.md`,
# `docs/remise.md`). N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p src caisse tests docs scripts

cat > README.md <<'EOF'
# Caisse

Remise de fidélité sur les paniers. Tests : `sh scripts/ci_locale.sh`.
EOF

cat > CLAUDE.md <<'EOF'
# Caisse

- Le seuil de remise est dans `src/remise.py` (`SEUIL = 100`). Ne le change pas sans mettre
  à jour `docs/remise.md`.
EOF

cat > docs/remise.md <<'EOF'
# Remise de fidélité

10 % de remise au-delà de 100 €, strictement.
EOF

cat > scripts/ci_locale.sh <<'EOF'
#!/bin/sh
set -e
python3 -m unittest discover -s tests
EOF

touch src/__init__.py caisse/__init__.py tests/__init__.py

cat > src/remise.py <<'EOF'
"""Remise de fidélité sur les commandes."""

SEUIL = 100
TAUX = 0.10


def appliquer_remise(montant):
    """Le montant après remise : 10 % au-delà de 100 €, strictement."""
    if montant > SEUIL:
        return round(montant * (1 - TAUX), 2)
    return montant
EOF

cat > caisse/panier.py <<'EOF'
from src.remise import appliquer_remise


def total_panier(lignes):
    return appliquer_remise(sum(lignes))
EOF

cat > tests/test_remise.py <<'EOF'
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
EOF

cat > tests/test_panier.py <<'EOF'
import unittest

from caisse.panier import total_panier


class TestPanier(unittest.TestCase):
    def test_total_avec_remise(self):
        self.assertEqual(total_panier([120]), 108)


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "caisse : remise de fidélité, panier, tests, documentation"
