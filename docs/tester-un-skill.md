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
  `CLAUDE_CODE_EFFORT_LEVEL`, la variable que `claude plugin eval` lit ; en local,
  le même lanceur pose aussi deux gardes avant de jouer, dites dans
  [Où tourne quoi](#où-tourne-quoi)). Mesuré sur
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
passages par cas) ; `--runs` n'est pas une option d'`evals_ab.py`. Le mode `aa`
affiche son coût (les deux passages joués). **Si un des deux jeux a des sessions
en erreur, il rend le code 4 et n'écrit aucun fichier de bruit** : un bruit
mesuré sur une panne serait trop large, et toute A/B qui le lirait jugerait avec
un seuil faux. Il faut alors rejouer la mesure.

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
palier. Le script est la source de ses propres options ; ce document ne
recopie que celles qui évitent de payer pour rien. Les résultats se consignent
dans `evals/RESULTATS.md`.

- **`--cas <nom>`** ne joue que ce cas ; l'option se répète
  (`--cas a --cas b`), elle ne prend pas de liste séparée par des virgules. Un nom
  inconnu est un refus avant tout jeu.
- **`--base-rapport <json>`** (ou `--reference`) ne rejoue pas la base : elle est
  lue dans un rapport déjà joué, dont `--base-rapport` extrait les cas choisis
  même s'il porte tout le banc. Un cas absent du rapport est un refus. C'est ce
  que fait la CI avec la base de son cache
  ([plus bas](#choisir-les-évals-dune-pr)).
- **`--estimer`** annonce le coût **avant** de payer, puis s'arrête sans rien
  jouer. Le montant est lu dans le rapport de `--base-rapport` ou `--reference` ;
  seul le bras de tête est compté, multiplié par le `--runs` passé après `--`.
  Sans rapport, c'est un refus : jamais un « 0 $ » qui dirait gratuit. Le geste
  complet est dans [Lancer une évaluation](#lancer-une-évaluation).
- **`--fumee`** joue la tête seule, en un passage : voir
  [La fumée](#la-fumée--ce-quelle-voit-ce-quelle-ne-voit-pas).

**En local, `evals_ab.py` ne prend pas le jeton de la machine lui-même.** C'est
`lancer.sh`, qu'il appelle une fois par bras, qui le prend puis le rend à chaque
appel ([Où tourne quoi](#où-tourne-quoi)). Prendre le jeton à la main avant un
A/B local est donc une erreur : la prise du lanceur trouverait le jeton tenu,
attendrait 300 s (`EVALS_ATTENDRE`), puis refuserait (code 75).

**Le verdict se lit dans `evals_ab.py`, pas dans le code de sortie brut de
`claude plugin eval`.** Ce dernier rend 1 aussi bien pour un cas sous le seuil
que pour un cas qui ne se charge pas, et le lanceur passe `--threshold 0` : le
seuil de l'outil ne juge rien ici. Le script, lui, distingue : `0` pas de recul
au-delà du bruit, `1` recul, `2` erreur d'usage, `3` refus (pré-vol, rapport
partiel, lanceur en échec, donnée illisible), `4` **non concluant**. Le `4` veut
dire qu'un bras a des sessions en erreur (limite de session, délai dépassé) : une
session en erreur n'a rien mesuré du plugin, son score est celui d'une panne.
C'est « panne d'infrastructure, à relancer », jamais un recul ; le `4` prime sur
le `1`, en A/B comme en A/A et en fumée. Sans lui, le rapport d'une tête qui avait
perdu 21 sessions sur 48 à une limite de session se serait lu comme un plugin qui
régresse.

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

**Le label est lu par l'API, et le poser lance la CI.** `evals-portee` relit les
labels par `gh api`, comme le corps de la PR, et non dans l'événement : un
« Re-run » rejoue l'événement d'origine, dont les labels sont périmés. Le type
`labeled` fait partie des déclencheurs de `ci.yml`, pour que poser `evals` lance le
banc sans rien pousser. **Un label étranger ne relance ni le banc ni la fumée** :
poser `review-required` sur une PR qui porte déjà `evals` ne doit pas payer un
second banc. Le contrôle « label ou `aucun` » tourne quand même sur ce run, mais
le verdict n'y est pas rendu à la légère : voir plus bas.

**La ligne `Evals:` du corps de la PR** porte le choix :
`Evals: <catégories séparées par des virgules> — <raison>`, `Evals: tout`, ou
`Evals: aucun — <raison>`. Elle vient de la ligne « Évals à jouer » du chapitre
`Exécution` du plan (`plan-notion` l'écrit, `executer-plan-notion` la recopie et
ne pose le label que si des catégories sont choisies). **Avec le label et sans
cette ligne, la CI joue tout le banc.**

**Le plancher** (`scripts/evals_selection.py`, job `evals-portee`) : chaque
fichier touché sous `skills/` ou `agents/` d'un plugin doit être exercé par au
moins une catégorie choisie, sinon le job est rouge et nomme le fichier. Le
choix reste libre au-dessus du plancher. Un fichier de `skills/_partage/` suit
la même règle qu'un skill : `evals/categories.json` dit, dans la liste `exerce`
de chaque catégorie, quels fichiers partagés elle teste, et la PR choisit parmi
elles. Et le banc entier est joué, quelle que soit la ligne, si la PR touche
`hooks/`, le banc lui-même (`evals/<plugin>/`, `evals/outillage/`,
`evals/categories.json`), `scripts/evals_ab.py`, `scripts/evals_selection.py`,
`ci.yml`, ou un fichier qu'aucune catégorie n'exerce : dans tous ces cas, une
sélection partielle ne prouverait rien. Ce dernier cas ne doit pas arriver :
`scripts/check_skills.py` (règle i) refuse tout fichier de `skills/` ou
`agents/` d'un plugin qui a un banc qu'aucune catégorie n'exerce, donc un
nouveau fichier se déclare dans `evals/categories.json` dans sa propre PR.

**Le job de verdict** s'appelle `Verdict des évals`, nom fixe : c'est lui que
le verrou de `main` exigera, quelle que soit la sélection (les jobs joués
changent d'une PR à l'autre, pas lui). Il compte la portée, les bras de l'A/B
**et la [fumée](#la-fumée--ce-quelle-voit-ce-quelle-ne-voit-pas)** : un job rouge
ou annulé, et il est rouge. **Sur un run déclenché par un label étranger**, tous
les jobs sont sautés et leur « vert » ne dit rien du SHA : le verdict **recopie le
dernier verdict terminé de ce SHA** (lu dans les check-runs, d'où la permission
`checks: read`), et il est rouge s'il n'y en a aucun ou si le dernier était rouge.
Sans cela, poser un label étranger rendrait vert un SHA dont les évals étaient
rouges.

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

**Un seul banc à la fois, sans annulation.** Les jobs `evals` et `fumee` d'un
plugin partagent le groupe de concurrence `evals-<plugin>`, avec
`cancel-in-progress: false` : tous les bancs puisent dans la limite de débit d'un
même abonnement, et trois bancs simultanés (le 2026-09-30) ont rendu des mesures
inexploitables. Le second run attend donc la fin du premier, et ne l'annule pas.
**Limite de GitHub** : un seul run peut attendre par groupe ; un troisième annule
celui qui attendait, et le run annulé se relance (il ne vaut pas verdict). Le
lancement manuel `aa` a un groupe à part, `evals-aa-<plugin>`, pour qu'une mesure
de bruit payée ne soit pas annulée par un A/B.

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
le cache de la base (décrit ci-dessous), puis publie le bruit en artefact
`evals-bruit-<plugin>` (le résumé du job le rappelle). Si un des deux jeux a des
sessions en erreur, le job est rouge (code 4) et aucun bruit n'est publié. Le télécharger (`gh run download <id> -n
evals-bruit-<plugin>`), le commiter en `evals/bruit-<plugin>.json` dans la PR,
et pousser : la CI suivante l'utilise. Sans `-f mode=aa`, le lancement manuel
joue l'A/B habituel (`mode=ab`, le défaut).

**La base est rejouée le moins possible : elle vit dans un cache de contenu.**
Rejouer la base d'une PR coûte autant que sa tête, pour un résultat qui ne change
que si la base change. La clé du cache (le pas « Clé du cache de la base » de `ci.yml`)
porte donc tout ce qui ferait changer le rapport de la base, et rien de plus :

- l'empreinte de `git ls-tree -r <base> plugins/<plugin>`, c'est-à-dire le
  **contenu** du plugin à la base, et non le SHA du commit : un merge de doc sur
  `main` ne change pas le plugin, il ne doit pas invalider la base ;
- l'empreinte des cas (`evals/<plugin>/`), le modèle, l'effort, le nombre de
  passages, la version de Claude Code du runner et l'empreinte du lanceur.

La clé finit par `-tout` quand tout le banc a été joué, sinon par
`-sel-<empreinte de la sélection>`. **Une base complète sert toute sélection** :
la restauration essaie la clé exacte, puis se replie sur la clé `-tout`
(jamais sur une autre sélection) et `evals_ab.py --base-rapport <json>` en extrait
les cas choisis, sans rejouer la base. Le résumé du job le dit
(« base reprise du cache »). Une base jouée sur une sélection seulement est
sauvée sous sa propre clé `-sel-…`.

**Le coût est annoncé avant de payer**, en tête du résumé du job. Avec une base
en cache, c'est `--estimer` (bras de tête seul, lu dans le rapport de la base).
Sans base en cache, aucun rapport ne dit les coûts, et la CI annonce le pire :
au plus 70 $, soit deux bras au plafond. **Le plafond est de 35 $ par bras**
(`EVALS_MAX_COUT_USD`, passé à `claude plugin eval --max-cost-usd`) ; un bras
complet coûte 27,53 $ sur Sonnet, soit un quart de marge. Un bras qui dépasse est
rendu partiel et refusé (code 3), et la facture s'arrête là.

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
   En local, **rien à prendre à la main** : `evals/outillage/lancer.sh` refuse de
   démarrer tant qu'un job « Évals » tourne en CI, puis prend lui-même le jeton de
   la machine (`etat-machine.py prendre evals-locales`) et le rend en sortant.
   Ses gardes, ses variables (`EVALS_FORCER`, `EVALS_PLAN`, `EVALS_ATTENDRE`) et
   ses codes de refus (75, 69) sont dans [Où tourne quoi](#où-tourne-quoi).
   Prendre le jeton avant de lancer serait une erreur : la prise du lanceur
   attendrait 300 s, puis refuserait. `EVALS_FORCER=1` passe outre le contrôle de
   la CI : sur ordre explicite seulement.
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
part pour les hooks et pour un fichier qu'aucune catégorie n'exerce. Elle coûte 0,54 $ à 2,38 $ par catégorie,
environ 9,2 $ au plus. La fumée ne remplace pas l'A/B : c'est le label `evals`
qui remplace la fumée par l'A/B.

Elle est jouée par le job `fumee` de `ci.yml`, qui partage le groupe de
concurrence `evals-<plugin>` de l'A/B (un seul banc à la fois, voir
[Choisir les évals d'une PR](#choisir-les-évals-dune-pr)), annonce son coût en
tête du résumé avant de jouer, et compte dans `Verdict des évals`. Un label
étranger ne la relance pas.

**Le job est rouge dans deux cas, que son message distingue.** Une catégorie
passe sous son plancher (code 1) : c'est un recul. Ou des sessions plantent
(code 4, « non concluant — panne d'infrastructure, à relancer ») : ce n'est pas un
recul, parce qu'un score tiré vers le bas par des sessions en erreur ne dit rien
du skill ; le 4 prime sur le 1. Le plancher est le plus bas tirage sain mesuré,
moins 0,10 (15 tirages sains sur Sonnet et Opus, 2026-10-01) :

| Catégorie | Tirage sain (min – max) | Plancher |
|---|---|---|
| `existant` | 0,75 – 0,92 | 0,65 |
| `bruit` | 0,80 – 0,92 | 0,70 |
| `etat-de-depart` | 0,92 – 1,00 | 0,82 |
| `maquette` | 0,90 – 1,00 | 0,80 |
| `decouvertes` | 0,51 – 0,57 | 0,41 |
| `perimetre` | 0,31 – 0,45 | 0,21 |
| `billet` (plugin `voyages`) | 1,00 – 1,00 | 0,90 |

Les six premières lignes sont celles de `plans-notion` ; `billet` est la catégorie du
plugin `voyages`, mesurée le 2026-10-06 sur 6 tirages sains (Sonnet, effort `high`,
mode `aa`, 3 + 3), tous à 1,00 : le plancher y est donc 0,90.

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
  session habituelle, sans le jeton OAuth de la CI.
  `evals/outillage/lancer.sh` pose alors **deux gardes** avant de jouer, parce que
  tous les bancs partagent la limite de débit de l'abonnement (le 2026-09-30, un
  A/B local lancé pendant deux bancs de CI a rendu des résultats inexploitables) :
  1. **refus si un job « Évals » tourne en CI** (`gh run list`, puis les jobs de
     chaque run en cours) : code **75**. Si `gh` ne répond pas (absent, hors
     ligne, non authentifié), il refuse aussi, faute de savoir : code **69**.
     `EVALS_FORCER=1` passe outre ce contrôle et le dit sur stderr ; à réserver à
     un ordre explicite, les mesures peuvent être faussées ;
  2. **prise du jeton de la machine** (`etat-machine.py prendre evals-locales
     --plan "${EVALS_PLAN:-évals locales}" --attendre "${EVALS_ATTENDRE:-300}"`).
     Si une autre action lourde le tient, le lanceur attend jusqu'à
     `EVALS_ATTENDRE` secondes (300 par défaut, de quoi laisser finir une suite de
     tests ; une autre éval locale dure plus), puis refuse avec le code 75. Le
     jeton est rendu en sortant, par un `trap`, même si `claude` échoue ou est
     interrompu. `EVALS_FORCER` ne dispense pas de cette prise : le jeton protège
     les autres sessions de la machine, pas la limite de débit. `EVALS_PLAN` dit
     au nom de quel plan il est pris, pour que `etat-machine.py qui` le montre ;
- **sur le runner GitHub**, tous les cas, **ni `gh` ni jeton machine** (le
  runner n'est pas le VPS) : `evals/outillage/preparer-runner.sh` lève la
  restriction sur la VM jetable, `evals/outillage/lancer.sh` joue les cas. La
  version de Claude Code du runner y est **figée** et se monte **à la
  main** : la CI n'installe pas « la dernière » pour ce job, sinon le bruit de
  mesure changerait avec la CLI.

Les jobs `evals` et `fumee` de la CI sont déclenchés par `pull_request`, **jamais par
`pull_request_target`**, limité aux PR de `benjaminge73` et hors brouillons.
Ce dernier point n'est pas de la précaution gratuite : `pull_request_target`
exécute le code d'une PR avec les secrets du dépôt, donc le jeton ci-dessous.
Sur un dépôt public, GitHub retient d'ailleurs les secrets aux PR venues d'un
fork (source : doc « Claude Code GitHub Actions », section « Run a skill »).

## Le jeton de CI

Les jobs `evals` et `fumee` s'authentifient avec un jeton OAuth lié à l'abonnement Max de
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
