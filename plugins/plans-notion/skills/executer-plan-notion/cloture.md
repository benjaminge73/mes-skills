# Clore — le détail du §6

Fichier de référence de `executer-plan-notion` : `SKILL.md` §6 dit **quand** le
lire (à la clôture, et à chaque demande de PR ou de remontée sur `main`). Le
détail vit ici.

Sommaire :

- Dans le même tour : `Statut`, `Branche`, entrée `État final`, compte rendu
- La séquence de clôture (suite complète locale, allègement des `CLAUDE.md`
  trop longs, preuve doc, push, PR prête, contrôle bloquant, clôture écrite
  (Récap, porte, hub, fiches, rattrapage), suivi de la CI, retrait du worktree)
- La PR, puis la remontée sur `main`

Dans le **même tour** que le compte rendu à Benjamin, jamais « plus tard »
(sauf `execute`, qui suit le merge : point 8 de la séquence) :

- `Statut` : **`a merger`** tant que le code n'est pas sur `main`. C'est l'état de
  fin de clôture, sur tous les dépôts : le travail est livré sur la branche du
  plan, prouvé en local, et sa PR est ouverte (en brouillon seulement si
  Benjamin l'a demandé). `execute` se pose dès que le merge est
  vérifié sur `main`, dans le tour où on le constate : ce peut être un tour
  après celui du compte rendu (point 8 de la séquence).
  Plan couvert par un plan maître : le passage à `a merger` rejoue aussi
  `statut-maitre.py --actuel` dans ce tour (`plan-notion/plan-maitre.md`, « Qui rejoue le
  calcul, et quand »).
  Une seule question, et sa réponse est factuelle — *où est le code à cette
  seconde ?* Poser `execute` sur du travail qui dort sur une branche ou une PR
  ouverte fait croire
  la base plus avancée qu'elle ne l'est, et c'est le genre de mensonge qu'on ne
  découvre qu'en cherchant une fonctionnalité absente de la production. **La
  symétrie est vraie aussi, et c'est elle qu'on oublie** : laisser `a merger`
  sur du travail déjà parti sur `main` annonce un chantier en attente qui
  n'existe plus, et le plan suivant repart d'une base fausse.
- Ce skill ne pose jamais `archive` : ranger une page est une décision de
  Benjamin, pas un effet de bord d'un merge.
- `Branche` renseignée : la branche du plan. `PR` porte l'URL de la PR dès
  qu'elle existe, et reste **vide** tant que la PR n'a pas été ouverte — une
  propriété remplie d'une PR qui n'existe pas ment autant qu'un statut faux.
- `Journal d'exécution` clos par une entrée `État final` (H3, comme les autres,
  §4) : ce qui est livré, le verdict de la suite complète (point 1 ci-dessous),
  les écarts, le reste à faire s'il y en a — **chaque ligne avec son propriétaire** :
  la question posée dans la session (avec la réponse de Benjamin), le plan de suite
  (§7, avec son lien) qui la porte, l'étape `D<n>` qui l'a faite, ou l'événement
  qu'elle attend ; une ligne sans propriétaire se règle avant `a merger`
  (`plan-de-suite.md`, « Le tri »). Cette entrée porte aussi :
  - **le décompte des découvertes, vérifié mécaniquement** — jamais recompté
    de tête : `grep -c 'découverte — trouvable' <journal>` et
    `grep -c 'découverte — pas trouvable' <journal>` sur le texte du journal,
    chiffres recopiés tels quels dans la ligne `3 découvertes, dont 1
    trouvable au plan` (§4). ⚠️ **Le premier motif compte aussi la
    variante « sur la page »** : `découverte — trouvable au plan — sur la page`
    commence par `découverte — trouvable`. Elle est donc **déjà dans** le
    premier chiffre, pas à ajouter. Pour la distinguer :
    `grep -c 'découverte — trouvable au plan — sur la page' <journal>` — un
    sous-ensemble du premier compte, qui se lit « dont N sur la page » ;
  - **le contrôle des libellés** (§4) : `grep -c 'Découvertes\*\* :' <journal>`
    égale `grep -c '^### Étape ' <journal>`, et chaque ligne marquée `ÉCART`
    ou `BLOQUÉ` a son libellé. Un écart entre les deux nombres, ou une
    surprise sans libellé, se corrige avant de poser `a merger`, en respectant
    la règle « dans le doute, `trouvable` » (§4) ;
  - **Ajouts sans question** : la liste des intégrations directes faites sans
    demander — retouches `_maj … ajouté sans question parce que …_` et puces de la
    section `### Ajouts sans question` de la page (conception) — pour qu'aucun ajout
    ne passe sans que Benjamin le voie. Le décompte se vérifie mécaniquement, jamais
    de tête, chiffres recopiés tels quels ; « aucun » s'écrit aussi :
    retouches : `grep -c 'maj 20[0-9][0-9]-[0-9][0-9]-[0-9][0-9] — ajouté sans question' <miroir de la page>` ;
    conception : `sed -n '/^### Ajouts sans question/,/^## /p' <miroir de la page> | grep -c '^- '`.
    Le total est la somme de ces deux termes, jamais un seul grep. Le nombre d'étapes
    `D` (`grep '^### Étape D' <miroir de la page> | sort -u | wc -l`) n'en est pas un : c'est un contrôle croisé, il doit être **inférieur ou égal** aux retouches (chaque `D<n>` porte sa correction datée). Un `D` de plus signale une correction oubliée, à corriger avant de clore. La règle est dans
    `${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md` (§ 2) ;
  - **Recos appliquées par défaut** : les recos appliquées sans réponse de Benjamin —
    questions passées au vert `(reco appliquée par défaut)` à l'ouverture et, en
    session sans humain, découvertes traitées par défaut, la dépense en tête. « aucune »
    s'écrit aussi. La règle est dans `decouvertes.md` (§ 3) ;
  - **le registre des outils** : toute découverte qui concerne un outil
    (quota, coût, piège, repli) part en PR sur `mes-skills`, dans
    `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`, fiche datée et
    sans nom privé — la règle de publication du fichier s'applique. Ce n'est
    pas la PR du plan : elle vise un autre dépôt et publie dans un dépôt public,
    donc le compte rendu la **propose**, et Benjamin décide de la remontée ;
  - **un verdict par étape, `verified` ou `unverifiable`** — jamais un
    troisième mot. `verified` : la preuve du brief a été rejouée par la
    session et elle est verte (§3). `unverifiable` : une preuve qu'on n'a pas
    pu jouer — poste sans navigateur pour des e2e, service externe
    indisponible — **n'est pas verte** ; elle se nomme comme telle, avec la
    raison, plutôt que de se fondre dans un compte rendu qui donne l'illusion
    que tout est passé. L'entrée `État final` recopie les verdicts posés dans
    le journal, un par étape, mêmes mots : elle ne les réécrit pas ;
  - **une rétrospective en cinq questions**, courte : qu'est-ce qui s'est
    passé, qu'est-ce qui a marché, qu'est-ce qui a surpris, une note sur 10,
    qu'est-ce qu'on ferait autrement. C'est ce qui nourrira la prochaine
    relecture d'historique sans re-dépouiller les plans passés un par un ;
  - **les schémas relus** — contrôle de `schemas.md` : autant de nœuds
    d'étape dans « le plan en un schéma » que de titres H3 `Étape N` sur la
    page, et les vagues réellement déroulées (§3 ci-dessus, `vagues.md`)
    reportées dans les `subgraph` si elles diffèrent de ce qui était prévu.

    📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`
  - **la taille des `CLAUDE.md`** — la ligne écrite par le geste du point 2
    de la séquence ci-dessous (taille avant, après, destinations, ou « sous
    les plafonds »).
  - **le coût réel du plan** — une ligne `Coût réel : …`, qui vient de
    `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/cout-plan.py --page <identifiant
    de la page du plan>`, lancé une fois à la clôture (environ 35 secondes).
    Sa sortie est recopiée telle quelle sous la ligne, dans l'entrée `État final`.
    Le total est en dollars d'équivalent API, et il est lu avec le barème de
    `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cout-des-plans.md`. Codes de sortie :
    0, le total est rendu ; 1, aucune session ne cite la page, ou aucune n'a de
    tokens chez ccusage : la ligne dit « coût non mesuré », avec la raison ;
    2 : `ccusage`, la grille ou le dossier des journaux indisponible, ou argument
    invalide ; l'erreur se recopie, et la ligne ne porte aucun chiffre inventé.
    `--page` attend l'identifiant de la page (32 caractères hexadécimaux, tirets
    facultatifs), pas son URL. Aucun pourcentage de quota.
- **Le compte rendu du chat est le récap** (Q15, `changelog-et-doc.md` § 3), sans
  réécriture : les quatre rubriques **Nouveau, Amélioré, Corrigé, Reste à faire**,
  dans cet ordre, chaque ligne ✨ ou 🔧 avec sa source ; puis une ligne
  `PR : <lien> · Statut : <statut>` ; puis le bloc **« Côté technique »**.
  Le texte des rubriques est celui du Récap de la page (point 7, geste b).
- **Côté technique** (le bloc replié, rien de perdu) : les étapes parties en
  sous-agent `executant` (Haiku) et, pour celles faites en direct, pourquoi (§3) ;
  la PR, son URL, prête — avec ou sans le label `review-required` selon ce que ce
  dépôt-là en fait (relevé du §2, les quatre cas connus au §6) — ou pourquoi elle
  est en brouillon, retenue, ou attend la réponse de Benjamin sur un trou e2e ;
  les rubriques **Ajouts sans question** et **Recos appliquées par défaut** de
  l'`État final`, même vides (« aucun »).
- **Doc vivante** : une ligne dit quel palier a posé l'entrée du hub (connecteur
  Notion, `composio`, ou fichier confié à Hermes : point 7, cascade), ou que le
  projet est désactivé, ou pose la question « Doc vivante : à activer pour
  <projet> ? » quand l'encadré manque (`changelog-et-doc.md` § 5). L'entrée
  `État final` du journal reste telle quelle, comme trace complète.
- **Avant le point 1 : trier le reste à faire.** Benjamin ne relit pas un plan
  terminé : un reste à faire n'y reste pas en phrase. Chaque ligne passe le tri de
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md` (« Le tri ») : une
  décision ou une réponse qu'on attend de lui part **dans la session**, par
  `AskUserQuestion`, avant `a merger` ; du travail qui reste tient en une étape
  `D<n>` faite maintenant, ou — au-delà d'**une étape au total** — se **propose dans
  la session** (créer le plan de suite, §7 ; le faire maintenant en étapes `D<n>` si
  c'est réversible et hors sécurité ; l'écarter), le plan de suite valant sans
  réponse ; ce qui attend un événement reste dans `La suite`, repris au Récap. Ce que
  la page garde d'une suite, la session l'a déjà montré. Le
  tri passe **avant** la suite complète du point 1 pour qu'un `D<n>` y soit couvert,
  avant l'ouverture de la PR, et avant le Récap du point 7, qui en reprend le
  résultat sans le décider. Un reste né de la suite complète elle-même repasse par
  ce tri.
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
  2 bis. **Preuve doc, après l'allègement et avant la porte.** Un passage `.md`
     qui cite un nom touché par la branche (fichier, fonction, constante) peut
     être devenu faux sans que rien ne le signale. Le relevé se joue par script,
     à la racine du dépôt du plan, sur le contenu final de la branche : après le
     point 2, qui peut déplacer du texte, et avant le push.
     ```bash
     python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/qualite-doc.py" lecteurs --base origin/main > <scratchpad>/lecteurs.json
     python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/qualite-doc.py" juger --entree <scratchpad>/lecteurs.json
     ```
     `juger` juge les passages en parallèle (`--parallele`, 8 par défaut) et
     écrit son avancement sur la sortie d'erreur : l'attendre sans le tuer.
     - **Le juge répond (code 0)** : `douteux` liste les passages dont le score
       atteint le seuil. Un passage dont `ligne_modifiee_dans_la_branche` est
       vrai dans `lecteurs.json` est **traité d'office**, douteux ou non : `juger`
       ne recopie pas ce champ, on le relit dans le relevé, par `fichier` et `ligne`.
     - **Le juge ne répond pas** : code 3 (juge indisponible) ou code 5 (modèle
       servi autre que celui attendu) : aucun verdict, le pilote relit chaque
       passage relevé et note son verdict au journal. Code 4 (plafond de coût) :
       `passages_non_juges` n'est qu'un nombre ; les passages à relire sont ceux de
       `lecteurs.json` absents de `verdicts` (repérés par `fichier` et `ligne`), de la même façon. Le relevé reste
       obligatoire dans les trois cas.
     - **Traitement, bloquant** : chaque passage douteux ou traité d'office est,
       soit corrigé dans la branche (par l'exécutant, en étape `D<n>` si la
       correction dépasse une retouche, `decouvertes.md` § 2), soit marqué au
       journal : « relu, toujours vrai — <commande ou chemin:ligne> ». Une preuve
       doc non jouée, ou un passage non traité, n'ouvre pas la clôture.
     - **Sortie** : la sortie brute des deux commandes va dans `État final`, telle
       quelle. Un `passages_omis` non nul (plus de 200 passages) se dit au journal :
       le relevé est alors incomplet. Un code 2 (relevé ou entrée illisible)
       n'ouvre pas la clôture, et on le dit à Benjamin.

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
       quand même**, **ouvrir en brouillon**, **attendre**. Pas de question
       si la CI du dépôt rejoue cette preuve sur la PR (label
       `review-required` là où il rejoue les e2e, « La PR, puis la remontée
       sur `main` ») : la preuve est alors couverte, et le nom reste au
       journal et au compte rendu.
     - **Code 2** : page, chapitre `Exécution` ou journal illisible. La porte
       ne passe pas : rien ne se pousse, et on le dit à Benjamin.
  4. **Pousser la branche du plan.** C'est le seul push de la clôture quand le
     relevé du §2 a retenu les commits en local ; sans lui, le travail ne vit
     que sur un disque. La sortie de la preuve va au journal (`État final`).
  5. **Ouvrir la PR, prête.** `gh pr create --base main --head <branche-du-plan>`,
     **sans `--draft`** : le brouillon se demande à Benjamin, il ne se décide pas
     seul. Titre = titre du plan ; corps = une ligne par étape reprise du
     journal, lien vers la page Notion, la ligne `Evals:` (sous-section
     ci-dessous) et la ligne `Doc :` (point 7, « Ensuite »). Label : décidé en
     regardant ce dépôt-là (sous-section).
     `PR` renseignée sur la page dès l'ouverture. **Un trou e2e non couvert par
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
  7. **Écrire la clôture, dans le même tour que le compte rendu.** Quatre gestes sur
     la doc du projet, dans cet ordre, puis l'écriture du journal. Le format, l'ancrage
     et la cascade d'écriture vivent dans
     📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/changelog-et-doc.md` (§ 2, § 4, § 6).
     - **(a) Le Récap.** Le H2 `## Récap · AAAA-MM-JJ · <titre du plan>` s'écrit en tête
       de la page du plan : c'est son **premier H2**, avant `Cartes`, et aussi avant
       `Reprise du plan #N` d'un plan de suite (un encadré d'introduction peut rester
       au-dessus). Un plan de suite n'est jamais dispensé de Récap : relevé du 2026-10-28,
       c'est le cas qui manquait le plus. Son nom commence par `Récap` : jamais
       « Exécution », « Journal » ou « Questions ». Il s'écrit dans tous les cas, projet
       activé ou non. Son en-tête porte `PR` (l'URL ouverte au point 5) et
       `Statut : a merger` : c'est le statut que la page aura à la fin de la clôture, et
       non le statut courant, puisque le Récap s'écrit avant le passage à `a merger`.
       Le titre du plan se lit dans les propriétés de la page, jamais dans son miroir
       local : `changelog-et-doc.md` § 4 point 1.
     - **(b) Le contrôle.** Relire la page fraîche, dans son miroir local, et jouer
       `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/controle-changelog.py <miroir>`.
       Si (a) est parti au palier 3 (la page ne porte pas de Récap), le contrôle ne se
       joue pas sur la page : il se joue sur le fichier Récap du palier 3, seul, sans
       miroir, `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/controle-changelog.py <fichier-recap>`
       (une entrée seule suffit). Si l'entrée du hub part aussi au palier 3 (point (c)),
       elle se contrôle de la même façon sur son propre fichier, `<fichier-hub>`. Chaque
       fichier réellement posé au palier 3 passe le contrôle avant qu'Hermes ne le pose.
       Corriger le texte, jamais le contrôle, jusqu'au code 0 ; une correction se pose par
       `update_content` sur le bloc de la page, ou par réécriture du fichier concerné au
       palier 3, puis on relit. Le corps du Récap et celui de l'entrée du hub sont les
       mêmes (`changelog-et-doc.md` § 2), mais chaque fichier se contrôle quand même : un
       code 0 sur l'un ne prouve rien sur l'autre. Code 2 (entrée absente ou illisible,
       fichier du palier 3 introuvable) : on le dit à Benjamin, et (c) et (d) ne se font pas.
     - **(b bis) La porte, avant `a merger`.** Le contrôle (b) regarde la forme du texte ;
       la porte regarde la présence de la doc. Relire le miroir frais de la page, et jouer
       `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/doc-de-cloture.py --porte <miroir-page>`,
       avec, selon le cas :
       - `--recap-fichier <fichier>` quand le Récap est parti au palier 3 (point (a)) ;
       - `--changelog <miroir-changelog> --pr <N>`, `N` étant la PR de ce plan (point 5),
         seulement pour un projet à encadré `📘 Doc vivante : activée` ; si l'entrée du hub
         part au palier 3, `--hub-fichier <fichier-hub>` s'ajoute à `--pr <N>` : le fichier
         est lu comme une source d'en-têtes, avec la même règle ;
       - `--lot` pour un plan enfant d'un lot (`plan-maitre.md`) : pas d'entrée individuelle,
         mais le Récap reste exigé.
       Code 0 : la porte est passée. Code 1 : une ligne dit ce qui manque. **Code 1 interdit
       `a merger`** : on écrit la pièce manquante (le Récap, ou l'entrée du hub après le
       point (c)), on relit, et on rejoue jusqu'au code 0. Code 2 : entrée illisible, on le
       dit à Benjamin, et `a merger` ne se pose pas.
       L'entrée du hub n'existe qu'après le point (c) : la forme `--changelog --pr` ne peut
       donc passer qu'une fois (c) posé. La première passe, ici, ne contrôle que le Récap ; la
       forme complète se rejoue avant `a merger` (voir « Ensuite » plus bas).
     - **(c) L'entrée du hub.** Un plan couvert par un plan maître (la session en porte
       un : `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`) **ne pose pas
       d'entrée individuelle** au hub : l'entrée consolidée du lot part à la fermeture du
       lot (`changelog-et-doc.md` § 2.4, et `plan-maitre.md`). Ce plan complète à la place
       sa ligne dans le tableau `Récap du lot` de la page maître, colonnes « Ce qui change
       pour toi » et « Reste à faire » : une puce par entrée du Récap du plan, avec son
       lien d'ancre et la mention en clair à côté (`changelog-et-doc.md` § 7). Cette ligne
       se complète quel que soit l'encadré ci-dessous : `plan-maitre.md` la demande à
       chaque clôture de plan, et la page maître n'est pas le hub. Relever la page maître
       fraîche, et écrire par la cascade du point (a).
       Relever la page `Projet` fraîche et lire son encadré d'activation
       (`changelog-et-doc.md` § 5) :
       - `📘 Doc vivante : activée` : créer la sous-page `📰 Changelog` (icône comprise)
         sous la page `Projet` si elle manque, et, sauf plan couvert par un plan maître,
         poser l'entrée **en tête**, ancrée après la fin complète du dernier bloc qui
         précède les entrées, jamais au milieu d'un paragraphe formaté. L'encadré
         « Doc partielle » ne se pose pas ici : il vit sur la page mère (point (d)). Relever
         aussi si la ligne `📘 Rétro-doc : faite AAAA-MM-JJ` figure sous l'encadré : elle
         conditionne l'encadré du point (d).
       - `📘 Doc vivante : désactivée` : (c) et (d) sont sautés. Le Récap reste écrit.
       - Encadré absent : (c) et (d) attendent. La question « Doc vivante : à activer
         pour <projet> ? » part dans le compte rendu, à chaque clôture tant qu'il manque.
     - **(d) Les fiches et les processus.** Projet activé seulement. Les fiches vivent
       sous la page mère `📚 Documentation`, elle-même sous la page `Projet`, rangées par
       famille (`changelog-et-doc.md` § 1). Trois gestes, dans cet ordre :
       - **La page mère.** Lire d'abord la ligne `📘 Rétro-doc : faite` de l'encadré
         d'activation (point (c)). Si elle est absente, l'encadré `🚧 Doc partielle —
         rétro-doc pas encore faite` se pose ; si elle est présente, la rétro-doc est faite
         et l'encadré ne se pose pas (`changelog-et-doc.md` § 5). Si la page mère manque, elle
         se crée vide de vue d'ensemble, avec ou sans cet encadré selon cette même ligne
         (§ 5, cas sans page mère) ; elle ne déplace jamais une page existante. Si la page
         mère existe sans encadré « Doc partielle », et la ligne est absente, l'ajouter en
         tête de la page mère ; s'il existe, le laisser en place. Un encadré resté sur la
         page `Projet` par l'ancienne règle n'est pas déplacé : le dire dans le compte rendu.
       - **La famille.** Chaque fiche se range dans la famille qui lui convient, sous-page
         de la page mère, avec son emoji et sa phrase. Si aucune ne convient, en créer une
         sous la page mère, icône et phrase comprises.
       - **La fiche.** Une fiche par fonctionnalité que le plan touche, et seulement celles-là,
         créée si elle manque, avec son icône et ses cinq titres à emoji, dans l'ordre et
         l'orthographe du § 9.2 de `changelog-et-doc.md`. Une fiche existante reçoit une ligne en tête
         de son `🕰️ Historique`, au format du § 4, point 4, par `update_content`. Une fiche
         déjà là hors de sa famille (ancienne place) n'est jamais déplacée : elle reçoit sa
         ligne d'historique, et son emplacement se signale dans le compte rendu. Une fiche
         créée a sa ligne au tableau `🧩 Fonctionnalités` de la page mère, s'il existe :
         `changelog-et-doc.md` § 5.
       La vue d'ensemble et les processus clés ne se mettent à jour que s'ils existent et
       que le diff du plan les touche : jamais créés, jamais réécrits au jugé (c'est le rôle
       de la rétro-doc, `changelog-et-doc.md` § 5). Les lignes « Sous le capot » des briques
       que le diff touche se mettent à jour à partir du diff (§ 9), jamais de mémoire.
     - **(e) Le rattrapage des PR sans entrée.** Projet à encadré `📘 Doc vivante : activée`
       seulement. Relever les PR mergées du dépôt, à la racine du dépôt du plan :
       `gh pr list --state merged --limit 200 --json number,title,mergedAt,author,labels > <scratchpad>/prs.json`.
       Puis, sur le miroir frais du `📰 Changelog`, jouer
       `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/doc-de-cloture.py --trous --changelog <miroir-changelog> --prs <scratchpad>/prs.json --projet <miroir-page-projet> [--sauf <N de ce plan>]`.
       - `--projet` : le miroir frais de la page projet. La date d'activation s'y lit, sur la
         ligne `📘 Activée le AAAA-MM-JJ` de l'encadré `📘 Doc vivante : activée`
         (`changelog-et-doc.md` § 5). `--depuis <date>` reste possible à sa place, et l'emporte
         (`--projet` n'est alors pas requis). Si la ligne manque (code 2), on ne devine pas la
         date : on ne joue pas `--trous`, et on le dit à Benjamin.
       - `--sauf` : la PR de ce plan, si son entrée n'est pas encore au hub (plan couvert par
         un plan maître, ou entrée restée au palier 3).
       - Code 0 : aucun trou. Code 1 : chaque PR listée reçoit une entrée « Sans plan »
         (`changelog-et-doc.md` § 2.6), contrôlée par `controle-changelog.py` avant pose, puis
         posée par la cascade du point Cascade ci-dessous. Code 2 : on le dit à Benjamin.
       - Rattachement : pour `hermes-custom`, la doc va toujours au hub Hermes (`changelog-et-doc.md`
         § 1), avec ou sans plan. Ailleurs, une PR qui a un plan (son numéro figure dans la ligne
         `Plan :` d'une page de plan) va au projet de ce plan. Une PR sans plan va au projet du dépôt
         s'il n'a qu'une page projet. Si un autre dépôt en a deux sans hub fixé, on ne devine pas :
         on demande à Benjamin.
       - Une PR de dépendances ne reçoit jamais d'entrée « Sans plan » (`--trous` les écarte).
       - L'entrée « Sans plan » ne remplace pas l'obligation du plan lui-même : une PR qui a un
         plan doit son entrée de plan (point (c)). Le rattrapage la couvre en attendant, et le
         compte rendu le dit à Benjamin.
     - **Cascade.** (a), (c), (d) et (e) suivent la cascade de repli de `changelog-et-doc.md`
       § 6 : connecteur Notion, puis la commande `composio`, puis le fichier confié à
       Hermes. Les commandes sont dans la fiche « Connecteurs MCP d'une session Claude
       Code » de `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md` : elles ne
       se recopient pas ici. Le compte rendu dit quel palier a posé l'entrée.
       Au palier 3, deux fichiers distincts sous `~/brouillons/<projet>/changelog/`, pour
       un même plan et une même date, chacun avec son propre titre :
       - `<AAAA-MM-JJ>-<plan>-recap.md` : le Récap de la page du plan, titre
         `## Récap · AAAA-MM-JJ · <titre du plan>`. Il s'écrit **dès que (a) n'a pu
         partir**, quel que soit l'encadré : sans lui, le Récap n'existe nulle part.
       - `<AAAA-MM-JJ>-<plan>.md` : l'entrée du hub, titre `## AAAA-MM-JJ · <titre du plan>`
         (`changelog-et-doc.md` § 2). Il ne s'écrit **que si l'encadré est
         `📘 Doc vivante : activée`**, et jamais pour un plan couvert par un plan maître
         (point (c)). Un projet désactivé ou sans encadré n'en reçoit aucun.
       Chaque fichier de palier 3 se donne à la porte (point (b bis)) : le Récap par
       `--recap-fichier`, l'entrée du hub par `--hub-fichier`, avec `--pr <N>`.
       Chaque fichier posé passe le contrôle (b) avant qu'Hermes ne le pose par
       `composio`. Le compte rendu les signale chacun comme à poser par Hermes, avec leur
       chemin, et dit quel palier a posé quoi.
       Au palier 3, (d) ne crée ni page mère, ni famille, ni fiche : les fiches prêtes
       restent dans le compte rendu, et leur création attend le retour du connecteur ou de
       `composio` (`changelog-et-doc.md` § 6, point 3).

     Ensuite, la porte se rejoue dans sa forme complète, après (c) et (d) : `--porte` avec
     `--changelog` et `--pr` quand le projet est activé, `--hub-fichier` si l'entrée du hub
     est partie au palier 3, et `--recap-fichier` si le Récap l'a été ; et `--lot` pour un
     plan enfant d'un lot (pas d'entrée individuelle au hub, point (c)), pour qu'un plan
     enfant ne pose pas une entrée individuelle sur un code 1. Code 0 exigé ; sinon on écrit
     la pièce manquante et on rejoue.
     Puis la **ligne `Doc :` de la description de la PR** (`gh pr edit <n> --body-file …`) :
     `Doc : <lien Notion de l'entrée du Changelog>` pour un projet activé ;
     `Doc : sans objet — lot <plan maître>, entrée consolidée à la fermeture du lot` pour un
     plan enfant d'un lot ; `Doc : sans objet — doc vivante non activée pour <projet>`
     sinon. Le dépôt qui a un job CI `doc` la relit par l'API : relancer ce job après
     l'édition (`gh run rerun <id> --job <id>`), sans quoi la PR reste rouge et ne se
     merge pas. Le job refuse une raison qui n'en est pas une (règle globale
     `doc-vivante.md`) : la page projet non lue, ou l'absence de job CI, n'en sont pas.
     Puis le journal et le compte rendu : `État final` (avec la sortie du point 6),
     `Statut` = **`a merger`**, `PR` = l'URL, et le compte rendu à Benjamin, qui est le
     récap (plus haut). `a merger` est vrai à cet instant : le code n'est pas encore sur
     `main`. Le rattrapage du point (e) se pose dans le même tour, sans attendre le merge.
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
       final`, retirer le worktree. Ce tour peut être un tour ultérieur à celui du
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
       `git worktree add`.

     Retrait du worktree (issues a et c) : `git worktree remove
     ~/repos/worktrees/<repo>/<branche-kebab>` — **la branche, elle, reste** : c'est
     le hook `SessionStart` qui la nettoiera après le merge éventuel, et **une
     branche encore checked-out dans un worktree n'est jamais nettoyée par ce hook**
     tant que le worktree existe. Retirer le worktree avant le hook, jamais la
     branche à sa place.

Un plan laissé à `en cours` raconte que le travail est en suspens alors qu'il est
livré, et c'est la page qui fait foi. Ce statut s'oublie exactement comme la règle
d'entrée s'oublie : en étant absorbé par le travail lui-même. D'où le fait de le
poser dans le tour du compte rendu, pendant qu'on y pense encore.

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
- **Ce qui retient le merge** : une PR brouillon (demandée par Benjamin), une CI
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
La fumée ne se joue que si Benjamin la demande dans son message courant : la session
pose alors le label `fumee`, ouvre la PR en brouillon puis la passe prête (jamais de
pose de sa propre initiative). Le label `evals` ne se pose que sur demande de Benjamin,
pour des catégories ou `tout`, jamais pour `aucun`. Sans ce label, une ligne `Evals:`
absente ou `aucun — <raison>` ne rend pas la CI rouge ; un `aucun` sans raison, ou
combiné à une catégorie, la rend rouge (`evals-portee`). Coûts :
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`.

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
