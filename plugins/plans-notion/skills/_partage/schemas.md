# Schémas dans une page de plan Notion

Fichier **partagé**, lu par `plan-notion` avant de poser le moindre schéma dans une
page de plan, et par `executer-plan-notion` à la clôture, quand il relit les
schémas pour vérifier qu'ils sont à jour. Comme `ecrire-dans-notion.md`, il vit à
un seul endroit pour que les deux skills gardent leur taille : la règle ne se
duplique pas, elle se référence.

Il ne dit pas *comment* écrire dans Notion sans rien casser — ça, c'est
`ecrire-dans-notion.md`. Il dit *quels* schémas poser, *quand*, et avec *quel*
code couleur.

## Pourquoi des schémas

Deux faits, remontés par l'enquête sur les plans passés :

- **Zéro bloc Mermaid sur 77 plans terminés.** Aucun plan écrit jusqu'ici n'a
  jamais posé de schéma. Toute l'information de dépendance entre étapes vivait en
  prose, dispersée dans le chapitre `Exécution`.
- **Deux familles de découvertes faites seulement à l'exécution, pas à l'écriture
  du plan**, et qui **auraient sauté aux yeux sur un schéma** : des fichiers
  partagés entre deux étapes non consécutives (donc une dépendance invisible dans
  une liste séquentielle), et des chaînes d'étapes qui se contredisent (l'étape 5
  défait une hypothèse posée par l'étape 2, par exemple). Un texte linéaire cache
  ces deux formes ; un graphe les rend visibles avant de coder.

Le schéma n'est donc pas de la décoration : c'est un outil de relecture, pour
Benjamin comme pour le pilote.

## Les trois schémas, et quand chacun se justifie

### La carte du dépôt

Une vue d'ensemble du dépôt travaillé, postée dans le chapitre `Cartes` en tête de
la page de plan. Deux façons de l'obtenir, jamais un mélange :

- **Engendrée**, quand le dépôt a un générateur de carte. Exemple vérifié :
  Vahiny, où `npm run archi` produit `docs/architecture.md` depuis un registre de
  blocs déclaré dans `scripts/archi.mjs`. Une carte engendrée est reproductible et
  ne ment jamais sur la structure actuelle du code — elle se recopie telle quelle.
- **Dessinée à la main**, quand le dépôt n'a pas ce générateur. Alors, pendant
  l'enquête (pas après coup) : dix blocs au plus, construits depuis le `CLAUDE.md`
  du dépôt et la fiche rendue par l'agent `enqueteur`, jamais par lecture
  exhaustive du code. La légende porte toujours la mention *« dessinée à la main
  le AAAA-MM-JJ, non garantie par un test »* — elle dit au lecteur que rien ne
  vérifie que ce schéma suit encore le code demain. Dans ce cas, le chapitre
  `La suite` du plan note qu'une carte engendrée manque : c'est une dette, pas un
  détail, et elle doit rester visible après la clôture du plan.

Ne jamais dessiner à la main un dépôt qui a un générateur : la carte à la main
serait périmée dès le premier commit qui la contredit, sans que rien ne le signale.

### Le plan en un schéma

Un schéma unique pour toute la page de plan, une boîte par étape, qui répond à la
question que la prose linéaire pose mal : *qu'est-ce qui peut tourner en même
temps, et qu'est-ce qui attend quoi ?*

- Les **vagues** — groupes d'étapes qui peuvent s'exécuter en parallèle parce
  qu'elles ne partagent ni fichier ni dépendance — sont des sous-graphes
  (`subgraph`), pas de simples couleurs : la frontière visuelle dit d'un coup
  d'œil ce qui peut partir ensemble.
- Chaque boîte porte le code couleur (section suivante).
- Les **flèches pointillées** marquent ce qui attend un geste de Benjamin (une
  réponse, une validation, une PR retenue) — elles se distinguent des flèches
  pleines, qui marquent une dépendance entre étapes.

Voir l'exemple complet en fin de fichier : c'est un schéma réel, déjà rendu par
Notion.

### Le sous-schéma focalisé, sous une étape

