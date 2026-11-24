# La revue au regard neuf

Fichier **partagé**, lu par `executer-plan-notion` (§3, dans « Après chaque
étape »), pour faire relire chaque étape — ou chaque lot d'étapes — par
l'agent `relecteur`. Comme `vagues.md` et `preuve-du-rouge.md`, il vit à un
seul endroit pour que le skill garde sa taille : la règle ne se duplique pas,
elle se référence.

Il ne dit pas *ce que* le relecteur cherche — ça vit dans
`${CLAUDE_PLUGIN_ROOT}/agents/relecteur.md`, les quatre catégories et le
format de remarque. Il dit *quand* l'appeler, *comment* le brief, et *comment*
boucler jusqu'à un verdict propre.

## Quand

**Deux régimes**, lus dans la colonne « Relecture » du tableau du chapitre
`Exécution` (`Étape · Fichiers touchés · Dépend de · Vague · Relecture` —
`plan-notion` l'écrit, le pilote la lit) :

- **`étape`** — relue **seule**, une fois la preuve rejouée verte par le pilote
  et l'étape commitée, **avant** l'entrée de journal (§4 du skill) : la revue et
  ses éventuels correctifs apparaissent dans le journal de l'étape, pas dans
  une entrée séparée après coup. Portée : la plage de commits de l'étape,
  `<base>..<tête>` — un commit pour une étape ordinaire, deux (rouge, vert) pour
  une étape testée (`preuve-du-rouge.md`), quatre pour un regroupement
  (`vagues.md`).
- **`lot`** — **pas de relecture à l'étape.** Des étapes `lot` consécutives
  forment **un lot**, relu **en une fois, à la preuve de fin de lot** : la
  dernière étape du lot commitée et sa preuve rejouée verte, un seul appel sur
  la plage `<base>..<tête>` qui couvre tout le lot. Le lot se ferme à la
  première étape `étape` qui suit, ou à la dernière étape du plan. Le journal
  de chaque étape du lot dit `Revue — avec le lot (étapes N à M)` ; la ligne
  `Revue` complète (voir plus bas) se pose sous la **dernière** étape du lot.
  Un correctif se commite sur la branche du plan : `fix(…): lot N à M — revue`.
- **Colonne absente** (plan écrit avant elle) : `étape` partout — c'est le
  régime d'avant, le plus prudent, et c'est celui que le pilote applique. Le script `--apres`,
  lui, ne lit aucune puce `Relecture` dans ce cas et ne contrôle pas la ligne `Revue` de ces
  étapes : la relecture seule n'y est tenue que par le pilote.

**Une étape de vague** (`vagues.md`) : si elle est `étape`, la revue a lieu
**dans le worktree de l'étape, sur sa branche d'étape** — avant le report par
`cherry-pick` sur la branche du plan (`vagues.md`, « Au retour », étape 3). Un
correctif de revue se commite dans ce même worktree, et se reporte avec le
reste de l'étape : sans ça, le report emporterait un diff que le relecteur n'a
jamais vu. Si elle est `lot`, le lot se relit **sur la branche du plan**, après
le report de toutes ses étapes, dans l'ordre des numéros.

**Pourquoi deux régimes.** Décision de Benjamin du 2026-09-23 (Q2) : relire
**après chaque** étape, sans distinction. **Remplacée par la décision du
2026-09-30 (Q6)** : la vérification se proportionne. Un appel Opus par étape
coûte autant pour une étape de doc de dix lignes que pour une migration ; le
plan dit, étape par étape, laquelle mérite son regard seul (`étape`) et
lesquelles se relisent d'un seul coup (`lot`). Le régime `étape` est
exactement celui du 2026-09-23 ; seul le second est nouveau.

## Comment l'appeler

Un appel `Agent` avec `subagent_type: "plans-notion:relecteur"` — nom
qualifié, le nom court ne résout pas, comme pour `plans-notion:executant`
(§3 du skill). **Sans paramètre `model`** : le frontmatter de l'agent porte
`opus` et `effort: medium`, et c'est le même principe que pour l'exécutant — le
modèle garanti par construction plutôt que par une discipline d'appel.

Le brief du relecteur, et rien de plus :

1. **L'objectif de l'étape**, recopié du chapitre `Exécution` — pas résumé.
2. **Le répertoire** où travailler : le worktree de l'étape pour une vague,
   sinon le worktree du plan — jamais le checkout principal (§2 du skill).
3. **La plage de commits**, `<base>..<tête>`.
4. **La tête attendue**, un SHA : le commit que le répertoire doit avoir en tête
   pour que le rejeu d'un test porte sur l'étape. Relève-le par `git rev-parse`
   et donne-le tel quel, pas un nom comme `HEAD` qui bouge. Le relecteur le
   compare à la tête du répertoire avant tout rejeu (`relecteur.md`, « Avant de
   rejouer un test »).

**Rien de la session** : ni le plan entier, ni la discussion, ni pourquoi tel
choix a été fait — c'est tout l'intérêt d'un regard neuf (`relecteur.md`,
« Pourquoi cet agent existe »). Aux tours suivants, le brief change : les
seuls correctifs depuis le dernier passage (nouvelle plage, donc nouvelle tête attendue), plus les
remarques que le pilote a écartées et sa raison de le faire.

