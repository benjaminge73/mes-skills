#!/usr/bin/env bash
# Dépôt de départ du cas bruit-bounded : un petit convertisseur de températures,
# propre, suite de tests verte, sans garde-fou caché. N'écrit que dans le
# répertoire courant.
set -euo pipefail

mkdir -p convertisseur tests

cat > README.md <<'EOF'
# convertisseur

Convertit une température de Celsius en Fahrenheit.

```bash
python -m convertisseur 21.5
```

## Tests

```bash
python -m unittest discover -s tests
```
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "convertisseur"
version = "1.2.0"
requires-python = ">=3.9"
EOF

cat > convertisseur/__init__.py <<'EOF'
"""convertisseur de températures."""
EOF

cat > convertisseur/calcul.py <<'EOF'
def celsius_vers_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32
EOF

cat > convertisseur/__main__.py <<'EOF'
import argparse
import sys

from convertisseur.calcul import celsius_vers_fahrenheit


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(prog="convertisseur")
    parseur.add_argument("celsius", type=float)
    args = parseur.parse_args(argv)
    sys.stdout.write(f"{celsius_vers_fahrenheit(args.celsius):.1f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
EOF

cat > tests/test_calcul.py <<'EOF'
import unittest

from convertisseur.calcul import celsius_vers_fahrenheit


class CalculTest(unittest.TestCase):
    def test_eau_qui_gele(self):
        self.assertEqual(celsius_vers_fahrenheit(0), 32)

    def test_eau_qui_bout(self):
        self.assertEqual(celsius_vers_fahrenheit(100), 212)


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "convertisseur : Celsius vers Fahrenheit"
