# Banc de comparaison de trois modèles sur les questions du support

## Cartes

`bot/repondre.py` → `bot/llm.py::complete` (à brancher) ; `tests/golden/questions_support.jsonl` (jeu de référence) ; `config.toml` (modèle courant).

## Besoins

- Comparer deux modèles Claude et un modèle open source local sur les questions type du support client.

## Maquette

Pas de maquette — aucune étape ne change ce qui s'affiche (outil de mesure en ligne de commande).

## Contraintes techniques vérifiées

- `bot/llm.py::complete` lève `NotImplementedError` (`bot/llm.py:3`) : aucun modèle n'est appelable aujourd'hui, le banc doit d'abord brancher le client.
- Le modèle se règle par une seule clé `modele` dans `config.toml:1` ; le banc passera le modèle en paramètre de `repondre(question, modele)` (`bot/repondre.py:6`).
- Un jeu de 12 questions de support existe : `tests/golden/questions_support.jsonl` (id, question, reponse_attendue), lu par `tests/test_golden.py`.
- Existant cherché : dans le dépôt (`find . -name "*.jsonl"`, `grep -rn question tests/`) ; puis jeux publics de questions de support client en français. / trouvé : `tests/golden/questions_support.jsonl` — 12 questions du support avec la réponse attendue, qui reflètent bien « le type de questions que reçoit notre support ». / fait maison parce que rien à fabriquer : on réutilise ce jeu tel quel ; 12 questions sont peu, l'extension viendra d'un plan à part.

## Questions ouvertes

### 🧭 Q1 — Comment noter une réponse ?

- [ ] (reco) Un juge LLM compare à `reponse_attendue` (note 0 à 2)
- [ ] Correspondance de mots-clés
- [ ] Autre / complément →

## La suite

Étendre le jeu de questions au-delà de 12.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Brancher le client | `bot/llm.py`, `tests/test_llm.py` | — | 1 |
| 2 — Lancer le banc | `bench/comparer.py`, `tests/test_comparer.py` | 1, Q1 | 2 |

### Étape 1 — Brancher le client

- **Choix d'architecture** : `complete(modele, prompt)` route selon le préfixe du modèle (Claude / local). Écarté : trois clients séparés.
- **Fichiers touchés** : `bot/llm.py` (modifié), `tests/test_llm.py` (créé).
- **Dépend de** : —
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien.
- **Impact technique** : dépendance au client de chaque fournisseur.
- **Preuve de fin** : `python3 -m unittest discover -s tests` vert.
- **Test attendu** : un modèle inconnu lève une erreur explicite, il ne retombe pas silencieusement sur le modèle par défaut.

### Étape 2 — Lancer le banc

- **Choix d'architecture** : script `bench/comparer.py` qui lit `tests/golden/questions_support.jsonl` et note chaque réponse.
- **Fichiers touchés** : `bench/comparer.py` (créé), `tests/test_comparer.py` (créé).
- **Dépend de** : étape 1, Q1.
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien.
- **Impact technique** : aucun.
- **Preuve de fin** : `python3 bench/comparer.py --modeles a b c` écrit un tableau de notes par modèle.
- **Test attendu** : une réponse identique à `reponse_attendue` reçoit la note maximale.

## Journal d'exécution

_Se remplira à l'exécution._
