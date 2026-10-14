# [Plan] Export CSV des notes

**Statut** : a merger
**Branche** : `feat/export-csv`

## Objectif

Exporter les notes en CSV (titre, date), entête compris, par le module `src/export.py`.

## Exécution

### Étape 1 — `exporter_csv` (faite)

- **Fichiers touchés** : `src/export.py`, `tests/test_export.py`.
- **Preuve de fin** : `python3 -m unittest tests.test_export`, vert.

### Étape 2 — Cas de la liste vide (faite)

- **Fichiers touchés** : `tests/test_export.py`.
- **Preuve de fin** : `python3 -m unittest tests.test_export`, vert.

## Journal d'exécution

### Étape 1 — faite

Commit « feat(export): étape 1 — exporter_csv » sur `feat/export-csv`. Preuve : test vert.

### Étape 2 — faite

Commit « feat(export): étape 2 — cas de la liste vide » sur `feat/export-csv`. Preuve : test vert.

### Remontée sur main — PR ouverte

PR #48 ouverte de `feat/export-csv` vers `main`, prête (pas en brouillon). CI en attente à la clôture ; merge non constaté sur `main`. Statut à « a merger » jusqu'à ce que le merge soit vu.
