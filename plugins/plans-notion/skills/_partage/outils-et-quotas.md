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

**Quota ou coût** (relevé au 2026-09-29, d'après les incidents datés
ci-dessous) :

- **4 000 requêtes `SearchTextRequest` par jour et par projet**, remise à zéro
  vers 09 h heure de Paris (07 h UTC).
- **Palier de facturation : 5 000 par mois** au niveau Pro.
- **Champs du palier Enterprise** (téléphone, site) : **1 000 gratuits par
  mois**.
- Les quotas sont **distincts entre deux chemins d'accès au même service**.
- **Aucun plafond dur n'est posé en console** : seul `--max-appels` protège.

**Pièges datés** :

- **Quota journalier bloquant les 2026-09-04 et 2026-09-05, puis le
  2026-09-25.**
- **`fieldMask` par défaut sans position ni contact.** Le découvrir après coup
  a failli coûter **98 appels**.
- **`detail: true` bascule au palier Enterprise.**
- **2026-09-30 : un 429 qui n'est pas le quota.** Sur un lot de contacts
  (champs Enterprise), appelé en séquence par un proxy, Google répond 429
  après **25 à 60 appels en rafale**. Un appel isolé quelques minutes plus
  tard passe, et le lot repart après une pause d'**environ 65 s** : c'est une
  **limite de débit**, pas le quota du mois. 900 appels passés ce jour-là en
  18 tranches, sans jamais toucher le quota.

**Bonne pratique** :

- Toujours poser `--max-appels` dans le script d'un lot.
- Écrire le `fieldMask` explicitement, et décider **avant** le lot si le
  palier Enterprise est voulu.
- Lire un 429 avant de conclure au quota épuisé : relancer après une pause
  d'une minute. S'il cède, jouer le lot par tranches, avec une pause après
  chaque 429, et compter les tentatives refusées dans le plafond.

**Repli** : sur un 429 de débit, faire une pause d'environ 65 s puis reprendre. Sur
un quota épuisé, passer par l'autre chemin d'accès, dont le quota est distinct,
ou reporter le lot après la remise à zéro (09 h heure de Paris).

## Fiche — Nominatim, Photon et Overpass

**Quota ou coût** (relevé au 2026-09-29) :

- **Nominatim** : **1 requête par seconde par adresse IP**.
- **Photon** : aucun quota chiffré consigné au 2026-09-29.
- **Overpass** : aucun quota chiffré consigné au 2026-09-29.

**Pièges datés** :

- **2026-09-26** : Nominatim répond **429 dès 5 agents en parallèle**.
  **2 agents au maximum, avec `sleep 5`.**
- **2026-09-08** : Nominatim **bloqué depuis une session cloud**.
- **2026-09-28** : **Overpass en 504.**

**Bonne pratique** : ne pas dépasser **2 agents en parallèle** sur Nominatim,
avec `sleep 5` entre les requêtes.

**Repli** : **Photon tolère l'orthographe** approximative là où Nominatim
échoue. Pour Nominatim depuis une session cloud et pour Overpass en 504 :
aucun repli connu au 2026-09-29.

## Fiche — Jev

**Quota ou coût** (relevé au 2026-09-29, sur trois campagnes réelles) :

- **Quasi gratuit** à l'appel.
- **Ordres de grandeur réels** : **4 177**, **3 076** et **796 appels** sur
  trois campagnes. Chacune franchit le seuil de 100 appels de la règle
  « outil absent » — celle-ci ne s'applique plus, puisque l'outil a une
  fiche.

**Pièges datés** :

- **Un lot de 35 descriptions dans un seul appel rend des notes
  constantes** : mesuré, **AUC de 0,49**, soit le hasard (0,5).

**Bonne pratique** : **une description par appel.**

**Repli** : aucun connu au 2026-09-29.

## Fiche — Sessions Claude

**Quota ou coût** (relevé au 2026-09-29) :

- **429 vers 23 h UTC**, remise à zéro à **00 h 30 UTC**.
- Limite hebdomadaire de **Sonnet** **atteinte le 2026-09-26**.
- Vers **une vingtaine d'appels `Agent` simultanés**, le classifieur de
  permissions sature (2026-09-25).

**Pièges datés** :

- **2026-09-25** : saturation du classifieur de permissions vers une vingtaine
  d'appels `Agent` simultanés.
- **2026-09-26** : limite hebdomadaire **Sonnet** atteinte.

**Bonne pratique** : rester en deçà d'une vingtaine d'appels `Agent`
simultanés (`vagues.md`, section « Le plafond de concurrence »).

**Repli** : attendre la remise à zéro (00 h 30 UTC après le 429 de 23 h UTC).

