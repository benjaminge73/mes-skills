# Écrire dans une page de plan Notion sans rien casser

Fichier **partagé** par `plan-notion` et `executer-plan-notion`. À lire avant la
première écriture dans une page de la base **Plans Claude** — pas de mémoire :
chacune de ces règles a été écrite après un dégât réel, et les citer de tête est
exactement la façon dont on en oublie une.

Il ne dit pas *quoi* écrire — ça, c'est le skill qui appelle. Il dit *comment*
écrire sans détruire ce qui est déjà là.

## Pourquoi ces règles existent

Entre deux passes, la page a vécu : Benjamin a coché des cases, écrit après
`Autre / complément →`, ajouté des remarques à même le corps. **Tout cela est de
la donnée, pas du brouillon** — c'est la seule trace de ses décisions, et le fil
de discussion ne la contient pas. Une passe qui réécrit une section par-dessus
l'efface sans prévenir, parce que recréer un bloc `to-do` le rend vierge.

## Le protocole, dans cet ordre, à chaque passe

1. **Relever avant d'écrire.** Recharger la page et noter, question par question :
   quelles cases sont cochées, et le texte libre exact que Benjamin a ajouté —
   après `Autre / complément →`, dans un encadré, ou en paragraphe isolé.
2. **Éditer de façon ciblée par défaut.** `update_content` sur le bloc concerné
   laisse les autres blocs — et leur état coché — intacts.
3. **Si une refonte de section est nécessaire**, la réécriture doit **remettre
   `- [x]` sur chaque case qui l'était** et **recopier le texte de Benjamin mot
   pour mot**. Le relevé de l'étape 1 est la liste de contrôle ; sans relevé, pas
   de refonte.
4. **Ne jamais reformuler ce que Benjamin a écrit.** Ni corriger, ni condenser, ni
   « intégrer proprement ». Sa formulation reste telle quelle ; la reprise vient
   à côté, pas à la place.
5. **Vérifier après coup, en comptant.** Relire la page et **recompter les
   cases cochées** : le total doit être **exactement** celui du relevé de
   l'étape 1, et chaque texte libre encore présent. Un total **supérieur** dit
   qu'une case a été cochée en passant — c'est le pire dégât possible ici, parce
   qu'il fait passer une proposition pour une décision de Benjamin sans que rien
   ne permette ensuite de les distinguer. Un total **inférieur** dit qu'une
   décision a été effacée. Dans les deux cas : le dire, ne pas corriger en
   silence. Une écriture Notion peut aussi échouer en silence (piège 2).

Le relevé se refait **toujours sur la page fraîche** avant une refonte, jamais sur
un miroir local : c'est précisément entre deux sessions que Benjamin coche.

## Le bleu des retouches

**Ce qui a bougé à la dernière passe s'écrit en bleu ; tout le reste est de la
couleur par défaut.** Une page de plan grossit à chaque passe, et sans repère il faut
la relire en entier pour trouver les trois lignes qui ont changé. Le bleu répond à une
seule question, celle qu'on se pose en rouvrant la page : *qu'est-ce qui est nouveau
depuis la dernière fois que je l'ai lue ?*

C'est donc un marqueur **glissant, pas un historique**. Le bleu ne s'accumule jamais :
à la passe suivante, celui de la passe d'avant redevient neutre. Un bleu cumulatif
finirait par couvrir toute la page, ce qui revient exactement à ne rien marquer.

### Deux temps, et l'ordre compte

1. **Décolorer d'abord.** Retirer le bleu posé à la passe précédente, partout où il
   est.
2. **Écrire ensuite, et colorer ce qu'on vient d'écrire.**

Faire l'inverse décolore ce qu'on vient tout juste de marquer, et la passe ne laisse
aucune trace visible. C'est l'erreur qui vide le dispositif de son sens sans qu'aucun
appel n'échoue.

### Comment

