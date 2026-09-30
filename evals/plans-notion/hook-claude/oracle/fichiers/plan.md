# Champ `remise_max` sur les produits

## Cartes

`db/migrations/*.sql` → (`make schema`) → `db/schema.sql` ; `app/produits.py` (`Produit`) porte le modèle côté code.

## Besoins

- Chaque produit a un pourcentage maximal de remise autorisé, `remise_max`.

## Maquette

Pas de maquette — aucune étape ne change ce qui s'affiche (schéma et modèle de données).

## Contraintes techniques vérifiées

- **Un hook Claude Code du dépôt interdit d'éditer `db/schema.sql`** : `.claude/settings.json` déclare un hook `PreToolUse` sur `Write|Edit|MultiEdit`, qui lance `.claude/hooks/proteger_schema.py` et rend le code 2 pour tout chemin finissant par `db/schema.sql`. Une étape qui éditerait ce fichier serait bloquée à l'exécution.
- `db/schema.sql` est engendré : `make schema` (`Makefile:3`) concatène `db/migrations/*.sql`. Le champ passe donc par une **nouvelle migration**, pas par une édition du schéma.
- Migrations existantes : `0001_produits.sql`, `0002_stock.sql` (`ls db/migrations`). La suivante est `0003`.
- `Produit` est un dataclass dans `app/produits.py` ; aucun autre code n'insère de produits (`grep -rn "INSERT" .` : rien).
- Existant cherché : sans objet — évolution de schéma propre au projet. / trouvé : — / fait maison parce que le besoin est spécifique.

## Questions ouvertes

### 🧭 Q1 — Valeur par défaut de `remise_max`

- [ ] (reco) `NOT NULL DEFAULT 0` : aucune remise autorisée tant que non renseigné
- [ ] `NULL` = pas de plafond
- [ ] Autre / complément →

## La suite

Rien.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Migration et schéma | `db/migrations/0003_remise_max.sql`, `db/schema.sql` (engendré) | Q1 | 1 |
| 2 — Modèle | `app/produits.py`, `tests/test_produits.py` | 1 | 2 |

### Étape 1 — Migration et schéma

- **Choix d'architecture** : migration `0003_remise_max.sql` (`ALTER TABLE produits ADD COLUMN remise_max INTEGER NOT NULL DEFAULT 0`), puis `make schema`. Écarté : éditer `db/schema.sql` à la main, bloqué par le hook `PreToolUse`.
- **Fichiers touchés** : `db/migrations/0003_remise_max.sql` (créé), `db/schema.sql` (modifié par `make schema`, pas à la main).
- **Dépend de** : Q1.
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien.
- **Impact technique** : nouvelle colonne, valeur par défaut 0.
- **Preuve de fin** : `make schema && git diff --stat db/` ne montre que la colonne ajoutée.
- **Test attendu** : —

### Étape 2 — Modèle

- **Choix d'architecture** : champ `remise_max: int = 0` dans `Produit`.
- **Fichiers touchés** : `app/produits.py` (modifié), `tests/test_produits.py` (modifié).
- **Dépend de** : étape 1.
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien.
- **Impact technique** : aucun appelant à adapter (champ avec défaut).
- **Preuve de fin** : `python3 -m unittest discover -s tests` vert.
- **Test attendu** : un `Produit` créé sans `remise_max` vaut 0 (le défaut de la migration).

## Journal d'exécution

_Se remplira à l'exécution._
