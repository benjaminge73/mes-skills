La clôture est faite. Suite complète jouée en local : `python3 -m unittest`, 2 tests OK. Preuve doc : `qualite-doc.py lecteurs --base origin/main` lancé, un passage relevé dans README.md (il cite `calculer_total`, renommé par la branche). Passage traité dans la branche : README.md cite désormais `calculer_somme`. Branche poussée. PR ouverte vers `main`, prête (pas en brouillon). Statut posé à « a merger » dans `plan.md`.

VERIFICATIONS:
- `python3 -m unittest` -> 2 tests OK
- `qualite-doc.py lecteurs --base origin/main` -> 1 passage (README.md, ligne 6), traité
- `README.md` ne cite plus `calculer_total` -> vrai
- `git push -u origin feat/renommer-somme` -> branche à jour sur origin
- `plan.md`, Statut -> « a merger »

DECOUVERTES:
- aucune
