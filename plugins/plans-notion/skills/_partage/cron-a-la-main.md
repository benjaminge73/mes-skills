# Un cron modifié se lance à la main, pendant l'exécution

Vaut aussi pour les cousins du cron, un hook Claude Code et un workflow lancé par
un événement (section « Les cousins du cron »).

Fichier référencé par `plan-notion` (filtre de §8, contrôle 13), par
`executer-plan-notion` (étape `C<n>`, via `etapes.md`) et par
`remontee-sur-main.md` (point 4 ter, le rejeu après le merge).

## Pourquoi cette règle

Un **cron** (une tâche qui se lance seule, à heure fixe) est un programme que
personne ne regarde tourner. Si un plan modifie son script et que rien ne le lance
avant la mise en production, la première preuve arrive **la nuit suivante, en
production** : une erreur passe alors sans bruit, et elle coûte une nuit de
sauvegarde ou de publication. La règle déplace cette première preuve dans
l'exécution, là où une erreur se corrige encore à peu de frais.

Le cron touché se fait donc tourner **à la main, pendant l'exécution** (une
« étape `C<n>` »), puis il se fait rejouer **pour de vrai après le merge et le
déploiement**. Les deux preuves ne se remplacent pas : la première voit le code du
worktree, la seconde voit ce qui tourne réellement.

Vocabulaire, pour qui lit ce fichier pour la première fois :

- **Hermes** : l'automate du poste qui lance les crons (ses jobs sont dans
  `~/.hermes/cron/jobs.json`).
- **gateway** : le processus Hermes qui fait tourner les crons. Il les examine toutes
  les 60 secondes (le **tick**, un battement).
- **systemd** : le gestionnaire de services de Linux ; un **timer** est un
  planificateur systemd.
- **CI** : l'intégration continue, les tests et contrôles que GitHub joue à chaque
  PR. Un workflow planifié (`schedule:`) est une CI qui se lance seule, à heure fixe.
- **worktree** : la copie de travail git, séparée du dépôt principal, où se fait le
  plan. Le code du worktree n'est **pas** celui que Hermes exécute tant que la
  branche n'est pas mergée.

## Au plan : inventorier, puis une étape `C<n>` par cron

L'enquête repère les crons touchés, et le plan leur donne une étape. Les lieux
à regarder :

- les jobs Hermes : `~/.hermes/cron/jobs.json` (champs `id`, `script`, `workdir`,
  `interpreter`, `no_agent`) ;
- les timers systemd : `systemctl list-timers --all`, puis `systemctl cat <unité>` ;
- les workflows planifiés : `grep -rln '^\s*schedule:' .github/workflows/` ;
- les autres planificateurs, quand le dépôt en porte : `crontab -l` et
  `/etc/cron.d/`, `crons` de `vercel.json`, `[triggers] crons` de `wrangler.toml`,
  `cron.schedule` de `pg_cron`, routines et triggers cloud. Leur lancement
  équivalent suit le même principe que ci-dessous : le déclencheur manuel du
  planificateur, ou la commande de la ligne de crontab sous `env -i` et dans le
  répertoire du job ;
