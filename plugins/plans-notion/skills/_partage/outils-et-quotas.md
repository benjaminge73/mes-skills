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
- **2026-10-09 : la PR qu'une CI merge seule, refusée par le classifieur de
  permissions.** Un `gh pr create --label <label d'auto-merge>` en fin
  d'exécution autonome est refusé (« Merge Without Review »), alors que la
  demande avait été écrite d'avance par l'utilisateur. La même commande passe
  quand la demande figure dans son message du tour. Depuis le 2026-10-14, la
  clôture ouvre sa PR sans demande dans le tour (`remontee-sur-main.md`) : ce
  refus peut donc tomber à chaque clôture, et pas seulement sur une demande.
- **2026-10-15 : le coût mesuré de `qualite-doc.py juger`.** Une mesure de
  3 passages à 2 votes chacun, soit 6 appels, a coûté **0,0118 $** au total,
  soit environ **0,002 $ par vote**. Pour comparaison, un juge avec outils coûte
  0,86 $ par fichier relu (fiche « Claude Code (CLI `claude`) »), et un vote
  avec passage et extrait du diff environ 0,0034 $ (mesure de la preuve de
  concept, date de lecture non consignée). Le même jour, trois rejeux sur les
  3 fautes du jeu étiqueté, avec la grille livrée, en ont signalé 1 à 2 au seuil
  0,45 : la note d'un même passage varie d'environ 0,2 d'un appel à l'autre, le
  seuil de départ reste donc à recalibrer sur des passages étiquetés.

**Bonne pratique** :

- Juger une autre grille que la doc (2026-10-28) : `qualite-doc.py juger --grille <fichier>`
  remplace `grille-doc.md` par le fichier lu. L'entrée devient une liste d'éléments
  `{"id", "texte"}`, recopiés tels quels dans le prompt et le rapport ; les douteux
  sont rangés par `id`. Une grille illisible sort en code 2, sans repli sur `grille-doc.md`.
- Rester en deçà d'une vingtaine d'appels `Agent` simultanés (`vagues.md`,
  section « Le plafond de concurrence »).
- Ne pas bâtir une étape sur la recopie intégrale de prose publiée par un
  modèle : lui faire rendre la structure, et recopier le texte par le code
  depuis une source numérique (epub). À défaut, contrôler chaque mot rendu par
  un garde déterministe, jamais par un ratio de longueur.

**Repli** : attendre la remise à zéro (00 h 30 UTC après le 429 de 23 h UTC).
Pour une PR refusée par le classifieur : ne pas contourner (un merge local
aurait le même effet). La branche reste poussée ; le compte rendu donne la
commande `gh pr create` prête et dit à Benjamin que la PR attend sa décision.
`PR` reste vide et `Statut` reste `a merger`. Une PR déjà ouverte reste ouverte.

## Fiche — Abonnement Claude Max

**Quota ou coût** (relevé le 2026-10-12, sur la doc Claude Code et la page des
tarifs) : aucun chiffre officiel en tokens ni en heures n'est publié pour
l'abonnement. Le pourcentage d'utilisation affiché dans la ligne de statut n'est
pas un chiffre documenté : il n'est pas retenu comme mesure. Les chiffres
qu'on trouve chez des tiers sont écartés. L'abonnement ne facture pas en
dollars : les dollars des fiches sont l'équivalent au tarif de l'API, qui sert
à comparer les postes entre eux (même convention que « claude plugin eval »).
Les plafonds observés (429, limite hebdomadaire) sont dans la fiche « Sessions
Claude ».

**Pièges datés** : aucun connu au 2026-10-12 propre à l'abonnement.

**Bonne pratique** : ne pas estimer la consommation d'un plan en heures ni en
pourcentage de quota. On mesure en jetons (fiche « ccusage ») et on chiffre sur
la grille de tarifs du dépôt (`grille-tarifs.json`, relevée le 2026-10-12).

**Repli** : quand un quota d'abonnement bloque, attendre la remise à zéro
indiquée dans la fiche « Sessions Claude ».

## Fiche — ccusage (lecture des journaux de session)

