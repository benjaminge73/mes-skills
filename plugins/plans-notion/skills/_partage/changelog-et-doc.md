# Changelog et doc vivante d'un projet

Fichier **partagé**, lu par `plan-notion` (plan maître), `executer-plan-notion` (clôture) et `deleguer-a-haiku` (plan natif). Il dit **quoi** écrire à la clôture d'un plan, **où** le poser dans Notion, et **comment** le poser sans rien casser. Il se lit en entier avant toute écriture.

Vocabulaire : **Notion** est le wiki où vivent les plans et la doc. Le **connecteur Notion** (un MCP : un branchement d'outil à la session) est l'accès direct de la session à Notion. **VPS** est le serveur privé où tourne Hermes, l'agent qui exécute les tâches planifiées. **PR** est une demande de fusion de code dans `main`. **CI** est le jeu de tests et de déploiement automatique sur GitHub.

Les règles d'écriture détaillées (relevé des cases, pièges de l'API Notion) sont dans `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`. Les schémas et leur code couleur sont dans `${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`.

## 1. Le hub : où la doc d'un projet vit

Le **hub** est la page `Projet`, sous `Clients / Projets`, et tout ce qui est dessous. Pour un plan rattaché à une page `Projet`, c'est celle du plan qu'on clôt. Pour un plan natif, c'est la page `Projet` du plan le plus récent du même `Repo` dans la base. Pour `hermes-custom`, le hub est toujours la page projet « Hermes » (sous `Clients / Projets`) et son `📰 Changelog`, quel que soit le `Projet` du plan (décision de Benjamin du 2026-10-25) ; la session la retrouve par recherche Notion.

La forme est la même pour chaque projet :

```
Projet                       encadré d'activation (§ 5), lien vers la page mère
├── 📰 Changelog             sous-page DIRECTE du projet, pas de la page mère
└── 📚 Documentation         page mère (§ 9.1)
    ├── 📱 <famille>         une phrase ; de 3 à 10 familles par projet
    │   ├── <fiche>          une fiche par fonctionnalité (§ 9.2)
    │   └── <fiche>
    └── 🏭 <famille>
        └── <fiche>
```

- La page `Projet` ne porte que son encadré d'activation, un lien vers la page mère et la sous-page `📰 Changelog`.
- La page mère `📚 Documentation`, sous-page du projet, porte la vue d'ensemble, les processus clés et le tableau des fonctionnalités (§ 9.1).
- Sous la page mère, une sous-page par **famille**. Une famille a son emoji et une phrase qui dit ce qui s'y range. Sous chaque famille, ses fiches. Une fiche nouvelle se range dans sa famille, ou en crée une si aucune ne convient.
- Chaque page a une icône emoji : la page mère, chaque famille, chaque fiche et le `📰 Changelog` compris. Elle se pose par le paramètre `icon` de `create-pages` ou `update-page`.

## 2. L'entrée : format

Une entrée a toujours cette forme. Dans la page du plan, elle commence par le titre `## Récap · AAAA-MM-JJ · <titre du plan>` : le mot `Récap` reste en tête (ancre du condensé, § 7), et la date, dans le titre, est ce que le contrôle du § 4 cherche. Dans le `Changelog` du hub, elle commence par `## AAAA-MM-JJ · <titre du plan>`. Le corps est le même dans les deux cas.

```
## AAAA-MM-JJ · <titre du plan>
Plan : <lien vers la page du plan> · PR : <lien, ou « aucune (plan natif) »> · Statut : <statut de la page>

### ✨ Nouveau
- <phrase> (étape N)

### 🔧 Amélioré
- <phrase> (preuve : <commande ou test>)

### 🐛 Corrigé
- rien

### ⏭️ Reste à faire
- rien

<toggle>Côté technique
	<contenu, § 2.3>
</toggle>
```

### 2.1 Les quatre rubriques

