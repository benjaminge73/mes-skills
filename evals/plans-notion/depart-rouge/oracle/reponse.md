Le plan est dans `plan.md`. Point d'attention : la suite de tests est déjà rouge avant toute modification (un test d'arrondi), ce qui est noté dans « État de départ » pour qu'on ne le prenne pas pour une régression de la remise. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `make test` sur le dépôt intact -> Ran 6 tests, FAILED (failures=1) : `tests/test_arrondi.py::ArrondiTest::test_arrondi_demi_negatif` (-2 != -3)
- appelants de `total()` (grep -rn "total(") -> uniquement `tests/test_panier.py`
- le nombre de commandes d'un client existe-t-il dans le dépôt ? -> non, aucune notion de client ni de commande dans `tarifs/`
DECOUVERTES:
- suite déjà rouge : `test_arrondi_demi_negatif` échoue à HEAD (round(-2.5) donne -2, le test attend -3), sans rapport avec la remise
- pas de notion de client : la règle « plus de 10 commandes » a besoin d'une donnée que `tarifs/` ne porte pas
