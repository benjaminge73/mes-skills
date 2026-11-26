# Ouvrir l'exécution — le détail du §2

Fichier de référence de `executer-plan-notion` : `SKILL.md` §2 dit **quand** le
lire (à l'ouverture, avant la première étape). Le détail vit ici, sauf la remise à jour
du chapitre `Exécution` et ce qui la suit : `remise-a-jour-execution.md`.

Sommaire :

- Le réglage du pilote : Sonnet `medium`, sinon une sous-session
- Qui prépare : le pilote, ou le `preparateur`
- Remettre le chapitre `Exécution` à jour — toujours (dans `remise-a-jour-execution.md`)
- La porte des preuves, avant — chaque étape a sa preuve de fin (dans `remise-a-jour-execution.md`)
- Puis, dans le même tour : maquette, questions orange, worktree, relevé de la
  CI, vagues, pilote (dans `remise-a-jour-execution.md`)
- Les prérequis : tout ce qu'il faut hors du dépôt, vérifié avant `pret`
- La porte du `pret` : l'entrée `Ouverture`, le script, puis `en cours`
- La fiche du plan, la sonnette et le courrier de Hal (à `en cours`)
- Une branche, la PR à la clôture

### Le réglage du pilote : Sonnet `medium`, sinon une sous-session

**Le pilote d'un plan tourne en Sonnet 5.5, effort `medium`** (décision de Benjamin du
2026-10-19). La vérification vient **avant tout geste du §2**, la relecture comprise : la
préparation est le travail du pilote, elle se joue donc déjà à ce réglage.

- **La session est à ce réglage** → elle continue, et la puce **Pilote** de l'entrée
  `Ouverture` dit `Sonnet 5.5, medium`.
- **Sinon, elle ne prépare ni ne code.** Elle ouvre une **sous-session visible**, à ce
  réglage, depuis le dépôt du plan, puis **s'arrête** : la sous-session reçoit le plan
  entier (préparation et étapes) et parle elle-même à Benjamin. Jamais un `claude -p`
  ni un agent d'arrière-plan lancé en silence : Benjamin n'y voit rien et ne peut rien
  y répondre (retour du 2026-10-19).
  - **Le brief est court** : l'URL de la page, « exécute ce plan avec
    `executer-plan-notion` », la page du plan maître s'il y en a une, la branche si elle
    existe déjà. Le détail est dans la page ; un brief long déborde du lien. **Un humain
    est là** : les questions passent en texte, pilotables par Hal (`_partage/pilotable-par-hal.md`), pas par la variante sans
    humain de `_partage/decouvertes.md` §3.
  - **Dans l'app Claude Code Desktop** (la voie d'abord) : un lien
    `claude://code/new?q=<brief encodé>&folder=<chemin absolu du dépôt, encodé>`, ouvert
    par `open` (macOS), `xdg-open` (Linux) ou `start ""` (Windows) ; sans bureau (une
    session cloud), le lien se donne tel quel à Benjamin pour qu'il le clique. Il ouvre
    une **nouvelle session dans la barre latérale**. Le lien **pré-remplit** le prompt sans l'envoyer, demande de **confirmer le
    dossier**, et **ne fixe ni modèle ni effort** : le message dit à Benjamin de choisir
    Sonnet 5.5 et `medium` avant d'envoyer.
  - **Dans un terminal** : donner à Benjamin la ligne à coller dans une nouvelle fenêtre,
    qui fixe le réglage elle-même :
    `claude --model claude-sonnet-5-5 --effort medium "<brief>"` (l'identifiant complet,
    pas l'alias `sonnet` : un alias lancé hors des réglages de l'utilisateur a servi une
    autre version, `_partage/outils-claude-code.md`, 2026-10-15). S'il préfère détacher la
    session : `claude --bg --name <plan> --model claude-sonnet-5-5 --effort medium
    "<brief>"`, qui s'ouvre et se suit par `claude agents`, `claude attach <nom>` et
    `claude logs <nom>`.
  - **La sous-session vérifie son propre réglage** avant son premier geste (`/model`,
    `/effort`) et le dit à Benjamin si ce n'est pas Sonnet `medium` ; la puce **Pilote**
    écrite au `pret` en reste la trace, et `preparation-prete.py` la contrôle.
  - **La session mère ne touche ni la page ni le dépôt** après avoir ouvert la
    sous-session, et ne fait pas semblant d'en relayer le compte rendu : elle dit à
    Benjamin où la trouver, c'est tout.
