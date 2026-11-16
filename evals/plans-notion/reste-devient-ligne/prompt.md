---
schema_version: "1.1"
name: reste-devient-ligne
description: "Clôture d'un plan dont trois restes restent à trier : le suivi qui attend un relevé à 30 jours et le geste que seul Benjamin peut poser deviennent chacun une ligne de la base « Restes », typée et déclenchée ; la décision restée sans réponse devient une ligne `décision` ; la page du plan ne recopie pas le déclencheur, et aucun plan de suite ne s'écrit (il ne reste aucun travail)."
tags: [execution]
max_turns: 40
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Agent]
---
Utilise le skill `executer-plan-notion` : le plan `plan.md` est exécuté, ses deux étapes sont faites et la suite complète est verte. Tu es au début de la clôture, au tri du reste à faire.

Ne joue que ce tri : pas de PR, pas de push, pas de Récap, pas de worktree.

Contexte de cette session : Notion n'est pas branché. `plan.md` tient lieu de la page du plan, et la base « Restes » n'est pas accessible : `lignes.md` tient lieu des lignes à créer dans cette base. Écris-y, en tableau, une ligne par reste à verser, avec les colonnes `Reste`, `Repo`, `Type`, `Pour`, `Condition` et `État` (`Repo` = `exemple/notes`, `État` = `ouvert`). Pour `Type`, choisis entre `geste`, `vérification`, `décision` et `suivi`.

L'outil de questions `AskUserQuestion` n'est pas disponible : écris dans `question.md` la question que tu poserais à Benjamin sur la décision, la recommandation en premier. Benjamin ne répond pas dans ce test : une décision sans réponse devient une ligne `décision` dans `lignes.md`.

Dans `plan.md`, remplace la rubrique « Reste à faire (non trié) » de l'`État final` par son tri : chaque reste y nomme son propriétaire et renvoie à sa ligne par son titre (pas de lien Notion dans ce test). Ne recopie pas dans cette rubrique le déclencheur d'un reste qui attend un événement : il vit dans sa ligne.

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
