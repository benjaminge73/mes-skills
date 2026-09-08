---
name: plan-notion
description: Écrit et fait évoluer un plan de travail dans Notion au lieu du chat. À utiliser dès que Benjamin demande un plan, une approche, une architecture, une découpe, « comment tu ferais », « par où on commence », « avant de coder », ou toute réflexion préalable à une implémentation. S'applique dans tous les modes de l'app sauf le mode plan natif de Claude Code, où il faut se taire et laisser le plan natif faire foi. Couvre aussi les passes suivantes (commentaires Notion non résolus, réponses dans les fils, mise à jour du plan et de son chapitre d'exécution). L'implémentation une fois le plan validé relève du skill executer-plan-notion.
---

# Plan dans Notion

## Deux règles qui priment sur tout

### 1. Ne jamais cocher une case à la place de Benjamin

**Aucune case n'est cochée par moi. Jamais. Pas même la reco.** Une case cochée
est une décision de Benjamin, et c'est souvent la *seule* trace de cette
décision — le fil de discussion ne la contient pas, et il disparaît au
compactage.

Une case que j'ai cochée est **indistinguable** d'une case qu'il a cochée. Elle
fait donc passer ma proposition pour son accord, définitivement : à la passe
suivante, plus personne — moi le premier — ne peut savoir qui a décidé. C'est le
seul dégât de ce dispositif qui ne se répare pas, puisqu'on ne sait même pas
qu'il a eu lieu.

Trois formes du même geste, toutes interdites :
- cocher la reco « puisqu'elle s'appliquera de toute façon » — non : **sans
  réponse, la reco s'applique sans être cochée** (§3) ;
- cocher pour « refléter » une réponse donnée dans le chat ou en commentaire —
  la réponse se recopie dans le texte de l'encadré, pas dans une case ;
- recréer un encadré en y remettant des `- [x]` **au-delà** de ce que le relevé
  préalable portait (§4).

Le seul `- [x]` que j'écris est celui que je **restitue** lors d'une refonte,
relevé en main, à l'identique de ce qui était coché avant. Aucun autre.

⚠️ Cette règle est répétée au §3 avec le détail des encadrés. Elle est ici parce
qu'elle a été enfouie et oubliée — Benjamin l'a signalé le 2026-08-26.

### 2. Ne rien coder avant `valide`

**Tant qu'un plan n'est pas au statut `valide`, ne rien coder** : aucune écriture
de fichier, aucun commit, aucun sous-agent d'implémentation. Sauf demande explicite
dans le message même. Dans le doute, demander plutôt que supposer.

Cette règle s'oublie d'une seule façon — en étant absorbé par la conception, au
point de commencer « juste un fichier » pour vérifier une hypothèse. Vérifier en
lisant est permis ; vérifier en écrivant ne l'est pas.

Une fois le statut à `valide`, l'implémentation ne se fait pas ici : elle relève du
skill **`executer-plan-notion`** (§8).

⚠️ Les valeurs réelles de la propriété `Statut` sont **sans accents** :
`brouillon`, `en revue`, `valide`, `en cours`, `a merger`, `execute`, `archive`.
Écrire `exécuté` fait échouer l'appel avec une `validation_error`.

## Quand s'appliquer, quand se taire

Ce skill s'applique **dans tous les modes de l'app sauf un**. Mode par défaut,
`acceptEdits`, `bypassPermissions` : toute demande de plan, d'approche,
d'architecture ou de découpe part dans Notion.

**La seule exception est le mode plan natif de Claude Code.** Quand il est actif,
se taire entièrement : ne pas créer de page, ne pas en proposer, ne pas y faire
allusion. Le plan natif a déjà son cycle complet — rédaction, puis validation
explicite par Benjamin avant la moindre écriture. Deux plans concurrents
produiraient exactement l'ambiguïté que ce dispositif existe pour supprimer :
lequel fait foi. En mode plan, c'est le plan natif, sans partage.

Sortir du mode plan ne rapatrie rien automatiquement dans Notion. Si Benjamin veut
la page après coup, il la demande, et ce skill reprend la main normalement.

Hors mode plan : annoncer en une ligne où le plan va être écrit, puis écrire. Ne
pas demander de confirmation — une page Notion se corrige, et la faire valider
d'avance coûte un tour pour rien.

## Outils nécessaires

Le connecteur **Notion** est indispensable, le connecteur **Vercel** l'est dès
qu'il y a une maquette. En session cloud, les connecteurs se choisissent
**par session** : s'ils manquent, le dire immédiatement plutôt que de contourner.

De quoi **rendre une page dans un navigateur et en tirer une image** est nécessaire dès
qu'une contrainte est visuelle — navigateur piloté par MCP, binaire de navigateur en
ligne de commande, ou harnais de test du dépôt. Aucun n'est garanti présent ni
fonctionnel : c'est une image non vide qui le prouve, pas la liste des outils. Son
absence n'est pas bloquante — elle change qui prend la capture, et c'est alors
Benjamin. Voir la sous-section « Les captures d'écran » du chapitre des contraintes.

## L'enquête avant les options

Un plan qui découvre à l'exécution ce que le code disait déjà n'a pas planifié : il
a deviné. **Avant d'écrire une question, une option ou une étape, aller chercher ce
qui est déjà su.** Cinq gisements, du moins cher au plus cher :

1. **La session en cours.** Une mesure faite il y a dix minutes reste vraie. C'est
   la source la plus souvent oubliée, parce qu'on rédige le plan dans la posture de
   celui qui ne sait pas encore — alors qu'on vient de regarder.
2. **Les plans antérieurs du même projet.** La base `Plans Claude` filtrée sur le
   projet, statuts `a merger` et `execute` : leur chapitre `Exécution` porte les
   arbitrages déjà rendus, leur `Journal d'exécution` les mesures déjà prises et les
   surprises déjà rencontrées. Une question qu'un plan précédent a tranchée ne se
   repose pas — on cite la page et on avance. Dans ces journaux, les lignes
   `découverte — trouvable au plan` sont à lire en premier : elles disent, noir sur
   blanc, ce que l'enquête d'un plan précédent a manqué sur ce projet-là.
3. **Le code.** Invoquer l'agent **`enqueteur`** (outil `Agent`,
   `subagent_type: "enqueteur"`) plutôt que fouiller soi-même : il porte déjà
   les six gestes qui évitent les angles morts de voisinage — couverture de
   l'index, `codebase-memory` en priorité sur la lecture de fichiers entiers,
   `grep` en défaut sur les zones que le graphe exclut, et surtout la
   recherche des **appelants** et pas seulement de la définition, là où se
   cachent la plupart des « découvertes » de l'exécution. Il rend une fiche
   courte et sourcée (`fichier:ligne`, ou la commande jouée et sa réponse),
   prête à recopier dans `Contraintes techniques vérifiées`.

   📄 `${CLAUDE_PLUGIN_ROOT}/agents/enqueteur.md`