- **Ni lien Desktop ni `claude` utilisable** (`sudo` et `HOME`, même fiche) → la session
  s'arrête avant tout geste et donne à Benjamin la ligne de relance ci-dessus, ou `/model
  sonnet` puis `/effort medium` dans la session courante.
- **Un plan maître a un seul pilote** : une seule sous-session visible conduit tout le lot.
- **Seul Benjamin déroge**, dans son message courant (un plan à haut enjeu qu'il veut
  piloter plus haut, par exemple). La puce dit alors `<modèle>, <effort> — dérogation de
  Benjamin, <date> : « <citation> »`. Sans cette citation, `preparation-prete.py` refuse
  `pret` pour tout réglage autre que Sonnet `medium`.
- La règle vise le **pilote**. Les agents nommés (`preparateur`, `executant`, `relecteur`…)
  portent leur propre modèle dans leur frontmatter.

### Qui prépare : le pilote, ou le `preparateur`

La préparation est le travail du pilote. Il la joue lui-même pour un plan ; pour
plusieurs plans, ou pour garder son contexte propre, il la **délègue, un appel par
plan**, à `plans-notion:preparateur` (`subagent_type`, nom qualifié, **aucun paramètre
`model` ni `effort`** : l'agent porte Sonnet `medium` dans son frontmatter, et un
paramètre ajouté écraserait cette définition), et **jamais un `general-purpose` écrit à la
main** : sans agent nommé, le sous-agent hérite du modèle et de l'effort de la session,
et personne n'a choisi lequel (constaté le 2026-10-16 sur la préparation d'un plan
Vahiny). Définition : `${CLAUDE_PLUGIN_ROOT}/agents/preparateur.md`.

- **Le brief** porte la page du plan, le dépôt, la page du plan maître s'il y en a un
  et **le modèle et l'effort du pilote** : la puce **Pilote** de l'entrée `Ouverture`
  dit le pilote, pas le sous-agent, qui ne sait pas lequel c'est.
- **Il lit la page et joue les commandes lui-même** : le connecteur Notion n'est pas garanti
  chez les sous-agents (absent de l'app de bureau, chargeable depuis le VPS), et un sous-agent ne rendrait que des preuves de seconde main ; donc pas
  de `lecteur` ni de `sondeur` dans la préparation qu'on lui confie. Il s'arrête à `pret` ;
  `en cours` reste au pilote.
- **Le pilote ne le croit pas sur parole** : il relit le miroir, rejoue
  `preparation-prete.py` (code 0), vérifie le modèle réellement servi par
  `modele-sous-agent.py` (`_partage/poc.md`, « La preuve de chaque réponse »), puis pose
  `en cours`. Un arrêt par `maxTurns` laisse un résultat partiel : la page garde ce qui
  est écrit, le pilote relance le `preparateur` sur la même page.

### Remettre le chapitre `Exécution` à jour — toujours

Le geste est dans un fichier à part, à lire en entier avant la première étape, comme ce fichier :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/remise-a-jour-execution.md` — la remise à jour
du chapitre `Exécution`, la porte des preuves, puis le reste de la préparation avant la première étape.

### Les prérequis — tout ce qu'il faut hors du dépôt, vérifié avant `pret`

Une exécution arrêtée à l'étape 12 faute d'une clé d'API (constaté le 2026-11-20) a
coûté douze étapes : le manque se voyait dès la page. **Un plan ne passe pas `pret`
tant que chaque chose dont l'exécution a besoin n'est pas vérifiée disponible.**

1. **Inventorier** en lisant le chapitre `Exécution` en entier, puis `Contraintes techniques
   vérifiées`, `Questions ouvertes` (les réponses tranchées) et les `Preuve de fin` : chaque étape
   appelle quoi ? Clés d'API et jetons, secrets et variables d'environnement, accès (dépôt
   privé, base, serveur, VPS, droits `gh`), connecteurs MCP (Notion, Composio…), outils et
   versions (CLI, Python, navigateur), services joignables et hôtes autorisés, fichiers ou
   données d'entrée, quota ou budget. Les étapes `D` prévisibles comptent aussi.
