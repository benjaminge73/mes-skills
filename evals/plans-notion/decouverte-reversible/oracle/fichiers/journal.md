# Journal d'exécution

### Étape 1 — `valeur_stock`

Fait : `valeur_stock` dans `src/inventaire.py`, test ajouté. Commit 3f9a1c2.
Découvertes : découverte — trouvable au plan (src/stock.py:11) : `en_rupture` compare avec `< 0`, un test existant échoue ; traité en D1.

### Étape D1 — `en_rupture` et la quantité nulle

Fait : `<` devient `<=` dans `src/stock.py`. Commit 8b4e07d, séparé de l'étape 1.
Découvertes : aucune
