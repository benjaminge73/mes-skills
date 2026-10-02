# Ouvrir l'exécution — le détail du §2

Fichier de référence de `executer-plan-notion` : `SKILL.md` §2 dit **quand** le
lire (à l'ouverture, avant la première étape). Le détail vit ici.

Sommaire :

- Remettre le chapitre `Exécution` à jour — toujours
- Puis, dans le même tour : maquette, questions orange, `Statut`, worktree,
  relevé de la CI, vagues
- Une branche, aucune PR par défaut

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

Cette passe **met le plan à jour, elle ne le redessine pas**. Si une réponse remet
en cause l'approche elle-même — pas une étape, l'approche — ce n'est plus une mise
à jour mais une nouvelle passe de conception : le dire, repasser par
`plan-notion`, et ne rien coder en attendant.

Puis, dans le même tour, avant la première étape :

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
- `Statut` = `en cours`, propriété `Branche` renseignée.
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

  Trois réponses à noter dans l'entrée `Ouverture` du journal (§4), parce
  qu'elles commandent la suite : **un `push` sur une branche autre que `main`
  lance-t-il un run ?** (si oui, la branche ne se pousse qu'à la clôture, §6 ;
  sinon, elle se pousse après chaque étape, §3) ; **le dépôt a-t-il des tests
  e2e ?** (si oui, ils passent en local à la clôture, §6) ; **que fait ce dépôt
  du label `review-required` ?** — `gh label list` et `grep -rn 'review-required'
  .github/workflows/`, parce que son effet change de signe d'un dépôt à l'autre
  et qu'il n'existe pas partout (§6) ;
  **un job merge-t-il tout seul les PR vertes ?** (si oui, ouvrir la PR, c'est
  remonter sur `main` — sur `vahiny`, `review-required` commande la suite
  complète de tests puis, tout vert, le merge par la CI : sans lui, ce dépôt ne
  joue que les tests unitaires).

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

**Par défaut, un plan = une seule branche, et aucune PR tant que Benjamin ne la
demande pas** (§3, §6). Les étapes sont des **commits** sur la branche du plan,
pas des PR, et l'exécution **s'arrête à la branche** : travail complet, suite
complète jouée en local, page à `a merger`. La raison est comptable : chaque PR
déclenche un run GitHub Actions complet — tests, build, e2e sur runner — et le
quota mensuel d'Actions s'y consumait. Même la PR unique de clôture ne
s'ouvre pas d'elle-même — la remontée vers `main` est un geste vers
l'extérieur, et il n'a lieu que sur demande explicite de Benjamin (§6). La CI ne
tourne donc **au plus qu'une fois par plan**, sur la PR qu'il demande ; en
cours de route comme à la clôture, la preuve est **locale** (§3, §6). Ce qui ne
change pas : `main` ne bouge pas de toute l'exécution, et la branche du plan
porte à tout moment l'état complet de ce qui est livré. Une autre organisation —
une PR par étape, plusieurs branches — ne se fait que si Benjamin la demande.

Une session peut aussi porter **plusieurs plans** à la fois : tout ce qui
précède vaut alors pour chacun, et la section « Plusieurs plans », plus bas,
dit ce qui s'y ajoute.
