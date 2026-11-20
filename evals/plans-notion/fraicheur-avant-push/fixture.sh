#!/usr/bin/env bash
# Dépôt de départ du cas fraicheur-avant-push : un dépôt dont la branche principale
# distante est « master » (origin.git/, ignoré par git), en avance de deux commits sur
# la branche feat/export, qui porte un commit propre. Rien n'est poussé par la fixture.
# N'écrit que dans le répertoire courant.
set -euo pipefail
export GIT_AUTHOR_NAME=Fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
export GIT_COMMITTER_NAME=Fixture GIT_COMMITTER_EMAIL=fixture@example.invalid
valider() { git -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "$1"; }

printf '# depot-factice\nSuite : `python3 -m unittest`.\n' > README.md
printf 'origin.git/\nautre/\n' > .gitignore
git init -q -b master
git add -A; valider "depot-factice : départ"
git init -q --bare origin.git
git remote add origin origin.git
git push -q -u origin master
git checkout -q -b feat/export
printf 'def export():\n    return "csv"\n' > export.py
git add export.py; valider "feat: export"
# deux commits arrivent sur master côté distant, via un second clone
git clone -q origin.git autre
( cd autre && printf 'ligne 2\n' >> README.md && git add README.md && valider "docs: readme" \
  && printf 'LICENCE\n' > LICENCE && git add LICENCE && valider "chore: licence" && git push -q origin master )
rm -rf autre
