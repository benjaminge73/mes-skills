---
schema_version: "1.1"
name: maitre-depart-ordre
description: "Un plan `pret` appartient à un lot dont le Croisement dit qu'il attend un autre plan, encore en cours : sur un « go », la session joue la porte du lot, ne passe pas le plan en cours et dit qui attend quoi."
tags: [execution]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---
Utilise le skill `executer-plan-notion` : Benjamin dit « go » sur le plan P2, `plan.md`, dont le `Statut` est `pret` et dont la préparation est faite. Ne code aucune étape.

Contexte de cette session : Notion n'est pas branché. `plan.md` tient lieu de la page du plan P2 et `maitre.md` de la page de son plan maître. Les `Statut` actuels des plans du lot, lus dans la base à l'instant, sont : P1 `en cours`, P2 `pret`, P3 `pret`.

Si tu passes le plan en cours, écris `Statut : en cours` dans `plan.md`. Si tu ne le passes pas, laisse `plan.md` tel quel et écris dans `refus.md` pourquoi : qui attend quoi, et à quel statut.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
