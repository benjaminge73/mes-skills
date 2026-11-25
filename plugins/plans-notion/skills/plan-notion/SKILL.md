---
name: plan-notion
description: Écrit et fait évoluer un plan de travail dans Notion au lieu du chat. À utiliser dès que Benjamin demande un plan, une approche, une architecture, une découpe, « comment tu ferais », « par où on commence », « avant de coder », ou qu'un design approuvé doit devenir une page de plan. L'exploration d'une idée encore floue (dialogue sur l'intention, les contraintes et les approches, avant tout plan) relève du skill brainstorming de methode-de-travail, qui passe la main à celui-ci une fois le design accepté. S'applique dans tous les modes de l'app sauf le mode plan natif de Claude Code, où il faut se taire et laisser le plan natif faire foi. Couvre aussi les passes suivantes (commentaires Notion non résolus, réponses dans les fils, mise à jour du plan et de son chapitre d'exécution). L'implémentation une fois le plan validé relève du skill executer-plan-notion.
---

# Plan dans Notion

## Invariants — ce qui tient même après un compactage

Un compactage du contexte ne recolle que le début de ce fichier : ce qui ne
doit jamais se perdre est donc ici, une ligne chacun, avec la section qui le
détaille.

- **Après un compactage, ré-invoquer ce skill** (outil `Skill`) avant
  d'écrire dans Notion ou de reprendre une passe — le compactage ne garde que
  le début du skill.
- **Ne jamais cocher une case** à la place de Benjamin, pas même la reco — sauf une question née verte dont la case reflète un choix validé en toutes lettres et cité : `Preuve : dispense — parce que choix de gouvernance de Benjamin, <date> : « <citation> »`
  (« 1. Ne jamais cocher… »).
- **Rien de livré avant `valide`** : ni fichier dans le dépôt, ni commit, ni
  sous-agent d'implémentation (« 2. Ne rien coder de livré… »).
- **`Statut` sans accents** : `brouillon`, `en revue`, `valide`, `pret`,
  `en cours`, `a merger`, `execute` (fin de « 2. Ne rien coder… »).
- **Toute passe qui écrit une page de plan finit par décider du `Statut`** : `_partage/fin-de-passe.md`.
- **Relevé avant d'écrire, recompte après** : cases cochées et textes libres
  relevés avant toute écriture, recomptés après (§4, `_partage/ecrire-dans-notion.md`).
- **Ce qui est découvert s'écrit dans le plan**, avec sa conséquence sur les
  étapes (tri : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md`) : une
  découverte gardée en tête disparaît au compactage (« Le chapitre `Exécution` »).

## Suis-je la bonne version ?

Un skill ne choisit pas d'où il est chargé (copie synchronisée périmée) ; il peut
seulement le constater. À vérifier au chargement, en une commande :

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-version.sh" "${CLAUDE_PLUGIN_ROOT}"
```

Code 0 : à jour. Code 1 : la version chargée (`plugin.json`) ou le chemin chargé
(« Base directory for this skill », soit `${CLAUDE_PLUGIN_ROOT}`) diffère de
l'`installPath` installé → le dire à Benjamin en une ligne, puis lire ce `SKILL.md`
et `_partage/` depuis cet `installPath`, pas depuis la copie chargée. Copie installée en retard sur `main` (le message le dit) : `claude plugin marketplace update atelier` puis `claude plugin update plans-notion@atelier` (redémarrage requis), relire l'installPath n'y change rien. Code 2 :
lecture impossible, à dire aussi. Pour charger la plus récente : `claude plugin update
plans-notion@atelier` (redémarrage requis) ; en session cloud, le setup script pose
déjà la dernière version publiée — jamais plus loin que ce que `main` du dépôt
porte. Ce que cette garde ne règle pas : une copie qui ne l'embarque pas ne
préviendra jamais — elle protège à partir de la version qui la porte.

## Deux règles qui priment sur tout

### 1. Ne jamais cocher une case à la place de Benjamin

**Aucune case n'est cochée par moi. Jamais. Pas même la reco** (sauf la question née verte, ci-dessous). Une case cochée
est une décision de Benjamin, et c'est souvent la *seule* trace de cette
décision — le fil de discussion ne la contient pas, et il disparaît au
compactage.

Une case que j'ai cochée est **indistinguable** d'une case qu'il a cochée. Elle
fait donc passer ma proposition pour son accord, définitivement : à la passe
suivante, plus personne — moi le premier — ne peut savoir qui a décidé. C'est le
seul dégât de ce dispositif qui ne se répare pas, puisqu'on ne sait même pas
qu'il a eu lieu.

Trois formes du même geste, toutes interdites :
- cocher la reco « puisqu'elle s'appliquera de toute façon » — non : **sans
  réponse, la reco s'applique sans être cochée** (§3) ;
- cocher pour « refléter » une réponse donnée dans le chat ou en commentaire —
  la réponse se recopie dans le texte de l'encadré, pas dans une case ;
- recréer un encadré en y remettant des `- [x]` **au-delà** de ce que le relevé
  préalable portait (§4).

Les seuls `- [x]` que j'écris : ceux que je **restitue** lors d'une refonte, relevé en main, à l'identique ; et la case d'une question née verte d'un choix validé, citée
(`Preuve : dispense — …`, voir `chapitres-questions-execution.md`). Aucun autre.

⚠️ Cette règle est répétée au §3 avec le détail des encadrés. Elle est ici parce
qu'elle a été enfouie et oubliée.

### 2. Ne rien coder de livré avant `valide`

**Tant qu'un plan n'est pas au statut `valide`, ne rien coder de livré** : aucune
écriture de fichier dans le dépôt, aucun commit, aucun sous-agent d'implémentation.
Sauf demande explicite dans le message même. Dans le doute, demander plutôt que
supposer.

Une exception, et une seule : le **code jetable** d'un POC (preuve de concept, une
mesure faite avant de choisir) ou d'une répétition à blanc (jouer à l'avance ce que
le plan écrit). Il vit dans le scratchpad, jamais dans le dépôt, et il est supprimé
dès que son résultat est sur la page. La répétition à blanc se joue, elle, dans un
worktree détaché retiré dans la même passe. Le détail est dans le fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`

Cette règle s'oublie d'une seule façon — en étant absorbé par la conception, au
point de commencer « juste un fichier » pour vérifier une hypothèse. Vérifier en
lisant est permis ; vérifier avec un code jetable, dans le scratchpad, aussi ;
vérifier en écrivant du code qui resterait dans le dépôt ne l'est pas.

Une fois le statut à `valide`, l'implémentation ne se fait pas ici : elle relève du
skill **`executer-plan-notion`** (§8).

⚠️ Les valeurs réelles de la propriété `Statut` sont **sans accents** :
`brouillon`, `en revue`, `valide`, `pret`, `en cours`, `a merger`, `execute`. Écrire `exécuté` fait échouer l'appel avec une `validation_error`.

## Quand s'appliquer, quand se taire

Ce skill s'applique **dans tous les modes de l'app sauf un**. Mode par défaut,
`acceptEdits`, `bypassPermissions` : toute demande de plan, d'approche,
d'architecture ou de découpe part dans Notion.

**La seule exception est le mode plan natif de Claude Code.** Quand il est actif,
se taire entièrement : ne pas créer de page, ne pas en proposer, ne pas y faire
allusion. Le plan natif a déjà son cycle complet — rédaction, puis validation
explicite par Benjamin avant la moindre écriture. Deux plans concurrents
produiraient exactement l'ambiguïté que ce dispositif existe pour supprimer :
lequel fait foi. En mode plan, c'est le plan natif, sans partage.

Sortir du mode plan ne rapatrie rien automatiquement dans Notion. Si Benjamin veut
la page après coup, il la demande, et ce skill reprend la main normalement.

Hors mode plan : annoncer en une ligne où le plan va être écrit, puis écrire. Ne
pas demander de confirmation — une page Notion se corrige, et la faire valider
d'avance coûte un tour pour rien.

## Outils nécessaires

Le connecteur **Notion** est indispensable ; il suffit aussi pour les
maquettes, qui vivent dans la page en bloc HTML. Le connecteur **Vercel** ne
sert plus qu'au repli décrit dans le fichier des maquettes (§7). En session
cloud, les connecteurs se choisissent **par session** : s'ils manquent, le dire
immédiatement plutôt que de contourner.

De quoi **rendre une page dans un navigateur et en tirer une image** est nécessaire dès
qu'une contrainte est visuelle — navigateur piloté par MCP, binaire de navigateur en
ligne de commande, ou harnais de test du dépôt. Aucun n'est garanti présent ni
fonctionnel : c'est une image non vide qui le prouve, pas la liste des outils. Son
absence n'est pas bloquante — elle change qui prend la capture, et c'est alors
Benjamin. Voir la sous-section « Les captures d'écran » du chapitre des contraintes (`chapitres-cadrage.md`).


## L'enquête avant les options

Un plan qui découvre à l'exécution ce que le code disait déjà n'a pas planifié : il
a deviné. **Avant d'écrire une question, une option ou une étape, aller chercher ce
qui est déjà su.** Six gisements, du moins cher au plus cher : la session en cours, les plans
antérieurs du projet, le code (agent `enqueteur`), l'historique, la carte du dépôt,
l'extérieur (agent `chercheur`). Pour le code, le pilote dresse d'abord une carte de voisinage légère par le graphe, que l'enquêteur vérifie (détail dans `enquete.md`).

Le budget d'enquête est **proportionnel à l'enjeu**, pas à la longueur du plan. Une
vérification nomme la décision qu'elle peut changer, ou le risque qu'elle couvre —
sinon elle ne se fait pas. La recherche de l'existant est **obligatoire** dès qu'on
crée quelque chose de non propre au projet, et pour la documentation de tout outil
d'un POC, avec une ligne « Existant cherché : … / trouvé : … / fait maison parce que
… » **par artefact**. La répétition à blanc est systématique, le POC de décision
obligatoire dès qu'une option dépend d'une incertitude mesurable, et une option qui
reporte une mesure faisable aujourd'hui n'est pas une option.

Les six gisements, la vérification d'un candidat *use* (seuil de 1 000 étoiles), la
répétition à blanc, le registre des outils et le cas du report de décision :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/enquete.md`

