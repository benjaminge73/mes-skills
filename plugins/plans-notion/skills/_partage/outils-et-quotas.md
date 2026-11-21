# Le registre des outils, de leurs quotas et de leurs pièges

Fichier **d'entrée** du registre, lu par `plan-notion` (avant d'écrire une étape qui lance un lot d'appels sur un outil externe), par `executer-plan-notion` (avant de déléguer un lot) et par l'agent `chercheur` (quand un outil n'a pas de fiche). Il porte les règles générales et l'**index** des fiches. Comme `vagues.md` et `bons-tests.md`, il vit à un seul endroit pour que les skills gardent leur taille : la règle ne se duplique pas, elle se référence.

Les fiches, une par outil, sont réparties par thème dans cinq fichiers `outils-*.md` du même dossier. Un fichier de thème ne se lit que quand un plan touche un de ses outils ; l'index plus bas dit où se trouve chaque fiche. Pourquoi par thème : un fichier par outil ferait trente fichiers à citer, et un seul fichier de 78 000 caractères se lisait en entier à chaque usage. Cinq thèmes voisins tiennent chacun sous le seuil de 30 000 caractères.

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
> créée dans son fichier de thème, et sa ligne ajoutée à l'index, avant tout
> lot. Au-delà de 100 appels, ou dès qu'un appel est payant, demander à
> Benjamin avant de lancer.

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
- **Une fiche neuve s'écrit en deux endroits, dans la même PR** : la fiche
  dans le fichier de thème qui couvre l'outil (`outils-claude-code.md`,
  `outils-connecteurs-et-evals.md`, `outils-code-et-securite.md`,
  `outils-infra-et-documents.md` ou `outils-donnees-publiques.md`), et sa ligne
  dans l'index plus bas, qui dit où la fiche se trouve. Une fiche sans ligne
  d'index est invisible : l'outil reste absent de l'index et suit « Règle pour
  un outil absent », qui recrée la fiche en double.
- **Chaque chiffre porte sa date de lecture.** Un quota change sans prévenir ;
  un chiffre sans date ne se distingue pas d'un chiffre périmé.

## Règle de publication

**Ce dépôt est public.** Une fiche ne contient **ni clé d'API, ni nom de
compte, ni numéro de projet**, et pas davantage d'identifiant de facturation,
d'adresse de messagerie ou d'URL contenant un jeton. Les pièges sont datés et
décrits **sans** dire à quel plan, quel client ou quel compte ils sont arrivés :
la date et le mécanisme suffisent à les retrouver dans le journal du plan
concerné, qui, lui, n'est pas public.

Contrôle avant d'ouvrir la PR : chercher dans les six fichiers `outils-*.md` du
dossier (l'index et les cinq fichiers de thème) toute suite de neuf chiffres ou
plus (un numéro de projet), tout nom de variable se terminant par « KEY »
précédé d'un tiret bas, et toute adresse de messagerie. Commande, depuis la
racine du dépôt :

```
grep -nE '[0-9]{9,}|_KE[Y]\b|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' plugins/plans-notion/skills/_partage/outils-*.md
```

La sortie attendue est vide. La preuve de l'étape qui a créé ces fichiers rejoue
cette recherche et attend une sortie vide.

## Forme d'une fiche

Un titre `## Fiche — <outil>`, puis quatre sous-rubriques, toujours les mêmes et
dans cet ordre : **Quota ou coût** (avec la source et la date de lecture),
**Pièges datés**, **Bonne pratique**, **Repli**. Une rubrique sans objet
s'écrit « aucun connu au <date> », elle ne disparaît pas.

## Choisir entre CLI et serveur MCP

Un même service peut se joindre de deux façons : une **CLI**, commande lancée par
`Bash` dont la sortie revient en texte, ou un **serveur MCP**, dont les outils sont
branchés dans la session et dont les schémas occupent le contexte. Quand les deux
existent, la règle est la **CLI**, pour deux mesures déjà faites dans ce fichier :

- **Le contexte.** Un appel `claude -p` sans outil a chargé **186 651 jetons** de
  connecteurs MCP du compte, contre **8 984** avec `--strict-mcp-config` (2026-10-16,
  fiche « Claude Code (CLI `claude`) sur un serveur à plusieurs comptes »). Un serveur
  MCP attaché à une session coûte ses schémas à chaque tour ; une CLI ne coûte rien
  tant qu'on ne l'appelle pas.
- **Le canal.** Les connecteurs claude.ai relayés par l'app de bureau tombent avec le
  hook de l'app (2026-10-08 à 2026-10-10, fiche « Connecteurs MCP d'une session Claude
  Code »). Le 2026-10-10, la commande `composio` du VPS a tenu les
  écritures Notion pendant que le connecteur de l'app restait injoignable plus de vingt
  minutes. Une CLI qui tourne sur la machine ne dépend ni de l'app ni de la session.

