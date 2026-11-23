# Clore — pousser, ouvrir la PR et suivre la CI

Détail du §6 (`cloture.md`, noyau) : lu quand la clôture en est aux points 1 à 6 (suite complète, allègement des `CLAUDE.md`, relecture, porte, push, PR, contrôle bloquant), au point 8 (suivi de la CI), ou à une demande de PR ou de remontée sur `main` (section « La PR, puis la remontée sur `main` »). Texte repris tel quel, sans réécriture.

- **Livrer la PR, prête, et la suivre jusqu'au merge.** La PR s'ouvre à la
  clôture ; c'est la CI qui la merge, jamais la session (points 5 et 8). La
  séquence de clôture est courte :
  1. **Jouer la suite complète en local** : tous les tests unitaires, lint,
     build, **et les tests e2e** — c'est ici, et seulement ici, qu'ils passent
     (§3). C'est **le verdict de fin de plan** : tant qu'il n'est pas vert, le
     plan n'est pas clos. Rouge → corriger jusqu'au vert, même boucle qu'en
     cours de route ; correctif structurant ou échec qu'on ne sait plus
     diagnostiquer → même arbitrage (§3) : journal, plan de suite (§7), et la
     page reste à `en cours`. Une suite qui n'est pas jouable sur le poste (e2e
     sans navigateur, par exemple) se dit au journal, tests nommés — ce n'est
     pas un vert, c'est un trou : il se pose à Benjamin avant l'ouverture de la
     PR (point 5, et « La PR, puis la remontée sur `main` »). Suite complète et
     e2e prennent le jeton des actions lourdes :
     `${CLAUDE_PLUGIN_ROOT}/skills/_partage/machine-partagee.md`.
  2. **Alléger les `CLAUDE.md` trop longs, sans demander.** Ce geste ne tourne
     que suite complète verte, et avant le push : son commit part avec la
     branche. Pourquoi à la clôture : un `CLAUDE.md` est lu en entier à chaque
     session, et il change assez rarement pour qu'un contrôle à chaque étape
     soit du bruit. Trois temps :
     - **(a) La mémoire du dépôt suit le plan.** Si le plan a changé une
       convention, une commande ou un piège du dépôt, son `CLAUDE.md` le dit :
       la ligne se met à jour, dans un commit à part sur la branche du plan.
     - **(b) Mesurer**, à la racine du dépôt du plan :
       ```bash
       python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/taille-claude-md.py --racine . --base origin/main
       ```
       Une ligne par fichier : `<chemin> <lignes> / <plafond> <verdict>`. Le
       plafond est 200 lignes, ou la taille du même fichier sur `origin/main`
       si elle est plus grande : un fichier ne grossit pas au-delà de ce qu'il
       pèse déjà sur la base (c'est le cliquet). Verdict `REFUS` = au-delà du
       plafond ; code de sortie 1 quand il y en a un.
     - **(c) Alléger tout de suite** si un fichier dépasse 200 lignes, ou si
       la mesure refuse. Un `executant` range le contenu selon
       `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ranger-claude-md.md` (où va chaque
       type de ligne : reste dans le fichier, règle à portée de chemin, skill,
       `docs/`, ou suppression si Claude le relit dans le dépôt). Le
       `relecteur` vérifie qu'aucune information ne s'est perdue. Le tout part
       dans un commit à part sur la branche du plan, puis la mesure est relancée :
       le fichier doit repasser sous son plafond. Si le rangement touche autre
       chose qu'un fichier de consignes, la suite complète est rejouée avant le
       push.
     - **Résultat** : une ligne à l'entrée `État final`, par fichier concerné,
       avec la taille avant, la taille après et les destinations créées — ou,
       si rien n'a dépassé, `CLAUDE.md : sous les plafonds, aucun allègement`.

  2 ter. **Relecture du plan entier, après la suite complète et avant la porte.**
     Un appel `Agent` avec `subagent_type: "plans-notion:relecteur"` (sans
     paramètre `model`, `revue.md`) en mode « plan entier » (`relecteur.md`,
     « Le mode « plan entier » ») : il compare le code de toute la branche au
     chapitre `Exécution` du plan, phrase par phrase (source du passage :
     `github/spec-kit`, `converge`, MIT). Le brief porte l'objectif du plan et son
     chapitre `Exécution`, recopiés depuis le miroir local de la page, et la
     plage `origin/main..<branche-du-plan>`. Il porte aussi la tête attendue :
     le SHA de la branche à la clôture (`git rev-parse HEAD` joué par le pilote
     juste avant d'appeler le relecteur). Sans elle, le relecteur écrit
     « Checkout non vérifié » et ne conclut sur aucun test rejoué.
     - **Chaque écart rendu** (manquant, partiel, contradictoire, non demandé)
       devient une découverte `D<n>` qui s'exécute dans le même plan (décision de
       Benjamin du 2026-10-28). Le tri suit `decouvertes.md` : § 1 pour ce qui est
       irréversible, de sécurité ou coûteux, c'est une question à Benjamin, posée
       dans la session avant `a merger` ; § 2 pour le reste, étape `D<n>` relue par
       la boucle de `revue.md` ; § 3 si la session n'a pas d'humain.
     - Les remarques des autres catégories du relecteur (bug de correction, test
       qui ne teste rien, découverte hors plan) suivent la même boucle.
     - Une `D<n>` issue de ce passage rejoue, une fois faite, les points 1 (suite
       complète), 2 et 2 bis avant la porte (point 3). Le verdict
       (`RIEN À SIGNALER` ou `REMARQUES (n)`) et chaque écart se recopient à
       l'`État final`.

  2 quater. **Rappel du déclencheur « nouveau modèle ».** Ce point ne s'applique que si ce
     plan touche un skill, un agent, un hook ou un `_partage/` du dépôt `mes-skills`. La
     session compare la date de la dernière entrée du journal de `docs/veille.md` aux modèles
     sortis, et aux alias qui servent un autre modèle, depuis cette date (le déclencheur
     est écrit au paragraphe « Le déclencheur » de `docs/veille.md`). Si un modèle est arrivé
     depuis, le compte rendu le dit à Benjamin et lui propose une passe de veille avant la prochaine
     PR qui touche un skill, sans bloquer celle de ce plan.
     Le constat ne bloque ni la porte (point 3) ni `a merger` : faire la passe d'abord est une
     décision de Benjamin. La passe reste exigée par `check_veille.py` selon son propre garde
     (30 jours), qui ne voit pas ce cas : ce rappel est le seul à le couvrir.

  3. **La porte des preuves, avant le push.** Le contrôle des journaux se joue
     par script, sur le miroir local de la page, avant tout push et toute PR :
     ```bash
     python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/preuves-des-etapes.py" <page.md> --apres
     ```
     - **Code 0** : `apres : <n> étape(s), toutes verified`. On poursuit.
     - **Code 1** : des défauts de journal, une ligne par défaut (entrée
       absente, champ vide, verdict hors vocabulaire, `unverifiable` sans
       raison, étape écrite deux fois). On corrige **la page, pas le code** :
       l'entrée de journal, puis on rejoue jusqu'au code 0 ou 3.
     - **Code 3** : aucun défaut, mais au moins une étape `unverifiable`,
       nommée sur sa ligne `non prouvée : Étape N — <raison>`. C'est le
       traitement du trou e2e : **question à Benjamin avant d'ouvrir la PR**
       (point 5), avec `AskUserQuestion` et trois réponses — **ouvrir prête
       quand même**, **ouvrir en brouillon**, **attendre**. Si la réponse ne vient pas
       dans le tour, la fiche passe en attente (`plan-en-cours.py attendre`, `ouverture.md`,
       « La fiche du plan »). Pas de question
       si la CI du dépôt rejoue cette preuve sur la PR (label
       `review-required` là où il rejoue les e2e, « La PR, puis la remontée
       sur `main` ») : la preuve est alors couverte, et le nom reste au
       journal et au compte rendu.
     - **Code 2** : page, chapitre `Exécution` ou journal illisible. La porte
       ne passe pas : rien ne se pousse, et on le dit à Benjamin.
  3 bis. **Remettre la branche à jour de la base avant de pousser.** Depuis le worktree :
     `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/fraicheur-depot.py" --depot . --appliquer`
     (`_partage/fraicheur-du-depot.md`). Code 0 : si des commits de la base ont été repris, rejouer
     la suite locale avant de continuer. Code 3 (arbre sale ou conflit de rebase) : arrêt, on le dit
     à Benjamin, rien ne se pousse. Code 4 (pas de réseau) : le dire au journal, continuer. Branche
     déjà poussée et rebasée : `git push --force-with-lease`, jamais `--force`.
  4. **Pousser la branche du plan.** C'est le seul push de la clôture quand le
     relevé du §2 a retenu les commits en local ; sans lui, le travail ne vit
     que sur un disque. La sortie de la preuve va au journal (`État final`).
  5. **Ouvrir la PR, prête, ou en brouillon le temps d'écrire la doc.**
     `gh pr create --base main --head <branche-du-plan>`, **sans `--draft`** : le
     brouillon se demande à Benjamin, il ne se décide pas seul. **Une exception, décidée
     par Benjamin le 2026-11-02** : dans un dépôt dont le `ci.yml` saute le job `doc` sur
     un brouillon (son `if` porte `draft == false` : `mes-skills`, `hermes-custom`, `vahiny`,
     `job-agent`, `mavod-perso` et `micro-trading` depuis le 2026-11-02), la PR
     s'ouvre **avec `--draft`**, parce que la ligne `Doc :` cite le numéro de la PR et ne
     peut s'écrire qu'après l'ouverture. Elle passe prête au point 7, une fois la ligne
     écrite. Un dépôt dont le job `doc` n'a pas ce `if` garde la règle générale. Titre = titre du plan ; corps = une ligne par étape reprise du
     journal, lien vers la page Notion, la ligne `Danger de merge : <réversible
     ou non> — <ce qui casse si ça casse>` (une seule ligne, pas un bloc ;
     « réversible » au sens de `decouvertes.md` § 1 : un `git revert` suffit, et
     rien n'est parti hors du dépôt — ni écriture externe, ni production,
     publication ou migration ; forme de `mattpocock/skills`, `engineering/pr`, MIT, qui crédite
     `humanlayer/skills` `show-me`, MIT), la ligne `Evals:` (sous-section
     ci-dessous) et la ligne `Doc :` (point 7, « Ensuite »). Label : décidé en
     regardant ce dépôt-là (sous-section).
     `PR` renseignée sur la page dès l'ouverture, et `plan-en-cours.py pr --numero <n>`
     pour la fiche (`_partage/remontee-sur-main.md`, point 1). **Un trou e2e non couvert par
     la CI du dépôt** se pose à Benjamin **avant** cette commande (sous-section
     « La PR, puis la remontée sur `main` ») : la PR ne part pas sans sa réponse.
  6. **Contrôle bloquant, avant d'attendre la CI.** Il ne dépend pas de la CI : il
     passe ici, juste après le push et l'ouverture de la PR.
     ```bash
     git branch --list '<branche-du-plan>-etape-*'
     git worktree list
     ```
     Rien d'autre que les branches `<branche-du-plan>-etape-N-en-echec` déclarées
     au journal. Le worktree du plan figure encore dans `git worktree list` : c'est
     normal, il est retiré au point 8 et pas avant (une correction en cas de rouge
     s'y fait). Les worktrees des autres plans n'en sont pas. Des branches de vague
     qui survivent à leur plan n'ont pas de filet après coup : plan parent
     squash-mergé, `git cherry` y rend `+` pour tout. Survivance → vérifier le
     report (`git log <branche-du-plan>`, `git cherry <branche-du-plan>
     <branche-d-etape>` : que des `-`), puis nettoyer. Sortie des deux commandes
     dans l'entrée `État final`.

     📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`

  8. **Suivre la CI jusqu'au merge, sans jamais merger soi-même, et sans quitter la PR
     avant son issue.** Une CI longue (30 à 40 minutes d'e2e) ne se suit pas au premier
     plan : abonnement aux événements de la PR, ou surveillance en arrière-plan (`Bash`
     avec `run_in_background`, ou `Monitor` sur `gh pr checks <n> --watch`), puis
     vérification du merge sur pièce. La session ne s'arrête pas à l'ouverture : le suivi
     et la mise à jour des plans au merge sont dans `_partage/remontee-sur-main.md`
     (« La session ne part pas à l'ouverture de la PR »). Trois issues :
     - **(a) Verte, et mergée par la CI** → vérifier le merge sur pièce
       (`gh pr view <n> --json state,mergeCommit`, et le commit de merge présent
       dans `origin/main`), poser `execute`, ajouter une ligne datée à `État
       final`, retirer le worktree, puis `plan-en-cours.py clore` (la fiche passe `clos`,
       et la garde de fin de tour la laisse passer). Puis retirer la sonnette de la fiche (`sonnette`
       de `plan-en-cours.py lire`) si l'outil de la session le permet (`RemoteTrigger` avec
       `enabled: false`, ou l'outil de suppression de réveil) ; sinon elle sonne dans le vide, ce qui est sans effet.
       Ce tour peut être un tour ultérieur à celui du
       point 7 : `execute` se pose dans le tour où le merge est constaté.
       Plan couvert par un plan maître : rejouer `statut-maitre.py --actuel` dans ce
       même tour (`plan-notion/plan-maitre.md`, « Qui rejoue le calcul, et quand »).
     - **(b) Rouge** → corriger dans le worktree, encore présent, rejouer la suite
       complète en local, repousser **une seule fois** (chaque push relance un
       run). `Statut` reste `a merger`. Un correctif structurant part à l'arbitrage
       de Benjamin, comme au §3 : la PR reste ouverte et rouge, et la session
       s'arrête là, comme en (c).
     - **(c) Retenue** (brouillon, workflows touchés, PR Dependabot) **ou session
       qui ne peut vraiment pas rester** → `Statut` reste `a merger` avec l'URL de
       la PR, la raison au journal et dans l'`Avancement` du maître, retirer le
       worktree, et dire dans le compte rendu « PR non suivie » : **la prochaine
       session qui lit `a merger` avec une PR renseignée vérifie l'état de la PR et
       pose `execute` si elle est mergée** (le filet, pas le plan). La branche reste : elle se rouvre par
       `git worktree add`. La fiche reste `a merger`, la garde la tient avec le réveil ou la
       sonnette ; quand plus aucune session n'est là, `agents/cloturier.md` fait le constat du
       merge et clôt la fiche.

     Retrait du worktree (issues a et c) : `git worktree remove
     ~/repos/worktrees/<repo>/<branche-kebab>` — si le retrait échoue (arbre sale, par
     exemple), la fiche ne se clôt pas : elle reste `a merger`, et le hook de démarrage
     (`retirer_worktrees_clos.py`) retente une fois la PR mergée. **La branche, elle, reste** : c'est
     le hook `SessionStart` qui la nettoiera après le merge éventuel, et **une
     branche encore checked-out dans un worktree n'est jamais nettoyée par ce hook**
     tant que le worktree existe. Retirer le worktree avant le hook, jamais la
     branche à sa place.

### La PR, puis la remontée sur `main`

La PR s'ouvre à la clôture, prête (points 5 et 8 ci-dessus) : une seule, de la
branche du plan vers `main`. Benjamin peut aussi la demander — « ouvre la PR »,
« merge sur main », « tu peux merger directement », « pousse ça sur main ». La
demande ne change pas le geste : si la PR n'existe pas encore (clôture
interrompue, plan repris plus tard), elle s'ouvre comme à la clôture ; si elle
existe, on la suit jusqu'au merge. Quelle que soit la demande, ces points
tiennent :

- **La session ne merge jamais**, pas même sur « merge sur main » ni sur « tu
  peux merger directement » : `gh pr merge` n'est pas lancé. C'est la CI qui
  merge une PR prête, quand les règles du dépôt le permettent. Si Benjamin veut
  un merge à la main, c'est lui qui le fait.
- **Le label `review-required` se décide en regardant ce dépôt-là**, jamais
  depuis la règle générale : il n'existe pas partout, et là où il existe son
  effet change de signe. Les quatre cas relevés à ce jour :
  - **`vahiny`, `micro-trading`, `mavod-perso` : le poser**
    (`gh pr create --label review-required …`). Là où son workflow le lit, il
    commande la suite complète. Sur `vahiny`, la CI merge seule une fois tout
    vert. Sur `micro-trading`, il lance l'e2e sur le runner du VPS ; `auto-merge`
    attend ce vert, et `deploy` met en production. Sur `mavod-perso`, il
    commande la suite complète (smoke puis e2e).
  - **`mes-skills` : jamais.** Son job `merge-auto` en est exclu : le label y
    empêcherait le merge.
  - **`hermes-custom` : le label n'existe pas**, et `gh pr create --label` y
    échoue. Le dépôt a des e2e sans label pour les commander : c'est un trou
    connu de sa CI : le trou se pose à Benjamin avant l'ouverture (bullet « Ce
    qui retient l'ouverture »), jamais contourné en silence.

  La ceinture reste la suite complète jouée en local à la clôture ; le label
  n'est que la bretelle, et une bretelle n'existe que si le dépôt en a une.
- **Ce qui retient le merge** : une PR brouillon (demandée par Benjamin, ou ouverte en
  brouillon par le point 5 et pas encore passée prête), une CI
  rouge, des workflows touchés (`.github/workflows/`), une PR Dependabot. Dans
  ces cas `Statut` reste `a merger`, et le compte rendu le dit à Benjamin : la
  PR est ouverte, elle attend une décision.
- **Ce qui retient l'ouverture elle-même** : un trou e2e non couvert par la CI du
  dépôt (suite e2e non jouable sur le poste, et aucun label `review-required` qui
  la rejoue sur la PR). La question part à Benjamin **avant** d'ouvrir, avec
  `AskUserQuestion` et trois réponses : **ouvrir prête quand même**, **ouvrir en
  brouillon**, **attendre**. Sans PR, `PR` reste vide et `Statut` reste `a merger`
  (le code est sur la branche, pas sur `main`). Quand la CI rejoue ces e2e sur la
  PR (`review-required` posé là où il existe : `vahiny`, `micro-trading`,
  `mavod-perso`), le trou est couvert : il se note au journal et au compte rendu,
  et la PR s'ouvre prête. Sur `mes-skills` et `hermes-custom`, le label ne rejoue
  rien : la question se pose dès qu'un trou existe.

Si le chapitre `Exécution` porte une ligne `Évals à jouer : …`, la recopier dans le
corps de la PR : `Evals: <catégories> — <raison>`, `Evals: tout` ou `Evals: aucun —
<raison>`. Le défaut du plan est `aucun — <raison>` : recopier tel quel, sans label.
Le corps de la PR porte aussi la ligne `Danger de merge :` (point 5).
La fumée ne se joue que si Benjamin la demande dans son message courant : la session
pose alors le label `fumee`, ouvre la PR en brouillon puis la passe prête (jamais de
pose de sa propre initiative). Le label `evals` ne se pose que sur demande de Benjamin,
pour des catégories ou `tout`, jamais pour `aucun`. Sans ce label, une ligne `Evals:`
absente ou `aucun — <raison>` ne rend pas la CI rouge ; un `aucun` sans raison, ou
combiné à une catégorie, la rend rouge (`evals-portee`). Coûts :
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-connecteurs-et-evals.md`.

La séquence complète — ouvrir, attendre la CI, vérifier que le merge a bien eu
lieu, poser `Statut` = `execute`, journaliser — et le piège qui la fait échouer
(le point qui saute le plus souvent : le statut, oublié une fois le merge fait)
vivent dans un fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/remontee-sur-main.md`

**À lire à chaque demande**, que ce soit avant l'exécution, en cours de route,
ou une session plus tard sur un plan déjà à `a merger` : c'est la seule
opération de ce skill qui peut arriver à trois moments différents, et qui a déjà
été bâclée en s'arrêtant au merge sans mettre `Statut` à jour. Une demande
explicite de PR ou de remontée se suit **sans réclamer de confirmation
supplémentaire** : refuser au nom d'une règle qui n'existait que pour le
protéger, c'est prendre la règle pour une fin. Un trou e2e fait exception : c'est un fait
que Benjamin n'a pas encore vu, et sa demande ne le couvrait pas (sous-section
ci-dessus). Ce que la session ne fait jamais,
même sur demande, c'est le merge lui-même (sous-section ci-dessus).
