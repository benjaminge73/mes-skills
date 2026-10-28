# Avant le plan

Partagé avec le skill `plans-notion:deleguer-a-haiku`, qui le cite à son ouverture : une session lancée en mode plan natif lit ce fichier dès son lancement.
Il ne vaut que pour le plan natif, sans page Notion ; le plan Notion a son enquête dans `plan-notion`.

Une session lancée en mode plan natif relève du skill `deleguer-a-haiku` dès son lancement, avant
`ExitPlanMode` (l'outil par lequel Claude Code quitte le mode plan). Le plan s'écrit dans le fichier natif, et rien dans Notion. Dans cet ordre,
sans sauter d'étape :

1. **Classer la demande** : Spike, Bounded ou Architectural, selon `methode-de-travail:brainstorming`
   (« Three Paths »). Le classement règle la profondeur de l'enquête.
2. **Dresser la carte de voisinage** par `codebase-memory`, sur `main`, **après avoir
   réindexé le dépôt** (`index_repository`, 2 à 15 s : un index périmé donne une carte fausse).
   Les outils sont différés : un `ToolSearch` d'abord ; le paramètre `project` se copie de `list_projects`.
   Le geste est dans `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/enquete.md`, gisement 3
   (« Le code »), section « La carte de voisinage ». Si la carte est omise, sa dispense
   `Pas de carte — <raison>` s'écrit dans le plan.
3. **Invoquer `plans-notion:enqueteur`** (nom qualifié) avec la carte dans son brief. Il rend
   une fiche sourcée en `fichier:ligne`. Le pilote ne lit pas lui-même un fichier de plus de
   200 lignes : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`.
4. **Invoquer `plans-notion:chercheur`** seulement si une étape fabrique un artefact qui n'est
   pas propre au projet : une ligne « Existant cherché : … / trouvé : … / fait maison parce
   que … » par artefact (`enquete.md`, gisement 6, « L'extérieur »).
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
