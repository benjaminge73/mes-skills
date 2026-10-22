# Le plan maître — détail

Référence de `plan-notion`, lue **avant le premier geste** d'un plan maître :
quand Benjamin demande de croiser, remettre à jour ou séquencer plusieurs plans,
ou quand `executer-plan-notion` lance une session qui en porte plusieurs
(« Plusieurs plans »). Les deux skills y renvoient, pour que la forme de la page
et la façon de la préparer ne vivent qu'ici.

## Sommaire

- Pourquoi ce fichier
- La page
- Les plans du lot, sous-éléments du maître
- Le travail préliminaire : les règles d'un plan classique, plan par plan
- Ce qui reste au pilote
- Le statut du plan maître et son lot
- Qui rejoue le calcul, et quand
- Le maître se revérifie aussi quand le contenu d'un plan change
- Un plan du lot ne s'exécute pas seul
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
  fait attendre (`executer-plan-notion`, « Plusieurs plans »). Chaque plan du
  tableau porte un identifiant `P1`, `P2`… et chaque contrainte s'écrit en une
  phrase que `depart-dans-le-lot.py` lit : `P3 attend P1 jusqu'à a merger` (sans
  « jusqu'à », `execute`) ou `P2 exclut P4` (ressource partagée, jamais en même
  temps), suivie de sa raison ;
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

Un H2 de plus, **`Récap du lot`**, n'est pas dans cette liste. `preparation-prete.py
--maitre` ne le cherche pas, et son titre ne commence par aucun des six : il n'en
est ni une condition ni un doublon. C'est le condensé du lot, la seule place où
Benjamin voit ce que chaque plan change pour lui sans ouvrir sa page :

- un tableau, **Plan · Ce qui change pour toi · Reste à faire**, une ligne par
  plan du lot ; la colonne Plan porte le lien vers la page du plan ;
- la colonne « Ce qui change pour toi » reprend l'entrée de ce plan, une puce par
  entrée (titre du plan, date, une phrase), et chaque puce porte son **lien
  d'ancre** vers le titre `## Récap · AAAA-MM-JJ · <titre du plan>` de la page du
  plan, avec la mention en clair à côté (`→ Récap`) tant que le clic n'est pas
  vérifié. La méthode de l'ancre et son repli sont au § 7 de
  `_partage/changelog-et-doc.md` : on y renvoie, on ne les recopie pas ;
- le pilote complète la ligne d'un plan **à chacune de ses clôtures**, dans la
  même passe que l'avancement. Tant qu'un plan n'a pas clos, sa ligne porte `—`
  dans « Ce qui change pour toi », et « Reste à faire » dit ce qui l'attend.
  Après la clôture, « Reste à faire » cite le lien du plan de suite ou l'événement
  attendu, jamais une décision en suspens : elle se pose dans la session
  (`_partage/plan-de-suite.md`, « Le tri »).

Elle s'écrit avec les mêmes précautions que le reste
(`_partage/ecrire-dans-notion.md`), schéma compris (`_partage/schemas.md`).

## Les plans du lot, sous-éléments du maître

**Chaque plan du lot est un sous-élément de la page maître**, dans la base `Plans
Claude` : la relation de parenté de la base (« Parent item » ou « Élément parent »
selon la langue de l'espace ; la lire dans le schéma de la base, `notion-fetch` sur sa
`collection://`, jamais la deviner) porte l'URL de la page maître. Le plan reste une
ligne de la base, avec ses propriétés `Statut`, `Repo`, `Branche` et `PR` dont la porte
d'entrée et `statut-maitre.py` dépendent ; il apparaît en plus sous son maître.

⚠️ **Jamais `notion-move-pages` sous la page maître** : le plan quitterait la base et
perdrait ses propriétés, donc sa porte d'entrée et le calcul du statut du maître.