À lire **avant d'écrire la première question, option ou étape** de la passe — le
résumé ci-dessus ne suffit pas à les faire bien.

**Le cadrage avec Hal et la relecture de la page avant `en revue`** : 📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/relecture-par-hal.md`

**Plusieurs plans à croiser — le plan maître.** C'est concevoir chacun d'eux : même
enquête, plan par plan, **en parallèle** (`lecteur`, `enqueteur`, `sondeur`) ; le
pilote ne garde que le croisement et l'écriture. La page, les gestes, la raison :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`

## 1. Trouver le bon projet

La correspondance repo → page projet vit **dans Notion**, pas dans ce fichier —
mais pas là où on l'attend. **Les pages projet ne sont pas dans une base**, donc
elles ne portent aucune propriété. C'est chaque page de plan qui porte `Repo`
(`owner/repo`) et `Projet` (l'URL de la page projet), et la correspondance se lit
donc **dans les plans déjà écrits**.

1. Interroger la base `Plans Claude` : le plan le plus récent dont `Repo` vaut le
   dépôt courant donne l'URL `Projet` à recopier.
2. Sans correspondance : chercher la page projet par nom sous **Clients /
   Projets**, faire confirmer avant d'écrire, puis **renseigner `Repo` et `Projet`
   sur le nouveau plan** — c'est ce qui rendra la fois suivante directe.

⚠️ Un même dépôt peut pointer vers **deux pages projet différentes** selon le
sujet — sur `hermes-custom`, l'infrastructure du VPS et l'automatisation ne vivent
pas au même endroit. Regarder les titres des plans rattachés à chaque URL avant de
choisir. La doc vivante de `hermes-custom`, elle, va toujours au hub Hermes (`_partage/changelog-et-doc.md` § 1).

## 2. Créer la page du plan

- Base **Plans Claude**, dans `IA / Claude`. Chaque page projet porte un bloc
  « Plans Claude » : une vue liée filtrée sur ce projet, du plus récent au plus ancien.
- Titre `[Plan] Nom_du_projet - Titre thématique`, sans date ; icône emoji : `icones.md`.
- Propriétés : `Projet` (**URL** de la page projet — *pas* une relation, les projets
  ne sont pas une base), `Repo` (`owner/repo`), `Statut` = `brouillon`, `Branche`,
  `PR`, `Date`. La base porte aussi `Date execution`, que ce skill ne pose pas.
- **Le deuxième plan d'un projet crée le maître**, sans qu'on le demande. À chaque
  création de page de plan (suite comprise) : maître ouvert du même `Repo` et `Projet` →
  il le rejoint ; sinon un autre plan non terminé → le maître naît ; sinon plan seul.
  Les gestes : `plan-maitre.md`, section du même nom.
- **Une page par sujet, tant que le sujet est vivant.** Les passes suivantes
  modifient cette page ; on n'en crée pas une nouvelle, sinon les fils de
  commentaires restent ancrés sur une page que personne ne rouvre.
- Un plan **clos** ne relance pas ce compteur : si son exécution laisse des étapes
  en échec ou un arbitrage en attente, `executer-plan-notion` ouvre un **plan de
  suite** — page neuve, même titre suffixé `#2` puis `#3`, qui reprend ce qui
  reste. Le `#1` n'est plus modifié, ses fils gardent leur sens là où ils sont.
- **`Branche` se renseigne dès la première version**, et un plan de suite `#N+1` hérite de la branche du précédent : trois cas, à trancher plutôt que laisser vide. Détail des cas et de la règle : 📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/branche-et-suites.md`, à lire à la création d'une page de plan ou d'un plan de suite `#N+1`.
- **Vérifier, pas supposer.** À chaque passe, comparer la branche annoncée par la
  page à celle qui est réellement sortie dans le dépôt. Un écart se **signale à
  Benjamin** au lieu de se corriger en silence : c'est le signe qu'une autre session
  a travaillé ailleurs, et écraser la propriété en effacerait la seule trace.

- Statuts : `brouillon` → `en revue` → `valide` → `pret` → `en cours` →
  `a merger` → `execute` (valeurs **sans accents**, cf. la règle en tête).
  - **`brouillon`** = rédaction partielle ; **`en revue`** = l'agent a **fini de rédiger**,
    Benjamin relit (`_partage/ecrire-dans-notion.md`), **après l'avis de Hal** (`relecture-par-hal.md`) ;
    chaque passe finit par en décider : `_partage/fin-de-passe.md`.
  **`pret`** : préparation prouvée, posé à l'ouverture (`executer-plan-notion` §2), jamais ici.
- **`a merger` et `execute` ne disent pas la même chose**, et les confondre fait
  mentir la base :
  - **`a merger`** — le travail est fait, testé et poussé, et sa **PR est
    ouverte** : le code n'est **pas encore sur `main`** (PR en attente de CI,
    brouillon demandé, CI rouge, merge retenu, trou e2e en attente de décision).
    C'est là que tout plan s'arrête tant que le merge n'est pas vérifié.
  - **`execute`** — le travail est **sur `main`**. Ce statut se pose quand le
    merge est vérifié, et pas une minute avant : c'est la seule façon de lire
    d'un coup d'œil ce qui est réellement livré et ce qui attend encore.
