---
name: deleguer-a-haiku
description: >-
  Se charge dès le lancement d'une session en mode plan natif (sans page Notion), avant d'écrire le plan, et quand on demande d'exécuter un plan validé qui vit dans un fichier : il le délègue à des sous-agents Haiku. Une étape par appel, cinq fichiers au plus, chacune avec sa preuve, envoyée à plans-notion:executant ; chaque rapport relu et sa preuve rejouée ; relecteur au-delà de cinq fichiers. Rien ne s'écrit dans Notion hors changelog et fiches, à la clôture. Déclencheurs complets : section « Quand charger ce skill ». Pour un plan dans une page Notion, c'est executer-plan-notion.
---

# Déléguer un plan natif à Haiku

Ce skill sert une session qui a un plan **sans page Notion**, à écrire ou approuvé.
Il ne lit ni n'écrit de page hors clôture.

## Quand charger ce skill

- **Au lancement en mode plan natif**, sans page Notion, avant d'écrire le plan : enquêter d'abord (« Avant le plan »). Vaut aussi quand Hermes lance la session en mode plan et lit son compte rendu final.
- **Exécution d'un plan natif approuvé** : « exécute le plan », « déroule plan.md », plan approuvé après `ExitPlanMode`, ou consigne qui le demande.
- **Pour un plan dans une page Notion**, ce n'est pas ce skill : c'est `executer-plan-notion`.

## Avant le plan

Au lancement en mode plan natif, avant `ExitPlanMode` : lire
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
lire ce skill depuis lui. Code 2 : lecture impossible, à dire.

## 1. Envoyer les étapes

- Brief : la forme de `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`,
  sans recopier la définition de l'`executant`.
- **En parallèle** si les fichiers sont disjoints, sinon en séquence (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`).

## 2. Relire et rejouer

- Lire chaque rapport en entier : état, fichiers, écarts.
- **Rejouer soi-même la preuve de fin** de chaque étape. Tout écart avec le rapport se signale.
- `NEEDS_CONTEXT` ou `BLOCKED` : le dire à Benjamin, ne pas trancher à sa place.

## 3. Relecteur, seulement au-delà de cinq fichiers

Au-delà de cinq fichiers touchés **en tout**, un appel à `plans-notion:relecteur` en fin de plan,
selon `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`. Sans commit, son brief liste les fichiers : écart à écrire au compte rendu.

## 4. Preuve doc

Après les étapes, sur la branche du plan :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/qualite-doc.py" lecteurs --base origin/main > <scratchpad>/passages.json
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/qualite-doc.py" juger --entree <scratchpad>/passages.json
```

Chaque passage relevé se traite selon la rubrique « Preuve doc » de
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md`. Bloquant.

## 5. Compte rendu

Avant la réponse finale, poser l'entrée du changelog selon `${CLAUDE_PLUGIN_ROOT}/skills/_partage/changelog-et-doc.md` (`controle-changelog.py`), puis lire `${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md` : il fixe le texte (preuve doc, cinq rubriques, « Changelog » après la pose).

Ses compagnons sont :
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/avant-le-plan.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`, `${CLAUDE_PLUGIN_ROOT}/skills/_partage/changelog-et-doc.md`,
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/grille-doc.md` et `${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md`.
