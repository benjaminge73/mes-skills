---
schema_version: "1.1"
name: reste-a-faire-trie
description: "Clôture d'un plan dont le journal liste cinq restes : la décision attendue de Benjamin est posée en question, le travail de plus d'une étape devient un plan de suite, l'événement attendu reste ; aucun reste ne dort sans propriétaire."
tags: [execution]
max_turns: 40
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Agent]
---
Utilise le skill `executer-plan-notion` : le plan `plan.md` est exécuté, ses deux étapes sont faites et la suite complète est verte. Tu es au début de la clôture.

Ne joue que le tri du reste à faire de la clôture : pas de PR, pas de push, pas de Récap, pas de worktree.

Contexte de cette session : Notion n'est pas branché, `plan.md` tient lieu de la page du plan. L'outil de questions `AskUserQuestion` n'est pas disponible dans ce test : écris à la place, dans le fichier `question.md`, la ou les questions que tu poserais à Benjamin dans la session (la recommandation en premier). Écris le plan de suite, s'il en faut un, dans `plan-suite.md`. Mets à jour la fin de `plan.md` pour que le tri y soit lisible.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