4. **L'historique.** `git log` sur les fichiers concernés, PR mergées, tests
   existants. Un comportement qui a déjà été changé l'a été pour une raison, et
   cette raison contraint le plan.
5. **La carte du dépôt.** Engendrée quand un générateur existe — chercher
   `docs/architecture.md`, un script `archi`, une commande `npm run archi` —
   sinon dessinée à la main pendant l'enquête, selon les règles du fichier
   partagé `_partage/schemas.md`. Une carte, même approximative, montre en un
   coup d'œil les blocs et leurs liens là où une liste de fichiers ne montre
   qu'un inventaire à plat.

Le budget d'enquête est **proportionnel à l'enjeu**, pas à la longueur du plan : une
étape qui touche un fichier et se relit d'un coup d'œil ne mérite pas une fouille
d'historique. Une étape qui change un réglage de production, oui.

### Une option qui reporte la décision n'est pas une option

Le cas type, et la raison d'être de cette section :

> *Option 1 — poser le réglage, laisser tourner une semaine, mesurer les
> chevauchements, puis décider si un patch vaut le coup.*

Ça ressemble à de la prudence. C'en est parfois. Le plus souvent c'est une
**décision non prise**, habillée en méthode — et il arrive que la mesure invoquée
ait déjà été faite, dans la session même, sans que la question ne le sache.

Avant d'écrire une option de cette forme, deux vérifications, dans cet ordre :

1. **La mesure existe-t-elle déjà ?** Session en cours, journal d'un plan antérieur,
   sortie d'outil, tableau de bord. Si oui, la question est tranchée : elle naît
   **verte**, avec la mesure et sa provenance.
2. **La mesure est-elle faisable maintenant ?** S'il ne manque qu'une commande, une
   requête ou une lecture — **la faire pendant la passe de plan**, et écrire la
   réponse. Lire, mesurer, interroger : tout cela est permis avant `valide`. Seule
   l'écriture de code ne l'est pas (règle en tête).

Le report ne reste recevable que dans un cas : **la donnée n'existe pas encore et le
temps est le seul moyen de la produire** — un volume qu'il faut accumuler, un usage
réel qu'il faut observer. Il s'écrit alors comme tel : ce qui sera mesuré, au bout
de combien de temps, et **quel seuil déclenche quelle décision**. Un report sans
seuil n'est pas un plan, c'est un abandon poli.

