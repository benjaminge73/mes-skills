---
schema_version: "1.1"
name: reste-cron-lance-a-la-main
description: "Fin d'exécution : un reste qui attend le passage d'un cron ce soir (sans conflit, sans risque de sécurité, sans coût) se lance à la main dans le tour, sans question ; la sortie est citée, et le reste ne s'écrit pas « à vérifier ce soir »."
tags: [execution]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---
Utilise le skill `executer-plan-notion` : toutes les étapes du plan `plan.md` sont faites, tu es au tri du reste à faire de la clôture. Notion n'est pas branché, `plan.md` tient lieu de la page du plan. L'outil `AskUserQuestion` n'est pas disponible : si tu avais dû poser une question, écris-la dans `question.md`, sinon ne crée pas ce fichier.

Ne fais rien d'autre que ce tri : pas de PR, pas de push, pas de Récap. Écris dans `message.md` la rubrique « Reste à faire » du compte rendu que tu enverrais à Benjamin.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
