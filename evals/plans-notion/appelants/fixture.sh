#!/usr/bin/env bash
# Dépôt de départ du cas appelants : `core.prix.format_prix` a quatre appelants
# répartis dans trois autres modules — un appel direct, un sous alias d'import
# (`as fp`), un par le nom de la fonction en chaîne (`getattr`), et un test.
# N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p core billing reports web tests

cat > README.md <<'EOF'
# facturation

Factures et rapports de la boutique.

## Tests

```bash
python3 -m unittest discover -s tests
```
EOF

for paquet in core billing reports web; do
  printf '"""%s."""\n' "$paquet" > "$paquet/__init__.py"
done

cat > core/prix.py <<'EOF'
def format_prix(montant: float, devise: str) -> str:
    """Prix affiché : deux décimales et le symbole de la devise."""
    symboles = {"EUR": "€", "USD": "$"}
    return f"{montant:.2f} {symboles.get(devise, devise)}"
EOF

cat > billing/facture.py <<'EOF'
from core.prix import format_prix


def ligne_facture(nom: str, montant: float, devise: str) -> str:
    return f"{nom} : {format_prix(montant, devise)}"
EOF

cat > reports/mensuel.py <<'EOF'
from core.prix import format_prix as fp


def resume(total: float) -> str:
    return "Chiffre d'affaires du mois : " + fp(total, "EUR")
EOF

cat > web/filtres.py <<'EOF'
import core.prix as prix

# Filtres de gabarit, désignés par nom : le moteur de pages appelle appliquer("prix", ...).
FILTRES = {"prix": "format_prix"}


def appliquer(nom: str, *args):
    return getattr(prix, FILTRES[nom])(*args)
EOF

cat > tests/test_prix.py <<'EOF'
import unittest

from core.prix import format_prix


class PrixTest(unittest.TestCase):
    def test_deux_decimales_et_symbole(self):
        self.assertEqual(format_prix(12.5, "EUR"), "12.50 €")


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_facture.py <<'EOF'
import unittest

from billing.facture import ligne_facture


class FactureTest(unittest.TestCase):
    def test_ligne_de_facture(self):
        self.assertEqual(ligne_facture("stylo", 2, "EUR"), "stylo : 2.00 €")


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "facturation : prix, factures, rapports, filtres web"
