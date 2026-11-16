#!/usr/bin/env bash
# Dépôt de départ du cas plan-reprend-les-restes : pas encore de page de plan, un sujet
# (sujet.md) et le résultat de la requête sur la base « Restes » pour exemple/notes
# (base-restes.md). Trois lignes ouvertes de ce dépôt sont à reprendre ; une est déjà
# prise par un autre plan, une est faite, une autre appartient à un autre dépôt. N'écrit
# que dans le répertoire courant.
set -euo pipefail

cat > sujet.md <<'DOC'
# Sujet du plan qui s'ouvre

Dépôt : exemple/notes.
Titre proposé : « [Plan] notes - Index de recherche par étiquette ».
Objectif : reconstruire l'index de recherche par étiquette, en une étape (`notes/index.py`).
DOC

cat > base-restes.md <<'DOC'
# Export de la base « Restes » : requête « Repo = exemple/notes » et autres lignes

Résultat déjà relevé pour ce dépôt (Notion non branché : ce fichier tient lieu de la requête).
Les lignes des autres dépôts sont présentes pour que la requête soit complète.

| Reste | Repo | Type | Pour | Condition | État | url |
| --- | --- | --- | --- | --- | --- | --- |
| Faut-il garder la lecture de l'ancien format v1 de `notes.json`, ou la supprimer ? | exemple/notes | décision | Benjamin | — | ouvert | https://example.invalid/restes/l1 |
| Mesurer le taux d'erreur de `compter` en usage réel | exemple/notes | suivi | Benjamin | relevé à 30 jours après la mise en service de `compter` | ouvert | https://example.invalid/restes/l2 |
| Activer l'auto-fix dans la barre de la PR | exemple/notes | geste | Benjamin | — | ouvert | https://example.invalid/restes/l3 |
| Nettoyer les exports de démonstration | exemple/notes | geste | Hal | déclencheur : la sortie de la version 0.4 | repris | https://example.invalid/restes/l4 |
| Fermer la vieille branche de test | exemple/notes | geste | Benjamin | — | fait | https://example.invalid/restes/l5 |
| Renouveler le certificat du site de démo | exemple/autre | suivi | Benjamin | 2026-12-01 | ouvert | https://example.invalid/restes/l6 |
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : sujet du prochain plan"
