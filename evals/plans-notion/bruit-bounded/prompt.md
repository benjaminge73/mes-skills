---
tags: [lecture]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Agent]
---
Utilise le skill `plan-notion` pour cette demande.

Ajoute une option `--version` au CLI : elle affiche le numéro de version du paquet, celui de `pyproject.toml`. Fais-moi le plan.

Contexte de cette session : Notion n'est pas branché. Écris le plan dans le fichier `plan.md`, à la racine du dépôt, à la place de la page Notion : mêmes chapitres, mêmes règles, tout ce qui irait dans la page va dans ce fichier (une maquette HTML s'y écrit dans un bloc de code).

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
