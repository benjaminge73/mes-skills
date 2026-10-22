#!/usr/bin/env bash
# Dépôt de départ du cas maitre-depart-ordre : un plan P2 `pret`, couvert par un plan maître
# dont le Croisement dit que P2 attend P1, encore en cours. N'écrit que dans le répertoire courant.
set -euo pipefail

cat > maitre.md <<'DOC'
# [Plan maître] notes - Compter puis afficher

**Statut** : en cours

## Plans

| Id | Plan | Statut |
|---|---|---|
| P1 | Commande `compter` | en cours |
| P2 | Afficher les comptes | pret |
| P3 | Documentation | pret |

## Croisement

- P2 attend P1 jusqu'à a merger : l'affichage appelle `compter`, qui doit être poussé.
- P3 part avec P1 : la doc ne touche pas le code.

## Ordre de merge

P1, puis P2, puis P3.

## File des actions lourdes

Aucune : les tests sont unitaires.
DOC

cat > plan.md <<'DOC'
# [Plan] notes - Afficher les comptes

**Statut** : pret
**Branche** : feat/afficher-comptes

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Afficher | `notes/affichage.py` | — | 1 |

### Étape 1 — Afficher

- **Fichiers touchés** : `notes/affichage.py` (créé).
- **Preuve de fin** : `python3 -m unittest`

## Journal d'exécution

### Ouverture

- **Orchestration** : plan maître `maitre.md` (P2) ; part après P1 ; rang 2 de l'ordre de merge.
- **Pilote** : Sonnet 5.5, medium
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : plan P2 prêt, maître en cours"
