# Maquettes HTML pour un plan Notion

Fichier référencé par `plan-notion` (§7), à lire dès que le plan touche à du
design, pour produire une maquette et la poser dans la page.

**La maquette vit dans la page, en bloc HTML.** Un fichier `.html` joint à la
page, affiché par un bloc `<embed>` que Notion rend dans un iframe isolé. Ni
Vercel, ni URL publique, ni projet à tenir : c'est la voie par défaut depuis le
2026-09-24, où elle a remplacé « déploiement Vercel + bloc `embed` ».

## Ce qui a été mesuré, et sur quoi

POC du 2026-09-24 : une page Notion, une maquette de 6,6 Ko qui affichait
elle-même ce que le bac à sable lui permettait, relue par Benjamin sur ordinateur
et dans l'app mobile. Les neuf points vérifiés tiennent :

- la maquette s'affiche, **pleine largeur**, et sa **hauteur suffit sans réglage
  manuel** — les deux défauts qui obligeaient à régler l'iframe Vercel à la main ;
- le **JavaScript s'exécute** : clics, filtres, glisser-déposer fonctionnent ;
- **Google Fonts se charge** et une requête sortante vers `cdn.jsdelivr.net`
  répond — une maquette peut donc tirer une police ou une bibliothèque d'un CDN
  public ;
- le rendu tient dans l'**app Notion mobile**.

Ce qui n'a **pas** été mesuré : `localStorage`, l'origine exacte de l'iframe, et
le comportement d'une maquette qui dépasse une page d'écran en hauteur. Une
maquette qui en dépend le vérifie d'abord.

## Le geste, en deux appels

1. **`create-attachment`** du MCP Notion, avec `filename` en `.html` et le HTML
   complet dans `content`. La réponse porte un `markdown_source` de la forme
   `file-upload://<id>`.
2. **Poser le bloc dans la page** — `create-pages` ou `update-page` :

   ```
   <embed src="file-upload://<id>">Légende de la maquette</embed>
   ```

   Relue ensuite, la page montre `src="file://%7B…attachment…%7D"` à la place :
   c'est le signe que le fichier est bien attaché au bloc.

⚠️ **Les deux appels dans la même passe.** Un fichier envoyé mais jamais posé
dans une page reste temporaire et expire : on le perd sans message.

⚠️ **Jamais de bloc de code ni de bloc fichier** pour une maquette : seul
`<embed>` la rend. Un ```` ```html ```` affiche la source, pas l'écran.

## Remplacer la maquette à une passe suivante

Vérifié le 2026-09-24 sur la même page : un nouvel `create-attachment`, puis
`update-page` en `update_content` dont `old_str` est **la ligne `<embed …>`
exacte relue sur la page fraîche** — avec son `src="file://…"` — et dont
`new_str` porte le nouveau bloc. Les cases cochées ailleurs dans la page ne
bougent pas.

Pour garder la version d'avant consultable, `new_str` la reprend telle quelle
dans un bloc repliable, sous le nouveau :

```
<embed src="file-upload://<nouvel-id>">Maquette — passe N</embed>
<details>
<summary>Maquette de la passe précédente</summary>
	<embed src="file://…recopié tel quel…">Maquette — passe N-1</embed>
</details>
```

Le fichier de la passe précédente reste celui d'origine : recopier son `src`
suffit, rien n'est renvoyé. Ne garder que la passe précédente — un empilement
de toutes les versions alourdit la page pour rien.

**Ne remplacer que si la maquette a changé** : chaque envoi fait transiter le
fichier entier en tokens.

## Le poids

Le HTML passe **dans l'appel** : il coûte ses tokens à chaque envoi, de l'ordre
de 15 à 20 k pour 60 Ko, exactement comme un déploiement Vercel le faisait.
Plafond de l'outil : **200 Kio** après encodage UTF-8.

Une maquette de plan reste donc **maigre** : les composants et les tokens du
design system trouvé, oui ; le jeu complet d'assets, non. Pas d'images en
base64 — sur `vahiny`, les seules illustrations pèsent environ 250 Ko avant
encodage, au-delà du plafond à elles seules. Le réseau sortant marchant, une
police se tire de Google Fonts plutôt que de s'embarquer.

Une maquette **engendrée par un outil du dépôt** (`scripts/galerie-inline.mjs`
sur `vahiny`) ne coûte rien tant qu'elle reste sur le disque ; c'est l'envoi
qui la fait passer dans le contexte. Un dépôt qui a son outil de rendu s'en
sert plutôt que de faire réécrire la maquette à la main.

**La voie sans tokens existe, mais pas en session cloud.** `create-file-upload`
rend une URL d'envoi : un `curl -F file=@maquette.html` y pose le fichier sans
qu'il passe par le contexte, et la réponse donne le `<embed>` à poser. Mesuré le
2026-09-24 : depuis une session cloud, le proxy sortant refuse `api.notion.com`
(CONNECT 403). En local ou sur le VPS, **non essayé** — la tenter une fois, et
reporter ici ce qu'elle donne, avant d'en faire une règle.

## La mise en page

- **Pleine largeur et pleine hauteur** : pas de `max-width`, marges intérieures
  serrées, corps en colonne flexible dont la zone centrale absorbe la place
  restante. Le bloc prend la largeur de la page ; une maquette centrée dans
  820 px y perd la moitié de l'espace.
- **Thème clair et sombre**, par `prefers-color-scheme`. Que l'iframe suive
  le thème de Notion ou celui du système n'a pas été mesuré : prévoir les deux
  palettes coûte quelques lignes et évite une maquette blanche dans une page
  sombre.
- **Un seul fichier HTML**, CSS et JS en ligne.

## Le contenu

La maquette a **les mêmes lecteurs que la page** : le fichier suit les droits de
la page, il n'a pas d'URL publique durable. La règle du contenu factice obligatoire,
qui venait de l'URL Vercel publique, tombe avec elle. Reste la règle de la
page elle-même : rien dans la maquette qu'on n'écrirait pas dans le plan.

## Ce qui ne s'embarque pas

**Un prototype Claude Design se lie, il ne s'embarque pas** : une URL
`claude.ai` refuse d'être affichée dans un iframe. Testé le 2026-09-10 sur
l'artefact **public** de la galerie `vahiny` — le cas le plus permissif — le
navigateur rend « claude.ai ne permettra pas à Firefox d'afficher la page si
celle-ci est intégrée par un autre site ». Pour le montrer dans le plan, on en
reprend le HTML dans un fichier joint.

## Vercel, en repli seulement

Deux cas où le déploiement Vercel reste la voie : une maquette qui dépasse les
200 Kio et qu'on ne peut pas amaigrir, ou une maquette qu'il faut montrer à
quelqu'un qui n'a pas accès à la page. Il faut alors le connecteur **Vercel**,
et ses pièges vérifiés tiennent toujours :

- **un seul projet dédié**, `plans-claude`, sans repo GitHub associé, un
  déploiement `preview` par passe ;
- **Deployment Protection sur « Disabled »** — sinon l'iframe reste vide, sans
  message d'erreur parlant ;
- **le tout premier déploiement d'un projet part en production**, même en
  demandant `preview`, et prend l'alias `<projet>.vercel.app` : écraser ce
  domaine par une page neutre qui dit qu'elle est vide exprès ;
- `vercel.json` avec `X-Robots-Tag: noindex, nofollow`, plus un `robots.txt`
  en `Disallow: /` ;
- **contenu factice obligatoire** : l'URL est publique pour qui l'a.