- Un **bloc entier** qui change — paragraphe, puce, `to-do`, titre : `{color="blue"}`
  en fin de première ligne du bloc.
- Une **portion de ligne** seulement : `<span color="blue">…</span>`.
- **Décolorer, c'est retirer le balisage** — l'attribut `{color="…"}` ou le `<span>` —
  et rien d'autre. ⚠️ Il n'existe **pas** de couleur « blanc » ni « défaut » dans
  Notion : l'absence de couleur *est* la couleur par défaut, et elle s'affiche en noir
  ou en blanc selon le thème du lecteur. Écrire `color="white"` ne colore rien et fait
  échouer l'appel.
- La granularité par défaut est **le bloc**, pas le mot. Un diff mot à mot est
  fragile à écrire et illisible à relire ; on veut repérer *où* regarder, pas rejouer
  la modification.

### Cinq choses que le bleu ne touche jamais

- **Une couleur qui porte déjà un sens.** Les encadrés de questions disent leur état
  par leur fond — orange = ouverte, vert = tranchée. Repeindre un tel encadré en bleu
  **détruit cet état**, et le sommaire se met alors à mentir. Dans un encadré de
  question, le changement se marque **ligne par ligne, en `<span>`**, et le fond de
  l'encadré ne bouge pas.
- **Le texte de Benjamin.** Le bleu dit « j'ai écrit ça à cette passe ». Le poser sur
  ses cases cochées ou ses réponses après `Autre / complément →` ferait passer ses mots
  pour les miens. Sa prose ne se colore pas, et ne se décolore pas non plus.
- **La première version d'un plan.** Tout y est nouveau, donc rien n'y est signal. Le
  bleu commence à la deuxième passe.
- **Les suppressions.** Un passage retiré ne laisse aucun bloc à peindre. C'est
  pourquoi la correction datée reste obligatoire et n'est pas un doublon du bleu : le
  bleu dit **où** regarder, la ligne `_maj AAAA-MM-JJ — …_` dit **quoi** et
  **pourquoi**.