Deux exceptions, où le serveur MCP passe avant la CLI :

1. **Quand la mesure de justesse tranche pour le serveur.** Pour le graphe de code,
   `codebase-memory` (serveur MCP) retrouve **11 éléments sur 11** en 41 appels ; la CLI
   `graphify` n'en retrouve que **5 sur 11** (`affected`, `explain`) ou **7 sur 11**
   (`query`), sur la même mesure (2026-11-11). Le critère est la justesse mesurée, pas le
   canal : la CLI a perdu, on garde le serveur. Son coût reste à borner, par exemple aux
   étapes à risque : une carte de voisinage sur un plan de 24 étapes a pris 57 appels
   (2026-10-09, fiche « codebase-memory »).
2. **Notion, quand la session a son connecteur.** Le connecteur MCP de la session passe
   en premier, la commande `composio` n'est que le second palier de la chaîne de repli.
   Raison : une session cloud n'a pas `composio` ; le connecteur de la session, lui, y
   est, et passe donc en premier. Le repli prend le relais quand le connecteur tombe,
   après trois essais sur une dizaine de minutes.

Pour un autre service, la question se tranche par une mesure, comme pour un outil absent
(« Règle pour un outil absent ») : la même tâche jouée par la CLI et par le serveur, la
justesse comparée, le coût en jetons relevé. Sans mesure, la CLI reste le défaut.

## Index des fiches

Une ligne par outil : son nom, une phrase, puis le fichier qui porte sa fiche (section « Fiche — … »). Les fiches se lisent à la demande, dans le fichier qui les porte. Un outil sans ligne dans cet index n'a pas de fiche utilisable : il suit « Règle pour un outil absent ». Une fiche présente dans un fichier de thème sans sa ligne ici est invisible ; il faut ajouter la ligne (« Règle de vie du registre »).

### `outils-claude-code.md` — Claude Code, abonnement et sessions

- **Sessions Claude** — quota de l'abonnement : 429 vers 23 h UTC, remise à zéro à 00 h 30 UTC (relevé 2026-09-29). → `outils-claude-code.md`, « Fiche — Sessions Claude ».
- **Abonnement Claude Max** — aucun chiffre officiel en tokens ni en heures n'est publié ; ce qu'on peut vérifier, et où (relevé 2026-10-12). → `outils-claude-code.md`, « Fiche — Abonnement Claude Max ».
- **ccusage** — lit les journaux locaux de session pour compter les jetons ; pas de quota (version épinglée 20.0.30). → `outils-claude-code.md`, « Fiche — ccusage (lecture des journaux de session) ».
- **Claude Code (CLI) sur un serveur à plusieurs comptes** — quota de l'abonnement du compte connecté ; 186 651 jetons de connecteurs MCP chargés sans `--strict-mcp-config`, 8 984 avec (relevé 2026-10-16). → `outils-claude-code.md`, « Fiche — Claude Code (CLI `claude`) sur un serveur à plusieurs comptes ».
- **maxTurns** — plafond de tours d'un sous-agent ; un arrêt par la limite est une sortie partielle reprenable, pas un échec. → `outils-claude-code.md`, « Fiche — maxTurns (limite de tours d'un sous-agent) ».
- **Claude Code Review** — service hébergé ; tarif et quota non relus à la date de la fiche. → `outils-claude-code.md`, « Fiche — Claude Code Review (service hébergé) ».
- **i-have-adhd** — règles de forme des réponses, sous forme de skill ; mesure du 2026-11-11 avec et sans les règles. → `outils-claude-code.md`, « Fiche — i-have-adhd (règles de forme des réponses, skill) ».
- **/advisor** — conseiller d'un autre modèle dans Claude Code ; coût affiché par la CLI, pas de quota (relevé 2026-11-11). → `outils-claude-code.md`, « Fiche — /advisor (conseiller d'un autre modèle, Claude Code) ».

### `outils-connecteurs-et-evals.md` — Connecteurs MCP et bancs d'évaluation

