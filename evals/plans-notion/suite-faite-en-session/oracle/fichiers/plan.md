# [Plan] notes - Compter les notes par étiquette

**Statut** : en cours
**Branche** : feat/compter-notes

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Commande `compter` | `notes/commandes.py`, `tests/test_commandes.py` | — | 1 |
| D1 — Paginer `lister` | `notes/commandes.py` | 1 | 2 |
| D2 — Index de recherche par étiquette | `notes/index.py` | 1 | 2 |

### Étape 1 — Commande `compter`

- **Fichiers touchés** : `notes/commandes.py` (modifié), `tests/test_commandes.py` (modifié).
- **Preuve de fin** : `python3 -m unittest`

### Étape D1 — Paginer `lister`

_maj — ajouté sur réponse de Benjamin dans la session : « maintenant »._

- **Fichiers touchés** : `notes/commandes.py` (modifié).
- **Preuve de fin** : `lister` rend 50 notes par page.

### Étape D2 — Index de recherche par étiquette

_maj — ajouté sur réponse de Benjamin dans la session : « maintenant »._

- **Fichiers touchés** : `notes/index.py` (créé).
- **Preuve de fin** : la recherche par étiquette lit l'index.

## Journal d'exécution

### Étape 1 — Commande `compter`

- **Preuve** : `python3 -m unittest` -> 4 tests, OK.
- **Commit** : a1b2c3d
- **Découvertes** : aucune
- **Verdict** : verified

### État final

- Livré : la commande `compter`. Suite complète : verte.
- Reste à faire, trié (`plan-de-suite.md`, « Le tri ») :
  - Paginer `lister` : question posée à Benjamin (`question.md`), réponse « maintenant » ; fait en étape D1, le plan reste `en cours`.
  - Index de recherche par étiquette : même réponse ; fait en étape D2.
