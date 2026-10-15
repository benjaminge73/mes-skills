# Le plan maître — détail

Référence de `plan-notion`, lue **avant le premier geste** d'un plan maître :
quand Benjamin demande de croiser, remettre à jour ou séquencer plusieurs plans,
ou quand `executer-plan-notion` lance une session qui en porte plusieurs
(« Plusieurs plans »). Les deux skills y renvoient, pour que la forme de la page
et la façon de la préparer ne vivent qu'ici.

## Sommaire

- Pourquoi ce fichier
- La page
- Le travail préliminaire : les règles d'un plan classique, plan par plan
- Ce qui reste au pilote
- Le statut du plan maître et son lot
- Lancé par `executer-plan-notion`

## Pourquoi ce fichier

Le 2026-10-15, le plan maître de cinq plans Vahiny a été préparé entièrement
par le pilote, en Opus : les cinq pages lues en entier, chaque affirmation
confrontée à `main` en lisant le code, les comptages (`wc -l`, branches, runs de
CI) joués à la main. Aucun `enqueteur`, aucun `sondeur`, rien en parallèle.
Rien ne l'interdisait : le plan maître n'était décrit que du côté de
l'exécution, par sa forme, et aucune des règles d'enquête d'un plan classique
(`enquete.md`, `_partage/lecture-deleguee.md`) ne disait s'appliquer à lui.

Elles s'appliquent. Un plan maître, c'est la conception de **plusieurs** plans
à la fois : le pilote reste en Opus, comme pour tout plan, et ce qui le rend
cher n'est pas son modèle mais ce qu'il lit. Cinq plans, c'est cinq fois la
lecture qu'un plan classique délègue.

## La page

Une page de la base `Plans Claude`, titre `[Plan maître] Nom_du_projet - Titre
thématique`, propriétés `Projet`, `Repo` et `Date` comme un plan (§2 de
`SKILL.md`), et un `Statut` **hérité** de ses plans (« Le statut du plan maître et
son lot ») : ce n'est pas un plan qu'on valide, et la porte d'entrée de
`executer-plan-notion` ne lit jamais ce statut, qui n'est qu'un affichage. Une page par ensemble de
plans : si une page maître couvre déjà ces plans, elle se met à jour au lieu
d'être recréée. Elle porte :

- **les plans** : un tableau, un plan par ligne (lien, `Statut`, `Branche`,
  étapes restantes, ce qui attend Benjamin) ;
- **le croisement** : qui part ensemble, qui attend quoi, et pourquoi ; entre
  plans, le parallèle est le défaut, seule une ressource partagée à l'exécution
  fait attendre (`executer-plan-notion`, « Plusieurs plans ») ;
- **l'ordre de merge** des plans qui touchent un même fichier ;
- **la file des actions lourdes** (`_partage/machine-partagee.md`) ;
- **l'avancement par plan**, une ligne datée par événement, avec un lien vers le
  journal de chacun ;
- **l'état final consolidé**, posé une fois le dernier plan clos.

Les quatre premières sont des **H2 aux titres fixes** — `Plans`, `Croisement`,
`Ordre de merge`, `File des actions lourdes` — parce que `preparation-prete.py
--maitre` les cherche, non vides : un plan couvert par ce maître ne passe pas
`pret` tant qu'une d'elles manque (« Le statut du plan maître et son lot »). Les
deux autres s'appellent `Avancement` et `État final`.

Elle s'écrit avec les mêmes précautions que le reste
(`_partage/ecrire-dans-notion.md`), schéma compris (`_partage/schemas.md`).

## Le travail préliminaire : les règles d'un plan classique, plan par plan

Chaque plan couvert reçoit **la même enquête qu'un plan classique**, et les
plans se traitent **en parallèle** : un message, plusieurs appels `Agent`, un
par plan et par geste. Le pool d'une douzaine de places
(`_partage/vagues.md`) borne le nombre d'appels simultanés.

1. **Relever les plans** dans la base `Plans Claude` : une requête, filtrée sur
   `Repo`, hors `execute` et `archive`. Rien à déléguer : la réponse est courte.