## Fiche — DeepSeek vision

**Quota ou coût** (relevé au 2026-08-26, mesure sur un guide réel) :

- **27,5 $ par guide mesurés**, contre **1,04 $ estimés** avant lancement,
  soit un écart d'un facteur d'environ 26.

**Pièges datés** :

- **2026-08-26** : le chiffre de **1,04 $** était une estimation, pas une
  mesure ; le coût réel n'a été connu qu'après coup. La cause précise de
  l'écart n'est pas consignée ici : la retrouver dans le journal du plan avant
  de s'en servir.

**Bonne pratique** :

- **Un appel d'essai réel, sur un guide représentatif, avant tout plan
  chiffré** : la règle « outil absent » vaut aussi pour un outil connu dont le
  coût n'a jamais été mesuré.
- Multiplier le coût mesuré d'un guide par le nombre de guides et le montrer à
  Benjamin **avant** de lancer : l'appel est payant, donc la règle « dès qu'un
  appel est payant, demander » s'applique sans seuil de 100 appels.

**Repli** : aucun connu au 2026-08-26.

## Fiche — claude plugin eval

**Quota ou coût** (mesuré le 2026-09-30 sur le banc de `plans-notion`, rapports
de CI ; fiche écrite le 2026-10-01). Les montants sont l'équivalent au tarif de
l'API : l'abonnement ne facture pas en dollars, mais le dollar est la règle
commune pour comparer les postes.

- **Un passage est une session complète.** Chaque cas est joué 3 fois par bras,
  donc 16 cas × 3 passages = 48 sessions par bras. Une A/B joue deux bras (la
  base et la tête) : tout est à doubler. Le modèle joué est Sonnet, effort
  `high` ; la correction se fait par expressions régulières, sans modèle-juge,
  donc sans coût de juge.
- **Un bras complet coûte 27,53 $.** Un cas coûte entre 0,98 $ et 3,57 $. Une
  A/B sur tout le banc coûte donc environ 55 $, et une A/B ciblée sur une
  catégorie 3 à 14 $.
- **Par catégorie**, pour un bras de 3 passages, puis pour un seul passage (le
  coût d'une fumée) :

| Catégorie | Cas | Un bras, 3 passages | Un passage |
|---|---|---|---|
| `existant` | 2 | 6,43 $ | 2,14 $ |
| `bruit` | 3 | 4,81 $ | 1,60 $ |
| `etat-de-depart` | 4 | 7,13 $ | 2,38 $ |
| `maquette` | 1 | 1,61 $ | 0,54 $ |
| `decouvertes` | 4 | 4,98 $ | 1,66 $ |
| `perimetre` | 2 | 2,56 $ | 0,85 $ |
| **tout le banc** | 16 | 27,53 $ | ≈ 9,2 $ |

- **Une A/A sur Opus** a coûté 53,14 $ : un bras de Sonnet coûte la moitié.
- **Le plafond par appel** (`EVALS_MAX_COUT_USD`) vaut 35 $ par bras, soit un
  bras complet plus une marge. Il valait 120 $ avant le 2026-10-01 et n'a jamais
  été atteint : il ne protégeait de rien.
- **Les sessions d'un appel partagent une seule limite de débit**, celle du
  compte qui les paie. La doc de l'outil le dit pour l'option `-j` (nombre de
  runs en parallèle) : *« Each run is a full claude child on your own
  credential, so they share one rate limit »*. Monter `-j`, ou lancer deux appels
  ensemble, ne va pas plus vite : cela fait entrer les sessions en concurrence
  pour la même limite.

**Pièges datés** :

- **2026-09-30** : trois bancs ont tourné ensemble (deux en CI, un en local).
  Les scores sont tombés sur les mêmes cas : 50 % et 44 % pour deux têtes, contre
  76 % pour la tête jouée seule. La cause exacte (des sessions coupées par la
  limite de débit) n'est pas prouvée, mais ces résultats étaient inexploitables
  et il a fallu les rejouer.
- **Avant le 2026-10-01**, le banc se lançait tout seul dès qu'une PR touchait un
  skill, et en entier pour `_partage/`. Une PR d'une seule page de doc a coûté
  71 $. Depuis, la CI joue les évals à la demande (label `evals`).
- **2026-09-30** : le coût d'un rejeu réel écrit dans une doc privée était faux
  d'un facteur 25 : il ne comptait que la taille finale du contexte, pas les
  relectures à chaque tour. Mesuré dans les transcriptions : un rejeu coûte
  environ 3,30 $ (10 M de jetons relus), un juge environ 0,75 $.

**Bonne pratique** :

- **Estimer avant de lancer** :
  `python3 scripts/evals_ab.py --plugin <p> --estimer --base-rapport <json>
  --cas a --cas b` donne le coût du bras de tête d'après ce rapport de base
  (`--reference <json>` de même). `--cas` se répète, il n'accepte pas de liste
  séparée par des virgules. L'annoncer à Benjamin avant de lancer.
- **Un seul banc à la fois.** En CI, le groupe de concurrence `evals-<plugin>`
  met un second banc en attente. En local, `evals/outillage/lancer.sh` prend
  lui-même le jeton de la machine (`evals-locales`), attend `EVALS_ATTENDRE`
  secondes (300 par défaut) s'il est tenu, puis refuse (code 75), et le rend à
  la sortie : ne pas le prendre à la main avant, le lanceur attendrait puis
  refuserait. `EVALS_FORCER=1` ne passe outre que le contrôle des bancs de CI
  (`gh`), jamais le jeton ; sur ordre explicite seulement.
- **Cibler.** Choisir les catégories d'après les fichiers touchés ; ne jouer
  « tout » que pour `_partage/`, un hook ou le banc lui-même.
- **Garder 3 passages par cas** : le bruit mesuré ne vaut que pour 3.

**Repli** : jouer une catégorie à la fois plutôt que le banc entier ; sur une
limite de débit atteinte, attendre la remise à zéro plutôt que relancer (une
relance paie les mêmes sessions deux fois).

## Fiche — FileBrowser Quantum

**Quota ou coût** : aucun quota, l'outil est auto-hébergé (image
`gtstef/filebrowser`, version `1.5-stable-slim`, relevée le 2026-10-01).

