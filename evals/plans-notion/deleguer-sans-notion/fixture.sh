#!/bin/bash
# Dépôt de départ du cas « deleguer-sans-notion ». N'écrit que dans le répertoire
# courant (l'espace de travail de l'essai), jamais ailleurs.
#
# Situation : un plan natif de trois étapes, à fichiers disjoints (donc pas de
# regroupement possible), sans page Notion. Réaction voulue : envoyer les étapes à
# plans-notion:executant, une par appel, sans rien écrire dans Notion, et citer la
# preuve de chaque étape dans la réponse finale.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.invalid"
git config commit.gpgsign false

printf '__pycache__/\n*.pyc\n' > .gitignore
mkdir -p src tests
: > src/__init__.py
: > tests/__init__.py

cat > README.md <<'DOC'
# Petites fonctions

Trois modules sans rapport entre eux. Tests : `python3 -m unittest`.
DOC

cat > src/nombres.py <<'PY'
"""Fonctions sur les nombres."""
PY

cat > src/listes.py <<'PY'
"""Fonctions sur les listes."""
PY

cat > src/chaines.py <<'PY'
"""Fonctions sur les chaînes de caractères."""
PY

cat > plan.md <<'DOC'
# Plan — Trois petites fonctions

**Statut** : approuvé (plan natif validé avant exécution, sans page Notion)

## Objectif

Ajouter trois fonctions utilitaires, chacune dans son module, chacune avec son test.

## Étapes

### Étape 1 — `somme_positive`

- Fichiers : `src/nombres.py`, `tests/test_nombres.py` (créé).
- Ajouter `somme_positive(valeurs)` dans `src/nombres.py` : la somme des nombres
  strictement positifs de la liste. Exemple : `somme_positive([3, -1, 0, 4])` vaut `7`.
- Ajouter le test correspondant dans `tests/test_nombres.py`.
- Preuve : `python3 -m unittest tests.test_nombres`

### Étape 2 — `premier_non_vide`

- Fichiers : `src/listes.py`, `tests/test_listes.py` (créé).
- Ajouter `premier_non_vide(valeurs)` dans `src/listes.py` : le premier élément qui
  n'est ni `None` ni `""`, ou `None` si aucun. Exemple :
  `premier_non_vide(["", None, "a", "b"])` vaut `"a"`.
- Ajouter le test correspondant dans `tests/test_listes.py`.
- Preuve : `python3 -m unittest tests.test_listes`

### Étape 3 — `inverser_mots`

- Fichiers : `src/chaines.py`, `tests/test_chaines.py` (créé).
- Ajouter `inverser_mots(phrase)` dans `src/chaines.py` : les mots de la phrase dans
  l'ordre inverse, séparés par une espace. Exemple : `inverser_mots("un deux trois")`
  vaut `"trois deux un"`.
- Ajouter le test correspondant dans `tests/test_chaines.py`.
- Preuve : `python3 -m unittest tests.test_chaines`
DOC

git add -A
git commit -q -m "chore: état de départ"
