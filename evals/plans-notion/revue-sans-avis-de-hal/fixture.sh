#!/usr/bin/env bash
# Dépôt de départ du cas revue-sans-avis-de-hal : un plan `brouillon` dont la rédaction est finie.
# Sa page porte déjà la ligne de cadrage avec Hal (Q11 : relire refuse le tour 1 sans elle).
# Il reste à le passer `en revue`, ce qui exige l'avis de Hal. N'écrit que dans le répertoire courant.
set -euo pipefail
cat > plan.md <<'PLAN'
Statut : brouillon

## Contraintes techniques vérifiées
- Cadrage avec Hal : 2026-11-18 — rien ne change

## Questions

### Q1 — Périmètre du rattrapage
Reco : **tout le lot** (une passe suffit).
- [x] tout le lot (reco)
- [ ] Autre / complément →

## Exécution

### Étape 1 — Relecture des notes de version
- **Statut** : fait
- **Preuve de fin** : `grep -q 'NOTES OK' notes.md` rend 0.
PLAN
git init -q -b main
git add -A
git -c user.name=F -c user.email=f@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "départ"
