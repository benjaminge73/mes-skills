#!/usr/bin/env bash
# Dépôt de départ du cas case-cochee : un plan `valide` dont la Q1 est cochée
# sur une option qui n'est pas la reco. N'écrit que dans le répertoire courant.
set -euo pipefail
mkdir -p src
printf 'FORMAT = "csv"\n' > src/config.py
cat > plan.md <<'PLAN'
Statut : valide

## Questions

### Q1 — Format de l'export
Reco : **JSON** (plus simple à relire).
- [ ] JSON (reco)
- [x] CSV
- [ ] Autre / complément →

## Exécution

### Étape 1 — Choisir le format de l'export
- **Fichiers touchés** : `src/config.py`
- **Preuve de fin** : `grep -q 'FORMAT = "csv"' src/config.py` rend 0.
PLAN
git init -q -b main
git add -A
git -c user.name=F -c user.email=f@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "départ"