- **`execute` est le terminus**, le seul statut de fin : la valeur `archive` a été
  supprimée de la base le 2026-11-17.

## 3. Structure du plan

Dans cet ordre : `Cartes` · `Besoins` · `Maquette` ·
`Contraintes techniques vérifiées` · `Questions ouvertes` · `La suite` ·
`Exécution` · `Journal d'exécution` · `Commentaires repris`.

**Hiérarchie de titres pensée pour la table des matières.** Notion ne met dans le
sommaire latéral que les blocs *heading* — jamais les encadrés, les listes ni les
to-do. Donc : chaque section ci-dessus est un **H2**, et **chaque question ouverte,
chaque étape d'exécution et chaque entrée du journal portent leur propre H3**
(détail dans les trois sous-sections qui suivent). C'est ce qui permet de sauter
directement à « Q2 », à « Étape 4 » ou au compte rendu de cette étape depuis le
sommaire, au lieu de faire défiler la page.

`Journal d'exécution` est créé **vide** dès la première version, avec une ligne qui
dit qu'il se remplira à l'implémentation. C'est `executer-plan-notion` qui l'écrit ;
le laisser absent obligerait ce skill-là à improviser une place dans la page. Sa
forme, elle, se décide ici (troisième sous-section ci-dessous).

**Sur un plan `Bounded`** (c'est `brainstorming` qui route une demande vers
`Spike`, `Bounded` ou `Architectural` avant que le plan ne s'écrive ; ce skill ne
décide pas du chemin, il applique la structure une fois le routage connu), la
page s'écrit **allégée** : `Cartes` · `Besoins` · `Maquette` · `Exécution` ·
`Journal d'exécution` — `Questions ouvertes` ne s'ajoute que s'il reste une
question à trancher. `Maquette` ne s'allège pas : un petit changement d'écran
est justement celui qu'on croit pouvoir décrire en mots.

