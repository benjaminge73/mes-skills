- [x] C0 Objets touchés — preuve : `SEUIL` et `appliquer_remise` (`src/remise.py:3`, `:7-11`) ; `total_panier` (`caisse/panier.py:4-5`) ; `tests/test_remise.py`, `tests/test_panier.py` ; `CLAUDE.md:3`, `docs/remise.md:3`
- [x] C1 Consommateurs — preuve : `Grep "appliquer_remise" .` → `src/remise.py:7`, `caisse/panier.py:1,5` (appelant direct, dans la carte), `tests/test_remise.py:8,11,14` (direct) ; `Grep "total_panier" .` → `caisse/panier.py:4`, `tests/test_panier.py:3,8` (consommateur de `appliquer_remise`, hors de la carte)
- [x] C2 Docs et consignes qui le citent — preuve : `CLAUDE.md:3` (« SEUIL = 100 », et « ne le change pas sans mettre à jour docs/remise.md ») ; `docs/remise.md:3` (« au-delà de 100 € », devient faux après le changement)
- [x] C3 Gardes, CI et règles — preuve : `CLAUDE.md:3` (règle écrite : seuil et doc liés) ; `scripts/ci_locale.sh:3` lance `python3 -m unittest discover -s tests`, sans valeur figée ; `Glob .github/**` → 0 fichier
- [x] C4 L'état vivant — preuve : `Glob cron/**`, `Glob **/jobs.json`, `Glob **/*.service` → 0 fichier ; aucun état déployé ne lit le seuil
- [x] C5 Le brief contre le code — preuve : `src/remise.py:7-11` lue en entier : `appliquer_remise(montant)` n'a pas de paramètre de taux ; le taux est la constante `TAUX` (`src/remise.py:4`), le seuil `SEUIL` (`src/remise.py:3`) ; la carte est juste : `caisse/panier.py:5` appelle bien la fonction
- [ ] C6 Contrat d'un outil externe — sans objet : le changement n'appelle aucun outil ni service externe
- [x] C7 Une valeur à plusieurs endroits — preuve : `Grep "100" src/ docs/ tests/ CLAUDE.md` → `src/remise.py:3` (`SEUIL = 100`), `src/remise.py:8` (docstring « 100 € »), `tests/test_remise.py:7,10,13` (noms de tests), `tests/test_remise.py:11` (assertion), `CLAUDE.md:3`, `docs/remise.md:3`
- [x] C8 Tests existants — preuve : `tests/test_remise.py:7-14` (direct) : figent 180 pour 200, 100 pour 100, 50 pour 50 ; à 150 € de seuil, ces assertions passent encore, mais leurs noms (l.7, l.10, l.13) citent 100 € et deviennent faux ; `tests/test_panier.py:8` (consommateur) : `total_panier([120])` attend 108, ce qui casse à 150 €
- [x] C9 Défauts voisins — preuve : aucun défaut vu dans `appliquer_remise` ni `total_panier` (lues en entier) ; absence notée : aucun contrôle de montant négatif (`src/remise.py:7-11`), hors du périmètre du changement
- [ ] C10 Données réelles — sans objet : le brief ne dépend d'aucun volume ni compte
- [x] C11 Historique et décisions antérieures — preuve : `git log --oneline` → un seul commit du dépôt ; `CLAUDE.md:3` est la seule décision écrite (seuil et doc liés)
- [x] C12 Sécurité — preuve : rien de touché (ni secret, ni droit, ni exposition)

# Couverture

Le dépôt est indexé par le graphe, branche `main` comme branche de travail. Hors graphe : `docs/`, `scripts/`, `CLAUDE.md` et les tests, lus par `Grep`.

# Faits vérifiés

- `src/remise.py:3` : `SEUIL = 100` ; `src/remise.py:4` : `TAUX = 0.10` ; `src/remise.py:7-11` : `appliquer_remise(montant)` lue en entier, sans paramètre de taux.
- `caisse/panier.py:5` : `total_panier` appelle `appliquer_remise(sum(lignes))`, appelant direct (`trace_path(direction=inbound) → 1 appelant`, confirmé par `Grep`).
- `tests/test_panier.py:8` : `total_panier([120])` attend 108 ; consommateur de `appliquer_remise`, hors de la carte du brief.
- `tests/test_remise.py:7-14` : trois tests directs sur `appliquer_remise`.
- `CLAUDE.md:3` et `docs/remise.md:3` : le seuil de 100 € est écrit en deux endroits qui devront suivre.
- `scripts/ci_locale.sh:3` : la suite se lance par `python3 -m unittest discover -s tests`.

# Hypothèses

- Un seuil de 150 € ferait échouer `tests/test_panier.py:8` (120 € ne serait plus remisé) : déduit de la règle `montant > SEUIL`, non joué.

# Non vérifié

- La suite de tests n'est pas jouée : l'enquêteur n'a pas `Bash`.

# Chiffres remesurés

Aucun chiffre repris d'un plan antérieur.
