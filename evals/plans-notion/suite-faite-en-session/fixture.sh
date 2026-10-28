#!/usr/bin/env bash
# Dépôt de départ du cas suite-faite-en-session : un plan exécuté (plan.md), dont la
# fin du journal liste deux restes à faire réversibles et hors sécurité (plus d'une
# étape au total). N'écrit que dans le répertoire courant.
set -euo pipefail

cat > plan.md <<'DOC'
# [Plan] notes - Compter les notes par étiquette

**Statut** : en cours
**Branche** : feat/compter-notes

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Commande `compter` | `notes/commandes.py`, `tests/test_commandes.py` | — | 1 |

### Étape 1 — Commande `compter`

- **Fichiers touchés** : `notes/commandes.py` (modifié), `tests/test_commandes.py` (modifié).
- **Preuve de fin** : `python3 -m unittest`

## Journal d'exécution

### Étape 1 — Commande `compter`

- **Preuve** : `python3 -m unittest` -> 4 tests, OK.
- **Commit** : a1b2c3d
- **Découvertes** : aucune
- **Verdict** : verified

### État final

- Livré : la commande `compter`. Suite complète : verte.
- Reste à faire (non trié) :
  - Paginer `lister` quand il y a plus de 50 notes.
  - Refaire l'index de recherche par étiquette.
DOC

mkdir -p notes tests
: > notes/__init__.py
: > tests/__init__.py

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : compter ; plan exécuté"
