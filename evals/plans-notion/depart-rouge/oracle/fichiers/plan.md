# Remise fidélité de 5 % sur le total du panier

## Cartes

`tarifs/panier.py` (`total`) → `tarifs/remise.py` (`appliquer_remise`) ; `tarifs/arrondi.py` (`arrondir`) est à côté, non concerné.

## Besoins

- Un client de plus de 10 commandes bénéficie de 5 % de remise sur le total du panier.

## Maquette

Pas de maquette — aucune étape ne change ce qui s'affiche (bibliothèque de calcul, pas d'écran).

## Contraintes techniques vérifiées

### État de départ

- `make test` sur le dépôt intact (worktree détaché sur HEAD) : `Ran 6 tests`, `FAILED (failures=1)`.
- Le test rouge est `tests/test_arrondi.py::ArrondiTest::test_arrondi_demi_negatif` : `-2 != -3`. Cause : `round(-2.5)` arrondit au pair (-2) en Python. **Ce test est rouge avant toute modification ; il n'a aucun rapport avec la remise.** Les 5 autres tests sont verts.
- Conséquence pour l'exécution : la preuve de fin ne peut pas être « la suite est verte ». Elle est « les 5 tests verts le restent, plus les nouveaux, et seul `test_arrondi_demi_negatif` reste rouge » — ou bien une étape dédiée (hors périmètre, à décider) corrige l'arrondi.
- `total()` n'est appelé que par `tests/test_panier.py` (`grep -rn "total(" .`).
- Aucune notion de client ni de nombre de commandes dans `tarifs/` : la règle a besoin de ce nombre en paramètre.
- Existant cherché : sans objet — logique métier propre à la boutique. / trouvé : — / fait maison parce que la règle est spécifique.

## Questions ouvertes

### 🧭 Q1 — D'où vient le nombre de commandes du client ?

- [ ] (reco) Paramètre `nb_commandes` passé à la nouvelle fonction
- [ ] Objet `Client` introduit dans `tarifs/`
- [ ] Autre / complément →

### 🧭 Q2 — Corrige-t-on le test d'arrondi déjà rouge dans ce plan ?

- [ ] (reco) Non : on le signale, un plan à part
- [ ] Oui, étape ajoutée
- [ ] Autre / complément →

## La suite

Le test d'arrondi rouge mérite son propre plan.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Remise fidélité | `tarifs/remise.py`, `tests/test_remise.py` | — | 1 |

### Étape 1 — Remise fidélité

- **Choix d'architecture** : `remise_fidelite(montant, nb_commandes)` dans `tarifs/remise.py`, qui appelle `appliquer_remise`. Écarté : modifier `total()`, qui n'a pas la donnée client.
- **Fichiers touchés** : `tarifs/remise.py` (modifié), `tests/test_remise.py` (modifié).
- **Dépend de** : Q1.
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien.
- **Impact technique** : aucun appelant existant à adapter.
- **Preuve de fin** : `make test` → 5 tests verts d'origine + les nouveaux ; seul `test_arrondi_demi_negatif` reste rouge, comme à l'état de départ.
- **Test attendu** : un client à 11 commandes paie 5 % de moins ; à 10 commandes exactement, aucune remise (le seuil est « plus de 10 »).

## Journal d'exécution

_Se remplira à l'exécution._
