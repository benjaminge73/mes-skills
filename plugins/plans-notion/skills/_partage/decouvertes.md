# Découvertes : une seule règle de tri

Fichier référencé par `executer-plan-notion` (ouverture §2, journal §4). Il dit quoi
faire de chaque chose trouvée en route : un bug voisin, une dépendance douteuse, une
doc fausse, un secret, une ambiguïté du plan. Le signal vient du rapport de
l'exécutant (cinquième pièce de son rapport), du relecteur ou du pilote. Une seule
règle vaut à trois moments.

## Pourquoi ce fichier

- Une trouvaille gardée « en tête » disparaît au compactage : Claude Code résume le
  contexte pour faire de la place, et ne garde que le début des fichiers. Une règle
  qui ne vit que dans le journal n'est donc pas sûre de survivre à une longue exécution.
- Il y avait deux règles de tri, une pour la conception, une pour l'exécution, et
  elles divergeaient.
- Une seule règle, lue aux trois moments, ne peut pas être appliquée différemment
  selon le moment.

## Les trois moments

- **Conception** : `plan-notion`, pendant l'enquête et les passes de rédaction.
  Le traitement entre dans le plan lui-même.
- **Ouverture** : `executer-plan-notion` §2, relecture du plan et répétition à blanc
  (`_partage/poc.md`), avant la première étape.
- **Exécution** : les rapports des étapes, et ce que le pilote voit en route
  (`journal.md` §4).

## 1. Question à Benjamin

Une découverte est une question à Benjamin si elle :

- touche une décision déjà tranchée dans le plan, ou son périmètre, ou est trop
  grande pour une seule étape ;
- coûte : de l'argent (une dépense), un quota externe, ou plus d'une étape de travail ;
- touche à la sécurité : un secret, des droits, l'authentification, une exposition
  réseau, une dépendance non vérifiée, une donnée personnelle ;
- est irréversible : suppression de données ou de fichiers non versionnés (donc
  non récupérables par `git revert`, qui annule un commit), écriture dans un service
  externe ou en production, publication, migration, réécriture d'historique.

**Dans le doute : la question.** Une question coûte un tour de Benjamin ; une erreur
sur ces points coûte une donnée, un secret exposé ou un travail à refaire.

La question part avec sa recommandation en premier, par l'outil natif
`AskUserQuestion` ; sans cet outil, en texte. L'exécution continue sur tout ce qui
n'en dépend pas. Une question restée sans réponse à la clôture donne un plan de
suite (`_partage/plan-de-suite.md`). À la clôture, une question en attente n'est
pas laissée dans le plan terminé : elle se pose dans la session avant `a merger`,
et c'est seulement faute de réponse qu'elle part au plan de suite (« Le tri »).

## 2. Traitée dans le plan (intégration directe)

Sinon, c'est-à-dire si la découverte est à la fois **réversible**, **hors sécurité**
et **petite** (une étape, sans revenir sur une décision), on l'intègre directement,
sans question. Le plan reste `valide`. L'ajout est tracé dans le chapitre
`Exécution` par une correction datée, `_maj AAAA-MM-JJ — ajouté sans question parce que …_`,
et il est **listé au compte rendu** : jamais en silence.

- **À la conception ou à l'ouverture** : c'est une retouche du chapitre `Exécution`.
  Ce n'est **pas** une étape `D`, rien n'a encore été exécuté. Le chapitre `La suite`
  d'un plan suit la même mesure : un élément réversible, hors sécurité et petit entre
  dans le plan au lieu d'y attendre (`${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/chapitres-questions-execution.md`).
- **À l'exécution** : l'intégration prend la forme d'une étape `D<n>` (D1, D2…,
  numérotée à part des étapes du plan) : une ligne de tableau, un titre H3, une
  correction datée. Elle part à l'exécutant avec sa liste fermée de fichiers, dans
  ses propres commits, est relue (`_partage/revue.md`), et se journalise sous
  `Étape D<n> — …` avec sa propre ligne `**Découvertes** :`.

Le relecteur est une source de découvertes comme le rapport de l'exécutant : sa
catégorie **« Découverte hors plan »** (`_partage/revue.md`, « La boucle ») est
un défaut réel que l'étape n'a pas causé et que son objectif ne demande pas. Son
traitement est celui de ce fichier : d'abord le §1, question à Benjamin si la
remarque touche une décision, la sécurité, l'irréversible ou une dépense ; sinon
le §2, étape `D<n>`. **Le nombre d'étapes `D<n>` n'est pas plafonné** (décision
de Benjamin du 2026-10-16) : la règle d'arrêt est la question à Benjamin (§1),
pas un compteur.

## 3. Variante sans humain

Quand la session est lancée par Hermes (l'automate qui démarre des sessions sans
personne pour répondre), une question n'obtiendra jamais de réponse. Alors :

- la **reco par défaut** s'applique, et le compte rendu le dit, sous la rubrique
  `Recos appliquées par défaut` ;
- sauf pour la **sécurité** et l'**irréversible** : ces découvertes **gèlent** les
  étapes qui en dépendent (elles ne s'exécutent pas tant que la décision manque ;
  les autres étapes continuent), et elles partent sous `Questions pour Benjamin` ;
- la **dépense** (argent, quota externe) **ne gèle pas** : elle s'applique par défaut,
  et elle se signale en tête de `Recos appliquées par défaut` (décision de Benjamin,
  Q10 de son plan) ;
- une exécution de plan Notion garde la règle générale : une dépense y reste une
  question, comme au point 1.

## 4. Le traitement, sur la ligne `**Découvertes** :`

Chaque découverte reçoit **un** traitement, écrit sur sa ligne `**Découvertes** :` de
l'entrée d'étape (`journal.md` §4) : `Question à Benjamin`, `Traitée dans le plan
(D<n>)`, ou `Recos appliquées par défaut` en variante sans humain. Un libellé « noté
pour plus tard » sans propriétaire ne compte pas.

## 5. Un secret ne se corrige jamais seul

**Un secret découvert ne se corrige jamais seul** : ni suppression, ni rotation,
ni réécriture d'historique, et **sa valeur ne s'écrit nulle part** — ni brief,
ni journal, ni page Notion. On note où il est (`fichier:ligne`) et ce que c'est,
puis la question part tout de suite.
