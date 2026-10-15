# Ouvrir l'exécution — le détail du §2

Fichier de référence de `executer-plan-notion` : `SKILL.md` §2 dit **quand** le
lire (à l'ouverture, avant la première étape). Le détail vit ici.

Sommaire :

- Remettre le chapitre `Exécution` à jour — toujours
- La porte des preuves, avant — chaque étape a sa preuve de fin
- Puis, dans le même tour : maquette, questions orange, worktree, relevé de la
  CI, vagues, pilote
- La porte du `pret` : l'entrée `Ouverture`, le script, puis `en cours`
- Une branche, la PR à la clôture

### Remettre le chapitre `Exécution` à jour — toujours

**Le chapitre `Exécution` est presque toujours en retard d'un tour.** Benjamin
répond aux questions dans la page, coche des cases, écrit après
`Autre / complément →`, laisse un commentaire, passe `Statut` à `valide` et
enchaîne directement sur ce skill — **sans repasser par `plan-notion`**. Rien n'a
donc répercuté ses dernières réponses dans les étapes. Coder sur ce chapitre-là,
c'est exécuter le plan d'avant ses réponses, et le découvrir trois étapes plus
loin.

Donc, **avant la première étape, sans exception** — même si le plan a l'air à
jour, même s'il a été écrit dans la même session :

1. Reprendre le relevé du §1 : chaque case cochée, chaque texte libre, chaque fil
   non résolu, chaque commentaire de la dernière passe.
2. **Confronter chaque réponse au chapitre `Exécution`, étape par étape.** Une
   réponse peut supprimer une étape, en fusionner deux, changer la liste des
   fichiers, retourner un choix d'architecture — ou ne rien changer du tout.
3. **Écrire ce qui change**, en édition ciblée (§5), et **dater** chaque
   correction : `_maj 2026-08-21 — Q3 tranchée : l'étape 4 tombe, le cache est
   fait côté serveur._` Renuméroter les H3 si des étapes disparaissent, pour que
   le sommaire reste une suite sans trou.
4. **Une réponse qui ne change rien s'écrit quand même**, en une ligne sous
   l'étape concernée : `_Q2 confirme l'approche, étape inchangée._` Sans ça, on ne
   distingue plus une réponse prise en compte d'une réponse oubliée.
5. **Relire le chapitre entier** une fois les corrections posées. Il doit se tenir
   seul, sans avoir à remonter aux questions pour le comprendre : c'est lui, et
   lui seul, qui part dans les briefs des sous-agents (§3), et un sous-agent n'a
   pas la page.

**Une découverte faite à l'ouverture** — en relisant le plan, ou à la répétition à
blanc (`_partage/poc.md`) — passe par le tri de
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md` **avant la première étape** :
question à Benjamin, ou correction datée du chapitre `Exécution`. Ce n'est pas encore
une étape `D`, rien n'a été exécuté.

Cette passe **met le plan à jour, elle ne le redessine pas**. Si une réponse remet
en cause l'approche elle-même — pas une étape, l'approche — ce n'est plus une mise
à jour mais une nouvelle passe de conception : le dire, repasser par
`plan-notion`, et ne rien coder en attendant.

**La porte des preuves, avant.** Une étape sans preuve de fin ne se code pas :
on ne saurait pas dire comment on prouvera qu'elle est faite. Une fois la
remise à jour écrite et relue, le contrôle se joue par script, sur le miroir
local de la page :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/preuves-des-etapes.py" <page.md> --avant
```

- **Code 0** : `avant : <n> étape(s), toutes ont une preuve de fin`. On
  commence la première étape.
- **Code 1** : une ligne par étape sans `**Preuve de fin**` non vide, ou
  écrite deux fois dans le chapitre. Une coquille (« — », « aucune », « à
  définir », « à voir ») compte comme absence. On écrit la preuve dans le
  chapitre, **sur la puce `- **Preuve de fin** : …` de l'étape** (la forme que
  le script lit : une ligne `_maj …_` seule ne compte pas), et on **date** la
  correction par une ligne `_maj <date> — preuve de fin de l'étape N écrite._`
  à côté. On rejoue jusqu'au code 0.
- **Code 2** : page, chapitre `Exécution` ou étape introuvable. On ne
  commence pas, et on le dit à Benjamin.

Le script ne juge pas la preuve : il vérifie qu'elle est écrite. C'est le
pilote qui la jouera (`SKILL.md` §3).

Puis, dans le même tour, avant la première étape (`Statut` reste `valide` tant
que la porte du `pret`, plus bas, n'est pas franchie) :

- **Vérifier le chapitre `Maquette`.** Si une étape au moins a un
  `Impact fonctionnel` autre que « Rien », le chapitre doit porter une
  maquette — ou une dispense dont la raison tient (`plan-notion`, §3). Sinon,
  **s'arrêter et le dire**, sans coder et sans fabriquer la maquette ici :
  dessiner l'écran est une décision que Benjamin doit voir avant qu'on code,
  et elle revient à une passe de `plan-notion`. Une seule sortie sans cette
  passe : Benjamin dit, dans son message, d'y aller sans maquette — ses mots
  se recopient alors en dispense datée dans le chapitre. Maquette présente :
  la relire une fois dans le miroir local, par le `file_upload_id` de sa
  légende. Le geste, et ce qu'on fait s'il échoue, sont dans
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md`, section
  « À l'exécution ».
- **Les questions restées orange passent au vert**, réponse recopiée en gras dans
  le titre de l'encadré, avec la mention `(reco appliquée par défaut)`. C'est le
  moment précis où l'absence de réponse devient une décision. Si ça reste
  implicite, plus personne ne saura ensuite distinguer ce qui a été choisi par
  accord de ce qui a été choisi faute de réponse.
- Créer **la** branche du plan **dans un worktree**, jamais dans le checkout
  principal : nom `type/thème-en-kebab` (`feat/`, `fix/`, `chore/`, `docs/`,
  `refactor/`), nommée d'après le sujet du plan et **dérivée de `main` à
  jour**. Jamais de travail sur `main`.

  ```bash
  mkdir -p ~/repos/worktrees/<repo>
  git worktree add ~/repos/worktrees/<repo>/<branche-kebab> -b <branche> origin/main
  ```

  Le checkout principal du dépôt peut être occupé par une autre session au
  même moment ; y créer la branche du plan directement, c'est risquer que les
  deux modifient le même répertoire sans le savoir — la raison même de la règle
  globale `CLAUDE.md` sur les worktrees, qui entre ici dans le skill qui ouvre
  les branches. Toute la suite de l'exécution (§3 et suivants) se joue dans ce
  worktree ; il est retiré à la clôture (§6), pas avant.
- **Relever ce qui déclenche la CI du dépôt**, une fois pour tout le plan :

  ```bash
  grep -n -A6 '^on:' .github/workflows/*.yml     # push ? pull_request ? sur quelles branches ?
  grep -ln 'pr merge' .github/workflows/*.yml     # un job merge-t-il seul les PR vertes ?
  grep -rli 'e2e\|playwright\|cypress' .github/workflows/ package.json pyproject.toml 2>/dev/null  # des e2e ?
  ```

  Quatre réponses à noter dans l'entrée `Ouverture` du journal (§4), parce
  qu'elles commandent la suite : **un `push` sur une branche autre que `main`
  lance-t-il un run ?** (si oui, la branche ne se pousse qu'à la clôture, §6 ;
  sinon, elle se pousse après chaque étape, §3) ; **le dépôt a-t-il des tests
  e2e ?** (si oui, ils passent en local à la clôture, §6 ; la PR de clôture ne
  les rejoue en CI que là où le label `review-required` les commande) ; **que
  fait ce dépôt du label `review-required` ?** — `gh label list` et `grep -rn
  'review-required' .github/workflows/`, parce que son effet change de signe
  d'un dépôt à l'autre et qu'il n'existe pas partout (§6) ;
  **un job merge-t-il tout seul les PR vertes ?** (si oui, la PR de clôture
  déclenche un run, puis le merge par la CI quand il est vert : la clôture
  remonte donc le plan sur `main` sans autre geste, et Benjamin le sait déjà
  par la règle. Sur `micro-trading`, ce merge déploie. Sur `vahiny`,
  `review-required` commande la suite complète avant le merge : sans lui, ce
  dépôt ne joue que les tests unitaires.)

- **Calculer les vagues**, une fois pour tout le plan : lire le tableau de
  chevauchement du chapitre `Exécution` (`Étape · Fichiers touchés · Dépend de
  · Vague · Relecture`) et déterminer quelles étapes peuvent tourner en parallèle, et
  lesquelles se regroupent dans un seul sous-agent. Le calcul se joue par
  script, qui lit la page (miroir local, sortie de `notion-fetch`) :

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/vagues.py" <page.md>             # une ligne par vague
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/vagues.py" <page.md> --comparer  # code 1 si la colonne « Vague » diffère du calcul
  ```

  La règle derrière le script, l'isolation par worktree et le report sur la
  branche du plan vivent dans un fichier partagé :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`

  Le résultat — la liste des vagues, une ligne par vague — s'ajoute à l'entrée
  `Ouverture` du journal (§4), à côté des trois réponses sur la CI ci-dessus :
  les deux relevés commandent la suite de la même façon, et se lisent
  ensemble.

### La porte du `pret` — la préparation se prouve avant `en cours`

`valide` dit que Benjamin a accepté le plan ; il ne dit pas que la session a fait
ce qu'il faut pour l'exécuter sans surprise. **`pret` le dit** : la préparation de
ce fichier est faite, et chaque geste a laissé sa trace. Parcours d'un plan :
`valide` → préparation → `pret` → `en cours` → `a merger` → `execute`. Une session
qui reçoit un « go » sur une page `valide` prépare d'abord ; elle ne saute pas à
la première étape, et le « go » ne remplace pas la porte.

**1. Écrire l'entrée `Ouverture`** du `Journal d'exécution` (H3 `Ouverture`),
dans la page et dans le miroir local, une puce à clé en gras par geste. Les neuf
clés sont obligatoires, dans cet ordre ; une valeur « — », « aucune », « à voir »
ne compte pas, et `sans objet — <raison>` est recevable, la raison en plus :

```
### Ouverture

- **Relecture** : chapitre `Exécution` relu le 2026-10-15 ; Q3 et Q5 reprises (étapes 2 et 4), le reste « inchangé »
- **Questions** : Q1 à Q6 vertes, 6 sur 6 ; 2 `(reco appliquée par défaut)`
- **Preuves** : `preuves-des-etapes.py --avant` code 0 ; `verifier-preuves.py <miroir> --depot <dépôt> --transcripts` code 0
- **Répétition** : « État de départ » présent dans `Contraintes techniques vérifiées` (POC compris), `main` inchangé depuis sa date
- **Maquette** : sans objet — aucune étape à impact fonctionnel
- **CI** : `push` sans run hors `main` ; pas d'e2e ; `review-required` sans effet ; `merge-auto` actif
- **Vagues** : vague 1 : étapes 1 et 2 ; vague 2 : étape 3
- **Pilote** : Sonnet 5.5, high
- **Branche** : `feat/le-theme`, worktree `~/repos/worktrees/<repo>/feat-le-theme`
```

Ce que chaque puce porte :

- **Relecture** : la remise à jour du chapitre `Exécution` (début de ce fichier),
  datée, avec ce qu'elle a changé ou « inchangé ».
- **Questions** : toutes vertes, décompte recopié de la page. Une question restée
  🧭 se tranche (reco appliquée par défaut) avant `pret`, jamais après.
- **Preuves** : les codes de sortie de la porte des preuves ci-dessus et de
  `verifier-preuves.py` (la preuve de chaque réponse, POC compris) ; un écart
  se corrige, ou se justifie par une dispense motivée dans la page.
- **Répétition** : l'« État de départ » de `poc.md` existe dans la page. Si `main`
  a bougé depuis sa date, on rejoue les gestes 1 et 2 de `poc.md` dans un
  worktree détaché avant de l'écrire ; un plan sans cette section n'a pas eu sa
  répétition, et on le dit plutôt que d'écrire `sans objet`.
- **Maquette**, **CI**, **Vagues**, **Pilote**, **Branche** : le résultat des
  puces correspondantes ci-dessus.

**2. Jouer la porte :**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/preparation-prete.py" <page.md>
```

- **Code 0** : `prêt : …`. `Statut` = `pret`, `Branche` renseignée, en une
  écriture Notion ; relire le miroir pour confirmer.
- **Code 1** : un défaut par ligne (question encore ouverte, étape sans preuve de
  fin, puce absente ou vide). On fait le geste manquant, on écrit sa puce, on
  rejoue. **Aucune étape ne démarre sur un code 1**, et `pret` ne se pose pas
  « en attendant ».
- **Code 2** : page, chapitre ou journal introuvable. On le dit à Benjamin, sans
  rien commencer.

Le script vérifie que chaque geste a laissé sa trace, pas que le geste est juste :
la justesse reste à la relecture du pilote.

**3. `Statut` = `en cours`** se pose sur la page `pret`, juste avant la première
étape, dans le même tour si rien ne l'arrête. Une session qui s'arrête entre les
deux laisse la page à `pret` ; la suivante passe par la ligne `pret` de la porte
d'entrée (`SKILL.md`) : relecture de la page, retour à `valide` si Benjamin y a
répondu depuis, sinon `en cours`. Reprise d'un plan déjà `en cours` : inchangée.

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
précède vaut alors pour chacun, et la section « Plusieurs plans », plus bas,
dit ce qui s'y ajoute.
