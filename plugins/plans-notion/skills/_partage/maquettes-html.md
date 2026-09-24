# Maquettes HTML pour un plan Notion

Fichier référencé par `plan-notion` (§3 et §7), à lire dès que le chapitre
`Maquette` d'un plan en exige une — une étape au moins change ce qui
s'affiche —, pour la produire et la poser dans la page. `executer-plan-notion`
le lit aussi, pour la section « À l'exécution » en fin de fichier.

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
   <embed src="file-upload://<id>">Maquette — passe N · AAAA-MM-JJ · file_upload_id <id></embed>
   ```

   L'`id` recopié dans la légende est le `file_upload_id` rendu par
   `create-attachment`. C'est la seule prise qu'aura une autre session pour
   relire le HTML (« À l'exécution », plus bas).

   Relue ensuite, la page montre `src="file://%7B…attachment…%7D"` à la place :
   c'est le signe que le fichier est bien attaché au bloc.

⚠️ **La légende va entre `<embed …>` et `</embed>`, jamais dans un paragraphe
séparé.** Vu le 2026-09-24, sur un plan de test : l'embed avait été posé vide,
et l'id était écrit dans le paragraphe du dessous. Le texte reste lisible, mais
le bloc lui-même ne porte plus rien. La règle vaut aussi pour un fichier envoyé
par `curl` (« La voie sans tokens », plus bas) : le `suggested_markdown` rendu
par l'envoi arrive **sans** légende, c'est à nous de l'ajouter.

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
<embed src="file-upload://<nouvel-id>">Maquette — passe N · AAAA-MM-JJ · file_upload_id <nouvel-id></embed>
<details>
<summary>Maquette de la passe précédente</summary>
	<embed src="file://…recopié tel quel…">…sa légende, recopiée telle quelle…</embed>
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

**La voie sans tokens : oui sur le VPS, non en session cloud.**
`create-file-upload` rend une URL d'envoi à usage unique, et le fichier y part
sans passer par le contexte :

```bash
curl -sS -w '\nHTTP %{http_code}\n' -X POST '<upload_url>' \
  -H 'authorization: <upload_headers.authorization>' \
  -F "file=@maquette.html;type=text/html; charset=utf-8"
```

La réponse porte un `suggested_markdown` en `<embed src="file-upload://<id>">`,
à poser **avec sa légende** (voir plus haut).

Mesuré le 2026-09-24 :
- **depuis le VPS, la voie marche** : `HTTP 200`, `status: uploaded`, puis le
  bloc est relu attaché à la page ;
- **mais pas toujours au premier essai.** Trois envois HTML sur deux URL ont
  échoué, avec `HTTP 500` et
  `{"name":"MemcachedCrossCellError","debugMessage":"Cross-cell memcached access is not allowed"}`.
  C'est une erreur interne à Notion, pas un blocage réseau. Le quatrième envoi
  est passé, sur une URL neuve avec le type complet ci-dessus. On ne sait pas si
  c'est le type qui a joué ou si la panne était passagère. La parade : un nouveau
  `create-file-upload`, puis un nouvel essai. Si ça échoue encore, on se
  rabat sur `create-attachment`, qui fait passer le HTML en tokens ;
- **depuis une session cloud, la voie est fermée** : le proxy sortant refuse
  `api.notion.com` (CONNECT 403). On y reste à `create-attachment`.

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

## À l'exécution : relire, puis comparer

Ce que `executer-plan-notion` fait de la maquette, pour les étapes dont
l'`Impact fonctionnel` n'est pas « Rien ».

**Relire le HTML une fois, à l'ouverture.** `download-attachment` avec le
`file_upload_id` de la légende rend le fichier entier ; l'écrire dans le miroir
local du plan, hors du dépôt. Vérifié le 2026-09-24 sur la page du POC : l'`id`
rendu par `create-attachment` répond, l'identifiant visible dans le `src` de la
page répond 404. **La relecture depuis une autre session marche aussi** :
vérifié le 2026-09-24 depuis le VPS, sur un fichier envoyé par une session
cloud. L'`id` de la légende a rendu le fichier entier (643 octets). Si elle
échoue malgré tout, le dire au journal : la comparaison passe alors à Benjamin,
qui voit la maquette dans la page.

**Le brief** d'une telle étape donne au sous-agent le chemin local de la
maquette et la partie qu'il doit réaliser — celle que nomme la ligne
`Impact fonctionnel` de l'étape. Il ne l'a pas autrement : un sous-agent n'a
pas la page.

**Comparer après l'étape.** Rendre le résultat — app qui tourne, page de revue,
harnais de test, par les voies de la sous-section « Les captures d'écran » de
`plan-notion` — et le mettre en regard de la partie de maquette visée.
L'entrée de journal de l'étape porte alors :

- la capture du résultat, si on sait la poser (plus bas) ;
- **les écarts avec la maquette, un par ligne, chacun qualifié** : *voulu*
  (une contrainte découverte en route l'impose — dire laquelle) ou *pas
  voulu*. Un écart pas voulu se corrige dans l'étape, comme une preuve rouge ;
- « Aucun écart » s'écrit, plutôt que de laisser la ligne vide.

**Poser une capture depuis le VPS marche.** Mesuré le 2026-09-24 : la capture
PNG est passée par `create-file-upload` + `curl` (`HTTP 200` au premier envoi),
puis `<image src="file-upload://<id>">` l'a posée dans la page. L'outil utilisé
était Chromium headless :
`chromium-browser --headless --no-sandbox --disable-gpu --window-size=L,H --screenshot=<chemin> file://<maquette>`.
⚠️ Ce Chromium est installé en snap, un format de paquet isolé, et il ne voit
pas `/tmp` : il échoue avec « Failed to write file … No such file or directory ».
Il faut écrire la capture et le fichier source sous `~`.

⚠️ **Poser une image depuis une session cloud ne marche pas.** C'est le même
envoi `curl` vers `api.notion.com`, et le proxy d'une session cloud l'a refusé
le 2026-09-24 (CONNECT 403). `create-attachment` ne prend un binaire que par
une URL publique, et une capture locale n'en a pas.
Dans ce cas, la comparaison s'écrit en mots — les écarts, qualifiés — et le
journal dit que la capture n'a pas pu être posée. Rien de cela n'empêche de
**regarder** la capture dans la session pour comparer : c'est la poser dans la
page qui échoue, pas la prendre.

**Pas de maquette dans un plan qui en exige une** — une étape change ce qui
s'affiche, le chapitre `Maquette` est vide ou sa dispense ne tient pas : on ne
la fabrique pas à l'exécution. Dessiner l'écran, c'est une décision que
Benjamin doit voir avant qu'on code. C'est la porte d'entrée
d'`executer-plan-notion` qui arrête le plan.

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
