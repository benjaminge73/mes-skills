# Le plan léger : une exception bornée au plan complet

Fichier de référence de `plan-notion`. Le **plan complet est la règle**. Le plan léger est une
exception, ouverte seulement quand l'aiguillage la propose **et** que Benjamin la valide. Il
garde les questions fonctionnelles et les critères ; il laisse la découverte technique à
l'exécution.

Sommaire :

- 1. L'aiguillage, avant tout
- 2. Ce que garde la page
- 3. Ce qu'elle saute, et ce qu'elle garde
- 4. L'exécution nue
- 5. Le modèle de l'exécution
- 6. Voisin : le mode plan natif

Pourquoi borné (mesure du 2026-11-24, entrée du 2026-11-25 de `docs/veille.md` du dépôt) : rejoués en léger, trois anciens plans
coûtent 6 à 27 % du coût réel, mais aucun ne tient tous les critères, et 31 % des découvertes
trouvables au plan auraient exigé une question à Benjamin.

## 1. L'aiguillage, avant tout

Avant de proposer un plan léger (que Benjamin le demande ou que la session y pense), et avant
d'écrire la page :

1. Écrire dans un fichier du scratchpad la demande, telle que Benjamin l'a dite, puis une ligne
   `Fichiers pressentis :` avec les fichiers qu'une recherche courte désigne, ou `inconnus`.
   Cette demande part vers un service externe (Jev) : ni secret, ni donnée personnelle, ni ligne
   de code. Si la demande ne peut pas s'écrire sans eux, le plan est complet.
2. Jouer :

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/aiguiller-plan.py" --demande <fichier>
   ```

   Code 0 : « léger » ; code 1 : « complet » ; code 2 : aiguillage impossible (clé absente,
   service en panne, demande refusée). **Seul le code 0 permet de continuer** : 1 et 2 valent
   plan complet, sans nouvel essai avec une demande reformulée. Dans ces deux cas, dire à
   Benjamin `Aiguillage : complet`, la cause (les `motifs` du script, ou son message d'erreur)
   et, quand la demande la montre, la case de la liste concernée.
3. Sur un code 0, recopier la liste `_partage/listes/aiguillage-plan.md` et **prouver chaque
   case**, sous la forme qu'elle demande. Le juge ne rend qu'une note : la preuve est ce que la
   session a lu. Dans la copie, une case prouvée se coche (`— preuve : …`) ; une case sans preuve
   reste décochée (`— non cochée : <raison>`). Une case sans preuve, ou un doute : plan complet.
4. **Proposer à Benjamin**, en tête de réponse : le verdict, la liste prouvée, ce que le plan
   léger saute, et la recommandation. Sans son accord dans la session, le plan est complet. Un
   accord vaut pour cette demande-là seulement.

Une demande qui grossit (une case qui bascule) fait repasser au plan complet : on le dit, et on
reprend `plan-notion` au début, enquête comprise.

## 2. Ce que garde la page

Même base, même gabarit de titre et mêmes `Statut` qu'un plan complet. Dans l'ordre :

- **`Besoins`**, dont le premier paragraphe est la ligne `Mode : léger`, suivie de la copie
  prouvée de la liste d'aiguillage et de la date de l'accord de Benjamin ;
- **`Questions ouvertes`** : les questions fonctionnelles seulement, chacune avec sa
  recommandation ;
- **`Critères`** : réussite ou échec, chacun avec la commande qui le tranche ;
- **`Vérifications`** : trois au plus, seulement celles qui peuvent changer un choix ;
- **`Arrêts`** : les décisions qui exigent de s'arrêter, tirées des classes du §1 de
  `_partage/decouvertes.md` et appliquées à cette tâche, en phrases concrètes (« changer le
  libellé du message d'erreur », pas « toucher au périmètre ») ;
- **`Exécution`** en une seule étape : fichiers pressentis, preuve de fin ;
- **`Journal d'exécution`**.

