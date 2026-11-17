#!/usr/bin/env bash
# Dépôt de départ du cas icone-des-plans : un plan vient d'être créé dans hermes-custom, la base
# compte un autre plan non terminé du même projet, aucun maître. N'écrit que dans le répertoire courant.
set -euo pipefail

cat > base.md <<'DOC'
# Requête sur Plans Claude — Repo = benjaminge73/hermes-custom, hors `archive`

| Titre | Statut | Projet | Parent |
|---|---|---|---|
| [Plan] hermes-custom - Corriger le cron du matin | brouillon | https://exemple.invalide/projets/hermes | — |
| [Plan] hermes-custom - Sauvegarde des journaux | brouillon | https://exemple.invalide/projets/hermes | — |

Aucune page `[Plan maître]` dans ce Repo.
DOC

cat > nouveau-plan.md <<'DOC'
# [Plan] hermes-custom - Sauvegarde des journaux

**Statut** : brouillon
**Repo** : benjaminge73/hermes-custom
**Projet** : https://exemple.invalide/projets/hermes
**Date** : 2026-11-17

## Cartes

Sauvegarder chaque nuit les journaux du service vers un disque distant.
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "hermes-custom : un plan vient d'être créé"
