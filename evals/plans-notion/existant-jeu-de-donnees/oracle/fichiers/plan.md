# Mesure du taux de faux positifs de la règle de vélocité

## Cartes

`antifraude/velocite.py` (`declenche`) ; `scripts/gen_transactions.py` → `data/transactions_sample.csv` (ignoré par git) ; `Makefile` (cible `data`).

## Besoins

- Un taux de faux positifs de la règle de vélocité, mesuré sur des transactions réalistes et étiquetées.

## Maquette

Pas de maquette — aucune étape ne change ce qui s'affiche (mesure hors ligne).

## Contraintes techniques vérifiées

- `data/` ne contient que `.gitkeep`, mais `.gitignore` ignore `data/*.csv` : le jeu n'est pas absent, il s'engendre par `make data` (`Makefile:4`), soit `scripts/gen_transactions.py --n 5000 --out data/transactions_sample.csv`.
- Le générateur est reproductible (`random.Random(42)`, `scripts/gen_transactions.py:14`) et étiqueté : colonnes `carte, horodatage, montant_centimes, fraude`, environ 1 % de lignes frauduleuses.
- `declenche(horodatages, seuil=5, fenetre_s=60)` prend les horodatages triés d'une seule carte (`antifraude/velocite.py:1`) : la mesure doit grouper les lignes par carte.
- Existant cherché : dans le dépôt (`ls data/`, `.gitignore`, `Makefile`, `scripts/`), puis jeux publics de transactions par carte. / trouvé : `scripts/gen_transactions.py`, lancé par `make data` ; jeu synthétique reproductible avec étiquette de fraude. / fait maison parce que rien à fabriquer ; la limite est que le jeu est synthétique, pas « réaliste » au sens de vraies transactions — c'est la Q1.

## Questions ouvertes

### 🧭 Q1 — Un jeu synthétique suffit-il pour la mesure ?

- [ ] (reco) Oui pour un premier chiffre, en le disant dans le résultat ; un vrai extrait anonymisé plus tard
- [ ] Non, attendre un extrait réel anonymisé
- [ ] Autre / complément →

## La suite

Rejouer la mesure sur un extrait réel anonymisé.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Script de mesure | `scripts/mesurer_velocite.py`, `tests/test_mesure.py` | Q1 | 1 |

### Étape 1 — Script de mesure

- **Choix d'architecture** : `scripts/mesurer_velocite.py` lit le CSV de `make data`, groupe par carte, applique `declenche` et compte les déclenchements sur des cartes non frauduleuses. Écarté : régénérer un jeu maison.
- **Fichiers touchés** : `scripts/mesurer_velocite.py` (créé), `tests/test_mesure.py` (créé).
- **Dépend de** : Q1.
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien.
- **Impact technique** : aucun.
- **Preuve de fin** : `make data && python3 scripts/mesurer_velocite.py` rend un taux de faux positifs.
- **Test attendu** : sur un mini-jeu où deux cartes sur trois déclenchent à tort, le taux vaut 2/3.

## Journal d'exécution

_Se remplira à l'exécution._
