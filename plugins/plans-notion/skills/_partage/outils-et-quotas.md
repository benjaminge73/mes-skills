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
- **2026-10-08 : la clé d'API n'est pas dans l'environnement d'une session
  Claude Code.** Elle vit dans le `.env` du dépôt applicatif, qu'une session ne
  lit pas sans l'accord de Benjamin. Une passe Jev prévue dans un plan exécuté
  en autonomie s'arrête donc net, au milieu de l'étape.

**Bonne pratique** :

- **Une description par appel.**
- **Trancher avant l'exécution comment la clé arrive au processus** dès qu'une
  étape appelle Jev : `.env` chargé dans le seul processus Jev (sans jamais
  afficher la valeur), ou commandes lancées par Benjamin.

**Repli** : pour la clé absente, faire lancer les commandes Jev par Benjamin.
Pour le reste, aucun connu au 2026-10-08.

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
- **2026-10-08 : la prose d'un guide imprimé, refusée ou résumée au hasard.**
  Des sous-agents Haiku 5.5 chargés de recopier mot à mot des pages de guide
  (lues sur image) ont refusé ou résumé la prose au nom du droit d'auteur, au
  hasard d'un lot à l'autre. Sur 12 lots de 3 pages : 3 complets, 8 résumés,
  1 refus. Les champs pratiques (adresses, horaires) étaient recopiés partout.
  Le rapport entre les mots rendus et les mots de la page ne sépare pas un lot
  complet d'un lot résumé (0,29 à 0,61 contre 0,11 à 0,63). Le même
  comportement est consigné pour Sonnet, sans mesure chiffrée.

**Bonne pratique** :

- Rester en deçà d'une vingtaine d'appels `Agent` simultanés (`vagues.md`,
  section « Le plafond de concurrence »).
- Ne pas bâtir une étape sur la recopie intégrale de prose publiée par un
  modèle : lui faire rendre la structure, et recopier le texte par le code
  depuis une source numérique (epub). À défaut, contrôler chaque mot rendu par
  un garde déterministe, jamais par un ratio de longueur.

**Repli** : attendre la remise à zéro (00 h 30 UTC après le 429 de 23 h UTC).

## Fiche — Connecteurs MCP d'une session Claude Code (Notion, Composio)

**Quota ou coût** : aucun quota rencontré au 2026-10-08. Le repli par Hermes
coûte, lui, les tokens du modèle d'Hermes : une session Hermes par écriture.

**Pièges datés** :

- **2026-10-08, en soirée : tous les appels MCP de la session échouent avant
  de partir.** Notion, Composio et le suivi de PR de l'app répondaient
  « host client may be unreachable » et « The tool call was not executed » :
  un hook `PreToolUse` de l'hôte ne répondait plus. L'outil n'était pas en
  cause et relancer ne changeait rien. Les commandes `Bash` passaient
  toujours, ce qui a ouvert le repli ci-dessous.
- **2026-10-08** : par `COMPOSIO_MULTI_EXECUTE_TOOL`, la sortie d'une lecture
  de blocs Notion volumineuse (`…FETCH_BLOCK_CONTENTS`) revient élidée : une
  page longue ne se relève pas par ce chemin. Le workbench, lui, la rend.
- **2026-10-08** : un `hermes chat` borné à 300 s a expiré sur une écriture
  Notion ; 900 s ont suffi.

**Bonne pratique** :

- **Lire le message d'erreur avant de conclure.** S'il nomme le hook et dit
  que l'appel n'est pas parti, la panne est entre la session et l'hôte :
  passer au repli plutôt qu'attendre.
- **Le pilote écrit lui-même le code** que le workbench exécutera, contenu à
  écrire compris. Hermes ne fait que le transmettre : jamais lui demander de
  rédiger ou de reformuler.
- **Verrouiller le contenu par une empreinte sha256**, calculée en local et
  vérifiée par le code distant avant toute écriture, qui s'arrête si elle
  diffère. Un modèle intermédiaire peut retoucher un texte ; l'empreinte
  prouve qu'il ne l'a pas fait.