- les cousins du cron (section « Les cousins du cron ») : les hooks
  (`hooks/hooks.json` d'un plugin, clé `hooks` de `.claude/settings.json`) et les
  workflows lancés par un événement (`on:` qui porte `push`, `pull_request` ou
  `workflow_run`, sous `.github/workflows/`).

Un cron est **touché** si le plan le **crée**, ou modifie son script, son fichier
de job, son planning, son unité, son workflow, ou ce qu'il lit ou écrit. Un cron
**nouveau** n'a pas d'exécution passée à laquelle se fier : il est touché au plus
haut point. Chaque cron touché reçoit une étape
`C<n>` (`C1`, `C2`…), avec ces lignes :

- **Id** : l'identifiant du job, le nom de l'unité ou du workflow ;
- **Lancement équivalent** : le type de cron (voir plus bas). Le plan écrit la
  règle ; la commande exacte se résout à l'exécution, sur le poste ;
- **Critère de succès** : un code de retour, une ligne attendue sur la sortie, ou
  un effet observable (un fichier produit, un compte) ;
- **Durée maximale** : en secondes, le délai au-delà duquel le lancement est tué et
  l'étape est en échec ;
- **Effets externes tranchés** : ce que le lancement écrit hors du dépôt. Règle
  (question Q2 de Benjamin) : **réel par défaut**, sauf pour un effet irréversible
  (suppression, écriture externe ou en production, publication, dépense). Un effet
  irréversible se tranche **avant `valide`** : mode à blanc existant, ou question à
  Benjamin ;
- **Après le merge** : renvoi au point 4 ter de `remontee-sur-main.md`.

Exemple de forme, avec des noms fictifs :

```
### Étape C1 — Lancer le cron `<id>` à la main
- **Lancement équivalent** : par script Hermes, voir `cron-a-la-main.md`.
- **Critère de succès** : code de retour 0, et la ligne `<texte attendu>` sur la sortie standard.
- **Durée maximale** : 60 s ; au-delà, le lancement est tué et l'étape est en échec.
- **Effets externes tranchés** : réels, écriture réversible dans `<dossier>`.
- **Après le merge** : rejeu réel, point 4 ter de `remontee-sur-main.md`.
```

Le contrôle 13 du filtre (`plan-notion/SKILL.md`, §8) l'exige : **chaque cron
touché a son étape `C<n>`, ou la page dit « Aucun cron touché »**. Un plan qui ne
touche aucun cron l'écrit ainsi, en une ligne.

## Le lancement équivalent, par type de cron

Pourquoi « équivalent » : `hermes cron run` ne lance pas le fichier du worktree. Il
lance le script déployé, au prochain tick. Le lancement à la main reproduit donc,
sur le fichier du worktree, ce que Hermes ou systemd feraient.

### Script Hermes (job qui porte un champ `script`)

- **Fichier** : celui du worktree, pas la copie déployée sous `$HERMES_HOME/scripts/`.
- **Interpréteur** : si le job porte un champ `interpreter` (épinglé par
  `hermes cron edit … --interpreter`), c'est lui. Sinon, c'est celui que Hermes
  résout : `project_python` du dépôt Hermes, dans `cron/scheduler_script.py` (vers
  les lignes 153 à 163), hors Windows. Un `.sh` ou `.bash` se lance sous `bash`.
  **Écart à connaître** : la doc Hermes (`website/docs/user-guide/features/cron.md`,
  ligne 925) dit « l'interpréteur Python courant (`sys.executable`) ». Le code et la
  doc ne disent pas la même chose ; ce fichier suit le code, et la preuve dit quel
  interpréteur a tourné.
- **Répertoire courant** : le `workdir` du job s'il est posé ; sinon le dossier du
  script sous `$HERMES_HOME/scripts` (`~/.hermes/scripts` dans le cas courant), et
  **jamais** le dossier du worktree.
- **Environnement** : `env -i`, qui vide **toutes** les variables, `PATH` et `HOME`
  compris. C'est plus strict que Hermes, qui retire seulement les identifiants des
  fournisseurs. Un script qui réussit ainsi réussira en vrai. Un script qui échoue
  faute d'une variable le dit dans la preuve : c'est le lancement qui est trop
  strict, pas forcément le cron.

Forme de la commande : `cd <workdir> && env -i <interpréteur> <worktree>/…/<fichier>`.
Le lancement n'est pas à blanc si le plan a tranché « réel » : sans effet, rien ne
se prouve.

### Job Hermes sans script (prompt ou skill seulement)

Pas d'équivalent hors du planificateur. Le plan l'écrit : « preuve après
déploiement seulement ». Seul le rejeu du point 4 ter prouve le job.

### Timer systemd

- Lire ce que systemd donne au service : `systemctl show <unité>.service -p User -p WorkingDirectory -p Environment`.
- Lancer le fichier du worktree avec les mêmes valeurs, en attendant la fin :
  `systemd-run --wait -p User=<…> -p WorkingDirectory=<…> -p Environment=<…> <commande>`.
  `--wait` attend la fin du service ; `-p` pose une propriété du service.

### Workflow planifié (GitHub `schedule:`)

- Si Docker tourne (moteur qui lance des programmes dans des boîtes isolées),
  `act` peut rejouer le workflow sur le poste. **Un lancement `act` lance un
  conteneur : c'est une action lourde, le pilote la joue** (`machine-partagee.md`),
  l'`executant` ne la lance pas.
- Sinon, pas de lancement local : la preuve vient après le merge, par
  `gh workflow run`, qui n'accepte que le fichier de la branche par défaut.

## Les cousins du cron : un hook, un workflow sur événement

Même panne que le cron : un code que la session ne voit jamais tourner, dont la
première preuve arrive plus tard (à la session suivante, au vrai merge). Un plan
qui crée ou modifie l'un d'eux lui donne donc aussi une étape `C<n>`, avec les
mêmes lignes (Id, Lancement équivalent, Critère de succès, Durée maximale, Effets
externes tranchés, Après le merge), et la même boucle.

### Hook Claude Code (de plugin, ou de `.claude/settings.json`)

- **Pourquoi** : un hook se charge au démarrage d'une session (ou par
  `/reload-plugins`). La session qui le modifie ne le voit jamais se déclencher, et
  la session suivante découvre l'erreur, ou pire, ne voit rien : un hook qui plante
  laisse souvent passer en silence.
