# [Plan] notes - Compter les notes par étiquette

**Statut** : en cours
**Branche** : feat/compter-notes

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Commande `compter` | `notes/commandes.py`, `tests/test_commandes.py` | — | 1 |
| 2 — Documenter `compter` | `README.md` | 1 | 2 |

### Étape 1 — Commande `compter`

- **Fichiers touchés** : `notes/commandes.py` (modifié), `tests/test_commandes.py` (modifié).
- **Preuve de fin** : `python3 -m unittest`

### Étape 2 — Documenter `compter`

- **Fichiers touchés** : `README.md` (modifié).
- **Preuve de fin** : le README liste `compter`.

## Journal d'exécution

### Étape 1 — Commande `compter`

- **Preuve** : `python3 -m unittest` -> 4 tests, OK.
- **Commit** : a1b2c3d
- **Découvertes** : aucune
- **Verdict** : verified

### Étape 2 — Documenter `compter`

- **Preuve** : `grep compter README.md` -> 1 ligne.
- **Commit** : d4e5f6a
- **Découvertes** : aucune
- **Verdict** : verified

### État final

- Livré : la commande `compter` et sa ligne dans le README. Suite complète : verte.
- Reste à faire, trié (`plan-de-suite.md`, « Le tri ») :
  - Ancien format v1 : question posée à Benjamin dans la session (`question.md`), réponse notée ici quand elle arrive.
  - SQLite, pagination de `lister`, index de recherche : plus d'une étape au total, proposés à Benjamin dans la session (`question.md`, question 2) ; sans réponse, portés par le plan de suite `plan-suite.md` (#2).
  - Mesurer le taux d'erreur de `compter` en usage réel : attend un événement, le relevé à 30 jours ; propriétaire Benjamin.
