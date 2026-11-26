# Naissance du maître et plans du lot — détail

Référence de `plan-notion`, lue à **chaque création de page de plan** (« Le deuxième plan
d'un projet crée le maître ») et pour **rattacher un plan à son maître** (« Les plans du lot,
sous-éléments du maître »). La page maître, sa préparation, son statut et l'exécution de son
lot sont dans `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`.

Sommaire :

- Le deuxième plan d'un projet crée le maître
- Les plans du lot, sous-éléments du maître

## Le deuxième plan d'un projet crée le maître

**Un plan maître ne se demande pas : il naît au deuxième plan non terminé d'un même
projet**, même si les deux ne sont pas créés le même jour ni dans la même session.
Relevé du 2026-10-28 : Benjamin a dû demander le maître à la session qui venait de
créer trois plans `hermes-custom`. Une session qui crée un plan ne sait pas ce que les
autres ont créé avant elle ; seule la vérification à chaque création les rassemble.

**Quand** : à chaque création d'une page de plan (§2 de `SKILL.md`), plan de suite
compris, avant de rendre la main. C'est une requête et une écriture : aucune page à
lire, rien à déléguer, aucune enquête (celle-ci viendra à la préparation, dans `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`, « Le travail préliminaire »).

1. **Relever** les plans de la base `Plans Claude` dont `Repo` est celui du nouveau plan,
   hors `execute` : titre, `Statut`, `Projet`, parent. Écarter ceux dont
   `Projet` diffère de celui du nouveau plan : un même dépôt peut porter deux sujets sous
   deux pages projet (§1 de `SKILL.md`), et ils ne se croisent pas. Séparer les pages
   `[Plan maître]` des plans.
   **Relever aussi les restes** : une seconde requête, sur la base « Restes »
   (`collection://41ab8cc8-aa1d-81cf-b83c-000b76701db9`), filtrée `Repo` = `benjaminge73/<repo>`
   et `État` = `ouvert`, sans lecture de page : la ligne se lit par ses propriétés. Règle
   d'ouverture : `_partage/restes.md`, règle 7 (le plan reprend chaque ligne par défaut, et
   cite « laissée ouverte (<lettre>) : <raison> » celles qu'une raison de la liste fermée retient) ; ce qu'elle rend s'écrit dans la page du plan
   (`chapitres-questions-execution.md`, « Les restes repris »).
2. **Trier**, premier cas qui s'applique :
   - **un maître ouvert** (`${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`, « Le statut du plan maître et son lot ») couvre ce projet : le
     nouveau plan le **rejoint** ; avec plusieurs maîtres ouverts, ne pas choisir de tête :
     poser la question dans la session, le plan restant seul d'ici la réponse ;
   - **aucun maître, au moins un autre plan non terminé** : créer le maître avec le nouveau
     plan **et** tous ces plans ;
   - **sinon** (aucun autre plan, ou seulement un maître au lot fermé) : le plan reste seul
     (un maître fermé ne reçoit un plan que s'il est le plan de suite d'un de ses plans). Le
     dire en une ligne.
   Un plan déjà sous un autre maître n'est jamais déplacé : un plan appartient à un seul
   maître.
3. **Écrire**, dans le même tour, sans demander de confirmation : une page Notion se corrige
   (`_partage/ecrire-dans-notion.md`).
   - *Créer le maître* : une **coquille**, pas la préparation. Page `[Plan maître]
     Nom_du_projet - <ce que les plans ont en commun>`, propriétés `Projet`, `Repo`, `Date`
     et `Statut` (calculé par `statut-maitre.py` sur les `Statut` relevés, jamais de tête) ;
     corps aux six H2 de « La page » (`${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`), `Récap du lot` en premier (`- rien encore`) ; tableau
     `Plans` avec un identifiant `P1`, `P2`… par plan, dans l'ordre de leur date ;
     `Croisement`, `Ordre de merge` et `File des actions lourdes` portent la seule ligne
     `à définir` : `preparation-prete.py --maitre` la lit comme une coquille, donc aucun plan
     du lot ne passe `pret` avant que « Le travail préliminaire » (`${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`) les ait remplies. Une ligne
     datée en `Avancement` dit que le maître est né du deuxième plan, et lesquels.
   - *Rejoindre un maître* : une ligne de plus au tableau `Plans` (identifiant suivant), une
     ligne `—` au `Récap du lot`, une ligne datée en `Avancement`, `Statut` du maître recalculé.
     Le `Croisement` ne se réécrit pas ici : « Ajouter un plan en route » (`${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`) le recalcule à la
     préparation de ce plan.
   - *Dans les deux cas* : rattacher chaque plan par la relation de parenté, et **relire les
     deux côtés** (« Les plans du lot, sous-éléments du maître »). La puce **Orchestration**
     de leur entrée `Ouverture` cite le maître le moment venu.
