Étape 1 faite : `src/facture_h.py` et son test, commités, avec `TAUX_TVA = 0.20`.

En prenant `facture_g.py` pour modèle, j'ai vu que sa constante vaut `0.02` alors que le commentaire et le README disent 20 %. C'est la même dans les sept modules `facture_a` à `facture_g` : la corriger touche sept fichiers, bien au-delà de ce qu'une étape D absorbe. Je n'y ai pas touché.

Question pour Benjamin : corrige-t-on ce taux dans les sept gabarits, dans un plan de suite dédié, ou le centralise-t-on dans un seul module de constantes ?

VERIFICATIONS:
- python3 -m unittest tests.test_facture_h -> OK (1 test)
- python3 -m unittest (suite complète) -> OK (2 tests)
DECOUVERTES:
- découverte — trouvable au plan (src/facture_g.py:3) : TAUX_TVA = 0.02 au lieu de 0.20, recopié dans facture_a à facture_g (7 fichiers) ; hors d'une étape D, question posée
