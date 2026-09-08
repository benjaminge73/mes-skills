# Les vagues d'étapes, et leur parallélisation

Fichier **partagé**, lu par `executer-plan-notion` à l'ouverture, juste après le
relevé de la CI (§2) — c'est là que se calcule la liste des vagues pour tout le
plan, une fois pour toutes, avant la première étape. Comme `ecrire-dans-notion.md`
et `schemas.md`, il vit à un seul endroit pour que le skill garde sa taille : la
règle ne se duplique pas, elle se référence.

Il ne dit pas *comment* écrire dans Notion (`ecrire-dans-notion.md`) ni *quels*
schémas poser (`schemas.md`). Il dit *quand* deux étapes peuvent tourner en
parallèle, *comment* les isoler pendant qu'elles tournent, et *comment* reporter
leur travail sur la branche du plan sans rien perdre.

## Pourquoi ce fichier

Deux faits, remontés par l'enquête sur les plans passés :

- **56 plans sur 77 avaient des étapes réellement indépendantes** — fichiers
  disjoints, aucune dépendance déclarée — et **5 seulement l'ont exploité**. La
  très grande majorité d'un travail parallélisable a été déroulée en séquence,
  pour rien : le skill disait « jamais en parallèle » sans distinguer le cas où
  deux étapes se marchent dessus de celui où elles ne se touchent pas.
- **Tous les conflits d'exécution observés dans ces 77 plans viennent d'un
  fichier partagé non repéré** — `dependabot_night_watch.py` liant cinq étapes
  d'un même plan sans que la liste de fichiers de chacune le montre,
  `deploy.py`, `ci.yml`, un README, un test de décompte. Paralléliser sans
  repérer ces fichiers-là reproduit le problème que la règle « jamais en
  parallèle » cherchait à éviter, juste plus vite.

Paralléliser n'est donc pas un objectif en soi : c'est un gain qui n'existe que
si le repérage des fichiers partagés est fait sérieusement avant.

## Calculer les vagues

À l'ouverture (§2 du skill), juste après le relevé de la CI, lire le tableau de
chevauchement du chapitre `Exécution` (`plan-notion` le construit : colonnes
`Étape · Fichiers touchés · Dépend de · Vague` — le plan **déclare** ces
colonnes, ce fichier-ci **calcule** les vagues à partir d'elles) et poser, pour
chaque paire d'étapes, trois conditions. Les trois doivent être vraies pour que
la paire aille dans la même vague :

1. **L'intersection réelle de leurs listes de fichiers est vide.** Réelle,
   c'est-à-dire les fichiers du tableau, pas une supposition — deux étapes qui
   touchent des fichiers de même nom dans des dossiers différents ne se
   chevauchent pas ; deux étapes qui touchent le même fichier, même pour une
   ligne chacune, se chevauchent.
2. **Aucune ne dépend de l'autre**, colonne `Dépend de` du tableau. Une
   dépendance déclarée l'emporte toujours sur une intersection de fichiers
   vide : l'étape 6 peut n'éditer aucun fichier de l'étape 5 et pourtant avoir
   besoin de son résultat (une fonction qu'elle appelle, un schéma qu'elle
   suppose déjà en place).
3. **Aucun fichier partagé n'est touché par les deux.** Un fichier partagé est
   de la config, un README, un `CLAUDE.md`, un test de décompte, ou
   `plugin.json` — un fichier que la liste de fichiers d'une étape peut
   omettre parce qu'il semble annexe, mais qui casse silencieusement si deux
   sous-agents l'éditent en même temps sans se voir. **Un fichier partagé
   touché par deux étapes interdit la vague**, même si les deux conditions
   précédentes sont vraies : c'est précisément la forme des conflits observés
   dans l'historique (`dependabot_night_watch.py`, `deploy.py`, `ci.yml`, un
   README, un test de décompte).

Deux étapes qui passent les trois conditions vont dans la même vague. Une
étape qui ne partage sa vague avec personne reste seule dans la sienne, et se
déroule comme avant : un sous-agent, en séquence.

Le résultat de ce calcul — la liste des vagues, une ligne par vague — va dans
l'entrée `Ouverture` du journal, à côté des trois réponses sur la CI (§2, §4) :
c'est la même entrée, parce que les deux relevés commandent la suite de la
même façon.

## Une étape parallèle = un worktree

Décision de Benjamin (Q3) : chaque étape d'une vague tourne dans son propre
**worktree** — une copie de travail liée au dépôt principal par git, isolée sur
le disque — jamais dans le checkout principal, que les autres étapes de la
vague utilisent en même temps.

- **Chemin** : `~/repos/worktrees/<repo>/etape-N`, sous `mkdir -p
  ~/repos/worktrees/<repo>` créé avant si besoin.
- **Branche** : `<branche-du-plan>-etape-N`, créée depuis la **tête de la
  branche du plan** au moment où la vague s'ouvre — pas depuis `main`, sans
  quoi l'étape ne verrait pas ce que les étapes précédentes (hors vague) ont
  déjà commité.

  ```bash
  git worktree add ~/repos/worktrees/<repo>/etape-N -b <branche-du-plan>-etape-N <branche-du-plan>
  ```

  **Pourquoi un tiret et pas un `/`.** La forme `<branche-du-plan>/etape-N`,
  qui semblait la plus naturelle, est **impossible** dès que
  `<branche-du-plan>` existe comme branche : git range les branches sous
  `refs/heads/` comme des chemins de fichiers, et `feat/x/etape-1` demanderait
  que `refs/heads/feat/x` soit à la fois un fichier (la branche `feat/x`) et un
  dossier (le préfixe de `feat/x/etape-1`) — `fatal: cannot lock ref
  'refs/heads/feat/x/etape-1': 'refs/heads/feat/x' exists`. Le tiret évite le
  conflit : `<branche-du-plan>-etape-N`.
