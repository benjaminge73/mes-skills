Contrôle de fraîcheur joué : `fraicheur-depot.py --appliquer` rebase `feat/export` sur `origin/master` (2 commits repris), puis push.

VERIFICATIONS:
- `fraicheur-depot.py --appliquer` -> « Remise à jour » : branche rebasée sur origin/master
- `git push -u origin feat/export` -> poussé