2. **Vérifier chacun là où l'exécution le jouera**, par une commande qui ne montre jamais la
   valeur d'un secret : `test -n "$NOM"` (code 0 ou non), `command -v <outil>`, `gh auth status`,
   `curl -sI <hôte>` ou un appel à vide du connecteur, `ls <fichier>`. Un secret tenu par le
   VPS ou par Hermes se vérifie là où il vit, pas dans l'environnement de la session cloud.
3. **Écrire la puce `**Prérequis**`** de l'entrée `Ouverture` : un élément par prérequis, avec
   l'étape qui l'exige et le résultat de la vérification (`disponible`, ou `manquant`). Aucune
   valeur de secret, jamais. `sans objet — <raison>` est recevable pour un plan sans clé, accès
   ni outil au-delà du dépôt (la raison est obligatoire).
4. **Un prérequis manquant bloque `pret`.** Le plan reste `valide`, la session le dit à Benjamin
   en nommant l'élément, l'étape qui l'exige et où le fournir, puis s'arrête (pilotable par
   Hal, `_partage/pilotable-par-hal.md` : question en texte, recopiée dans la page). Elle ne
   pose pas `pret` « en attendant », et ne code pas les étapes qui n'en ont pas besoin : la
   préparation reprend quand l'élément est fourni, et seule sa puce se rejoue. Un secret ne
   s'écrit pas dans la page ni dans le rapport.

### La porte du `pret` — la préparation se prouve avant `en cours`

`valide` dit que Benjamin a accepté le plan ; il ne dit pas que la session a fait
ce qu'il faut pour l'exécuter sans surprise. **`pret` le dit** : la préparation de
ce fichier est faite, et chaque geste a laissé sa trace. Parcours d'un plan :
`valide` → préparation → `pret` → `en cours` → `a merger` → `execute`. Le parcours
se fait dans la même séance : un « go » sur une page `valide` lance la préparation,
puis `pret`, puis `en cours`, sans attendre un nouveau « go ». La règle du « go »
et sa raison sont dans `SKILL.md`, « La porte d'entrée » ; elle ne se répète pas
ici. Une session ne saute pas à la première étape pour autant, et le « go » ne
remplace pas la porte.

**1. Écrire l'entrée `Ouverture`** du `Journal d'exécution` (H3 `Ouverture`),
dans la page et dans le miroir local, une puce à clé en gras par geste. Les onze
clés sont obligatoires, plus **une puce `Preuve de l'étape N` par étape** du
chapitre `Exécution` (étapes `D` comprises). Une valeur « — », « aucune »,
« à voir » ne compte pas, et `sans objet — <raison>` est recevable, la raison en
plus :

```
### Ouverture

- **Relecture** : chapitre `Exécution` relu le 2026-10-15 ; Q3 et Q5 reprises (étapes 2 et 4), le reste « inchangé »
- **Questions** : Q1 à Q6 vertes, 6 sur 6 ; 2 `(reco appliquée par défaut)`
- **Preuves** : `preuves-des-etapes.py --avant` code 0 ; `verifier-preuves.py <miroir> --depot <dépôt> --transcripts` code 0
- **Répétition** : `releve-du-jour.py --comparer` sans écart ; « État de départ » présent (POC compris), `main` inchangé depuis sa date
- **Maquette** : sans objet — aucune étape à impact fonctionnel
- **CI** : `push` sans run hors `main` ; pas d'e2e ; `review-required` sans effet ; `merge-auto` actif
- **Vagues** : vague 1 : étapes 1 et 2 ; vague 2 : étape 3
- **Pilote** : Sonnet 5.5, medium
- **Branche** : `feat/le-theme`, worktree `~/repos/worktrees/<repo>/feat-le-theme`
- **Orchestration** : sans objet — aucun plan maître
- **Prérequis** : `ANTHROPIC_API_KEY` (étape 3) disponible (`test -n` code 0) ; `gh auth status` code 0 ; connecteur Notion répond
- **Preuve de l'étape 1** : `pytest a -q` rejouée à blanc : code 1 attendu (l'étape n'est pas faite), la commande tourne
- **Preuve de l'étape 2** : `pytest b -q` rejouée à blanc : code 1 attendu, la commande tourne
```

