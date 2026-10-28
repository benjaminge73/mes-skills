#!/usr/bin/env bash
# Dépôt de départ du cas maitre-au-deuxieme-plan : un plan vient d'être créé, la base compte un autre
# plan non terminé du même projet, un plan terminé et un plan d'un autre projet ; aucun plan maître.
# N'écrit que dans le répertoire courant.
set -euo pipefail

cat > base.md <<'DOC'
# Requête sur Plans Claude — Repo = acme/notes, hors `archive`

| Titre | Statut | Projet | Parent |
|---|---|---|---|
| [Plan] notes - Export CSV | brouillon | https://exemple.invalide/projets/notes | — |
| [Plan] notes - Ancienne migration | execute | https://exemple.invalide/projets/notes | — |
| [Plan] notes - Site vitrine | brouillon | https://exemple.invalide/projets/vitrine | — |
| [Plan] notes - Recherche plein texte | brouillon | https://exemple.invalide/projets/notes | — |

Aucune page `[Plan maître]` dans ce Repo.
DOC

cat > nouveau-plan.md <<'DOC'
# [Plan] notes - Recherche plein texte

**Statut** : brouillon
**Repo** : acme/notes
**Projet** : https://exemple.invalide/projets/notes
**Date** : 2026-10-28

## Cartes

Ajouter une recherche plein texte dans les notes.
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : un plan vient d'être créé"
