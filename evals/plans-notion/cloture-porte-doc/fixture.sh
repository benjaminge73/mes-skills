#!/usr/bin/env bash
# Dépôt de départ du cas cloture-porte-doc : un dépôt factice (suite « python3 -m unittest »,
# un test de socle) dont le plan « Documenter le socle » est à la clôture. Son étape unique
# est faite sur la branche feat/porte-doc, poussée sur origin.git/ (dépôt nu, ignoré par git).
# Le miroir de la page du plan (plan.md) n'a PAS de Récap : la porte (doc-de-cloture.py
# --porte) sort en code 1. Le projet est à doc vivante activée (projet.md). Le miroir du
# Changelog (changelog.md) ne cite que la PR 11 : la PR 12 n'a pas d'entrée. La fixture ne
# lance ni la clôture ni le script. Les fichiers sont fixes, sans aléa. N'écrit que dans le
# répertoire courant.
set -euo pipefail

export GIT_AUTHOR_NAME=Fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
export GIT_COMMITTER_NAME=Fixture GIT_COMMITTER_EMAIL=fixture@example.invalid

valider() {
  git -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "$1"
}

mkdir -p tests docs

cat > .gitignore <<'EOF'
__pycache__/
*.pyc
origin.git/
EOF

touch tests/__init__.py
cat > tests/test_socle.py <<'EOF'
import unittest


class TestSocle(unittest.TestCase):
    def test_socle(self):
        self.assertEqual(1 + 1, 2)


if __name__ == "__main__":
    unittest.main()
EOF

cat > projet.md <<'EOF'
# Projet depot-factice (miroir de la page Projet)

📘 Doc vivante : activée
📘 Rétro-doc : faite 2026-10-01
EOF

cat > changelog.md <<'EOF'
# Changelog

## 2026-10-10 · Plan précédent
Plan : lien · PR : #11 · Statut : execute

### ✨ Nouveau
- Le socle de test tourne sous unittest (Étape 1)

### 🔧 Amélioré
- rien

### 🐛 Corrigé
- rien

### ⏭️ Reste à faire
- rien

<toggle>Côté technique
	Le socle n'a qu'un test.
</toggle>
EOF

cat > plan.md <<'EOF'
# [Plan] Documenter le socle

**Statut** : en cours
**Branche** : `feat/porte-doc`
**PR** : #12

## Objectif

Ajouter une ligne de documentation au socle du dépôt.

## Exécution

### Étape 1 — documenter le socle (faite)

- **Fichiers touchés** : `docs/socle.md`.
- **Preuve de fin** : `python3 -m unittest`, vert.

## Journal d'exécution

### Étape 1 — faite

Commit « docs(socle): étape 1 » sur `feat/porte-doc`. Preuve : suite verte.

L'étape est faite, la suite complète est verte sur la branche. Reste la clôture.
EOF

git init -q -b main
git add -A
valider "depot-factice : socle, plan en cours, étape faite"
git init -q --bare origin.git
git remote add origin origin.git
git push -q -u origin main

git checkout -q -b feat/porte-doc
cat > docs/socle.md <<'EOF'
# Le socle

Le socle du dépôt a un test, lancé par `python3 -m unittest`.
EOF
git add docs/socle.md
valider "docs(socle): étape 1 — la ligne de documentation du socle"
git push -q -u origin feat/porte-doc
