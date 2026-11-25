# Couverture

Le dépôt est indexé. Hors graphe : `docs/`, `scripts/`, `CLAUDE.md` et les tests.

# Faits vérifiés

- `caisse/panier.py:5` : `total_panier` appelle `appliquer_remise`.
- `src/remise.py:3` : `SEUIL = 100`.
- `CLAUDE.md:3` : le seuil est écrit en deux endroits.

# Hypothèses

- Un seuil de 150 € casse peut-être un test.

# Non vérifié

- La suite de tests n'est pas jouée.

# Chiffres remesurés

Aucun.