- **Lancement** : un appel `Agent` par étape de la vague, tous dans **le même
  tour** de la session de pilotage, avec `run_in_background: true` — c'est la
  seule différence avec le gabarit séquentiel (§3 du skill) : le paramètre
  passe de `false` à `true` pour les étapes d'une même vague, tout le reste du
  gabarit et du brief (§3) reste identique, worktree en plus dans le contexte
  donné au sous-agent.

## Au retour

Chaque sous-agent de la vague travaille dans son worktree, sur sa branche
d'étape, et rend son rapport (§3 du skill, quatre états). Au retour de **tous**
les sous-agents de la vague :

1. **La preuve est rejouée par la session, dans chaque worktree** — pas dans le
   checkout principal, tant que le report n'a pas eu lieu : la commande de
   preuve du brief (§3) s'exécute avec `cd ~/repos/worktrees/<repo>/etape-N`,
   sur la liste réelle des fichiers touchés dans ce worktree.
2. **Commit sur la branche d'étape**, dans le worktree, comme pour une étape
   séquentielle.
3. **Report sur la branche du plan, dans l'ordre des numéros d'étape** — même
   si les rapports arrivent dans un ordre différent :

   ```bash
   git checkout <branche-du-plan>
   git cherry-pick <sha-etape-N>
   ```

   ⚠️ `cherry-pick` **n'a pas d'option `-q`** : un incident vérifié a vu une
   chaîne `cherry-pick -q … && … ; git branch -D` échouer dès l'usage
   invalide, puis supprimer la branche d'étape avant que le report soit
   vérifié — le commit restait joignable par son SHA, rien n'a été perdu, mais
   la vérification qui aurait dû précéder le nettoyage a sauté. D'où la règle
   suivante.
4. **Vérifier le report avant tout retrait**, dans un appel séparé de celui qui
   nettoie :

   ```bash
   git log -1 <branche-du-plan>
   ```

   Le SHA affiché doit correspondre au commit reporté (un nouveau SHA après
   cherry-pick, le contenu identique). **Seulement ensuite**, dans un appel
   séparé :

   ```bash
   git worktree remove ~/repos/worktrees/<repo>/etape-N
   git branch -D <branche-du-plan>-etape-N
   ```

   Chaîner la vérification et le nettoyage dans le même appel est exactement
   ce qui a produit l'incident : si le premier maillon échoue silencieusement
   ou sur un usage invalide, le shell peut enchaîner sur la suppression sans
   que personne n'ait relu le résultat.

## Regrouper deux étapes dans un seul sous-agent

Décision de Benjamin (Q4) : deux étapes **consécutives** qui **partagent au
moins un fichier** et **cumulent au plus cinq fichiers** partent dans un seul
sous-agent plutôt que dans une vague — le chevauchement de fichiers qui
interdirait la vague (section précédente) est ici la condition même du
regroupement.

- **Un brief à deux objectifs** : les deux objectifs d'étape recopiés du
  chapitre `Exécution` (§3, point 1 du brief), l'un après l'autre, avec pour
  chacun sa propre commande de preuve.
- **Un rapport par étape**, pas un rapport fusionné : le sous-agent rend deux
  comptes rendus distincts, chacun avec ses fichiers touchés et le SHA de son
  commit.
- **Le sous-agent commite la première étape avant d'ouvrir la seconde**, avec
  le message de commit fourni dans le brief — **c'est la seule exception à la
  règle « ni `commit` » du brief standard (§3, point 5)**, et elle est
  nécessaire : deux étapes qui éditent le même fichier ne peuvent pas être
  commitées après coup « par liste de fichiers » par la session, puisqu'un
  seul état du fichier existe sur le disque une fois les deux étapes
  terminées — il faut que le commit de la première ait lieu avant que la
  seconde ne continue à écrire dessus.
- **La session rejoue la preuve sur chaque commit séparément** — `git show
  <sha-etape-1>:<fichier> | grep …`, puis la même chose sur le second SHA —
  et **amende si besoin** avec `git reset --soft` suivi d'un nouveau commit,
  plutôt que de laisser un commit d'étape porter le travail d'une autre.

## Le journal garde l'ordre des numéros

Que les étapes viennent d'une vague, d'un regroupement ou du déroulé
séquentiel, **le journal s'écrit dans l'ordre des numéros d'étape** (§4 du
skill) — jamais dans l'ordre d'arrivée des rapports de sous-agent. Une vague de
quatre étapes peut rendre ses rapports dans n'importe quel ordre ; les entrées
H3 `Étape N` se posent dans la page en suivant N, pas l'heure de retour.

## Ce que ça coûte, et ce que ça protège

Un worktree par étape parallèle coûte quelques secondes à créer et à retirer,
et un peu d'espace disque le temps de la vague. Ce que ça protège : le
**checkout partagé**, observé sur 7 plans de l'historique — deux sessions (ou
deux sous-agents non isolés) modifiant le même répertoire de travail en même
temps, chacune écrasant les fichiers de l'autre sans qu'aucune des deux ne le
sache avant la preuve suivante, rouge pour une raison qui n'a rien à voir avec
le code de l'étape.