## 3. Ce qu'elle saute, et ce qu'elle garde

Sautés : l'enquêteur, le chercheur, la carte, la répétition à blanc complète, et le POC (essai
mesuré) sauf incertitude qu'une mesure peut trancher.

Gardés : **la relecture de Hal** avant `en revue` (`_partage/relecture-par-hal.md` ; le hook du
plugin la refuse sinon), les règles d'écriture dans la page
(`_partage/ecrire-dans-notion.md`), la validation de Benjamin (`valide`).

## 4. L'exécution nue

Elle **n'utilise pas** `executer-plan-notion` : ni préparation `pret`, ni sous-agents par étape,
ni relecteur par étape.

- **Elle part sur l'ordre de Benjamin**, jamais seule. Le cron `plans-veille` arrête ses
  reprises à `pret` (hermes-custom #1079) et un plan léger n'a pas ce statut ; la reprise d'un
  plan léger resté `en cours` attend elle aussi son ordre.
- **Statuts** : `valide` → `en cours` → `a merger` → `execute` (merge constaté). Pas de `pret`.
- **Consigne** : un worktree et une branche, jamais `main` ; les tests ; le push ne sert qu'à
  la PR, ouverte en brouillon. Toute décision de la liste `Arrêts`, ou du §1 de
  `_partage/decouvertes.md`, rencontrée en route s'écrit dans **`QUESTIONS.md` à la racine du
  worktree**, jamais commité, **sans agir** sur ce point ; le reste avance.
- **Relecture finale du diff**, avant de passer la PR prête : un appel `Agent`
  (`subagent_type: "general-purpose"`, `model: "sonnet"`), en lecture seule. Le brief porte le
  worktree et la plage de commits, la page recopiée (`Besoins`, réponses, `Arrêts`), l'ordre de
  ne rien modifier ni commiter, et la question : « liste chaque décision prise dans ce diff que
  ni la demande ni une réponse ne tranchait, avec la ligne du diff qui la porte ; s'il n'y en a
  aucune, écris `aucune` ». Un rapport sans liste ni `aucune` se redemande. Sonnet et non
  Haiku : à juger si une découverte était une décision, Haiku n'a rendu la même étiquette d'un
  passage à l'autre que dans 81,5 % des cas.
- **Avant la PR prête** : poser à Benjamin, en une fois, les points de `QUESTIONS.md` et les
  décisions listées par la relecture. La session ne merge jamais.
- **Clôture** : les points de doc d'un plan (Changelog, ligne `Doc :`,
  `_partage/changelog-et-doc.md`), et **deux lignes** à l'`État final` du journal : le coût réel
  (`cout-plan.py --page <id>`), et la liste des décisions prises sans question (ou « aucune »).
  Elles servent à juger le mode sur l'usage.

## 5. Le modèle de l'exécution

**Opus 5.5, effort `medium`** : c'est le réglage mesuré. Une session lancée par Hal le reçoit
par la ligne `Modèle de session : opus` du prompt, plus `Mode : auto` si la tâche passe le
contrôle du « Chemin allégé » du skill `piloted-code-change` (hermes-custom). Ce chemin dit
« Pas de plan Notion » : pour un plan léger, la page, son `Statut`, son journal et ses deux
lignes de clôture restent dus, et le prompt le dit. La liste
d'aiguillage reprend ses conditions (cases A2, A6 à A9) et y ajoute les classes mesurées
(A1, A3 à A5).

**Piège** : si ce contrôle échoue au lancement, la session repart en `opusplan` en mode plan
(Opus planifie, Sonnet écrit). Ce n'est plus l'exécution mesurée : le dire à Benjamin avant de
coder.

## 6. Voisin : le mode plan natif

Une session en mode plan natif (sans page Notion) suit `_partage/avant-le-plan.md`, qui a ses
propres temps (plan « Une veille qui lit Anthropic, et des sessions en mode plan natif guidées
par la checklist », hermes-custom). Ce fichier ne le change pas.
