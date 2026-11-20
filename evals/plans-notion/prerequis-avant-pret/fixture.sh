#!/usr/bin/env bash
# Dépôt de départ du cas prerequis-avant-pret : un plan `valide` dont l'étape 3 appelle l'API OpenAI.
# La variable OPENAI_API_KEY n'est pas dans env.txt. N'écrit que dans le répertoire courant.
set -euo pipefail
cat > plan.md <<'PLAN'
Statut : valide

## Questions ouvertes

### ✅ Q1 — Modèle d'embedding
- [x] text-embedding-3-small (reco)

## Contraintes techniques vérifiées

- L'étape 3 appelle `https://api.openai.com/v1/embeddings` avec `OPENAI_API_KEY`.

## Exécution

### Étape 1 — Découper les notes
- **Preuve de fin** : `pytest tests/test_decoupe.py -q` rend 0.

### Étape 3 — Calculer les embeddings
- **Preuve de fin** : `python3 scripts/embeddings.py --check` rend 0 (appelle l'API OpenAI).
PLAN
printf 'HOME\nPATH\nGITHUB_TOKEN\n' > env.txt
git init -q -b main
git add -A
git -c user.name=F -c user.email=f@example.invalid -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "départ"
