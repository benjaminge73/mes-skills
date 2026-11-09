#!/usr/bin/env bash
# Dépôt de départ du cas reste-recopie-dans-la-session : un plan à `execute` (PR déjà
# mergée) dont l'État final liste trois points : un propriétaire à relancer, un
# événement attendu, et une action liée à la PR devenue sans objet. N'écrit que dans
# le répertoire courant.
set -euo pipefail

cat > plan.md <<'DOC'
# [Plan] notes - Compter les notes par étiquette

**Statut** : execute
**Branche** : feat/compter-notes
**PR** : https://example.invalid/notes/pull/12 (mergée le 2026-11-08, commit de merge e4f5a6b présent sur main)

## Journal d'exécution

### État final

- Livré : la commande `compter` et sa ligne dans le README. Suite complète : verte.
- Points ouverts, chacun avec son propriétaire :
  - Auto-fix à activer dans la barre de la PR 12 (propriétaire : Benjamin).
  - Décider si l'ancien format v1 de `notes.json` est supprimé : la question est posée à Benjamin, réponse attendue de lui, et sans réponse la lecture v1 reste en place (propriétaire : Benjamin).
  - Mesurer le taux d'erreur de `compter` en usage réel le 2026-12-08 (événement : 30 jours après le merge ; propriétaire : la session qui lira ce plan à cette date, en lançant `python3 -m notes.mesure`).
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : plan exécuté et mergé"
