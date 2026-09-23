# La revue au regard neuf

Fichier **partagé**, lu par `executer-plan-notion` (§3, dans « Après chaque
étape »), pour faire relire chaque étape par l'agent `relecteur` avant de
passer à la suivante. Comme `vagues.md` et `preuve-du-rouge.md`, il vit à un
seul endroit pour que le skill garde sa taille : la règle ne se duplique pas,
elle se référence.

Il ne dit pas *ce que* le relecteur cherche — ça vit dans
`${CLAUDE_PLUGIN_ROOT}/agents/relecteur.md`, les trois catégories et le
format de remarque. Il dit *quand* l'appeler, *comment* le brief, et *comment*
boucler jusqu'à un verdict propre.

## Quand

Après **chaque** étape — décision de Benjamin du 2026-09-23 (Q2) — une fois
la preuve rejouée verte par le pilote et l'étape commitée, **avant** l'entrée
de journal (§4 du skill) : la revue et ses éventuels correctifs doivent
apparaître dans le journal de l'étape, pas dans une entrée séparée après
coup.

Portée : la plage de commits de l'étape, `<base>..<tête>` — un commit pour
une étape ordinaire, deux (rouge, vert) pour une étape testée
(`preuve-du-rouge.md`), quatre pour un regroupement (`vagues.md`).

**Pour une étape de vague** (`vagues.md`) : la revue a lieu **dans le
worktree de l'étape, sur sa branche d'étape** — avant le report par
`cherry-pick` sur la branche du plan (`vagues.md`, « Au retour », étape 3).
Un correctif de revue se commite dans ce même worktree, et se reporte avec
le reste de l'étape : sans ça, le report emporterait un diff que le relecteur
n'a jamais vu.

## Comment l'appeler

Un appel `Agent` avec `subagent_type: "plans-notion:relecteur"` — nom
qualifié, le nom court ne résout pas, comme pour `plans-notion:executant`
(§3 du skill). **Sans paramètre `model`** : le frontmatter de l'agent porte
`opus` et `effort: low`, et c'est le même principe que pour l'exécutant — le
modèle garanti par construction plutôt que par une discipline d'appel.

Le brief du relecteur, et rien de plus :

1. **L'objectif de l'étape**, recopié du chapitre `Exécution` — pas résumé.
2. **Le répertoire** où travailler : le worktree de l'étape pour une vague,
   sinon le worktree du plan — jamais le checkout principal (§2 du skill).
3. **La plage de commits**, `<base>..<tête>`.

**Rien de la session** : ni le plan entier, ni la discussion, ni pourquoi tel
choix a été fait — c'est tout l'intérêt d'un regard neuf (`relecteur.md`,
« Pourquoi cet agent existe »). Aux tours suivants, le brief change : les
seuls correctifs depuis le dernier passage (nouvelle plage), plus les
remarques que le pilote a écartées et sa raison de le faire.

## La boucle

Décision de Benjamin du 2026-09-23 (Q4) : « pas de nouveau plan, on itère
jusqu'à ce que ce soit ok pour le reviewer. »

Le relecteur rend `RIEN À SIGNALER` ou `REMARQUES (n)`. Pour chaque remarque :

1. **Le pilote la vérifie avant d'agir** — relit le code visé, rejoue une
   commande si besoin. Ni accord de façade, ni correctif aveugle : le
   discernement reste dans la session qui a le contexte pour le faire.
2. **Retenue** : elle se corrige comme n'importe quel correctif — délégué à
   l'agent `plans-notion:executant`, avec un brief qui porte la remarque et
   son `fichier:ligne`. Commit `fix(…): étape N — revue`.
3. **Écartée** : avec une raison écrite, au journal — pas un silence, une
   phrase qui dit pourquoi.

Puis nouvel appel au relecteur, brief réduit aux seuls correctifs (nouvelle
plage de commits) plus les remarques écartées et leurs raisons. Le relecteur
prend position sur chacune — maintenue avec un argument nouveau, ou
abandonnée (`relecteur.md`, « Aux tours suivants »). On recommence jusqu'à
`RIEN À SIGNALER`. **Aucun tour de cette boucle n'ouvre de plan de suite** :
une remarque de revue se règle dans l'étape, pas dans une page à part.

## Garde-fou

**Trois tours de suite** où le relecteur maintient une remarque contre l'avis
argumenté du pilote : ça remonte à Benjamin **dans la session** — pas un plan
de suite, une ligne dans le fil. L'exécution continue sur les étapes qui n'en
dépendent pas pendant qu'on attend son arbitrage.

**Corriger une remarque exige de revenir sur une décision du plan** — schéma
de données, contrat d'API, dépendance : c'est l'arrêt déjà prévu au §3 du
skill, « L'autonomie est le défaut ». Une décision qui engage va à Benjamin,
qu'elle vienne d'un rouge en cours d'étape ou d'une remarque de revue ne
change rien à la règle.

## Les preuves après correctif

Un correctif de revue rejoue la preuve de l'étape — les tests des fichiers
impactés (§3 du skill, « précisément ») — avant d'être renvoyé au relecteur.
S'il touche un fichier de test, la preuve du rouge s'applique : c'est une
décision à journaliser au format « quoi — pourquoi — ce que ça coûte si
c'est faux » (`preuve-du-rouge.md`).

## Journal

Sous l'entrée de l'étape (§4 du skill), une ligne `Revue` :

```
Revue — N tour(s)
  [écart au plan] fichier:ligne — retenue, fix abc1234
  [bug] fichier:ligne — écartée : <raison>
  Verdict final : RIEN À SIGNALER
```

Une ligne par remarque, quel que soit le tour où elle est apparue.

## Coût assumé

Un appel Opus effort low par étape, plus un par tour de correction — décision
de Benjamin. Avant ce fichier, le pilote ne rejouait que des tests, jamais un
regard neuf sur le diff : c'est exactement la dérive que superpowers
`executing-plans` met en garde — « Do not skip it, and do not replace it with
your own read of the diff » — un pilote qui a écrit ou brief l'étape partage
les angles morts de celui qui l'a écrite.

## Les étapes sans code

Les étapes sans code (doc, config) sont relues comme les autres : la revue
porte sur l'écart au plan autant que sur les bugs, et un fichier de doc peut
dériver de son objectif sans qu'aucun test ne le voie.