2. **Faire lire chaque page, pas la lire.** La lecture part à l'agent `lecteur`
   (`plans-notion:lecteur`, nom qualifié, sans `model` ni `effort`) : Haiku, avec
   les seuls outils Notion en lecture, une page par agent. Jamais un
   `general-purpose`, qui hériterait du modèle de la session — Opus, et c'est
   exactement la façon dont tout finit en Opus (`_partage/poc.md`, « Qui joue le
   POC »). Il rend une fiche courte : `Statut`, `Branche`, la date de la page, chaque
   étape avec ses « Fichiers touchés » et ce qui en reste, les questions
   ouvertes et celles déjà tranchées, et **les affirmations sur le dépôt** à
   revérifier (chemins, numéros de ligne, comptes). Il écrit aussi le miroir
   de la page dans le scratchpad et y joue `preuves-des-etapes.py --avant` et
   `verifier-preuves.py` (`SKILL.md` §8, points 11 à 13) : le pilote reçoit les
   codes de sortie et les écarts, pas la page.
3. **Confronter chaque plan à `main` par un `enqueteur`** (`plans-notion:enqueteur`,
   sans `model`), un par plan, en parallèle, avec dans son brief la fiche de
   l'étape 2 : chaque affirmation revient « toujours vrai », « déplacé »
   (nouveau `fichier:ligne`) ou « fait ailleurs » (le commit ou la PR). Le
   pilote ne lit pas le code (`_partage/lecture-deleguee.md`).
4. **Les comptages et l'état du dépôt au `sondeur`** (`plans-notion:sondeur`,
   sans `model`) : branches poussées, PR ouvertes, runs de CI, tailles de
   fichiers, budgets de tests. Un seul `sondeur` peut porter tous les plans :
   ses questions sont mécaniques.
5. **Le recoupement des fichiers se calcule, il ne se lit pas.** Le même
   `sondeur`, ou un second, reçoit les listes « Fichiers touchés » des fiches
   et rend chaque fichier touché par deux plans ou plus, avec les étapes
   concernées. C'est la matière du tableau des recoupements.

Une fiche qui manque ou rend `NEEDS_CONTEXT` se relance pour ce plan seul ; les
autres ne l'attendent pas.

**Quand Notion ne répond pas.** Le `lecteur` rend `BLOCKED` avec l'erreur mot
pour mot ; le repli est au pilote, dans l'ordre de la fiche « Connecteurs MCP
d'une session Claude Code » de `_partage/outils-et-quotas.md` :

1. panne « hôte injoignable » (hook, délai dépassé, appel non parti) : attendre
   une à deux minutes et relancer le `lecteur`, trois fois au plus — rien n'est
   parti, donc pas de doublon ;
2. la panne dure et la session a l'outil Composio : lire la page par lui. Une
   lecture de blocs volumineuse revient élidée par `COMPOSIO_MULTI_EXECUTE_TOOL` ;
   pour une page longue, c'est le workbench (`COMPOSIO_REMOTE_WORKBENCH`) qui la
   rend, et son code écrit la page dans un fichier au lieu de la renvoyer, pour
   que le pilote ne la charge pas dans son contexte ;
3. toujours rien : `hermes chat --query-file`, délai d'au moins 900 s (300 s a
   expiré), seulement pour lire — le pilote écrit lui-même la consigne.

Le pilote ne lit jamais la page en Opus par le connecteur « pour aller plus
vite » : c'est le chemin que ce fichier ferme. Et les pages que le `lecteur` a
déjà rendues ne se relisent pas à cause d'un repli sur une autre.

## Ce qui reste au pilote

- **Le jugement** : l'ordre de merge, l'exception voulue au parallèle (des
  fonctions déplacées qu'un autre plan modifie), une décision commune à deux
  plans à ne prendre qu'une fois, ce qui passe d'un plan à l'autre.
- **L'écriture** : la page maître, puis, s'il y a lieu, une passe `plan-notion`
  sur chaque page de plan (encadré daté, mise au format) — chacune avec **son**
  relevé avant d'écrire et son recompte après, page par page : le relevé d'une
  page qu'on modifie reste au pilote (`_partage/lecture-deleguee.md`, « Ce qui
  reste au pilote »).
- **Les questions à Benjamin**, groupées sur la page maître en un seul tableau,
  sans remplacer celles des pages.

## Le statut du plan maître et son lot

