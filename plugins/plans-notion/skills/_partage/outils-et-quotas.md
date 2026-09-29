# Le registre des outils, de leurs quotas et de leurs pièges

Fichier **partagé**, lu par `plan-notion` (avant d'écrire une étape qui lance un
lot d'appels sur un outil externe), par `executer-plan-notion` (avant de
déléguer un lot) et par l'agent `chercheur` (quand un outil n'a pas de fiche).
Comme `vagues.md` et `bons-tests.md`, il vit à un seul endroit pour que les
skills gardent leur taille : la règle ne se duplique pas, elle se référence.

Il ne dit pas *comment* prouver qu'une étape est finie (`preuve-du-rouge.md`)
ni *comment* paralléliser (`vagues.md`). Il dit ce que **coûte** un outil,
ce qui l'a **déjà fait échouer**, et **quoi faire à la place** quand il échoue.

## Pourquoi ce fichier

Les mêmes pannes d'outil se sont répétées d'un plan à l'autre, chacune
redécouverte en pleine exécution : un quota journalier épuisé au milieu d'une
campagne, un service public qui répond 429 dès qu'on le sollicite en parallèle,
un lot qui « marche » mais rend des résultats sans valeur, un coût estimé à
partir d'un chiffre jamais mesuré. Aucune de ces pannes n'était imprévisible :
chacune était écrite quelque part — dans la doc de l'outil, dans le journal
d'un plan précédent — sans que le plan suivant la lise.

La pire des quatre est la dernière. Le 2026-08-26, un guide dont la génération
avait été estimée à **1,04 $** en a coûté **27,5 $** à la mesure : le chiffre
fondateur du plan n'avait jamais été vérifié sur un appel réel. Un plan bâti
sur un chiffre faux prend toutes ses décisions d'échelle à l'envers.

## Règle pour un outil absent

Quand un plan doit appeler un outil qui n'a **pas de fiche** ci-dessous :

> Doc lue par l'agent `chercheur`, puis un seul appel d'essai, puis la fiche
> créée dans le registre avant tout lot. Au-delà de 100 appels, ou dès qu'un
> appel est payant, demander à Benjamin avant de lancer.

Trois précisions :

- **Un seul appel d'essai, mesuré.** Ce qu'on relève : le quota consommé, le
  coût réel, le format de la réponse. Le chiffre du plan vient de cet appel,
  jamais d'une estimation lue dans une doc ou dans un article.
- **La fiche précède le lot**, pas l'inverse. Une fiche écrite après coup
  décrit les pannes qu'on a subies ; écrite avant, elle empêche la première.
- **Le seuil de 100 appels** est celui de la demande à Benjamin, pas celui de
  la fiche : la fiche se crée dès le premier appel.

## Règle de vie du registre

