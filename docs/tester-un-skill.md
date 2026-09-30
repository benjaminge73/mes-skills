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
- [Écrire un cas](#écrire-un-cas)
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
  bloc court et structuré. `file_exists` ne voit que les fichiers **créés
  pendant le passage** ; un `regex` sur un fichier se déclare
  `target: {source: file, path: …}`.
- **Un cas qui a besoin de Bash** se tague autrement que `tags: [lecture]` (voir
  [Où tourne quoi](#où-tourne-quoi)).
- **Toute leçon ajoutée à un skill arrive avec son cas.** Pas de règle nouvelle
  dans un `SKILL.md`, un agent ou un `_partage/` sans le cas qui la prouve dans
  la même PR.

## Mesurer le bruit avant de fixer un seuil

Un modèle ne rend pas deux fois la même chose : le score d'un cas varie d'un
passage à l'autre. Un écart de score ne veut donc rien dire tant qu'on ne sait
pas de combien un skill **identique à lui-même** varie.

**Le seuil se fixe d'après le bruit mesuré, jamais avant.** On le mesure en
**A/A** : la même version contre elle-même.

```bash
python3 scripts/evals_ab.py --mode aa --base <ref> --tete <ref> --runs 3 [--bruit <fichier>]
```

Ordre de grandeur, pour savoir à quoi s'attendre : l'intervalle de confiance à
95 % vaut environ `1/√(n·R)` pour `n` cas et `R` passages. Avec 16 cas et
3 passages, `1/√48 ≈ 0,14` : **± 14 points**. Un écart de 8 points entre deux
versions ne prouve rien à cette taille.

## Comparer deux versions

```bash
python3 scripts/evals_ab.py --mode ab --base <ref> --tete <ref> --runs 3 \
    [--prive <chemin-vers-bancs/skills>] [--bruit <fichier>] [--journal]
```

`evals_ab.py` assemble, pour chaque référence git, une copie temporaire du
plugin avec les cas de `evals/<plugin>/`, joue les deux bras et compare. Avec
`--prive`, il ajoute les cas réels du dépôt privé ; c'est le geste du second
palier. Le script est la source de ses propres options ; ce document ne les
recopie pas. Les résultats se consignent dans `evals/RESULTATS.md`.

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
