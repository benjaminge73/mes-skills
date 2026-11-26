# Le registre des outils : infrastructure du VPS et documents

Fiches du registre `outils-et-quotas.md` (fichier d'entrée : règles générales et index des fiches). Ce fichier porte les outils locaux ou auto-hébergés du VPS (Hermes, FileBrowser, Cloudflare, Chromium, PyMuPDF) et la vision de DeepSeek. Il se lit quand un plan touche l'un de ces outils ; les règles générales sont dans `outils-et-quotas.md`.

Sommaire :

- Fiche — DeepSeek vision
- Fiche — FileBrowser Quantum
- Fiche — Cloudflare Zero Trust (tunnel et Access)
- Fiche — Hermes Agent (cron, hub de skills, rendu Slack)
- Fiche — Chromium (snap) et Chrome headless
- Fiche — PyMuPDF

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