## 1. Trouver le bon projet

La correspondance repo → page projet vit **dans Notion**, pas dans ce fichier —
mais pas là où on l'attend. **Les pages projet ne sont pas dans une base**, donc
elles ne portent aucune propriété. C'est chaque page de plan qui porte `Repo`
(`owner/repo`) et `Projet` (l'URL de la page projet), et la correspondance se lit
donc **dans les plans déjà écrits**.

1. Interroger la base `Plans Claude` : le plan le plus récent dont `Repo` vaut le
   dépôt courant donne l'URL `Projet` à recopier.
2. Sans correspondance : chercher la page projet par nom sous **Clients /
   Projets**, faire confirmer avant d'écrire, puis **renseigner `Repo` et `Projet`
   sur le nouveau plan** — c'est ce qui rendra la fois suivante directe.

⚠️ Un même dépôt peut pointer vers **deux pages projet différentes** selon le
sujet — sur `hermes-custom`, l'infrastructure du VPS et l'automatisation des
dépôts ne vivent pas au même endroit. Regarder les titres des plans rattachés à
chaque URL avant de choisir, plutôt que de prendre la première trouvée.

## 2. Créer la page du plan

- Base **Plans Claude**, dans `IA / Claude`. Chaque page projet porte un bloc
  « Plans Claude » : une vue liée filtrée sur ce projet, du plus récent au plus ancien.
- Titre : `[Plan] Nom_du_projet - Titre thématique`. Jamais de date dans le titre.
- Propriétés : `Projet` (**URL** de la page projet — *pas* une relation, les projets
  ne sont pas une base), `Repo` (`owner/repo`), `Statut` = `brouillon`, `Branche`,
  `PR`, `Date`. La base porte aussi `Date execution`, que ce skill ne pose pas.
- **Une page par sujet, tant que le sujet est vivant.** Les passes suivantes
  modifient cette page ; on n'en crée pas une nouvelle, sinon les fils de
  commentaires restent ancrés sur une page que personne ne rouvre.
- Un plan **clos** ne relance pas ce compteur : si son exécution laisse des étapes
  en échec ou un arbitrage en attente, `executer-plan-notion` ouvre un **plan de
  suite** — page neuve, même titre suffixé `#2` puis `#3`, qui reprend ce qui
  reste. Le `#1` n'est plus modifié, ses fils gardent leur sens là où ils sont, et
  la suite du travail a sa propre page de discussion.
- **`Branche` dit où le travail vit, et elle se renseigne au plus tôt.** Le plus
  souvent c'est `executer-plan-notion` qui crée la branche et remplit la propriété
  en ouvrant l'exécution. Mais **si une branche de travail existe déjà** quand le
  plan s'écrit — Benjamin y est, ou un plan précédent l'a laissée vivante — **la
  renseigner ici, dès la première version**. Une page qui laisse `Branche` vide
  alors qu'une branche existe fait ouvrir une seconde branche pour le même sujet,
  et les deux moitiés du travail cessent de se voir.
- **Un plan de suite `#N+1` hérite de la `Branche` du précédent**, et c'est ce qui
  garantit qu'on continue au même endroit au lieu de repartir à côté. Trois cas, et
  il faut **trancher plutôt que laisser vide** :
  - la branche du `#N` **vit encore** → la recopier telle quelle ;
  - elle est **partie sur `main`** → le `#N+1` ouvre la sienne, et on l'écrit ;
  - elle a été **abandonnée** → nommer celle qui la remplace, et dire pourquoi.
- **Vérifier, pas supposer.** À chaque passe, comparer la branche annoncée par la
  page à celle qui est réellement sortie dans le dépôt. Un écart se **signale à
  Benjamin** au lieu de se corriger en silence : c'est le plus souvent le signe
  qu'une autre session a travaillé ailleurs, et écraser la propriété ferait
  disparaître la seule trace de cet ailleurs.

- Statuts : `brouillon` → `en revue` → `valide` → `en cours` → `a merger` →
  `execute` (valeurs **sans accents**, cf. la règle en tête).
- **`a merger` et `execute` ne disent pas la même chose**, et les confondre fait
  mentir la base :
  - **`a merger`** — le travail est fait, testé et poussé, mais il vit **encore
    sur sa branche**. C'est là que tout plan s'arrête : la PR vers `main` ne
    s'ouvre que sur demande de Benjamin, jamais d'elle-même.
  - **`execute`** — le travail est **sur `main`**. Ce statut se pose au merge, et
    pas une minute avant : c'est la seule façon de lire d'un coup d'œil ce qui est
    réellement livré et ce qui attend encore.
- **`execute` est le terminus.** La valeur `archive` existe dans la base mais ce
  skill ne la pose jamais : ranger une page est une décision de Benjamin, pas un
  effet de bord d'un merge.

## 3. Structure du plan

Dans cet ordre : `Cartes` · `Besoins` · `Contraintes techniques vérifiées` ·
`Questions ouvertes` · `La suite` · `Exécution` · `Journal d'exécution` ·
`Commentaires repris`.

**Hiérarchie de titres pensée pour la table des matières.** Notion ne met dans le
sommaire latéral que les blocs *heading* — jamais les encadrés, les listes ni les
to-do. Donc : chaque section ci-dessus est un **H2**, et **chaque question ouverte,
chaque étape d'exécution et chaque entrée du journal portent leur propre H3**
(détail dans les trois sous-sections qui suivent). C'est ce qui permet de sauter
directement à « Q2 », à « Étape 4 » ou au compte rendu de cette étape depuis le
sommaire, au lieu de faire défiler la page.

`Journal d'exécution` est créé **vide** dès la première version, avec une ligne qui
dit qu'il se remplira à l'implémentation. C'est `executer-plan-notion` qui l'écrit ;
le laisser absent obligerait ce skill-là à improviser une place dans la page. Sa
forme, elle, se décide ici (troisième sous-section ci-dessous).

### Le chapitre `Cartes`

Un H2 **en tête de page**, avant `Besoins` : c'est le premier chapitre qu'on lit,
et une carte se lit avant une liste de besoins, pas après. Il porte deux schémas :

- **La carte du dépôt** — une vue d'ensemble du code touché, engendrée par un
  générateur du dépôt s'il en existe un, sinon dessinée à la main.
- **Le plan en un schéma** — les étapes du chapitre `Exécution` regroupées en
  vagues, avec ce qui dépend de quoi et ce qui attend un geste de Benjamin.

Présent **dès la première version du plan**, comme `Exécution` et pour la même
raison : si on ne sait pas encore le dessiner, c'est qu'on ne sait pas encore ce
qu'on va faire. Les deux schémas se remettent à jour à **chaque passe qui touche
le chapitre `Exécution`** — une étape ajoutée, fusionnée ou reformulée les rend
faux sinon.

Le contenu de chaque schéma, son code couleur et ses pièges Notion vivent dans un
fichier partagé, pas ici — le répéter ferait diverger les deux skills qui le
lisent :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`

**Sur un plan `Bounded`** (c'est `brainstorming` qui route une demande vers
`Spike`, `Bounded` ou `Architectural` avant que le plan ne s'écrive ; ce skill ne
décide pas du chemin, il applique la structure une fois le routage connu), la
page s'écrit **allégée** : `Cartes` · `Besoins` · `Exécution` ·
`Journal d'exécution` — `Questions ouvertes` ne s'ajoute que s'il reste une
question à trancher.

### Le chapitre `Contraintes techniques vérifiées`

Son nom est un contrat : **« vérifiées » veut dire qu'on est allé voir.** Une ligne
par contrainte, chacune avec sa **provenance** entre parenthèses — `fichier:ligne`,
la commande et ce qu'elle a répondu, une PR, une page de plan antérieure.

Sans provenance, ce n'est pas une contrainte vérifiée : c'est une hypothèse, et sa
place est dans `Questions ouvertes`. Mélanger les deux est exactement ce qui produit
les mauvaises surprises d'exécution — le sous-agent qui lit la page ne peut pas
deviner quelles lignes ont été confirmées et lesquelles ont été supposées, alors il
les traite toutes pareil.

#### Les captures d'écran

Une contrainte peut être vraie et rester illisible : `fichier:ligne` dit **où** le
code vit, jamais **quoi** on a sous les yeux. Sur un produit à plusieurs écrans, lire
« la fiche étape porte déjà un bloc horaires » n'identifie pas l'écran concerné — il
faut aller ouvrir la chose pour retrouver de quoi on parle, et ce détour se refait à
chaque relecture de la page.

**Une capture rend cette identification immédiate.** Elle ne remplace pas la
provenance textuelle : elle s'ajoute à elle.

**Quand une capture est justifiée** — et une seule question suffit à trancher :
*est-ce que quelqu'un aurait à aller ouvrir la chose pour savoir de quoi cette ligne
parle ?*

- ✅ Un écran, un composant, un état visuel, un enchaînement d'écrans, une donnée
  telle qu'elle s'affiche réellement, **une page d'un document source** dont la mise
  en page porte du sens.
- ❌ Une contrainte de code pur — signature de fonction, schéma de base, variable
  d'environnement, contrat d'API. Une capture d'éditeur de texte n'apporte rien
  qu'un `fichier:ligne` ne dise mieux, et alourdit la page pour rien.

Le budget est le même que celui de l'enquête : **proportionnel à l'enjeu**. Une page
qui devient un album photo a raté sa cible autant qu'une page sans aucune image.

**Commencer par le `CLAUDE.md` du projet.** Avant de chercher comment produire une
image, y lire ce que le dépôt dit déjà des captures : quelles surfaces existent, quel
outil les rend, quels pièges ont déjà été payés. Sur un projet qui n'a pas que des
écrans, cette section est le seul endroit où l'inventaire est juste — et l'outil de
rendu existe souvent **déjà**, écrit pour un autre besoin. Le construire à nouveau,
c'est produire un doublon en croyant découvrir. Rien sur le sujet dans le `CLAUDE.md` :
enquêter comme ci-dessous, puis **y écrire ce qu'on a trouvé** — c'est là que ça
servira la prochaine fois, pas ici.

Ce fichier reste, lui, indépendant de tout dépôt de travail (§9) : il dit **quand** une
capture se justifie et **comment la poser dans Notion**, jamais quelle commande la
produit sur telle machine.

**Ce qui est capturable ne se limite pas à l'app.** Trois familles, et les manquer
fait conclure « pas de capture possible » sur un sujet qui s'en serait très bien
accommodé :

1. **Une app qui tourne** — serveur de développement local, ou déploiement existant.
2. **Un document HTML local**, ouvert en `file://`, sans serveur : page de revue
   engendrée par un outil du dépôt, rapport, maquette, export.
3. **Un document source converti en HTML** — le cas le moins évident et le plus
   fréquent sur un projet éditorial. Un epub, par exemple, est souvent un PDF
   converti : chaque page imprimée y est un fichier XHTML positionné au pixel près,
   donc **rendable dans un navigateur** comme n'importe quelle page. Le détour par
   une visionneuse dédiée n'est pas nécessaire.

**Qui prend la capture.** Moi, pendant l'enquête, dès que la chose est joignable par
l'une de ces trois voies. Je vais jusqu'à l'écran ou la page et je prends la capture,
sans rien demander. Les cas où ce n'est pas possible se disent **en une ligne** plutôt
que de se contourner : pas d'outil de navigateur qui marche dans la session, rien de
joignable, ou accès derrière une authentification que je n'ai pas. **Demander alors la
capture à Benjamin**, en nommant précisément ce qu'on veut voir — et écrire quand même
la contrainte, avec sa provenance textuelle : une contrainte vérifiée sans image reste
une contrainte vérifiée.

⚠️ **Vérifier que l'outil rend vraiment une image, ne pas le supposer.** Plusieurs
chemins existent (navigateur piloté par MCP, binaire de navigateur en ligne de
commande, harnais de test du dépôt) et **ils ne marchent pas tous sur toutes les
machines** : un canal de navigateur absent, un binaire qui se bloque, un confinement
qui interdit un répertoire de travail. La preuve qu'une capture est possible, c'est un
fichier image non vide — pas la présence d'un outil dans la liste. Un chemin qui marche
sur cette machine se **note dans le `CLAUDE.md` du dépôt concerné**, pas ici.

⚠️ **La référence que porte la donnée n'est pas forcément l'adresse du document.** Sur
un document paginé, le numéro que le code manipule est le **numéro imprimé**, alors que
le fichier à ouvrir porte un **rang de fabrication** — les deux diffèrent dès qu'il y a
des pages liminaires, et l'écart n'est jamais annoncé. Ouvrir le fichier qui porte le
numéro cherché donne alors une page **voisine**, donc plausible, donc fausse sans que
rien ne le signale : le pire cas possible pour une contrainte dite « vérifiée ».
**Résoudre l'un vers l'autre en le mesurant** — lire le numéro imprimé sur la page
rendue et le comparer à celui qu'on cherchait — plutôt qu'en supposant l'écart. Et
vérifier l'écart sur **plusieurs** pages avant de s'y fier : rien ne garantit qu'il
soit constant d'un bout à l'autre du document.

⚠️ L'agent **`enqueteur`** ne prend aucune capture : ses outils sont en lecture de
code seule, sans navigateur. Sa fiche revient donc en texte, et c'est ici que les
captures s'ajoutent — ne pas les lui demander.

**Où elle se place.** Sous la ligne de contrainte qu'elle illustre, jamais en galerie
groupée en fin de chapitre : une image séparée de sa phrase oblige à faire
l'appariement à l'œil, et c'est exactement le travail qu'on cherchait à supprimer.
Chaque contrainte visuelle devient donc un petit bloc — la ligne, sa provenance, puis
l'image juste en dessous.

**La légende porte la provenance de l'image**, et pas celle du code : **de quoi elle
est la capture** — l'URL exacte pour une app, le chemin du fichier pour un document
local, le document et son **numéro de page imprimé** pour une page d'ouvrage — et la
**date** de la capture. Une capture est un instantané, et il vieillit sans prévenir :
sans sa date, une passe ultérieure ne peut pas savoir si elle montre encore l'état
d'aujourd'hui. Et pour une page d'ouvrage, c'est le **numéro imprimé** qui se
légende, jamais le rang du fichier ouvert pour la produire — c'est le premier que le
lecteur retrouvera dans son exemplaire, et le second ne veut rien dire hors de la
mécanique de rendu.

**Comment la poser dans la page**, en trois appels :

1. `create-file-upload` avec le nom du fichier → rend une `upload_url` et des
   `upload_headers` ;
2. un unique POST `multipart/form-data` vers cette URL, le fichier dans le champ
   `file`, tous les `upload_headers` inclus → la réponse porte un `markdown_source` ;
3. `update-page` en `update_content`, qui insère ce `markdown_source` sous la ligne
   de contrainte.

⚠️ **La pose d'une image reste une écriture dans la page**, donc le protocole du
fichier partagé s'applique entièrement (§4) — relevé avant, édition ciblée, recomptage
des cases après. Insérer une image par une **refonte** du chapitre est le geste à
éviter : les contraintes voisinent avec les questions ouvertes, et une recréation de
bloc rend les cases vierges.

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
  « L'enquête avant les options »). Une contrainte mesurée vaut mieux qu'une option
  plausible : la moitié des décisions de ce dispositif ont changé après
  vérification. Et si l'enquête donne la réponse, la question naît **verte** — on
  n'ouvre pas une question pour faire joli dans le sommaire.

### Le chapitre `Exécution`

Présent **dès la première version du plan**, jamais repoussé au moment de coder.
C'est là que le plan cesse d'être une intention : si on ne sait pas encore
l'écrire, c'est qu'on ne sait pas encore ce qu'on va faire, et c'est cette
ignorance-là qu'il faut rendre visible.

**En tête du chapitre, un tableau `Étape · Fichiers touchés · Dépend de ·
Vague`**, une ligne par étape — le pre-flight scan du chapitre : il donne
d'un coup d'œil ce qui se recoupe, avant même d'entrer dans le détail de
chaque étape. La colonne `Vague` est **proposée** ici : deux étapes vont
dans la même vague si elles ne partagent aucun fichier, si aucune ne dépend
de l'autre, et si aucun fichier partagé (config, README, `CLAUDE.md`, test de
décompte) n'est touché par les deux. Mais c'est `executer-plan-notion` qui la
**calcule** à l'ouverture de l'exécution : le plan **déclare**, il
n'**ordonnance** pas — calculer les vagues ici ferait mentir un plan qui
change d'ordre en route sans que le tableau ne le sache.

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
- **Taille** — le nombre de fichiers touchés. Plus de cinq → découper l'étape :
  l'enquête montre que tous les conflits d'exécution observés viennent d'un
  fichier partagé non repéré, et une étape large le cache d'autant mieux
  qu'elle est large.
