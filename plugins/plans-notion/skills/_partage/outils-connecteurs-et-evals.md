# Le registre des outils : connecteurs MCP et bancs d'évaluation

Fiches du registre `outils-et-quotas.md` (fichier d'entrée : règles générales et index des fiches). Ce fichier porte la chaîne de repli des connecteurs Notion et Composio, et les deux bancs d'évaluation (`claude plugin eval`, `inspect_ai`). Il se lit quand un appel de connecteur échoue ou quand un plan chiffre le coût d'un banc ; les règles générales sont dans `outils-et-quotas.md`.

Sommaire :

- Fiche — Connecteurs MCP d'une session Claude Code (Notion, Composio)
- Fiche — claude plugin eval
- Fiche — inspect_ai (banc d'évaluation Python)

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
   installée à `~/.local/bin/composio` (lien vers le shim `mise`
   `~/.local/share/mise/shims/composio`, version 0.4.5 relevée le 2026-11-19, déclarée
   dans `config/mise.toml` de hermes-custom). Lecture : `echo '{"page_id":"<id>"}' | composio execute
   NOTION_GET_PAGE_MARKDOWN -d -` ; une grosse page revient dans un fichier
   (`storedInFile`, puis `outputFilePath`, champ `data.markdown`). Écriture de
   contenu : `composio execute NOTION_UPDATE_PAGE_MARKDOWN -d @args.json`, et
   d'une propriété : `NOTION_UPDATE_PAGE`. Le texte passe par un fichier, jamais
   recopié à la main ; `old_str` se construit par script, et les cases se
   recomptent après chaque écriture (skill `methode-de-travail:connecteurs-timeout`). L'outil
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
   NOTION_UPDATE_PAGE_MARKDOWN -d @fichier`, ou une entrée de changelog dans un
   dossier de brouillons), c'est le pilote qui le reprend, jamais
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

Limite : `composio` est installé par `mise` (cran 3 de la cascade de
`installer-un-outil.md`), déclaré dans `config/mise.toml` de hermes-custom et suivi
par le veilleur `upstream-watch`. Une session cloud ne l'a pas : là-bas, on passe du
palier 1 au palier 3.

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
  coût d'une fumée), mesuré le 2026-09-30. La colonne « Cas au 2026-11-25 »
  donne le nombre de cas que chaque catégorie compte aujourd'hui :

| Catégorie | Cas au 2026-11-25 | Cas mesurés le 2026-09-30 | Un bras, 3 passages | Un passage |
|---|---|---|---|---|
| `existant` | 3 | 2 | 6,43 $ | 2,14 $ |
| `bruit` | 5 | 3 | 4,81 $ | 1,60 $ |
| `etat-de-depart` | 7 | 4 | 7,13 $ | 2,38 $ |
| `maquette` | 1 | 1 | 1,61 $ | 0,54 $ |
| `decouvertes` | 16 | 4 | 4,98 $ | 1,66 $ |
| `perimetre` | 7 | 2 | 2,56 $ | 0,85 $ |
| `delegation` | 1 | — | non mesuré | non mesuré |
| `preuves` | 14 | — | non mesuré | non mesuré |
| `revue-hors-plan` | 5 | — | non mesuré | non mesuré |
| `escalade-bornee` | 1 | — | non mesuré | non mesuré |
| **tout le banc** | 60 | 16 | 27,53 $ | ≈ 9,2 $ |

Les coûts datent du 2026-09-30 et ne sont extrapolés à aucune catégorie. Les
catégories `existant` et `decouvertes` ont gagné des cas depuis : elles coûtent
plus que leur ligne. `delegation`, `preuves`, `revue-hors-plan` et `escalade-bornee`
ne figuraient pas dans la mesure, et leur coût n'a jamais été mesuré. `tout le banc`
désigne le banc de `plans-notion` ; `voyages` en compte un de plus (`billet`), soit
49 cas au total. Le cas `deux-executants` (`perimetre`) est écrit sans être joué :
son coût n'est pas mesuré, et la colonne « Cas mesurés » ne le compte pas.

Mesure postérieure pour `decouvertes` : la PR #60 (son run du
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
