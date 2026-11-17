---
schema_version: "1.1"
name: icone-des-plans
description: "Un plan vient d'être créé alors qu'un autre plan non terminé du même projet existe : la session crée le maître avec l'icône fixe du projet, et donne au nouveau plan une icône de sujet qui n'est pas celle du maître."
tags: [execution]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---
Utilise le skill `plan-notion` : tu viens d'écrire la page du plan `nouveau-plan.md`. Applique ce que le skill prescrit à la création d'une page de plan, plan maître compris. Ne code rien.

Contexte de cette session : Notion n'est pas branché. `base.md` tient lieu du résultat de la requête sur la base `Plans Claude`, filtrée sur le `Repo` du nouveau plan. Écris la page du plan maître en Markdown dans `maitre.md`, et le titre du nouveau plan dans `plan.md`. Chaque fichier commence par une ligne `Icône : <emoji>` : l'icône que tu poserais par le paramètre `icon` de `create-pages`. Ne modifie pas `base.md`.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