- **Blocs touchés** — les nœuds de la carte du dépôt (chapitre `Cartes`) que
  l'étape modifie. « Aucun bloc de la carte » est une réponse valable, et il
  faut l'écrire plutôt que laisser la ligne vide.
- **Impact fonctionnel** : ce que l'utilisateur voit changer. « Rien » est une
  réponse valable, et il faut l'écrire plutôt que laisser la ligne vide.
- **Impact technique** : migrations, dépendances, variables d'environnement,
  contrats d'API, effet sur les tests existants.
- **Preuve de fin** : la commande ou l'observation qui dit que l'étape est faite.

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

## 4. Ce qu'une passe ne doit jamais effacer

Entre deux passes, la page a vécu : Benjamin a coché des cases, écrit après
`Autre / complément →`, ajouté des remarques à même le corps. **Tout cela est de
la donnée, pas du brouillon** — c'est la seule trace de ses décisions, et le fil
de discussion ne la contient pas. Une passe qui réécrit une section par-dessus
l'efface sans prévenir, parce que recréer un bloc `to-do` le rend vierge.

**Comment écrire sans rien casser vit dans un fichier partagé avec
`executer-plan-notion` :**

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`

Le protocole en cinq temps — relever avant d'écrire, éditer de façon ciblée,
remettre les `- [x]` en cas de refonte, ne jamais reformuler Benjamin, vérifier
après coup — et les cinq pièges de l'API : `update_content` qui ne décoche pas,
l'écriture qui échoue en silence, le commentaire qu'on ne résout jamais
soi-même, `replace_all_matches` sur un motif de balisage, et l'insertion
ancrée au milieu d'un paragraphe formaté.

Il porte aussi **« Le bleu des retouches »** : ce qui a bougé à la dernière passe
s'écrit en bleu, et le bleu de la passe d'avant redevient neutre — dans cet ordre,
sous peine d'effacer ce qu'on vient de marquer. C'est le repère qui permet de rouvrir
la page et de voir en un coup d'œil ce qui est nouveau, au lieu de la relire en
entier. Deux garde-fous à connaître avant d'y toucher : le bleu ne repeint jamais un
encadré de question — sa couleur dit déjà son état (§3) — et il ne se pose jamais sur
le texte de Benjamin.

**À lire avant la première écriture de la session**, pas de mémoire. Chacune de
ces règles a coûté un dégât réel ; les deux skills les partagent pour qu'une
correction ne se fasse qu'une fois.

**Ceinture — fichier introuvable.** Si la lecture échoue (plugin pas encore
installé, version périmée, fichier supprimé localement) : **le dire en une
ligne avec le chemin, et ne pas écrire dans la page**. Pas de repli « je m'en
souviens à peu près » : ces règles existent précisément parce qu'elles ne se
reconstituent pas de mémoire, et une passe faite au jugé efface des décisions
de Benjamin sans rien signaler. Deux issues, dans cet ordre : **mettre à jour
le plugin** — `claude plugin update plans-notion` (redémarrage requis pour
l'appliquer), ou `claude plugin marketplace update` si la source a bougé — ou
**demander à Benjamin**. Écrire quand même est le seul choix qui n'est pas sur
la table ; lire la page, en revanche, reste permis.

## 5. La boucle de commentaires

À chaque passe, dans cet ordre :

1. Lire les fils **non résolus**, y compris ceux ancrés dans le corps — il faut le
   demander explicitement, sinon on ne voit que les commentaires de niveau page.
2. Les traiter **un par un**. Répondre dans le fil en disant *ce qui a changé dans
   le plan*, pas seulement si on est d'accord.
3. Répercuter dans le plan. L'édition ciblée est le défaut — elle préserve les
   fils vivants et l'état des cases (§4) — mais **le plan prime sur les ancres** :
   si une refonte est meilleure, la faire, relevé en main.
4. Tout commentaire dont l'ancre n'a pas survécu est recopié — son texte et la
   réponse — dans `Commentaires repris`, un bloc par commentaire, par passe.
5. **Relire le plan entier** et raccorder ce que la passe a désaligné : renvois
   entre questions, décisions périmées, décomptes, et le chapitre `Exécution` que
   les réponses viennent de rendre faux.
6. **Ne jamais résoudre un fil soi-même.** C'est l'accusé de réception de
   Benjamin, et c'est ce qui donne gratuitement la liste à traiter à la passe suivante.
7. **Relire les schémas.** Une passe qui a touché `Exécution` a pu rendre « le
   plan en un schéma » faux (chapitre `Cartes`, §3) — le rejouer, puis vérifier
   mécaniquement que le nombre de nœuds d'étape égale le nombre de titres H3
   `Étape N` de la page (contrôle détaillé dans `_partage/schemas.md`).

Les pièges de l'API qui mordent ici — commentaire ni déplaçable ni résoluble,
écriture qui échoue en silence après normalisation du texte par Notion — sont
décrits dans le fichier partagé (§4).

## 6. Lecture économe

Garder un miroir du plan hors du dépôt, avec l'horodatage de dernière
modification de la page **et le relevé préalable (§4)** — cases cochées et
textes libres. À chaque passe : lire les fils — quelques centaines de tokens — et
ne recharger la page entière que si elle a changé côté Notion, ou pour la
relecture de cohérence finale. **Le miroir est un cache, jamais une source de
vérité** : absent — autre machine, autre session — on recharge, sans état d'âme.
Et le relevé se refait toujours sur la page fraîche avant une refonte, jamais sur
le miroir : c'est précisément entre deux sessions que Benjamin coche.

## 7. Maquettes HTML

Si le plan touche à du design, produire une maquette et la référencer dans la
page. Le déploiement Vercel et ses pièges vérifiés (Deployment Protection,
premier déploiement qui part en prod, contenu factice obligatoire, pleine
largeur pour l'iframe Notion, fichier HTML unique) vivent dans un fichier
partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-vercel.md`