Ce que chaque puce porte :

- **Relecture** : la remise à jour du chapitre `Exécution` (`remise-a-jour-execution.md`),
  datée, avec ce qu'elle a changé ou « inchangé ».
- **Questions** : toutes vertes, décompte recopié de la page. Une question restée
  🧭 se tranche (reco appliquée par défaut) avant `pret`, jamais après.
- **Preuves** : les codes de sortie de la porte des preuves (`remise-a-jour-execution.md`) et de
  `verifier-preuves.py` (la preuve de chaque réponse, POC compris) ; un écart
  se corrige, ou se justifie par une dispense motivée dans la page.
- **Preuve de l'étape N** : **toutes les étapes sont prouvées, pas seulement
  écrites.** La commande de la `Preuve de fin` se joue à blanc, telle quelle, à
  l'endroit où l'exécution la jouera (geste 1 de `poc.md`), et la puce dit ce
  qu'elle a rendu : une commande qui sort en code 2 faute d'entrée, ou dont le
  `--check` exige un zéro impossible à son rang, se corrige ici, pas à l'étape.
  Une étape qui crée ce qu'elle teste est rouge avant d'être faite : le rouge
  attendu s'écrit tel quel. Une preuve qui ne se joue pas en commande (lecture,
  relecture humaine) s'écrit avec sa nature, pas avec un code.
- **Répétition** : `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/releve-du-jour.py" --comparer <fiche>`,
  où <fiche> est le bloc « Relevé du jour » de `Contraintes techniques vérifiées`,
  recopié dans un fichier du scratchpad. Seul l'écart va dans cette puce ; sortie
  vide = aucun écart, code 2 = fiche illisible, à dire. L'« État de départ » de
  `poc.md` existe dans la page. Si `main` a bougé depuis sa date, on rejoue les
  gestes 1 et 2 de `poc.md` dans un worktree détaché avant de l'écrire. Un plan
  sans ce bloc se dit « relevé : pas de fiche dans la page ». Un plan sans « État
  de départ » n'a pas eu sa répétition : on le dit en une ligne plutôt que d'écrire `sans objet`.
- **Vagues** : la liste que `vagues.py` calcule (une ligne par vague), **et** les
  étapes regroupées dans un seul sous-agent, avec leur raison ; le script compare
  en plus la colonne « Vague » du tableau de chevauchement au calcul et refuse un
  écart. La parallélisation est donc prévue et écrite avant la première étape.
- **Orchestration** : `sans objet — aucun plan maître`, ou, pour un plan couvert
  par un plan maître, le lien de sa page et la place de ce plan : avec qui il part
  en parallèle, ce qu'il attend, son rang dans l'ordre de merge, les fichiers qu'il
  partage avec d'autres plans, son créneau dans la file des actions lourdes. La
  page maître doit porter ces choses avant que ses plans passent `pret`
  (`plan-notion/plan-maitre.md`, « Le statut du plan maître et son lot »).
- **Prérequis** : l'inventaire de « Les prérequis » ci-dessus, chaque élément avec l'étape qui
  l'exige et son état vérifié ; `preparation-prete.py` refuse la puce qui nomme un élément
  manquant, indisponible ou à fournir.
- **Maquette**, **CI**, **Pilote**, **Branche** : le résultat des puces
  correspondantes ci-dessus.

