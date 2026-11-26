#!/usr/bin/env bash
# Dépôt de départ du cas declenchement-negatif-plan : une fonction à renommer, rien de fait.
# Le prompt ne parle ni de plan ni de skill : plan-notion ne doit pas se charger.
# N'écrit que dans le répertoire courant.
set -euo pipefail
cat > salut.py <<'PY'
def saluer(nom):
    return f"Bonjour, {nom} !"


print(saluer("Benjamin"))
PY
