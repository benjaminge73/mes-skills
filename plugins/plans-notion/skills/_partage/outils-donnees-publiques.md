# Le registre des outils : données publiques, géographie, médias et crypto

Fiches du registre `outils-et-quotas.md` (fichier d'entrée : règles générales et index des fiches). Ce fichier porte les API de données publiques (lieux, géocodage, photos, actualités) et les sources de marché crypto (DexScreener, RPC Solana, GeckoTerminal, PumpPortal). Il se lit quand un plan touche l'une de ces sources ; les règles générales sont dans `outils-et-quotas.md`.

Sommaire :

- Fiche — Google Places
- Fiche — Nominatim, Photon et Overpass
- Fiche — Jev
- Fiche — Wikimedia Commons (photos téléchargées pour un usage hors ligne)
- Fiche — DexScreener
- Fiche — RPC public Solana
- Fiche — GeckoTerminal
- Fiche — PumpPortal
- Fiche — GDELT

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
- **2026-10-09** : une notation ciblée de **40 appels**, une description par
  appel, Jev seul sans repli, ne rencontre aucun refus de quota.
- **Juge d'adoption (2026-10-16)** : question `noul` (« faut-il adopter cette
  source ? »), seuil fixe 0,5. **0,2 s par appel**, coût négligeable. Rejeu : **100 %
  de verdicts identiques**. Accord de **90 %** avec une vérité étiquetée à l'aveugle
  sur 20 fiches, et **0 fausse adoption** sur 20 fiches dures (injections, pièges), dans
  un jeu de 40 fiches construit le même jour. Il ne rend aucune justification.
- **Jury Jev + Opus (2026-10-16)** : deux passes, à l'unanimité, avec deux fiches
  pièges (« canaris ») mêlées à chaque passe. **8 canaris refusés sur 8**, une bonne
  fiche adoptée **2/2**, en ≈ 50 s pour ≈ 0,14 $ (12 appels).

**Pièges datés** :

- **Un lot de 35 descriptions dans un seul appel rend des notes
  constantes** : mesuré, **AUC de 0,49**, soit le hasard (0,5).
- **2026-10-08 : la clé d'API n'est pas dans l'environnement d'une session
  Claude Code.** Elle vit dans le `.env` du dépôt applicatif, qu'une session ne
  lit pas sans l'accord de Benjamin. Une passe Jev prévue dans un plan exécuté
  en autonomie s'arrête donc net, au milieu de l'étape.
- **2026-10-15 : Jev écarté pour juger de la documentation.** Sur un jeu de
  100 passages de documentation étiquetés à l'aveugle (95 exacts, 3 fautes,
  2 indécidables), **AUC de 0,370** contre **0,858** pour Haiku, sur le même
  jeu. Pour rattraper les 3 fautes, le seuil de Jev doit descendre à 0,32 (la
  plus basse des trois notes de faute) ; à ce seuil, il signale **88 passages
  exacts sur 95**, contre **22 sur 95** pour Haiku. Ne pas l'utiliser pour ce
  terrain : il ne sépare plus les bons passages des fautes.