**Plan léger** (exception, jamais le défaut) : si Benjamin en demande un, ou avant d'en
proposer un, lire `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-leger.md`. Aiguillage
puis accord de Benjamin d'abord ; sans les deux, plan complet.

Le détail de chaque chapitre vit dans deux fichiers de référence, à lire **avant
d'écrire ou de remettre à jour** le chapitre concerné, pas de mémoire :

- `Cartes`, `Maquette`, `Contraintes techniques vérifiées` (dont la ligne « Existant »,
  l'intertitre « État de départ » et les captures d'écran) — `Cartes` et `Maquette`
  sont présents dès la première version, sur tout plan ; la maquette ou une dispense
  écrite `Pas de maquette — <raison>` ; une contrainte sans provenance est une
  hypothèse et va dans `Questions ouvertes` :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/chapitres-cadrage.md`

- `Questions ouvertes` (un H3 et un encadré par question, cases vides sauf question née verte de choix validé, couleur
  = état), `La suite` (un élément n'y reste que si un autre plan le porte ou s'il attend un événement, et alors sa ligne `suivi` de la base « Restes » (`_partage/restes.md`) le porte : sinon étape du plan, ou plan à part s'il est gros), `Exécution` (tableau de tête, un H3 par étape, champs
  obligatoires, modifications datées) et `Journal d'exécution` (un H3 par entrée) :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/chapitres-questions-execution.md`

