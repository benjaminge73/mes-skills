---
name: doc-vivante
description: >-
  Doc vivante : la trace d'une PR ou d'un plan dans la documentation Notion. À charger avant
  d'ouvrir ou de passer prête une pull request, de rédiger sa description (ligne « Doc : »), de
  clore un plan ou après un merge sur main, dans un dépôt de Benjamin ; aussi quand on demande
  quelle entrée de Changelog écrire, si une PR de correctif en doit une, quelle raison « sans objet »
  est recevable, ou pourquoi le job CI « doc » refuse une PR.
---

# Doc vivante : l'entrée de Changelog se pose sans qu'on la demande

Cette règle répond à une seule question, et elle se pose dans n'importe quel projet :
**cette PR (ou ce plan) laisse-t-elle sa trace dans la documentation ?**

Elle existe à cause d'un relevé daté. Le 2026-10-22, sur Vahiny (doc vivante activée
depuis le 2026-10-20), deux plans (#279, #281) se sont fermés sans Récap ni entrée de
Changelog, et douze PR faites hors plan n'avaient aucun circuit qui leur fasse écrire une
entrée. Personne n'avait refusé de le faire : personne n'y avait pensé, et rien ne le
rappelait.

## Quand elle s'applique

Seulement dans un projet dont la **page projet Notion** (base Projets, propriété `Repo`
égale au dépôt) porte l'encadré **« Doc vivante : activée »**. Sans cet encadré, rien à
faire : ne pas créer de Changelog dans un projet qui n'en a pas.

Le **Changelog** est la sous-page de la page projet qui liste, par date, ce qui a changé
pour la personne qui se sert de l'app. Une **fiche** est la page Notion d'une
fonctionnalité.

## Ce qu'on fait, sans qu'on le demande

- **Un plan** : la clôture (`executer-plan-notion`, point 7) écrit le Récap dans la page du
  plan, l'entrée au Changelog et la ligne d'historique des fiches touchées. Ce n'est pas une
  option de fin de séance : sauter ce point, c'est le cas qui a motivé cette règle. Exception
  prévue par le skill : un plan enfant d'un lot (plan maître) ne pose pas d'entrée individuelle,
  une seule entrée consolidée part à la fermeture du lot (voir sa ligne `Doc :` plus bas).
- **Une PR sans plan** (correctif, retouche, session libre) : une entrée « Hors plan » au
  Changelog, courte, dont l'en-tête cite le numéro de la PR, et la ligne d'historique des
  fiches touchées, s'il y en a. Le faire dans la même séance que le merge, pas « plus tard ».
- **La description de la PR** porte une ligne qui commence par `Doc :`, dans l'une de ces
  formes, et pas une autre (un nom de fichier ou un titre d'entrée n'est pas un lien) :
  - `Doc : <lien>` : une URL `https://…` vers l'entrée du Changelog, **son ancre et pas la page
    entière** : `…/p/<page du Changelog>#<id du titre H2 de l'entrée, sans tirets>`. L'id se lit
    par `NOTION_FETCH_BLOCK_CONTENTS` sur la page Changelog ; si cette lecture échoue, le lien de
    la page suivi du titre de l'entrée en clair. Méthode : `changelog-et-doc.md` § 2.5 (skill
    `plans-notion`). Relevé du 2026-10-28 : 20 PR pointaient sur la page entière ;
  - `Doc : sans objet — <raison>` (p.ex. un pur correctif de test sans effet visible) ;
  - pour un plan enfant d'un lot : `Doc : sans objet — lot <plan maître>, entrée consolidée à la fermeture du lot`.
