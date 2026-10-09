# Export du journal des commandes vers le reporting

## Cartes

`data/commandes.csv` (journal) ; `docs/export.md` (seuil) ; `export/exporter.py` (`exporter_unique`, stub).

## Besoins

- Le reporting importe le journal des commandes depuis `data/commandes.csv`.

## Maquette

Pas de maquette : aucune étape ne change ce qui s'affiche.

## Contraintes techniques vérifiées

- Enregistrements dans `data/commandes.csv` : 1843 (sondeur, `tail -n +2 data/commandes.csv | wc -l` → 1843, en-tête exclu).
- Seuil écrit dans `docs/export.md` : au-delà de 2 000 enregistrements, export paginé ; en deçà, export unique.

## Décision

- Décision : export unique, car 1 843 enregistrements est sous le seuil de 2 000 (`docs/export.md`). L'export paginé ne s'impose qu'au-delà de ce seuil.

## Exécution

### Étape 1 — Export unique

- **Fichiers touchés** : `export/exporter.py` (à écrire après validation).
- **Preuve de fin** : l'import du reporting lit le fichier unique sans erreur.
- **Test attendu** : `exporter_unique` écrit 1843 lignes de données plus l'en-tête.

## Journal d'exécution

_Se remplira à l'exécution._
