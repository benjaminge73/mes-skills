#!/usr/bin/env bash
# Dépôt de départ du cas relecture-plan-cochee : un plan `en revue` qui attend sa relecture
# avant `valide`. Il porte des pièges visibles à la lecture : un fichier cité qui n'existe pas,
# une étape qui fait deux choses, une « preuve » qui n'est qu'un contrôle manuel.
# N'écrit que dans le répertoire courant.
set -euo pipefail
cat > plan.md <<'PLAN'
Statut : en revue

## Contraintes techniques vérifiées
- Cadrage avec Hal : 2026-11-20 — rien ne change

## Questions ouvertes

### Q1 — Nom du fichier de sortie
Reco : **rapport.txt**.
- [x] rapport.txt (reco)
- [ ] Autre / complément →

## Exécution

Aucun cron touché.

### Étape 1 — Écrire le rapport et son titre
- **Fichiers touchés** : `out/rapport.txt`, `src/rapport.py`
- **Impact fonctionnel** : Rien
- **Preuve de fin** : `grep -q 'RAPPORT OK' out/rapport.txt` rend 0.

### Étape 2 — Vérifier le rendu
- **Fichiers touchés** : `out/rapport.txt`
- **Impact fonctionnel** : Rien
- **Preuve de fin** : contrôle manuel du rendu, à l'œil.
PLAN
git init -q -b main
git add -A
git -c user.name=F -c user.email=f@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "départ"