**Mode plan entier.** Il se joue **une fois**, à la clôture, après la suite
complète et avant la porte (`cloture.md`, point 2 ter). Par exception à « Rien
de la session », son brief porte aussi le chapitre `Exécution` du plan, recopié,
et le mot « mode plan entier » ; la plage est `origin/main..<branche-du-plan>`, sa tête attendue le SHA de la branche à la clôture,
le répertoire le worktree du plan. La boucle ci-dessous s'applique telle quelle.
Chaque écart rendu (`relecteur.md`, « Le mode « plan entier » ») devient une
découverte traitée selon `decouvertes.md` : étape `D<n>` dans le même plan si
elle est réversible, hors sécurité et petite ; question à Benjamin sinon, avant
`a merger`.

## La boucle

Décision de Benjamin du 2026-09-23 (Q4) : « pas de nouveau plan, on itère
jusqu'à ce que ce soit ok pour le reviewer. »

Avant tout, le pilote vérifie que le rapport ouvre par le bloc `Liste parcourue` : neuf lignes, A à H puis « Hors liste », chacune « rien » ou des numéros `R<n>` (`relecteur.md`, « La liste, puis les quatre catégories »). **Un rapport sans ce bloc est refusé** : le pilote ne le lit pas, il le renvoie au relecteur, et le renvoi compte comme un tour.

Le relecteur rend `RIEN À SIGNALER` ou `REMARQUES (n)`. Pour chaque remarque :

1. **Le pilote la vérifie avant d'agir** — relit le code visé, rejoue une
   commande si besoin. Ni accord de façade, ni correctif aveugle : le
   discernement reste dans la session qui a le contexte pour le faire.
2. **Retenue** : elle se corrige comme n'importe quel correctif — délégué à
   l'agent `plans-notion:executant`, avec un brief qui porte la remarque et
   son `fichier:ligne`. Commit `fix(…): étape N — revue`.
3. **Écartée** : avec une raison écrite, au journal — pas un silence, une
   phrase qui dit pourquoi. Une remarque `Sécurité (hors diff)` ne se corrige
   pas dans l'étape : elle est écartée *de l'étape* avec la raison « traitée en
   découverte », et suit le traitement de `executer-plan-notion` §4 (question à
   Benjamin, jamais de correctif seul).

Une remarque `Découverte hors plan` (quatrième catégorie du relecteur) passe par
la même vérification (point 1). Elle n'est **pas** corrigée dans l'étape relue :
c'est un défaut réel que l'étape n'a pas causé et que son objectif ne demande
pas. Elle suit `_partage/decouvertes.md` : une étape `D<n>` si elle est
réversible, hors sécurité et petite ; une question à Benjamin sinon. Le
garde-fou « trois tours » ci-dessous ne change pas pour elle. Écartée de
l'étape, elle entre dans le brief des tours suivants avec sa raison, comme les
autres remarques écartées.