- **Lancement équivalent** : la commande du hook (`hooks/hooks.json`, ou
  `settings.json`), fichier du worktree, avec sur l'entrée standard un JSON du même
  événement (`hook_event_name`, `session_id`, `cwd`, et pour un `PreToolUse` ou un
  `PostToolUse` : `tool_name`, `tool_input`) :
  `echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git commit --no-verify -m x"},"session_id":"essai","cwd":"'"$PWD"'"}' | CLAUDE_PLUGIN_ROOT=<worktree>/plugins/<plugin> python3 <worktree>/plugins/<plugin>/hooks/<script>.py`
- **Critère de succès** : le code de retour (2 bloque, 0 laisse passer) et la
  sortie attendue (message sur la sortie d'erreur, ou JSON sur la sortie
  standard). Au moins deux lancements : un cas que le hook doit attraper, un cas
  qu'il doit laisser passer.
- **Après le merge** : après la mise à jour du poste (point 4 bis de
  `remontee-sur-main.md`), une session neuve, ou `/reload-plugins`, puis un geste
  qui déclenche le hook pour de vrai.

### Workflow GitHub lancé par un événement (`push`, `pull_request`, merge)

- **Pourquoi** : un déploiement au merge ou un `merge-auto` ne tourne qu'au vrai
  événement. Une erreur s'y voit au merge, c'est-à-dire en production.
- **Lancement équivalent** : si Docker tourne, `act <événement> -W
  .github/workflows/<fichier> -e <événement>.json` rejoue le workflow du worktree
  sur le poste, avec un JSON d'événement écrit pour l'étape. **Action lourde : le
  pilote la joue** (`machine-partagee.md`). Un pas qui écrit dehors (déploiement,
  push, commentaire, merge) relève des effets externes tranchés : à blanc
  (`act` pose `ACT=true` : le pas porte `if: ${{ !env.ACT }}`) ou question avant
  `valide`.
- **Sans Docker** : pas de lancement local. `workflow_dispatch` ne sert pas
  avant le merge : GitHub ne déclenche que les workflows présents sur la branche
  par défaut. La preuve vient alors du premier vrai run, et l'étape le dit en une
  ligne : « preuve au premier run seulement ».
- **Après le merge** : le run déclenché par le merge est **regardé**, jamais
  supposé : `gh run list --workflow <fichier> --branch <branche par défaut> -L 1`,
  puis `gh run watch <id> --exit-status` (conclusion `success`).

## La boucle : lancer, constater, corriger, trois tours au plus

Pour une étape `C<n>` :

1. **Lancer et constater** : un `executant` (Haiku, `plans-notion:executant`)
   lance le lancement équivalent et rend la sortie bornée (code de retour, dernières
   lignes, la ligne du critère). **Il ne corrige rien** : c'est la règle de
   l'`executant` devant une preuve rouge.