- **2026-10-16 : Jev juge bien la conformité d'une source à une règle.** Sur
  40 fiches de sources construites (20 à adopter, 20 à refuser, dont 14
  d'injection ou de piège), la moyenne de deux passes sépare parfaitement les
  bonnes des mauvaises (**AUC de 1,0**, seuil fixe 0,5), avec 2 bonnes sources
  sous le seuil. Le piège du 2026-10-15 ne vaut donc pas pour tout usage :
  Jev juge ici la **conformité**, pas la **qualité d'un texte**. Une réponse
  hors schéma ou une panne compte comme un refus.
- **2026-10-16 : la fiche à juger reste du texte marqué comme donnée.** Elle se passe
  comme donnée à évaluer, jamais comme consigne au juge.

**Bonne pratique** :

- **Une description par appel.**
- **Trancher avant l'exécution comment la clé arrive au processus** dès qu'une
  étape appelle Jev : `.env` chargé dans le seul processus Jev (sans jamais
  afficher la valeur), ou commandes lancées par Benjamin.
- **Mêler deux canaris à chaque passe d'un jury** : le refus des canaris se vérifie
  à chaque passe (8 sur 8 le 2026-10-16), sans quoi un jury qui adopte tout passerait
  inaperçu.

**Repli** : pour la clé absente, faire lancer les commandes Jev par Benjamin.
Pour juger de la documentation, ne pas utiliser Jev (piège du 2026-10-15) :
`qualite-doc.py juger` passe par Haiku. Pour le reste, aucun connu au 2026-10-08.

## Fiche — Wikimedia Commons (photos téléchargées pour un usage hors ligne)

**Quota ou coût** : gratuit. Aucun quota chiffré relevé au 2026-10-09 ; les
refus arrivent en 429 (limite de débit) ou 503.

**Pièges datés** :

- **2026-10-09 : des photos manquent au téléchargement hors ligne, même après
  reprises.** À 4 requêtes simultanées, avec jusqu'à 5 reprises par URL sur
  429/503 (attente doublée à chaque fois, plafonnée à 30 s) : **8 photos sur 55**
  en échec final. Sur le même lot, les tuiles de carte (CARTO) ne perdent que
  2 URL sur 5 358.

**Bonne pratique** :

- Compter les échecs et les rapporter, plutôt que de les masquer : un poids
  hors ligne mesuré avec des trous se nomme comme tel.
- Ne pas monter la concurrence pour gagner du temps : c'est elle qui déclenche
  les refus.

**Repli** : relancer la mesure plus tard, le cache garde ce qui est déjà
téléchargé (reprise gratuite). Aucun autre connu au 2026-10-09.

## Fiche — DexScreener

**Quota ou coût** (relevé au 2026-10-21) : gratuit. La réponse ne porte aucun
en-tête de limite.

- Le point `/tokens/v1/solana/<adresses>` accepte **jusqu'à 30 adresses par
  appel**. Mesure du 2026-10-21 : HTTP 200 en 0,09 s, 30 jetons sur 30 rendus.
- Limite publiée : **60 requêtes par minute**, mais seulement pour
  `/token-boosts/latest/v1`, `/token-boosts/top/v1` et
  `/token-profiles/latest/v1`. Rien n'est publié pour `/tokens/v1`.
- Conditions (`docs.dexscreener.com/api/api-terms-and-conditions`, version du
  2023-08-18) : licence limitée et révocable ; usage commercial et non commercial
  permis ; **redistribution du service interdite** ; la limite du plan gratuit
  n'est affichée qu'« au checkout », pas dans les conditions.

**Pièges datés** :

- **2026-10-21 : une paire existante n'est pas un jeton vivant.** Sur 30 jetons
  diplômés il y a 24 à 48 h, 24 ont encore une paire, mais **6 seulement ont eu un
  échange dans l'heure**. Les liquidités restent typiquement autour de 2 000 USD
  même sans échange : la liquidité ne dit pas si un jeton vit, l'activité
  (`txns`) si.
- **2026-10-21 : tous les jetons n'ont pas de paire `pumpswap`.** Sur les 30,
  28 en ont une ; prix, liquidité et volume ne sont présents que sur 27 de ces
  28 paires. Un champ absent se traite comme une donnée manquante, jamais comme
  un zéro.
- **2026-10-21 : aucun compteur de quota dans la réponse.** Le nombre d'appels
  se tient soi-même ; l'en-tête ne le dira pas.

**Bonne pratique** :

- Regrouper les adresses par tranches de 30 : un appel par tranche, pas un par
  jeton.
- Lire `pairCreatedAt` et `txns` avant la liquidité pour décider si un jeton vit.
- Ne pas republier les réponses brutes : les conditions interdisent de
  redistribuer le service.

**Repli** : sur un 429, doubler l'attente à chaque refus. La durée de la première
attente n'est pas mesurée au 2026-10-21.

## Fiche — RPC public Solana

**Quota ou coût** (relevé au 2026-10-21) : gratuit, mais **« not intended for
production »** selon la documentation officielle de Solana. Limite publiée :
**100 requêtes par 10 secondes et par adresse IP**. Point d'accès :
`wss://api.mainnet-beta.solana.com`.

**Pièges datés** :

- **2026-10-21 : un abonnement qui tient n'est pas un abonnement sobre.** Un
  `logsSubscribe` sur le programme PumpSwap
  (`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`) n'a subi aucune coupure, mais
  a reçu **25 831 messages et 80 Mo en 70 secondes**, soit environ 1,1 Mo/s. Le
  coût est dans le volume de messages, pas dans le nombre d'appels.

**Bonne pratique** :

- Ne pas s'abonner aux journaux d'un programme à fort débit sur le RPC public.
- Pour un prix de jeton, lire DexScreener (fiche ci-dessus) plutôt que le flux de
  journaux.

**Repli** : DexScreener pour les prix. Un RPC payant ou dédié seulement si le
besoin ne se couvre pas autrement. Aucun RPC payant n'a été essayé au
2026-10-21.

## Fiche — GeckoTerminal

**Quota ou coût** (relevé au 2026-10-21, d'après la page d'aide de CoinGecko) :
**30 appels par minute** en gratuit. Le consommateur qui l'interroge (listes
`pool_nouveau` et `pool_tendance`) appelle toutes les **300 secondes** : bien
sous cette limite.

