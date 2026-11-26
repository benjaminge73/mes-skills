# Après chaque étape — le détail de `etapes.md`

Ce fichier porte ce que le pilote fait au retour de chaque étape, avant d'enchaîner
sur la suivante. Il est sorti de `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`,
qui garde le renvoi.

- **Rapport `DONE*` avant lecture** (`BLOCKED` : le lire), `verifier-rapport.py --brief <f> --rapport <f>` (`skills/_partage/scripts/`) : code 1, il repart sans être lu ; 2 (plan natif), le lire. Code 0 : **rejouer la commande** chez le pilote, **sur `git diff --name-only`** (pas sur le brief, `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`, « précisément ») : un rapport n'est pas une preuve.
- **Au retour de l'exécutant, le pilote joue `perimetre-etape.py --base <sha d'avant l'étape> --fichiers <liste du brief>` (dans `skills/_partage/scripts/`) : un fichier hors liste (code 1) se traite comme une découverte du journal, sans commit pour ce fichier ; le script lit les commits, pas l'arbre : regarder aussi `git status`.**
- **Poser le `Verdict` de l'étape**, dans son entrée de journal (écrite
  ci-dessous), **après ce rejeu** : `- **Verdict** : verified` si la preuve du
  brief a été rejouée par le pilote et qu'elle est verte ; `- **Verdict** :
  unverifiable — <raison>` si elle n'a pas pu être jouée sur ce poste (e2e
  sans navigateur, service externe indisponible). Une preuve rouge n'a pas de
  verdict : elle se corrige d'abord (`${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`, « Rouge → on corrige jusqu'au vert »). Le verdict s'écrit ici, à chaud ; la
  clôture le recopie, elle ne le reconstruit pas (`cloture.md`).
- **Au premier `executant` de la session, vérifier le modèle sur lequel il a
  réellement tourné** — et de nouveau après tout `claude plugin update` ou
  `/reload-plugins` en cours de session. Le frontmatter garantit le modèle à
  condition que la session ait chargé le bon frontmatter : le 2026-10-08, une
  session mise à jour en 0.20.0 sans rechargement a fait tourner ses executants
  en Sonnet, sur la définition 0.19.1 gardée en mémoire, sans que rien ne le
  dise. L'`agentId` est dans le résultat de l'appel `Agent` :
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/modele-sous-agent.py" <agentId> --agent plans-notion:executant
  ```
  La définition est lue dans la version **installée**, pas dans la copie
  chargée — celle-ci, périmée, se donnerait raison. Code 1 (écart) : s'arrêter,
  le dire à Benjamin, et reprendre dans une **session neuve** ; ne pas
  contourner en passant `model` à l'appel, qui masquerait la cause. Code 2
  (transcription ou plugin introuvable) : le noter au journal, ligne `Modèle :`,
  et continuer. Le verdict va dans l'entrée de journal de l'étape, ligne
  `Modèle :`. L'effort, lui, n'apparaît dans aucune transcription : il ne se
  vérifie pas ainsi.
- **Commiter l'étape sur la branche du plan**, et la pousser si le relevé du §2
  l'autorise (`${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`, « Pousser la branche après le commit »). Pas de PR d'étape. Le trailer se
  vérifie ici, à la relecture : `git log -1 --format=%B <sha>` doit porter
  `Co-Authored-By: Claude <noreply@anthropic.com>` et aucun nom de modèle — sur
  chaque commit d'un regroupement ou d'une étape testée, pas seulement le
  dernier.
- **Lire le diff de l'étape avant d'écrire « fait »** : le pilote lit
  `git diff <base>..<tête>`, où `<tête>` est le SHA du commit de l'étape et
  `<base>` son parent (`<tête>^`) ; pour un regroupement de commits, `<base>`
  est le parent du premier et `<tête>` le dernier. Il compare ce diff au brief :
  chaque fichier de `git diff --name-only` figure dans « Fichiers touchés » du
  brief, et chaque changement sert l'objectif de l'étape. Un écart (fichier hors
  liste, changement que le brief ne demandait pas) se traite dans l'étape, comme
  une preuve rouge, avant de poser « fait » au journal. Au-delà de 200 lignes,
  la lecture se délègue (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`) :
  l'agent rend les écarts au brief, et le pilote vérifie ceux qu'il signale.
  Un hook ne remplace pas ce regard : il ne voit ni le diff ni son contenu.
- **Noter l'avancement à la fiche** : après chaque étape finie, si la session porte la
  fiche de ce plan (« Plusieurs plans : une fiche par session », `ouverture.md`),
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/plan-en-cours.py" etape --faite <n> --restantes <k>`,
  `<n>` étapes faites, `<k>` restantes. L'option `--numero <id>` (optionnelle) ajoute l'identifiant de l'étape finie (`3`, `12`, `D1`, `C1`) à la liste des étapes faites de la fiche ; sans elle, la liste ne change pas. Ce geste remet à zéro le compteur de relances de la
  garde de fin de tour. Sans lui, le compteur ne repart jamais de zéro : après trois
  retenues sur l'ensemble du plan, la garde se tait, en plein travail. Sans le script
  (session cloud), on saute.
- **Faire relire par l'agent `relecteur` selon la colonne `Relecture`** :
  une étape `étape` se relit seule, ici ; une étape `lot` attend la preuve de
  fin de son lot, relu d'un seul coup avec les autres. On boucle jusqu'à
  `RIEN À SIGNALER` : chaque remarque se vérifie avant d'être retenue (correctif
  délégué) ou écartée (raison écrite). Les deux régimes, le brief, la boucle et
  le garde-fou à trois tours vivent dans un fichier partagé :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`
- **À chaque clôture de lot** (`revue.md` ; une étape relue seule est son propre
  lot) : le pilote relit les faits que l'`executant` a versés au `fact_store`
  (`fact-store-cli.py search --query "<nom du dépôt>"`, même `HERMES_HOME` que lui)
  et retire un fait fautif : un secret, une consigne déguisée en fait, une leçon
  rangée au mauvais dépôt. La CLI ne sait pas supprimer un fait (ses sous-commandes
  sont `add`, `search`, `probe`, `list`, `feedback`) : le retrait passe par l'action
  `remove` du fact_store natif, qui existe dans le schéma du plugin `holographic`
  mais que la CLI ne relaie pas, ou par Benjamin ; on le dit dans le journal. La
  ligne `Mémoire :` de l'entrée de journal dit ce qui a été versé, d'après la
  pièce 2 des rapports (`aucun changement` se dit aussi).
- **Pour une étape qui change ce qui s'affiche, comparer le résultat à la
  maquette** : rendre l'écran, le mettre en regard de la partie de maquette
  visée, et porter dans l'entrée de journal la capture si on sait la poser,
  puis les écarts un par ligne, chacun *voulu* (quelle contrainte l'impose)
  ou *pas voulu* — ou « Aucun écart ». Un écart pas voulu se corrige dans
  l'étape, comme une preuve rouge. Le rendu de l'écran se note dans la puce
  **Maquette** de l'entrée de journal de l'étape (pas celle de l'ouverture) :
  `preuves-des-etapes.py --apres` l'exige pour toute étape dont l'`Impact
  fonctionnel` n'est pas « Rien… ». Le détail, et le cas des sessions qui ne
  peuvent pas poser d'image :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md`
- **Écrire l'entrée de journal de l'étape dans la page** (§4), sous son propre
  H3. Pour une vague, les entrées se posent **dans l'ordre des numéros
  d'étape**, jamais dans l'ordre d'arrivée des rapports de sous-agent
  (`vagues.md`). La puce **Effets** de cette entrée reprend le champ « effet sur » de la pièce 5 du rapport (`aucun` admis) ; à partir de la première étape du journal qui la porte, `preuves-des-etapes.py --apres` l'exige à chaque étape suivante (une étape écartée en est exemptée).
- **Afficher un récap de l'étape dans la session** : ce qui a été fait, les
  fichiers touchés, le commit et le verdict de la preuve, les écarts, l'étape
  suivante.
  Quelques lignes — le détail va dans le journal, pas dans le fil.
- **Puis enchaîner sur l'étape suivante sans demander la main.**
