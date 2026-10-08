# Clore — le détail du §6

Fichier de référence de `executer-plan-notion` : `SKILL.md` §6 dit **quand** le
lire (à la clôture, et à chaque demande de PR ou de remontée sur `main`). Le
détail vit ici.

Sommaire :

- Dans le même tour : `Statut`, `Branche`, entrée `État final`, compte rendu
- La séquence de clôture (suite complète locale, push, pas de PR, contrôle
  bloquant, retrait du worktree)
- La PR, puis la remontée sur `main` — sur demande seulement

Dans le **même tour** que le compte rendu à Benjamin, jamais « plus tard » :

- `Statut` : **`a merger`**. C'est le statut normal de fin d'exécution, sur tous
  les dépôts : le travail est livré sur la branche du plan, prouvé en local, et
  il attend une décision de remontée qui n'appartient pas à ce skill. `execute`
  ne se pose que sur du code **vérifié sur `main`** (sous-section suivante).
  Une seule question, et sa réponse est factuelle — *où est le code à cette
  seconde ?* Poser `execute` sur du travail qui dort sur une branche fait croire
  la base plus avancée qu'elle ne l'est, et c'est le genre de mensonge qu'on ne
  découvre qu'en cherchant une fonctionnalité absente de la production. **La
  symétrie est vraie aussi, et c'est elle qu'on oublie** : laisser `a merger`
  sur du travail déjà parti sur `main` annonce un chantier en attente qui
  n'existe plus, et le plan suivant repart d'une base fausse.
- Ce skill ne pose jamais `archive` : ranger une page est une décision de
  Benjamin, pas un effet de bord d'un merge.
- `Branche` renseignée : la branche du plan. `PR` reste **vide** tant qu'aucune
  PR n'existe — une propriété remplie d'une PR qui n'a pas été ouverte ment
  autant qu'un statut faux.