Puis nouvel appel au relecteur, brief réduit aux seuls correctifs (nouvelle
plage de commits, donc nouvelle tête attendue) plus les remarques écartées et leurs raisons. Le relecteur
prend position sur chacune — maintenue avec un argument nouveau, ou
abandonnée (`relecteur.md`, « Aux tours suivants »). On recommence jusqu'à
`RIEN À SIGNALER`. **Aucun tour de cette boucle n'ouvre de plan de suite** :
une remarque de revue se règle dans l'étape, pas dans une page à part (sauf la
`Découverte hors plan` ci-dessus : étape `D<n>` du même plan, ou question).

## Garde-fou

**Trois tours de suite** où le relecteur maintient une remarque contre l'avis
argumenté du pilote : ça remonte à Benjamin **dans la session** — pas un plan
de suite, une ligne dans le fil. L'exécution continue sur les étapes qui n'en
dépendent pas pendant qu'on attend son arbitrage.

**Corriger une remarque exige de revenir sur une décision du plan** — schéma
de données, contrat d'API, dépendance : c'est l'arrêt déjà prévu au §3 du
skill, « L'autonomie est le défaut ». Une décision qui engage va à Benjamin,
qu'elle vienne d'un rouge en cours d'étape ou d'une remarque de revue ne
change rien à la règle.

## Les preuves après correctif

Un correctif de revue rejoue la preuve de l'étape — les tests des fichiers
impactés (§3 du skill, « précisément ») — avant d'être renvoyé au relecteur.
S'il touche un fichier de test, la preuve du rouge s'applique : c'est une
décision à journaliser au format « quoi — pourquoi — ce que ça coûte si
c'est faux » (`preuve-du-rouge.md`).

## Journal

Sous l'entrée de l'étape (§4 du skill), une puce `- **Revue** : …` (clé en gras, comme
les autres champs du journal). Le script accepte aussi l'ancienne forme, `Revue — N tour(s) : …`
(sans gras ni tiret, celle des plans écrits avant cette forme) ; un plan neuf écrit la forme en gras :

```
- **Revue** : N tour(s)
  [écart au plan] fichier:ligne — retenue, fix abc1234
  [bug] fichier:ligne — écartée : <raison>
  Verdict final : RIEN À SIGNALER
```

Une ligne par remarque, quel que soit le tour où elle est apparue. Une remarque
`Découverte hors plan` s'y écrit « traitée en découverte », comme une remarque
`Sécurité (hors diff)` : elle ne se corrige pas dans l'étape. Cette puce est
**exigée** pour une étape dont la puce `Relecture` du chapitre vaut `étape` :
`preuves-des-etapes.py --apres` refuse l'étape qui ne la porte pas (code 1, son numéro
nommé). Une étape sans puce `Relecture` au chapitre n'est pas contrôlée sur ce point, pas
plus qu'une étape `lot` : le script ne voit pas son régime. Une étape écartée, jamais jouée, n'a
pas de revue à tracer : son entrée porte `**Verdict** : unverifiable — étape écartée` (le mot
« écartée » dans l'entrée), et le script l'exempte alors de la ligne Revue, de la Maquette et de la
puce Effets.

## Coût assumé

Un appel Opus effort `medium` par étape marquée `étape` et par lot, plus un par
tour de correction, plus un pour le plan entier — décisions de Benjamin du
2026-09-23 et du 2026-09-30 pour
le régime, et du 2026-10-16 pour l'effort `high` (il remplace le `low` posé le
2026-09-23), et du 2026-11-23 pour l'effort `medium` (il remplace le `high` posé
le 2026-10-16).
Avant ce fichier, le pilote ne rejouait que des tests, jamais un
regard neuf sur le diff : c'est exactement la dérive que superpowers
`executing-plans` met en garde — « Do not skip it, and do not replace it with
your own read of the diff » — un pilote qui a écrit ou brief l'étape partage
les angles morts de celui qui l'a écrite.

