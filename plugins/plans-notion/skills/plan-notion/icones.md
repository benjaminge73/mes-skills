# L'icône d'une page de plan

Chaque page de la base `Plans Claude` porte une **icône emoji**, posée par le
paramètre `icon` de `create-pages` (ou `update-page`), à la création de la page.
Elle sert à repérer les plans d'un coup d'œil dans le tableau Notion.

## Plan maître : l'icône fixe du projet

Un plan maître porte **toujours** l'icône de son projet, la même d'un maître à
l'autre. Le projet se lit dans `Repo` (`owner/repo`).

| Projet (`Repo`) | Icône du maître |
| --- | --- |
| `benjaminge73/mes-skills` | 🔧 |
| `benjaminge73/hermes-custom` | 🦉 |
| `benjaminge73/vahiny` | 🌴 |
| `benjaminge73/carnet-de-voyage-crete` | 🏛 |
| `benjaminge73/bolossabalos` | 🏛 |
| `benjaminge73/jira-kanban-dashboard` | 📊 |
| `benjaminge73/jira-reports` | 📑 |
| `benjaminge73/kanban_mAIster_ATI4` | 🗂 |
| `benjaminge73/kanban_mAIster_CRM` | 🤝 |
| `benjaminge73/job-agent` | 💼 |
| `benjaminge73/micro-trading` | 📈 |
| `benjaminge73/mavod` | 🎬 |
| `benjaminge73/mavod-perso` | 🍿 |
| `benjaminge73/newsletter-ia` | 📰 |
| `benjaminge73/mariage` | 💍 |
| `benjaminge73/benjamin-goalabre` | 🙋 |
| Amersports (projet sans dépôt propre, lu dans `Projet`) | 🏔 |

Validé par Benjamin le 2026-11-17.
L'icône de `hermes-custom` est passée de 🪽 à 🦉 le 2026-11-19, à la demande de Benjamin : l'API Notion refuse 🪽 (« Invalid page icon URL »).

**Un projet absent de ce tableau** : l'agent choisit l'icône du maître à la
**première** création d'un maître de ce projet, puis l'ajoute au tableau
(dans la même PR si la session travaille ici, sinon il le dit à Benjamin en
une ligne). Avant de choisir, il relit les maîtres existants du projet : s'il
en trouve un avec une icône, il la reprend, il n'en invente pas une autre.

## Tous les autres plans : l'agent choisit

Un plan (`[Plan] …`), un plan de suite compris, reçoit **l'émoticône la plus
adaptée à son sujet**, choisie à la rédaction : 🔍 pour une enquête, 🐛 pour un
bug, 🔐 pour la sécurité, par exemple. Règles :

- une seule émoticône, pas de drapeau ni de lettre ;
- jamais l'icône d'un maître : elle est réservée aux maîtres, pour qu'on les
  distingue dans le tableau ;
- un **plan de suite `#N+1` reprend l'icône du `#N`** : c'est le même sujet ;
- un plan existant n'est pas retouché pour y poser une icône : la règle vaut
  pour les pages créées à partir de maintenant.