**Quota ou coût** (appel d'essai du 2026-10-12, version épinglée 20.0.30) : pas
de quota, c'est un outil qui lit les journaux locaux de session. Ses jetons
recoupent les journaux au token près. Son `cost` vient d'une table de prix
LiteLLM, différente de la grille de tarifs du dépôt : sur une mesure de deux
sessions du 2026-10-12, ccusage annonçait 86,65 $ et la grille du dépôt, 80,14 $
pour les mêmes jetons. La cause de l'écart n'est pas isolée.

**Pièges datés** :

- **2026-10-12 : le `cost` de ccusage n'est pas le prix de l'API tel que le
  dépôt le compte.** Écart de 86,65 $ contre 80,14 $ sur deux sessions, cause non
  isolée. Un chiffre de ccusage ne se recopie pas dans un rapport de coût.
- **2026-10-12 : des noms de modèles qui ne sont pas tous des identifiants de la
  grille.** Les journaux portent `claude-sonnet-5` et `claude-sonnet-5-5`,
  `claude-opus-5` et `claude-opus-5-5`, puis `sonnet`, `opus`, `haiku` et des
  noms anciens. `claude-opus-5` peut désigner Opus 5, plus cher qu'Opus 5.5 : une
  ligne de ce nom ne se chiffre pas au tarif 5.5, elle reste « non chiffrée ».
- **2026-10-12 : écriture de cache non ventilée.** `cacheCreationTokens` est un
  total. L'écriture de 5 minutes et celle d'une heure ne se séparent que dans le
  journal brut, au champ `message.usage.cache_creation`.

**Bonne pratique** : installer la version épinglée (`npm i -g ccusage@20.0.30`),
ne prendre de ccusage que les jetons, et chiffrer sur la grille du dépôt
(`cout-plan.py` le fait). Le `cost` de ccusage ne sert pas de montant.

**Repli** : si ccusage est absent ou change de forme de sortie, `cout-plan.py`
s'arrête avec un message et le code 2, sans trace Python. Les jetons restent
lisibles dans les journaux bruts (`~/.claude/projects`, champ `message.usage`),
mais une somme brute compte deux fois les lignes répétées du streaming : elle ne
sert pas de chiffre sans dédoublonnage.

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
- **2026-10-09 : la même panne du hook, mais passagère.** Trois appels Notion de
  suite refusés (« did not respond before its timeout »), puis le connecteur
  repart seul après une dizaine de minutes. Pendant ce temps, l'outil Composio
  de la session elle-même répondait.
- **2026-10-09 : `notion-fetch` d'une grosse page dépasse le plafond de
  sortie** à partir d'environ 200 000 caractères. Rien n'est perdu : la réponse
  est enregistrée dans un fichier dont le message donne le chemin. C'est un JSON
  dont le champ `text` porte la page en Markdown.
- **2026-10-09** : une capture d'écran se joint à une page en deux temps,
  `notion-create-file-upload` puis un POST du fichier vers l'adresse rendue.
- **2026-10-10 : Notion et les outils Composio de la session tombent
  ensemble.** L'app est restée injoignable plus de vingt minutes, et les
  `mcp__<uuid>__COMPOSIO_*` ont expiré sur le même hook que Notion. Seule la
  commande `composio` du VPS (palier 2 ci-dessous) a tenu, en lecture comme en
  écriture. D'où le palier 2 hors de l'app, et non l'outil Composio de la
  session.
- **2026-10-20 : le connecteur Notion de l'app de bureau porte un nom en
  `uuid`.** Ses outils s'appellent `mcp__<uuid>__…`, et la liste d'outils d'un
  agent ne peut pas les prévoir : un agent ne cherche pas `notion-fetch` par son
  nom. Il regarde si un outil Notion figure dans sa liste ; sinon il passe au
  palier 2 sans attendre.
- **2026-10-20 : les commentaires ne se lisent pas d'un coup par le chemin
  `composio`.** `NOTION_FETCH_COMMENTS` prend un bloc à la fois : un relevé qui
  veut les fils fait un appel par bloc concerné, ou écrit « fils non relus
  (chemin composio) » et laisse le pilote les lire par `notion-get-comments`.

**Bonne pratique** :

- **Lire le message d'erreur avant de conclure.** S'il nomme le hook et dit
  que l'appel n'est pas parti, la panne est entre la session et l'hôte : suivre
  le repli ci-dessous (palier 1 réessayé, puis palier 2), sans conclure que
  Notion est en panne.
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

**Repli** : trois paliers, dans cet ordre. On ne passe au suivant que si le
précédent échoue, et le compte rendu dit lequel a posé l'écriture ou fourni la
lecture.

1. **Le connecteur Notion de la session.** Si l'appel est refusé par le hook
   (« did not respond before its timeout »), attendre une à deux minutes et
   réessayer le même appel, jusqu'à trois essais sur une dizaine de minutes.
   Rien n'est parti, donc pas de doublon. Pendant ce temps, avancer sur ce qui
   ne dépend pas de l'app.
2. **La commande `composio` du VPS**, en lecture et en écriture. Elle est
   installée à `~/.local/bin/composio` (lien vers `~/.composio/composio`, version
   0.4.0). Lecture : `echo '{"page_id":"<id>"}' | composio execute
   NOTION_GET_PAGE_MARKDOWN -d -` ; une grosse page revient dans un fichier
   (`storedInFile`, puis `outputFilePath`, champ `data.markdown`). Écriture de
   contenu : `composio execute NOTION_UPDATE_PAGE_MARKDOWN -d @args.json`, et
   d'une propriété : `NOTION_UPDATE_PAGE`. Le texte passe par un fichier, jamais
   recopié à la main ; `old_str` se construit par script, et les cases se
   recomptent après chaque écriture (`connecteurs-timeout-hook.md`). L'outil
   Composio de la session ne compte pas comme palier : il passe par le même
   relais que Notion et tombe avec lui.
3. **Hermes, au pilote seulement.** `hermes chat --query-file <consigne>`, avec
   un délai d'au moins 900 s ; Hermes appelle son propre Composio,
   `COMPOSIO_REMOTE_WORKBENCH`, dont le code joue `proxy_execute(method,
   endpoint="/v1/…", toolkit="notion", body=…)` vers l'API Notion. Le contenu
   est verrouillé par son empreinte sha256 (voir plus haut). Un agent ne lance
   jamais ce palier : un `hermes chat` dure jusqu'à 900 s et ouvre une session
   par écriture, il bloquerait une vague de sous-agents. Un agent qui atteint le
   palier 2 sans succès rend `BLOCKED` et laisse le texte prêt dans un fichier.

   **Reprendre un fichier d'arguments laissé par un agent.** Quand un agent rend
   `BLOCKED` avec un fichier prêt (un `args.json` pour `composio execute
   NOTION_UPDATE_PAGE_MARKDOWN -d @fichier`, ou une entrée de changelog sous
   `~/brouillons/<projet>/changelog/`), c'est le pilote qui le reprend, jamais
   l'agent. Le pilote calcule l'empreinte sha256 du fichier, puis charge Hermes,
   par le même `hermes chat --query-file` et le même délai, de jouer lui-même une
   seule commande sur ce chemin exact, qui vérifie l'empreinte juste avant
   l'envoi : `echo "<sha256>  <fichier>" | sha256sum -c - && composio execute
   <slug> -d @<fichier>`. Si l'empreinte diffère, `sha256sum -c` échoue et
   `composio` n'est jamais appelé : rien n'est envoyé. Même action, même fichier.
   La consigne interdit à Hermes d'ouvrir le fichier et de le recopier ; c'est
   `composio` qui le lit. Si malgré tout la page ne correspond pas au texte prévu
   après l'envoi, le pilote la relit, la compare au texte prévu et corrige par une
   nouvelle écriture ciblée, selon le protocole de `ecrire-dans-notion.md`, jamais
   en silence. Hermes rend le JSON de la réponse de `composio`, et le pilote relit
   la page et recompte les cases avant de tenir l'écriture pour faite.

   **Nuance : l'échec vient de Composio.** Si l'agent a rendu `BLOCKED` parce que
   Composio lui-même refuse (compte déconnecté ou expiré, refus de l'API), rejouer
   la même commande refera la même erreur. Le pilote le lit dans le message du
   `BLOCKED`. Dans ce cas, il ne rejoue pas la commande : il charge Hermes de
   passer par son workbench (`COMPOSIO_REMOTE_WORKBENCH` / `proxy_execute`, voie
   décrite plus haut dans ce palier), le code du workbench étant écrit par le
   pilote lui-même, comme le veut la bonne pratique plus haut, et l'empreinte
   vérifiée par ce code avant toute écriture.

Limite : `composio` est posé à la main sur le VPS, hors de la cascade
d'installation de `installer-un-outil.md`, sans manifeste ; rien ne le met à
jour. Une session cloud ne l'a pas : là-bas, on passe du palier 1 au palier 3.

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

- **Un passage est une session complète.** Chaque cas est joué 3 fois par bras.
  Le 2026-09-30, le banc comptait 16 cas : 16 × 3 = 48 sessions par bras. Il
  compte 26 cas au 2026-10-16, soit 26 × 3 = 78 sessions par bras. Une A/B joue
  deux bras (la base et la tête) : tout est à doubler. Le modèle joué est Sonnet,
  effort `high` ; la correction se fait par expressions régulières, sans
  modèle-juge, donc sans coût de juge.
- **Un bras complet coûtait 27,53 $ le 2026-09-30, sur 16 cas.** Un cas coûtait
  entre 0,98 $ et 3,57 $ à la même date. Une A/B sur tout le banc coûtait donc
  environ 55 $, et une A/B ciblée sur une catégorie 3 à 14 $ (chiffres du
  2026-09-30). Le coût d'un bras à 26 cas n'a pas été remesuré.
- **Par catégorie**, pour un bras de 3 passages, puis pour un seul passage (le
  coût d'une fumée), mesuré le 2026-09-30. La colonne « Cas au 2026-10-16 »
  donne le nombre de cas que chaque catégorie compte aujourd'hui :

| Catégorie | Cas au 2026-10-28 | Cas mesurés le 2026-09-30 | Un bras, 3 passages | Un passage |
|---|---|---|---|---|
| `existant` | 3 | 2 | 6,43 $ | 2,14 $ |
| `bruit` | 3 | 3 | 4,81 $ | 1,60 $ |
| `etat-de-depart` | 4 | 4 | 7,13 $ | 2,38 $ |
| `maquette` | 1 | 1 | 1,61 $ | 0,54 $ |
| `decouvertes` | 8 | 4 | 4,98 $ | 1,66 $ |
| `perimetre` | 4 | 2 | 2,56 $ | 0,85 $ |
| `delegation` | 1 | — | non mesuré | non mesuré |
| `preuves` | 9 | — | non mesuré | non mesuré |
| `revue-hors-plan` | 1 | — | non mesuré | non mesuré |
| `escalade-bornee` | 1 | — | non mesuré | non mesuré |
| **tout le banc** | 35 | 16 | 27,53 $ | ≈ 9,2 $ |

Les coûts datent du 2026-09-30 et ne sont extrapolés à aucune catégorie. Les
catégories `existant` et `decouvertes` ont gagné des cas depuis : elles coûtent
plus que leur ligne. `delegation`, `preuves`, `revue-hors-plan` et `escalade-bornee`
ne figuraient pas dans la mesure, et leur coût n'a jamais été mesuré. `tout le banc`
désigne le banc de `plans-notion` ; `voyages` en compte un de plus (`billet`), soit
27 cas au total.

Mesure postérieure pour `decouvertes` : la PR #60 (run `38881638080`, le
2026-10-16), à bras identiques puisqu'elle ne changeait aucun fichier du plugin.
6 cas × 3 passages × 2 bras, aucune session en erreur, 18,68 $ pour les deux
bras ensemble (montant brut, non divisé par deux).

- **Une A/A sur Opus** a coûté 53,14 $ : un bras de Sonnet coûte la moitié.
- **Une fumée reprise du cache ne coûte rien** (depuis le 2026-10-08). Le job
  `fumee` garde le vert de chaque catégorie sous une clé (fichiers exercés, cas,
  plancher, modèle, effort, version de Claude Code, lanceur) : tant que la clé ne
  change pas, la catégorie n'est pas rejouée, soit 0 $ au lieu de 0,54 à 2,38 $ pour
  elle. Seul un vert est gardé : un rouge se rejoue à chaque push. Le résumé du job
  dit « fumée reprise du cache ».
- **Le plafond par appel** (`EVALS_MAX_COUT_USD`) vaut 45 $ par bras. Il a été
  fixé sur une extrapolation, pas sur une mesure : le 2026-10-15, un bras de 23
  cas à ~39,6 $ (23 × le coût par cas mesuré le 2026-09-30), plus une marge
  d'environ 14 %. Le banc compte 26 cas au 2026-10-16 ; aucune
  nouvelle extrapolation n'est faite. Il valait 120 $ avant le 2026-10-01, puis
  35 $ du 2026-10-01 au 2026-10-15 : trop bas pour un passage complet du banc à
  23 cas, alors. Le 120 $ n'a jamais été atteint : il ne protégeait de rien.
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
- **2026-10-09** : la limite de session de l'abonnement, atteinte en cours de
  banc, fait sortir chaque passage suivant en erreur (`exit 1: You've hit your
  session limit · resets …`), à 0 $ et en une ou deux secondes. Le rapport, lui,
  n'est **pas** marqué `partial` : il a l'air complet. Un cas rejoué dans ces
  conditions a rendu trois passages à 0,17 sur trois, à remplacer après la
  remise à zéro (trois passages verts).
- **2026-10-09** : un appel arrêté par un signal (`kill -TERM`) écrit quand même
  son rapport, marqué `partial: true` et `partialReason: interrupted`, avec tous
  les passages finis. `evals_ab.py` refuse ce rapport tel quel (code 3), mais il
  se récupère : 26 passages sur 27 d'une base arrêtée à une heure de jeu.

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
- **Lire les erreurs, pas seulement `partial`.** Avant de se fier à un rapport,
  compter les passages dont `error` n'est pas nul : une limite de session ne se
  voit que là (piège du 2026-10-09).

**Repli** : jouer une catégorie à la fois plutôt que le banc entier ; sur une
limite de débit atteinte, attendre la remise à zéro plutôt que relancer (une
relance paie les mêmes sessions deux fois). **Un bras interrompu se complète
au lieu de se rejouer** : rejouer seulement les cas manquants ou en erreur sur
la même copie du plugin (`evals/outillage/lancer.sh <copie> <sortie.json>
--case <cas> --runs 3`, même lanceur, même version de Claude Code), remplacer
ces cas dans le rapport partiel, retirer `partial`, puis le passer à
`evals_ab.py --base-rapport` ; `--estimer` vérifie qu'il est accepté.

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

## Fiche — Hermes Agent (cron, hub de skills, rendu Slack)

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
- **2026-10-12** : le rendu Slack d'Hermes a deux lecteurs de tableau Markdown,
  et ils ne lisent pas `\|` de la même façon. Le chemin par blocs riches
  (table native Block Kit, `plugins/platforms/slack/block_kit.py`, fonction
  `_split_row`) protège la barre échappée et l'affiche dans la cellule. Le
  chemin texte (`plugins/platforms/slack/adapter.py`, `_split_table_row`, appelé
  par `_align_table`) ne la protège pas : il coupe sur `\|`, le tableau gagne
  une colonne et la ligne se décale. Une cellule qui doit contenir une barre
  s'écrit donc avec `¦` à la place, que les deux lecteurs ne coupent pas.
- **2026-10-13** : `skills.external_dirs` n'a pas de précédence entre ses
  dossiers. Deux dossiers déclarés là qui portent un skill de même nom sont au
  même rang : Hermes ne les départage pas et masque les deux copies (état
  `ambiguous` du catalogue). Un skill posé au rang local (`~/.hermes/skills/`)
  l'emporte sur les externes.

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
- Dans un tableau destiné à Slack, remplacer la barre d'une cellule par `¦`
  plutôt que l'échapper en `\|` : seul un des deux lecteurs sait lire `\|`.
- Avant une étape qui change une configuration vivante comme `skills.external_dirs`,
  une sonde en lecture seule du catalogue réel de Hermes dit ce qu'il servira ;
  sans elle, l'étape écrite sur une précédence supposée a été défaite.

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
- **2026-10-13 : `claude --plugin-dir` cède à un plugin installé du même nom.**
  Un plugin déjà installé qui porte le même nom que le dossier passé par
  `--plugin-dir` masque ce dossier : la session charge la copie installée, pas le
  dossier de travail. Une preuve « mon hook de branche tourne » prouve alors la
  mauvaise copie.
- **2026-10-15 : `claude -p --model haiku` sert Haiku 4.5 hors des réglages
  utilisateur.** Lancé sans les réglages utilisateur du poste (c'est le cas de
  `qualite-doc.py juger`, avec `--setting-sources project`), l'alias `haiku` a
  servi **Haiku 4.5**, relevé dans `modelUsage` de la réponse JSON. Épingler
  l'identifiant complet `claude-haiku-5-5`, qui sert Haiku 5.5. `qualite-doc.py
  juger` vérifie le modèle servi dans `modelUsage` et sort en code 5 s'il
  n'est pas celui demandé.
- **2026-10-15 : un juge Haiku avec outils coûte 0,86 $ par fichier relu.**
  Un juge qui lit lui-même les fichiers (outils activés) a coûté **0,86 $**
  par fichier relu. Un vote sans outils, qui reçoit le passage et l'extrait du
  diff, coûte nettement moins (fiche « Sessions Claude », même date).
- **2026-10-16 : les connecteurs claude.ai du compte gonflent le contexte
  d'un appel `claude -p`.** Un appel Haiku sans outil, lancé sans
  `--strict-mcp-config`, a chargé **186 651 jetons** de contexte (1,51 $
  affichés) ; avec `--strict-mcp-config` (et `--setting-sources ""`), **8 984
  jetons** (0,023 $ affichés).
- **2026-10-16 : `claude -p` lit l'entrée standard et reste bloqué sans
  `< /dev/null`.** Lancé depuis un script ou un outil qui n'ouvre pas
  l'entrée standard, l'appel attend indéfiniment.
- **2026-10-16 : le coût affiché de `claude-haiku-5-5` n'est pas son tarif**
  (version 2.1.292, sur un compte de service : le modèle n'est pas reconnu par
  la table de prix de la CLI). Chiffrer un lot en **jetons lus × grille**, pas
  d'après `total_cost_usd`.
- **2026-10-16 : `sudo` ne transmet pas les variables d'environnement du
  pilote.** Un lanceur passé sous `sudo` perd, par exemple, un drapeau posé
  juste avant ; un lot a ainsi rejoué sa première passe à la place de la
  seconde. Le lanceur lit lui-même ce dont il a besoin, ou la variable est
  posée dans la commande sous `sudo`.
- **2026-10-16 : une CLI ancienne affiche un coût faux pour un modèle récent.** La
  CLI 2.1.292 ne reconnaît pas `claude-haiku-5-5` : avertissement
  `[claude-code:unrecognized_model]`, et coût affiché à un tarif faux, surévalué
  d'un facteur ≈ 4 (**1,446 $** affichés pour 147 000 jetons d'entrée et 32 000 de
  sortie, contre ≈ 0,35 $ à la grille). `--max-budget-usd` porte sur ce coût
  affiché : une exécution s'arrête en `error_max_budget_usd`, résultat nul, avant
  la fin, alors que la dépense réelle est faible.
- **2026-10-16 : un sous-agent ne reçoit que des outils présents dans la liste de
  la session parente.** Un outil absent de cette liste ne passe pas : la CLI répond
  « Agent would be spawned with zero tools ». La liste d'outils ne suffit donc pas
  à interdire la recherche web au seul parent.
- **2026-10-16 : un hook `PreToolUse` qui plante laisse passer l'outil.** Seul le
  code de sortie 2 bloque l'appel ; un plantage sort avec un autre code, et l'appel
  passe.
- **2026-10-16 : un sous-processus `asyncio` tué au délai peut pendre au `wait()`.**
  Si un enfant garde le tuyau de sortie ouvert, `kill()` puis `wait()` n'en finit
  pas.

**Bonne pratique** :

- Sur un serveur, installer par le dépôt apt officiel (`/usr/bin/claude`, visible
  de tous les comptes), après avoir comparé l'empreinte de la clé à celle publiée
  par la page d'installation.
- Prouver, dès l'ouverture d'un plan, que chaque compte qui lancera `claude` le
  trouve : `sudo -u <compte> -i claude --version`.
- Connecter chaque compte par `/login`. Vérifier par un appel minimal
  (`claude -p … --model claude-haiku-5-5`, identifiant complet : l'alias `haiku`
  peut servir une autre version, voir le piège du 2026-10-15) sous ce compte, sans
  jamais lire son fichier d'identifiants.
- Jouer un e2e qui appelle `claude` sous le compte qui porte la connexion, pas
  sous `sudo`. Ne charger par `sudo` que les tests qui ont besoin d'un fichier
  de secrets réservé à root.
- Prouver un hook ou un skill de branche avec une **copie renommée** du plugin
  (nom différent de celui qui est installé), jamais avec le dossier de travail sous
  son nom d'origine : la copie renommée n'entre pas en collision avec le plugin
  installé, donc rien ne la masque.
- Pour un appel de lot sans outil (jury, notation) : `--strict-mcp-config
  --setting-sources "" --no-session-persistence --max-budget-usd <plafond>
  --output-format json`, `--json-schema` pour une sortie contrainte, et
  `< /dev/null`. Ces options sont mesurées fonctionnelles au 2026-10-16
  (`--effort` aussi). Le plafond tient lieu de garde de dépense.
- **Un lot de votes en JSON** : `claude -p --json-schema … --output-format json` rend
  la réponse dans le champ `structured_output` de l'enveloppe. Mesure du 2026-10-16
  sur 80 appels d'Opus 5.5 : ≈ 8 s et ≈ 0,023 $ par vote. Un processus neuf par
  appel : aucun cache entre deux votes.
- **Plafond après un coût affiché faux** (2026-10-16) : chiffrer en jetons × grille ;
  régler `--max-budget-usd` à au moins **deux fois** le coût affiché observé ; mettre
  à jour la CLI du compte concerné.
- **Interdire un outil au parent seul** (2026-10-16) : un hook `PreToolUse` passé par
  `--settings` (pris en compte malgré `--setting-sources ""`) sort en code 2 quand
  l'entrée du hook n'a pas de `agent_id` : il refuse l'appel du parent et laisse
  passer celui du sous-agent. Mesure : 0 recherche du parent, 11 à 12 du sous-agent.
  Son interpréteur se donne par chemin absolu, et il attrape toute exception pour
  sortir en 2.
- **Depuis Python**, `subprocess.run(…, stdin=subprocess.DEVNULL)` ferme l'entrée
  standard de `claude -p` (2026-10-16) : même panne que ci-dessus, côté appelant.
- **Sous-processus `asyncio`** (2026-10-16) : le lancer avec `start_new_session=True`,
  tuer son groupe par `os.killpg`, et seulement ensuite `wait()`.

**Repli** : mise à jour à la main, `sudo apt update && sudo apt upgrade
claude-code`, en attendant qu'une origine autorisée ou un veilleur s'en charge.

## Fiche — codebase-memory (graphe de code, serveur MCP)

**Quota ou coût** : aucun quota, l'outil tourne en local (relevé au 2026-10-09).
Le coût est en appels et en contexte. Mesure du 2026-10-09 : une carte de
voisinage rejouée sur un plan de 24 étapes a pris **57 appels**, contre 3 à 6
annoncés pour un plan court. Le coût grandit avec le nombre d'étapes cartées.

**Pièges datés** :

- **2026-10-09 : le mode `moderate` n'indexe pas `scripts/` ni `docs/`.** Un
  `search_graph` ou un `trace_path` qui ne trouve rien dans ces dossiers ne
  prouve rien. Seul `check_index_coverage` sur le chemin le dit.
- **2026-10-09 : un appel par `importlib` est invisible.** La 0.10.8 le résout,
  la 0.11.0 ne le résout plus : un appelant chargé par `importlib` sort de
  `trace_path`. La version en service se relit avant de conclure « aucun
  appelant ».
- **2026-10-16 : la 0.12.0 ne le résout pas non plus.** Mesuré sur trois fichiers
  (une fonction, un appelant par import statique, un appelant qui charge le module par
  `importlib.util.spec_from_file_location` puis appelle `module.f()`) : 2 appelants en
  0.10.8, 1 en 0.11.0 et en 0.12.0. Ticket ouvert : `DeusData/codebase-memory-mcp#2659`.
- **2026-10-09 : une seule version à la fois sur la machine.** Une autre version
  refuse de démarrer (« conflicting CBM process is active »), même avec un
  `HOME` et un dossier de cache isolés. Pour en tester une, il faut un
  conteneur.
- **2026-10-09 (relevé) : le paramètre `project` n'est pas le nom court du dépôt.** C'est le chemin
  racine, `/` remplacé par `-`. Le copier depuis `list_projects`, jamais le
  deviner.

**Bonne pratique** :

- Les outils sont différés dans une session Claude Code : un `ToolSearch`
  d'abord, puis `index_repository` sur le dépôt (2 à 15 s) avant la carte, puis
  `list_projects`.
- Avant toute affirmation négative (« aucun appelant », « aucun test »),
  `check_index_coverage` sur chaque chemin cité.
- Pour les appelants : `trace_path` avec `direction: "inbound"` et
  `include_tests`, ce qui sort aussi les tests qui exercent le symbole.
- Borner la carte aux étapes à risque (contrat, signature, fichier partagé),
  pas à tout le plan (mesure de 57 appels ci-dessus).

**Repli** : `grep` ou l'agent `enqueteur`, qui lit les fichiers. Une ligne de
la carte que le graphe ne tranche pas devient une question, pas un fait.

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

## Fiche — maxTurns (limite de tours d'un sous-agent)

**Quota ou coût** : aucun quota. `maxTurns` est un plafond de tours posé dans le
frontmatter d'un sous-agent (doc lue le 2026-10-16,
`https://code.claude.com/docs/en/sub-agents.md`). Mesure rapportée par le pilote, le
2026-10-16, sur 14 jours d'exécutants : 676 exécutants, médiane 27 tours, 95e centile
73, maximum 158.