**2. Jouer la porte :**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/preparation-prete.py" <page.md> --depot <dépôt> [--maitre <maitre.md>]
```

`<page.md>` et `<maitre.md>` sont les miroirs de `notion-fetch` ; `--maitre` est
obligatoire dès que **Orchestration** cite un plan maître. Il rejoue aussi la porte des
preuves, `verifier-preuves.py` et `vagues.py --comparer` ; leurs défauts sortent dans le même rapport, préfixés (`preuves :`, `réponses :`, `vagues :`).

- **Code 0** : `prêt : …`. `Statut` = `pret`, `Branche` renseignée, en une
  écriture Notion ; relire le miroir pour confirmer.
- **Code 1** : un défaut par ligne (question encore ouverte, étape sans preuve de
  fin ou sans preuve rejouée, vagues qui ne collent pas au calcul, section de la
  page maître absente ou vide, puce absente ou vide). On fait le geste manquant, on écrit sa puce, on
  rejoue. **Aucune étape ne démarre sur un code 1**, et `pret` ne se pose pas
  « en attendant ».
- **Code 2** : page, chapitre ou journal introuvable, ou `--depot` manquant. On le dit à Benjamin, sans
  rien commencer.

Le script vérifie qu'un geste a laissé sa trace, pas qu'il est juste : c'est la relecture du pilote.

**3. `Statut` = `en cours`** se pose sur la page `pret`, juste avant la première
étape, dans le même tour si rien ne l'arrête. Une session qui s'arrête entre les
deux laisse la page à `pret` ; la suivante passe par la ligne `pret` de la porte
d'entrée (`SKILL.md`) : relecture de la page, retour à `valide` si Benjamin y a
répondu depuis, sinon `en cours`. Reprise d'un plan déjà `en cours` : inchangée.
Si la puce **Orchestration** cite un plan maître, **un plan du lot ne passe jamais `en
cours` seul** : avant de poser le statut, jouer `depart-dans-le-lot.py <maitre.md> <Pn>
--statuts …` (`plan-notion/plan-maitre.md`, « Un plan du lot ne s'exécute pas seul »). Code 1 :
le plan reste `pret`, la session dit qui attend quoi et ne démarre aucune étape. Code 0 : le
passage à `en cours` rejoue `statut-maitre.py --actuel` dans le même tour (« Qui rejoue le
calcul, et quand ») : c'est ce geste-là qui fait passer le maître de `pret` à `en cours`.

### La fiche du plan, la sonnette et le courrier de Hal

Le plan a un état que la garde de fin de tour (`hooks/garde_fin_de_tour.py`) et le
hook de démarrage lisent sans réseau : une **fiche locale** par session, tenue par
`plan-en-cours.py` (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/plan-en-cours.py`).
Ses états suivent ceux de la page : `en cours`, `attente`, `a merger`, `clos`. Si le
script n'existe pas (session cloud, plugin sans lui), le dire en une ligne et
continuer.

