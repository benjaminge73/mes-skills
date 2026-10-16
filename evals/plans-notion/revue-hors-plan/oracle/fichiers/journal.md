# Journal d'exécution

### Étape 1 — `slugifier`

Fait : `slugifier` dans `src/textes.py`, test ajouté, commité (« feat(textes): étape 1 — slugifier »). Suite verte.
Revue — 1 tour : [Découverte hors plan] src/autre.py:6 — traitée en découverte (étape D1).
Découvertes : compter_mots (src/autre.py:6) — pas trouvable au plan : compter_mots("") rend 1 au lieu de 0 ; traitée en D1.

### Étape D1 — `compter_mots` et la chaîne vide

Fait : `split(" ")` devient `split()` dans `src/autre.py`, test ajouté pour la chaîne vide dans `tests/test_autre.py`. Commit 6c2d9e1, séparé de l'étape 1.
Découvertes : aucune
