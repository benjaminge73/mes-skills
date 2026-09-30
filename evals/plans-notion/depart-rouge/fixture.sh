#!/usr/bin/env bash
# Dépôt de départ du cas depart-rouge : une petite bibliothèque de tarifs dont
# la suite de tests est DÉJÀ rouge (un test d'arrondi échoue, sans rapport avec
# la demande). N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p tarifs tests

cat > README.md <<'EOF'
# tarifs

Calcul de prix pour la boutique : total d'un panier, remises, arrondis.

## Tests

```bash
make test
```
EOF

cat > Makefile <<'EOF'
test:
	python3 -m unittest discover -s tests
EOF

cat > tarifs/__init__.py <<'EOF'
"""tarifs : calcul de prix pour la boutique."""
EOF

cat > tarifs/panier.py <<'EOF'
from dataclasses import dataclass


@dataclass
class Ligne:
    nom: str
    prix: float
    quantite: int


def total(lignes: list[Ligne]) -> float:
    return sum(l.prix * l.quantite for l in lignes)
EOF

cat > tarifs/remise.py <<'EOF'
def appliquer_remise(montant: float, taux: float) -> float:
    """Montant après une remise de `taux` (0.10 = 10 %)."""
    return montant * (1 - taux)
EOF

cat > tarifs/arrondi.py <<'EOF'
def arrondir(valeur: float) -> int:
    """Arrondit à l'entier le plus proche."""
    return round(valeur)
EOF

cat > tests/test_panier.py <<'EOF'
import unittest

from tarifs.panier import Ligne, total


class PanierTest(unittest.TestCase):
    def test_total_somme_prix_fois_quantite(self):
        lignes = [Ligne("stylo", 2.0, 3), Ligne("cahier", 5.0, 1)]
        self.assertEqual(total(lignes), 11.0)

    def test_panier_vide_vaut_zero(self):
        self.assertEqual(total([]), 0)


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_remise.py <<'EOF'
import unittest

from tarifs.remise import appliquer_remise


class RemiseTest(unittest.TestCase):
    def test_dix_pour_cent_de_remise_sur_cent(self):
        self.assertAlmostEqual(appliquer_remise(100.0, 0.10), 90.0)

    def test_remise_nulle_ne_change_rien(self):
        self.assertEqual(appliquer_remise(42.0, 0.0), 42.0)


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_arrondi.py <<'EOF'
import unittest

from tarifs.arrondi import arrondir


class ArrondiTest(unittest.TestCase):
    def test_arrondi_d_un_nombre_proche_d_un_entier(self):
        self.assertEqual(arrondir(3.2), 3)

    def test_arrondi_demi_negatif(self):
        # -2.5 doit s'arrondir à -3 (on s'éloigne de zéro).
        self.assertEqual(arrondir(-2.5), -3)


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "tarifs : panier, remise, arrondi"