Le coût de l'ombre, environ 0,3 dollar par étape relue tant qu'elle tourne, s'ajoute à celui-ci : voir « L'ombre de relecture ».

## L'ombre de relecture

Une ombre rejoue le brief d'une étape relue en régime `étape` sur trois Haiku high (la checklist de `_partage/listes/relecture-code.md`), puis sur la chaîne qui vérifie leurs remarques, et un bras Sonnet medium compté à part. Elle ne décide rien : elle mesure, sur de vraies étapes, si la chaîne peut remplacer Opus. Le bilan qui tranche est `evals/banc-relecture/bilan_ombre.py`, et sa règle est dans `evals/banc-relecture/README.md`.

Le geste, pour le pilote, après chaque relecture d'étape :

1. **Lancer l'ombre en tâche de fond** (`run_in_background`), dès que le rapport d'Opus est reçu, depuis un checkout de `mes-skills` (le script vit dans ce dépôt, pas dans le plugin installé) :
   `python3 evals/banc-relecture/ombre.py --id <id> --brief <brief.txt> --rep <worktree de l'étape> --depot <dépôt de l'étape> --debut <base> --fin <tête> --opus <rapport-opus.md>`
   `<id>` tient en lettres, chiffres, `.`, `_` et `-` (par exemple `<plan>-e<n>`). Le brief est le fichier même envoyé au relecteur, et le rapport d'Opus est écrit dans un fichier avant l'appel.
2. **Traiter les remarques d'Opus** comme d'habitude (boucle ci-dessus), en notant celles que tu retiens dans un fichier de tri.
3. **À la fin de l'ombre** (notification), lire son rapport de chaîne (`chaine.result` dans `$BANC_DONNEES/ombres/ombre-<id>.json`, par défaut `~/.local/share/banc-relecture`) et trier chaque remarque de la chaîne : celle qu'Opus ne fait pas (`origine` `ombre`, `verdict` `réelle` si elle est fondée, `bruit` sinon) et celle qu'Opus fait aussi mais que tu écartes (`origine` `commune`, `verdict` `écartée`, comptée comme bruit de la chaîne). Une remarque de l'ombre seule jugée réelle entre au bilan même si tu ne la retiens pas : juger et corriger sont deux gestes. Tu ne la corriges que si tu la retiens, par la boucle de revue ; jamais parce qu'elle vient de l'ombre.
4. **Écrire le tri** au format suivant, puis relancer la même commande avec `--retenues <fichier>` : elle valide le tri et le range à côté de l'ombre, sans rejouer une seule relecture (une sortie de chaîne déjà présente n'est pas relancée).
   ```json
   {"remarques": [
     {"origine": "opus", "verdict": "retenue", "gravite": "bug (correction)", "categorie": "D", "resume": "..."},
     {"origine": "commune", "verdict": "retenue", "gravite": "autre", "resume": "..."},
     {"origine": "ombre", "verdict": "réelle", "gravite": "autre", "resume": "..."},
     {"origine": "ombre", "verdict": "bruit", "gravite": "autre", "resume": "..."}
   ]}
   ```
   `origine` : `opus` (remarque d'Opus retenue, que l'ombre n'a pas), `commune` (Opus et l'ombre la disent, retenue), `ombre` (de l'ombre seule, triée). `gravite` commence par `bug` pour un défaut de correction, sinon `autre`. Une remarque d'Opus écartée ne s'écrit pas ici : elle reste au journal, avec sa raison.
`categorie` (facultatif, A à H) : la lettre de la catégorie de la liste de relecture qui aurait dû la voir.

Le bilan se lance à la date fixée par le plan, jamais dans une étape : `python3 evals/banc-relecture/bilan_ombre.py [--depuis AAAA-MM-JJ]`. Il rend une recommandation (`bascule`, `hybride`, `statu quo` ou `pas assez d'étapes`) et ne bascule rien : la décision reste à Benjamin.

## Les étapes sans code

Les étapes sans code (doc, config) sont relues comme les autres : la revue
porte sur l'écart au plan autant que sur les bugs, et un fichier de doc peut
dériver de son objectif sans qu'aucun test ne le voie.