## 4. Ce qu'une passe ne doit jamais effacer

Entre deux passes, Benjamin coche, écrit et remarque dans la page : tout cela est de la donnée, jamais du brouillon à écraser. Le protocole d'écriture sans rien casser (relevé avant, recompte après, bleu des retouches, pièges de l'API) vit dans un fichier lu avant la première écriture de la session :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/ne-rien-effacer.md` : à lire avant la première écriture dans une page de plan (passe, refonte ou relecture), pas de mémoire.

**Ceinture — fichier introuvable.** Si la lecture échoue (plugin pas encore
installé, version périmée, fichier supprimé localement) : **le dire en une
ligne avec le chemin, et ne pas écrire dans la page**. Pas de repli « je m'en
souviens à peu près » : ces règles existent précisément parce qu'elles ne se
reconstituent pas de mémoire, et une passe faite au jugé efface des décisions
de Benjamin sans rien signaler. Deux issues, dans cet ordre : **mettre à jour
le plugin** — `claude plugin update plans-notion` (redémarrage requis pour
l'appliquer), ou `claude plugin marketplace update` si la source a bougé — ou
**demander à Benjamin**. Écrire quand même est le seul choix qui n'est pas sur
la table ; lire la page, en revanche, reste permis.

## 5. La boucle de commentaires

À chaque passe, dans cet ordre :

1. Lire les fils **non résolus**, y compris ceux ancrés dans le corps — il faut le
   demander explicitement, sinon on ne voit que les commentaires de niveau page.
2. Les traiter **un par un**. Répondre dans le fil en disant *ce qui a changé dans
   le plan*, pas seulement si on est d'accord.
3. Répercuter dans le plan. L'édition ciblée est le défaut — elle préserve les
   fils vivants et l'état des cases (§4) — mais **le plan prime sur les ancres** :
   si une refonte est meilleure, la faire, relevé en main.
4. Tout commentaire dont l'ancre n'a pas survécu est recopié — son texte et la
   réponse — dans `Commentaires repris`, un bloc par commentaire, par passe.
5. **Relire le plan entier** et raccorder ce que la passe a désaligné : renvois
   entre questions, décisions périmées, décomptes, et le chapitre `Exécution` que
   les réponses viennent de rendre faux.
6. **Ne jamais résoudre un fil soi-même.** C'est l'accusé de réception de
   Benjamin, et c'est ce qui donne gratuitement la liste à traiter à la passe suivante.
7. **Relire les schémas.** Une passe qui a touché `Exécution` a pu rendre « le
   plan en un schéma » faux (chapitre `Cartes`, §3) — le rejouer, puis vérifier
   mécaniquement que le nombre de nœuds d'étape égale le nombre de titres H3
   `Étape N` de la page (contrôle détaillé dans `_partage/schemas.md`).
8. **Poser le `Statut` que l'état de la page justifie** (§2, « Statuts »), en dernier.

Pièges de l'API (commentaire ni déplaçable ni résoluble, écriture qui échoue en
silence) : fichier partagé, §4.

## 6. Lecture économe

Garder un miroir du plan hors du dépôt, avec l'horodatage de dernière modification
de la page **et le relevé préalable (§4)** — cases cochées et textes libres. À chaque
passe : lire les fils (quelques centaines de tokens), ne recharger la page entière que
si elle a changé côté Notion ou pour la relecture finale. **Le miroir est un cache,
jamais une source de vérité** : absent, on recharge. Le relevé se refait toujours
sur la page fraîche avant une refonte : c'est entre deux sessions que Benjamin coche.

## 7. Maquettes HTML

Dès qu'un chapitre `Maquette` en exige une, la maquette cherche d'abord le design system du dépôt, puis se pose dans la page en bloc HTML, sans Vercel. Le détail (design system, geste en deux appels, poids, repli) vit dans un fichier lu avant de poser une maquette :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/maquettes.md` : à lire avant de poser ou de remplacer une maquette, pas de mémoire.

