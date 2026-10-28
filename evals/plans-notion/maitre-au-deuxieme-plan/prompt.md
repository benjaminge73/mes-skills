---
schema_version: "1.1"
name: maitre-au-deuxieme-plan
description: "Un plan vient d'être créé alors qu'un autre plan non terminé du même projet existe, sans plan maître : sans qu'on le demande, la session crée le maître avec les deux plans (et seulement eux), sa page en coquille."
tags: [execution]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---
Utilise le skill `plan-notion` : tu viens d'écrire la page du plan `nouveau-plan.md`. Applique ce que le skill prescrit, à la création d'une page de plan, au sujet d'un plan maître. Ne code rien.

Contexte de cette session : Notion n'est pas branché. `base.md` tient lieu du résultat de la requête sur la base `Plans Claude`, filtrée sur le `Repo` du nouveau plan, lue à l'instant. Si un plan maître doit naître, écris sa page en Markdown dans `maitre.md`. Sinon, écris dans `seul.md` pourquoi le plan reste seul. Ne modifie pas `base.md`.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
