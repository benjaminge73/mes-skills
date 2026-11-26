# Remettre le chapitre `Exécution` à jour — toujours

Geste du pilote, ou du `preparateur` quand il le délègue (« Qui prépare », `ouverture.md`) :
ce fichier se lit en entier avant la première étape, à la suite de `ouverture.md`. Les `§N`
renvoient à `SKILL.md`, comme dans `ouverture.md`.

**Le chapitre `Exécution` est presque toujours en retard d'un tour.** Benjamin
répond aux questions dans la page, coche des cases, écrit après
`Autre / complément →`, laisse un commentaire, passe `Statut` à `valide` et
enchaîne directement sur ce skill — **sans repasser par `plan-notion`**. Rien n'a
donc répercuté ses dernières réponses dans les étapes. Coder sur ce chapitre-là,
c'est exécuter le plan d'avant ses réponses, et le découvrir trois étapes plus
loin.

Donc, **avant la première étape, sans exception** — même si le plan a l'air à
jour, même s'il a été écrit dans la même session :

0. **Une case cochée vaut décision**, même hors reco : elle s'applique sans confirmation
   (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/pilotable-par-hal.md`, §1). À partir de `valide`,
   la session ne pose aucune question par `AskUserQuestion` (§2 du même fichier : question en
   texte, recopiée dans la page, fin de tour), et pose `Session` et `Machine` sur la page dès
   le début de la préparation pour que Hal la trouve.
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
en cause l'approche elle-même, ce n'est plus une mise
à jour mais une nouvelle passe de conception : le dire, repasser par
`plan-notion`, et ne rien coder en attendant.

**La porte des preuves, avant.** Une étape sans preuve de fin ne se code pas :
on ne saurait pas la prouver. Une fois la
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
que la porte du `pret` (`ouverture.md`, « La porte du `pret` ») n'est pas franchie) :

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
  git fetch origin <principale>   # sinon origin/<principale> peut être une référence périmée
  git worktree add ~/repos/worktrees/<repo>/<branche-kebab> -b <branche> origin/main
  ```

  Le checkout principal peut être occupé par une autre session : y créer la branche,
  c'est risquer que deux sessions modifient le même répertoire, la raison de la règle
  `CLAUDE.md` sur les worktrees. Toute la suite de l'exécution (§3 et suivants) se joue dans ce
  worktree ; il est retiré à la clôture (§6), pas avant. Reprise sur un worktree
  qui existe déjà : le rendre frais avant de reprendre
  (`_partage/fraicheur-du-depot.md`, conflit ou arbre sale : s'arrêter et le dire).
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
  remonte donc le plan sur `main` sans autre geste. Sur `micro-trading`, ce merge déploie. Sur `vahiny`,
  `review-required` commande la suite complète avant le merge : sans lui, ce
  dépôt ne joue que les tests unitaires.)

- **Calculer les vagues**, une fois pour tout le plan : lire le tableau de
  chevauchement du chapitre `Exécution` (`Étape · Fichiers touchés · Dépend de
  · Vague · Relecture`) et déterminer quelles étapes peuvent tourner en parallèle, et
  lesquelles se regroupent dans un seul sous-agent. Le calcul se joue par
  script, sur le miroir local de la page :

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/vagues.py" <page.md>             # une ligne par vague
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/vagues.py" <page.md> --comparer  # code 1 si la colonne « Vague » diffère du calcul
  ```

  La règle derrière le script, l'isolation par worktree et le report sur la
  branche du plan vivent dans un fichier partagé :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`

  Une étape dont `Relecture` vaut `étape` a son worktree et sa branche d'étape
  même seule dans sa vague (`vagues.md`, « Une étape relue seule ») : le calcul
  ci-dessus ne change pas pour elle.

  Le résultat (la liste des vagues) s'ajoute à l'entrée `Ouverture` du journal (§4), à côté des réponses
  sur la CI :
  les deux relevés commandent la suite de la même façon, et se lisent
  ensemble.
