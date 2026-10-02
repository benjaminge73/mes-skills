---
name: executer-plan-notion
description: >-
  Implémente un plan de travail cadré dans Notion — vérification du statut avant de coder, découpe en étapes, sous-agents, journal d'exécution écrit sur la page, statut final. À charger AVANT d'écrire la moindre ligne de code dès que Benjamin donne le feu vert sur un travail déjà cadré, par exemple « go », « vas-y », « on y va », « attaque », « tu peux coder », « lance l'implémentation », « déroule le plan », « on passe à la réalisation », « c'est bon pour moi ». À charger aussi pour reprendre un chantier commencé — « reprends là où on s'est arrêté », « continue le refacto », « t'en étais à l'étape 2 », « on continue l'exécution ». À charger aussi quand Benjamin demande la PR ou la remontée sur `main` d'un travail déjà livré — « ouvre la PR », « merge sur main », « tu peux merger directement », « pousse ça sur main » — y compris dans une session où rien n'a été codé : la PR ne s'ouvre que sur sa demande, et ce skill fait passer la page de `a merger` à `execute`. Vaut même si ni Notion ni le mot « plan » ne sont cités, même si seule une partie des étapes est demandée, et même si le plan n'est pas encore validé, car c'est ce skill qui dit quoi faire dans ce cas. Commence toujours par remettre le chapitre Exécution à jour des dernières réponses et commentaires de Benjamin. Ne couvre pas la conception du plan, qui relève du skill plan-notion, ni une tâche isolée sans plan derrière.
---

# Exécuter un plan Notion

## Invariants — ce qui tient même après un compactage

Un compactage du contexte ne recolle que le début de ce fichier : ce qui ne
doit jamais se perdre est donc ici, une ligne chacun, avec la section qui le
détaille.

- **Après un compactage, ré-invoquer ce skill** (outil `Skill`) avant
  d'écrire dans Notion ou de lancer une étape — le compactage ne garde que le
  début du skill.