**Un plan maître couvre au moins deux plans, gérés dans une seule session** (le
pilote unique de `executer-plan-notion`, « Plusieurs plans »). Un plan seul n'a
pas de maître. Un plan appartient à **un seul** maître : avant d'en ajouter un,
chercher dans la base les autres maîtres du même `Repo` qui le listent.

**Le statut est hérité des plans du lot, et calculé, jamais écrit de tête.** Le
pilote lit les `Statut` actuels des plans (une requête sur la base ou la fiche du
`lecteur`, pas la colonne recopiée dans la page maître, qui se périme dès que
Benjamin change un statut à la main), puis joue :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/statut-maitre.py" "en cours" valide pret
```

Le script rend `statut=<valeur>` et `lot=ouvert|ferme`. La règle :

- **dès qu'un plan est `en cours`, le maître l'est** ; sinon il prend le statut du
  plan **le moins avancé** (`brouillon` < `en revue` < `valide` < `pret` <
  `en cours` < `a merger` < `execute`). Le minimum strict ferait reculer le maître
  à `valide` quand on ajoute un plan à un lot déjà en route, et l'afficherait
  `pret` pendant que du code s'écrit ;
- `archive` ne compte pas ; un plan abandonné **sort du lot** par une ligne datée
  dans la page maître (sinon il bloque le minimum) ;
- le pilote rejoue le script et réécrit le `Statut` du maître à chaque événement :
  ajout, changement de statut d'un plan, clôture.

**Le lot est fermé** quand tous les plans sont au moins `a merger` : le maître vaut
alors `a merger` tant qu'une PR n'est pas mergée, `execute` quand toutes le sont.
**Un plan ne s'ajoute qu'à un lot ouvert.** Un plan créé une fois le lot fermé
n'y entre pas : il ouvre un autre maître (avec un second plan) ou reste seul. Le
seul cas qui rouvre un lot fermé est le **plan de suite** d'un plan du lot
(`_partage/plan-de-suite.md`) : né de ce plan, il le rejoint, et le statut du
maître est recalculé. Un lot qui retombe à un plan (un abandon) reste un maître
jusqu'à sa fermeture.

**Ajouter un plan en route** : sa préparation se joue seule, jusqu'à `pret`
(`lecteur`, `enqueteur`, `sondeur` sur ce plan, plus les étapes ci-dessous), puis
le croisement, l'ordre de merge et les recoupements de fichiers se recalculent
avec les plans déjà avancés, dont ceux déjà sur `main` ; sans cela le croisement
ment. La ligne d'ajout est datée dans l'avancement.

**Chaque plan du lot passe par `pret`** : un plan `valide` ne passe pas à
`en cours` sans que sa préparation (`executer-plan-notion` §2, `ouverture.md`)
soit faite, son entrée `Ouverture` écrite et `preparation-prete.py` à 0, avec
`--maitre` : l'orchestration entre les plans (`Croisement`, `Ordre de merge`,
`File des actions lourdes`, tableau `Plans`) est donc **écrite sur la page maître
avant** que le premier plan du lot soit `pret`, et la puce **Orchestration** de
chaque plan en cite le lien et dit sa place (avec qui il part, ce qu'il attend,
son rang de merge). Le
pilote prépare les plans du lot avant de lancer la première étape d'aucun :
l'enquête ci-dessus en est la matière (les fiches du `lecteur` et des `enqueteur`
nourrissent les puces **Relecture**, **Preuves** et **Répétition** de chaque
plan). Un plan `pret` attend son tour de vague ; il passe `en cours` quand son
tour vient, pas avant. La page maître dit dans l'avancement quel plan reste
`valide` faute de préparation complète, et ce qui lui manque.

## Lancé par `executer-plan-notion`

À l'exécution, le pilote (Sonnet effort `high`, `executer-plan-notion` §2)
cherche d'abord une page maître qui couvre ces plans : s'il y en a une, il la
met à jour (avancement, ordre de merge revu) au lieu d'en créer une seconde ;
sinon il la crée au lancement, par les mêmes gestes. Chaque plan garde ensuite
son ouverture (§1 et §2 de ce skill-là), qui relit sa page en entier : c'est le
relevé d'une page qu'on va écrire.
