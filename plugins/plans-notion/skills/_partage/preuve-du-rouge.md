# La preuve du rouge

Fichier **partagé**, lu par `executer-plan-notion` (§3, dans « Une étape = un
commit sur la branche du plan, prouvé en local ») et par `executant` (règle
« Ce que tu ne fais jamais »), pour une étape qui écrit du code testé. Comme
`vagues.md` et `schemas.md`, il vit à un seul endroit pour que le skill garde
sa taille : la règle ne se duplique pas, elle se référence.

Il ne dit pas *comment* rejouer la suite complète (§6 du skill) ni *quand*
paralléliser (`vagues.md`). Il dit *comment* prouver qu'un test a mordu avant
de le faire passer, et *comment* vérifier que le code qui le fait passer ne
l'a pas simplement fait taire.

## Pourquoi ce fichier

La règle « test d'abord » vit déjà dans les `CLAUDE.md` des dépôts de travail.
Ce qui manque, ce n'est pas la règle : c'est la **preuve** qu'elle a été
suivie. Aujourd'hui, le rouge est une affirmation du sous-agent dans son
rapport — rien ne la rejoue.

- **ImpossibleBench** (arXiv 2510.20270) montre que des agents modifient les
  tests pour faire passer la barre quand la tâche s'avère impossible — 76 %
  des cas pour GPT-5 sur OneOff-SWEbench. Des tests en lecture seule ramènent
  cette triche vers zéro.
- Kent Beck (« Augmented Coding: Beyond the Vibes ») rapporte le même geste :
  l'agent supprime des tests plutôt que de les faire passer.
- Un `git diff` vide entre le commit rouge et le commit vert, sur les fichiers
  de test, est la version mécanique de « tests en lecture seule » : personne
  n'a besoin de faire confiance au rapport du sous-agent sur ce point
  précis, un `git diff` vide ou non se lit sans interprétation.
- Un test jamais vu rouge peut ne rien tester — un mauvais import, une
  assertion qui passe toujours. Le voir échouer d'abord prouve qu'il mord.

Décision de Benjamin du 2026-09-23 (plan « Preuve du rouge, revue au regard
neuf et hygiène des branches »).

## Le brief : deux messages de commit, une liste de fichiers de test

Pour une étape qui écrit du code testé, le brief de l'exécutant (§3, point 1
et 3 du skill) porte, en plus de l'objectif et de la liste fermée de
fichiers :

- **Le message du commit rouge**, tests seuls : `test(…): étape N — rouge`.
- **Le message du commit vert**, code : `feat(…): étape N — …` (ou `fix(…)`,
  selon la nature de l'étape).
- **La liste des fichiers de test** de l'étape — celle que le pilote vérifie
  ensuite au `git diff`.

L'exécutant commite **d'abord** les tests seuls, puis le code — deux commits,
jamais un seul qui mélange les deux. C'est la seconde exception à la règle
« ni `commit` » du brief standard (`executant.md`, « Ce que tu ne fais
jamais »), au même titre que le regroupement de deux étapes (`vagues.md`) :
sur ordre explicite du brief, et seulement dans ce cadre.

## Le geste du pilote : rejouer les tests sur le commit rouge

Le pilote — la session qui exécute le plan — rejoue la commande de preuve du
brief sur le **premier** commit, celui qui ne porte que les tests, avant de
regarder le second.

**Pas de `git checkout <sha-rouge> -- .`** : cette forme plaque l'arbre du
commit sur l'index et le répertoire de travail courants sans déplacer `HEAD`
— elle mélange le contenu du commit rouge avec l'état local (fichiers non
suivis, suppressions non prises en compte), et rien ne dit « je suis ailleurs
maintenant » tant qu'on n'a pas tout réverté à la main.

**Pas de worktree jetable non plus**, malgré la cohérence avec l'idiome que
`vagues.md` utilise déjà pour isoler une étape parallèle — écarté pour deux
raisons concrètes, pas de style :

1. **Un worktree neuf n'a ni `node_modules` ni `.venv`** : ces répertoires
   sont ignorés par git, donc absents de tout arbre fraîchement extrait.
   `npx vitest`, `pytest` ou tout runner y échouerait pour une raison
   d'environnement — un faux rouge, qui ne dit rien du test.
2. **La règle globale du poste réserve `~/repos/worktrees/<repo>/…` aux
   worktrees d'étape**, avec leur branche propre ; un worktree jetable ailleurs
   (`/tmp` ou autre) en sort.

