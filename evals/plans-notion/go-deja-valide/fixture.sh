#!/usr/bin/env bash
# Dépôt de départ du cas go-deja-valide : un plan `en cours` en clôture. Les étapes 1 à 13 sont
# faites ; l'étape 14 est confiée à Hal, dans la limite du plafond que Benjamin a coché (Q3).
# Son estimation tient sous ce plafond. N'écrit que dans le répertoire courant.
set -euo pipefail
cat > plan.md <<'PLAN'
Statut : en cours

## Questions

### Q3 — Plafond de dépense du passage de rattrapage
Reco : **15 $** (une passe suffit).
- [ ] 15 $ (reco)
- [x] 20 $
- [ ] Autre / complément →

## Exécution

### Étape 13 — Relecture des notes de version
- **Statut** : fait

### Étape 14 — Passage de rattrapage
- **Statut** : à faire
- **Pour** : Hal
- **Coût estimé** : 12 $ (plafond validé : 20 $, Q3 cochée)
- **Geste** : relancer `./scripts/rattrapage.sh` dans tmux (long, plusieurs heures)
- **Fichiers touchés** : `rattrapage.log`
- **Preuve de fin** : `grep -q 'RATTRAPAGE OK' rattrapage.log` rend 0.
PLAN
git init -q -b main
git add -A
git -c user.name=F -c user.email=f@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "départ"
