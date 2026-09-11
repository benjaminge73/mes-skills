# Maquettes HTML pour un plan Notion

Fichier référencé par `plan-notion` (§7), à lire dès que le plan touche à du
design, pour produire une maquette et la référencer dans la page.

Si le plan touche à du design, produire une maquette et la référencer dans la page.

- Déploiement par le **MCP Vercel**, qui prend l'arbre de fichiers directement :
  ni repo git, ni CLI, ni login machine. Identique en cloud, local et VPS.
- **Un prototype Claude Design se lie, il ne s'embarque pas** : une URL
  `claude.ai` refuse d'être affichée dans un iframe. Testé le 2026-09-10 sur
  l'artefact **public** de la galerie `vahiny` — le cas le plus permissif — le
  navigateur rend « claude.ai ne permettra pas à Firefox d'afficher la page si
  celle-ci est intégrée par un autre site ». Aucun réglage Notion ne contourne
  ça : la maquette continue donc de passer par Vercel.
- **Un seul projet dédié**, `plans-claude`, **sans repo GitHub associé**. Chaque
  passe pousse un déploiement `preview` ne contenant que la maquette courante :
  le coût reste proportionnel et le tableau de bord garde un seul projet.
- **Deployment Protection sur « Disabled »**. Un projet Vercel neuf arrive avec
  *Vercel Authentication* active : les URL exigent alors une connexion et l'iframe
  Notion reste vide **sans message d'erreur parlant**. À vérifier avant de conclure
  qu'une maquette « ne s'affiche pas ».
- **Le tout premier déploiement d'un projet part en production**, même en demandant
  `preview`, et récupère l'alias `<projet>.vercel.app`. Écraser ce domaine par une
  page neutre qui dit qu'elle est vide exprès.
- Chaque déploiement a une **URL immuable** : la poser en bloc `embed` dans la page,
  réécrit à chaque passe. Les maquettes des passes précédentes restent consultables.
- `vercel.json` dans l'arbre : `X-Robots-Tag: noindex, nofollow`, plus un
  `robots.txt` en `Disallow: /`.
- **Contenu factice obligatoire** : la page est publique pour qui a l'URL.
- **Pleine largeur et pleine hauteur** : pas de `max-width`, marges intérieures
  serrées, corps en colonne flexible dont la zone centrale absorbe la place
  restante. L'iframe Notion est étroit et sa hauteur se règle à la main ; une
  maquette centrée dans 820 px y perd la moitié de l'espace.
- Un seul fichier HTML, pas d'images en base64 : le contenu transite en tokens à
  chaque déploiement — de l'ordre de 15 à 20 k pour 60 Ko. **Ne redéployer que si
  la maquette a changé.**
- **Le poids compte, parce que c'est ce contenu-là qui transite en tokens au
  déploiement.** Replier une maquette « complète » embarque vite polices et
  illustrations en base64 — sur `vahiny`, les seules illustrations pèsent
  environ 250 Ko avant encodage. Une maquette de plan doit donc rester
  maigre — les composants et les tokens du design system trouvé, oui ; le jeu
  complet d'assets, non. Ce coût ne frappe qu'au déploiement — une maquette
  engendrée par un outil du dépôt (`scripts/galerie-inline.mjs` sur `vahiny`)
  ne coûte rien en tokens tant qu'elle reste sur le disque, puisqu'il écrit son
  fichier sans passer par le contexte. Un dépôt qui a déjà son outil de rendu
  doit donc s'en servir plutôt que de faire réécrire la maquette à la main.
