---
schema_version: "1.1"
name: reste-recopie-dans-la-session
description: "Message qui constate le merge d'un plan à execute : le reste à faire est recopié en entier dans le message (quoi, qui, action attendue) au lieu de renvoyer à l'État final, et le point lié à la PR mergée (auto-fix) est omis."
tags: [execution]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---
Utilise le skill `executer-plan-notion` : la PR du plan `plan.md` vient d'être mergée, le plan est à `execute`. Tu es à la remontée sur `main`, au moment de dire à Benjamin ce qui s'est passé.

Ne fais rien d'autre que ce message : pas de PR, pas de push, pas de Récap. Notion n'est pas branché, `plan.md` tient lieu de la page du plan. Écris dans le fichier `message.md` le message que tu enverrais à Benjamin dans la session, rubrique « Reste à faire » comprise.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
