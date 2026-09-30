Le plan est dans `plan.md`. Le jeu de données n'est pas à fabriquer : un générateur reproductible existe déjà (`make data`), et son CSV est ignoré par git, ce qui explique que `data/` paraisse vide. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `ls -a data/` -> seulement `.gitkeep`, aucun CSV versionné
- `.gitignore` -> `data/*.csv` ignoré
- `Makefile` -> cible `data` : `python3 scripts/gen_transactions.py --n 5000 --out data/transactions_sample.csv`
- ce que produit le générateur (lecture de `scripts/gen_transactions.py`) -> CSV `carte, horodatage, montant_centimes, fraude`, graine fixe 42, environ 1 % de lignes frauduleuses
- appelants de `declenche` -> `tests/test_velocite.py` seulement
DECOUVERTES:
- générateur existant : `scripts/gen_transactions.py` (lancé par `make data`) produit un jeu reproductible étiqueté (colonne `fraude`) ; le CSV est ignoré par git, d'où un dossier `data/` vide
