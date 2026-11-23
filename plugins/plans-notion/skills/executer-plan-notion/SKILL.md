---
name: executer-plan-notion
description: >-
  Implémente un plan cadré dans Notion : vérification du statut, découpe en étapes, sous-agents, journal sur la page, statut final. À charger AVANT toute ligne de code dès que Benjamin donne le feu vert sur un plan (« go », « vas-y »), pour reprendre un chantier commencé (« reprends là où on s'est arrêté ») et pour ouvrir la PR ou remonter sur `main` un travail livré (« ouvre la PR »), même sans code écrit dans la session. Déclencheurs complets : section « Quand charger ce skill ». Ne couvre ni la conception du plan (skill plan-notion), ni une tâche sans plan.
---

# Exécuter un plan Notion

## Invariants — ce qui tient même après un compactage

Un compactage du contexte ne recolle que le début de ce fichier : ce qui ne
doit jamais se perdre est donc ici, une ligne chacun, avec la section qui le
détaille.

- **Après un compactage, ré-invoquer ce skill** (outil `Skill`) avant
  d'écrire dans Notion ou de lancer une étape — le compactage ne garde que le
  début du skill.
- **Rien avant `valide`, aucune étape avant `pret`** : lire le `Statut` de la
  page avant toute ligne de code ; `valide` → préparation complète (§2) puis
  `pret` ; `en cours` ne se pose que sur une page `pret` (« La porte d'entrée »).
- **`Statut` sans accents** : `brouillon`, `en revue`, `valide`, `pret`,
  `en cours`, `a merger`, `execute` (« La porte d'entrée »).
- **Ne jamais cocher une case** de Benjamin : le seul `- [x]` écrit est celui
  que le relevé portait déjà, ou une question née verte citée (§5, `ecrire-dans-notion.md`).
- **Relevé avant d'écrire, recompte après** : chaque écriture Notion part du
  relevé du §1 et se vérifie en recomptant (§5).
- **Jamais `--no-verify`**, ni check désactivé, ni test rendu tolérant : une
  preuve rouge se corrige (§3, « Une étape = un commit… »).
- **La clôture ouvre la PR vers `main`, prête** (brouillon seulement sur demande
  de Benjamin, ou le temps d'écrire la ligne `Doc :` là où le job `doc` saute les
  brouillons : `cloture.md`, points 5 et 7, qui la passent prête) ; la CI la merge, la session ne merge jamais (§6, « La PR, puis
  la remontée sur `main` »). Un trou e2e non couvert par la CI se pose à Benjamin
  avant l'ouverture. **La session suit la PR jusqu'au merge**, puis met à jour le
  plan, le maître et le Récap dans le même tour.
- **Un plan d'un lot ne démarre jamais seul** : `depart-dans-le-lot.py` à 0 (§2).
- **Aucune clôture sans preuve de chaque étape** : `preuves-des-etapes.py
  --avant` à l'ouverture, `--apres` avant le push (§2, §6).
- **Découvertes hors plan** : une seule règle de tri, dans
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md` — question à Benjamin si
  elle touche une décision, la sécurité, l'irréversible ou une dépense ; sinon,
  réversible et petite → étape `D<n>`. Elle vaut à l'ouverture (§2) comme pendant
  l'exécution (§4). Un secret ne se corrige jamais seul.

## Suis-je la bonne version ?

Un skill ne choisit pas d'où il est chargé (copie synchronisée périmée, version
plus ancienne que celle installée) ; il peut seulement le constater. À vérifier
au chargement, en une commande :

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-version.sh" "${CLAUDE_PLUGIN_ROOT}"
```

Code 0 : à jour. Code 1 : écart de version ou de chemin (le message dit
lequel). Code 2 : lecture impossible. Écart → le dire à Benjamin en une ligne,
puis lire ce `SKILL.md` et `_partage/` depuis l'`installPath` d'`installed_plugins.json`
(plugin `plans-notion@atelier`), pas depuis la copie chargée. Pour charger la
plus récente : `claude plugin update plans-notion@atelier` (redémarrage
requis) ; en session cloud, le setup script pose déjà la dernière version
publiée — jamais plus loin que ce que `main` du dépôt porte. Ce que cette
garde ne règle pas : une copie qui ne l'embarque pas ne préviendra jamais — elle
protège à partir de la version qui la porte. (Historique : `docs/retex/executer-plan-notion.md`.)

## La porte d'entrée

**Aucune ligne de code avant d'avoir lu le `Statut` de la page du plan.**

- `valide` → **préparer** (§2, `ouverture.md`) : aucune étape ne démarre, même
  sur un « go » de Benjamin. La préparation finie et prouvée, `Statut` = `pret`,
  puis `en cours` dans la même séance (règle du « go », plus bas).
- `pret` → la préparation est faite : relire la page et les fils non résolus
  (§1). Une case, un texte libre ou un commentaire postérieur à l'entrée
  `Ouverture` du journal renvoie à `valide` et refait la préparation ; sinon
  `preparation-prete.py` rend 0 (mêmes arguments) et, pour un plan du lot,
  `depart-dans-le-lot.py` aussi ; `Statut` = `en cours`, première étape.
- `a merger` ou `execute` → **le travail est déjà fait**, sa PR en attente de
  merge pour le premier, `main` pour le second. S'arrêter et le
  dire : refaire une exécution terminée est le plus coûteux des malentendus.
  **Une exception, et une seule** : à `a merger`, la suite n'est pas une
  réexécution mais la fin de la clôture (§6) : suivre la CI de la PR, marquer
  prête une PR brouillon si Benjamin le demande, traiter ce qui retient le
  merge — et poser `execute` dans le tour où le merge est constaté sur `main`,
  qui peut être un tour après la clôture. Une PR déjà mergée à la reprise se
  vérifie sur pièce, et `execute` se pose ; une PR encore ouverte se suit.
- `brouillon` (rédaction pas finie), `en revue` (en attente de relecture) → s'arrêter et
  le dire. Un plan pas encore validé est une proposition, pas une commande : coder
  dessus, c'est produire un travail que Benjamin n'a jamais accepté.
- `en cours` → une exécution est déjà commencée (donc passée par `pret`). Lire le `Journal d'exécution`
  avant tout et reprendre où elle s'est arrêtée, plutôt que de repartir de zéro.
- Benjamin qui dit « go » ne remplace pas le statut. Il le dit de mémoire, la page
  dit ce qui a été tranché. **En cas de désaccord entre les deux, demander** — ça
  coûte un tour, refaire une implémentation en coûte dix.
- **Case cochée = décision ; session pilotable par Hal** : dès `valide`, une case cochée (même hors
  reco) ne se redemande pas, et pas d'`AskUserQuestion` : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/pilotable-par-hal.md`.
- **Un « go » sur un plan `valide` suffit à lancer l'exécution** : il ne se redemande pas,
  il enchaîne sur le `Statut` et la préparation prouvée. Outre les arrêts prévus dans ce skill
  (maquette, connecteur Notion, statut), la session s'arrête sur un choix de sécurité majeur,
  financier ou irréversible non validé par Benjamin, et le lui pose (Benjamin, 2026-10-16 :
  « sauf choix de sécu majeur, financier ou irréversible que je n'aurais pas déjà validé »).

⚠️ Les valeurs de `Statut` sont **sans accents** : `brouillon`, `en revue`,
`valide`, `pret`, `en cours`, `a merger`, `execute`. Écrire `exécuté`
ou `prêt` fait échouer l'appel (le hook du plugin refuse aussi).

Le connecteur **Notion** est indispensable. S'il manque, le dire immédiatement
plutôt que de contourner : exécuter sans pouvoir écrire le journal produit un
travail dont il ne reste aucune trace hors du fil de discussion, et le fil
disparaît au compactage du contexte.

## Quand charger ce skill

- **Feu vert sur un plan cadré** : « go », « vas-y », « on y va », « attaque », « tu peux coder », « lance l'implémentation », « déroule le plan », « on passe à la réalisation », « c'est bon pour moi ». Vaut même si ni Notion ni le mot « plan » ne sont cités, même si seule une partie des étapes est demandée, et même si le plan n'est pas encore validé : c'est ce skill qui dit quoi faire (« La porte d'entrée »).
- **Reprise d'un chantier commencé** : « reprends là où on s'est arrêté », « continue le refacto », « t'en étais à l'étape 2 », « on continue l'exécution ». Commencer par remettre le chapitre `Exécution` à jour des dernières réponses et commentaires de Benjamin (§2).
- **PR ou remontée sur `main`** d'un travail déjà livré : « ouvre la PR », « merge sur main », « tu peux merger directement », « pousse ça sur main ». Vaut aussi dans une session où rien n'a été codé : la clôture ouvre la PR, prête, suit la CI et fait passer la page de `a merger` à `execute` (§6).

## 1. Charger le plan

1. Retrouver la page : base **Plans Claude**, dans `IA / Claude`, reliée à la page
   projet dont la propriété `Repo` correspond au dépôt courant.
2. Lire la page **entière**, pas seulement le chapitre `Exécution`. Les décisions
   vivent aussi dans les cases cochées et dans le texte libre écrit après
   `Autre / complément →`, que `get-comments` ne montre pas.
3. Lire les fils de commentaires **non résolus** — il faut demander explicitement
   ceux ancrés dans le corps, sinon on ne voit que ceux de niveau page. Un fil non
   résolu qui contredit le chapitre `Exécution` bloque l'étape concernée : le
   signaler plutôt que de trancher seul.
4. **Relever, question par question, les cases cochées et les textes libres.** Ce
   relevé est le garde-fou de chaque écriture ultérieure (§5) ; sans lui, une
   refonte de section efface silencieusement les décisions de Benjamin.
   Le relevé des cases se calcule par script, sur le miroir local de la page
   (sortie de `notion-fetch`) : `python3
   "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/compter-cases.py" <page.md>
   > <releve.json>` écrit sur la sortie standard le JSON seul `{"Q1": 1, …}` —
   le fichier `<releve.json>` sert au recompte du §5 ; le `total : n` part sur
   la sortie d'erreur, à l'écran.

## 2. Préparer, puis ouvrir l'exécution

**Le chapitre `Exécution` est presque toujours en retard d'un tour** : Benjamin
répond dans la page, passe `Statut` à `valide` et enchaîne sur ce skill sans
repasser par `plan-notion`. Avant la première étape, sans exception : reprendre
le relevé du §1, confronter chaque réponse au chapitre étape par étape, écrire
ce qui change en édition ciblée et **daté** (`_maj 2026-08-21 — …_`), écrire
aussi une réponse qui ne change rien (`_Q2 confirme l'approche, étape
inchangée._`), relire le chapitre entier — c'est lui seul qui part dans les
briefs. Cette passe met le plan à jour, elle ne le redessine pas : si
l'approche est en cause, repasser par `plan-notion` et ne rien coder.

**La porte des preuves, avant la première étape** : `preuves-des-etapes.py
<page.md> --avant` rend 0 si chaque étape du chapitre porte une `Preuve de
fin` ; sinon la remise à jour la pose, datée, et on ne code pas
(`ouverture.md`).

Puis, dans le même tour, avant la première étape :

- **Maquette** : une étape à `Impact fonctionnel` autre que « Rien » exige une
  maquette ou une dispense datée ; sinon s'arrêter et le dire.
- **Questions restées orange** → vert, `(reco appliquée par défaut)`.
- **Créer la branche du plan dans un worktree**
  (`~/repos/worktrees/<repo>/<branche-kebab>`, depuis `origin/main` à jour),
  jamais dans le checkout principal, jamais de travail sur `main`. `git fetch` d'abord (copie à jour de la principale distante : `_partage/fraicheur-du-depot.md`).
- **Relever ce qui déclenche la CI** (un `push` lance-t-il un run ? des e2e ?
  que fait le label `review-required` ? un job merge-t-il seul ?) et
  **calculer les vagues** (`vagues.py`) ; les deux relevés s'écrivent dans
  les puces **CI** et **Vagues** de l'entrée `Ouverture` du journal (§4).
- **Réglage du pilote : Sonnet 5.5, effort `medium`**, contrainte de lancement. À
  vérifier **avant le premier geste de ce §**, d'après ce que la session sait de son
  modèle et de son effort. Une session qui n'est pas à ce réglage ne prépare ni ne
  code : elle ouvre une **sous-session visible** à ce réglage (lien Desktop ou ligne
  de terminal, jamais `claude -p` en silence) et s'arrête (`ouverture.md`, « Le
  réglage du pilote »). Seul Benjamin déroge,
  dans son message. La puce `**Pilote** : <modèle>, <effort>` de l'entrée `Ouverture`
  dit ce qui a servi (p.ex. `Sonnet 5.5, medium`), et `preparation-prete.py` refuse
  `pret` sinon. Pourquoi Sonnet : c'est le modèle du banc d'évals (`EVALS_MODELE` de
  `evals/outillage/lancer.sh`) ; `medium` n'y est pas mesuré (le banc joue `high`).
  La conception (`plan-notion`) reste en Opus.

Un plan ne passe `pret` que si toutes ses étapes sont prouvées et rejouées à blanc, ses vagues calculées, et son orchestration écrite s'il a un plan maître ; `preparation-prete.py` tranche (code 0, sinon pas de `pret`, donc pas d'étape). Détail : `porte-du-pret.md`.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/porte-du-pret.md` — **à lire avant de poser `pret`** : les gestes qui laissent chacun une puce dans l'entrée `Ouverture`, et la commande de contrôle.

**Par défaut, un plan = une seule branche, sans PR d'étape** : les étapes sont
des commits sur la branche du plan, et la PR du plan s'ouvre à la clôture,
prête (§3, §6). Une autre organisation ne se fait que si Benjamin la demande.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/ouverture.md` — **à lire en entier à l'ouverture**, avant la première
étape : la procédure de remise à jour du chapitre, la vérification de la
maquette, les commandes de relevé de la CI, le calcul des vagues et la
raison de la règle « une branche, pas de PR d'étape ».

Une session peut aussi porter **plusieurs plans** à la fois : tout ce qui
précède vaut alors pour chacun, **sauf la fiche locale** (une seule, pour le
premier plan ouvert : « Plusieurs plans », plus bas).

## 3. Dérouler les étapes

Le chapitre `Exécution` de la page est la feuille de route ; il ne se réécrit
pas pour raconter l'avancement, qui va dans `Journal d'exécution` (§4).

- **Une étape = un commit sur la branche du plan**, prouvé en local : pas de PR d'étape ; une sous-branche seulement pour une étape `Relecture : étape` (`vagues.md`).
  La preuve, ce sont **les tests des fichiers
  impactés** (liste réelle, `git diff --name-only`), **jouée par le
  pilote** (la session qui orchestre le plan), jamais la suite complète ni les e2e — ceux-là passent une fois, à
  la clôture (§6). Rouge → on corrige jusqu'au vert, jamais de contournement ;
  seul un correctif structurant (ou un échec qu'on ne sait plus diagnostiquer)
  part à l'arbitrage de Benjamin, sur une branche de côté `-etape-N-en-echec`.
  Étape qui écrit du code testé : deux commits, rouge puis vert.
- **La délégation est la règle** : charger ce skill vaut demande de déléguer.
  Pilote en Sonnet effort `medium`, **un appel `Agent` par étape**
  (`subagent_type: "plans-notion:executant"`, nom qualifié, aucun paramètre
  `model` ni `effort`, sauf l'escalade bornée (`etapes.md`) et la correction
  `D<n>` de cron (`model: "sonnet"`), voir
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md` : l'agent porte
  `haiku` et `effort: high`), en séquence
  par défaut, en parallèle par
  vagues ou regroupées quand `vagues.md` le prescrit. Une exécution sans
  aucun appel `Agent` est un défaut.
- **Le brief** porte, à chaque fois : l'objectif recopié, le contexte, la
  liste fermée des fichiers, la commande de preuve (et son délai), ce que le
  sous-agent ne fait pas, le format du rapport en cinq pièces.
- **Après chaque étape** : rejouer la preuve, vérifier au premier `executant`
  le modèle réellement servi (`modele-sous-agent.py`), commiter, faire relire par
  `relecteur` (`revue.md`), relire les faits que l'`executant` a versés au
  `fact_store` à chaque clôture de lot (`etapes.md`), écrire l'entrée de journal, afficher un récap, puis
  **enchaîner sans demander la main** : l'autonomie est le défaut, on ne
  s'arrête que sur ce qui rendrait la suite fausse ou irréversible.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md` — **à lire avant la première étape, puis à chaque étape** :
le détail de la preuve locale et de la boucle rouge, l'appel `Agent` exact, le
brief complet, ce qui reste chez le pilote, la liste « Après chaque
étape » et les cas où l'on s'arrête.

Étape testée : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/preuve-du-rouge.md` ; vagues :
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md` ; relecture :
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md` ; maquettes :
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md` — les renvois à ces
fichiers, et au jeton des actions lourdes
(`${CLAUDE_PLUGIN_ROOT}/skills/_partage/machine-partagee.md`), sont dans
`etapes.md` à l'endroit où ils servent. L'agent lui-même :
`${CLAUDE_PLUGIN_ROOT}/agents/executant.md`.

## 4. Le journal, et les écarts

Après **chaque** étape, écrire dans `Journal d'exécution` — et dans le miroir local
du plan : c'est le briefing du sous-agent suivant, et ce qui permet de reprendre
après un compactage. Règles qui ne bougent pas :

Elles tiennent en cinq points : ordre des numéros d'étape, un titre H3 par entrée, une ligne `**Découvertes**` obligatoire, un écart écrit aux deux endroits, un secret jamais corrigé seul. Détail : `journal-regles.md`.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/journal-regles.md` — **à lire avant chaque entrée de journal** : le texte exact des cinq règles.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/journal.md` — **à lire avant d'écrire la première entrée de journal** :
le contenu exact d'une entrée, les trois libellés, les deux traitements
possibles d'une découverte, le contrôle mécanique des libellés à la clôture.

## 5. Écrire dans la page sans rien casser

La page porte des décisions de Benjamin que le fil de discussion ne contient pas :
cases cochées, texte libre après `Autre / complément →`, remarques dans le corps.
Une écriture maladroite les efface sans rien signaler.

**Les règles vivent dans un fichier partagé avec `plan-notion` :**

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`

Le protocole en cinq temps — relever avant d'écrire, éditer de façon ciblée,
remettre les `- [x]` en cas de refonte, ne jamais reformuler Benjamin, vérifier
après coup — et les cinq pièges de l'API : `update_content` qui ne décoche pas,
l'écriture qui échoue en silence, le commentaire qu'on ne résout jamais
soi-même, `replace_all_matches` jamais employé sur un motif fait de caractères
de balisage, et une insertion jamais ancrée au milieu d'un paragraphe formaté —
toujours sur une frontière de bloc.

Deux règles de plus, avant la première écriture Notion de la session : le **bleu des retouches** (la remise à jour du chapitre `Exécution` décolore le bleu de la passe précédente) et la **ceinture** (fichier de règles introuvable : le dire en une ligne, ne rien écrire dans la page).

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/ecrire-dans-la-page.md` — **à lire avant la première écriture Notion de la session** : le détail du bleu et de la ceinture.

Le relevé du §1 est la liste de contrôle de tout ça : sans lui, pas de refonte de
section. **Le recompte des cases cochées après une écriture se joue par script**,
sur le miroir local relu après l'écriture :
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/compter-cases.py" <page.md> --releve <releve.json>`
(`<releve.json>` : le fichier écrit par `… <page.md> > <releve.json>` au §1 ;
0 : identique au relevé ; 1 : une ligne par écart ; 2 : fichier illisible ou
section « Questions ouvertes » absente).

## 6. Clore

Dans le **même tour** que le compte rendu à Benjamin, jamais « plus tard »
(sauf `execute`, qui suit le merge : voir plus bas) :

Les points de clôture, dans l'ordre : `Statut` (`a merger` tant que le code n'est pas sur `main`, `execute` une fois le merge vérifié), `Branche` et `PR`, `Journal d'exécution` clos par `État final`, récap, preuve doc, porte des preuves, PR prête suivie jusqu'au merge (la CI merge seule).

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/points-de-cloture.md` — **à lire à la clôture, avant le `Statut` de fin et avant le push** : le détail de chaque point, suite complète en local comprise.

Quand Benjamin demande « ouvre la PR » ou « merge sur main » : si la PR du plan
n'existe pas encore, elle s'ouvre comme à la clôture (une seule, de la branche
vers `main`, le label décidé en regardant ce dépôt-là) ; si elle existe, on la
suit jusqu'au merge. Un trou e2e non couvert retient cette ouverture : la question
part à Benjamin d'abord, sa demande ne le couvrait pas. **La session ne lance
jamais `gh pr merge`, même sur
demande** : c'est la CI qui merge. `Statut` = `execute` dans le tour où le
merge est constaté sur `main`.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture.md` — **à lire à la clôture, et à chaque demande de PR ou de
remontée sur `main`** : le noyau, qui donne l'ordre des points et renvoie aux trois fichiers lus quand la clôture y arrive.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-reste-et-suite.md` — lu quand l'`État final` s'écrit, que le reste à faire se trie ou que le compte rendu se rédige.
📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-doc.md` — lu quand la clôture en est à la preuve doc ou à la doc (Récap, Changelog, fiches, ligne `Doc :`).
📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-pr-et-ci.md` — lu avant le push, pour la PR, la CI et la remontée sur `main`, avec la ligne `Evals`.

## 7. Le reste à faire, et le plan de suite

Rien ne reste sans destination : avant `a merger`, chaque ligne du reste se trie (question à Benjamin, étape `D<n>`, ou plan de suite au-delà d'une étape) ; ce qui attend un geste de Benjamin va dans la base « Restes ».

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/reste-a-faire.md` — **à lire à chaque clôture, avant `a merger`** : le tri détaillé et la règle du plan de suite.

## Plusieurs plans

Un pilote unique conduit tous les plans ; chaque plan garde sa porte, sa branche, son worktree, son journal et sa clôture ; un pool glissant d'une douzaine de places est partagé ; le parallèle entre plans est le défaut, sauf ressource partagée ; un plan maître coiffe les plans d'une session. Une seule fiche locale, pour le premier plan.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/plusieurs-plans.md` — **à lire dès qu'une session porte au moins deux plans**, avant de lancer le second.

## 8. Ce que ce skill ne fait pas

Les refus principaux : ne pas concevoir le plan (`plan-notion`), ne pas coder sans `valide`, ne jamais merger ni poser `execute` sans merge constaté, ne pas écrire soi-même le code des étapes déléguables, ne pas relire le diff à la place du relecteur, ne jamais coder dans le checkout principal, pas de PR d'étape, ne pas résoudre les fils. Détail : `hors-perimetre.md`.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/hors-perimetre.md` — **à lire quand une demande touche la frontière du skill** (concevoir, merger, coder hors `valide`, relire soi-même).

- Il ne dépend d'aucun `CLAUDE.md`, d'aucun hook, d'aucun fichier du dépôt de
  travail. Ses compagnons sont les fichiers partagés
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/demander-a-hal.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/remontee-sur-main.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/restes.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/preuve-du-rouge.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/grille-doc.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/bons-tests.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/machine-partagee.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cout-des-plans.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ranger-claude-md.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/fraicheur-du-depot.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/changelog-et-doc.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/pilotable-par-hal.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-claude-code.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-connecteurs-et-evals.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-code-et-securite.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-infra-et-documents.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-donnees-publiques.md`, livrés par le plugin `plans-notion` — pas par le dépôt de travail, quel qu'il soit.