**Pièges datés** :

- **2026-10-21 : pour un jeton diplômé, GeckoTerminal rend le pool de la courbe
  pump.fun, pas le pool PumpSwap.** Un prix lu là est celui de la courbe, pas
  celui de l'échange où le jeton se négocie après sa migration.
- **2026-10-21 : la liquidité n'est relevée qu'une fois.** Un chiffre lu à la
  création du pool est un instantané, il ne suit pas le pool.

**Bonne pratique** :

- Vérifier le DEX de la paire rendue (pump.fun ou PumpSwap) avant de lire son
  prix.
- Relever la liquidité à chaque cycle si une décision s'appuie dessus.

**Repli** : aucun repli mesuré au 2026-10-21 sur GeckoTerminal. Pour le prix d'un
jeton migré, DexScreener rend la paire PumpSwap (fiche ci-dessus) ; ce n'est pas un
essai de substitution sur le même jeu de jetons.

## Fiche — PumpPortal

**Quota ou coût** (relevé au 2026-10-21) :

- **Migrations : gratuites.** Environ 6 394 migrations sur 7 jours.
- **Flux des échanges : payant**, 0,01 SOL pour 10 000 messages. Il est donc
  exclu.

**Pièges datés** :

- **2026-10-21 : la charge d'une migration ne porte pas l'adresse du pool.** Elle
  porte `signature`, `mint`, `txType` et `pool = "pump-amm"`. Or `pump-amm` est le
  nom d'un pool, pas son adresse : qui veut la paire doit la retrouver ailleurs.

**Bonne pratique** :

- Lire `pool = "pump-amm"` comme la marque d'une migration vers PumpSwap, et
  chercher la paire par `mint`.
- Ne pas supposer un flux d'échanges gratuit : le seul mesuré est payant.

**Repli** : pour retrouver la paire d'un `mint`, DexScreener (fiche ci-dessus), non
mesuré sur ce flux au 2026-10-21. Pour les échanges, aucun flux gratuit mesuré ; on
lit l'activité par `txns` de DexScreener, qui n'est pas le même flux.

## Fiche — GDELT

**Quota ou coût** (relevé au 2026-10-21) :

- **Gratuit, sans limite annoncée** : licence « unlimited and unrestricted use …
  without fee » (`gdeltproject.org/about.html`). Condition : toute utilisation ou
  redistribution doit **citer le GDELT Project avec un lien vers
  `https://www.gdeltproject.org/`**.
- **L'API de recherche (`doc/geo`) refuse** : HTTP 429 deux fois de suite depuis le
  VPS, le 2026-10-21.
- **Les fichiers publiés toutes les 15 minutes** se téléchargent sans refus. Pour
  le seul fichier GKG (articles, thèmes, tons) : 6,1 Mo compressé par créneau,
  soit **environ 585 Mo par jour** (96 créneaux × 6,1 Mo, calcul).

**Pièges datés** :

- **2026-10-21 : le créneau annoncé peut ne pas exister encore.** L'index
  `lastupdate.txt` annonce le créneau courant ; le fichier qu'il désigne a rendu
  404. Le créneau précédent se lit par son nom.
- **2026-10-21 : `lastupdate.txt` en http redirige vers https.** Appeler directement
  l'adresse https.
- **2026-10-21 : une recherche par sous-chaîne ramène du bruit.** Sur le fichier GKG
  du 2026-10-21 à 14 h UTC (1 354 articles), une recherche par simple sous-chaîne
  sur les mots crypto (dont « ether ») rend 21 articles ; 6 à 10 seulement sont
  vrais. « ether » tombe dans « whether », et le thème `ECON_BITCOIN` est posé
  sur des articles hors sujet.

**Bonne pratique** :

- Lire le titre dans la balise `PAGE_TITLE` de la colonne `V2EXTRASXML`, et le ton
  dans le premier nombre de `V1.5TONE` (de −100 à +100). Le fichier compte
  27 colonnes.
- Filtrer par mot entier, jamais par sous-chaîne, et ne pas tenir un thème pour une
  preuve de pertinence : le titre tranche.
- Vérifier la taille et le md5 annoncés dans l'index avant de décompresser un
  fichier.

**Repli** : sur un 429 de `doc/geo`, lire les fichiers GKG créneau par créneau : ils
ne refusent pas au 2026-10-21. Le délai de reprise de l'API n'est pas mesuré.