**À lire avant tout déploiement de maquette**, pas de mémoire : chacun de ces
pièges a déjà produit une maquette invisible ou un domaine de production
écrasé.

## 8. Passer la main à l'exécution

Concevoir et réaliser sont deux postures opposées — l'une n'écrit rien, l'autre
n'écrit que du code — et elles vivent dans deux skills séparés. Ce fichier
s'arrête au moment où le plan devient exécutable.

Quand Benjamin valide le plan :

1. **D'abord répercuter ses dernières réponses dans le chapitre `Exécution`** —
   cases cochées, textes libres après `Autre / complément →`, commentaires de la
   passe — corrections datées (§3). Un plan passe à `valide` avec un chapitre
   `Exécution` juste, ou il n'y passe pas : c'est ce chapitre-là, et pas les
   réponses éparpillées dans la page, qui part dans les briefs des sous-agents
   d'exécution.
2. **Passer le plan au filtre de l'enquête.** Sept vérifications, et elles se
   font page ouverte, pas de mémoire :
   1. plus aucune question ouverte dont la réponse était vérifiable et n'a pas
      été vérifiée ;
   2. plus aucune option qui reporte une mesure faisable aujourd'hui ;
   3. chaque chemin de « Fichiers touchés » qui existe vraiment, ou qui est
      annoncé comme une création ;
   4. une relecture de **cohérence interne** : les renvois entre sections
      pointent juste, l'ordre des étapes est le bon, et aucune prémisse ne
      contredit une réponse tranchée plus loin dans la page ;
   5. chaque « Preuve de fin » a été **jouée**, ou est **réfutable**, avant de
      passer `valide` — une preuve qu'on ne peut ni jouer ni contredire ne
      prouve rien à l'exécution ;
   6. aucun chiffre n'est repris d'un plan `#N-1` **sans remesure** ;
   7. toute question chiffrée porte, à côté de sa réponse, la commande jouée
      et son résultat — sinon rien ne permet de la remesurer au point 6
      suivant.

   Les quatre derniers points viennent de l'enquête sur les plans passés : la
   page du plan elle-même est la source de **11 %** des découvertes manquées à
   l'exécution — ordre des étapes faux, preuve de fin impossible à jouer,
   renvois périmés — et des chiffres recopiés d'un plan antérieur s'y sont
   trouvés faux avec des écarts allant jusqu'à **80 %**. Ce filtre coûte
   quelques minutes ici et évite la découverte en pleine exécution, qui coûte
   une étape.
