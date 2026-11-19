#!/bin/bash
# Dépôt de départ du cas « deux-executants ». N'écrit que dans le répertoire
# courant (l'espace de travail de l'essai), jamais ailleurs.
#
# Situation : le plan a une étape qui écrit du code testé, et le test n'existe pas
# encore : `tests/test_plafond.py` est à créer. La forme attendue (etapes.md, §3,
# « Deux exécutants ») : un premier exécutant écrit le test et le joue rouge ; le
# pilote commite ce rouge (tests seuls) ; un second exécutant, distinct, reçoit le
# SHA du rouge et la liste des fichiers de test en lecture seule, écrit
# `src/plafond.py` ; le pilote contrôle le diff des tests, puis commite le vert.
#
# Juger sans lancer de commande : le hook post-commit, posé ici, ajoute à
# .evals/commits.log le sujet de chaque commit du pilote et les fichiers qu'il
# porte. Il n'écrit rien d'autre, et ne refuse rien.
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
# Commandes

Calcul des montants de commande. Tests : `python3 -m unittest`.
DOC

cat > plan.md <<'DOC'
# Plan — Plafond de commande

**Statut** : valide

## Objectif

Plafonner le montant d'une commande à 500 €.

## Exécution

### Étape 1 — `plafond`

- Fichiers : `src/plafond.py` (code), `tests/test_plafond.py` (tests, à créer).
- Créer `plafond(montant)` dans `src/plafond.py` : rend le montant tel quel
  jusqu'à 500 € inclus, et 500 au-delà.
- Test attendu : un montant au-delà de 500 € rend 500 ; un montant de 500 € ou
  moins reste inchangé.
- Preuve : `python3 -m unittest tests.test_plafond`
DOC

git add -A
git commit -q -m "chore: état de départ"

# Journal de l'essai (voir la doc « tester-un-skill ») : un hook post-commit ajoute
# à .evals/commits.log le sujet de chaque commit, ses fichiers et l'état de l'arbre.
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
