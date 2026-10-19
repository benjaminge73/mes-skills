# Compter les notes par étiquette

## Cartes

`notes/commandes.py` (commandes) → `notes/stockage.py` (fichier `notes.json`) ; tests dans `tests/test_commandes.py`.

## Besoins

- Une commande `compter` donne le nombre de notes par étiquette.

## Maquette

Pas de maquette — outil en ligne de commande, sans écran ; la sortie est une ligne `étiquette : nombre` par étiquette.

## Contraintes techniques vérifiées

- `notes/commandes.py:11` : `ajouter` écrit `etiquettes` comme liste (`grep -n etiquettes notes/`).
- `notes/commandes.py:6` : la docstring de `lister` dit « triées par date » alors que le tri est par titre.

## Questions ouvertes

Aucune.

## La suite

- Export CSV des notes : porté par le plan `plan-export.md`, étape 1, pas ici.
- Ranger les notes dans une base SQLite plutôt que dans `notes.json` : trop gros pour ce plan (il change le stockage et migre les données), c'est un plan à part, à ouvrir quand tu veux.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Commande `compter` | `notes/commandes.py`, `tests/test_commandes.py` | — | 1 |
| 2 — Docstring de `lister` | `notes/commandes.py` | 1 | 2 |

### Étape 1 — Commande `compter`

- **Fichiers touchés** : `notes/commandes.py` (modifié), `tests/test_commandes.py` (modifié).
- **Preuve de fin** : `python3 -m unittest`

### Étape 2 — Docstring de `lister`

- **Fichiers touchés** : `notes/commandes.py` (modifié).
- **Preuve de fin** : la docstring dit « triées par titre ».

_maj 2026-10-19 — ajouté depuis « La suite » parce que réversible, hors sécurité et d'une étape._
