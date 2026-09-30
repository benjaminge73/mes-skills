# Corriger la coquille du titre d'installation (README)

## Cartes

Un seul fichier concerné : `README.md`. Rien d'autre dans le dépôt ne référence ce titre.

## Besoins

- Le titre de la section d'installation du `README.md` est écrit « Instalation » ; il doit être écrit « Installation ».

## Maquette

Pas de maquette — la seule modification est l'orthographe d'un titre de documentation, aucune étape ne change un écran.

## Exécution

### Étape 1 — Corriger le titre

- **Fichiers touchés** : `README.md` (modifié, ligne 5).
- **Dépend de** : —
- **Taille** : 1 fichier.
- **Impact fonctionnel** : Rien.
- **Impact technique** : aucun ; aucun lien vers l'ancre `#instalation` n'existe (`grep -rn instalation` : une seule occurrence, le titre).
- **Preuve de fin** : `grep -n "^## Installation" README.md` rend la ligne 5, et `grep -rn Instalation .` ne rend plus rien.
- **Test attendu** : —

## Journal d'exécution

_Se remplira à l'exécution._
