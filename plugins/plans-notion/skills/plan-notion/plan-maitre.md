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
`SKILL.md`), **sans `Statut`** : ce n'est pas un plan qu'on valide, et la porte
d'entrée de `executer-plan-notion` n'a rien à y lire. Une page par ensemble de
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

## Lancé par `executer-plan-notion`

À l'exécution, le pilote (Sonnet effort `high`, `executer-plan-notion` §2)
cherche d'abord une page maître qui couvre ces plans : s'il y en a une, il la
met à jour (avancement, ordre de merge revu) au lieu d'en créer une seconde ;
sinon il la crée au lancement, par les mêmes gestes. Chaque plan garde ensuite
son ouverture (§1 et §2 de ce skill-là), qui relit sa page en entier : c'est le
relevé d'une page qu'on va écrire.