3. Passer `Statut` à `valide`.
4. Le dire en une ligne, et **invoquer `executer-plan-notion`** si l'implémentation
   enchaîne dans la foulée. Un skill n'en charge pas un autre tout seul : sans
   invocation explicite, ses règles ne s'appliquent pas.
5. Ne pas commencer à coder ici « en attendant ». Le §1 tient jusqu'au bout.

Le plus souvent, ce n'est pas moi qui valide : **Benjamin répond dans la page,
passe `Statut` à `valide` lui-même et invoque `executer-plan-notion` directement**,
sans repasser par ici. Ce skill n'a alors jamais vu ses réponses. C'est pourquoi
`executer-plan-notion` refait cette mise à jour à son entrée (§2 de ce skill-là) :
les deux passages font le même travail, exprès. On ne sait jamais d'avance lequel
des deux sera sauté, et un chapitre `Exécution` en retard d'un tour produit un
travail qui répond à la version d'avant.

Ce que `executer-plan-notion` prend en charge, et qu'il est donc inutile de
détailler dans le plan : la découpe en sous-agents, le `Journal d'exécution`, la
branche du plan — sa PR unique n'attend que la demande de Benjamin —, le
déroulé de bout en bout en autonomie, le
statut de fin (`a merger`, puis `execute` une fois sur `main`), et le plan de
suite `#N+1` s'il reste des arbitrages. Ce
qui reste au plan, c'est le **contenu** du chapitre `Exécution` — le quoi, pas le
comment de la séance de code.

## 9. Ce que ce skill ne fait pas

- Il ne code pas, jamais — même après `valide`. C'est `executer-plan-notion`.
- Il ne résout pas les fils de commentaires.
- Il n'ouvre pas de PR de lui-même et ne merge rien.
- Il ne passe jamais un plan en `archive`.
- Il ne dépend d'aucun `CLAUDE.md`, d'aucun hook, d'aucun fichier du dépôt de
  travail. Ses compagnons sont les fichiers partagés
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md` et
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-vercel.md`, livrés par le
  plugin `plans-notion` — pas par le dépôt de travail, quel qu'il soit.
