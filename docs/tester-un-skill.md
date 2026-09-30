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
- [Ce que la méthode interdit](#ce-que-la-méthode-interdit)
- [Où tourne quoi](#où-tourne-quoi)
- [Le jeton de CI](#le-jeton-de-ci)

## Deux paliers

| Palier | Où | Quand | Ce qu'il prouve |
|---|---|---|---|
| **Cas simulés**, publics | `evals/<plugin>/` dans ce dépôt | joués en CI à chaque PR qui touche `skills/`, `agents/` ou `_partage/` | qu'une consigne produit le bon état final sur une situation inventée |
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
- **Le modèle** : jouer les cas avec le modèle par défaut du lanceur, pas un
  petit modèle. Au passage de fumée, haiku n'a pas appelé l'outil `Skill` : il
  a écrit « à la manière » du skill, ce qui ne prouve rien. Un petit modèle ne
  sert qu'à vérifier un format.

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
