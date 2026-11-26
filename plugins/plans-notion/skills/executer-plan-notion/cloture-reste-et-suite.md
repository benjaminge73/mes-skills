# Clore — l'`État final`, le reste à faire et le compte rendu

Détail du §6 (`cloture.md`, noyau) : lu quand la clôture écrit l'`État final` du journal, trie le reste à faire (« Avant le point 1 »), joue le garde des restes du point 7 ou rédige le compte rendu du chat. Texte repris tel quel, sans réécriture.

Sommaire :

- L'entrée `État final` du journal
- Le compte rendu du chat, qui sert de récap
- Le côté technique, le bloc replié
- Avant le point 1 : trier le reste à faire

Ordre de la clôture (qui suit qui) : `cloture-reste-et-suite.md` (tri, avant le point 1) → `cloture-pr-et-ci.md` (points 1 à 2) → `cloture-doc.md` (point 2 bis) → `cloture-pr-et-ci.md` (points 2 ter à 6) → `cloture-doc.md` (point 7) → `cloture-reste-et-suite.md` (garde des restes, puis `a merger`) → `cloture-pr-et-ci.md` (point 8). Un « point N » cité sans nom de fichier se trouve dans le fichier que `cloture.md` lui assigne.

- `Journal d'exécution` clos par une entrée `État final` (H3, comme les autres,
  §4) : ce qui est livré, le verdict de la suite complète (point 1 ci-dessous),
  les écarts, le reste à faire s'il y en a — **chaque ligne avec son propriétaire** :
  la question posée dans la session (avec la réponse de Benjamin), le plan de suite
  (§7, avec son lien) qui la porte, l'étape `D<n>` qui l'a faite, ou la ligne de la
  base « Restes » qui la porte (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/restes.md`),
  citée par son lien : c'est là que le garde de clôture la cherche (point 7) ;
  une ligne sans propriétaire se règle avant `a merger`
  (`plan-de-suite.md`, « Le tri » ; un reste qui attend un cron se lance à la main
  avant, sans demander sauf conflit, risque de sécurité ou coût non validé). Cette entrée porte aussi :
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
    (quota, coût, piège, repli) part en PR sur `mes-skills` : la fiche datée et
    sans nom privé s'écrit dans le fichier de thème qui porte l'outil (l'un des
    cinq fichiers `outils-claude-code.md`, `outils-connecteurs-et-evals.md`,
    `outils-code-et-securite.md`, `outils-infra-et-documents.md` ou
    `outils-donnees-publiques.md`, tous dans le dossier `_partage/` de l'index),
    et sa ligne d'index dans `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md` ;
    la règle de publication des six fichiers `outils-*.md` s'applique. Ce n'est
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
  - **une rétrospective en six questions**, courte : qu'est-ce qui s'est
    passé, qu'est-ce qui a marché, qu'est-ce qui a surpris, une note sur 10,
    qu'est-ce qu'on ferait autrement, quelle consigne du skill ou du `CLAUDE.md`
    n'a rien changé à cette exécution ? C'est ce qui nourrira la prochaine
    relecture d'historique sans re-dépouiller les plans passés un par un ;
  - **la boucle incident → règle tenue** : pour chaque incident ou découverte signalé dans le journal (pièce 5 de l'exécutant, formule « règle convertie ? »), la session pose la question : « règle convertie ? » — cet incident ou cette découverte est-il devenu une règle tenue par un garde, ou reste-t-il une ligne de prose ? Une ligne de prose se dit telle quelle, avec sa raison. Une règle convertie se dit avec le chemin de son garde, en code, et sa ligne de `docs/garde-fous.md` (statut « manquant » si le garde vient plus tard). Un garde qui reste à écrire part en découverte (`decouvertes.md`), pas dans la clôture. La réponse se recopie dans l'entrée `État final`, une ligne par incident ;
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
  Le texte des rubriques est celui du Récap de la page (point 7, geste b), sauf
  « Reste à faire » (ci-dessous).
  **La rubrique « Reste à faire » recopie chaque point ouvert en entier** (quoi, qui,
  l'action attendue de Benjamin), sans renvoi vers l'`État final` ni vers la page, et
  sans les points devenus sans objet : `plan-de-suite.md`, « Le reste à faire se
  recopie en entier dans la session ». Même exigence au message qui constate le merge.
  **Chaque ligne créée à ce tour dans la base « Restes » (point « Avant le point 1 »)
  est citée dans ce message avec son lien**, à côté du texte du point qu'elle porte.
  Le Récap de la page, lui, ne recopie pas le texte : il cite la ligne par son lien
  (`changelog-et-doc.md`, § 2.1).
- **Côté technique** (le bloc replié, rien de perdu) : les étapes parties en
  sous-agent `executant` (Haiku) et, pour celles faites en direct, pourquoi (§3) ;
  la PR, son URL, prête — avec ou sans le label `review-required` selon ce que ce
  dépôt-là en fait (relevé du §2, les quatre cas connus au §6) — ou pourquoi elle
  est en brouillon, retenue, ou attend la réponse de Benjamin sur un trou e2e ;
  les rubriques **Ajouts sans question** et **Recos appliquées par défaut** de
  l'`État final`, même vides (« aucun »).

- **Avant le point 1 : trier le reste à faire.** Benjamin ne relit pas un plan
  terminé : un reste à faire n'y reste pas en phrase. Chaque ligne passe le tri de
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md` (« Le tri ») : une
  décision ou une réponse qu'on attend de lui part **dans la session**, par
  `AskUserQuestion`, avant `a merger` ; du travail qui reste tient en une étape
  `D<n>` faite maintenant, ou — au-delà d'**une étape au total** — se **propose dans
  la session** (créer le plan de suite, §7 ; le faire maintenant en étapes `D<n>` si
  c'est réversible et hors sécurité ; l'écarter). Un petit reste (un geste ou une vérification dans le dépôt du plan, hors comptes de Benjamin, réversible, hors sécurité, 15 minutes au plus, estimé à côté : « ≈ 10 min ») se fait sur place en `D<n>` avant `a merger`, sans être versé (`plan-de-suite.md`, « Le tri », point 2). Ce qui n'a pas de réponse dans la
  session devient une ligne de la base « Restes »
  (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/restes.md`) : une décision sans réponse
  (`Type` `décision`), un geste que seul Benjamin peut poser (`geste`), un événement
  attendu (`suivi`). Le plan de suite ne vaut sans réponse que s'il reste aussi du
  travail. Les lignes s'écrivent ici, une par reste, `Plan d'origine` = ce plan, par la
  cascade d'écriture de `changelog-et-doc.md` (§ 6) ; si toute la cascade échoue, la
  ligne ne s'écrit pas ailleurs, et le garde du point 7 refuse `a merger`. Ce que
  la page garde d'une suite, la session l'a déjà montré. Le
  tri passe **avant** la suite complète du point 1 pour qu'un `D<n>` y soit couvert,
  avant l'ouverture de la PR, et avant le Récap du point 7, qui en reprend le
  résultat sans le décider. Un reste né de la suite complète elle-même repasse par
  ce tri. Une étape **déjà validée** dans le plan (case cochée, plafond écrit) et confiée à Hal ne
  part pas à Benjamin comme un reste : elle se transmet à Hal, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/demander-a-hal.md`
  (§ 2 bis), et le compte rendu écrit « transmise à Hal, plafond X $, validé en Qn ». Jamais « dis-moi go ».
  Un dépassement de ce plafond, lui, reste une question à Benjamin.

     Suite du tri : le point 1 (suite complète) est dans `cloture-pr-et-ci.md`. Le garde ci-dessous se joue au point 7, après la clôture écrite de `cloture-doc.md`.

     **Avant de poser `a merger`, le garde des restes** (tout plan, PR en brouillon ou
     non) : relire le miroir frais de la page du plan, puis jouer
     `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/restes-sans-ligne.py <miroir-page> --lignes <lignes.json>`.
     `<lignes.json>` vit dans le scratchpad de la session : c'est l'export des lignes de
     la base « Restes » dont `Plan d'origine` est ce plan, relues après écriture, au format
     de `restes.md` (clés `Reste`, `Pour`, `État`, `Plan d'origine`, et `url` = le lien de
     la ligne). Le garde lit la rubrique « Reste à faire » de l'`État final` : chaque reste
     en attente doit y citer sa ligne, par son lien ou par son texte. Code 0 : tout a sa ligne.
     **Code 1 interdit `a merger`** : le garde écrit sur la sortie un défaut par reste sans
     ligne ; on écrit la ligne (point « Avant le point 1 »), on relit, et on rejoue jusqu'au
     code 0. Code 2 (page ou export illisible) : on le dit à Benjamin, et `a merger` ne se
     pose pas.
     Puis le journal et le compte rendu : `État final` (avec la sortie du point 6),
     `Statut` = **`a merger`**, `PR` = l'URL, et le compte rendu à Benjamin, qui est le
     récap (plus haut). `a merger` est vrai à cet instant : le code n'est pas encore sur
     `main`. Le rattrapage du point (e) se pose dans le même tour, sans attendre le merge.
