Étape 1 faite : `valeur_stock` est dans `src/inventaire.py`, testée, commitée.

En lançant la suite complète, un test déjà présent échouait : `stock.en_rupture` comparait la quantité avec `< 0` au lieu de `<= 0`. Une ligne, réversible, dans un module voisin qui n'est pas dans le périmètre de l'étape : je l'ai traitée en étape D1, dans un commit séparé de l'étape 1.

VERIFICATIONS:
- python3 -m unittest tests.test_inventaire -> OK (2 tests)
- python3 -m unittest (suite complète) -> OK (6 tests) après l'étape D1
DECOUVERTES:
- découverte — trouvable au plan (src/stock.py:11) : en_rupture ne voyait pas la quantité nulle (`< 0`) ; corrigé en étape D1, commit séparé
