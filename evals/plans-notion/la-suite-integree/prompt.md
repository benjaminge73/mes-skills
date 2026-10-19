---
schema_version: "1.1"
name: la-suite-integree
description: "Trois restes à côté d'une demande : le petit entre dans le plan, celui qu'un autre plan porte est cité, le gros devient un plan à part ; aucun ne reste en attente dans « La suite »."
tags: [lecture]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Agent]
context:
  scaffold_script: fixture.sh
---
Utilise le skill `plan-notion` pour cette demande.

Dans l'outil de notes, ajoute une commande `compter` qui donne le nombre de notes par étiquette. Fais-moi le plan.

Trois choses à côté, que je te signale en passant :
- la docstring de `lister` dit encore « triées par date » alors qu'elles sont triées par titre ;
- l'export CSV des notes : il est déjà prévu dans le plan `plan-export.md` ;
- à terme, je veux ranger les notes dans une base SQLite plutôt que dans un fichier JSON.

Contexte de cette session : Notion n'est pas branché. Écris le plan dans le fichier `plan.md`, à la racine du dépôt, à la place de la page Notion : mêmes chapitres, mêmes règles. Le fichier `plan-export.md` tient lieu de la page Notion de l'autre plan.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