- **`ouvrir`, à `en cours`, dans le même tour.** D'abord la **sonnette** : une session
  sur Remote Control (elle a un identifiant claude.ai) crée **sa** sonnette, un message
  programmé lointain lié à elle, par l'outil de réveil du serveur `claude-code-remote`
  (`send_later`, ou son trigger) quand elle l'a, sinon par `RemoteTrigger`. L'identifiant
  rendu (`<trigger_id>`) doit exister **avant** `ouvrir` : `ouvrir --sonnette` est la seule
  commande qui l'inscrit dans la fiche. Une session sans identifiant claude.ai (terminal
  du VPS) n'en crée pas. Puis :

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/plan-en-cours.py" ouvrir \
      --page <id de la page> --titre "<titre du plan>" --depot <owner/repo> \
      --branche <branche> --worktree <chemin du worktree> [--sonnette <trigger_id>]
  ```

  Sortie 1 : une fiche existe déjà pour cette session. On la lit (`lire`), on ne
  l'écrase pas. Si elle porte **un autre plan**, celui-ci est le second de la session : il
  n'a pas de fiche (« Plusieurs plans : une fiche par session », en fin de fichier). La sortie « pas de sonnette possible » dit que la session n'a pas
  d'identifiant claude.ai : le réveil qu'on vient de créer n'a alors personne à réveiller,
  on le retire si l'outil le permet, et on le dit.

- **`lire`**, même tour. Trois valeurs de la fiche vont sur la page du plan, dans la base
  **Plans Claude**, en une écriture relue après (`_partage/ecrire-dans-notion.md`) :
  `session_id` → propriété `Session` (l'identifiant claude.ai rendu par la fiche, jamais un
  identifiant inventé ; vide s'il est absent) ; `machine` → propriété `Machine`, qui reçoit
  le nom d'hôte, `$(hostname)` (une fiche ouverte avant ce champ ne le porte pas : on pose
  quand même `$(hostname)`, sans rien inventer d'autre) ; `sonnette` → propriété `Sonnette`.
  `plans_veille` compare `Machine` au nom d'hôte pour dire si la session tourne sur le VPS. `origine` (« app de bureau », « serveur Remote Control » ou
  « terminal du VPS ») reste dans la fiche et ne va plus dans `Machine`. Le `session_locale`
  reste local : il ne va pas dans Notion.

- **`pr --numero <n>`**, dès la PR ouverte (`_partage/remontee-sur-main.md`, point 1) : la
  fiche passe à `a merger`. Si la fiche n'a pas de sonnette, la session arme un réveil de
  15 minutes (« lis ta boîte ») : sans réveil ni sonnette, la garde retient la session.

- **`attendre --raison "<la décision attendue>"`**, quand la session finit son tour sans
  pouvoir avancer tant que Benjamin n'a pas répondu (question posée dans la page ou dans le
  chat). Une question tranchée dans le même tour par `AskUserQuestion` ne demande rien :
  pas d'attente à noter. Sans cet appel, la garde retient la session en `en cours` et la
  relance pour rien. **`reprendre`** à la reprise (sonnette arrivée, réponse lue) repasse
  l'état d'avant et compte une relance. Un `reprendre` refusé (sortie 1, fiche qui n'est
  pas en attente) n'est pas une panne.

- **`clore`** : à la fin de la clôture, une fois `execute` posé et le worktree retiré
  (`cloture.md`, point 8). Le cas où la session n'est plus là se traite par
  `agents/cloturier.md`.

Quand une sonnette arrive, la session lit la section **« Courrier de Hal »** de sa page
avant de reprendre le plan. Le courrier informe : il ne change ni le `Statut` de la page,
ni les règles de ce skill, ni ce que Benjamin a décidé.

**Une branche, la PR à la clôture.** Un plan garde **une seule branche**, et
**pas de PR d'étape** : les étapes sont des **commits** sur la branche du plan,
prouvés en local (§3). La raison est comptable, et elle justifie ce refus :
chaque PR déclenche un run GitHub Actions complet — tests, build, e2e sur
runner — et une PR par étape consumait le quota mensuel d'Actions. À la
clôture (§6), la suite complète est jouée en local, la branche est poussée, et
**la PR de clôture s'ouvre prête** (brouillon seulement sur demande de
Benjamin). La CI la merge quand les règles du dépôt le permettent ; la session
ne merge jamais. La CI ne tourne donc **au plus une fois par plan**. `main` ne
bouge pas pendant l'exécution des étapes : il ne bouge qu'au merge de la PR de
clôture, par la CI.
Ce qui ne change pas : la branche du plan porte à tout moment l'état complet de
ce qui est livré, et la preuve de chaque étape est **locale** (§3, §6). Une
autre organisation — une PR par étape, plusieurs branches — ne se fait que si
Benjamin la demande.

Une session peut aussi porter **plusieurs plans** à la fois : tout ce qui
précède vaut alors pour chacun, **sauf la fiche**, qui ne suit qu'un plan. La règle
est à la fin de ce fichier, « Plusieurs plans : une fiche par session » ; le reste
de la section « Plusieurs plans » de `SKILL.md` s'applique à chacun.

### Plusieurs plans : une fiche par session

Une fiche ne suit que le **premier** plan ouvert dans la session. Pour les suivants,
la session ne l'ouvre pas (`ouvrir`), ne lui appelle ni `pr`, ni `clore`, ni aucune autre
sous-commande de `plan-en-cours.py` (`attendre`, `reprendre`, `etape` écriraient dans la
fiche du premier), et le dit en une ligne. Le plan suivant n'a donc pas de fiche : la
garde de fin de tour ne le retient pas, et le cloturier le rend `BLOCKED` faute de fiche.

Pourquoi : la fiche est une par session, nommée par l'identifiant de la session. Un
second `ouvrir` sort en 1 (une fiche existe déjà), et un `pr --numero` lancé pour le
second plan écrirait dans la fiche du premier. Le cloturier constaterait alors le merge
de la PR du second plan et poserait `execute` sur la page du premier.
