#!/usr/bin/env bash
# Dépôt de départ du cas declenchement-executer : un plan `valide`, rien de fait. Le prompt ne
# nomme aucun skill ; c'est la description de executer-plan-notion qui doit porter le « go ».
# N'écrit que dans le répertoire courant.
set -euo pipefail
cat > plan.md <<'PLAN'
Statut : valide

## Questions

### Q1 — Nom du fichier produit
Reco : **hello.txt**.
- [x] hello.txt (reco)
- [ ] Autre / complément →

## Exécution

### Étape 1 — Fichier de salutation
- **Statut** : à faire
- **Fichiers touchés** : `hello.txt`
- **Preuve de fin** : `grep -q bonjour hello.txt` rend 0.
PLAN
git init -q -b main
git add -A
git -c user.name=F -c user.email=f@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "départ"
