---
schema_version: "1.1"
name: plan-reprend-les-restes
description: "Création d'une page de plan pour le dépôt exemple/notes : elle reprend en tête de page les lignes ouvertes de la base « Restes » de ce dépôt (une décision devient une question ouverte, les autres une puce en lien), laisse ouvertes avec leur raison celles qu'une raison de la liste fermée retient, et marque chaque ligne reprise ; les lignes déjà prises, faites ou d'un autre dépôt ne sont pas reprises."
tags: [execution]
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Agent]
---
Utilise le skill `plan-notion` : tu crées la page d'un nouveau plan, jusqu'à l'étape où elle relève les restes du dépôt. Le sujet du plan est dans `sujet.md`, le dépôt est `exemple/notes`.

Ne joue que cette reprise : pas de Maquette, pas d'étapes d'exécution, pas de branche, pas de PR, pas de plan maître.

Contexte de cette session : Notion n'est pas branché. `base-restes.md` est le résultat de la requête sur la base « Restes » pour ce dépôt, déjà faite : lis-le, ne cherche pas ailleurs. Écris la page du plan dans `plan.md`, titre `[Plan] notes - Index de recherche par étiquette`, `Statut` = `brouillon`. En tête de page, un H2 `Restes repris` : une puce par ligne ouverte du dépôt, son titre en lien (vers l'url de la ligne), puis `Pour` et `Condition`. Une ligne de type `décision` devient une question ouverte, en H3 `🧭 Q1 — …`, avec des cases à cocher toutes vides, la recommandation en premier, et le lien de la ligne dans l'encadré.

Écris dans `lignes-maj.md`, à appliquer à la création de la page, une ligne de tableau par ligne reprise, aux colonnes `url`, `Repris par` et `État` (`Repris par` = ce plan, `État` = `repris`).

Termine ta réponse finale par ce bloc, et rien après lui :

VERIFICATIONS:
- <ce que tu as vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>

Écris « - aucune » sous DECOUVERTES si tu n'as rien découvert.
