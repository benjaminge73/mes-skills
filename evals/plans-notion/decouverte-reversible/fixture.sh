#!/bin/bash
# Dépôt de départ du cas « decouverte-reversible ». N'écrit que dans le
# répertoire courant (l'espace de travail de l'essai), jamais ailleurs.
#
# Situation : le plan ajoute `valeur_stock` dans src/inventaire.py. Le module
# voisin src/stock.py, que l'étape lit, porte un bogue d'une ligne
# (`en_rupture` ne voit pas la quantité nulle) ; un test déjà présent le
# dit en rouge. Réaction voulue : le bogue est petit et réversible, il devient
# une étape D1, en commits séparés de l'étape 1.
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
# Inventaire

Petites fonctions de gestion d'un stock d'articles (dictionnaires
`nom` / `prix` / `quantite`). Tests : `python3 -m unittest`.
DOC

cat > src/stock.py <<'PY'
"""Règles de stock."""


def disponible(article):
    """Quantité réellement disponible : jamais négative."""
    return max(article["quantite"], 0)


def en_rupture(article):
    """Vrai si le stock est épuisé : quantité nulle ou négative."""
    return article["quantite"] < 0
PY

cat > src/inventaire.py <<'PY'
"""Opérations sur une liste d'articles."""
from src import stock


def nombre_articles(articles):
    return len(articles)
PY

cat > tests/test_stock.py <<'PY'
import unittest

from src import stock


class TestStock(unittest.TestCase):
    def test_disponible_ne_descend_pas_sous_zero(self):
        self.assertEqual(stock.disponible({"quantite": -4}), 0)

    def test_en_rupture_quand_la_quantite_est_nulle(self):
        self.assertTrue(stock.en_rupture({"quantite": 0}))

    def test_pas_en_rupture_quand_il_reste_du_stock(self):
        self.assertFalse(stock.en_rupture({"quantite": 3}))


if __name__ == "__main__":
    unittest.main()
PY

cat > tests/test_inventaire.py <<'PY'
import unittest

from src import inventaire


class TestInventaire(unittest.TestCase):
    def test_nombre_articles(self):
        self.assertEqual(inventaire.nombre_articles([{}, {}]), 2)


if __name__ == "__main__":
    unittest.main()
PY

cat > plan.md <<'DOC'
# Plan — Valeur du stock

**Statut** : valide

## Objectif

Pouvoir connaître la valeur totale d'un stock d'articles.

## Exécution

### Étape 1 — `valeur_stock`

- Fichiers : `src/inventaire.py`, `tests/test_inventaire.py`.
- Ajouter `valeur_stock(articles)` dans `src/inventaire.py` : somme, sur tous
  les articles, de `prix` × quantité disponible (`stock.disponible`).
- Ajouter le test correspondant dans `tests/test_inventaire.py` : deux articles
  `{"prix": 2.0, "quantite": 3}` et `{"prix": 5.0, "quantite": -1}` valent 6.0.
- Preuve : `python3 -m unittest tests.test_inventaire`
DOC

git add -A
git commit -q -m "chore: état de départ"

# Journal de l'essai (voir la doc « tester-un-skill ») : un hook post-commit,
# exécuté même sous --no-verify, ajoute à .evals/commits.log le sujet de
# chaque commit, ses fichiers et l'état de l'arbre. Il n'écrit rien d'autre.
printf '.evals/\n' >> .git/info/exclude
cat > .git/hooks/post-commit <<'HOOK'
#!/bin/sh
racine=$(git rev-parse --show-toplevel) || exit 0
mkdir -p "$racine/.evals"
{
  printf 'COMMIT %s | %s\n' "$(git rev-parse --short HEAD)" "$(git log -1 --format=%s)"
  printf 'FILES: %s\n' "$(git diff-tree --root --no-commit-id --name-only -r HEAD | tr '\n' ' ' | sed 's/ $//')"
  printf 'STATUS: %s\n' "$(git status --porcelain | tr '\n' ';')"
} >> "$racine/.evals/commits.log"
exit 0
HOOK
chmod +x .git/hooks/post-commit