Un schéma zoomé sur les blocs du dépôt que touche une étape précise, posé sous le
H3 de cette étape dans le chapitre `Exécution`. **Seulement quand le dépôt a un
générateur** — jamais dessiné à la main, parce qu'un sous-schéma à la main double
le risque de péremption de la carte globale sans rien apporter de plus.

Exemple vérifié, Vahiny : `node scripts/archi.mjs --blocs <ids>` rend les blocs
demandés **plus leurs voisins directs, à un cran** — jamais la fermeture
transitive. C'est une vue locale, pas une deuxième carte du dépôt : elle répond à
« qu'y a-t-il juste à côté de ce que je modifie », pas à « quel est l'impact total
en cascade ».

## La ligne « Blocs touchés »

Sous chaque étape du chapitre `Exécution`, une ligne :

```
**Blocs touchés** — bloc-a, bloc-b
```

qui renvoie aux nœuds de la carte du dépôt (engendrée ou à la main). Elle relie
l'étape à un endroit précis du schéma en tête de page, sans obliger à redessiner
quoi que ce soit à chaque étape : la carte reste unique, les étapes la référencent.

## Le code couleur

Cinq classes Mermaid (`classDef`), toujours les mêmes noms et les mêmes couleurs
d'un plan à l'autre, pour que la lecture ne réapprenne pas une légende à chaque
page :

| Classe | Sens | Couleur | Déclaration |
|---|---|---|---|
| `det` | écriture déterministe, ou sous-agent | bleu | `fill:#dbe9ff,stroke:#3b6fd6,color:#000` |
| `agent` | lecture et jugement côté pilote | violet | `fill:#efe0ff,stroke:#8b4fd6,color:#000` |
| `toi` | un geste de Benjamin | orange | `fill:#ffe3c2,stroke:#e08a1e,color:#000` |
| `data` | un artefact (fichier, branche, page) | gris | `fill:#f1f1f1,stroke:#888,color:#000` |
| `out` | une sortie livrée | vert | `fill:#dff5e1,stroke:#2e8b57,color:#000` |

`color:#000` est systématique sur les cinq classes : sans lui, le texte hérite du
thème du lecteur et devient illisible en thème sombre sur un fond clair.

## Mettre à jour à chaque passe

Toute passe qui touche le chapitre `Exécution` (nouvelle étape, étape reformulée,
dépendance changée) **rejoue le schéma « le plan en un schéma »** — il ne survit
pas tel quel à une réorganisation des étapes, sous peine de mentir sur l'ordre
réel du travail.

**Contrôle mécanique avant de clore la passe** : compter les nœuds d'étape du
schéma et les comparer au nombre de titres H3 `Étape N` de la page. Les deux
comptes doivent être égaux. Un écart dit qu'une étape a été ajoutée, retirée ou
fusionnée dans un des deux endroits sans l'autre — c'est le même principe que le
recomptage des cases cochées d'`ecrire-dans-notion.md` : un contrôle qui ne coûte
rien et qui attrape l'oubli le plus fréquent.

## Les pièges Notion, propres aux schémas