4. **Dire** en une ligne à Benjamin ce qui s'est passé : « maître créé avec <plans> » ou
   « rejoint le maître <titre> ». Sans relation de parenté dans la base, le dire aussi : le
   tableau `Plans` porte alors seul le lien.

Cette règle est la seule qui rattache de sa propre initiative des plans qui existaient déjà
(« Portée », plus bas) : Benjamin l'a demandée pour tout projet, sans qu'il ait à y penser.

## Les plans du lot, sous-éléments du maître

**Chaque plan du lot est un sous-élément de la page maître**, dans la base `Plans
Claude` : la relation de parenté de la base (« Parent item » ou « Élément parent »
selon la langue de l'espace ; la lire dans le schéma de la base, `notion-fetch` sur sa
`collection://`, jamais la deviner) porte l'URL de la page maître. Le plan reste une
ligne de la base, avec ses propriétés `Statut`, `Repo`, `Branche` et `PR` dont la porte
d'entrée et `statut-maitre.py` dépendent ; il apparaît en plus sous son maître.

⚠️ **Jamais `notion-move-pages` sous la page maître** : le plan quitterait la base et
perdrait ses propriétés, donc sa porte d'entrée et le calcul du statut du maître.
Même piège à la main : un plan glissé dans le corps de la page maître, ou créé par
« Nouvelle page » dans ce corps, devient une simple sous-page hors de la base (il
n'a plus que son titre et disparaît du tableau). Le rattachement passe **toujours** par
la propriété, jamais par la page. Vu le 2026-10-22 sur le lot micro-trading : un plan
glissé dans le maître, remis en ligne par `notion-move-pages` vers le `data_source_id`
de la base, a gardé ses propriétés mais n'apparaissait pas sous le maître.

- **Quand** : à la création du maître (chaque plan du lot), à l'ajout d'un plan en
  route, et pour un plan de suite d'un plan du lot (il rejoint le lot). Un plan qui
  sort du lot (abandon) perd son parent, dans le tour où la ligne datée est écrite
  sur la page maître.
- **Comment** : une écriture de propriété seule (`notion-update-page`, la relation),
  sans toucher au corps de la page ; le relevé des cases n'a pas lieu d'être.
- **Relire les deux côtés, dans le même tour.** Le tableau lit la relation du côté du
  maître : après l'écriture, une requête sur la base doit montrer le parent sur le plan
  **et** le plan dans la propriété des sous-éléments du maître. Si le maître ne le
  liste pas (relation à sens unique, vue après un `notion-move-pages` de réparation),
  écrire la propriété des sous-éléments **sur la page maître**, avec la liste complète
  de ses enfants (une écriture qui n'en donnerait qu'un retirerait les autres), puis
  relire. Un rattachement dit fait sans cette relecture n'est pas fait.
- **Si la base n'a pas de relation de parenté** (les sous-éléments se activent une
  fois, dans la vue Tableau de la base, par Benjamin), le dire en une ligne et
  continuer : le tableau `Plans` et la puce **Orchestration** portent alors seuls le
  lien. Ne pas créer la propriété soi-même.
- **Portée** : la règle vaut pour les maîtres créés ou modifiés après elle. Un lot
  existant se rattache quand Benjamin le demande, jamais de l'initiative d'une
  session qui passe par là ; seule exception, « Le deuxième plan d'un projet crée le
  maître », qui rattache à la création d'un plan ceux du projet qui n'ont pas de maître.

