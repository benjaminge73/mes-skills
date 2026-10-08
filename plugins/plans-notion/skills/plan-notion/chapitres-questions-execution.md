# Les chapitres Questions ouvertes, Exécution et Journal d'exécution — détail

Référence de `plan-notion`, lue **avant d'écrire ou de remettre à jour** l'un de ces trois chapitres. Le déroulé et l'ordre des chapitres restent dans `SKILL.md` (§3).

## Sommaire

- Les questions ouvertes
- Le chapitre `Exécution`
- Le `Journal d'exécution`

### Les questions ouvertes

**Chaque question commence par un titre H3**, juste au-dessus de son encadré :
`Q1 — Titre court de la question`. C'est ce titre qui la fait apparaître dans la
table des matières ; l'encadré seul y est invisible. L'état se lit aussi depuis le
sommaire grâce à l'emoji en tête du titre : `🧭 Q1 — …` tant qu'elle est ouverte,
`✅ Q1 — …` une fois tranchée. Quand une question passe au vert, **mettre à jour
le H3 en même temps que l'encadré** — un sommaire qui dit 🧭 pour une question
tranchée ment.

Sous ce titre, un encadré par question, et **la couleur du cadre dit l'état de la
question** :

- 🧭 **fond orange = ouverte.** Elle le reste tant que la réponse n'est pas
  *écrite dans la page* — avoir une intuition sur la réponse ne suffit pas.
- ✅ **fond vert = tranchée.** La réponse est recopiée en gras dans le titre de
  l'encadré, pour se lire sans déplier.

Une reco non contestée s'applique par défaut (voir plus bas), et c'est **au moment
où on l'applique** que l'encadré passe au vert, avec la mention
`(reco appliquée par défaut)`. Avant ce moment, la question n'a pas de réponse et
le cadre reste orange : un vert posé d'avance ferait passer une supposition pour
un accord.

Contenu de l'encadré :

- Des cases à cocher, **toutes laissées vides**, la reco marquée `(reco)` en
  premier. **Ne jamais précocher, pas même la reco** : une case cochée par moi
  est indistinguable d'une case cochée par Benjamin à la passe suivante, et fait
  passer une proposition pour une décision.
- Dernière case toujours libre : `Autre / complément →`.
- **Sans réponse, la reco s'applique.** Benjamin ne répond qu'aux désaccords.
- **À chaque passe, relire le texte EN FACE de chaque case cochée**, et pas
  seulement quelles cases le sont — en particulier ce qui suit
  `Autre / complément →`. Benjamin répond dans le corps de la page aussi souvent
  qu'en commentaire ; `get-comments` ne le montre pas. Une reco cochée *et* un
  `Autre` rempli veut dire « oui, mais » — les deux comptent.
- **Une question ne s'écrit qu'après l'enquête**, et pas avant (section
  « L'enquête avant les options », dans `enquete.md`). Une contrainte mesurée vaut mieux qu'une option
  plausible : la moitié des décisions de ce dispositif ont changé après
  vérification. Et si l'enquête donne la réponse, la question naît **verte** — on
  n'ouvre pas une question pour faire joli dans le sommaire.

### Le chapitre `Exécution`

Présent **dès la première version du plan**, jamais repoussé au moment de coder.
C'est là que le plan cesse d'être une intention : si on ne sait pas encore
l'écrire, c'est qu'on ne sait pas encore ce qu'on va faire, et c'est cette
ignorance-là qu'il faut rendre visible.

**En tête du chapitre, un tableau `Étape · Fichiers touchés · Dépend de ·
Vague · Relecture`**, une ligne par étape — le pre-flight scan du chapitre : il donne
d'un coup d'œil ce qui se recoupe, avant même d'entrer dans le détail de
chaque étape. La colonne `Vague` est **proposée** ici : deux étapes vont
dans la même vague si elles ne partagent aucun fichier, si aucune ne dépend
de l'autre, et si aucun fichier partagé (config, README, `CLAUDE.md`, test de
décompte) n'est touché par les deux. Mais c'est `executer-plan-notion` qui la
**calcule** à l'ouverture de l'exécution : le plan **déclare**, il
n'**ordonnance** pas — calculer les vagues ici ferait mentir un plan qui
change d'ordre en route sans que le tableau ne le sache.

La colonne `Relecture` dit, étape par étape, comment le relecteur la voit :
`étape` (relue seule, dès qu'elle est commitée) pour ce qui mérite un regard
à part — une migration, un contrat d'API, un schéma —, `lot` (relue d'un seul
coup avec les étapes `lot` consécutives) pour ce qui est petit ou sans
risque, comme dix lignes de doc. Un plan écrit sans la colonne se lit `étape`
partout. Les deux régimes, la définition du lot et la décision de Benjamin du
2026-09-30 (Q6, qui remplace celle du 2026-09-23) sont dans
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`.

**Si le plan modifie un plugin d'un dépôt qui a un banc d'évals par catégorie** (un
`evals/categories.json`), le chapitre porte une ligne `Évals à jouer : <catégories> —
pourquoi`, ou `aucun — <raison>`. **Le défaut est `aucun — la fumée suffit`** : la
fumée (la tête seule, un passage, quelques dollars) se joue sans label. Des catégories,
donc le label `evals`, se demandent seulement pour **un changement de règle de
comportement** dans un skill, un agent ou un `_partage/`, ou pour **un changement de
modèle ou d'effort d'un agent** : là, l'A/B est le seul juge d'un recul fin. Son coût
est annoncé dans la ligne avant de poser le label. « Tout » est demander le label
`evals` pour tout le banc ; « aucun » ne le demande pas. La CI refuse une sélection qui
ne couvre pas un skill touché, et joue tout le banc pour `_partage/`, les hooks ou le
banc lui-même. Coûts : fiche `claude plugin eval` de
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`.