- **L'ordre, le même partout** (décision de Benjamin du 2026-11-02) : ouvrir la PR **en brouillon**
  (son numéro n'existe qu'alors), écrire l'entrée en citant ce numéro, éditer la description pour y
  mettre `Doc : <lien>`, puis **passer la PR prête** (`gh pr ready <n>`). Les dépôts à job `doc` ne jouent
  aucune CI sur un brouillon (le run de la sortie de brouillon est le premier à tout jouer) ; `doc` lit la description une seule fois, après les tests, quand la PR est prête : il lit une
  ligne déjà écrite et ne rougit plus à l'ouverture. Une PR laissée en brouillon ne se merge jamais.
  Si la ligne est corrigée plus tard, le workflow `doc-relance` relance le job quand la description
  est éditée. `Doc : sans objet — entrée à venir` est refusé par la CI
  et serait une fausse déclaration.
- **Juste avant `gh pr ready`, jouer la garde en local** (décision de Benjamin du 2026-11-03),
  depuis le worktree. La garde est celle que le job `doc` jouera, avec le même contrat :
  `PR_BODY="$(gh pr view <n> --json body -q .body)" PR_AUTHOR=benjaminge73 python3 scripts/garde_doc_pr.py`
  (sur `vahiny` : `node scripts/garde-doc-pr.mjs`). **Code 0 exigé** avant de passer la PR prête ; un
  1 (refusée) ou un 4 (rien après `Doc :`) se corrige dans la description, puis on rejoue. Dans un plan,
  la clôture le fait par `verifier-ligne-doc.py` (plugin `plans-notion`), qui trouve la garde seul.
  Relevé du 2026-11-03 : 34 échecs de `doc` en 19 jours sur les six dépôts, invisibles dans la liste
  des runs parce que `doc-relance` relance le job et que le run finit vert ; chacun a coûté un run de
  CI pour une ligne qu'une seconde en local aurait refusée.

Sur un dépôt qui a le job CI `doc`, une description sans cette ligne bloque le merge. La
ligne est déclarative : la CI vérifie sa présence et sa forme, pas le contenu de Notion. La
tenir honnête reste l'affaire de la session.

## Ce qui décide, et ce qui ne décide pas

- **L'encadré « Doc vivante : activée » de la page projet décide** si la règle s'applique, jamais
  la présence d'un job CI `doc` dans le dépôt.
- Un **effet visible pour l'utilisateur** (écran, horaire d'un cron, comportement) a toujours une
  entrée : il n'existe pas de « sans objet » pour lui.
- **La PR d'un plan porte aussi sa ligne `Doc :`**, comme toute autre.
- **Le Récap est le premier H2 de la page du plan**, plans de suite compris (un encadré d'intro
  peut rester au-dessus).
- Les dépôts à doc vivante ont un **job CI `doc`** qui lit la ligne `Doc :` (hermes-custom,
  mes-skills) ; il ne vérifie ni Notion ni le fond, seulement la forme et les raisons refusées.

### Raisons « sans objet » refusées

La CI les rejette, et la session ne doit pas les écrire :

- « la page projet n'a pas été consultée » : la lire, puis décider ;
- « pas de job `doc` dans la CI » : voir plus haut, c'est l'encadré qui décide ;
- « pas de Changelog » : un projet à doc vivante activée en a un ;
- « entrée à venir », « plus tard », « à faire » : une fausse déclaration, on écrit l'entrée d'abord ;
- la doc du dépôt (README, `docs/`) citée à la place de l'entrée : elle ne dit pas ce qui change
  pour l'utilisateur.

## Ce qu'on ne fait pas

- Ne pas recopier cette règle dans le `CLAUDE.md` d'un projet : elle vit ici, une seule
  fois, pour tous les projets présents et à venir.
- Ne pas deviner la page projet d'un dépôt qui en a deux : une PR avec plan va au projet du
  plan ; sans plan, la signaler « à classer » à Benjamin.
  **Exception tranchée, `hermes-custom`** (décision de Benjamin du 2026-10-25) : sa doc
  vivante va toujours à la page **Projets / Hermes** et à sa sous-page `Changelog`
  (adresses à retrouver dans Notion : ce dépôt est public), avec ou sans plan. Une PR
  `hermes-custom` n'est jamais « à classer » : son entrée se pose dans ce Changelog, dans la
  même séance que le merge.
- Ne pas inventer une entrée pour une PR de dépendances (Dependabot) : elles sont exemptées.