- **Rien avant `valide`** : lire le `Statut` de la page avant toute ligne de
  code (« La porte d'entrée »).
- **`Statut` sans accents** : `brouillon`, `en revue`, `valide`, `en cours`,
  `a merger`, `execute`, `archive` (« La porte d'entrée »).
- **Ne jamais cocher une case** de Benjamin : le seul `- [x]` écrit est celui
  que le relevé portait déjà (§5, `_partage/ecrire-dans-notion.md`).
- **Relevé avant d'écrire, recompte après** : chaque écriture Notion part du
  relevé du §1 et se vérifie en recomptant (§5).
- **Jamais `--no-verify`**, ni check désactivé, ni test rendu tolérant : une
  preuve rouge se corrige (§3, « Une étape = un commit… »).
- **Pas de PR vers `main` sans demande explicite** de Benjamin : l'exécution
  s'arrête à la branche (§6, « La PR, puis la remontée sur `main` »).
- **Découvertes hors plan** : réversible, hors sécurité et petite → étape
  `D<n>` ; sinon question à Benjamin ; un secret ne se corrige jamais seul et
  sa valeur ne s'écrit nulle part (§4, « Découvertes hors plan »).

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

- `valide` → on y va.
- `a merger` ou `execute` → **le travail est déjà fait**, sur sa branche pour le
  premier, sur `main` pour le second. S'arrêter et le dire : refaire une
  exécution terminée est le plus coûteux des malentendus.
  **Une exception, et une seule** : à `a merger`, Benjamin peut demander la
  **PR du plan, ou la remontée sur `main`**. Ce n'est pas une réexécution,
  c'est la dernière opération du plan — la faire (§6), et poser `execute` dans
  le même tour si le code part sur `main`.
- `brouillon`, `en revue` → s'arrêter et le dire. Un plan pas encore validé est
  une proposition, pas une commande : coder dessus, c'est produire un travail que
  Benjamin n'a jamais accepté.
- `en cours` → une exécution est déjà commencée. Lire le `Journal d'exécution`
  avant tout et reprendre où elle s'est arrêtée, plutôt que de repartir de zéro.
- Benjamin qui dit « go » ne remplace pas le statut. Il le dit de mémoire, la page
  dit ce qui a été tranché. **En cas de désaccord entre les deux, demander** — ça
  coûte un tour, refaire une implémentation en coûte dix.

⚠️ Les valeurs de `Statut` sont **sans accents** : `brouillon`, `en revue`,
`valide`, `en cours`, `a merger`, `execute`, `archive`. Écrire `exécuté` fait
échouer l'appel avec une `validation_error`.

Le connecteur **Notion** est indispensable. S'il manque, le dire immédiatement
plutôt que de contourner : exécuter sans pouvoir écrire le journal produit un
travail dont il ne reste aucune trace hors du fil de discussion, et le fil
disparaît au compactage du contexte.

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

## 2. Ouvrir l'exécution

**Le chapitre `Exécution` est presque toujours en retard d'un tour** : Benjamin
répond dans la page, passe `Statut` à `valide` et enchaîne sur ce skill sans
repasser par `plan-notion`. Avant la première étape, sans exception : reprendre
le relevé du §1, confronter chaque réponse au chapitre étape par étape, écrire
ce qui change en édition ciblée et **daté** (`_maj 2026-08-21 — …_`), écrire
aussi une réponse qui ne change rien (`_Q2 confirme l'approche, étape
inchangée._`), relire le chapitre entier — c'est lui seul qui part dans les
briefs. Cette passe met le plan à jour, elle ne le redessine pas : si
l'approche est en cause, repasser par `plan-notion` et ne rien coder.

Puis, dans le même tour, avant la première étape :

- **Maquette** : une étape à `Impact fonctionnel` autre que « Rien » exige une
  maquette ou une dispense datée ; sinon s'arrêter et le dire.
- **Questions restées orange** → vert, `(reco appliquée par défaut)`.
- `Statut` = `en cours`, propriété `Branche` renseignée.
- **Créer la branche du plan dans un worktree**
  (`~/repos/worktrees/<repo>/<branche-kebab>`, depuis `origin/main` à jour),
  jamais dans le checkout principal, jamais de travail sur `main`.
- **Relever ce qui déclenche la CI** (un `push` lance-t-il un run ? des e2e ?
  que fait le label `review-required` ? un job merge-t-il seul ?) et
  **calculer les vagues** (`vagues.py`) ; les deux relevés s'écrivent dans
  l'entrée `Ouverture` du journal (§4).

**Par défaut, un plan = une seule branche, et aucune PR tant que Benjamin ne la
demande pas** : les étapes sont des commits sur la branche du plan, et
l'exécution s'arrête à la branche (§3, §6). Une autre organisation ne se fait que
si Benjamin la demande.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/ouverture.md` — **à lire en entier à l'ouverture**, avant la première
étape : la procédure de remise à jour du chapitre, la vérification de la
maquette, les commandes de relevé de la CI, le calcul des vagues et la
raison de la règle « une branche, pas de PR ».

Une session peut aussi porter **plusieurs plans** à la fois : tout ce qui
précède vaut alors pour chacun, et la section « Plusieurs plans », plus bas,
dit ce qui s'y ajoute.

## 3. Dérouler les étapes

Le chapitre `Exécution` de la page est la feuille de route ; il ne se réécrit
pas pour raconter l'avancement, qui va dans `Journal d'exécution` (§4).

- **Une étape = un commit sur la branche du plan**, prouvé en local : pas de
  sous-branche, pas de PR d'étape. La preuve, ce sont **les tests des fichiers
  impactés** (liste réelle, `git diff --name-only`), **jouée par le
  pilote** (la session qui orchestre le plan), jamais la suite complète ni les e2e — ceux-là passent une fois, à
  la clôture (§6). Rouge → on corrige jusqu'au vert, jamais de contournement ;
  seul un correctif structurant (ou un échec qu'on ne sait plus diagnostiquer)
  part à l'arbitrage de Benjamin, sur une branche de côté `-etape-N-en-echec`.
  Étape qui écrit du code testé : deux commits, rouge puis vert.
- **La délégation est la règle** : charger ce skill vaut demande de déléguer.
  Pilote en Opus effort high, **un appel `Agent` par étape**
  (`subagent_type: "plans-notion:executant"`, nom qualifié, aucun paramètre
  `model` : l'agent porte `sonnet`), en séquence par défaut, en parallèle par
  vagues ou regroupées quand `vagues.md` le prescrit. Une exécution sans
  aucun appel `Agent` est un défaut.
- **Le brief** porte, à chaque fois : l'objectif recopié, le contexte, la
  liste fermée des fichiers, la commande de preuve (et son délai), ce que le
  sous-agent ne fait pas, le format du rapport en cinq pièces.
- **Après chaque étape** : rejouer la preuve, commiter, faire relire par
  `relecteur` (`revue.md`), relire le diff de la mémoire de l'`executant` à
  chaque clôture de lot, écrire l'entrée de journal, afficher un récap, puis
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

- **dans l'ordre des numéros d'étape**, pas dans l'ordre d'arrivée des rapports ;
- **une entrée = un titre H3**, repris mot pour mot du chapitre `Exécution` :
  `Étape N — <titre court>` ; `Ouverture` au démarrage, `État final` à la
  clôture (§6) ;
- **une ligne `Découvertes :` obligatoire** dans chaque entrée d'étape —
  `aucune`, ou la liste, chacune avec son libellé (`découverte — trouvable au
  plan` / `découverte — pas trouvable`, jamais un autre) **et** son traitement
  (étape `D<n>` ou question à Benjamin) ; dans le doute, `trouvable` ;
- **un écart** entre prévu et fait s'écrit aux deux endroits : ligne `écart` au
  journal et correction **datée** dans l'étape du chapitre `Exécution` ;
- **un secret** découvert ne se corrige jamais seul et sa valeur ne s'écrit
  nulle part.

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

Il porte aussi **« Le bleu des retouches »**, et cette règle-là s'applique ici pour
une raison précise : **la remise à jour du chapitre `Exécution` en ouverture est une
retouche du plan comme une autre** (§2). Elle décolore donc le bleu de la passe
précédente avant d'écrire, et marque en bleu ce qu'elle change — sans quoi la page
garderait un bleu périmé qui désignerait les mauvaises lignes. Le `Journal
d'exécution`, lui, ne se colore pas : il s'écrit par ajout, chaque entrée y est neuve
par construction.

**Le lire avant la première écriture Notion de la session**, pas de mémoire. Cette
session-ci en fait beaucoup : la remise à jour du chapitre `Exécution` (§2), une
entrée de journal par étape (§4), la clôture (§6). Une seule de ces écritures
faite de travers coûte les décisions d'une passe entière.

Le relevé du §1 est la liste de contrôle de tout ça : sans lui, pas de refonte de
section. **Le recompte des cases cochées après une écriture se joue par script**,
sur le miroir local relu après l'écriture :
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/compter-cases.py" <page.md> --releve <releve.json>`
(`<releve.json>` : le fichier écrit par `… <page.md> > <releve.json>` au §1 ;
0 : identique au relevé ; 1 : une ligne par écart ; 2 : fichier illisible ou
section « Questions ouvertes » absente).

**Ceinture — fichier introuvable.** Si la lecture échoue (plugin pas encore
installé, version périmée, fichier supprimé localement) : **le dire en une
ligne avec le chemin, et ne rien écrire dans la page**. Et comme la remise à
jour du chapitre `Exécution` (§2) précède la première étape, **ça bloque aussi
le code** — même raisonnement que pour le connecteur Notion manquant (en tête
de fichier) : exécuter sans pouvoir tenir la page produit un travail dont il ne
reste aucune trace hors du fil de discussion, et le fil disparaît au
compactage. Deux issues, dans cet ordre : **mettre à jour le plugin** —
`claude plugin update plans-notion` (redémarrage requis pour l'appliquer), ou
`claude plugin marketplace update` si la source a bougé — ou **demander à
Benjamin**. Coder en se promettant d'écrire la page plus tard est le scénario que
tout ce dispositif existe pour empêcher.

## 6. Clore

Dans le **même tour** que le compte rendu à Benjamin, jamais « plus tard » :

- `Statut` : **`a merger`** — le statut normal de fin d'exécution, sur tous les
  dépôts. `execute` ne se pose que sur du code **vérifié sur `main`** ; la
  symétrie est vraie aussi : jamais `a merger` sur du travail déjà parti sur
  `main`. Ce skill ne pose jamais `archive`.
- `Branche` renseignée ; `PR` reste **vide** tant qu'aucune PR n'existe.
- `Journal d'exécution` clos par une entrée `État final` (H3) : ce qui est
  livré, le verdict de la suite complète, les écarts, le reste à faire (chaque
  ligne avec son propriétaire), plus : le décompte des découvertes **vérifié
  mécaniquement** (`grep -c`, jamais de tête), le contrôle des libellés, le
  registre des outils, **un verdict par étape (`verified` ou
  `unverifiable`, jamais un troisième mot)**, une rétrospective en cinq
  questions, les schémas relus
  (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`).
- Le compte rendu dit **quelles étapes sont parties en sous-agent Sonnet** et,
  pour celles faites en direct, pourquoi ; il dit aussi que **la PR n'est pas
  ouverte et qu'elle le sera sur demande**.
- **Livrer la branche, et s'arrêter là** : (1) jouer la suite complète en
  local, e2e compris — c'est le verdict de fin de plan ; (2) pousser la branche
  du plan ; (3) **ne pas ouvrir la PR** ; (4) contrôle bloquant
  (`git branch --list '<branche-du-plan>-etape-*'`, `git worktree list`)
  avant de poser `a merger` ; (5) retirer le worktree, **pas la branche**.

Quand Benjamin demande « ouvre la PR » ou « merge sur main » : une seule PR, de
la branche du plan vers `main`, le label `review-required` se décide en
regardant ce dépôt-là ; `Statut` = `execute` dans le même tour que le merge
vérifié.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture.md` — **à lire à la clôture, et à chaque demande de PR ou de
remontée sur `main`** : le détail de chaque point ci-dessus, la séquence de
clôture complète, la section « La PR, puis la remontée sur `main` » et la
ligne `Evals`.

## 7. Le plan de suite, quand tout n'est pas passé

Une exécution autonome se termine parfois avec des étapes en échec, des étapes
sautées faute de dépendance, ou une décision qui attend Benjamin. **Dans ce cas
— et dans ce cas seulement — créer un plan de suite.** La forme de la page
(titre suffixé, propriétés, chapitre `Reprise du plan #N-1`, sort de la
`Branche`, lien entre les deux pages) vit dans un fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md`

**À lire au moment de la clôture**, dès qu'il reste quelque chose que
l'autonomie a mis de côté. Ne pas créer de plan de suite quand tout est passé :
une page vide de contenu utile encombre la base et fait douter du statut de
celle qui la précède.

## Plusieurs plans

Tout ce qui précède décrit un plan. Quand une session en porte plusieurs,
chacun garde son déroulé (§2 à §7) ; ce qui s'ajoute tient en cinq points.

**Un pilote unique.** Le pilote conduit tous les plans, et aucun
n'est confié à un « pilote » délégué. La raison est mécanique : un sous-agent
ne peut pas lancer d'autres sous-agents. Un pilote par plan, délégué, ne
pourrait donc plus appeler `executant` ni `relecteur` — les étapes se
coderaient dans le pilote, ce que le §3 interdit.

**Chaque plan garde sa porte, sa branche et son worktree.** La porte d'entrée
se lit plan par plan : un plan dont le `Statut` n'est pas `valide` ne
démarre pas. La branche, le worktree du plan (§2), le journal (§4) et la
clôture (§6) sont ceux de ce plan, jamais partagés avec un autre. Au contrôle
bloquant de la clôture, `git worktree list` montre aussi les worktrees des
autres plans encore en cours : ne regarder que ceux du plan qu'on clôt.

**Un seul pool glissant.** Toutes les étapes de tous les plans partagent
**une douzaine de places**. Une étape qui termine libère sa place pour la
prochaine étape prête, de n'importe quel plan. Le plafond est celui du pool,
pas celui de chaque plan :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`

**Entre plans, le parallèle est le défaut.** Seule une ressource partagée à
l'exécution fait attendre :

- **le port des tests e2e** — deux plans ne le prennent pas en même temps ;
- **la base locale** — même raison ;
- **les actions lourdes** (suites, e2e, évals) — une seule à la fois sur la
  machine : le plan maître porte leur file, le pilote les prend une par une
  (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/machine-partagee.md`) ;
- **le quota d'un outil**, lu au registre :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`

Deux plans qui touchent **le même fichier** ne s'attendent pas : ils donnent un
**ordre de merge**, signalé dans le plan maître et dans le compte rendu. Chaque
plan vit sur sa propre branche, donc rien ne se marche dessus à l'exécution ;
c'est au moment de remonter sur `main` que l'ordre compte.

**Un plan maître.** Une page Notion créée **au lancement**, sans statut de
validation — ce n'est pas un plan qu'on valide, et la porte d'entrée n'a rien
à y lire. Elle porte :

- **le croisement** : qui part ensemble, qui attend quoi, et pourquoi ;
- **l'avancement par plan**, avec un lien vers le journal de chacun ;
- **l'état final consolidé**, posé une fois le dernier plan clos.

Elle s'écrit avec les mêmes précautions que le reste (§5).

## 8. Ce que ce skill ne fait pas

- Il ne **conçoit** pas le plan — c'est `plan-notion`. Il **tient à jour** le
  chapitre `Exécution` : à l'entrée pour y répercuter les dernières réponses de
  Benjamin (§2), et en cours de route pour les écarts datés (§4). Mettre à jour
  n'est pas concevoir ; si l'approche est en cause, la main repasse à
  `plan-notion`.
- Il ne crée de sa propre initiative que deux sortes de page : le **plan de suite
  `#N+1`** en clôture (§7), qui repart ensuite en `plan-notion` comme n'importe
  quel brouillon, et, quand une session porte plusieurs plans, le **plan maître**
  du lancement (« Plusieurs plans »).
- Il ne code pas si le statut n'est pas `valide`.
- Il n'écrit pas lui-même le code des étapes déléguables : ça part en sous-agent
  `plans-notion:executant`, **Sonnet par définition**, dans sa dernière
  version — un par étape en séquence par défaut, mais
  pas absolument : en parallèle par vagues, ou regroupées, quand `vagues.md`
  le permet ou le prescrit (§3). Piloter, ce n'est pas coder.
- Il ne relit pas lui-même le diff d'une étape à la place de l'agent
  `plans-notion:relecteur` : un regard qui a piloté l'étape partage ses angles
  morts avec celui qui l'a écrite. Il **fait relire** (§3, `revue.md`), et
  vérifie chaque remarque avant d'agir dessus.
- Il ne code jamais dans le checkout principal du dépôt : la branche du plan
  vit dans un worktree dédié dès sa création (§2), retiré à la clôture (§6) —
  jamais avant, et jamais à la place de la branche elle-même, que le hook
  `SessionStart` nettoie après le merge.
- Il n'ouvre **aucune PR de sa propre initiative** — ni d'étape, ni de
  clôture (§6). L'exécution s'arrête à la branche du plan, prouvée en local et
  poussée. Chaque PR est un run de CI, et le quota GitHub Actions est la
  contrainte qui a fixé cette règle (§2) ; la remontée vers `main` est un geste
  vers l'extérieur, et c'est Benjamin qui en décide le moment.
- Il ouvre **la** PR du plan — une seule, de la branche vers `main` — **quand
  Benjamin la demande**, avec ou sans `review-required` selon ce que ce dépôt-là
  en fait (§6) ;
  il merge sur `main` **quand Benjamin le demande** — et pose alors `execute`
  dans le même tour, une fois le merge vérifié (§6). Là où la CI du dépôt merge
  seule la PR (`vahiny` sur `review-required`), il **vérifie** le merge et pose
  `execute` ; il ne merge rien de sa propre initiative.
- Il ne pose jamais `execute` sur un travail qui n'est pas sur `main` — ni ne
  laisse `a merger` sur un travail qui y est déjà (§6).
- Il ne s'arrête pas entre deux étapes pour demander l'autorisation de continuer
  (§3).
- Il ne passe jamais un plan en `archive`.
- Il ne résout pas les fils de commentaires.
- Ses fichiers de référence, à côté de ce `SKILL.md`, se lisent à l'endroit où
  le déroulé les cite : `ouverture.md` (§2), `etapes.md` (§3), `journal.md`
  (§4), `cloture.md` (§6).
- Il ne dépend d'aucun `CLAUDE.md`, d'aucun hook, d'aucun fichier du dépôt de
  travail. Ses compagnons sont les fichiers partagés
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/remontee-sur-main.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/preuve-du-rouge.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/bons-tests.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/machine-partagee.md` et
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`, livrés par le
  plugin `plans-notion` — pas par le dépôt de travail, quel qu'il soit.