## 8. Passer la main à l'exécution

Quand Benjamin valide le plan, le chapitre `Exécution` est répercuté d'abord, puis le plan passe au filtre de l'enquête (quinze vérifications), puis `Statut` passe à `valide` et `executer-plan-notion` prend la suite. Ce skill ne code jamais, même après `valide`. La procédure, le filtre et ce que `executer-plan-notion` prend en charge vivent dans un fichier lu à ce moment-là :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/passer-la-main.md` : à lire quand Benjamin valide le plan ou demande `valide`, pas de mémoire.

## 9. Ce que ce skill ne fait pas

- Il ne code pas, jamais — même après `valide`. C'est `executer-plan-notion`.
  (Le code jetable d'un POC ou d'une répétition à blanc n'est pas du code livré :
  règle 2.)
- Il ne résout pas les fils de commentaires.
- Il n'ouvre pas de PR et ne merge rien : la PR du plan est ouverte par la
  clôture de `executer-plan-notion`.
- Il ne dépend d'aucun `CLAUDE.md`, d'aucun hook, d'aucun fichier du dépôt de
  travail. Ses compagnons sont les fichiers partagés
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-claude-code.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-connecteurs-et-evals.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-code-et-securite.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-infra-et-documents.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-donnees-publiques.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/restes.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/relecture-par-hal.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/fin-de-passe.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/changelog-et-doc.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md` et
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/bons-tests.md`, ses quatre fichiers de
  référence (`enquete.md`, `chapitres-cadrage.md`,
  `chapitres-questions-execution.md` et `plan-maitre.md`, dans ce dossier), ainsi que les
  agents `${CLAUDE_PLUGIN_ROOT}/agents/enqueteur.md`,
  `${CLAUDE_PLUGIN_ROOT}/agents/chercheur.md` et
  `${CLAUDE_PLUGIN_ROOT}/agents/lecteur.md`, livrés par le plugin
  `plans-notion` — pas par le dépôt de travail, quel qu'il soit.
