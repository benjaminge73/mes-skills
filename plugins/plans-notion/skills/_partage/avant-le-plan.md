# Avant le plan

Partagé avec le skill `plans-notion:deleguer-a-haiku`, qui le cite à son ouverture : une session lancée en mode plan natif lit ce fichier dès son lancement.
Il ne vaut que pour le plan natif, sans page Notion ; le plan Notion a son enquête dans `plan-notion`.

Une session lancée en mode plan natif relève du skill `deleguer-a-haiku` dès son lancement, avant
`ExitPlanMode` (l'outil par lequel Claude Code quitte le mode plan). Le plan s'écrit dans le fichier natif, et rien dans Notion. Dans cet ordre,
sans sauter d'étape :

1. **Classer la demande** : Spike, Bounded ou Architectural, selon `methode-de-travail:brainstorming`
   (« Three Paths »). Le classement règle la profondeur de l'enquête.
1 bis. **Relever la fraîcheur de la copie locale** : `fraicheur-depot.py` (sans `--appliquer` si le
   checkout peut être occupé), règle et cas délicats dans `${CLAUDE_PLUGIN_ROOT}/skills/_partage/fraicheur-du-depot.md`.
2. **Dresser la carte de voisinage** par `codebase-memory`, sur `main`, **après avoir
   réindexé le dépôt** (`index_repository`, 2 à 15 s : un index périmé donne une carte fausse).
   Les outils sont différés : un `ToolSearch` d'abord ; le paramètre `project` se copie de `list_projects`.
   Le geste est dans `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/enquete.md`, gisement 3
   (« Le code »), section « La carte de voisinage ». Si la carte est omise, sa dispense
   `Pas de carte — <raison>` s'écrit dans le plan.
3. **Invoquer `plans-notion:enqueteur`** (nom qualifié) avec la carte et le relevé des voisins
   (`releve-voisins.py`, joué sur les fichiers touchés) dans son brief. Avant lui, le pilote joue
   `releve-du-jour.py --objets <fichiers touchés>` depuis le dépôt et joint sa sortie au brief. Il suit la liste
   `listes/enquete.md` et rend une fiche cochée, sourcée en `fichier:ligne` ; le pilote la contrôle
   par `verifier-fiche-enquete.py`, une relance au plus, puis confie les cases d'état « non vérifié »
   (C4, C10, C11, et ce que C0 nomme : cron, fichier d'état, unité) à **un** appel de `plans-notion:sondeur`
   (`enquete.md`, gisement 3, « Les lectures d'état, confiées au sondeur »). Pas de page Notion ici :
   le relevé reste dans le plan, sous un intertitre « Relevé du jour », hors de `## Étapes`. Une ligne
   `SECURITE` du relevé devient une question d'office à Benjamin dans le plan, hors de `## Étapes`, en
   plus de la case C12. Le pilote ne lit pas lui-même un fichier de plus de
   200 lignes : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`.
4. **Invoquer `plans-notion:chercheur`** seulement si une étape fabrique un artefact qui n'est
   pas propre au projet : une ligne « Existant cherché : … / trouvé : … / fait maison parce
   que … » par artefact (`enquete.md`, gisement 6, « L'extérieur »). Les dépôts étoilés se
   listent avant lui, par la commande triée par date de mise en favori : `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/enquete.md`, gisement 6, « D'abord, les dépôts étoilés ».
5. **Mesurer le POC, s'il y en a un.** Un POC (preuve de concept : une mesure jetable,
   faite avant de choisir) lève une incertitude mesurable du plan. Le pilote ne le joue
   **jamais** lui-même : il le délègue à `plans-notion:sondeur` si la réponse sort d'une
   commande, à `plans-notion:evaluateur` si elle relève du jugement. Le brief, la grille
   et la forme de la preuve : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`. Pas
   d'incertitude mesurable, aucun de ces deux agents.
6. **Seulement alors, écrire le plan natif.** Chaque choix tranché a sa ligne dans une
   section `## Décisions`, au format `D<n> — <décision> · Preuve : <type> — …` (types et
   format : `poc.md`, « La preuve de chaque réponse »). Tout cron, hook ou workflow sur événement touché a une étape
   `C<n>` : voir `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md`. Avant
   `ExitPlanMode`, la vérification doit rendre 0 :

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-preuves.py" --format natif <plan> --depot <dépôt> --transcripts
   ```

   `--transcripts` fait vérifier le modèle servi de chaque POC cité ; sans lui, le script le signale sur la sortie d'erreur (« POC non vérifié »).

   Code 1 : un écart par ligne, à corriger dans le plan. Code 2 : plan illisible
   (pas de section `## Décisions`, ou aucune ligne `D<n>` dedans).

6 bis. **Jouer la liste de relecture** `${CLAUDE_PLUGIN_ROOT}/skills/_partage/listes/relecture-plan.md`
   sur le plan natif, après le code 0, et avant `ExitPlanMode` : la copie cochée, case par case, chacune
   avec sa preuve. Ses cases 4, 9, 15 et 16 à 19 se cochent `sans objet — plan natif` (la liste le dit en
   tête). Une case non tenue se corrige dans le plan, puis se recoche.