- **On fonctionne par outil, pour le quota.** Un quota est propre à un outil
  (et parfois à un chemin d'accès à cet outil, voir Google Places) : on ne
  raisonne pas en « budget d'appels » global du plan.
- **Le registre se met à jour par PR sur `mes-skills`, à la clôture de chaque
  plan qui a appris quelque chose sur un outil** — un quota mesuré, un piège
  rencontré, un repli qui a marché. Un plan qui n'a rien appris n'ouvre pas de
  PR pour ce fichier.
- **Chaque chiffre porte sa date de lecture.** Un quota change sans prévenir ;
  un chiffre sans date ne se distingue pas d'un chiffre périmé.

## Règle de publication

**Ce dépôt est public.** Une fiche ne contient **ni clé d'API, ni nom de
compte, ni numéro de projet**, et pas davantage d'identifiant de facturation,
d'adresse de messagerie ou d'URL contenant un jeton. Les pièges sont datés et
décrits **sans** dire à quel plan, quel client ou quel compte ils sont arrivés :
la date et le mécanisme suffisent à les retrouver dans le journal du plan
concerné, qui, lui, n'est pas public.

Contrôle avant d'ouvrir la PR : chercher dans ce fichier toute suite de neuf
chiffres ou plus (un numéro de projet), tout nom de variable se terminant par
« KEY » précédé d'un tiret bas, et toute adresse de messagerie. La preuve de
l'étape qui a créé ce fichier rejoue cette recherche et attend une sortie vide.

## Forme d'une fiche

Un titre `## Fiche — <outil>`, puis quatre sous-rubriques, toujours les mêmes et
dans cet ordre : **Quota ou coût** (avec la source et la date de lecture),
**Pièges datés**, **Bonne pratique**, **Repli**. Une rubrique sans objet
s'écrit « aucun connu au <date> », elle ne disparaît pas.

## Fiche — Google Places

**Quota ou coût** (relevé au 2026-09-29, console du fournisseur et incidents
ci-dessous) :

- **4 000 requêtes `SearchTextRequest` par jour et par projet**, remise à zéro
  vers 09 h heure de Paris (07 h UTC).
- **Palier de facturation : 5 000 par mois** au niveau Pro.
- **Champs du palier Enterprise** (téléphone, site web) : **1 000 gratuits par
  mois**, payants au-delà.
- Les quotas sont **distincts selon le chemin d'accès** : passer par un
  connecteur tiers et passer par un relais serveur propre consomme deux
  quotas séparés. Épuisé d'un côté, l'autre peut rester disponible.
- **Aucun plafond dur n'est posé en console** : rien côté fournisseur
  n'arrête une campagne qui s'emballe. Seul un `--max-appels` posé dans le
  script protège.

**Pièges datés** :

- **Quota journalier épuisé les 2026-09-04 et 2026-09-05, puis le
  2026-09-25** : chaque fois au milieu d'une campagne, sans alerte préalable.
- **`fieldMask` par défaut sans position ni contact** : la réponse ne porte
  ni coordonnées ni téléphone. Le découvrir après coup a failli coûter
  **98 appels** de plus.
- **`detail: true` bascule au palier Enterprise** : un seul champ demandé
  suffit à faire facturer la requête au tarif du palier supérieur.

**Bonne pratique** :

- Toujours poser `--max-appels` dans le script d'un lot, à une valeur
  inférieure au quota restant, jamais « illimité ».
- Écrire le `fieldMask` explicitement, champ par champ, et décider **avant** le
  lot si le palier Enterprise est voulu.
- Lire le quota restant avant de lancer, et l'heure de remise à zéro : ne pas
  lancer un lot de 3 000 appels à 08 h 30 heure de Paris.

**Repli** : basculer sur l'autre chemin d'accès (connecteur tiers ou relais
propre) dont le quota est distinct, ou reporter le lot après 09 h heure de
Paris. Ne pas contourner en multipliant les projets : ce n'est pas un
repli, c'est un détournement du quota.

## Fiche — Nominatim, Photon et Overpass

Trois services publics de cartographie ouverte, traités ensemble parce qu'ils
échouent pour la même raison : ce sont des serveurs communautaires, sans
contrat, dimensionnés pour un usage léger.

**Quota ou coût** (relevé au 2026-09-29) :

- **Nominatim** : gratuit, **1 requête par seconde par adresse IP**. Politique
  d'usage publiée par le service ; le dépasser mène au blocage.
- **Photon** : gratuit, sans quota chiffré publié, même logique d'usage
  raisonnable.
- **Overpass** : gratuit, quota dépendant de la charge du serveur au moment de
  l'appel — une même requête peut passer à 10 h et échouer à 14 h.

**Pièges datés** :

- **2026-09-26** : **429 (trop de requêtes) dès 5 agents en parallèle** sur
  Nominatim, l'IP étant partagée par tous les agents d'une même machine.
  **2 agents au maximum, avec `sleep 5`** entre les requêtes, ont tenu.
- **2026-09-08** : Nominatim **bloqué depuis une session cloud** — les plages
  d'adresses des hébergeurs sont refusées en bloc.
- **2026-09-28** : **Overpass en 504** (délai dépassé côté serveur) sur une
  requête qui avait passé la veille.

**Bonne pratique** :

- Une seule file de requêtes par IP, jamais une file par agent : le quota se
  partage entre tous les processus de la machine.
- Envoyer un en-tête `User-Agent` identifiable (nom du projet, contact
  générique) — c'est exigé par la politique de Nominatim.
- Mettre en cache tout ce qui a déjà été résolu : une adresse géocodée une fois
  ne se redemande pas.
- Sur un 429 ou un 504, attendre et **réessayer avec délai croissant**, pas
  relancer en boucle.

**Repli** : **Photon tolère l'orthographe** approximative là où Nominatim
échoue — l'utiliser quand une adresse saisie à la main ne se résout pas. Pour
un volume qui dépasse durablement 1 requête par seconde, ou depuis une session
cloud, monter une instance propre plutôt que de forcer le service public.

## Fiche — Jev

**Jev** est le modèle d'évaluation interne : il note des descriptions, une
note par description. Il n'a pas de tarif public : c'est un service maison.

**Quota ou coût** (relevé au 2026-09-29, sur trois campagnes réelles) :

- **Quasi gratuit** à l'appel : le coût ne limite pas le volume.
- **Ordres de grandeur réels** : **4 177**, **3 076** et **796 appels** sur
  trois campagnes. Un lot de plusieurs milliers d'appels est donc normal, et
  franchit à chaque fois le seuil de 100 appels de la règle « outil absent » —
  celle-ci ne s'applique plus, puisque l'outil a une fiche.

**Pièges datés** :

- **Un lot de 35 descriptions dans un seul appel rend des notes
  constantes** : mesuré, **AUC de 0,49** — c'est-à-dire le hasard pur. L'appel
  répond, le format est correct, les notes ne valent rien. Rien ne signale
  l'échec dans la réponse ; seule la mesure du pouvoir discriminant le révèle.

**Bonne pratique** :

- **Une description par appel**, sans exception.
- Mesurer l'AUC (ou un équivalent) sur un échantillon **avant** de lancer la
  campagne complète, et refuser un résultat dont la mesure est proche du
  hasard (0,5).
- Lancement glissant plutôt qu'en un bloc si la campagne dépasse une douzaine
  d'agents (voir `vagues.md`).

**Repli** : aucun connu au 2026-09-29. En cas d'indisponibilité, reporter la
campagne : une note produite par un autre modèle n'est pas comparable à celles
déjà obtenues.

## Fiche — Sessions Claude

Les sessions Claude elles-mêmes sont un outil à quota : un plan qui délègue
beaucoup consomme le même plafond que la session de pilotage.

**Quota ou coût** (relevé au 2026-09-29) :

- **Limite par fenêtre glissante** : **429 vers 23 h UTC**, remise à zéro à
  **00 h 30 UTC**.
- **Limite hebdomadaire par famille de modèle** : la limite hebdomadaire de
  **Sonnet** a été **atteinte le 2026-09-26**.
- **Plafond de concurrence** : au-delà d'**une vingtaine d'appels `Agent`
  simultanés**, le classifieur de permissions sature (2026-09-25).

**Pièges datés** :

- **2026-09-25** : vers une vingtaine d'appels `Agent` en même temps, `Bash` et
  `SendMessage` se mettent à être refusés, et des agents calent sans qu'aucun
  n'ait échoué proprement.
- **2026-09-26** : limite hebdomadaire **Sonnet** atteinte. Le quota
  hebdomadaire est propre à une famille de modèles : l'épuiser ne dit rien de
  ce qui reste sur les autres.

**Bonne pratique** :

- **Ne pas dépasser une douzaine d'agents simultanés** ; pour une longue
  campagne, lancement glissant (`vagues.md`, section « Le plafond de
  concurrence »).
- Éviter de lancer un gros lot à l'approche de 23 h UTC : une coupure en cours
  de vague laisse des étapes à moitié faites.
- Répartir la charge entre familles de modèles quand une limite hebdomadaire
  approche, plutôt que de tout envoyer à la même.

**Repli** : attendre la remise à zéro (00 h 30 UTC pour la fenêtre courte),
reprendre le plan à l'étape interrompue — le journal d'exécution sur la page
dit où — plutôt que de relancer la vague entière.

## Fiche — DeepSeek vision

**Quota ou coût** (relevé au 2026-08-26, mesure sur un guide réel) :

- **27,5 $ par guide mesurés**, contre **1,04 $ estimés** avant lancement — un
  écart d'un facteur d'environ 26. C'est la fiche du registre où le coût est
  le paramètre décisif, pas le quota.

**Pièges datés** :

- **2026-08-26** : le chiffre de **1,04 $** était une estimation, pas une
  mesure ; le coût réel n'a été connu qu'après coup. La cause précise de
  l'écart n'est pas consignée ici : la retrouver dans le journal du plan avant
  de s'en servir.
- C'est **l'exemple type d'un chiffre fondateur faux** : la décision
  d'architecture (tout traiter par cet outil) reposait sur lui.

**Bonne pratique** :

- **Un appel d'essai réel, sur un guide représentatif, avant tout plan
  chiffré** : la règle « outil absent » vaut aussi pour un outil connu dont le
  coût n'a jamais été mesuré dans le contexte du plan.
- Multiplier le coût mesuré d'un guide par le nombre de guides et le montrer à
  Benjamin **avant** de lancer : le coût est payant, donc la règle « dès qu'un
  appel est payant, demander » s'applique sans seuil de 100 appels.
- Poser un plafond de dépense dans le script du lot, comme un `--max-appels`.

**Repli** : réduire ce qui est envoyé à l'outil (moins d'images, images
réduites) ou traiter un échantillon plutôt que la totalité ; ne pas relancer le
lot complet tant que le coût mesuré n'a pas été accepté.
