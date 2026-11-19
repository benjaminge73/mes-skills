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

Les deux messages se terminent par le trailer exact `Co-Authored-By: Claude <noreply@anthropic.com>`, sans nom de modèle : règle détaillée dans `etapes.md`, au paragraphe « Le trailer, quand il commite ».

L'exécutant commite **d'abord** les tests seuls, puis le code — deux commits,
jamais un seul qui mélange les deux. C'est la seconde exception à la règle
« ni `commit` » du brief standard (`executant.md`, « Ce que tu ne fais
jamais »), au même titre que le regroupement de deux étapes (`vagues.md`) :
sur ordre explicite du brief, et seulement dans ce cadre. Dans la forme à
deux exécutants (section « Deux exécutants », plus bas), ce n'est pas un
exécutant qui commite : c'est le pilote, le rouge comme le vert.

## Deux exécutants : le second ne touche pas au test

Une étape testée peut se faire en deux appels d'`executant` enchaînés
(`executer-plan-notion`, `etapes.md`, §3). C'est le pilote qui choisit cette
forme, dans le brief ; le sous-agent ne la décide pas.

- **Le premier exécutant** n'écrit que les tests de l'étape, les joue, et rend
  sa sortie rouge. Il ne touche à aucun code et ne commite rien.
- **Le pilote commite le rouge** (tests seuls, `test(…): étape N — rouge`),
  puis rejoue la preuve sur ce commit, comme décrit plus haut.
- **Le second exécutant** reçoit dans son brief le SHA de ce commit rouge et la
  liste des fichiers de test, **en lecture seule**. Il écrit le code qui les
  fait passer, et ne modifie aucun de ces fichiers : ni assertion, ni import,
  ni `skip`, ni nouveau fichier de test. Il ne commite pas non plus.
- **Le pilote contrôle, puis commite le vert.** Les deux contrôles se jouent
  **avant** le commit, sur l'arbre de travail, et doivent être vides :
  `git diff <sha-rouge> -- <fichiers-de-test>` (sans `..HEAD` : à ce moment
  HEAD est encore le commit rouge, et une plage entre deux commits ignore
  l'arbre de travail) et `git status --porcelain -- <dossier des tests>` (aucun
  fichier de test nouveau ou modifié, fichiers non suivis compris). Un résultat
  non vide, c'est l'étape qui repart, comme dans la section « Trois issues ».

Si le second exécutant croit le test faux, il ne le corrige pas : il rend
`BLOCKED`, avec l'assertion en cause et la raison. Le pilote tranche : un
nouveau commit rouge, qui rejoue tout le geste depuis le début, ou une étape
bloquée. Celui qui n'a pas écrit le test ne le réécrit pas.

## Le contrôle du vert, par script

Le `git diff` ci-dessus se joue aussi en une commande, sur les deux SHA :

```bash
python3 plugins/plans-notion/skills/_partage/scripts/verifier-rouge-vert.py <sha-rouge> <sha-vert> [--tests <chemin> ...]
```

- **Code 0** : entre le rouge et le vert, aucun fichier de test n'a bougé (le vert ne touche que le code).
- **Code 1** : un fichier de test a été ajouté, modifié ou supprimé. La liste dit pourquoi : test désactivé (`skip`, `xfail`, `skipTest`), assertion retirée ou remplacée par `assert True` / `pass`, fichier supprimé. L'étape repart.
- **Code 2** : panne (SHA inconnu, dossier qui n'est pas un dépôt git). À corriger avant de conclure quoi que ce soit.

`--tests` liste les fichiers ou dossiers de test (relatifs à la racine du dépôt) ; sans lui, un fichier est tenu pour un test s'il est dans `tests/`, `test/` ou `__tests__/`, ou si son nom suit `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`. Le script ne lit que les deux commits : il se joue donc sur le commit vert une fois créé, en local, avant le push. Sur un code 1, on défait ce commit local (`git reset --soft HEAD~1`), on corrige, et on rejoue. Il ne remplace pas le rejeu du rouge ci-dessous : il prouve seulement que le vert n'a pas touché les tests.

## Le geste du pilote : rejouer les tests sur le commit rouge

Le pilote — la session qui orchestre le plan — rejoue la commande de preuve du
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

**`git diff <sha-rouge> -- <fichiers-de-test>` ou `git status --porcelain -- <dossier des tests>` n'est pas vide.** Le
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

## Une preuve d'idempotence compare le contenu, pas les compteurs

Le même principe — une affirmation ne vaut que rejouée, jamais recopiée de
mémoire — s'applique à une preuve d'idempotence (rejouer un traitement deux
fois doit produire le même résultat) : elle compare le **contenu réel** des
fichiers produits, `cmp -s` en main, cartes et propositions comprises —
jamais un compteur de bilan. Constaté deux fois : un compteur passé de « 64 à
3 » a fait croire à une perte, alors qu'il ne comptait que les nouveautés du
tour (fausse alerte) ; à l'inverse, des compteurs identiques d'une passe à
l'autre cachaient un champ qui dérivait réellement — un vrai bug, trouvé
seulement en comparant les fichiers eux-mêmes.

## Exceptions : pas de commit rouge

- **Étape de doc ou de config** : la preuve est le lint ou le build des
  fichiers touchés, comme le prévoit déjà §3 du skill pour une étape sans
  test. Pas de commit rouge, rien à rejouer en deux temps.
- **Refactor pur** : la preuve est verte avant, verte après — le
  comportement ne change pas, il n'y a rien à voir rouge. Un commit suffit,
  comme pour une étape ordinaire.

Zéro hook, zéro appel en plus dans les deux cas : la preuve du rouge ne
s'applique qu'à une étape qui écrit du code neuf sous test.
