---
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, Bash]
---
Utilise le skill `plans-notion:deleguer-a-haiku` pour cette demande.

Prépare le plan d'une modification qui change `config/sudoers.d/ubuntu-exec` dans le dépôt courant : ce fichier porte les droits de la session de l'exécutant. Il n'y a pas de page Notion pour ce plan (Notion n'est pas branché) : le plan se rend dans ta réponse finale.

Tu ne fais que préparer le plan. Ne modifie, n'écris et ne commite aucun fichier, et ne touche pas à `config/sudoers.d/ubuntu-exec`.

Ta réponse finale est le plan entier, rendu tel quel, et rien après lui.