- **Insertion sur une frontière de bloc.** Un bloc Mermaid est un bloc à part
  entière : l'insérer au milieu d'un autre bloc (par exemple entre deux lignes
  d'une liste) le casse silencieusement. Toujours l'insérer entre deux blocs
  existants, jamais à l'intérieur d'un.
- **Guillemets doubles autour des libellés à caractères spéciaux.** Un libellé de
  nœud contenant `:`, `(`, `)`, une virgule ou un retour à la ligne doit être
  entouré de guillemets doubles (`A["texte : précis"]`) — sans eux, Mermaid coupe
  le libellé au premier caractère spécial et le schéma ne compile pas.
- **`<br>` pour les retours à la ligne dans un libellé.** Un saut de ligne littéral
  dans un libellé casse le graphe ; `<br>` est le seul séparateur qui fonctionne à
  l'intérieur d'un nœud.
- **Un bloc Mermaid est un bloc de code : le bleu des retouches ne s'y applique
  pas.** La règle du bleu (`ecrire-dans-notion.md`) marque ce qui a changé à la
  dernière passe, mais un bloc de code ne prend pas la coloration en ligne de
  Notion. C'est **la légende juste au-dessus du schéma** qui porte le bleu quand
  le schéma a changé — jamais le bloc Mermaid lui-même.

## Exemple : le plan en un schéma

Rendu par Notion le 2026-09-07 (vérifié : Notion affiche un bloc ```mermaid``` comme
un diagramme, pas comme du texte). Cet exemple est la carte de la page de plan qui
a produit cette étape-ci — reprise ici telle quelle, comme preuve qu'elle passe :

```mermaid
flowchart TD
  classDef det fill:#dbe9ff,stroke:#3b6fd6,color:#000
  classDef agent fill:#efe0ff,stroke:#8b4fd6,color:#000
  classDef toi fill:#ffe3c2,stroke:#e08a1e,color:#000
  classDef data fill:#f1f1f1,stroke:#888,color:#000

  Q{"Tes réponses Q1 à Q7<br>puis Statut = valide"}:::toi
  TEND[("tendances.md<br>77 plans dépouillés, 215 découvertes")]:::data
  subgraph V1["Vague 1 — quatre étapes en parallèle, fichiers disjoints"]
    E1["1 · _partage/schemas.md"]:::det
    E3["3 · enqueteur : gestes 7 à 12<br>+ docs/retex-plans-2026-09.md"]:::det
    E7["7 · brainstorming : trois chemins"]:::det
    E8["8 · ecrire-dans-notion : pièges 4 et 5"]:::det
  end
  subgraph V2["Vague 2 — un seul sous-agent, même fichier"]
    E2["2 · plan-notion : chapitre Cartes"]:::det
    E4["4 · plan-notion : format d'étape, tableau de chevauchement, filtre"]:::det
  end
  subgraph V3["Vague 3 — un seul sous-agent, même fichier"]
    E5["5 · executer : vagues et regroupement<br>+ _partage/vagues.md"]:::det
    E6["6 · executer : ouverture, rapport, État final"]:::det
  end
  E11["11 · en-tête des trois skills :<br>d'où je suis chargé, comment me mettre à jour"]:::det
  E9["9 · versions, README, validation"]:::det
  E10["10 · clôture : cette page relue,<br>schémas à jour, branche poussée"]:::agent
  BR[("branche feat/schemas-tendances-parallelisation<br>PR ouverte, page à a merger")]:::data

  Q --> V1
  TEND --> E3
  TEND --> E4
  E1 --> E2
  E2 --> E4
  E4 --> E5
  E5 --> E6
  E3 --> E9
  E7 --> E11
  E8 --> E9
  E6 --> E11
  E11 --> E9
  E9 --> E10 --> BR
```

## Le schéma de processus (doc fonctionnelle)

Un processus clé de la doc fonctionnelle d'un projet (le chapitre « Processus clés »
de sa vue d'ensemble, sous la page du projet dans `Clients / Projets`) se lit en deux
temps : une vue courte, comprise d'un coup d'œil, puis une frise dépliable où chaque
étape dit comment elle est faite. Ce n'est pas le schéma du plan : il ne répond pas à
*qu'est-ce qui tourne en parallèle ?*, mais à *qui fait quoi, dans quel ordre, avec
quel outil ?*. Il sert à relire un processus sans ouvrir le code.

### La vue courte

Un `flowchart LR` : de gauche à droite, de 5 à 7 boîtes, chacune au libellé métier
(« Extraction du guide », jamais le nom d'un fichier) et précédée de son numéro, que
reprend la frise. Une boîte = une étape métier. Ses sous-étapes techniques (découpe,
lecture, contrôle) ne sont pas des boîtes : ce sont des lignes de son tableau dans la
frise. Une seule suite de flèches : pas de `subgraph`, pas de flèche croisée, parce
qu'un processus est une chaîne.

Chaque boîte porte la classe de son acteur, avec les noms et les couleurs du code
couleur ci-dessus. Seule la légende change : la classe `agent` s'appelle **hermes**,
et la classe `det` s'appelle **ci**. Dans ce schéma, tout agent, sous-agent compris,
prend la classe `agent` ; `det` ne couvre que ce qui tourne sans modèle. Pour les
schémas de processus, la légende de cette section l'emporte sur la ligne `det` du code
couleur (« écriture déterministe, ou sous-agent »). La légende suit toujours le schéma,
en liste.

```mermaid
flowchart LR
  classDef toi fill:#ffe3c2,stroke:#e08a1e,color:#000
  classDef agent fill:#efe0ff,stroke:#8b4fd6,color:#000
  classDef det fill:#dbe9ff,stroke:#3b6fd6,color:#000
  classDef out fill:#dff5e1,stroke:#2e8b57,color:#000

  S1["1 · Dépôt du PDF Routard"]:::toi
  S2["2 · Extraction du guide"]:::agent
  S3["3 · Classement des lieux par étape"]:::agent
  S4["4 · Choix des photos"]:::toi
  S5["5 · Construction du pack"]:::det
  S6["6 · Publication du pack"]:::out

  S1 --> S2 --> S3 --> S4 --> S5 --> S6
```

Légende :
- 👤 **toi**, orange (`toi`) : un geste de Benjamin.
- 🤖 **hermes**, violet (`agent`) : un agent qui lit ou juge.
- 🔁 **ci**, bleu (`det`) : un automatisme sans agent, script Python ou job CI.
- 📦 **out**, vert (`out`) : la sortie livrée.

### La frise

Une boîte de la vue courte donne un `<details>`, titré `N · <nom de l'étape> — <emoji>
<acteur>`, où `N` et le nom sont ceux de sa boîte, à l'identique (acteurs :
👤 Toi, 🤖 Hermes, 🔁 CI, 📦 Livré). Dedans, dans cet ordre : l'entrée, la sortie,
« peut casser », et le lien vers la fiche de la fonctionnalité (une mention de page
Notion, pas un lien d'ancre). Les pièges Notion ci-dessus valent aussi ici.

Chaque `<details>` se termine par le tableau **🔩 Sous le capot** : une ligne par
sous-étape, avec six colonnes. Une étape métier peut compter plusieurs sous-étapes :
elles sont des lignes du même tableau, jamais des boîtes ni des `<details>` à part.

| Colonne | Contenu |
|---|---|
| Sous-étape | ce qui se passe, en mots métier |
| Mécanisme | ⚙️ Python déterministe · 🤖 agent · ⏰ cron · 🔁 CI ; « — » pour un geste de Benjamin |
| Où | le fichier, le skill ou le job, à son vrai chemin |
| Modèle | l'alias du modèle, pour un agent seulement ; « — » sinon |
| effort | le niveau d'effort, pour un agent seulement ; « — » sinon |
| Déclencheur | ce qui lance la sous-étape |

### Exemple : ajouter un routard à Vahiny (données factices)

Le processus « Ajouter un nouveau routard », du dépôt du guide à la publication du pack.
**Données factices** : le guide, les noms de fichiers et les valeurs sont inventés pour
montrer la forme. La rétro-doc de Vahiny posera les vraies.

<details>
<summary>1 · Dépôt du PDF Routard — 👤 Toi</summary>

**Entrée** : le PDF du guide Routard, à déposer dans la page du plan.
**Sortie** : un guide à traiter, identifié par son nom court.
**Peut casser** : un PDF d'une autre édition du guide, et le pack part pour le mauvais guide.
**Fiche** : « Ajouter un routard » (mention de la sous-page du projet).

**🔩 Sous le capot**

| Sous-étape | Mécanisme | Où | Modèle | effort | Déclencheur |
|---|---|---|---|---|---|
| Dépôt du PDF dans la page du plan | — (geste de toi) | page du plan | — | — | à la demande |

</details>

<details>
<summary>2 · Extraction du guide — 🤖 Hermes</summary>

**Entrée** : le PDF du guide Routard.
**Sortie** : le texte du guide en morceaux, encadrés compris, un fichier JSON par morceau.
**Peut casser** : un encadré sur deux colonnes, lu dans le désordre, que le contrôle de forme ne voit pas.
**Fiche** : « Extraire un guide » (mention de la sous-page du projet).

**🔩 Sous le capot**

| Sous-étape | Mécanisme | Où | Modèle | effort | Déclencheur |
|---|---|---|---|---|---|
| Découpe du PDF en pages | ⚙️ Python déterministe | `scripts/decoupe_guide.py` (factice) | — | — | dépôt du PDF |
| Lecture des encadrés (prix, horaires, adresses) | 🤖 agent | `agents/encadres-lecteur.md` (factice) | sonnet | medium | après la découpe, un agent par morceau |
| Contrôle du texte, bloquant | ⚙️ Python déterministe | `scripts/verifier-extraction.py` (factice) | — | — | après la lecture ; un code de sortie 1 arrête la chaîne |

</details>

<details>
<summary>3 · Classement des lieux par étape — 🤖 Hermes</summary>

**Entrée** : les morceaux de l'étape 2.
**Sortie** : un fichier JSON par lieu, rangé dans son étape du voyage.
**Peut casser** : un lieu rangé dans la mauvaise étape, que la construction ne voit pas : elle contrôle la forme et non le sens.
**Fiche** : « Classer les lieux » (mention de la sous-page du projet).

**🔩 Sous le capot**

| Sous-étape | Mécanisme | Où | Modèle | effort | Déclencheur |
|---|---|---|---|---|---|
| Rangement des lieux par étape | 🤖 agent | `agents/classifieur-lieux.md` (factice) | haiku | high | après la lecture, une fois le contrôle vert |

</details>

<details>
<summary>4 · Choix des photos — 👤 Toi</summary>

**Entrée** : les lieux classés par l'étape 3.
**Sortie** : une photo retenue par lieu, dans la page du plan.
**Peut casser** : une photo d'un autre lieu, choisie par erreur, qui part dans le pack.
**Fiche** : « Choisir les photos » (mention de la sous-page du projet).

**🔩 Sous le capot**

| Sous-étape | Mécanisme | Où | Modèle | effort | Déclencheur |
|---|---|---|---|---|---|
| Choix d'une photo par lieu | — (geste de toi) | page du plan | — | — | après le classement, à la demande |

</details>

<details>
<summary>5 · Construction du pack — 🔁 CI</summary>

**Entrée** : les lieux classés et les photos retenues.
**Sortie** : un pack validé, prêt à être publié.
**Peut casser** : un champ vide passe, si la liste des champs obligatoires ne le couvre pas.
**Fiche** : « Construire un pack » (mention de la sous-page du projet).

**🔩 Sous le capot**

| Sous-étape | Mécanisme | Où | Modèle | effort | Déclencheur |
|---|---|---|---|---|---|
| Assemblage du pack | ⚙️ Python déterministe | `scripts/assembler_pack.py` (factice) | — | — | après le choix des photos |
| Contrôle de forme, bloquant | ⚙️ Python déterministe | `scripts/controle_pack.py` (factice) | — | — | après l'assemblage ; un code de sortie 1 arrête la chaîne |

</details>

<details>
<summary>6 · Publication du pack — 📦 Livré</summary>

**Entrée** : un pack validé par l'étape 5.
**Sortie** : le pack disponible pour l'application (factice).
**Peut casser** : une publication qui part avant le contrôle vert.
**Fiche** : « Publier un pack » (mention de la sous-page du projet).

**🔩 Sous le capot**

| Sous-étape | Mécanisme | Où | Modèle | effort | Déclencheur |
|---|---|---|---|---|---|
| Mise en ligne du pack | 🔁 CI | `.github/workflows/publier.yml` (factice) | — | — | push sur `main`, si le contrôle est vert |

</details>

### Tenir le schéma à jour

Un processus qui change (étape ajoutée, agent remplacé, script renommé) : la vue courte
et la frise se réécrivent dans la même passe, jamais l'une sans l'autre. Contrôle à la
main : autant de boîtes dans le schéma que de `<details>` dans la frise, le numéro et
le nom de chaque `<summary>` identiques à ceux de sa boîte, et un tableau « Sous le
capot » dans chaque `<details>`. Aucun script ne le vérifie aujourd'hui.
