# Travailler sur `mes-skills`

Ce dépôt **est** la marketplace `atelier` : des plugins Claude Code (liste : `.claude-plugin/marketplace.json`), dont `plans-notion` (skills
`plan-notion`, `executer-plan-notion` et `deleguer-a-haiku`, agents : voir `plugins/plans-notion/agents/`,
fichiers `_partage/`), `methode-de-travail` (`brainstorming`, `systematic-debugging`,
`verification-before-completion` ; agents : voir `plugins/methode-de-travail/agents/`)
et `voyages` (skill `organiser-voyage`). Les deux premiers sont installés en scope `user`
sur le poste et arrivent dans **toutes** les sessions, cloud comprise ; `voyages` ne
s'installe que là où on l'utilise. Le README dit l'installation, la mise à jour automatique
et la licence ; ce fichier ne dit que ce qui surprend une session qui travaille **ici**.

## Les trois copies du même plugin : voir le README

Ce piège concerne **toutes** les sessions, pas seulement celles qui
travaillent ici : le tableau des trois copies, le fait qui les met en
collision, le levier qui neutralise un instantané et la commande de
diagnostic (`python3 scripts/copies_installees.py`) vivent désormais dans le
[README](README.md), chapitre « Les trois copies du même plugin ». C'est là
qu'il faut chercher, mettre à jour et lire — pas ici.

Ce qui reste propre à une session qui travaille **dans ce dépôt** :

⚠️ **Ce dépôt n'y est pour rien, et c'est la correction à retenir.** On a cru
un temps que travailler dans `mes-skills` faisait charger le plugin depuis
l'arbre de travail à cause de son `.claude-plugin/marketplace.json`. **C'est
faux** : `mes-skills` n'a même pas de répertoire `.claude/`, et rien dans le
dépôt n'enregistre de marketplace à l'ouverture. Le chargement `@inline`
vient de la surface `claude.ai`, pas d'ici.

**Une modification ici ne change rien à ta session en cours**, quelle que
soit la copie qui te gouverne. Elle prend effet après merge sur `main` : la
remontée joue le point 4 bis de
`plugins/plans-notion/skills/_partage/remontee-sur-main.md`
(`claude plugin marketplace update atelier`, puis
`claude plugin update <plugin>@atelier` pour chaque plugin dont la version a
bougé), et un redémarrage ou `/reload-plugins`. Ne cherche pas à
vérifier un changement de règle en te regardant travailler : lis le fichier.

## D'où vient un instantané, et pourquoi rien ne le rattrape

Le détail (origine des instantanés `@inline`, pourquoi `autoUpdate` et la suppression du disque ne les rattrapent pas, et les pistes écartées) est dans [docs/instantanes.md](docs/instantanes.md).

## La règle qui refuse une PR : bouger la version

**Toute PR qui touche un fichier sous `plugins/<nom>/` doit changer la `version`
de `plugins/<nom>/.claude-plugin/plugin.json`.** Claude Code compare cette
chaîne, jamais le contenu des fichiers : sans bump, `plugin update` répond
« already at the latest version » et personne ne voit le travail. La CI le refuse
(`scripts/plugin_version_guard.py`). Un fichier hors `plugins/` — ce fichier-ci,
le README, `docs/`, `scripts/` — n'exige aucun bump.

## Mettre à jour un skill ou un plugin

Avant de toucher à un skill, un agent, un hook ou un `_partage/`, lire deux
documents : [docs/tester-un-skill.md](docs/tester-un-skill.md) (comment on prouve
qu'une consigne fonctionne) et [docs/garde-fous.md](docs/garde-fous.md) (les règles
que la CI tient déjà, et le garde de chacune).

- **Tout correctif ajoute sa ligne au registre et son garde dans la même PR.** Un
  correctif qu'aucun garde ne tient peut être défait sans que la CI le voie : la
  panne reviendrait, et on la corrigerait une seconde fois.
- **Avant toute PR qui touche un skill, un agent, un hook ou un `_partage/` : une
  passe de veille.** Un fait de doc peut changer d'une version de Claude Code à
  l'autre, et une règle fondée sur un fait périmé protège la mauvaise chose.
  L'agent `chercheur`, avec le brief de [docs/veille.md](docs/veille.md), lit les
  sources depuis la dernière passe ; ce qui s'applique entre dans la PR (ou dans un
  plan si c'est plus gros) ; l'entrée datée s'ajoute au journal. La CI refuse la PR
  si la dernière entrée a plus de 30 jours (`scripts/check_veille.py`), et un
  workflow hebdomadaire ouvre une issue quand une citation du tableau des faits
  n'est plus sur sa page.