- **Connecteurs MCP d'une session Claude Code (Notion, Composio)** — chaîne de repli des écritures Notion (connecteur, puis `composio`, puis Hermes) : délais, pannes datées, commandes. → `outils-connecteurs-et-evals.md`, « Fiche — Connecteurs MCP d'une session Claude Code (Notion, Composio) ».
- **claude plugin eval** — banc d'évaluation d'un plugin : nombre de cas par catégorie, coût mesuré par run. → `outils-connecteurs-et-evals.md`, « Fiche — claude plugin eval ».
- **inspect_ai** — banc d'évaluation Python, bibliothèque libre ; le coût est celui des appels de modèle qu'elle lance. → `outils-connecteurs-et-evals.md`, « Fiche — inspect_ai (banc d'évaluation Python) ».

### `outils-code-et-securite.md` — graphes de code, revue de sécurité et cage

- **codebase-memory** — graphe de code en serveur MCP, local ; le coût se compte en appels et en contexte. → `outils-code-et-securite.md`, « Fiche — codebase-memory (graphe de code, serveur MCP) ».
- **Cage d'une source codée (bwrap, AppArmor, srt, systemd)** — outils locaux pour isoler une source codée ; aucun quota, chaque fait se vérifie par une commande. → `outils-code-et-securite.md`, « Fiche — Cage d'une source codée (bwrap, AppArmor, srt, systemd) ».
- **graphify** — graphe de code en CLI, sans serveur MCP ni appel de modèle ; justesse mesurée plus basse que codebase-memory. → `outils-code-et-securite.md`, « Fiche — graphify (graphe de code, sans serveur MCP) ».
- **hermes-security** — revue de sécurité d'un dépôt, plugin Hermes ; la dépense est en jetons, sur l'abonnement du poste. → `outils-code-et-securite.md`, « Fiche — hermes-security (revue de sécurité d'un dépôt, plugin Hermes) ».

### `outils-infra-et-documents.md` — infrastructure du VPS et documents

- **DeepSeek vision** — vision de DeepSeek : 27,5 $ mesurés par guide, contre 1,04 $ estimés avant lancement (relevé 2026-08-26). → `outils-infra-et-documents.md`, « Fiche — DeepSeek vision ».
- **FileBrowser Quantum** — auto-hébergé, sans quota ; image et version relevées le 2026-10-01. → `outils-infra-et-documents.md`, « Fiche — FileBrowser Quantum ».
- **Cloudflare Zero Trust (tunnel et Access)** — tunnel et applications Access ; aucun quota rencontré au 2026-10-01. → `outils-infra-et-documents.md`, « Fiche — Cloudflare Zero Trust (tunnel et Access) ».
- **Hermes Agent (cron, hub de skills, rendu Slack)** — pas de quota propre ; un passage de job qui réveille l'agent coûte les jetons du modèle du job. → `outils-infra-et-documents.md`, « Fiche — Hermes Agent (cron, hub de skills, rendu Slack) ».
- **Chromium (snap) et Chrome headless** — navigateur local, sans quota ; ses pièges datés. → `outils-infra-et-documents.md`, « Fiche — Chromium (snap) et Chrome headless ».
- **PyMuPDF** — bibliothèque locale de lecture de PDF, sans quota ; ses pièges datés. → `outils-infra-et-documents.md`, « Fiche — PyMuPDF ».

### `outils-donnees-publiques.md` — données publiques, géographie, médias et crypto

- **Google Places** — API de lieux : quota et coût propres à chaque chemin d'accès (relevé 2026-09-29). → `outils-donnees-publiques.md`, « Fiche — Google Places ».
- **Nominatim, Photon et Overpass** — géocodage et données OpenStreetMap ; Nominatim accepte 1 requête par seconde et par adresse IP. → `outils-donnees-publiques.md`, « Fiche — Nominatim, Photon et Overpass ».
- **Jev** — appels quasi gratuits ; ordres de grandeur mesurés sur trois campagnes réelles (relevé 2026-09-29). → `outils-donnees-publiques.md`, « Fiche — Jev ».
- **Wikimedia Commons** — photos téléchargées pour un usage hors ligne ; gratuit, les refus arrivent en 429 ou 503. → `outils-donnees-publiques.md`, « Fiche — Wikimedia Commons (photos téléchargées pour un usage hors ligne) ».
- **DexScreener** — API publique gratuite ; la réponse ne porte aucun en-tête de limite (relevé 2026-10-21). → `outils-donnees-publiques.md`, « Fiche — DexScreener ».
- **RPC public Solana** — nœud public gratuit, « not intended for production » selon la documentation Solana (relevé 2026-10-21). → `outils-donnees-publiques.md`, « Fiche — RPC public Solana ».
- **GeckoTerminal** — 30 appels par minute en gratuit, d'après la page d'aide de CoinGecko (relevé 2026-10-21). → `outils-donnees-publiques.md`, « Fiche — GeckoTerminal ».
- **PumpPortal** — flux des migrations, gratuit ; volume mesuré sur sept jours (relevé 2026-10-21). → `outils-donnees-publiques.md`, « Fiche — PumpPortal ».
- **GDELT** — actualités mondiales ; gratuit, sans limite annoncée (relevé 2026-10-21). → `outils-donnees-publiques.md`, « Fiche — GDELT ».
