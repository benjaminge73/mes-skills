# Les chapitres Cartes, Maquette et Contraintes techniques vérifiées — détail

Référence de `plan-notion`, lue **avant d'écrire ou de remettre à jour** l'un de ces trois chapitres. Le déroulé et l'ordre des chapitres restent dans `SKILL.md` (§3).

## Sommaire

- Le chapitre `Cartes`
- Le chapitre `Maquette`
- Le chapitre `Contraintes techniques vérifiées` (dont « Les captures d'écran »)

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


### Le chapitre `Maquette`

Un H2 juste après `Besoins` : les besoins disent ce qu'on veut, la maquette
montre l'écran qui y répond, avant qu'on descende dans les contraintes et les
étapes.

**Présent dès la première version, sur tout plan, allégé compris.** Il porte
l'une de deux choses, jamais rien :

- **La maquette**, dès qu'une étape change ce qui s'affiche — c'est-à-dire dès
  que sa ligne `Impact fonctionnel` (chapitre `Exécution`) dit autre chose que
  « Rien » : un écran, un composant, un état (vide, erreur, chargement), un
  libellé, un enchaînement d'écrans. La taille du changement ne dispense pas :
  un libellé qui change se montre en une maquette de vingt lignes.
- **Une dispense écrite**, en une ligne : `Pas de maquette — <raison>`. Deux
  raisons seulement sont recevables : **aucune étape ne change ce qui
  s'affiche** (serveur, refacto front sans effet visible, tests, outillage), ou
  **Benjamin l'a demandé**, ses mots recopiés. « C'est petit », « c'est
  évident », « le design system suffit » ne sont pas des raisons.

Pourquoi un chapitre toujours présent, même pour dire « rien » : il pose la
question à chaque plan, et une dispense devient une phrase que Benjamin lit et
peut contester, au lieu d'un silence.

**Ce que la maquette montre** : les écrans et les états que les étapes
changent, dans leur **état cible** — pas l'application entière. L'état actuel,
quand il compte, est déjà dans `Contraintes techniques vérifiées` sous forme de
capture. Plusieurs écrans touchés : **un seul fichier**, avec des onglets ou
des sections, pour qu'une passe n'ait qu'un bloc à remplacer.

**La légende** porte `Maquette — passe N · AAAA-MM-JJ · file_upload_id <id>`,
l'`id` étant celui que `create-attachment` a rendu. C'est **la seule prise**
qu'aura une autre session pour relire le HTML — à l'exécution notamment :
l'identifiant visible dans le `src` de la page ne sert pas à ça (mesuré le
2026-09-24, `download-attachment` le refuse en 404).

**Chaque étape qui change ce qui s'affiche dit, dans son `Impact fonctionnel`,
quelle partie de la maquette elle réalise.** C'est ce qui permet, à
l'exécution, de comparer une étape à sa cible au lieu de comparer le tout au
tout.

Le chapitre se remet à jour à **chaque passe qui change ce qu'une étape
affiche** — une maquette qui montre l'écran d'avant la dernière réponse de
Benjamin est pire qu'aucune. Le comment — design system, geste en deux
appels, remplacement, poids — est au §7.

### Le chapitre `Contraintes techniques vérifiées`

Son nom est un contrat : **« vérifiées » veut dire qu'on est allé voir.** Une ligne
par contrainte, chacune avec sa **provenance** entre parenthèses — `fichier:ligne`,
la commande et ce qu'elle a répondu, une PR, une page de plan antérieure.

Sans provenance, ce n'est pas une contrainte vérifiée : c'est une hypothèse, et sa
place est dans `Questions ouvertes`. Mélanger les deux est exactement ce qui produit
les mauvaises surprises d'exécution — le sous-agent qui lit la page ne peut pas
deviner quelles lignes ont été confirmées et lesquelles ont été supposées, alors il
les traite toutes pareil.

**Deux blocs propres à ce chapitre**, issus de l'enquête (« L'enquête avant les
options », dans `enquete.md`) :

- **La ligne « Existant »**, obligatoire, **une par artefact**, dès que le plan crée
  quelque chose de non propre au projet : *« Existant cherché : … / trouvé : … /
  fait maison parce que … »*. Elle reprend le verdict d'ensemble du `chercheur`, avec, pour un candidat
  *use*, les chiffres rejoués par `gh api` et le verdict de l'outil de vérification
  (« Vérifier un candidat *use* », dans `enquete.md`). « Sans objet » est une réponse, à condition de
  dire pourquoi.
- **L'intertitre « État de départ »**, qui porte le résultat de la répétition à
  blanc : commandes jouées, sorties, décompte de la suite, comptages. Un plan
  `valide` sans cette section n'a pas eu sa répétition.

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

Ce skill reste, lui, indépendant de tout dépôt de travail (§9) : il dit **quand** une
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

