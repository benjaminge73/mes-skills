# Tester un skill avant de le publier

Ce dépôt est public et ses plugins partent dans **toutes** les sessions de
Benjamin dès le merge (voir `CLAUDE.md`, « Ouvrir une PR ici, c'est demander la
publication »). La CI vérifie des manifestes, des renvois et un numéro de
version ; elle ne dit **rien de la justesse d'une consigne**. Ce document dit
comment on la prouve.

La règle vit ici, à la racine, et non dans un plugin : elle concerne qui
**modifie** un skill de ce dépôt, pas qui s'en sert ailleurs. Un fichier
`_partage/` l'aurait envoyée chez tous les utilisateurs et aurait exigé une
montée de version à chaque retouche.

- [Deux paliers](#deux-paliers)
- [La veille avant la PR](#la-veille-avant-la-pr)
- [Écrire un cas](#écrire-un-cas)
- [Le format d'un cas](#le-format-dun-cas)
- [Mesurer le bruit avant de fixer un seuil](#mesurer-le-bruit-avant-de-fixer-un-seuil)
- [Comparer deux versions](#comparer-deux-versions)
- [Choisir les évals d'une PR](#choisir-les-évals-dune-pr)
- [Lancer une évaluation](#lancer-une-évaluation)
- [La fumée : ce qu'elle voit, ce qu'elle ne voit pas](#la-fumée--ce-quelle-voit-ce-quelle-ne-voit-pas)
- [Rejeu réel : quand et combien](#rejeu-réel--quand-et-combien)
- [Ce que la méthode interdit](#ce-que-la-méthode-interdit)
- [Où tourne quoi](#où-tourne-quoi)
- [Le jeton de CI](#le-jeton-de-ci)

## Deux paliers

| Palier | Où | Quand | Ce qu'il prouve |
|---|---|---|---|
| **Cas simulés**, publics | `evals/<plugin>/` dans ce dépôt | joués en CI **à la demande** (label `evals`, [voir plus bas](#choisir-les-évals-dune-pr)) ; sans le label, une [fumée](#la-fumée--ce-quelle-voit-ce-quelle-ne-voit-pas) à chaque PR qui touche `skills/`, `agents/`, un hook ou `_partage/` | qu'une consigne produit le bon état final sur une situation inventée |
| **Cas réels**, privés | `bancs/skills/` dans le dépôt privé `hermes-custom` | rejoués **en local** pour tout changement de doctrine | que la consigne tient sur de vraies situations, qu'on ne publie pas |

Le second palier est privé parce que les cas réels contiennent des noms de
dépôts, de plans et de pages Notion. Le premier est le filet de tous les jours ;
le second est celui qu'on rejoue quand la **doctrine** bouge (une règle qui
change de sens, pas une reformulation).

Les cas simulés sont joués par `claude plugin eval` (natif Claude Code), qui
lit `evals/<cas>/case.yaml` — ou `prompt.md` plus `graders/*.md` — et joue
**3 passages par cas**. Ils vivent à la racine du dépôt et non dans les
plugins : `experimental.evals` hors de la racine du plugin est ignoré, et
`scripts/evals_ab.py` les assemble donc dans une copie temporaire du plugin au
moment de jouer.

## Écrire un cas

**Un juge se prouve avant de juger.** Pour chaque cas, avant de le garder :

1. **un oracle** — une sortie écrite à la main, qu'on sait bonne — **passe** ;
2. **un témoin nul** — une sortie vide, ou l'état de départ sans rien faire —
   **échoue**.

Un cas dont le témoin nul passe ne mesure rien : il est trop indulgent. Un cas
dont l'oracle échoue mesure autre chose que ce qu'on croit.

Ensuite :

- **Juger l'état final** — un fichier écrit, un commit fait, une commande
  lancée — **jamais le récit** que le modèle en fait. Un modèle raconte très bien
  ce qu'il n'a pas fait.
- **Des cas négatifs** : la situation où le skill ne doit **pas** se déclencher,
  ou doit refuser. Un banc fait de seuls cas positifs récompense un skill qui
  se déclenche sur tout. Compter 15 à 100 cas au total, dont des négatifs.
- **Les juges gratuits d'abord** : `regex`, `tool_used`, `file_exists`. Le juge
  `llm` coûte et bruite sur les longs fichiers ; on préfère un `regex` sur un
  bloc court et structuré. Un `regex` sur un fichier se déclare
  `target: {source: file, path: …}` et lit le disque **en fin de passage** : un
  fichier créé, modifié **ou préexistant**. `file_exists`, lui, ne voit que les
  fichiers **créés pendant le passage**.
- **`tool_used` : `min` vaut 1 par défaut.** « Jamais appelé » s'écrit donc
  `min: 0` **et** `max: 0` ; avec `max: 0` seul, le juge échoue toujours. Et
  pour qu'un skill de plugin puisse être appelé, `Skill` doit figurer dans
  `allowed_tools`. Un cas dont un juge ne peut pas passer avec les outils
  accordés émet un avertissement au chargement : le lire.
- **Les tags filtrent avec `--tag`**, qu'ils soient posés dans le frontmatter de
  `prompt.md` ou dans `case.yaml` (`tags: [lecture]`). Un cas qui a besoin de
  Bash n'a simplement pas le tag `lecture` : il ne se joue alors que sur le
  runner GitHub (voir [Où tourne quoi](#où-tourne-quoi)).
- **Un cas qui ne se charge pas** fait sortir `claude plugin eval` en **code 1**,
  le même code qu'un score sous le seuil. Le code de sortie seul ne distingue
  donc pas une panne d'un mauvais score : lire la sortie. Seule une erreur de
  syntaxe YAML a été vue rejetée au chargement ; un type de juge inconnu ou une
  regex invalide ne l'ont pas été lors d'un essai, et c'est pourquoi le pré-vol
  de `evals_ab.py` (sans modèle, sans coût) compte. Pour vérifier gratuitement
  que la suite se charge : `--tag inexistant` sort proprement (« No eval cases
  found »).
- **Toute leçon ajoutée à un skill arrive avec son cas.** Pas de règle nouvelle
  dans un `SKILL.md`, un agent ou un `_partage/` sans le cas qui la prouve dans
  la même PR.

## Le format d'un cas

Ce que le lanceur charge tient dans un format précis. Un cas est un dossier
`evals/<plugin>/<cas>/` qui porte un `case.yaml`, un `prompt.md` (frontmatter
plus consigne), ou les deux.

- **`case.yaml`** exige `schema_version: "1.1"` et `name`.
- **Le frontmatter de `prompt.md`** n'accepte que : `schema_version`, `name`,
  `description`, `tags`, `plugins`, `runs`, `expected_outcome`, `model`,
  `max_turns`, `timeout_seconds`, `allowed_tools`, `artifact_publish`,
  `growthbook_overrides`, `append_system_prompt`, `env`. Toute autre clé, dont
  `context`, est une erreur.
- **Quand les deux fichiers coexistent, ils fusionnent** : `prompt.md` gagne sur
  les clés de haut niveau et sur `execution`, les `graders` s'additionnent.
  C'est la forme à utiliser dès qu'un cas a besoin d'un scaffold, puisque
  `context.scaffold_script` ne va que dans `case.yaml`.
- **Le scaffold** (`context.scaffold_script`, chemin relatif au dossier du cas)
  prépare l'état de départ. Il n'est joué qu'avec `--scaffold`, en bash, **hors
  bac à sable et sous le compte de l'utilisateur**, dans le répertoire de travail
  de l'agent : un dossier vide sous le `TMPDIR` de l'éval, avec `HOME`
  redéfini et un environnement minimal. Il dispose de 120 s ; un échec donne un
  score de 0. Comme il n'est pas isolé, la règle est qu'**un `fixture.sh`
  n'écrit que dans son répertoire courant**.
- **Les motifs `regex` s'évaluent en JavaScript** dans `claude plugin eval`,
  mais avec le module `re` de **Python** dans le pré-vol d'`evals_ab.py` : les
  deux ne se valent pas. Par exemple `clé\b` : en Python `é` est une lettre, en
  JavaScript sans le drapeau `u` non, donc un motif peut passer le pré-vol et se
  comporter autrement en vrai. Écrire des motifs qui ont le même sens des deux
  côtés : `(?!\w)` plutôt que `\b` après une lettre accentuée, pas de syntaxe
  propre à Python (`(?P<nom>…)`, drapeaux en ligne `(?i)`), et passer par
  `flags:` pour les drapeaux.
- **Le modèle** : jouer les cas avec un modèle de taille courante, pas un petit
  modèle. La CI joue **Sonnet (`claude-sonnet-5-5`) en effort `high`**, fixés par
  `EVALS_MODELE` et `EVALS_EFFORT` dans le job `evals` de `ci.yml` (le lanceur
  `evals/outillage/lancer.sh` a les mêmes défauts, et exporte l'effort en
  `CLAUDE_CODE_EFFORT_LEVEL`, la variable que `claude plugin eval` lit). Mesuré sur
  le cas `hook-claude` (3 passages) : Sonnet appelle le skill 3 fois sur 3 et
  obtient 90 %, contre 95 % pour Opus ; l'effort `high` fait réfléchir 4 800 à
  7 800 jetons, contre 350 à 550 en `low`. Au passage de fumée, haiku n'a pas
  appelé l'outil `Skill` : il a écrit « à la manière » du skill, ce qui ne prouve
  rien. Un petit modèle ne sert qu'à vérifier un format.

## Mesurer le bruit avant de fixer un seuil

Un modèle ne rend pas deux fois la même chose : le score d'un cas varie d'un
passage à l'autre. Un écart de score ne veut donc rien dire tant qu'on ne sait
pas de combien un skill **identique à lui-même** varie.

**Le seuil se fixe d'après le bruit mesuré, jamais avant.** On le mesure en
**A/A** : la même version contre elle-même.

```bash
python3 scripts/evals_ab.py --plugin <nom> --mode aa --tete <ref> \
    --sortie-bruit <fichier> -- --runs 3
```

En mode `aa`, seule la tête est jouée (deux fois) : `--base` n'y sert à rien.
Tout ce qui suit `--` est transmis tel quel au lanceur (`--runs 3` : trois
passages par cas) ; `--runs` n'est pas une option d'`evals_ab.py`.

Ordre de grandeur, pour savoir à quoi s'attendre, tant qu'aucune mesure
n'existe. L'intervalle de confiance à 95 % d'**une** moyenne vaut environ
`1/√(n·R)` pour `n` cas et `R` passages. Mais on compare **deux** moyennes, la
base et la tête, qui portent chacune leur bruit : leurs variances
s'additionnent, et l'écart est `√2` fois plus incertain qu'une moyenne seule.
`evals_ab.py` estime donc le bruit d'un écart à `√2/√(n·R)` en moyenne
globale, et à `√2/√R` par cas. Avec 16 cas et 3 passages,
`√2/√48 ≈ 0,20` : **± 20 points** sur la moyenne, et `√2/√3 ≈ 0,82` :
± 82 points par cas. Un écart de 8 points entre deux versions ne prouve rien à
cette taille ; prendre `1/√(n·R)` (≈ 0,14) ferait passer pour un signal ce
qui n'est que du hasard.

Cette estimation n'est qu'un **repli**. Dès que l'A/A a été joué avec
`--sortie-bruit <fichier>`, on la remplace par le bruit **mesuré** en passant ce
fichier à `--bruit` lors de la comparaison : c'est lui la référence, il dépend
des cas réels et non d'une formule.

**Le seuil par cas est plus large que l'intervalle d'un cas**, et c'est voulu.
Tester chaque cas à 95 % revient, sur `n` cas, à une probabilité
`1 − 0,95ⁿ` qu'**au moins un** dépasse par pur hasard (≈ 56 % pour 16 cas) :
la règle « un cas au-delà du bruit suffit » ferait échouer la CI une fois sur
deux sans aucun changement (comparaisons multiples ; A/A réel du 2026-09-30,
9 cas, où un cas a bougé de −10 pts alors que les deux jeux étaient
identiques). `evals_ab.py` corrige donc le seuil par cas par Bonferroni :
`z_n × rms`, avec `z_n = 1,96` pour un cas, ≈ 2,77 pour 9 cas, **≈ 2,95 pour
16 cas** (rms de 0,0385 : ± 11 pts par cas au lieu de ± 7,5). Le seuil sur la
moyenne ne change pas : c'est une seule comparaison. Les `demi_largeur_ic95_*`
du fichier de bruit restent des mesures brutes, pas les seuils appliqués.

## Comparer deux versions

```bash
python3 scripts/evals_ab.py --plugin <nom> --mode ab --base <ref> --tete <ref> \
    [--prive <chemin-vers-bancs/skills>] [--bruit <fichier>] [--journal] \
    -- --runs 3
```

`evals_ab.py` assemble, pour chaque référence git, une copie temporaire du
plugin avec les cas de `evals/<plugin>/`, joue les deux bras et compare. Avec
`--prive`, il ajoute les cas réels du dépôt privé ; c'est le geste du second
palier. Le script est la source de ses propres options ; ce document ne les
recopie pas. Les résultats se consignent dans `evals/RESULTATS.md`.

**Le verdict se lit dans `evals_ab.py`, pas dans le code de sortie brut de
`claude plugin eval`.** Ce dernier rend 1 aussi bien pour un cas sous le seuil
que pour un cas qui ne se charge pas, et le lanceur passe `--threshold 0` : le
seuil de l'outil ne juge rien ici. Le script, lui, distingue : `0` pas de recul
au-delà du bruit, `1` recul, `2` erreur d'usage, `3` refus (pré-vol, rapport
partiel, lanceur en échec, donnée illisible).

**Les traces se lisent après un `chmod`.** Le lanceur passe `--keep-temp`, qui
garde les dossiers de passage, mais **scellés** (mode `000`) : pour les lire,
`chmod 700 <dossier> <dossier>/sealed`. La trace d'un passage se trouve ensuite
dans `<TMPDIR>/claude-eval-*/out/trace.jsonl`.

**Un changement par tour.** Deux retouches dans la même comparaison, et on ne
sait plus laquelle a bougé le score.

**Un tirage de confirmation** quand l'écart est à la limite du bruit mesuré :
on rejoue, on ne tranche pas sur un seul tirage.

**Lire au moins trois transcriptions par passe**, pas seulement les scores. Un
score identique peut cacher un cas gagné pour la mauvaise raison ; un score en
baisse peut venir d'un juge trop strict. Les transcriptions sont ce qui le dit.

## Choisir les évals d'une PR

Jouer tout le banc à chaque PR coûte cher et n'apprend rien quand la PR ne
touche qu'un skill : le banc est donc **découpé en catégories**, et la PR dit
lesquelles jouer. Le plan choisit, la CI tient un plancher.

**Les catégories** vivent dans `evals/categories.json`, plugin par plugin ; c'est
la **seule** liste (les cas n'ont pas d'étiquette). Chaque catégorie nomme les
cas qu'elle regroupe et les fichiers qu'elle exerce. Pour `plans-notion` :

| Catégorie | Exerce | Cas |
|---|---|---|
| `existant` | `skills/plan-notion/`, `agents/chercheur.md` | `existant-jeu-de-donnees`, `existant-jeu-de-questions` |
| `bruit` | `skills/plan-notion/` | `bruit-bounded`, `bruit-doc-seule`, `report-sans-seuil` |
| `etat-de-depart` | `skills/plan-notion/`, `agents/enqueteur.md` | `appelants`, `garde-fou-cache`, `hook-claude`, `depart-rouge` |
| `maquette` | `skills/plan-notion/` | `maquette-requise` |
| `decouvertes` | `skills/executer-plan-notion/`, `agents/executant.md`, `agents/relecteur.md` | les quatre `decouverte-*` |
| `perimetre` | `skills/executer-plan-notion/`, `agents/executant.md` | `no-verify`, `rien-hors-plan` |

**Les évals se jouent à la demande.** La CI ne joue l'A/B que si la PR porte le
label `evals`. Une PR qui touche un skill, un agent, un hook ou `_partage/` sans
ce label doit dire pourquoi : `Evals: aucun — <raison>` dans son corps, sinon
la CI est rouge, le refus n'étant jamais silencieux. Choisir des catégories
implique donc le label ; `aucun` ne le pose pas.

**La ligne `Evals:` du corps de la PR** porte le choix :
`Evals: <catégories séparées par des virgules> — <raison>`, `Evals: tout`, ou
`Evals: aucun — <raison>`. Elle vient de la ligne « Évals à jouer » du chapitre
`Exécution` du plan (`plan-notion` l'écrit, `executer-plan-notion` la recopie et
ne pose le label que si des catégories sont choisies). **Avec le label et sans
cette ligne, la CI joue tout le banc.**

**Le plancher** (`scripts/evals_selection.py`, job `evals-portee`) : chaque
fichier touché sous `skills/` ou `agents/` d'un plugin doit être exercé par au
moins une catégorie choisie, sinon le job est rouge et nomme le fichier. Le
choix reste libre au-dessus du plancher. Et le banc entier est joué, quelle
que soit la ligne, si la PR touche `skills/_partage/`, `hooks/`, le banc
lui-même (`evals/<plugin>/`, `evals/outillage/`, `evals/categories.json`),
`scripts/evals_ab.py`, `scripts/evals_selection.py`, `ci.yml`, ou un fichier
qu'aucune catégorie n'exerce : dans tous ces cas, une sélection partielle ne
prouverait rien.

**Le job de verdict** s'appelle `Verdict des évals`, nom fixe : c'est lui que
le verrou de `main` exigera, quelle que soit la sélection (les jobs joués
changent d'une PR à l'autre, pas lui).

**Éditer le corps de la PR, puis relancer le run.** Le job `evals-portee` relit
le corps de la PR par l'API GitHub à chaque run (et non dans le payload de
l'événement, périmé dès qu'on rejoue un run). Ajouter ou corriger la ligne
`Evals:` demande donc de **relancer le run** (« Re-run all jobs ») ou de pousser
un commit ; c'est aussi ce que dit le message de refus du plancher. `ci.yml`
n'écoute pas `edited` : une édition de titre rejouerait une CI où `evals` est
sauté, et son « Verdict des évals » serait vert sur un commit dont les évals
étaient rouges. Si l'appel API échoue, le job est rouge : il ne se replie jamais
sur « tout » ni sur une sélection vide. Un lancement manuel `ab` ou `aa` a son
propre groupe de concurrence (le mode en fait partie) : un `ab` n'annule plus un
`aa` en cours.

**Le seuil par cas est aveugle sans bruit mesuré pour le bon modèle.** Sans
fichier `evals/bruit-<plugin>.json` mesuré **pour le modèle joué**, le seuil par
cas est le repli de la formule, qui dépasse 100 points (± 123 pts pour 16 cas
× 3 passages) : `evals_ab.py` dit alors « non concluant par cas » et ne voit
aucun recul cas par cas. Le fichier de bruit porte un champ `"modele"` ; un
bruit mesuré sur un autre modèle est **ignoré**, pas utilisé de travers. **Tant
que `evals/bruit-<plugin>.json` porte un autre modèle que Sonnet** (c'est le cas
de `evals/bruit-plans-notion.json`, mesuré sur Opus, jusqu'à la nouvelle mesure),
le verdict par cas est donc « non concluant » : la moyenne reste jugée, pas
chaque cas.

**Changer de modèle ou d'effort, c'est remesurer le bruit.** Le modèle et
l'effort joués sont `EVALS_MODELE` et `EVALS_EFFORT` dans le job `evals` de
`ci.yml` (Sonnet, `high`) ; quand l'un change, rejouer l'A/A
([Mesurer le bruit](#mesurer-le-bruit-avant-de-fixer-un-seuil)) avec ces
réglages. Le tableau de `evals_ab.py` rappelle le modèle et l'effort joués. La
CI joue les sessions à 5 en parallèle : c'est une donnée de coût, pas un
réglage de la mesure.

**Mesurer le bruit sur le runner** (avec le vrai modèle, les vraies limites de
la CI) :

```bash
gh workflow run ci.yml --ref <branche> -f mode=aa
```

Le lancement manuel joue la tête deux fois sur tout le banc, sans lire ni écrire
le cache de la base, puis publie le bruit en artefact `evals-bruit-<plugin>`
(le résumé du job le rappelle). Le télécharger (`gh run download <id> -n
evals-bruit-<plugin>`), le commiter en `evals/bruit-<plugin>.json` dans la PR,
et pousser : la CI suivante l'utilise. Sans `-f mode=aa`, le lancement manuel
joue l'A/B habituel (`mode=ab`, le défaut).

## Lancer une évaluation

Il n'y a pas de skill pour ça, et c'est voulu : un skill est une consigne qu'un
modèle lit, il ne refuse rien. Les garde-fous sont dans les scripts, qui
refusent ou annoncent d'eux-mêmes. La porte d'entrée est donc
`scripts/evals_ab.py`, et le geste tient en trois temps. On rouvrira la question
d'un skill si une session se trompe encore de geste.

1. **Estimer.** Le coût se lit avant de payer :
   ```bash
   python3 scripts/evals_ab.py --plugin <p> --estimer --cas …
   ```
   Le script l'établit d'après le coût par cas des derniers rapports. Une A/B
   joue deux bras (base et tête), un bras complet coûte 27,53 $ sur Sonnet,
   et une catégorie 1,61 $ à 7,13 $ par bras (tableau de la fiche
   `claude plugin eval` de `outils-et-quotas.md`). **Annoncer ce coût à
   Benjamin avant de lancer.** Le plafond est de 35 $ par bras
   (`EVALS_MAX_COUT_USD=35`), contre 120 $ avant, jamais atteint.
2. **Vérifier le verrou.** Un seul banc à la fois : toutes les sessions d'un
   appel partagent la limite de débit de leur compte, et trois bancs ensemble
   ont rendu des scores inexploitables. En CI, le groupe de concurrence
   `evals-<plugin>` met un second banc en attente ; GitHub n'en garde qu'un,
   un troisième annule celui qui attendait, et il faut alors reposer le label.
   En local, le lanceur refuse de démarrer tant qu'un banc tourne en CI ; avant
   de lancer, prendre le jeton de la machine :
   ```bash
   python3 plugins/plans-notion/skills/_partage/scripts/etat-machine.py prendre evals-locales
   ```
   `EVALS_FORCER=1` passe outre : sur ordre explicite seulement.
3. **Lancer.** En CI : poser le label `evals` et écrire la ligne `Evals:` de la
   PR ([voir plus haut](#choisir-les-évals-dune-pr)). En local, sur le VPS,
   seuls les cas `tags: [lecture]` se jouent ([Où tourne quoi](#où-tourne-quoi)) :
   `evals_ab.py --mode ab`, comme dans [Comparer deux versions](#comparer-deux-versions).
   Garder 3 passages par cas : le bruit mesuré ne vaut que pour 3.

## La fumée : ce qu'elle voit, ce qu'elle ne voit pas

Quand une PR touche un skill, un agent, un hook ou `_partage/` sans porter le
label `evals`, la CI joue une **fumée** : la tête seule, en **un passage**, sur
Sonnet, sur les catégories que les fichiers touchés exercent. Ces catégories
sont **calculées** par `scripts/evals_selection.py`, pas choisies ; tout le banc
part pour `_partage/` et les hooks. Elle coûte 0,54 $ à 2,38 $ par catégorie,
environ 9,2 $ au plus. La fumée ne remplace pas l'A/B : c'est le label `evals`
qui remplace la fumée par l'A/B.

**Elle est rouge** si une session plante, ou si une catégorie passe sous son
plancher. Le plancher est le plus bas tirage sain mesuré, moins 0,10 (15 tirages
sains sur Sonnet et Opus, 2026-10-01) :

| Catégorie | Tirage sain (min – max) | Plancher |
|---|---|---|
| `existant` | 0,75 – 0,92 | 0,65 |
| `bruit` | 0,80 – 0,92 | 0,70 |
| `etat-de-depart` | 0,92 – 1,00 | 0,82 |
| `maquette` | 0,90 – 1,00 | 0,80 |
| `decouvertes` | 0,51 – 0,57 | 0,41 |
| `perimetre` | 0,31 – 0,45 | 0,21 |

Ces valeurs sont l'origine des planchers ; ceux que la CI applique sont dans son
code. Sur le seul bras cassé mesuré (trois bancs simultanés), les tirages
tombaient à 0,48 – 0,52 pour 0,73 – 0,78 en bonne santé, avec 21 sessions en
erreur sur 48 : un seul tirage l'aurait vu.

**Ce qu'elle ne voit pas :**

- un **recul fin**, de moins de 0,10 sur une catégorie : c'est le rôle de l'A/B ;
- sur `decouvertes`, le bras cassé gardait un score dans la plage saine : seules
  les sessions en erreur l'auraient signalé ;
- le **taux de faux rouges** : 15 tirages ne le mesurent pas, seul l'usage le
  dira ;
- **Haiku** : aucun tirage mesuré, donc aucun plancher connu.

**Un rouge à tort se relance une fois** ; au second rouge, on pose `evals`
pour trancher par l'A/B. Attention à la file : le groupe `evals-<plugin>` ne
garde qu'un run en attente, et **une fumée en attente peut annuler un A/B en
attente**. Un run annulé se relance, il ne vaut pas verdict.

## Rejeu réel : quand et combien

Le rejeu réel, c'est le second palier : rejouer en local de vrais cas passés,
avec des sous-agents qui refont le travail puis des juges qui le notent. **Il se
lance seulement sur demande explicite de Benjamin, avec le coût annoncé avant** :
nombre de rejeux × 3,30 $, plus les juges à 0,75 $ pièce, et un seul tirage par
défaut. Aucun skill ne le prescrit ; un lot de plan n'en lance pas de son chef.

**Ce que ça coûte, mesuré** (2026-09-30, dans les transcriptions des
sous-agents ; équivalent tarif API) :

| Poste | Jetons | Coût |
|---|---|---|
| un rejeu | ≈ 10 M | ≈ 3,30 $ |
| un juge | ≈ 0,9 M | ≈ 0,75 $ |
| 18 rejeux | 191 M | ≈ 60 $ |
| 12 juges | 11 M | ≈ 9 $ |
| un retest | 72,4 M | ≈ 25 $ |
| le rejeu d'un lot de doctrine, juges compris | ≈ 202 M | ≈ 69 $ |

Ce dernier rejeu a donné un écart de + 1,9 point, resté sous le bruit : 69 $ pour
un verdict qui ne tranche pas. D'où la règle ci-dessus.

**La méthode de mesure : compter les relectures cumulées, pas la taille
finale.** Un agent fait 40 à 60 tours, et **à chaque tour** il relit tout son
contexte (≈ 270 000 jetons en fin de rejeu), en lecture de cache. Un rejeu
relit donc ≈ 10 M de jetons, pas 270 000. Un coût annoncé d'après la taille
finale du contexte (≈ 2,84 M de jetons pour le retest) était faux d'un facteur
25 : le mesuré est 72,4 M. Pour mesurer : sommer, tour par tour, l'`usage` de la
transcription du sous-agent (entrée, écriture de cache, lecture de cache,
sortie), puis multiplier par le tarif du modèle (par million de jetons, Sonnet :
2 $ en entrée, 10 $ en sortie, 4 $ l'écriture de cache d'une heure, 0,20 $ la
lecture ; Opus : 4 $, 20 $, 8 $, 0,20 $).

## Ce que la méthode interdit

- **Un cas qui inspire une règle ne la prouve pas.** Le cas d'où vient la
  leçon a servi à l'écrire : il passera toujours. On garde des cas **de côté**
  (held-out), jamais vus au moment d'écrire la règle.
- **Choisir les cas mis de côté d'après le score de l'ancienne version.** Ce
  serait sélectionner les cas où elle échoue, donc où la nouvelle a le plus de
  chances de « progresser ». La sélection se confie à un **sous-agent**, qui
  ne voit pas les scores.
- **Fixer un seuil avant l'A/A**, ou le déplacer après avoir vu le résultat.
- **Renvoyer au modèle une sortie de test non bornée** : on la tronque avant
  qu'elle ne noie le contexte.
- **Lancer `claude plugin eval` sans `--no-publish`** : sans lui, le rapport
  HTML est **publié sur claude.ai**. Et sans `--ablation none`, un bras « sans
  plugin » double le coût. `evals_ab.py` passe les deux ; à la main, il faut
  les écrire.

Les autres options utiles de `claude plugin eval` : `--json`, `--threshold`,
`--tag`, `--scaffold`, `--allow-tools`.

## La veille avant la PR

Un fait de doc peut changer d'une version de Claude Code à l'autre : un cas ou une
règle fondés sur un fait périmé prouvent la mauvaise chose. **Avant toute PR qui
touche un skill, un agent, un hook ou un `_partage/`, une passe de veille** :
l'agent `chercheur`, avec le brief de [`docs/veille.md`](veille.md), lit les sources
depuis la dernière passe. Ce qui s'applique entre dans la PR — ou dans un plan si
c'est plus gros — et l'entrée datée s'ajoute au journal des passes.

La CI refuse la PR si la dernière entrée du journal a plus de 30 jours
(`scripts/check_veille.py`). Le tableau des faits porteurs de `veille.md` est
rejoué chaque semaine par `.github/workflows/veille.yml` ; une citation qui n'est
plus sur sa page ouvre une issue « Doc Claude changée : <fait> ».

## Où tourne quoi

**Sur le VPS, Bash est impossible dans une éval.** Le noyau
(`kernel.apparmor_restrict_unprivileged_userns=1`) interdit l'espace de noms
imbriqué dont le bac à sable a besoin, y compris en conteneur. Donc :

- **en local**, seuls les cas taggés `tags: [lecture]` (sans Bash), sur la
  session habituelle, sans jeton ;
- **sur le runner GitHub**, tous les cas : `evals/outillage/preparer-runner.sh`
  lève la restriction sur la VM jetable, `evals/outillage/lancer.sh` joue les
  cas. La version de Claude Code du runner y est **figée** et se monte **à la
  main** : la CI n'installe pas « la dernière » pour ce job, sinon le bruit de
  mesure changerait avec la CLI.

Le job `evals` de la CI est déclenché par `pull_request`, **jamais par
`pull_request_target`**, limité aux PR de `benjaminge73` et hors brouillons.
Ce dernier point n'est pas de la précaution gratuite : `pull_request_target`
exécute le code d'une PR avec les secrets du dépôt, donc le jeton ci-dessous.
Sur un dépôt public, GitHub retient d'ailleurs les secrets aux PR venues d'un
fork (source : doc « Claude Code GitHub Actions », section « Run a skill »).

## Le jeton de CI

Le job `evals` s'authentifie avec un jeton OAuth lié à l'abonnement Max de
Benjamin, rangé en secret GitHub `CLAUDE_CODE_OAUTH_TOKEN`. Les faits ci-dessous
ont été vérifiés le 2026-09-30 ; ce qui n'a pas pu l'être est dit comme tel.

**Création** — sourcé (doc `code.claude.com/docs/en/authentication`,
« Generate a long-lived token ») :

```bash
claude setup-token     # ouvre le même flux navigateur que /login
```

Le jeton, valable **un an**, s'affiche dans le terminal ; la commande **ne le
sauvegarde nulle part**. Il ne sert qu'à faire des requêtes au modèle (pas de
Remote Control, pas de connecteurs claude.ai). Le ranger sans le laisser dans
l'historique du shell, en le collant sur l'entrée standard :

```bash
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo benjaminge73/mes-skills
```

(sans `--body`, `gh` le lit sur l'entrée standard ; `gh secret set --help`).

**Renouvellement** — avant l'an écoulé : refaire `claude setup-token`, puis la
même commande `gh secret set` ; elle remplace le secret existant (`gh secret
set` « crée ou met à jour »). Poser un rappel à onze mois : rien dans la doc
consultée n'annonce l'expiration d'un jeton de CI. Devant un job `evals` qui
échoue en authentification sans changement dans la PR, tester d'abord le jeton
en local avant de déboguer le workflow (doc « Claude Code GitHub Actions »,
« Authentication errors »).

**Suppression du secret** : `gh secret delete CLAUDE_CODE_OAUTH_TOKEN --repo
benjaminge73/mes-skills`. ⚠️ Cela **ne révoque rien** : la doc le dit pour ce
secret précis — *« If you delete a secret, the credential it held stays
valid. »* (« Uninstall », page GitHub Actions).

**Révocation — non vérifiée.** Ni `claude setup-token --help`, ni
`claude auth --help` (sous-commandes `login`, `logout`, `status` seulement), ni
la doc officielle consultée ne décrivent comment invalider un jeton émis par
`setup-token`. `claude auth logout` ne doit pas être présumé le faire : la doc
n'affirme cette révocation que pour une connexion Console sans clé API, pas
pour un jeton `setup-token`. Deux demandes de fonctionnalité sur
`anthropics/claude-code` (#48373, fermée comme doublon, et #57400, fermée
« not planned ») affirment qu'il n'existe **aucune** commande pour lister ou
révoquer ces jetons, et que la seule voie est la console web ; c'est un
témoignage d'utilisateurs, pas la doc, et l'adresse qu'ils citent est celle des
clés API, qui n'est peut-être pas celle d'un jeton d'abonnement. **À faire si un
jour le jeton fuit** : supprimer le secret GitHub tout de suite, puis chercher
la révocation dans les réglages du compte claude.ai — et écrire ici ce qu'on y
trouve.

**Ce qui borne la fuite, en attendant** : le jeton est rangé en secret (jamais
dans un fichier du dépôt) ; le job ne tourne que sur `pull_request` pour les PR
de `benjaminge73` ; et un jeton `setup-token` est limité à l'inférence.
