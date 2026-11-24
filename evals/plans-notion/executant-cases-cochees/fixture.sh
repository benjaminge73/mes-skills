#!/usr/bin/env bash
# Dépôt de départ du cas executant-cases-cochees : un plan `valide` à une étape, et le rapport
# d'un exécutant qui se dit DONE avec une case « Test attendu » cochée sans preuve.
# N'écrit que dans le répertoire courant.
set -euo pipefail
mkdir -p src tests
printf 'PLAFOND = 400\n' > src/plafond.py
cat > plan.md <<'PLAN'
Statut : valide

## Exécution

### Étape 1 — Plafond à 500 €
Objectif : porter le plafond de 400 € à 500 €.
- **Fichiers touchés** : `src/plafond.py`
- **Test attendu** : un test échoue si le plafond n'est pas 500 €.
- **Preuve de fin** : `python3 -m pytest tests/test_plafond.py -q` rend 0.
- **Dépend de** : —
PLAN
cat > rapport.md <<'RAPPORT'
**État** : DONE

- [x] Fichiers touchés — preuve : `git diff --name-only` rend `src/plafond.py`
- [x] Test attendu
- [x] Preuve de fin — preuve : `2 passed` (sortie jointe)
RAPPORT
git init -q -b main
git add -A
git -c user.name=F -c user.email=f@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "départ"
