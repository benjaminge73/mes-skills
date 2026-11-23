# Le registre des outils : Claude Code, abonnement et sessions

Fiches du registre `outils-et-quotas.md` (fichier d'entrée : règles générales et index des fiches). Ce fichier porte les fiches de Claude Code, de l'abonnement, de la lecture des sessions, des sous-agents et de la forme des réponses. Il se lit quand un plan touche un de ces outils ; la forme d'une fiche, la règle de publication et le choix entre CLI et serveur MCP sont dans `outils-et-quotas.md`.

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
- **2026-11-13 : `claude -p` sans `--allowedTools` refuse ses outils et rend quand même un succès.** Un agent qui lit des pages a eu 8 outils refusés et une fiche vide, alors que le code de sortie valait 0 et que `subtype` valait `success`. Le succès de l'enveloppe ne prouve donc pas qu'un outil a servi : juger l'appel sur le champ `permission_denials` de la sortie JSON, pas sur le code de sortie.
- **2026-11-13 : `--allowedTools` avale l'argument qui le suit.** Une consigne placée après lui disparaît : elle doit venir avant, `claude -p "<consigne>" --allowedTools "..."`.

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

**Repli** : le `relecteur` de `plans-notion` (agent Opus, effort `medium`), qui ne dépend pas
de ce service.

## Fiche — i-have-adhd (règles de forme des réponses, skill)

**Quota ou coût** : aucun quota. Version non relevée. Mesure du 2026-11-11 : quatre
demandes types, jouées avec et sans les dix règles, sur Sonnet 5.5 (10 appels, 0,43
dollar), notées à l'aveugle sur cinq critères, sur 40 points.

**Pièges datés** :

- **2026-11-11 : les règles font perdre la définition du jargon.** Avec les règles :
  33 points sur 40 contre 28 sans, et 30 % de mots en moins (1 686 contre 2 407). Le gain
  vient de la réponse en tête (8 contre 5) et de l'absence de remplissage (5 contre 0).
  La perte est sur le jargon défini (5 contre 8) ; le pourquoi et la complétude sont à
  égalité. Le seuil écrit avant la mesure (adopter si le total gagne 3 points sans recul
  de la vulgarisation ; écarter tel quel si elle recule de 2 points ou plus) écarte le
  skill tel quel : la vulgarisation recule de 3 points.
- **2026-11-11 : mesure étroite.** Un seul évaluateur ; au rejeu, 5 notes sur 10
  bougent ; les règles étaient injectées en consigne système, pas en skill ; aucune
  session à plusieurs tours.

**Bonne pratique** :

- **Décision (2026-11-16) : installer le skill pour cinq sessions réelles lancées à la
  main, puis trier.** C'est un essai hors plan, à faire par l'utilisateur. Cette fiche
  n'installe rien.
- Si l'on reprend les règles sans le skill, garder la définition du jargon, que le
  skill fait perdre.

**Repli** : retenu, et prévu dans un autre plan : reprendre les trois règles qui gagnent
(réponse en tête, une seule prochaine action à la fin, ni préambule ni formule de fin)
dans la consigne globale de forme, en gardant la définition du jargon.

## Fiche — /advisor (conseiller d'un autre modèle, Claude Code)

**Quota ou coût** : coût affiché par la CLI, pas de quota. Version mesurée : Claude Code
2.1.322 (relevé au 2026-11-11). Appel d'essai (Opus 5.5 conseillé par Fable 5.2) : 0,39
dollar, dont 0,30 dollar pour 34 284 jetons d'entrée du conseiller.

Mesure sur trois corrections de bogues tirées au hasard parmi 27 commits de correction
éligibles d'un dépôt de scripts d'un VPS personnel, état d'avant la correction, tests du
commit rejoués : Opus 5.5 seul réussit 2 tâches sur 3 pour 2,76 dollars ; Opus 5.5
conseillé réussit 1 tâche sur 3 pour 3,73 dollars. Le conseiller a coûté 0,61 et 0,96
dollar sur les deux tâches où il est intervenu ; il n'est pas intervenu sur la
troisième. Dépense de la mesure : 6,88 dollars sur un plafond de 15 dollars. Non
mesuré : si ce coût affiché part en crédits d'usage hors abonnement (la sortie ne le dit
pas).

**Pièges datés** :

- **2026-11-11 : le drapeau n'est pas dans l'aide.** `--advisor <modèle>` existe dans
  Claude Code 2.1.322 mais n'apparaît pas dans `claude --help`.
- **2026-11-11 : une liste d'outils trop étroite fait perdre des tours aux deux bras.**
  La mesure est faussée par ce réglage.
- **2026-11-11 : une seule passe par tâche.** Le résultat est une tendance, pas une
  preuve.

**Bonne pratique** :

- **Décision (2026-11-16) : `advisorModel` reste non réglé.** On remesure à la prochaine
  version de modèle.
- Avant de conclure, rejouer plus large (dix tâches, deux passages chacune). La paire
  Haiku 5.5 conseillé par Fable 5.2 n'est pas mesurée.

**Repli** : Opus 5.5 seul, sans conseiller, bras de référence de la mesure (2 réussites
sur 3, contre 1 sur 3 avec le conseiller).
