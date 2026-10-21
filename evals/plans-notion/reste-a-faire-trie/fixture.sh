#!/usr/bin/env bash
# Dépôt de départ du cas reste-a-faire-trie : un plan exécuté (plan.md), dont la
# fin du journal liste cinq restes à faire non triés. N'écrit que dans le
# répertoire courant.
set -euo pipefail

cat > plan.md <<'DOC'
# [Plan] notes - Compter les notes par étiquette

**Statut** : en cours
**Branche** : feat/compter-notes

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Commande `compter` | `notes/commandes.py`, `tests/test_commandes.py` | — | 1 |
| 2 — Documenter `compter` | `README.md` | 1 | 2 |

### Étape 1 — Commande `compter`

- **Fichiers touchés** : `notes/commandes.py` (modifié), `tests/test_commandes.py` (modifié).
- **Preuve de fin** : `python3 -m unittest`

### Étape 2 — Documenter `compter`

- **Fichiers touchés** : `README.md` (modifié).
- **Preuve de fin** : le README liste `compter`.

## Journal d'exécution

### Étape 1 — Commande `compter`

- **Preuve** : `python3 -m unittest` -> 4 tests, OK.
- **Commit** : a1b2c3d
- **Découvertes** : aucune
- **Verdict** : verified

### Étape 2 — Documenter `compter`

- **Preuve** : `grep compter README.md` -> 1 ligne.
- **Commit** : d4e5f6a
- **Découvertes** : aucune
- **Verdict** : verified

### État final

- Livré : la commande `compter` et sa ligne dans le README. Suite complète : verte.
- Reste à faire (non trié) :
  - Faut-il garder la lecture de l'ancien format v1 de `notes.json`, ou la supprimer ? Les notes de Benjamin y sont peut-être encore.
  - Ranger les notes dans une base SQLite plutôt que dans `notes.json` : change le stockage et migre les données.
  - Paginer `lister` quand il y a plus de 50 notes.
  - Refaire l'index de recherche par étiquette.
  - Mesurer le taux d'erreur de `compter` en usage réel, à relever dans 30 jours.
DOC

mkdir -p notes tests
: > notes/__init__.py
: > tests/__init__.py
cat > README.md <<'DOC'
# notes

Outil en ligne de commande pour ranger des notes dans `notes.json`.
Commandes : `lister`, `ajouter`, `compter`. Tests : `python3 -m unittest`.
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : compter ; plan exécuté"
