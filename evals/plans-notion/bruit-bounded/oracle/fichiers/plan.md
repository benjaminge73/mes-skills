# Option `--version` du CLI

## Cartes

`convertisseur/__main__.py` (argparse) ← `pyproject.toml` (version `1.2.0`).

## Besoins

- `python -m convertisseur --version` affiche le numéro de version de `pyproject.toml`.

## Maquette

Pas de maquette — aucune étape ne change un écran ; la sortie est une ligne de terminal.

## Contraintes techniques vérifiées

- État de départ : `python -m unittest discover -s tests` → 2 tests, OK.
- La version vit dans `pyproject.toml:3` (`1.2.0`). Le paquet n'est pas installé dans ce dépôt : lire `importlib.metadata.version("convertisseur")` échouerait hors installation.
- Existant cherché : sans objet — option standard d'argparse. / trouvé : `action="version"` de la bibliothèque standard. / fait maison parce que — rien à fabriquer.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Option `--version` | `convertisseur/__main__.py`, `tests/test_version.py` | — | 1 |

### Étape 1 — Option `--version`

- **Choix d'architecture** : `parseur.add_argument("--version", action="version", version=...)`, la valeur lue dans `pyproject.toml` avec `tomllib` (Python 3.11) ou, pour 3.9, une lecture directe de la ligne `version`. Écarté : recopier le numéro en dur, qui divergerait.
- **Fichiers touchés** : `convertisseur/__main__.py` (modifié), `tests/test_version.py` (créé).
- **Dépend de** : —
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien à l'écran ; une option de plus en ligne de commande.
- **Impact technique** : aucun.
- **Preuve de fin** : `python -m convertisseur --version` affiche `1.2.0` et la suite reste verte.
- **Test attendu** : la version affichée est celle de `pyproject.toml` ; elle change si on la change.

## Journal d'exécution

_Se remplira à l'exécution._