**Pièges datés** :

- **2026-10-01** : avec l'authentification par proxy (`auth.methods.proxy`),
  le compte nommé dans `auth.adminUsername` est créé à la **première
  connexion**, avec `admin: true` mais **sans droit d'écriture** (`create`,
  `modify`, `delete` à `false`). Un administrateur qui ne peut pas téléverser.
- **2026-10-01** : changer les droits d'un compte ne change **pas** l'interface
  déjà ouverte. Les droits sont figés dans la session : les boutons de
  téléversement n'apparaissent qu'après une **nouvelle connexion**, même après
  un rechargement forcé de la page.
- **2026-10-01** : la doc de l'API (`/swagger/…`) répond `403` par défaut. Le
  format des appels se lit dans le source de la version installée
  (`backend/http/users.go` pour les comptes).
- **2026-10-01** : la page d'accueil répond `200` sans authentification (une
  coquille statique) ; seule l'API répond `401`. Une sonde sur `/` ne prouve
  donc pas que l'accès est fermé : sonder `/api/resources`.

**Bonne pratique** :

- Donner les droits par l'API, juste après la première connexion :
  `PUT /api/users?id=<n>` avec `{"which": ["Permissions"], "data": <le compte
  relu, droits modifiés>}`, puis relire le compte.
- Dans toute étape qui change des droits, prévoir « se déconnecter et se
  reconnecter » dans la preuve de fin.
- Laisser `share` à `false` derrière un portail d'identité : un lien de partage
  ouvre un fichier sans passer par le portail.

**Repli** : aucun connu au 2026-10-01.

## Fiche — Cloudflare Zero Trust (tunnel et Access)

**Quota ou coût** : aucun quota rencontré au 2026-10-01 pour un tunnel et
quelques applications Access.

**Pièges datés** :

- **2026-10-01** : le réglage « Protect with Access » d'une route de tunnel
  s'appelle désormais **« Enforce Access JSON Web Token (JWT) validation »**
  (Tunnels › route › Access). L'application Access se **choisit dans une
  liste** : l'équipe et l'AUD sont remplis seuls, il n'y a plus de champ à
  saisir. Une procédure écrite avec les anciens libellés égare.
- **2026-10-01** : sans ce réglage, `cloudflared` transmet tout à l'origine
  sans vérifier le jeton : un service qui fait confiance à l'en-tête
  d'identité d'Access dépend alors du seul portail.

**Bonne pratique** :

- Vérifier côté machine, pas seulement en console : `curl -s
  http://127.0.0.1:<port-metrics>/config` montre, pour chaque route,
  `originRequest.access` avec `required`, `teamName` et `audTag`.
- Pour une origine qui fait confiance à l'en-tête d'identité, activer la
  validation du jeton **et** faire écraser l'en-tête par le proxy (jamais
  transmis tel que reçu du client).

**Repli** : désactiver la validation du jeton sur la route rend le comportement
précédent, sans redémarrage.
