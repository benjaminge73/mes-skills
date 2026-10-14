La clôture est faite. Suite complète jouée en local : `python3 -m unittest`, 2 tests OK. Branche `feat/export-csv` poussée. PR #48 ouverte vers `main`, prête (pas en brouillon), avec `gh pr create`. Je ne l'ai pas mergée : le merge revient à la CI (merge-auto), et ce dépôt n'a pas le label review-required. Statut posé à « a merger » dans `plan.md` ; il passera à « execute » quand le merge sera vu sur `main`.

VERIFICATIONS:
- `python3 -m unittest` -> 2 tests OK
- `git push -u origin feat/export-csv` -> branche à jour sur origin
- `gh pr create` (sans --draft) -> PR #48 ouverte vers main
- `plan.md`, Statut -> « a merger »

DECOUVERTES:
- aucune
