# [Plan] notes - Commande compter

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
- Reste à trier, chaque reste avec sa ligne (`lignes.md`) :
  - Mesurer le taux d'erreur de `compter` en usage réel : attend un événement ; propriétaire Benjamin. La ligne qui la porte (type `suivi`) est citée ici, son déclencheur reste dans la base.
  - Auto-fix de la PR : propriétaire Benjamin ; ligne « Activer l'auto-fix dans la barre de la PR » (type `geste`).
  - Ancien format v1 de `notes.json` : question posée à Benjamin (`question.md`), sans réponse ; ligne « Garder ou supprimer la lecture de l'ancien format v1 » (type `décision`), propriétaire Benjamin.
