# [Plan] notes - Compter les notes par étiquette #2

**Statut** : brouillon
**Branche** : feat/compter-notes

## Reprise du plan #1

- **Fait** : étape 1 (commande `compter`), étape 2 (README).
- **Laissé de côté** : trois chantiers qui font plus d'une étape ensemble : ranger les notes dans une base SQLite (stockage et migration), paginer `lister` au-delà de 50 notes, refaire l'index de recherche par étiquette.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Stockage SQLite et migration | `notes/stockage.py` | — | 1 |
| 2 — Pagination de `lister` | `notes/commandes.py` | 1 | 2 |
| 3 — Index de recherche par étiquette | `notes/index.py` | 1 | 2 |