**Une étape = un titre H3** : `Étape 1 — Titre court de l'étape`. Comme pour les
questions, c'est le H3 qui met l'étape dans la table des matières et permet d'y
sauter directement ; une simple liste numérotée n'y apparaît pas. La numérotation
vit dans le titre. Si une passe fusionne ou supprime des étapes, renuméroter les
H3 pour que le sommaire reste une suite sans trou.

Sous chaque titre, le contenu de l'étape :

- **Choix d'architecture** retenu — et celui qu'on écarte, avec la raison.
- **Fichiers touchés**, chemin par chemin, en distinguant créé / modifié / supprimé.
- **Dépend de** — les étapes et les questions dont l'étape a besoin, « — » si
  aucune. C'est cette ligne, reprise dans le tableau de tête de chapitre, que
  `executer-plan-notion` lit pour calculer les vagues d'exécution.
- **Relecture** — `étape` ou `lot` (`_partage/revue.md`) ; reprise dans la
  dernière colonne du tableau de tête de chapitre.
- **Taille** — le nombre de fichiers touchés. Plus de cinq → découper l'étape :
  l'enquête montre que tous les conflits d'exécution observés viennent d'un
  fichier partagé non repéré, et une étape large le cache d'autant mieux
  qu'elle est large.
- **Blocs touchés** — les nœuds de la carte du dépôt (chapitre `Cartes`) que
  l'étape modifie. « Aucun bloc de la carte » est une réponse valable, et il
  faut l'écrire plutôt que laisser la ligne vide.
- **Impact fonctionnel** : ce que l'utilisateur voit changer. « Rien » est une
  réponse valable, et il faut l'écrire plutôt que laisser la ligne vide. Toute
  autre réponse exige une maquette et dit **quelle partie** de la maquette
  l'étape réalise (chapitre `Maquette`).
- **Impact technique** : migrations, dépendances, variables d'environnement,
  contrats d'API, effet sur les tests existants.
- **Preuve de fin** : la commande ou l'observation qui dit que l'étape est faite.
- **Test attendu** — pour une étape qui écrit du code : la panne que le test
  attrapera, le comportement cassé qu'il doit voir rouge avant d'écrire le
  code. Cette ligne est le budget de tests : un test par panne nommée.
  « — » si l'étape n'écrit pas de test.

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/bons-tests.md`

Ce chapitre **bouge à chaque passe**, pour deux raisons distinctes :

- une question tranchée peut supprimer une étape, en fusionner deux, ou en
  retourner une ;
- une investigation peut découvrir ce que le plan ignorait — un appelant oublié,
  une contrainte du framework, un fichier généré. **Ce qui est découvert
  s'écrit**, avec sa conséquence sur les étapes, même si personne ne l'a demandé.
  Une découverte gardée en tête disparaît au compactage du contexte.

Toute modification d'une étape déjà écrite se **date** en fin d'entrée :
`_maj 2026-08-17 — étapes 3 et 4 fusionnées, la réponse à Q2 supprime le cache._`
Sans cette trace, on ne distingue plus ce qui a été décidé de ce qui a dérivé.

### Le `Journal d'exécution`

Il se remplit à l'exécution, mais **sa structure est celle-ci, et elle vaut aussi
bien quand c'est `executer-plan-notion` qui écrit que quand une passe de plan
vient relire** :

**Une entrée = un titre H3**, repris mot pour mot du chapitre `Exécution` :
`Étape 1 — Titre court de l'étape`. Sans ce titre, l'entrée n'existe pas dans la
table des matières — Notion n'y met que les *headings* — et le journal d'un plan
de dix étapes devient un mur qu'on fait défiler pour retrouver ce qui s'est passé
à l'étape 3. Les entrées hors étape prennent le même traitement : `Ouverture` au
démarrage de l'exécution, `État final` à la clôture.

Les titres du journal **répondent** à ceux du chapitre `Exécution` : même
numéro, même libellé. Le sommaire met alors le prévu et le réalisé côte à côte, et
l'écart entre les deux se voit sans ouvrir la page.

**Un journal déjà commencé sans titres se chapitre à la passe suivante**, avant
d'y ajouter quoi que ce soit : découper le texte existant par étape, poser les H3
au-dessus, **sans reformuler une seule ligne de ce qui est écrit** (§4). Un
journal à moitié chapitré est pire qu'un journal plat — le sommaire annonce alors
une complétude qu'il n'a pas.