- **Avant de pousser : lancer `scripts/ci_locale.sh`.** C'est la **seule** liste des
  contrôles : ce que la CI joue dans son job `validation` (deux steps : validation,
  puis gardes ; en local, le script joue les gardes d'abord), et rien d'autre à
  énumérer ici. Sur une branche de PR, il compare à `origin/main` ; une autre base
  se passe par `BASE_REF=<réf>`. Il ne joue ni le job `evals` (payant, sur le runner
  GitHub seulement) ni `fumee`. Un contrôle ajouté au dépôt s'ajoute **dans ce script**, une fois.

La CI appelle ce même script, avec la CLI Claude Code épinglée dans
`evals/outillage/preparer-runner.sh` (`CLAUDE_CODE_VERSION`, la même que les évals) :
une montée se fait dans ce fichier, en PR revue. Une CLI du poste plus récente peut
valider autre chose que la CI : un écart de version se regarde d'abord là.

**Aucune éval sans demande explicite de Benjamin, dans son message courant** (décision du
2026-10-16 : trop de jetons et de temps). Ni `claude plugin eval`, ni `evals_ab.py`, ni
`lancer.sh`, ni `gh workflow run ci.yml`, ni « pour vérifier » : un cas d'éval **s'écrit**
sans se jouer. Hors CI, `lancer.sh` refuse sans `EVALS_DEMANDE_PAR_BENJAMIN=1`, à ne poser
que sur cette demande. Deux exceptions, datées, et elles seules : le cron de Hal qui mesure la boucle de la liste de relecture lance le banc sans cette demande, dans un plafond d'environ 5 dollars par mois (décision de Benjamin du 2026-11-24, détail dans `docs/garde-fous.md`) ; et l'ombre de relecture d'étape, lancée par le pilote après chaque relecture d'étape (≈ 0,3 dollar, décidée au plan « Réduire la voilure », reprise par Q2 de P1). Tout le reste reste soumis à l'accord dans le message courant. La fumée est à la demande elle aussi : elle ne part que sur le label `fumee` (décision du 2026-10-27, qui remplace celle du 2026-10-16 qui la gardait sans label). Détail, et comment la demander ou la jouer en local : [docs/tester-un-skill.md](docs/tester-un-skill.md).

**Toute leçon ajoutée à un skill, un agent ou un `_partage/` arrive avec son
cas d'évaluation** dans `evals/<plugin>/`, prouvé par un oracle qui passe et un
témoin nul qui échoue. Une consigne changée se compare à l'ancienne en A/B avec
`python3 scripts/evals_ab.py`, et le seuil se fixe d'après le bruit mesuré en
A/A, jamais avant. La méthode complète : [docs/tester-un-skill.md](docs/tester-un-skill.md).

La CI le contrôle (`scripts/check_lecon_a_son_cas.py`) : une PR qui touche
`plugins/<nom>/skills/`, `agents/`, `hooks/` ou `_partage/` doit aussi toucher
`evals/<nom>/`, **ou** porter dans un de ses commits une ligne
`Eval-cas: <cas existant>`, ou `Eval-cas: aucun — <raison>`. La dérogation est
possible, jamais silencieuse : elle s'affiche dans le résumé de la CI.

⚠️ **Le frontmatter d'un `SKILL.md` est du YAML.** Un deux-points suivi d'une
espace dans une `description` non citée casse le parsing, et le skill se charge
alors avec des métadonnées vides, **sans rien dire**. En cas de doute, une
description longue s'écrit en bloc (`description: >-`).

## Ouvrir une PR ici, c'est demander la publication

La CI merge seule toute PR verte (job `merge-auto`, décision de Benjamin du
2026-09-09). Sur ce dépôt, **ouvrir la PR prête vaut publication** : il n'y a
plus de geste entre le vert et la mise en ligne. La règle d'un plan est la
même : la clôture ouvre la PR prête, la CI la merge, la session ne merge
jamais (`plugins/plans-notion/skills/_partage/remontee-sur-main.md`).

Trois choses retiennent le merge : une PR en brouillon (demandé par Benjamin
seulement ; ou le temps d'écrire la ligne `Doc :`, 2026-11-02), une PR ouverte par quelqu'un d'autre, et le label
**`review-required`**, la porte de sortie d'un humain qui veut relire malgré
le vert. C'est le même nom et le même sens que sur `vahiny` et
`kanban_mAIster_ATI4`. **Jamais sur la PR de clôture d'un plan** : la clôture
l'ouvre pour qu'elle parte, et ici le label empêcherait le merge (`merge-auto`
en est exclu). Une modification dont on n'est pas sûr s'ouvre **en brouillon**,
à la demande de Benjamin, jamais avec ce label.

⚠️ Ce que la CI vérifie, ce sont des manifestes, des renvois et un numéro de
version. **Elle ne dit rien de la justesse d'une consigne.** Une phrase fausse
dans un `SKILL.md` passe au vert et part dans toutes les sessions.

## Pas de déploiement

Rien ne se déploie depuis ce dépôt : les postes **tirent** `main`, par
`claude plugin update` ou par l'`autoUpdate` de la marketplace au démarrage.
Le point 4 bis de `plugins/plans-notion/skills/_partage/remontee-sur-main.md`
fait cette mise à jour du poste juste après le merge.
Merger sur `main` avec la version bumpée *est* la mise à disposition. C'est
pourquoi la CI n'a pas de job de livraison, et n'en aura pas.
