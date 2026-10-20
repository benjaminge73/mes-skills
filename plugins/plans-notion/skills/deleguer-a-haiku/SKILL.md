---
name: deleguer-a-haiku
description: >-
  Se charge DÈS LE LANCEMENT d'une session en mode plan natif de Claude Code (sans page Notion), pour enquêter avant d'écrire le plan : carte de voisinage, agent enqueteur, agent chercheur si l'artefact n'est pas propre au projet, le tout écrit dans le plan natif. Exécute aussi un plan natif approuvé, sans page Notion, en le déléguant à des sous-agents Haiku. À utiliser quand on demande d'exécuter, dérouler ou implémenter un plan validé qui vit dans un fichier et non dans Notion : « exécute le plan », « déroule plan.md », plan natif approuvé après ExitPlanMode, ou consigne d'Hermes qui lance une session en mode plan et lit son compte rendu final. Découpe le plan en étapes de cinq fichiers au plus, chacune avec sa preuve ; envoie chaque étape à plans-notion:executant, en parallèle quand les fichiers sont disjoints ; relit chaque rapport et rejoue la preuve ; n'ajoute un relecteur qu'au-delà de cinq fichiers touchés en tout ; cite dans le compte rendu la commande de preuve de chaque étape. Rien ne s'écrit dans Notion, sauf le changelog et les fiches du projet à la clôture. Pour un plan dans une page Notion, c'est executer-plan-notion.
---

# Déléguer un plan natif à Haiku

Ce skill sert une session qui a un plan **sans page Notion**, à écrire ou déjà approuvé.
Il ne lit ni n'écrit aucune page hors clôture (changelog et fiches).

## Avant le plan

Dès le lancement d'une session en mode plan natif, avant `ExitPlanMode` : lire
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/avant-le-plan.md` et suivre ses six temps.

## Invariants

- **Une étape = un appel `Agent` à `plans-notion:executant`**, nom qualifié, sans
  `model` (son frontmatter le fixe, sauf montée de l'escalade bornée, `etapes.md`).
  Jamais `general-purpose` pour une étape d'exécution :
  `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`.
- **Diagnostic, pas correctif** : voir `${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md`.

## Suis-je la bonne version ?

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-version.sh" "${CLAUDE_PLUGIN_ROOT}"
```

Code 0 : à jour. Code 1 : version ou chemin différents de l'`installPath` : le dire, puis
lire ce skill depuis cet `installPath`. Code 2 : lecture impossible, à dire.

## 1. Envoyer les étapes

- Brief : la forme de `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`,
  sans recopier la définition de l'`executant`.
- **En parallèle** si les fichiers sont disjoints, sinon en séquence (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`).

## 2. Relire et rejouer

- Lire chaque rapport en entier : état, fichiers, écarts.
- **Rejouer soi-même la preuve de fin** de chaque étape. Un écart avec le rapport est à signaler.
- `NEEDS_CONTEXT` ou `BLOCKED` : le dire à Benjamin, ne pas trancher à sa place.

## 3. Relecteur, seulement au-delà de cinq fichiers

Si le plan touche **plus de cinq fichiers en tout**, un appel à `plans-notion:relecteur` en fin
de plan, selon `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`. Sans commit, son brief désigne
la liste des fichiers : écart à écrire au compte rendu.

## 4. Preuve doc

Après les étapes, sur la branche du plan :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/qualite-doc.py" lecteurs --base origin/main > <scratchpad>/passages.json
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/qualite-doc.py" juger --entree <scratchpad>/passages.json
```

Chaque passage relevé se traite selon la rubrique « Preuve doc » de
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md`. Bloquant.

## 5. Compte rendu

Avant la réponse finale, lire `${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md` :
il fixe le texte, dont la preuve doc et ses cinq rubriques.

Ses compagnons sont les fichiers partagés
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/avant-le-plan.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/changelog-et-doc.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/grille-doc.md` et
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md`.