- Elles sont **toujours présentes, dans cet ordre** : ✨ Nouveau, 🔧 Amélioré, 🐛 Corrigé, ⏭️ Reste à faire.
- Une rubrique vide s'écrit `- rien`. Une rubrique n'est **jamais omise**, y compris ⏭️ Reste à faire.
- ✨ Nouveau : ce qui existe désormais et n'existait pas.
- 🔧 Amélioré : ce qui existait et marche mieux.
- 🐛 Corrigé : un défaut connu, corrigé. Rédigé du point de vue de la personne qui s'en servait.
- ⏭️ Reste à faire : ce qui n'est pas livré, **avec où cela atterrit** — le lien du plan de suite, l'événement attendu, ou la décision que Benjamin vient de rendre dans la session. Une décision qu'on attend de lui n'y reste pas en phrase : elle a été posée dans la session avant la clôture (`plan-de-suite.md`, « Le tri »), ou elle est une question ouverte du plan de suite, avec son lien.

### 2.2 Règles de rédaction

1. **Le bénéfice d'abord.** La phrase dit ce que la personne peut faire ou voit désormais, pas ce qui a été codé. Exemple, pour ✨ : « Un récap de chaque clôture, lisible en une minute. »
2. **Pas de jargon dans la phrase.** Ni nom de fichier, ni nom de fonction, ni sigle non défini. Le terme technique va dans « Côté technique ».
3. **Une ligne, une idée**, en phrase courte, au présent.
4. **Chaque ligne ✨ ou 🔧 finit par sa source entre parenthèses** : le numéro de l'étape du plan, `(étape 4)`, ou la preuve, `(preuve : <commande>)`. Pour une étape de découverte, la source peut être `(étape D<n>)`. Une phrase sans source ne va pas en ✨ ni en 🔧 : elle va en ⏭️ ou dans « Côté technique ».
5. **Ne jamais inventer un bénéfice** que la preuve ne montre pas. Si la preuve ne le montre pas, la phrase reste technique.

### 2.3 Côté technique

Le bloc `<toggle>` est replié. Il contient tout ce qui sert à la relecture et n'est pas dans les quatre rubriques :

- les étapes parties, et celles confiées à un sous-agent ;
- l'URL de la PR et le statut de la page ;
- les fichiers touchés, le SHA du commit s'il y en a un ;
- les sorties des commandes de preuve, bornées ;
- les « Ajouts sans question » et les « Recos appliquées par défaut » ;
- les écarts et les décisions prises en route.

Rien du compte rendu actuel n'est perdu en le rangeant ici.

La lecture d'une page par `composio` (§ 6, point 2) rend ce bloc sous la forme repliable à balise `details` dont le titre est porté par `summary`, au lieu de `toggle` ; les deux formes sont acceptées par `controle-changelog.py` et par `doc-de-cloture.py`.

### 2.4 Trois variantes

- **Lot de plan maître** : une seule entrée consolidée au `Changelog`, titre `## AAAA-MM-JJ · Lot <titre du plan maître>`. Le condensé de la page maître (§ 7) reprend chaque plan du lot avec son lien.
- **Plan natif** : le titre porte `(plan natif)`, et la ligne d'en-tête dit `PR : aucune (plan natif)`. Le cas complet est au § 8.
- **Projet désactivé ou sans décision** : le récap de la page du plan s'écrit quand même ; le hub, lui, reste intact (§ 5).

### 2.5 Ce qui compte comme documentation d'une PR

Une PR est **documentée** seulement si son numéro figure dans l'**en-tête** d'une entrée du `Changelog` : la ligne H2 datée (ou `Récap`), et la ligne `Plan :` qui la suit immédiatement. Partout ailleurs, la PR n'est pas documentée : ni dans un bloc `<toggle>Côté technique`, ni dans une puce ou une phrase d'une rubrique, ni dans une phrase d'absence (« pas d'entrée pour #258 »). Un numéro dans le corps d'une entrée ne vaut pas entrée.

Quels numéros comptent dans un en-tête :