- `Journal d'exécution` clos par une entrée `État final` (H3, comme les autres,
  §4) : ce qui est livré, le verdict de la suite complète (point 1 ci-dessous),
  les écarts, le reste à faire s'il y en a — **chaque ligne avec son propriétaire** :
  une question à Benjamin, ou le plan de suite (§7) qui la porte ; une ligne sans
  propriétaire se règle avant `a merger` — et le lien vers le plan de suite s'il
  y en a un. Cette entrée porte aussi :
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
  - **le contrôle des libellés** (§4) : `grep -c 'Découvertes :' <journal>`
    égale `grep -c '^### Étape ' <journal>`, et chaque ligne marquée `ÉCART`
    ou `BLOQUÉ` a son libellé. Un écart entre les deux nombres, ou une
    surprise sans libellé, se corrige avant de poser `a merger`, en respectant
    la règle « dans le doute, `trouvable` » (§4) ;
  - **le registre des outils** : toute découverte qui concerne un outil
    (quota, coût, piège, repli) part en PR sur `mes-skills`, dans
    `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`, fiche datée et
    sans nom privé — la règle de publication du fichier s'applique. Ce n'est
    pas la PR du plan : elle vise un autre dépôt, et la règle de ce §6 (aucune
    PR d'initiative) vaut pour elle aussi — le compte rendu la propose, et
    Benjamin décide de la remontée ;
  - **un verdict par étape, `verified` ou `unverifiable`** — jamais un
    troisième mot. `verified` : la preuve du brief a été rejouée par la
    session et elle est verte (§3). `unverifiable` : une preuve qu'on n'a pas
    pu jouer — poste sans navigateur pour des e2e, service externe
    indisponible — **n'est pas verte** ; elle se nomme comme telle, avec la
    raison, plutôt que de se fondre dans un compte rendu qui donne l'illusion
    que tout est passé ;
  - **une rétrospective en cinq questions**, courte : qu'est-ce qui s'est
    passé, qu'est-ce qui a marché, qu'est-ce qui a surpris, une note sur 10,
    qu'est-ce qu'on ferait autrement. C'est ce qui nourrira la prochaine
    relecture d'historique sans re-dépouiller les plans passés un par un ;
  - **les schémas relus** — contrôle de `schemas.md` : autant de nœuds
    d'étape dans « le plan en un schéma » que de titres H3 `Étape N` sur la
    page, et les vagues réellement déroulées (§3 ci-dessus, `vagues.md`)
    reportées dans les `subgraph` si elles diffèrent de ce qui était prévu.

    📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`
- Le compte rendu dit **quelles étapes sont parties en sous-agent `executant` (Haiku)** et,
  pour celles faites en direct, pourquoi (§3). Il dit aussi, en une ligne, que
  **la PR n'est pas ouverte et qu'elle le sera sur demande** — avec ou sans le
  label `review-required` selon ce que ce dépôt-là en fait (relevé du §2, les
  trois cas connus au §6).
- **Livrer la branche, et s'arrêter là.** Pas de PR : la remontée vers `main`
  est un geste vers l'extérieur, et il n'a lieu que sur demande explicite de
  Benjamin. La séquence de clôture est courte :
  1. **Jouer la suite complète en local** : tous les tests unitaires, lint,
     build, **et les tests e2e** — c'est ici, et seulement ici, qu'ils passent
     (§3). C'est **le verdict de fin de plan** : tant qu'il n'est pas vert, le
     plan n'est pas clos. Rouge → corriger jusqu'au vert, même boucle qu'en
     cours de route ; correctif structurant ou échec qu'on ne sait plus
     diagnostiquer → même arbitrage (§3) : journal, plan de suite (§7), et la
     page reste à `en cours`. Une suite qui n'est pas jouable sur le poste (e2e
     sans navigateur, par exemple) se dit au journal, tests nommés — ce n'est
     pas un vert, c'est un trou, et Benjamin doit le voir avant de demander la
     PR. Suite complète et e2e prennent le jeton des actions lourdes :
     `${CLAUDE_PLUGIN_ROOT}/skills/_partage/machine-partagee.md`.
  2. **Pousser la branche du plan.** C'est le seul push de la clôture quand le
     relevé du §2 a retenu les commits en local ; sans lui, le travail ne vit
     que sur un disque. La sortie de la preuve va au journal (`État final`).
  3. **Ne pas ouvrir la PR.** Ni la merger, ni la préparer « pour gagner du
     temps ». Le compte rendu s'arrête sur la branche, prouvée et poussée.
  4. **Contrôle bloquant, avant de poser `a merger`** :
     ```bash
     git branch --list '<branche-du-plan>-etape-*'
     git worktree list
     ```
     Rien d'autre que les branches `<branche-du-plan>-etape-N-en-echec`
     déclarées au journal, ni le worktree du plan (retiré au point suivant).
     Des branches de vague qui survivent à leur plan n'ont pas de filet après
     coup : plan parent squash-mergé, `git cherry` y rend `+` pour tout.
     Survivance → vérifier le report (`git log
     <branche-du-plan>`, `git cherry <branche-du-plan> <branche-d-etape>` :
     que des `-`), puis nettoyer. Sortie des deux commandes dans l'entrée
     `État final`.

     📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`
  5. **Retirer le worktree**, `git worktree remove ~/repos/worktrees/<repo>/
     <branche-kebab>` — **la branche, elle, reste** : c'est le hook
     `SessionStart` qui la nettoiera après le merge éventuel, et **une branche
     encore checked-out dans un worktree n'est jamais nettoyée par ce hook**
     tant que le worktree existe. Retirer le worktree avant le hook, jamais la
     branche à sa place.

Un plan laissé à `en cours` raconte que le travail est en suspens alors qu'il est
livré, et c'est la page qui fait foi. Ce statut s'oublie exactement comme la règle
d'entrée s'oublie : en étant absorbé par le travail lui-même. D'où le fait de le
poser dans le tour du compte rendu, pendant qu'on y pense encore.

### La PR, puis la remontée sur `main` — sur demande seulement

Benjamin demande la suite quand il le décide : « ouvre la PR », « merge sur
main », « tu peux merger directement », « pousse ça sur main ». Deux demandes
distinctes, et il faut entendre laquelle est faite :

- **« ouvre la PR »** → une seule PR, de la branche du plan vers `main`. **Le
  label `review-required` se décide en regardant ce dépôt-là**, jamais depuis la
  règle générale : il n'existe pas partout, et là où il existe son effet change
  de signe (§6, trois cas relevés). La ceinture reste la suite complète jouée en
  local à la clôture ; le label n'est que la bretelle. Sur `vahiny`, il commande
  aussi le merge par la CI une fois tout vert : y demander la PR, c'est demander
  la remontée, et Benjamin le sait.
  Si le chapitre `Exécution` porte une ligne `Évals à jouer : …`, la recopier dans le
  corps de la PR : `Evals: <catégories> — <raison>`, `Evals: tout` ou `Evals: aucun —
  <raison>`. Le défaut du plan est `aucun — la fumée suffit` : recopier tel quel, sans
  label. Poser le label `evals` pour des catégories ou `tout` (changement de règle de
  comportement, de modèle ou d'effort d'un agent), jamais pour `aucun` ; sans ligne, la
  CI est rouge. Coûts : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`.
- **« merge sur main »** → la PR (ouverte à cette occasion si elle ne l'est
  pas), CI verte, merge, vérification sur pièce, `execute`.

La séquence complète — ouvrir, attendre la CI, vérifier que le merge a bien eu
lieu, poser `Statut` = `execute`, journaliser — et le piège qui la fait échouer
(le point qui saute le plus souvent : le statut, oublié une fois le merge fait)
vivent dans un fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/remontee-sur-main.md`

**À lire à chaque demande**, que ce soit avant l'exécution, en cours de route,
ou une session plus tard sur un plan déjà à `a merger` : c'est la seule
opération de ce skill qui peut arriver à trois moments différents, et qui a déjà
été bâclée en s'arrêtant au merge sans mettre `Statut` à jour. Une demande
explicite se fait **sans réclamer de confirmation supplémentaire** : refuser au
nom d'une règle qui n'existait que pour le protéger, c'est prendre la règle pour
une fin.
