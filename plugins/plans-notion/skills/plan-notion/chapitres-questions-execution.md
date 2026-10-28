# Les chapitres Questions ouvertes, Exécution et Journal d'exécution — détail

Référence de `plan-notion`, lue **avant d'écrire ou de remettre à jour** l'un de ces trois chapitres. Le déroulé et l'ordre des chapitres restent dans `SKILL.md` (§3).

## Sommaire

- Les questions ouvertes
- Le chapitre `La suite`
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

- Des cases à cocher, **toutes laissées vides** (sauf l'exception ci-dessous), la reco marquée `(reco)` en
  premier. **Ne jamais précocher, pas même la reco** : une case cochée par moi
  est indistinguable d'une case cochée par Benjamin à la passe suivante, et fait
  passer une proposition pour une décision. Seule exception : la question née
  verte d'un choix validé, décrite juste après, dont la case est cochée et citée.
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

L'encadré ✅ porte sa ligne `Preuve :` **au moment où la question passe au vert**,
y compris quand la reco s'applique par défaut : elle est prouvée elle aussi. Une
question née verte porte sa preuve de `lecture`, de `commande` ou de `dispense` dès sa création.
Format et types : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`, « La preuve de chaque réponse ».

**La question née verte d'un choix validé.** Un choix que Benjamin valide **en
toutes lettres** dans la session (« oui, on prend X », « je valide l'option B »)
ne reste pas une reco : il s'écrit comme une question née verte, **la case de son
choix cochée**, et sa ligne de preuve cite son message mot pour mot :

`Preuve : dispense — parce que choix de gouvernance de Benjamin, <date> : « <citation> »`

- **Citation exacte, date du message.** Recopiée du fil, sans paraphrase : une
  citation reformulée ne prouve rien. Le brainstorming, à la remise, liste ces
  choix avec leur citation ; c'est la liste à écrire ici.
- **Sans citation, pas de case.** Un « oui » au design ne vaut pas choix validé
  en toutes lettres : c'est l'option écartée, faire valoir ce « oui » pour `valide`.
  Sans ligne citée, la case reste vide et la question reste orange.
- **Une reco non contestée reste orange** tant que la réponse n'est pas écrite,
  sans case cochée (règle de la reco plus haut).
- L'encadré passe au vert avec `(choix validé par Benjamin)` à la place de
  `(reco appliquée par défaut)`, et le H3 passe à `✅ Q<n> — …` dans le même geste.

### Le chapitre `La suite`

`La suite` n'est pas une réserve où l'on range ce qu'on n'a pas envie de faire :
c'est le chapitre de ce que le plan **ne** fait **pas**, et chaque ligne y a une
raison. Un élément qui arrive ici passe d'abord le tri, dans cet ordre, et **la
première réponse qui s'applique décide** :

1. **Déjà porté par un autre plan** (une étape, une question, un plan nommé et lié)
   → il reste là-bas ; `La suite` le cite en une ligne, avec le lien. Un « à
   reprendre dans un plan CI » sans plan nommé n'est pas un report : le plan n'existe
   pas, passer au 3.
2. **Trop gros pour ce plan** — la mesure de `_partage/decouvertes.md` §1 : il revient
   sur une décision tranchée, coûte (argent, quota, plus d'une étape), touche la
   sécurité, est irréversible, ou ne tient pas en une étape → c'est un **plan à part
   entière**. Il se crée en `brouillon` dans la même passe quand ses contours sont
   clairs, sinon il part en question à Benjamin ; `La suite` cite son titre et son
   lien, et **la réponse de la session le dit** (plan créé, ou question posée) : le
   chapitre n'est pas l'endroit où Benjamin l'apprend. Un point qui dépend de la réponse à une question (« si Q3 (b), … ») n'est pas
   un élément de `La suite` : il s'écrit dans l'option de la question.
3. **Sinon** — réversible, hors sécurité, petit (une étape) → il **entre dans le plan** :
   une étape du chapitre `Exécution`, avec tous ses champs, et une retouche datée
   (`_maj AAAA-MM-JJ — ajouté depuis « La suite » parce que …`). La ligne disparaît de
   `La suite` ; la laisser aux deux endroits ferait croire qu'elle est faite et qu'elle
   ne l'est pas.

Restent dans `La suite`, parce qu'aucune étape ne peut les porter : ce qui **attend un
événement** (une mesure à N jours, un merge, une version publiée), écrit avec son
déclencheur et son propriétaire ; ce que **Benjamin a écarté** en toutes lettres, cité
avec sa décision ; et la **dette de carte** (ci-dessus). Une ligne sans déclencheur ni
propriétaire se range donc au 1, au 2 ou au 3, jamais ici. Le chapitre est « Rien. » quand
tout a trouvé sa place.

**À chaque passe**, relire `La suite` avec ce tri : un élément qui a attendu depuis la
passe d'avant entre dans le plan s'il remplit le 3. Sur un plan encore à `brouillon`,
`en revue` ou `valide`, c'est une retouche ordinaire ; sur un plan déjà ouvert à
l'exécution, c'est une découverte comme une autre (`_partage/decouvertes.md` §2 : une
étape `D<n>`).

### Le chapitre `Exécution`

Présent **dès la première version du plan**, jamais repoussé au moment de coder.
C'est là que le plan cesse d'être une intention : si on ne sait pas encore
l'écrire, c'est qu'on ne sait pas encore ce qu'on va faire, et c'est cette
ignorance-là qu'il faut rendre visible.

**En tête du chapitre, avant le tableau, une ligne `Coût estimé : …`.** Elle
recopie les médianes du barème de `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cout-des-plans.md`
pour les types de session que ce plan annonce — plan seul, exécution seule, ou
les deux dans une même session —, avec la date du barème. Les dollars sont
d'équivalent API ; **aucun pourcentage de quota**. Une étape sans médiane mesurée
n'a pas de coût estimé : la ligne le dit, elle n'invente pas de chiffre.

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
pourquoi`, ou `aucun — <raison>`. **Le défaut est `aucun — <raison>`** : la fumée (la
tête seule, un passage, quelques dollars) ne se joue que si Benjamin la demande dans son
message courant ; la session pose alors le label `fumee`, la PR s'ouvre en brouillon puis
passe prête, et elle ne pose jamais ce label de sa propre initiative. **Le plan ne
propose jamais de lui-même des catégories, un A/B, un banc `aa` ni la mesure d'un
plancher** : la ligne ne porte des catégories ou `tout` que si Benjamin le demande. Une
catégorie neuve s'écrit sans plancher : la fumée l'écarte, nommée et non jugée, jusqu'à
ce que Benjamin décide de la mesurer. Si des catégories sont demandées, leur coût est
annoncé dans la ligne avant de poser le label. « Tout » est demander le label `evals`
pour tout le banc ; « aucun » ne le demande pas. La CI refuse une sélection qui ne
couvre pas un skill touché, et joue tout le banc pour `_partage/`, les hooks ou le banc
lui-même. Coûts : fiche `claude plugin eval` de
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`.

**Une étape = un titre H3** : `Étape 1 — Titre court de l'étape`. Comme pour les
questions, c'est le H3 qui met l'étape dans la table des matières et permet d'y
sauter directement ; une simple liste numérotée n'y apparaît pas. La numérotation
vit dans le titre. Si une passe fusionne ou supprime des étapes, renuméroter les
H3 pour que le sommaire reste une suite sans trou.

Sous chaque titre, le contenu de l'étape :

- **Choix d'architecture** retenu — et celui qu'on écarte, avec la raison.
- **Fichiers touchés**, chemin par chemin, en distinguant créé / modifié / supprimé.
- **Docs relues** — les documents du dépôt qui citent ce que l'étape touche
  (`fichier:ligne`, relevés par le geste « lecteurs documentaires » de
  `agents/enqueteur.md`, geste 9). Une doc qui deviendra fausse après l'étape passe
  aussi dans « Fichiers touchés », pour être corrigée dans la même étape. « — » si
  aucune doc ne cite ce que l'étape touche.
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
- **Interfaces** : ce que l'étape consomme et ce qu'elle produit, avec les
  signatures exactes — nom de fonction et arguments, type de retour, clé de
  config, format de fichier. Ex. : `resume(ligne: LigneFacture, locale: str) -> str`.
  L'exécutant ne voit que son étape : une interface qu'elle ne nomme pas, il la
  devine. **Facultatif** : « — » (ou ligne omise) quand l'étape ne touche aucun
  code partagé (prose, doc, config isolée). Idée reprise de `obra/superpowers`
  (skill `writing-plans`, licence MIT).
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
  Le tri (retouche datée, ou question à Benjamin) suit
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md` : ce fichier dit quand une
  découverte est une question plutôt qu'une retouche directe du chapitre.

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
