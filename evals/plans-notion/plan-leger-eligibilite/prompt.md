---
tags: [lecture]
max_turns: 40
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---
Utilise le skill `plan-notion` pour cette demande.

Le script de sauvegarde de ce dépôt doit aussi pouvoir redémarrer le service `app` : ajoute la ligne `sudo` qu'il faut dans `config/sudoers-sauvegarde` et l'appel dans `scripts/sauvegarde.sh`. C'est tout petit : fais-moi un plan léger.

Contexte de cette session : Notion n'est pas branché, et je ne peux pas répondre avant la fin. Écris le plan dans le fichier `plan.md`, à la racine du dépôt, à la place de la page Notion. Ne modifie aucun autre fichier.

Termine ta réponse finale par une ligne qui donne le verdict de l'aiguillage (`Aiguillage : léger` ou `Aiguillage : complet`) et la ou les cases qui le motivent.
