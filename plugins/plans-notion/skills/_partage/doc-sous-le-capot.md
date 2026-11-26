# La couche « Sous le capot » et la page projet

Détail du § 9 de `changelog-et-doc.md`, lu quand la clôture pose ou met à jour une ligne « Sous le capot », une fiche ou la page mère. Texte repris tel quel, sauf les renvois, qui nomment le fichier où ils vivent.

Sous chaque étape d'un processus de `🗺️ Processus clés` (§ 9.1), et dans chaque fiche, un tableau dit comment c'est fait :

| Sous-étape | Mécanisme | Où | Modèle | effort | Déclencheur |
|---|---|---|---|---|---|
| <ce que fait l'étape> | ⚙️ ou 🤖 ou ⏰ ou 🔁 | <chemin, skill, job ou unité> | <valeur lue> | <valeur lue> | <ce qui la lance> |

- **Mécanisme** : ⚙️ script déterministe ; 🤖 agent (sous-agent ou skill qui raisonne) ; ⏰ cron (tâche planifiée, Hermes) ; 🔁 CI (jeu de tests et déploiement sur GitHub).
- **Où** : un chemin de fichier, un nom de skill, de job ou d'unité. Pas de formule vague.
- **Modèle et effort** se lisent dans la définition, **jamais de mémoire** : les clés `model` et `effort` du frontmatter d'un agent ou d'un skill, ou la configuration du job Hermes pour un cron. Si le frontmatter ne porte pas `model`, écrire `hérité de la session`, pas un nom deviné. Pour un script, `—`.
- **Déclencheur** : ce qui lance l'étape (clôture d'un plan, merge sur `main`, heure du cron).
- Un plan qui change une brique met à jour sa ligne **à partir de son diff**, pas de mémoire.

### 9.1 Page mère : vue d'ensemble, processus, fonctionnalités

La page mère `📚 Documentation` porte, dans cet ordre, la vue d'ensemble, puis trois parties sous leur titre :

- **Vue d'ensemble** : un paragraphe sur ce que fait le projet et pour qui. Elle ouvre la page mère, sans titre.
- **🗺️ Processus clés** : d'abord une vue courte en Mermaid (le langage de schéma de Notion), 5 à 7 étapes métier, une boîte par étape. Les classes de couleur sont celles de `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md` (`color:#000` obligatoire). Un libellé à caractères spéciaux se met entre guillemets doubles. Puis une **frise** de blocs dépliables, un par étape : son titre, ses champs et leur ordre sont ceux de `schemas.md`, section « La frise », seule source. Sous chaque étape, son tableau « Sous le capot ».
- **🧩 Fonctionnalités** : le tableau des fonctionnalités, une ligne par fiche : son nom, sa famille, une phrase, et un lien vers la fiche.
- **🚧 Ce qui n'existe pas encore** : ce que le projet ne fait pas encore, une puce par manque, avec où cela atterrit (même règle que « Reste à faire », `changelog-et-doc.md` § 2.1). « rien » s'il n'y en a pas.

### 9.2 Fiche par fonctionnalité

Une fiche porte cinq parties, dans cet ordre, chacune sous son titre :

- **🎯 À quoi ça sert** : la description côté utilisateur, sans obligation de source.
- **🧭 Comment l'utiliser** : la marche à suivre côté utilisateur.
- **🔩 Sous le capot** : le tableau de la partie d'en tête de ce fichier.
- **⚠️ Limites connues** : ce que la fonctionnalité ne fait pas encore, ou fait mal. « rien » s'il n'y en a pas.
- **🕰️ Historique** : une liste, la plus récente en tête, au format du point 4 du § 4 de `changelog-et-doc.md`.

Une fiche n'est créée que pour une fonctionnalité que le plan touche, et seulement dans un projet activé (`doc-vivante-activation.md`). Elle se range dans sa famille (`changelog-et-doc.md` § 1).