- **Dans le titre H2**, seule la forme finale `(PR #N)`, en fin de titre : c'est celle que pose le gabarit « Sans plan » (§ 2.6). Ni un `#N` nu (`## … · Sans plan — Revert « … » (#282)` ne documente pas la PR 282), ni un `PR N` ou un `pull/N` ailleurs dans le titre ne documentent : le titre recopie celui de la PR, qui peut citer d'autres PR (« … ce que la PR #190 a fait … » ne documente pas la 190). Un `(PR N)` sans dièse (« (PR 150) ») ne documente pas non plus la 150. Un numéro du titre de plan (« Vahiny - Thaïlande #4 ») ne documente pas non plus la PR 4. Hors de cette forme finale, le numéro se lit sur la ligne `Plan :` (ci-dessous).
- **Sur la ligne `Plan :`**, seul le segment qui suit `PR :` compte, jusqu'à `· Statut :` (exclu) ou la fin de ligne ; il tient ainsi un groupe de liens séparés par `·` (`PR : [x](pull/262) · [x](pull/263)`). Le lien du plan et son titre ne comptent jamais : `Plan : [Plan … #2 - 3e passe](…) · PR : #12` ne documente ni 2 ni 3.
- **Dans ce segment** : `#N` (frontière de mot : `#25` ne couvre pas `#258`), `pull/N`, et les plages (toutes les PR de A à B incluses) : `#A à #B` et `#A à B` (avec « à » seulement, la borne B peut être sans dièse), `#A–#B`, `#A-#B`, `#A … #B` (avec ces séparateurs, la borne B porte son dièse). Une plage inversée (A > B) ou de plus de 50 numéros (B − A > 50) ne compte pas du tout. Un `PR N` en prose n'est pas lu : `PR : #12 (voir PR 190)` ne documente que la 12. Limite assumée : un `#N` cité entre parenthèses dans ce segment compte encore (`PR : #12 (voir #190)` documente 190 ; le relecteur le voit à l'œil).
- **Un bloc de code** (``` ou ~~~) ne compte ni pour le Récap, ni pour un en-tête : un exemple d'entrée cité dans un bloc ne documente rien.

Le script `${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/doc-de-cloture.py` applique cette règle, dans ses deux usages (§ 4, point 2 bis).

**Le lien de la ligne `Doc :`** d'une PR (règle globale `doc-vivante.md`) vise **l'entrée elle-même**, pas la page `Changelog` entière : `Doc : …/p/<page du Changelog>#<id du titre H2 de l'entrée, sans tirets>`. L'identifiant se lit comme pour le condensé (§ 7) : `NOTION_FETCH_BLOCK_CONTENTS` sur la page `Changelog` (Composio, `echo '{"block_id":"<page>","page_size":100}' | composio execute NOTION_FETCH_BLOCK_CONTENTS -d -`, en suivant `next_cursor`), puis le bloc `heading_2` dont le titre ou la ligne `Plan :` qui le suit porte le numéro de la PR (même lecture qu'au-dessus). **Repli** si la lecture échoue : le lien de la page `Changelog`, suivi du titre de l'entrée en clair (`— entrée « 2026-10-28 · … »`). Le job CI `doc` accepte les deux formes ; l'ancre épargne au lecteur de chercher l'entrée dans une page qui en compte des dizaines (relevé du 2026-10-28 : 20 descriptions de PR corrigées à la main, qui pointaient toutes sur la page entière).

### 2.6 L'entrée « Sans plan »

Une PR mergée sans entrée au hub, et qui n'a pas de plan, se rattrape par une entrée « Sans plan ». Elle a la forme d'une entrée ordinaire :

```
## AAAA-MM-JJ · Sans plan — <titre de la PR> (PR #N)
Plan : aucun (sans plan) · PR : <lien> · Statut : mergée

### ✨ Nouveau
- <phrase> (preuve : PR #N)

### 🔧 Amélioré
- rien

### 🐛 Corrigé
- rien

### ⏭️ Reste à faire
- rien

<toggle>Côté technique
	<contenu, § 2.3>
</toggle>
```

- La date du titre est celle de la pose du rattrapage.
- Les entrées déjà écrites sous l'ancien intitulé de ce gabarit (avant la 0.49.0) restent valides : les scripts ne lisent que `(PR #N)` dans le titre et `Plan : aucun` sur la ligne `Plan :`, jamais la parenthèse qui suit ; on les renomme à la main si on veut l'homogénéité.
- Le numéro de la PR figure **dans le titre**, sous la forme `(PR #N)`, et dans la ligne `Plan :` sous `PR : <lien>` : c'est la forme finale du § 2.5 qui documente la PR, un `#N` nu dans le titre ne suffirait pas, et un `PR N` ailleurs dans le titre ne compte pas.
- Elle passe `controle-changelog.py` comme toute entrée : quatre rubriques, source sur chaque ligne ✨ ou 🔧, bloc « Côté technique ». La source d'une PR sans plan est `(preuve : PR #N)`.
- Elle ne s'écrit **pas** pour une PR de dépendances (auteur Dependabot, ou label `dependencies`).
- Elle **ne remplace pas** l'obligation du plan : une PR qui a un plan doit son entrée de plan (`cloture.md`, point (c)). L'entrée « Sans plan » ne fait que couvrir la PR en attendant, et le compte rendu le dit à Benjamin.
- Le rattachement suit `cloture.md`, point (e) : une PR avec plan va au projet de ce plan, sauf `hermes-custom` (hub Hermes, § 1) ; une PR sans plan sur `hermes-custom` va au Changelog du hub Hermes (§ 1) ; sur un autre dépôt qui aurait deux pages projet sans hub fixé, on demande à Benjamin plutôt que de deviner.

## 3. Le récap et le compte rendu du chat

Le compte rendu de clôture dans le chat **est** le récap, sans réécriture : les quatre rubriques, puis une ligne `PR : <lien> · Statut : <statut>`. Le bloc « Côté technique » suit. Le journal du plan garde son entrée `État final` telle quelle, comme trace complète.

## 4. Les gestes d'écriture

Les règles de `ecrire-dans-notion.md` s'appliquent : relevé avant écriture, édition ciblée, vérification après. Ici, le détail :

1. **Relever.** Recharger la page fraîche (hub ou page du plan) avant d'écrire. Noter l'encadré d'activation, les sous-pages existantes, la page mère avec ses familles, et les fiches déjà là. Ne jamais écrire sur un miroir local. Le titre de la page se lit dans ses propriétés (`title` ou `Titre` de `notion-fetch`), jamais dans le miroir : le corps rendu par `notion-fetch` ne le porte pas, et celui de `composio` (`NOTION_GET_PAGE_MARKDOWN`) n'a ni titre ni propriétés.
2. **Contrôler la forme.** Passer l'entrée au script `${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/controle-changelog.py` avant pose. Il vérifie les quatre rubriques dans l'ordre, la source sur chaque ligne ✨ ou 🔧, et « rien » là où une rubrique est vide. Il vérifie aussi que l'en-tête porte sa ligne `Plan :` et que l'entrée a son bloc « Côté technique ». Sa ligne de commande est dans son en-tête. Si le contrôle échoue, corriger le texte, pas le contrôle.
2 bis. **Deux usages du script `${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/doc-de-cloture.py`.** `--porte` : la page du plan porte son Récap, et, pour un projet activé, l'entrée du hub cite la PR (§ 2.5) ; au palier 3, cette entrée se donne par `--hub-fichier` (fichier confié à Hermes, même format) ; code 1 interdit `a merger` (`cloture.md`, point (b bis)). `--trous` : liste les PR mergées sans entrée, hors dépendances, depuis la date d'activation (`cloture.md`, point (e)) ; chacune reçoit une entrée « Sans plan » (§ 2.6). Le contrôle de forme reste `controle-changelog.py` (point 2).
3. **Poser l'entrée en tête.** Dans le `Changelog`, l'entrée va avant l'entrée précédente, la plus récente en haut. Ancrer le texte sur la **fin complète** du dernier bloc qui précède les entrées (le titre de la page ou son intro), jamais au milieu d'un paragraphe formaté : l'insertion y casserait l'italique ou le gras, sans erreur. Dans la page du plan, le `## Récap · AAAA-MM-JJ · <titre du plan>` se pose de la même façon, en tête : il est le **premier H2 de la page**, au-dessus de `Cartes`, et aussi au-dessus de `Reprise du plan #N` pour un plan de suite (c'est là qu'il manquait le plus, relevé du 2026-10-28). Un encadré d'introduction peut rester au-dessus. `doc-de-cloture.py --porte` refuse un Récap qui n'est pas le premier H2.
3 bis. **Écrire dans le Récap, c'est d'abord vérifier qu'il existe.** La page d'un plan ne naît pas avec un Récap : il n'existe qu'à partir de la clôture (`cloture.md`, point 7 (a)), et les plans clos avant la règle n'en portent pas toujours (11 pages sur 30 au 2026-10-28). Avant toute écriture dans le Récap (le poser, le corriger, y reprendre un reste à faire, y passer `Statut` à `execute` au merge), relever la page fraîche et chercher le H2 dont le titre commence par `Récap`. **Présent** : le modifier en place, `update_content` ancré sur son propre texte, relu. **Absent** : le créer, en tête, par le geste du point 3, avec la forme du § 2 et les quatre rubriques complètes ; jamais un `update_content` ancré sur un titre qu'on suppose là, qui échoue ou s'écrit nulle part. Pas de coquille « Récap » vide posée à la création du plan : `doc-de-cloture.py --porte` ne lit que le titre, et une coquille passerait la porte sans doc.
4. **Réécrire une fiche par bloc.** Une fiche se met à jour par `update_content` sur le bloc concerné, jamais par recréation de la page. Ajouter une ligne en tête de sa liste, sous le titre `🕰️ Historique` : `- AAAA-MM-JJ · <titre du plan> — <ce qui a changé, côté utilisateur>`.
5. **Ne jamais insérer juste avant une liste de cases à cocher.** Notion la recrée et redistribue ses cases cochées. Ancrer après la liste. Ne jamais utiliser un remplacement global (`replace_all`) sur un motif qui contient du balisage.
6. **Vérifier après.** Relire la page : l'entrée est en tête, l'encadré d'activation n'a pas bougé, chaque fiche touchée a sa ligne d'historique. Une écriture peut échouer en silence : sans relecture, l'écriture n'est pas prouvée.
7. **Pas de bleu sur l'entrée.** Elle est neuve par nature, et sa place en tête le dit. Les règles de décoloration de `ecrire-dans-notion.md` s'appliquent à la page du plan lue en passe, pas à l'entrée.

## 5. L'activation par projet

La doc vivante est **activée projet par projet**. Un encadré en tête de la page `Projet` le dit :

- `📘 Doc vivante : activée`, ou
- `📘 Doc vivante : désactivée`.

L'encadré d'activation peut porter une seconde ligne, sous `📘 Doc vivante : activée` : `📘 Rétro-doc : faite AAAA-MM-JJ`. Elle s'écrit dans l'encadré d'activation de la page `Projet`, et c'est le plan de rétro-doc qui la pose à sa fin, en retirant dans le même geste l'encadré « 🚧 Doc partielle » de la page mère. Sans cette ligne, retirer l'encadré ne laisserait aucune trace : la clôture suivante le reposerait. Si la page mère n'a pas d'encadré mais que la ligne est présente, la clôture ne le pose pas.

L'encadré d'activation porte aussi, à l'activation, une ligne `📘 Activée le AAAA-MM-JJ` : la date du jour où l'encadré `📘 Doc vivante : activée` est posé. C'est elle que `doc-de-cloture.py --trous --projet` lit pour borner le rattrapage (`cloture.md`, point (e)) ; le script la cherche comme le motif `Activée le AAAA-MM-JJ`, insensible au gras ou à l'emoji qui l'entoure. Sans elle, `--trous` sans `--depuis` refuse (code 2) : la date ne se devine pas à partir du premier Changelog. Un projet activé avant l'existence de cette ligne ne la porte pas ; Benjamin l'ajoute à la main, avec la date d'activation.

Trois cas :

- **Encadré absent** (projet sans décision, ou nouveau projet) : la clôture **n'écrit rien dans le hub** (ni `Changelog`, ni fiche, ni vue d'ensemble). Elle garde l'entrée prête dans le récap de la page du plan, et pose la question dans son compte rendu : « Doc vivante : à activer pour <projet> ? ». La question est posée à chaque clôture tant que l'encadré n'existe pas.
- **Réponse de Benjamin** : le pilote pose l'encadré (`activée` ou `désactivée`). S'il active, il y ajoute la ligne `📘 Activée le <date du jour>`, puis pose l'entrée, comme un projet activé.
- **Projet activé** : la clôture crée la sous-page `📰 Changelog` si elle manque, et y pose l'entrée. Elle crée **une fiche par fonctionnalité que le plan touche**, et seulement celles-là, rangée dans sa famille (§ 1) ; si aucune famille ne convient, elle en crée une. Chaque fiche créée ajoute une ligne au tableau `🧩 Fonctionnalités` de la page mère (§ 9.1) — son nom, sa famille, une phrase, un lien vers la fiche — **si ce tableau existe**. S'il n'existe pas, la clôture ne le crée pas et n'en invente pas : c'est le rôle de la rétro-doc, comme pour la vue d'ensemble. Une fiche déjà là ne reçoit qu'une ligne d'historique, jamais de ligne de tableau. L'encadré « Doc partielle » vit sur la page mère, plus sur la page `Projet` : si la page mère n'en a pas encore, elle en ajoute un en tête, `🚧 Doc partielle — rétro-doc pas encore faite`, et le laisse en place s'il existe déjà. Elle ne le pose que si la ligne `📘 Rétro-doc : faite` manque dans l'encadré d'activation (ci-dessus) : si elle est là, la rétro-doc est faite et l'encadré n'est pas posé. Un encadré « Doc partielle » déjà posé sur la page `Projet` par l'ancienne règle n'est pas déplacé (la clôture ne déplace jamais une page existante) : elle le signale dans son compte rendu. Elle n'écrit **jamais** de vue d'ensemble ni de processus au jugé : c'est le rôle de la rétro-doc, plan dédié par projet.

**Projet activé, pas de page mère** (décision Q3) : la clôture crée la page mère « 📚 Documentation » vide de vue d'ensemble, avec, si la ligne « 📘 Rétro-doc : faite » manque dans l'encadré d'activation, l'encadré « 🚧 Doc partielle — rétro-doc pas encore faite » (sinon la page naît sans encadré), puis la famille et la fiche ; cette page neuve n'a pas de tableau `🧩 Fonctionnalités`, donc la fiche n'y a pas de ligne (règle du § 5, puce « Projet activé »). Elle ne déplace JAMAIS une page existante, et signale dans son compte rendu les fiches restées à l'ancienne place.

Le récap de la page du plan s'écrit **dans tous les cas**. L'activation ne concerne que le hub.

## 6. La cascade d'écriture dans Notion

Pour toute écriture de la clôture dans Notion (hub, et page du plan), une seule chaîne, la même partout. On passe au palier suivant seulement si le précédent échoue.

1. **Le connecteur Notion de la session.** Si l'appel est refusé par le hook (« did not respond before its timeout »), rien n'est parti : pas de doublon à craindre. Attendre une à deux minutes, réessayer le même appel, jusqu'à trois essais sur une dizaine de minutes. Pendant l'attente, avancer sur ce qui ne dépend pas de Notion.
2. **La commande `composio` du VPS**, en écriture : `composio execute NOTION_UPDATE_PAGE_MARKDOWN -d @<fichier>`. Le texte passe par un fichier, jamais recopié à la main. Le `old_str` se construit par script. Les cases se recomptent après écriture.
3. **Les fichiers confiés à Hermes.** Au palier 3, deux fichiers distincts sous `~/brouillons/<projet>/changelog/`, pour un même plan et une même date :
   - `<AAAA-MM-JJ>-<plan>-recap.md` : le Récap de la page du plan (titre `## Récap · AAAA-MM-JJ · <titre du plan>`). Il s'écrit dès que la page du plan n'a pu recevoir le Récap, quel que soit l'encadré.
   - `<AAAA-MM-JJ>-<plan>.md` : l'entrée du hub (titre `## AAAA-MM-JJ · <titre du plan>`). Il ne s'écrit que si l'encadré dit « activée », et jamais pour un plan couvert par un plan maître (§ 2.4).

   Le compte rendu signale chaque fichier posé comme à poser par Hermes. Hermes les pose par `composio` avec ce fichier, sans les recopier. L'agent qui écrit ne lance pas Hermes lui-même.
   Au palier 3, la clôture ne crée ni page mère, ni famille, ni fiche : les fiches prêtes restent dans le compte rendu, et leur création attend le retour du connecteur ou de `composio`. Les deux fichiers ci-dessus ne changent pas.

Le compte rendu dit **quel palier** a posé l'entrée. Le détail des commandes de lecture et d'écriture, et la façon dont Hermes reçoit la transmission, sont dans la fiche « Connecteurs MCP d'une session Claude Code » de `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`. Ne pas recopier ce détail ici.

## 7. Le condensé du plan maître

Sur la page d'un plan maître, un chapitre `## Récap du lot`, **premier H2 de la page** (au-dessus de `Plans`), reprend les entrées de chaque plan enfant :

- une puce par entrée : titre du plan, date, une phrase de l'entrée ;
- un **lien d'ancre** vers le titre exact de la section concernée : `### Étape N` pour une étape, ou le titre commençant par `## Récap` (`## Récap · AAAA-MM-JJ · <titre du plan>`) pour le récap du plan. `## Récap du lot` n'est pas une cible : c'est le condensé d'un lot, sur la page maître, et il ne récapitule aucun plan ;
- l'identifiant de chaque titre se lit par `NOTION_FETCH_BLOCK_CONTENTS` (Composio, appel par bloc). La forme du lien est `…/p/<page>#<id du bloc sans tirets>` ;
- **repli** : si la lecture de l'identifiant échoue, la mention en clair, `page du plan — → Étape 3` (ou `→ Récap`), sans lien.

Le lien d'ancre est vérifié (2026-10-20, page de test, Notion web) : ouvert par son URL, il arrive sur le titre ; cliqué depuis une autre page de Notion, il atterrit plusieurs sections avant. La mention en clair reste donc toujours écrite à côté du lien.

Pour un lot, le condensé liste chaque plan du lot avec son lien ; le `Changelog` garde l'entrée consolidée unique (§ 2.4).

## 8. Les plans natifs (`deleguer-a-haiku`)

- Un plan natif alimente le `Changelog` et les fiches. C'est la seule exception à la règle « rien dans Notion » d'un plan natif. Son entrée est marquée `(plan natif)`.
- Le hub d'un plan natif suit le § 1.
- Le compte rendu natif porte une **cinquième rubrique `Changelog`**, toujours présente. Ses mentions possibles, et ce que chacune veut dire, sont celles de `${CLAUDE_PLUGIN_ROOT}/skills/_partage/compte-rendu-natif.md`, rubrique « Changelog ». Cette rubrique en est la seule source : ce fichier n'en recopie aucune mention.
- Le skill **n'échoue pas** parce que Notion manque, et il ne cherche aucun contournement en dehors de la chaîne du § 6.
- Projet désactivé (§ 5) : rien n'est tenté dans Notion, et la mention qui le dit est celle de `compte-rendu-natif.md`.

## 9. La couche « Sous le capot »

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
- **🚧 Ce qui n'existe pas encore** : ce que le projet ne fait pas encore, une puce par manque, avec où cela atterrit (même règle que « Reste à faire », § 2.1). « rien » s'il n'y en a pas.

### 9.2 Fiche par fonctionnalité

Une fiche porte cinq parties, dans cet ordre, chacune sous son titre :

- **🎯 À quoi ça sert** : la description côté utilisateur, sans obligation de source.
- **🧭 Comment l'utiliser** : la marche à suivre côté utilisateur.
- **🔩 Sous le capot** : le tableau du § 9.
- **⚠️ Limites connues** : ce que la fonctionnalité ne fait pas encore, ou fait mal. « rien » s'il n'y en a pas.
- **🕰️ Historique** : une liste, la plus récente en tête, au format du point 4 du § 4.

Une fiche n'est créée que pour une fonctionnalité que le plan touche, et seulement dans un projet activé (§ 5). Elle se range dans sa famille (§ 1).