- **Quand** : à la création du maître (chaque plan du lot), à l'ajout d'un plan en
  route, et pour un plan de suite d'un plan du lot (il rejoint le lot). Un plan qui
  sort du lot (abandon) perd son parent, dans le tour où la ligne datée est écrite
  sur la page maître.
- **Comment** : une écriture de propriété seule (`notion-update-page`, la relation),
  sans toucher au corps de la page ; le relevé des cases n'a pas lieu d'être.
- **Si la base n'a pas de relation de parenté** (les sous-éléments se activent une
  fois, dans la vue Tableau de la base, par Benjamin), le dire en une ligne et
  continuer : le tableau `Plans` et la puce **Orchestration** portent alors seuls le
  lien. Ne pas créer la propriété soi-même.
- **Portée** : la règle vaut pour les maîtres créés ou modifiés après elle. Un lot
  existant se rattache quand Benjamin le demande, jamais de l'initiative d'une
  session qui passe par là.

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

**Quand Notion ne répond pas.** Le `lecteur` joue lui-même les deux premiers
paliers de la chaîne : le connecteur de la session, puis la commande `composio`
du VPS, en lecture seule. Quand les deux échouent, il rend `BLOCKED` avec
l'erreur mot pour mot, et y nomme le palier suivant si `composio` a été joué.
La chaîne complète, ses délais
et ses règles de doublon sont dans la fiche « Connecteurs MCP d'une session
Claude Code » de `_partage/outils-et-quotas.md` : on la lit là, elle n'est pas
recopiée ici. L'outil Composio de la session n'est pas un palier : il passe par
le même relais que Notion et tombe avec lui.

Le pilote lit la mention du `BLOCKED` :

- **« palier suivant : Hermes, au pilote »** : le `lecteur` a déjà joué
  `composio`, et ça a échoué. Il ne relance pas le `lecteur` pour cette page.
  Le pilote passe au palier Hermes de la fiche, seulement pour lire, avec la
  consigne qu'il écrit lui-même.
- **Sans cette mention** : `composio` était absent, ou la page est refusée
  (catégorie « autre »). Le pilote suit la fiche pour ce cas. Il ne relance le
  `lecteur` que si la fiche prévoit une nouvelle tentative (panne « hôte
  injoignable » : attendre une à deux minutes, trois essais au plus) ; une page
  refusée ne se relance pas, elle refuserait à l'identique.

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
- le `Statut` du maître n'est **jamais vide** : il se pose à la création de la page,
  par ce même script, et non « plus tard ».

**Le lot est fermé** quand tous les plans sont au moins `a merger` : le maître vaut
alors `a merger` tant qu'une PR n'est pas mergée, `execute` quand toutes le sont.
**Un plan ne s'ajoute qu'à un lot ouvert.** Un plan créé une fois le lot fermé
n'y entre pas : il ouvre un autre maître (avec un second plan) ou reste seul. Le
seul cas qui rouvre un lot fermé est le **plan de suite** d'un plan du lot
(`_partage/plan-de-suite.md`) : né de ce plan, il le rejoint, et le statut du
maître est recalculé. Un lot qui retombe à un plan (un abandon) reste un maître
jusqu'à sa fermeture.