- **Relire le code réellement envoyé** dans la base d'état d'Hermes
  (`state.db`, table `messages`, arguments des appels d'outils), pas le récit
  qu'Hermes en fait. Ses grosses sorties sont dans son dossier de débordement
  (`cache/spillover/`).
- Recompter après l'écriture, en relisant la page, comme avec le connecteur
  direct (`ecrire-dans-notion.md`).

**Repli** : `hermes chat --query-file <consigne>`, avec un délai d'au moins
900 s ; Hermes appelle son propre Composio, `COMPOSIO_REMOTE_WORKBENCH`, dont le
code joue `proxy_execute(method, endpoint="/v1/…", toolkit="notion", body=…)`
vers l'API Notion.

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
- **Une fumée reprise du cache ne coûte rien** (depuis le 2026-10-08). Le job
  `fumee` garde le vert de chaque catégorie sous une clé (fichiers exercés, cas,
  plancher, modèle, effort, version de Claude Code, lanceur) : tant que la clé ne
  change pas, la catégorie n'est pas rejouée, soit 0 $ au lieu de 0,54 à 2,38 $ pour
  elle. Seul un vert est gardé : un rouge se rejoue à chaque push. Le résumé du job
  dit « fumée reprise du cache ».
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
- **2026-10-06** : le lanceur laisse des dossiers `tmp.*` sous `/tmp` (avec
  `--keep-temp`), dont des sous-dossiers en mode `000` qu'un `rm -r` simple ne
  retire pas. Les relever et les retirer à la clôture, après accord : ils
  peuvent contenir des sorties de cas.

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

## Fiche — Hermes Agent (cron et hub de skills)

**Quota ou coût** (mesuré le 2026-10-06) : aucun quota propre. Un passage de
job qui réveille l'agent coûte les tokens du modèle du job : un passage de
veille silencieux (6 appels modèle, 5 outils) a coûté environ 350 k tokens
d'entrée cumulés, cache à environ 98 %, en 46 s.

**Pièges datés** :

- **2026-10-06** : avec `cron create … --deliver local`, la livraison `local`
  n'archive que la sortie, **l'alerte d'échec comprise**. Sans
  `--failure-deliver <cible>`, un job qui finit en code 1 ou 2 ne prévient
  personne.
- **2026-10-06** : la limite `repeat` compte **chaque passage**, y compris ceux
  où le pré-script rend `{"wakeAgent": false}` (aucun appel modèle). Une limite
  calculée pour une cadence (un passage par jour) devient fausse quand la
  planification change : passée à toutes les 2 h, elle aurait éteint le job
  environ 12 fois plus tôt.
- **2026-10-06** : `hermes cron run <job>` joue d'abord le pré-script. Hors de
  sa fenêtre, le passage manuel n'est qu'une porte fermée
  (`wakeAgent=false`) et ne prouve rien du chemin agent.
- **2026-10-06** : `hermes skills inspect|install <owner>/<repo>/<skill>`
  résout d'abord par l'index public skills.sh quand le dépôt y est indexé,
  avant le tap GitHub du profil. Seul l'identifiant au chemin complet
  `<owner>/<repo>/<chemin>/<skill>` installe depuis le tap.

**Bonne pratique** :

- Poser `--failure-deliver` systématiquement avec `--deliver local`.
- Recalculer, ou retirer (`--repeat 0` : 0 vaut « sans limite » ; `forever`
  est refusé, l'option n'accepte qu'un entier), la limite à chaque changement
  de planification ; pour borner un job dans le temps, préférer un pré-script
  qui se tait à une limite.
- Sauvegarder l'entrée du job (`cron/jobs.json` du profil) avant un
  `cron edit`.
- Après un `--prompt "$(sed …)"`, comparer le prompt stocké au fichier source.
- Pour tester le chemin agent d'un job à pré-script : pointer le job, le temps
  d'un passage, vers un script d'enrobage qui appelle le pré-script avec un
  instant forcé, et rétablir le script d'origine par un `trap` dans le même
  appel de shell.

**Repli** : pour le hub de skills, l'identifiant au chemin complet ; sinon
aucun connu au 2026-10-06.

## Fiche — Chromium (snap) et Chrome headless

**Quota ou coût** : aucun, l'outil est local.

**Pièges datés** :

- **2026-10-06** : le Chromium d'Ubuntu est un snap confiné (AppArmor). Il ne
  lit ni n'écrit que sous les dossiers du répertoire personnel dont le nom ne
  commence ni par `.` ni par `s`. `/tmp`, `~/.cache` et un dossier caché sont
  refusés, et `--screenshot` vers un tel dossier **ne produit aucun fichier,
  sans erreur**.
- **2026-10-06** : sur les runners GitHub `ubuntu-latest` (24.04), Chrome
  headless refuse en général de démarrer avec son bac à sable (restriction
  AppArmor des espaces de noms utilisateur).

**Bonne pratique** :

- Écrire la sortie et les captures dans un dossier de travail sous le
  répertoire personnel, non caché.
- Désactiver le bac à sable **seulement en CI**, par une variable
  d'environnement explicite du job, jamais en dur dans le script.

**Repli** : aucun connu au 2026-10-06.

## Fiche — PyMuPDF

**Quota ou coût** : aucun.

**Pièges datés** :

- **2026-10-06** : en 1.28, `import fitz` imprime un avertissement de
  dépréciation **sur la sortie standard**. Un script qui rend du JSON sur
  stdout devient illisible (`JSONDecodeError` chez l'appelant). Constaté
  seulement dans un venv neuf : un venv plus ancien ne le montrait pas.

**Bonne pratique** :

- Écrire `import pymupdf`.
- Prouver un script sur un venv neuf, installé depuis ses `requirements`.

**Repli** : aucun connu au 2026-10-06.

## Fiche — Claude Code (CLI `claude`) sur un serveur à plusieurs comptes

**Quota ou coût** : celui de l'abonnement du compte connecté, voir la fiche
« Sessions Claude ». Rien de propre à l'installation (relevé au 2026-10-09).

**Pièges datés** :

- **2026-10-09 : `claude` invisible pour les comptes de service.** Installé par
  npm sous nvm, le binaire vit dans le dossier personnel de l'utilisateur qui
  l'a installé. Un autre compte Unix (service, unité systemd) ne le trouve pas :
  « command not found » au premier `/login`, alors que le plan supposait
  seulement une connexion à faire.
- **2026-10-09 : le paquet apt ne se met pas à jour seul.** Anthropic publie un
  dépôt apt signé (canaux `stable` et `latest`, page officielle d'installation).
  Mais `unattended-upgrades` n'autorise par défaut que les origines de la
  distribution : un paquet venu de ce dépôt reste figé tant que personne ne lance
  `apt upgrade`.
- **2026-10-09 : un e2e qui appelle `claude` échoue sous `sudo`.** `sudo`
  remplace `PATH` par son `secure_path` (le binaire n'y est plus), puis, une fois
  le chemin donné, `HOME` pointe sur `/root`, où aucune connexion n'existe :
  l'appel rend une sortie vide ou « Not logged in ». Le code n'y est pour rien.
- **2026-10-09 : `claude setup-token` n'enregistre rien.** Il affiche un jeton
  longue durée, à ranger soi-même (variable d'environnement). Sur un compte qui
  doit lancer `claude -p` sans surveillance, `/login` dans une session interactive
  enregistre les identifiants du compte et les renouvelle seul.

**Bonne pratique** :

- Sur un serveur, installer par le dépôt apt officiel (`/usr/bin/claude`, visible
  de tous les comptes), après avoir comparé l'empreinte de la clé à celle publiée
  par la page d'installation.
- Prouver, dès l'ouverture d'un plan, que chaque compte qui lancera `claude` le
  trouve : `sudo -u <compte> -i claude --version`.
- Connecter chaque compte par `/login`. Vérifier par un appel minimal
  (`claude -p … --model haiku`) sous ce compte, sans jamais lire son fichier
  d'identifiants.
- Jouer un e2e qui appelle `claude` sous le compte qui porte la connexion, pas
  sous `sudo`. Ne charger par `sudo` que les tests qui ont besoin d'un fichier
  de secrets réservé à root.

**Repli** : mise à jour à la main, `sudo apt update && sudo apt upgrade
claude-code`, en attendant qu'une origine autorisée ou un veilleur s'en charge.
