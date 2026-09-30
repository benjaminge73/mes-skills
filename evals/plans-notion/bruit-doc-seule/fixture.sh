#!/usr/bin/env bash
# Dépôt de départ du cas bruit-doc-seule : un petit outil Python propre, dont
# le README a une coquille dans le titre « Installation ». N'écrit que dans le
# répertoire courant.
set -euo pipefail

mkdir -p mini_cli tests

cat > README.md <<'EOF'
# mini-cli

Un petit outil en ligne de commande qui affiche l'heure courante dans un fuseau horaire.

## Instalation

```bash
pip install .
```

## Usage

```bash
python -m mini_cli Europe/Paris
```

## Tests

```bash
python -m unittest discover -s tests
```
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "mini-cli"
version = "0.1.0"
requires-python = ">=3.9"
EOF

cat > mini_cli/__init__.py <<'EOF'
"""mini-cli : l'heure courante dans un fuseau horaire."""
EOF

cat > mini_cli/heure.py <<'EOF'
from datetime import datetime
from zoneinfo import ZoneInfo


def heure_dans(fuseau: str, maintenant: datetime | None = None) -> str:
    """Heure formatée HH:MM dans le fuseau demandé."""
    instant = maintenant or datetime.now(tz=ZoneInfo("UTC"))
    return instant.astimezone(ZoneInfo(fuseau)).strftime("%H:%M")
EOF

cat > mini_cli/__main__.py <<'EOF'
import sys

from mini_cli.heure import heure_dans


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        sys.stderr.write("usage : python -m mini_cli <fuseau>\n")
        return 2
    sys.stdout.write(heure_dans(argv[0]) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
EOF

cat > tests/test_heure.py <<'EOF'
import unittest
from datetime import datetime, timezone

from mini_cli.heure import heure_dans


class HeureDansTest(unittest.TestCase):
    def test_paris_est_en_avance_de_deux_heures_en_ete(self):
        midi_utc = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(heure_dans("Europe/Paris", midi_utc), "14:00")


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "mini-cli : version initiale"