**À la fermeture du lot, une seule entrée au Changelog.** L'entrée se pose au
**passage** du lot de `ouvert` à `ferme`, jamais à chaque fois que
`statut-maitre.py` rend `lot=ferme` : un lot déjà fermé dont un plan avance
(`a merger` → `execute`) reste fermé, et le script le rend encore. Le passage se
lit sur le `Statut` du maître avant réécriture : il valait un statut de lot
ouvert (`brouillon` à `en cours`), le script rend désormais `lot=ferme`. Au
passage, le pilote relit le `Changelog` du hub (page fraîche, § 4 de
`_partage/changelog-et-doc.md`) et cherche une entrée `Lot <titre du plan maître>`
déjà posée. Si elle n'existe pas, il pose l'entrée consolidée, titre
`## AAAA-MM-JJ · Lot <titre du plan maître>`, qui reprend chaque plan du lot avec
son lien. Si elle existe déjà (lot rouvert par un plan de suite puis refermé), il
**met à jour cette entrée** au lieu d'en poser une seconde : le corps reprend le
lot tel qu'il est, à sa nouvelle fermeture. Les plans du lot n'en écrivent pas
chacun : leur récap reste en tête de leur propre page (`## Récap · …`), et le
`Récap du lot` de la page maître reste le condensé. L'entrée part à la clôture du
lot, comme une entrée de plan part à sa clôture, avant le merge : « Reste à faire »
dit ce qui attend. Format et règles : `_partage/changelog-et-doc.md` (§ 2.4, et § 5
pour un projet non activé, où le hub n'est pas touché).

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

### Qui rejoue le calcul, et quand

Un statut dérivé ne reste juste que si quelqu'un le recalcule. Le 2026-10-20, le
maître Vahiny « Les suites du 17 octobre » était encore `pret`, lot ouvert, alors
que ses sept plans étaient `execute` ou `archive` : le calcul n'avait été joué qu'à la
préparation, et les passages `en cours`, `a merger` et `execute` s'étaient faits
dans d'autres tours, parfois d'autres sessions, que personne ne chargeait de le
rejouer. Le maître « La doc suit le plan » n'avait même jamais reçu de `Statut`.

**Celui qui écrit le `Statut` d'un plan couvert par un maître rejoue le calcul dans
le même tour**, comme `execute` se pose dans le tour où le merge est constaté. Ça
vaut pour toute session, pas seulement le pilote du lot : la plupart des
transitions (`execute` après un merge, `archive`, un plan de suite) se font hors de
lui.

1. **Trouver le maître** : la puce **Orchestration** de l'entrée `Ouverture` du plan
   en cite le lien. Pas de lien (`sans objet — aucun plan maître`), pas de maître,
   rien à faire. Un plan sans entrée `Ouverture` (clos avant la règle, ou archivé à
   la main) : chercher dans la base les maîtres du même `Repo` non `execute` ni
   `archive`, et lire leur tableau `Plans`.
2. **Relever les `Statut` de tous les plans du tableau `Plans`** par une requête sur
   la base (jamais la colonne recopiée dans la page) ; ajouter les plans de suite nés
   d'un plan du lot.
3. **Jouer le script avec le statut actuel du maître** :

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/statut-maitre.py" --actuel "pret" execute execute archive
   ```

   Code 0 : le maître est à jour, rien à écrire. **Code 3** : il est périmé (ou
   vide) ; réécrire `Statut` avec la valeur rendue, ajouter une ligne datée à
   `Avancement` (ancien statut, nouveau, plan qui a bougé), et, quand le lot devient
   fermé, mettre à jour le tableau `Plans` et l'`État final`.

À l'**entrée** d'un maître ou d'un de ses plans, la même vérification est un
rattrapage : Benjamin change des statuts à la main (`archive` en tête), et rien
d'autre ne le voit. Un écart trouvé à ce moment se corrige tout de suite, sans
attendre un événement, et se signale d'une ligne à Benjamin.

### Le maître se revérifie aussi quand le contenu d'un plan change

Le statut n'est pas la seule chose que la page maître dérive de ses plans : son
`Croisement`, son `Ordre de merge`, sa `File des actions lourdes` et le tableau
`Plans` (étapes restantes, ce qui attend Benjamin) disent ce que les plans disent. Un
plan dont le contenu change sans que le maître le sache rend ces sections fausses sans
qu'aucun statut ait bougé : un fichier ajouté à une étape crée un recoupement, une étape
`D<n>` change ce qui reste, une question nouvelle change ce qui attend Benjamin.

**Celui qui écrit la page d'un plan du lot revérifie le maître dans le même tour**, que
ce soit un `Statut` (calcul ci-dessus) ou le contenu : les chapitres `Exécution`,
`Questions ouvertes`, `Besoins`, `Cartes`, ou les propriétés `Branche` et `PR`. Les
entrées du `Journal d'exécution` ne déclenchent rien de plus : leur ligne d'`Avancement`
suffit.

1. **Relire la partie du plan qui a changé** (une fiche du `lecteur`, `_partage/lecture-deleguee.md`,
   pour ce seul plan), pas les autres.
2. **Confronter à la page maître** : les `Fichiers touchés` aux recoupements et à
   l'ordre de merge, les étapes aux contraintes `attend` / `exclut` du `Croisement`, la
   ligne du plan dans le tableau `Plans` et dans le `Récap du lot`. Un plan déjà `pret`
   dont la place change relit sa puce **Orchestration** et la corrige.
3. **Écrire le verdict dans `Avancement`**, une ligne datée : « maître revérifié après
   <changement> du plan <Pn> : inchangé » ou « corrigé : <ce qui a bougé> ». Un
   changement qui rend un `Croisement` déjà appliqué faux (un plan démarré qui aurait dû
   attendre) n'est pas corrigé en silence : il est dit à Benjamin dans la session.

## Un plan du lot ne s'exécute pas seul

Un plan couvert par un maître ne démarre jamais sur la seule foi de sa page : la
session qui reçoit un « go » sur lui lit **d'abord** le maître, et ne passe le plan `en
cours` que si le `Croisement` le permet. La raison est celle du lot entier : le pilote
unique de `executer-plan-notion` (« Plusieurs plans ») conduit tous les plans, et une
session qui ouvre un plan à côté d'un lot en route ne voit ni ce qu'il attend ni ce
qu'il bloque.

1. **Savoir si le plan est couvert** : sa propriété de parenté (voir « Les plans du
   lot, sous-éléments du maître »), la puce **Orchestration** de son entrée `Ouverture`,
   et, à défaut des deux, les maîtres du même `Repo` non `execute` ni `archive` dont le
   tableau `Plans` le liste. Un seul de ces trois suffit : le plan est couvert.
2. **Lire le maître** : sa page entière par le `lecteur`, puis les `Statut` actuels des
   plans du lot par une requête sur la base (jamais la colonne de la page).
3. **Jouer la porte du lot**, au moment de passer `pret` à `en cours` :

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/depart-dans-le-lot.py" <maitre.md> <Pn> --statuts "P1=en cours" "P2=pret" …
   ```

   Code 0 : le départ est permis, `Statut` = `en cours` (et le maître se recalcule, plus haut).
   **Code 1** : un motif par ligne (qui attend quoi, quel statut est lu). Le plan reste
   `pret`, la session le dit en une ligne et ne démarre aucune étape : elle reprend
   quand le plan attendu atteint le statut demandé. **Code 2** : le `Croisement` ne se
   lit pas (pas d'identifiants, section absente) ; lire les contraintes à la main, et
   demander à Benjamin dans la session si elles ne sont pas claires, plutôt que démarrer.
4. **Le pilote du lot est l'exécutant normal.** Quand le pilote conduit le lot, la porte
   se joue pour chaque plan à son tour de vague ; une autre session ne démarre le plan
   que si le `Croisement` le permet **et** qu'aucun autre pilote ne tient déjà le lot (la
   ligne d'`Avancement` dit qui).

Le script vérifie les contraintes écrites, pas leur justesse : un `Croisement` oublié de
l'orchestration ne se rattrape que par la revérification du maître ci-dessus.

## Lancé par `executer-plan-notion`

À l'exécution, le pilote (Sonnet effort `medium`, `executer-plan-notion` §2)
cherche d'abord une page maître qui couvre ces plans : s'il y en a une, il la
met à jour (avancement, ordre de merge revu) au lieu d'en créer une seconde ;
sinon il la crée au lancement, par les mêmes gestes. Chaque plan garde ensuite
son ouverture (§1 et §2 de ce skill-là), qui relit sa page en entier : c'est le
relevé d'une page qu'on va écrire.