- **Un bloc de code, Mermaid compris.** Un ```` ```mermaid ```` est un bloc de code :
  ni `{color="blue"}` ni un `<span>` n'y ont d'effet, et un `<span>` glissé à
  l'intérieur casserait le diagramme lui-même. C'est la légende juste au-dessus du
  bloc qui porte le bleu, et qui dit ce qui a changé dans le schéma.

### Ce que ça coûte, et ce que ça ne risque pas

Le travail de décoloration est borné par **ce qui a changé à la passe précédente**,
jamais par la taille de la page : une passe qui touche trois blocs en décolore trois.

Recolorer un `to-do` **ne décoche rien** : `update_content` remplace le texte du bloc
et laisse son attribut coché intact (piège 1 ci-dessous) — c'est ici la propriété qui
sauve, là où ailleurs c'est le piège. En revanche, **ne jamais recréer un bloc pour le
recolorer** : la recréation, elle, rend la case vierge.

Et parce qu'une passe de couleur touche beaucoup de blocs d'un coup, le recomptage de
l'étape 5 du protocole n'est pas une formalité : c'est le seul contrôle qui attrape une
case perdue au milieu d'une repeinte.

## Six pièges de l'API Notion, vérifiés sur pièce

Les trois premiers datent du 2026-08-17. Les quatrième et cinquième viennent du
journal du plan « Carte d'architecture engendrée » (dépôt Vahiny), vérifiés le
2026-09-07. Le sixième vient du plan « Le design system en deux exemplaires »,
vérifié le 2026-09-11.

1. **`update_content` ne décoche pas.** Il ne change pas l'attribut coché d'un
   bloc `to-do` : il remplace son texte, et **l'appel rend un succès** même si la
   case reste `- [x]` alors que le `new_str` porte `- [ ]`. Seule la recréation du
   bloc décoche, ce qui coûte l'état de toute la section. Conséquence pratique :
   **on ne décoche pas.** Si une case cochée n'a plus de sens, c'est que la
   question a changé de nature — refondre l'encadré entier, relevé en main.
2. **Une écriture peut échouer en silence** quand Notion a normalisé le texte
   cherché : gras et code inline se déplacent, et le `old_str` ne correspond plus.
   D'où l'étape 5 du protocole — après une passe d'écriture, relire la page et
   vérifier que chaque modification a bien pris.
3. **Un commentaire ne peut être ni déplacé ni résolu par l'API.** Et de toute
   façon, **ne jamais résoudre un fil soi-même** : c'est l'accusé de réception de
   Benjamin, et c'est ce qui donne gratuitement la liste à traiter à la passe
   suivante. Un commentaire dont l'ancre n'a pas survécu à une refonte se recopie
   — son texte et la réponse — dans la section `Commentaires repris` de la page.
4. **`replace_all_matches` ne s'emploie jamais sur un motif fait de caractères
   de balisage** (`*`, un accent grave) : le motif atteint aussi l'intérieur
   d'un bloc de code inline, et le remplacement global y altère un fait, pas
   de la mise en forme. Dégât réel : un motif cru anodin a changé un fragment
   de code au passage, sans que rien ne le signale. Geste sûr : cibler chaque
   occurrence une par une, avec un `old_str` qui inclut du texte voisin non
   balisé — jamais le motif balisé seul.
5. **Une insertion s'ancre sur une frontière de bloc, jamais au milieu d'un
   paragraphe formaté.** L'appel **rend un succès** et casse l'italique (ou le
   gras) du paragraphe visé. Geste sûr : ancrer le `old_str` sur la fin
   complète d'un bloc — son dernier caractère — et faire commencer le
   `new_str` par ce même texte suivi d'un saut de ligne, jamais en plein
   milieu d'une phrase balisée.

6. **Insérer des lignes juste avant une liste de `to-do`, dans un encadré, fait
   recréer cette liste — et redistribue les cases cochées.** C'est le pire dégât
   du fichier, parce qu'il fabrique une décision de Benjamin qui n'existe pas.
   Vérifié le 2026-09-11 : trois lignes ajoutées en tête d'un encadré de
   question, et à la relecture la coche de Benjamin était passée sur **l'option
   voisine** dans une question, tandis qu'une autre question, où **rien** n'était
   coché, en portait une. **L'appel rend un succès**, et les `to-do` se
   retrouvent en prime indentés d'un cran de trop, enfants du dernier paragraphe
   inséré. Geste sûr : **écrire après la liste, jamais avant** — ancrer le
   `old_str` sur la dernière option de l'encadré. Si le dégât est déjà fait, la
   réparation passe par un aller-retour `to-do` → paragraphe → `to-do` : c'est
   le seul moyen connu de décocher (piège 1), et elle exige le relevé du §1 sous
   les yeux pour réécrire les bons états, option par option.

**Remarque, vérifiée le 2026-09-08** sur la page du plan qui commande cette
étape : Notion transforme un nom de fichier nu comme `CLAUDE.md` ou
`SKILL.md` en lien `http://…` dès qu'il n'est pas entre accents graves.
Toujours écrire ces noms en code inline, jamais en texte nu.

## Rappel de vocabulaire

Les valeurs de la propriété `Statut` sont **sans accents** : `brouillon`,
`en revue`, `valide`, `en cours`, `a merger`, `execute`, `archive`. Écrire
`exécuté` fait échouer l'appel avec une `validation_error`.

`a merger` et `execute` se distinguent par **où vit le travail** : sur sa branche
pour le premier, sur `main` pour le second. Un plan livré mais non remonté reste
à `a merger` — c'est la vérité, pas un oubli. Et **dès que la branche part sur
`main`, la page passe à `execute` dans le même tour que le merge** : le statut
suit le code, et une page restée à `a merger` sur du travail déjà remonté annonce
un chantier en attente qui n'existe plus.
