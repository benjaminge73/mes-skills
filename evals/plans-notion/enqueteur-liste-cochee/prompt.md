---
tags: [lecture]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---
Tu es le pilote d'un plan qui porte sur `src/remise.py`, dans le dépôt courant. Avant d'écrire le plan, tu fais enquêter le voisinage par l'agent `plans-notion:enqueteur` (outil `Agent`, un seul appel). Tu n'enquêtes pas toi-même : l'agent applique sa propre liste, tu ne lui en ajoutes aucune. Tu n'écris, ne modifies et ne commites aucun fichier.

Le brief que tu donnes à l'enquêteur porte, dans cet ordre :

- la question : le plan veut porter le seuil de remise de 100 € à 150 € (`SEUIL` dans `src/remise.py`) et ajouter un paramètre `taux` à `appliquer_remise`. Quels objets, appelants, tests, documents et gardes ce changement touche-t-il ?
- le répertoire courant ;
- la carte du brief : `caisse/panier.py` appelle `appliquer_remise`. Rien d'autre n'a été recensé.

Ta réponse finale est la fiche de l'enquêteur, recopiée telle quelle, sans commentaire de ta part.
