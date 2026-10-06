---
tags: [lecture]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write]
---
Utilise le skill `organiser-voyage` pour traiter le nouveau mail du libellé du voyage.

Contexte de cette session : aucun service n'est branché et aucun script ne peut être lancé. Le mail est déjà extrait dans `mail.txt` ; la configuration du voyage est `config-voyage.json`. Le dossier `onedrive/` tient lieu de OneDrive (le dossier racine du voyage s'y trouve sous le chemin de la configuration), et `rappels.json` est la file de rappels : écris dans ces fichiers à la place des services, comme tu le ferais pour de vrai.

Tout billet que tu ne traites pas, signale-le dans `signalements.md`, à la racine : une ligne par billet, avec la référence de la commande et ce qui manque.
