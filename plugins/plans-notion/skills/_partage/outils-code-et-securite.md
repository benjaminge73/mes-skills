# Le registre des outils : graphes de code, revue de sécurité et cage

Fiches du registre `outils-et-quotas.md` (fichier d'entrée : règles générales et index des fiches). Ce fichier porte les outils qui lisent un dépôt de code (graphes de code, revue de sécurité) et l'isolement d'une source codée. Il se lit quand un plan touche l'un de ces outils ; les règles générales sont dans `outils-et-quotas.md`.

Sommaire :

- Fiche — codebase-memory (graphe de code, serveur MCP)
- Fiche — Cage d'une source codée (bwrap, AppArmor, srt, systemd)
- Fiche — graphify (graphe de code, sans serveur MCP)
- Fiche — hermes-security (revue de sécurité d'un dépôt, plugin Hermes)

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

## Fiche — graphify (graphe de code, sans serveur MCP)

**Quota ou coût** : aucun quota, l'outil tourne en local. Version mesurée : graphify
0.9.106 (relevé au 2026-11-11). Code seul, sans appel de modèle : la construction du
graphe prend 27 secondes et donne 11 091 nœuds et 25 407 arêtes ; une reconstruction
donne un résultat identique à l'octet. Installation : 205 Mo (environnement supprimé
après la mesure). Non mesuré : la passe sur les documents, qui appelle un modèle.

**Pièges datés** :

- **2026-11-11 : les commandes ciblées trouvent moins que `codebase-memory`.** Six
  questions de structure sur un dépôt de scripts Python de 296 fichiers, onze éléments
  attendus, vérité tirée par `ast` et `grep` : 5 éléments sur 11 par `affected` et
  `explain`, 7 sur 11 par `query`. `codebase-memory` en retrouve 11 sur 11, en 41 appels.
- **2026-11-11 : `query` rend beaucoup de texte.** Entre 54 et 179 nœuds par question,
  soit 17 000 à 114 000 caractères.
- **2026-11-11 : deux angles morts.** graphify ne voit ni les imports faits par
  `importlib`, ni une table de données qui déclare des preuves par composant.
- **2026-11-11 : pas de serveur MCP.** graphify est une commande, pas un outil qu'une
  session appelle comme `codebase-memory`.
- À garder en tête pour la comparaison : `codebase-memory` a donné des faux positifs
  dans ses arêtes de tests lors de la même mesure.

**Bonne pratique** :

- **Décision (2026-11-11) : ne pas adopter graphify, garder `codebase-memory`.** Ce
  relevé sert à ne pas refaire l'étude.
- Un réexamen demande des mesures absentes : la passe sur les documents (appel de
  modèle, plafond à fixer avant) et un dépôt de skills, non mesurés.

**Repli** : `codebase-memory` (fiche ci-dessus). Pour une question qu'il ne tranche
pas, `grep`.

## Fiche — hermes-security (revue de sécurité d'un dépôt, plugin Hermes)

**Quota ou coût** : pas de quota propre. La dépense est en jetons, prise sur
l'abonnement du poste et exprimée en équivalent API. Version mesurée : plugin 0.1.3.

- Passage Opus, mode `standard`, tout le dépôt (2026-11-11) : 25 minutes, 9,43 dollars
  d'équivalent API pour la session et ses trois sous-sessions. 12 lots relus sur 40, soit
  24 fichiers de code sur 292 relus en entier, avec 2 relecteurs.
- Passage Haiku, tout le dépôt, 10 relecteurs (2026-11-13) : coupé par la limite de
  40 minutes de la mesure. 3 lots relus sur 39, 13 fichiers sur 292, 3,40 dollars
  d'équivalent API (parent 1,26 dollar, six sous-sessions Haiku 2,14 dollars), soit
  0,26 dollar par fichier relu.
- Passage Haiku, périmètre ciblé de trois fichiers (2026-11-13) : 3 fichiers sur 3
  relus, 3,01 dollars, coupé au plafond de 3 dollars pendant la validation, 26 minutes.
- Passage Haiku, revue complète, tout le dépôt (2026-11-16) : 16,65 dollars d'équivalent
  API pour 73 sessions (71 sous-sessions Haiku 15,37 dollars, parent 0,88 dollar, reprise
  du parent 0,40 dollar), soit environ le cinquième de l'estimation de 75 dollars. 41
  paquets, 293 fichiers sur 293 relus (175 029 lignes), scan scellé au statut partiel :
  11 unités de déploiement différées faute de preuve d'exécution, aucun contrôle ASVS
  marqué relu (0 sur 142). 5 constats élevés, 30 moyens, 132 faibles, 1 informatif.
  Deux séances : 40 minutes jusqu'à la coupure, puis 46 minutes à la reprise.
- Estimation, non mesurée : Opus, environ 100 dollars estimés.

**Pièges datés** :

- **2026-11-11 : le réglage par défaut ne lance que deux relecteurs.** En mode
  `--oneshot`, `delegation.oneshot_max_children` vaut 2. À 0, les dix relecteurs partent
  (vu au passage Haiku du 2026-11-13).
- **2026-11-13 : le plugin n'a aucune option de modèle.** Le modèle des relecteurs se
  règle par `delegation.model` dans la configuration de Hermes, réglage global à Hermes.
  Le modèle du parent se passe par `hermes chat --oneshot -m <identifiant complet>`.
- **2026-11-13 : installer ou retirer le plugin réécrit tout le fichier de configuration
  de Hermes** (clés réordonnées). Copie avant, comparaison après.
- **2026-11-13 : des relecteurs échouent en `error_max_turns`.** 2 relecteurs sur 6 au
  passage complet, 1 sur 4 au ciblé (limite de tours atteinte).
- **2026-11-13 : `systemctl show` rend `Result=success` même sur une coupure.** Le
  journal de l'unité fait foi.
- **2026-11-13 : l'export exige un scan finalisé.** Un scan coupé en cours de validation
  ne donne pas d'export.
- **2026-11-13 : les candidats ne sont pas des constats.** 16 candidats nouveaux non
  validés sur le passage complet ; 14 candidats sur 29 non validés sur le ciblé.
- **2026-11-11 : les hooks déjà branchés dans la passerelle ne partent qu'à son
  prochain redémarrage.**
- **2026-11-16 : un garde-fou de Hermes coupe la session parent.** Après 54 appels de
  délégation sans progrès, la session `--oneshot` s'arrête sans finaliser le scan et
  sans export, avec un code de sortie de réussite. Une reprise par `--resume` (même
  identifiant de session) a fini le scan en relançant les seuls relecteurs en échec.
- **2026-11-16 : une délégation de plus de dix relecteurs est refusée** (« Too many
  tasks ») ; le parent doit découper en lots de dix au plus.
- **2026-11-16 : le parent peut changer de modèle en route.** À la reprise, la session
  parent a basculé sur un autre fournisseur après une panne de celui de Haiku ; seuls
  les relecteurs restent sur le modèle de `delegation.model`.

**Bonne pratique** :

- Lancer la revue détachée, par `systemd-run --user` avec une durée maximale
  (`RuntimeMaxSec`), et couper l'unité au plafond de coût.
- Lire le statut dans le journal de l'unité, pas dans `systemctl show`. Vérifier qu'un
  scan est finalisé avant l'export.
- Rappel (2026-11-13, périmètre ciblé) : Haiku retrouve 2 constats sur 3 du passage
  Opus. Le troisième, une dépendance vulnérable, n'est vu que par l'analyseur de
  dépendances du plugin, par aucun relecteur.
- **Décision (2026-11-13) : revue complète sur Haiku, dix relecteurs, plafond de 90
  dollars d'équivalent API.** Le coût estimé est de l'ordre de 75 dollars ; la revue
  se lance une fois, puis le plugin est retiré.

**Repli** : un passage ciblé sur quelques fichiers, plafond posé avant le lancement
(3 fichiers sur 3 pour 3,01 dollars). La comparaison avec `/security-review` n'est pas
mesurée.
