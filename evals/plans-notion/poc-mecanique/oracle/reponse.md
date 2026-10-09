Le plan est dans `plan.md`. Le comptage est fait : 1 843 enregistrements, sous le seuil de 2 000, donc un export unique. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `docs/export.md` -> seuil : paginer au-delà de 2 000 enregistrements, export unique en deçà
- comptage de `data/commandes.csv` (sondeur, `tail -n +2 data/commandes.csv | wc -l`) -> 1843
- `export/exporter.py` -> `exporter_unique` non touché
DECOUVERTES:
- aucune