**Pièges datés** :

- **2026-10-16 : la marque « partielle » exige Claude Code v2.1.246 ou plus.** À la
  limite, la sortie d'un sous-agent est rendue marquée partielle ; sur une version plus
  ancienne, cette marque n'est pas posée.
- **2026-10-16 : un arrêt par la limite de tours n'est pas un échec.** La sortie
  partielle est reprenable. `executer-plan-notion` la reprend au même palier, soit par
  `SendMessage` à la même instance, soit par un nouvel appel dont le brief reprend le
  résultat partiel (`etapes.md`, « L'escalade bornée », règle 6). Ce n'est pas une montée.

**Bonne pratique** :

- Poser `maxTurns` dans le frontmatter de l'agent, sur une valeur mesurée sur ses sessions
  réelles (ici `90` pour `executant`), jamais sur une valeur devinée.
- Lire une sortie marquée partielle comme un arrêt à reprendre, pas comme une étape
  terminée.

**Repli** : reprendre le sous-agent par son nom ou son ID (`SendMessage`) pour qu'il
continue là où il s'est arrêté. Sur une version de Claude Code antérieure à la v2.1.246,
la marque « partielle » n'est pas posée : vérifier la version avant de s'y fier.

## Fiche — Claude Code Review (service hébergé)

**Quota ou coût** : **non lu.** Le tarif et le quota de Code Review n'ont pas été relus
au 2026-10-16 ; la page a une section tarif (ancre `#pricing`) qui ne figure pas dans ce
relevé. Plans : Team et Enterprise, sur dépôts GitHub (page lue le 2026-10-16,
`https://code.claude.com/docs/en/code-review.md`).

**Pièges datés** :

- **2026-10-16 : une revue ne bloque ni n'approuve la PR.** Les constats arrivent en
  commentaires en ligne, classés par gravité, avec un résumé et un check run ; la décision
  de merge reste à l'équipe. Un avis vert de Code Review n'est donc pas une approbation.
- **2026-10-16 : le service tourne sur l'infrastructure d'Anthropic**, et non sur le poste
  ni sur le VPS (colonne « Où il tourne » du tableau de la page).

**Bonne pratique** :

- Traiter ses constats comme des avis à lire ; la décision de merge reste humaine (la page
  le dit).
- Ne pas le tenir pour le `relecteur` de `plans-notion` : la page ne dit pas que Code Review
  reçoit l'objectif d'une étape, ce que le `relecteur` fait.

**Repli** : le `relecteur` de `plans-notion` (agent Opus, effort `high`), qui ne dépend pas
de ce service.

## Fiche — inspect_ai (banc d'évaluation Python)

**Quota ou coût** (relevé au 2026-10-16) : la bibliothèque est libre et ne
coûte rien par elle-même ; le coût est celui des appels de modèle qu'elle
lance. Version lue : 0.3.281.

**Pièges datés** :

- **2026-10-16 : un fournisseur de modèle maison (`@modelapi`) qui garde un
  client HTTP ne survit pas à une seconde évaluation.** Deux évaluations
  successives dans le même processus tournent chacune dans une boucle
  d'événements neuve ; un client créé pour la première échoue sur la seconde
  (`Event loop is closed`). Il faut construire le client **par boucle
  d'événements**.
- **2026-10-16 : `uv` absent du poste.** L'installation passe par `pip` dans un
  environnement virtuel à usage unique ; la version posée peut différer d'un cran
  de celle que la doc cite.

**Bonne pratique** : écrire les jeux et leurs étiquettes avant tout appel, en
poser les empreintes (`sha256`) dans un fichier, tenir un journal par appel
(modèle, jetons, coût grille, latence) et ne dépouiller qu'avec des définitions
de réussite fixées avant de lire les résultats. Supprimer l'environnement et les
journaux d'`inspect` à la fin ; garder jeux, empreintes et résultats.

**Repli** : un script direct qui appelle chaque modèle, sans `inspect_ai`, quand
le banc n'a qu'un jeu et deux juges.

## Fiche — Cage d'une source codée (bwrap, AppArmor, srt, systemd)

**Quota ou coût** : aucun. Ce sont des outils locaux (relevé en 2026-10). Chacun
des faits ci-dessous se vérifie par une commande, pas par la documentation seule.

**Pièges datés** :

- **2026-10 : `RuntimeMaxSec` est ignoré pour un service `Type=oneshot`.** Le
  réglage n'a aucun effet sur un tel service : une durée bornée par lui n'est
  pas bornée.
- **2026-10 : une restriction de familles d'adresses qui omet `AF_NETLINK`
  casse `bwrap --unshare-net`.** `systemd-run --user -p
  RestrictAddressFamilies=… /usr/bin/bwrap …` reproduit une restriction de
  familles d'adresses, mais `AF_NETLINK` doit rester dans la liste : sans lui,
  `bwrap --unshare-net` ne se lance pas.
- **2026-10, Ubuntu 26.04 : `apt install nodejs` n'installe pas `npm`.** Et le
  PATH de `sudo` ne voit pas le `npm` de l'utilisateur : une commande npm lancée
  sous `sudo` échoue même quand `npm` est présent sous le compte.

**Bonne pratique** :

- **Valider un profil AppArmor sans root** : `apparmor_parser -K -Q <profil>`
  valide le profil sans droits root et sans passer par le cache. La vérification
  se fait donc avant tout chargement, depuis un compte ordinaire.
- **Prouver une restriction par la commande, pas par le réglage seul** :
  `systemd-run --user -p RestrictAddressFamilies=… /usr/bin/bwrap …`, avec
  `AF_NETLINK` dans la liste si `bwrap --unshare-net` est utilisé.
- **Lancer les commandes npm sous le compte de l'utilisateur**, jamais sous
  `sudo`, et vérifier `npm --version` dans le même environnement que la commande.
- **srt 0.0.79 (relevé en 2026-10)** : le binaire bwrap se désigne par le
  réglage `bwrapPath`. Son proxy réseau fonctionne par liste blanche de domaines :
  un domaine absent de la liste est refusé. En ajouter un est une décision à
  prendre, pas un réglage à faire en passant.

**Repli** : pour un service `Type=oneshot` qui doit être borné dans le temps,
borner la durée dans la commande elle-même ; ce repli n'est pas mesuré dans cette
fiche. Si la restriction d'adresses casse `bwrap --unshare-net`, rétablir
`AF_NETLINK` dans la liste. Pour `npm` absent sous `sudo` : aucun repli mesuré au
2026-10, passer par le compte de l'utilisateur comme ci-dessus.

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