**La forme retenue : `git switch --detach`, dans le worktree de l'étape
lui-même** — celui qui porte déjà les dépendances installées, `node_modules`
et `.venv` compris, puisque ce sont des fichiers ignorés qui survivent au
`switch`. Le mode de panne identifié plus haut (une interruption entre le
`switch --detach` et le retour laisse le worktree détaché) ne disparaît pas :
il se **couvre par un garde-fou explicite**, pas par le choix de la commande.

**Avant le switch, l'arbre doit être propre** — `git status --short` vide.
Un switch sur un arbre sale échoue, ou pire, emporte des modifications locales
sur le commit rouge sans le dire.

```bash
git status --short                # doit être vide avant de commencer
git switch --detach <sha-rouge>
<commande de preuve du brief>     # attendu : rouge
git switch <branche>              # la branche d'étape, ou celle du plan
git branch --show-current         # doit afficher <branche> : le garde-fou
```

**Le pilote ne commite ni ne pousse jamais tant que `git branch
--show-current` n'a pas rendu la branche attendue.** C'est cette dernière
ligne, pas la nature de la commande, qui couvre l'interruption : un `switch`
de retour oublié ou raté laisse le worktree détaché, et le garde-fou le dit
avant que quoi que ce soit d'autre ne s'exécute dessus.

## Trois issues

**Rouge sur le commit rouge, comme attendu.** Le pilote recopie cette sortie
au journal (§4 du skill) — c'est la preuve que le test mord. Il regarde
ensuite le second commit.

**Vert sur le commit rouge : le test ne mord pas.** L'étape n'est pas finie,
même si un commit existe. Le test ne teste rien tant qu'il ne peut pas
échouer — un mauvais import, une assertion toujours vraie, une fixture qui ne
couvre pas le cas visé. Retour au sous-agent avec la sortie verte et la
demande de corriger le test, pas le code ; un nouveau commit rouge remplace
l'ancien.

**`git diff <sha-rouge>..HEAD -- <fichiers-de-test>` n'est pas vide.** Le
code a retouché un fichier que le rouge avait déjà jugé — exactement ce que
la preuve du rouge existe pour empêcher. L'étape repart : le commit vert ne
doit toucher aucun fichier de test. Si le test était réellement faux — une
assertion mal posée, découverte en écrivant le code — ce n'est pas un
contournement mais une décision, et elle se note au journal au format « quoi
— pourquoi — ce que ça coûte si c'est faux », avec un **nouveau commit
rouge** qui rejoue tout le geste ci-dessus depuis le début.

## La ligne de journal

L'entrée d'étape (§4 du skill) porte, pour une étape à deux commits, les deux
SHA et la sortie rouge en plus de la sortie verte habituelle :

```
Étape N — <titre>
Commit rouge <sha-rouge> : test(…): étape N — rouge
  <sortie rouge, telle quelle>
Commit vert <sha-vert> : feat(…): étape N — …
  <sortie verte, telle quelle>
git diff <sha-rouge>..<sha-vert> -- <fichiers-de-test> : vide
```

## Avec une vague, avec un regroupement

**Vague** (`vagues.md`) : chaque étape parallèle a son propre worktree et sa
propre branche d'étape. Les deux commits — rouge puis vert — se reportent sur
la branche du plan par `cherry-pick`, dans l'ordre, comme n'importe quel
commit d'étape : deux `cherry-pick` au lieu d'un, toujours avant le retrait
du worktree et de la branche (`vagues.md`, « Au retour »).

**Regroupement de deux étapes** (`vagues.md`) : quatre commits, dans l'ordre
— rouge de l'étape 1, vert de l'étape 1, rouge de l'étape 2, vert de l'étape
2. Le sous-agent commite chaque étape avant d'ouvrir la suivante, comme le
prescrit déjà le regroupement ; le pilote rejoue la preuve du rouge sur les
deux commits rouges séparément, et vérifie le `git diff` sur chacune des deux
paires.

## Exceptions : pas de commit rouge

- **Étape de doc ou de config** : la preuve est le lint ou le build des
  fichiers touchés, comme le prévoit déjà §3 du skill pour une étape sans
  test. Pas de commit rouge, rien à rejouer en deux temps.
- **Refactor pur** : la preuve est verte avant, verte après — le
  comportement ne change pas, il n'y a rien à voir rouge. Un commit suffit,
  comme pour une étape ordinaire.

Zéro hook, zéro appel en plus dans les deux cas : la preuve du rouge ne
s'applique qu'à une étape qui écrit du code neuf sous test.