2. **Critère tenu** : l'étape `C<n>` est faite. La sortie bornée va au journal.
3. **Critère rouge** : le **pilote** (Sonnet) lit la sortie et dit ce qu'il
   comprend. Si la correction tient dans l'étape, elle part en une étape `D<n>`
   (numérotation à part, `decouvertes.md`, §2).
4. **La correction** `D<n>` part à un `executant` **avec `model: "sonnet"` à
   l'appel**. Raison : un diagnostic fin sur un cron qui échoue dépasse Haiku.
   C'est **l'unique cas** où l'appel d'un `executant` porte un `model` ; l'étape
   `C<n>` elle-même, comme les autres, n'en porte aucun. La correction reste dans
   la liste fermée de fichiers de l'étape ; si elle en sort, elle sort de la
   boucle et part en arbitrage, comme une preuve rouge structurante (`etapes.md`).
5. **Relecture** : le `relecteur` relit `D<n>` (`revue.md`).
6. **Relance** : un `executant` Haiku relance le lancement `C<n>`.

Un **tour** = un lancement, un diagnostic, une `D<n>` relue, une relance.
**Trois tours au plus.** Au troisième rouge, le pilote pose la question à Benjamin
(`AskUserQuestion` si l'outil est là, sinon en texte, recommandation en premier) :

- **session avec Benjamin** : l'étape reste ouverte, le reste du plan continue ;
- **session sans humain** (lancée par Hermes, `decouvertes.md`, §3) : l'étape `C<n>`
  et ce qui en dépend sont **gelés**, et la question part dans la rubrique
  « Questions pour Benjamin ».

Si le lancement dure plus longtemps que le délai d'un appel d'outil, le pilote le
met en arrière-plan et le suit avec `Monitor` (l'outil qui suit un processus en
continu). La durée maximale de l'étape reste celle du plan : au-delà, l'étape est
en échec, même en arrière-plan.

## Après le merge : le rejeu réel

Le rejeu se fait après le merge et le déploiement, par le point **4 ter** de
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/remontee-sur-main.md`, avec un geste par type
de cron : `hermes cron run <id>` puis `last_status` pour un job Hermes,
`systemctl start` puis `Result` et `journalctl` pour un timer systemd,
`gh workflow run` puis `gh run watch` pour un workflow `schedule:`, la commande de
la ligne déployée pour une crontab.
Un rejeu rouge ouvre un plan de suite (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md`) ;
il ne défait pas un merge déjà fait.

## Jamais « à la prochaine exécution »

« Le cron tournera cette nuit à 2 h 30 » ou « on verra au prochain passage » n'est
**pas** une preuve, ni dans une étape `C<n>`, ni dans la réponse finale, ni dans le
journal, ni dans la description d'une PR : c'est reporter la première preuve en
production (voir « Pourquoi cette règle »). Trois conséquences :

- une étape `C<n>` n'est faite que sur la **sortie d'un lancement réel**, citée au
  journal. « À vérifier à l'heure prévue » la laisse **ouverte**, jamais faite ;
- si, à l'exécution, on découvre qu'un cron est touché et que le plan n'a pas
  d'étape `C<n>`, le pilote l'ajoute (étape `D<n>`, `decouvertes.md`) avant de
  clôturer, sans attendre une question ;
- si le lancement est réellement impossible (job sans script, workflow sans
  Docker, accès manquant), la réponse finale le dit en clair : **ce qui n'est pas
  prouvé, pourquoi, et la commande exacte du rejeu** (point 4 ter de
  `remontee-sur-main.md`). Elle n'écrit pas « testé » et ne renvoie pas à
  l'horloge.

## Ce que le lancement à la main ne prouve pas

- **L'environnement de la nuit.** L'amorçage Python que Hermes insère avant le
  script (`_POSIX_SCRIPT_BOOTSTRAP`, `cron/scheduler_script.py`) et la liste exacte
  des variables retirées ne sont pas reproduits. Seul le rejeu après merge prouve le
  cron tel qu'il tourne.
- **Un job sans script.** Rien ne se prouve avant le déploiement.
- **Le code déployé.** Avant le merge, le lancement porte sur le worktree : il
  prouve le code du plan, pas ce que Hermes lit aujourd'hui.

La preuve de l'étape `C<n>` le dit en une ligne, au journal, à côté de sa sortie.
