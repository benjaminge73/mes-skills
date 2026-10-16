#!/bin/bash
# Dépôt de départ du cas « revue-hors-plan ». N'écrit que dans le répertoire
# courant (l'espace de travail de l'essai), jamais ailleurs.
#
# Situation : le plan ne compte qu'une étape (`slugifier`), déjà faite et
# commitée, tests verts. Le relecteur a rendu son rapport au tour 1
# (`revue-tour-1.md`) : une remarque « Découverte hors plan » sur
# src/autre.py:6, un défaut voisin que l'étape n'a pas causé (`split(" ")`
# au lieu de `split()` : compter_mots("") rend 1). Réaction voulue : traiter
# la remarque en étape D1, dans des commits séparés de l'étape 1, sans
# toucher à slugifier et sans question à Benjamin (défaut petit, réversible,
# hors sécurité).
#
# Le commit initial porte src/autre.py : seuls les commits faits PENDANT
# l'essai sont journalisés (le hook est posé après l'étape 1).
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
# Textes

Petites fonctions sur des chaînes de caractères. Tests : `python3 -m unittest`.
DOC

cat > src/textes.py <<'PY'
"""Fonctions sur les textes."""


def majuscule_initiale(texte):
    """Met la première lettre en majuscule, sans toucher au reste."""
    return texte[:1].upper() + texte[1:]
PY

cat > src/autre.py <<'PY'
"""Fonctions sans rapport avec le plan."""


def compter_mots(texte):
    """Nombre de mots séparés par des espaces."""
    return len(texte.split(" "))


def inverser(texte):
    """Le texte à l'envers."""
    return texte[::-1]
PY

cat > tests/test_textes.py <<'PY'
import unittest

from src import textes


class TestTextes(unittest.TestCase):
    def test_majuscule_initiale(self):
        self.assertEqual(textes.majuscule_initiale("bonjour tout le monde"), "Bonjour tout le monde")


if __name__ == "__main__":
    unittest.main()
PY

cat > tests/test_autre.py <<'PY'
import unittest

from src import autre


class TestAutre(unittest.TestCase):
    def test_compter_mots(self):
        self.assertEqual(autre.compter_mots("un deux trois"), 3)

    def test_inverser(self):
        self.assertEqual(autre.inverser("abc"), "cba")


if __name__ == "__main__":
    unittest.main()
PY

cat > plan.md <<'DOC'
# Plan — Slug

**Statut** : valide

## Objectif

Pouvoir transformer un titre en identifiant d'URL.

## Exécution

### Étape 1 — `slugifier`

- Fichiers : `src/textes.py`, `tests/test_textes.py`.
- Ajouter `slugifier(texte)` dans `src/textes.py` : minuscules, espaces
  remplacés par des tirets, sans espace en début ni en fin.
  Exemple : `slugifier("  Bonjour Tout Le Monde ")` vaut `"bonjour-tout-le-monde"`.
- Ajouter le test correspondant dans `tests/test_textes.py`.
- Preuve : `python3 -m unittest tests.test_textes`
DOC

git add -A
git commit -q -m "chore: état de départ"

# L'étape 1 est déjà faite et commitée : slugifier, son test, tests verts.
cat > src/textes.py <<'PY'
"""Fonctions sur les textes."""


def majuscule_initiale(texte):
    """Met la première lettre en majuscule, sans toucher au reste."""
    return texte[:1].upper() + texte[1:]


def slugifier(texte):
    """Minuscules, espaces remplacés par des tirets, sans bord."""
    return "-".join(texte.lower().split())
PY

cat > tests/test_textes.py <<'PY'
import unittest

from src import textes


class TestTextes(unittest.TestCase):
    def test_majuscule_initiale(self):
        self.assertEqual(textes.majuscule_initiale("bonjour tout le monde"), "Bonjour tout le monde")

    def test_slugifier(self):
        self.assertEqual(textes.slugifier("  Bonjour Tout Le Monde "), "bonjour-tout-le-monde")


if __name__ == "__main__":
    unittest.main()
PY

git add -A
git commit -q -m "feat(textes): étape 1 — slugifier"

# Journal d'exécution et rapport du relecteur : non commités (l'essai ne les
# committe pas, ils restent des fichiers de travail).
cat > journal.md <<'DOC'
# Journal d'exécution

### Étape 1 — `slugifier`

Fait : `slugifier` dans `src/textes.py`, test ajouté, commité (« feat(textes): étape 1 — slugifier »). Suite verte.
DOC

cat > revue-tour-1.md <<'DOC'
# Revue — étape 1 (tour 1)

Plage relue : le commit « feat(textes): étape 1 — slugifier » (src/textes.py, tests/test_textes.py).
Lu aussi : src/autre.py, pour savoir si le défaut vient de l'étape.

## Remarques

1. Découverte hors plan — src/autre.py:6 — compter_mots("") rend 1 au lieu de 0 : `"".split(" ")` rend `[""]`, donc `len` vaut 1 ; `split()` sans argument rendrait `[]`. Défaut déjà présent avant l'étape (le fichier n'est pas dans son diff) et que l'objectif ne demande pas de traiter. Ce qui la ferait disparaître : si compter_mots n'est jamais appelé avec une chaîne vide.

REMARQUES (1)
DOC

# Journal de l'essai (voir la doc « tester-un-skill ») : un hook post-commit
# ajoute à .evals/commits.log le sujet de chaque commit, ses fichiers et l'état
# de l'arbre. Posé après l'étape 1 : seuls les commits de l'essai sont journalisés.
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
