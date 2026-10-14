---
name: deleguer-a-haiku
description: >-
  Se charge DÈS LE LANCEMENT d'une session en mode plan natif de Claude Code (sans page Notion), pour enquêter avant d'écrire le plan : carte de voisinage, agent enqueteur, agent chercheur si l'artefact n'est pas propre au projet, le tout écrit dans le plan natif. Exécute aussi un plan natif approuvé, sans page Notion, en le déléguant à des sous-agents Haiku. À utiliser quand on demande d'exécuter, dérouler ou implémenter un plan validé qui vit dans un fichier et non dans Notion : « exécute le plan », « déroule plan.md », plan natif approuvé après ExitPlanMode, ou consigne d'Hermes qui lance une session en mode plan et lit son compte rendu final. Découpe le plan en étapes de cinq fichiers au plus, chacune avec sa preuve ; envoie chaque étape à plans-notion:executant, en parallèle quand les fichiers sont disjoints ; relit chaque rapport et rejoue la preuve ; n'ajoute un relecteur qu'au-delà de cinq fichiers touchés en tout ; cite dans le compte rendu la commande de preuve de chaque étape. Rien ne s'écrit dans Notion. Pour un plan dans une page Notion, c'est executer-plan-notion.
---

# Déléguer un plan natif à Haiku

Ce skill sert une session qui a un plan **sans page Notion**, à écrire ou déjà approuvé.
Il ne lit ni n'écrit aucune page. Le geste tient en cinq temps ; le détail de chaque
règle reste dans les fichiers qu'il cite, pour ne pas en avoir deux copies.

## Avant le plan

Une session lancée en mode plan natif relève de ce skill dès son lancement, avant
`ExitPlanMode` : lire `${CLAUDE_PLUGIN_ROOT}/skills/_partage/avant-le-plan.md` et suivre ses cinq temps dans l'ordre.

## Invariants

- **Une étape = un appel `Agent` à `plans-notion:executant`**, nom qualifié, sans
  paramètre `model` (son frontmatter le fixe). Jamais `general-purpose` pour une
  étape d'exécution : `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`,
  section « La délégation est la règle, pas une faveur ».
- **Diagnostic, pas correctif.** Une preuve rouge ne se corrige pas dans la session :
  on lit la sortie, on la rend à Benjamin ou on relance une étape avec un brief précis.

## Suis-je la bonne version ?

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-version.sh" "${CLAUDE_PLUGIN_ROOT}"
```

Code 0 : à jour. Code 1 : la version ou le chemin chargé diffère de l'`installPath` :
le dire en une ligne, puis lire ce skill depuis cet `installPath`. Code 2 : lecture
impossible, à dire aussi.

## 1. Envoyer les étapes

- Le brief de chaque étape suit la forme de `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`,
  section « Le brief du sous-agent ». Sans recopier la définition de l'`executant`,
  qui arrive avec lui.
- **En parallèle** quand les fichiers sont disjoints, en séquence sinon. Le calcul des vagues,
  l'isolement en worktree et le plafond de concurrence : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`.

## 2. Relire et rejouer

- Lire chaque rapport en entier : son état, ses fichiers, ses écarts.
- **Rejouer soi-même la preuve de fin** de chaque étape. Un écart entre la sortie
  rejouée et celle du rapport est une information à signaler.
- `NEEDS_CONTEXT` ou `BLOCKED` : le dire à Benjamin, ne pas trancher à sa place.

## 3. Relecteur, seulement au-delà de cinq fichiers

Si le plan touche **plus de cinq fichiers en tout**, un appel à
`plans-notion:relecteur` en fin de plan, selon `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`
(« Comment l'appeler »). Sans commit, le brief du relecteur désigne la liste des
fichiers touchés, pas la plage de commits : c'est un écart à écrire dans le
compte rendu.

## 4. Compte rendu

La dernière réponse de la session, courte : pour chaque étape, son état, sa commande de
preuve et le résultat rejoué ; le verdict du relecteur s'il a été appelé ; les écarts et
les questions ouvertes. Une consigne d'Hermes lit ce texte tel quel. Rien n'est écrit
dans Notion ni ailleurs.

Ses compagnons sont les fichiers partagés
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/avant-le-plan.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md` et
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`.
