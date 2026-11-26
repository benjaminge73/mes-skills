# Clore — la doc : Changelog, Récap, fiches et rattachement

Détail du §6 (`cloture.md`, noyau) : lu quand la clôture en est à la preuve doc (point 2 bis) ou à l'écriture de la doc (point 7 : Récap, entrée du hub, fiches, rattrapage, ligne `Doc :`). Texte repris tel quel, sans réécriture.

Ordre de la clôture (qui suit qui) : `cloture-reste-et-suite.md` (tri, avant le point 1) → `cloture-pr-et-ci.md` (points 1 à 2) → `cloture-doc.md` (point 2 bis) → `cloture-pr-et-ci.md` (points 2 ter à 6) → `cloture-doc.md` (point 7) → `cloture-reste-et-suite.md` (garde des restes, puis `a merger`) → `cloture-pr-et-ci.md` (point 8). Un « point N » cité sans nom de fichier se trouve dans le fichier que `cloture.md` lui assigne.

- **Doc vivante** : une ligne dit quel palier a posé l'entrée du hub (connecteur
  Notion, `composio`, ou fichier confié à Hermes : point 7, cascade), ou que le
  projet est désactivé, ou pose la question « Doc vivante : à activer pour
  <projet> ? » quand l'encadré manque (`doc-vivante-activation.md`). L'entrée
  `État final` du journal reste telle quelle, comme trace complète.

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

     Suite du point 2 bis : les points 2 ter à 6 sont dans `cloture-pr-et-ci.md`, puis le point 7 reprend ici.

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
       **Ce H2 se crée ici** : la page n'en porte pas avant la clôture, et un plan clos avant
       cette règle peut ne pas en avoir non plus. On relève la page, et s'il manque on le
       pose en tête ; on n'écrit jamais dans un Récap supposé là (`changelog-et-doc.md` § 4,
       point 3 bis).
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
       (`doc-vivante-activation.md`) :
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
         et l'encadré ne se pose pas (`doc-vivante-activation.md`). Si la page mère manque, elle
         se crée vide de vue d'ensemble, avec ou sans cet encadré selon cette même ligne
         (`doc-vivante-activation.md`, cas sans page mère) ; elle ne déplace jamais une page existante. Si la page
         mère existe sans encadré « Doc partielle », et la ligne est absente, l'ajouter en
         tête de la page mère ; s'il existe, le laisser en place. Un encadré resté sur la
         page `Projet` par l'ancienne règle n'est pas déplacé : le dire dans le compte rendu.
       - **La famille.** Chaque fiche se range dans la famille qui lui convient, sous-page
         de la page mère, avec son emoji et sa phrase. Si aucune ne convient, en créer une
         sous la page mère, icône et phrase comprises.
       - **La fiche.** Une fiche par fonctionnalité que le plan touche, et seulement celles-là,
         créée si elle manque, avec son icône et ses cinq titres à emoji, dans l'ordre et
         l'orthographe du § 9.2 de `doc-sous-le-capot.md`. Une fiche existante reçoit une ligne en tête
         de son `🕰️ Historique`, au format du § 4, point 4, par `update_content`. Une fiche
         déjà là hors de sa famille (ancienne place) n'est jamais déplacée : elle reçoit sa
         ligne d'historique, et son emplacement se signale dans le compte rendu. Une fiche
         créée a sa ligne au tableau `🧩 Fonctionnalités` de la page mère, s'il existe :
         `doc-vivante-activation.md`.
       La vue d'ensemble et les processus clés ne se mettent à jour que s'ils existent et
       que le diff du plan les touche : jamais créés, jamais réécrits au jugé (c'est le rôle
       de la rétro-doc, `doc-vivante-activation.md`). Les lignes « Sous le capot » des briques
       que le diff touche se mettent à jour à partir du diff (`doc-sous-le-capot.md`), jamais de mémoire.
     - **(e) Le rattrapage des PR sans entrée.** Projet à encadré `📘 Doc vivante : activée`
       seulement. Relever les PR mergées du dépôt, à la racine du dépôt du plan :
       `gh pr list --state merged --limit 200 --json number,title,mergedAt,author,labels > <scratchpad>/prs.json`.
       Puis, sur le miroir frais du `📰 Changelog`, jouer
       `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/doc-de-cloture.py --trous --changelog <miroir-changelog> --prs <scratchpad>/prs.json --projet <miroir-page-projet> [--sauf <N de ce plan>]`.
       - `--projet` : le miroir frais de la page projet. La date d'activation s'y lit, sur la
         ligne `📘 Activée le AAAA-MM-JJ` de l'encadré `📘 Doc vivante : activée`
         (`doc-vivante-activation.md`). `--depuis <date>` reste possible à sa place, et l'emporte
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
       Code » de `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-connecteurs-et-evals.md` : elles ne
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
     `Doc : <lien d'ancre de l'entrée du Changelog>` pour un projet activé, soit
     `…/p/<page du Changelog>#<id du titre de l'entrée>` (lecture de l'id et repli :
     `changelog-et-doc.md` § 2.5, fin ; le repli s'écrit `<lien de page> — entrée « <titre> »`,
     tiret long, jamais le titre entre parenthèses) ;
     `Doc : sans objet — lot <plan maître>, entrée consolidée à la fermeture du lot` pour un
     plan enfant d'un lot ; `Doc : sans objet — doc vivante non activée pour <projet>`
     sinon. Le dépôt qui a un job CI `doc` la relit par l'API, une seule fois, après les
     tests. **Avant de la passer prête, jouer la garde en local**, depuis le worktree :
     `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-ligne-doc.py" <n>`.
     Le script lit la description par `gh pr view` et la passe à la garde du dépôt
     (`scripts/garde_doc_pr.py` ou `scripts/garde-doc-pr.mjs`), celle que le job `doc`
     jouera : **code 0 exigé**. Un 1 ou un 4 se corrige dans la description, puis on
     rejoue ; un 3 dit que le dépôt n'a pas de garde (c'est l'encadré de la page projet
     qui décide de l'entrée, pas ce code). Relevé du 2026-11-03 : 34 échecs de `doc` en
     19 jours, chacun un run de CI pour une ligne qu'une seconde en local aurait refusée.
     Dans ces dépôts (PR ouverte en brouillon, point 5), **la PR passe prête
     juste après avoir écrit la ligne** (`gh pr ready <n>`, ou `update_pull_request` avec
     `draft: false`) : `ready_for_review` lance le run complet, où `doc` lit une ligne qui
     existe déjà. Une PR laissée en brouillon ne se merge jamais, et rien ne le dit à
     part elle : la passer prête fait partie du point 7, pas de la remontée.
     **Exception, le palier 3** (`changelog-et-doc.md` § 6 : le connecteur Notion
     **puis** `composio` ont échoué, les deux, jamais le fichier d'emblée) : l'entrée
     du hub est un fichier que Hermes posera plus tard, la ligne `Doc :` n'a pas de
     lien à citer, et un `sans objet` serait faux. La PR **reste en brouillon**,
     `Statut` reste `a merger`, la raison va au journal (point 8, issue c). Quand
     Hermes a posé l'entrée, la session qui le constate (la suivante qui lit
     `a merger` comprise) lit le lien d'ancre (§ 2.5), écrit la ligne, puis passe la
     PR prête. Si seule la lecture de l'ancre échoue, pas de brouillon : le repli du
     § 2.5 (lien de la page et titre en clair) suffit. Ces
     dépôts ne jouent **aucune CI sur un brouillon** (les jobs racines sautent) : le run
     `ready_for_review` est le premier et le seul à tout jouer. Là où le label
     `review-required` lance l'e2e (`vahiny`, `mavod-perso`, `micro-trading`), le poser
     **à l'ouverture en brouillon, ou au plus tard avant** `gh pr ready` : sur un
     brouillon il ne coûte rien, et le run de la sortie de brouillon le porte déjà. Si une ligne fausse
     a rougi `doc`, éditer la description suffit : le workflow `doc-relance.yml`
     (déclencheur `edited`) le relance dès que la ligne est valide, run fini. Le job refuse une raison qui n'en est pas une (règle globale
     `doc-vivante.md`) : la page projet non lue, ou l'absence de job CI, n'en sont pas.
     **Avant de poser `a merger`**, dans un dépôt où la PR s'est ouverte en brouillon
     (point 5) : relire `gh pr view <n> --json isDraft`, `false` exigé. Un `true` veut
     dire que la PR n'est pas passée prête : la ligne `Doc :` écrite, on la passe
     prête ; seul un brouillon demandé par Benjamin reste tel quel (point 8, issue c).

Suite du point 7 (garde des restes, `Statut` = `a merger`) : 📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-reste-et-suite.md`, puis point 8 : 📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-pr-et-ci.md`.
