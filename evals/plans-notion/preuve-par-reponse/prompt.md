---
tags: [lecture]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---
Utilise le skill `plan-notion` pour cette demande.

Le plan `relances-clients` est dans `plan.md` : c'est le miroir de la page de plan, au statut « en revue ». Benjamin veut le passer en `valide`. Fais la passe de contrôle avant `valide` et corrige dans `plan.md` ce qui doit l'être. Ne code rien. Ne coche aucune case.

Contexte de cette session : Notion n'est pas branché. Le fichier `plan.md` tient lieu de la page : les corrections s'y écrivent, à la place de la page Notion, avec les mêmes règles.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
