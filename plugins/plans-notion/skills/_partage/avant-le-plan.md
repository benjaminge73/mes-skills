# Avant le plan

Partagé avec le skill `plans-notion:deleguer-a-haiku`, qui le cite à son ouverture : une session lancée en mode plan natif lit ce fichier dès son lancement.
Il ne vaut que pour le plan natif, sans page Notion ; le plan Notion a son enquête dans `plan-notion`.

Une session lancée en mode plan natif relève du skill `deleguer-a-haiku` dès son lancement, avant
`ExitPlanMode`. Le plan s'écrit dans le fichier natif, et rien dans Notion. Dans cet ordre,
sans sauter d'étape :

1. **Classer la demande** : Spike, Bounded ou Architectural, selon `methode-de-travail:brainstorming`
   (« Three Paths »). Le classement règle la profondeur de l'enquête.
2. **Dresser la carte de voisinage** par `codebase-memory`, sur `main`. Les outils sont
   différés : un `ToolSearch` d'abord ; le paramètre `project` se copie de `list_projects`.
   Le geste est dans `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/enquete.md`, gisement 3
   (« Le code »), section « La carte de voisinage ». Si la carte est omise, sa dispense
   `Pas de carte — <raison>` s'écrit dans le plan.
3. **Invoquer `plans-notion:enqueteur`** (nom qualifié) avec la carte dans son brief. Il rend
   une fiche sourcée en `fichier:ligne`. Le pilote ne lit pas lui-même un fichier de plus de
   200 lignes : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`.
4. **Invoquer `plans-notion:chercheur`** seulement si une étape fabrique un artefact qui n'est
   pas propre au projet : une ligne « Existant cherché : … / trouvé : … / fait maison parce
   que … » par artefact (`enquete.md`, gisement 6, « L'extérieur »).
5. **Seulement alors, écrire le plan natif.**
