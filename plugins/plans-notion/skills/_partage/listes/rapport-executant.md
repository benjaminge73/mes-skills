# Rapport d'exécutant à cases

Ce fichier dit comment un rapport d'exécutant se coche, champ par champ, et ce que
`verifier-rapport.py` refuse. Il sert à l'exécutant pour écrire son rapport et au pilote pour
le contrôler. L'état (`DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, `NEEDS_CONTEXT`) reste une ligne à
part, en tête : il n'est pas une case.

## Des champs de l'étape aux cases

Chaque puce `- **Champ** : valeur` du brief devient une case du rapport, dans le même ordre,
sauf les champs que tient le pilote (ci-dessous).

Une case prouvée s'écrit sur une seule ligne :

```
- [x] <champ> — preuve : <la preuve>
```

Une case non prouvée reste `- [ ] <champ>` ou disparaît. Une case cochée sans preuve (`- [x] <champ>`
seul, ou avec une preuve faite de tirets) compte comme non prouvée. La preuve se lit sur la ligne :
une sortie bornée, une commande suivie de son résultat, une référence précise (fichier:ligne, pièce
du rapport). « Les tests passent » ne prouve rien.

Preuve attendue selon le champ :

- **Choix d'architecture** : la décision retenue et ce qu'elle coûte si elle est fausse (pièce 4).
- **Fichiers touchés** : la sortie de `git diff --name-only <base>..HEAD`.
- **Docs relues** : les chemins lus, avec les lignes consultées.
- **Interfaces** : la commande jouée et les codes de sortie observés.
- **Impact fonctionnel** : ce qui se voit changer, ou « rien », avec la commande qui le montre.
- **Impact technique** : ce qui a été mesuré (octets, codes, nombre de fichiers).
- **Test attendu** : la sortie rouge puis la sortie verte du test nommé.
- **Preuve de fin** : la sortie bornée de la commande, telle quelle (pièce 3 du rapport).
- Tout autre champ du brief : la preuve qui le montre, sur la même ligne.

## Les champs que tient le pilote

Ces quatre champs ne deviennent pas des cases, et l'exécutant ne les coche pas : `Dépend de`,
`Relecture`, `Taille`, `Blocs touchés`. Le pilote les tient dans le journal du plan.

## Le contrôle

```
python3 plugins/plans-notion/skills/_partage/scripts/verifier-rapport.py --brief <brief> --rapport <rapport>
```

- code 0 : chaque champ de l'étape a une case cochée avec une preuve ;
- code 1 : une ligne par défaut sur la sortie standard, la case nommée :
  `case manquante : <champ>`, `case non cochée : <champ>` ou `case sans preuve : <champ>` ;
- code 2 : usage (fichier illisible, brief sans champ).

Le script vérifie la présence et la forme de la preuve, pas sa vérité : il ne rejoue rien. Le
pilote rejoue la preuve de fin de son côté, comme pour le rapport libre.

## Exemple

Brief (extrait) :

```
- **Test attendu** : un rapport DONE dont la case « Test attendu » est cochée sans preuve rend 1.
- **Dépend de** : Q3
```

Rapport refusé (code 1, `case sans preuve : Test attendu`) :

```
**État** : DONE

- [x] Test attendu
```

Rapport accepté (code 0) :

```
**État** : DONE

- [x] Test attendu — preuve : rouge `1 failed` (sortie jointe), vert `4 passed` (sortie jointe)
```
