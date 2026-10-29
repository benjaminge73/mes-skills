# Coût des plans : le barème, et comment on le lit

Fichier partagé du plugin `plans-notion`. Il est lu par `plan-notion` (la ligne
« Coût estimé » en tête du chapitre `Exécution`) et par `executer-plan-notion`
(la ligne « Coût réel » à l'entrée `État final`, mesurée par `cout-plan.py`).

## L'unité : des dollars d'équivalent API, rien d'autre

Tout coût s'écrit en **dollars d'équivalent API** : ce que la session coûterait
au tarif officiel de l'API. Sur l'abonnement, on ne paie pas ces dollars ; ils
servent d'unité commune pour comparer des plans entre eux. **Aucun pourcentage de
quota** n'est écrit, ni estimé, ni recopié (décision Q4 du plan).

Les tarifs sont dans `scripts/grille-tarifs.json`, à côté de `cout-plan.py`
(`plugins/plans-notion/skills/_partage/scripts/`).

## Conception et exécution : deux coûts, deux pilotes

Un plan coûte en deux temps, et les deux ne se lisent pas de la même façon :

- **Le coût de conception** : le pilote est en Opus (`plan-notion`), qui écrit le
  plan dans la page. C'est la ligne « Coût estimé » du chapitre `Exécution`.
- **Le coût d'exécution** : le pilote est en Sonnet effort `medium`
  (`executer-plan-notion`, décision Q9 du plan), les sous-agents `executant` sont
  en Haiku, et le `relecteur` en Opus. C'est la ligne « Coût réel » de l'entrée
  `État final`, mesurée par `cout-plan.py`.

Les tarifs sont dans `scripts/grille-tarifs.json` : Sonnet 5.5 à 2 $ l'entrée et
10 $ la sortie par million de tokens, la moitié d'Opus 5.5 (4 $ et 20 $). Une
exécution pilotée en Sonnet se lit donc à environ la moitié du poste « pilote »
du barème ci-dessous. Ce chiffre n'est pas remesuré ici : la remesure le
confirmera, et les médianes ci-dessous restent celles mesurées avant ce
changement, quand le pilote d'exécution était encore en Opus.

## Le barème mesuré le 2026-10-12

**Méthode** : les journaux de session (`.jsonl`) de Claude Code, messages
dédoublonnés par `message.id` (le même message est écrit plusieurs fois dans le
journal), tokens recalculés au tarif officiel d'Anthropic. Période : les 14 jours
précédant la mesure, soit 35 sessions de plan.

**Médianes par type de session** (`n` = nombre de sessions du type) :

| Type de session | Médiane | Min | Max | n |
|---|---|---|---|---|
| plan seul | 14 $ | 2 $ | 73 $ | 11 |
| exécution seule | 28 $ | 1 $ | 122 $ | 11 |
| plan puis exécution dans la même session | 132 $ | 32 $ | 398 $ | 12 |

Le total de la période est d'environ 3 600 $ d'équivalent API, pour 11,8 milliards
de tokens, dont l'essentiel en lecture de cache. Les trois `n` font 34 ; le
relevé annonçait 35 sessions, et la répartition manquante n'est pas donnée.

**Par étape** : aucune médiane par étape n'a encore été mesurée. Quand une étape
l'aura été, sa médiane s'ajoute ici, avec sa date et son nombre de sessions. Une
étape sans mesure n'a pas de coût estimé : on l'écrit, on n'en invente pas un.

## Ce que ces chiffres disent, et ce qu'ils ne disent pas

- Une médiane n'est pas une prévision pour un plan donné. La dispersion est
  large (de 1 $ à 398 $) : la ligne « Coût estimé » donne un ordre de grandeur.

## La remesure

Le barème se remesure **à chaque passe de veille**, sur les sessions de plan des
**14 derniers jours**, par la même méthode : journaux dédoublonnés par
`message.id`, écritures de cache ventilées comme le fait `cout-plan.py` (part 1 h
mesurée par modèle dans les journaux, appliquée aux écritures de ccusage), autres
tarifs de la grille. Chaque chiffre porte sa date de mesure ; une remesure remplace
les médianes ci-dessus et change la date en même temps.

⚠️ La sonde qui a fait la mesure du 2026-10-12 n'est pas dans ce dépôt. Tant
qu'elle n'y est pas, la remesure se refait à la main, par la même méthode.

## Lire les deux lignes de coût

- **« Coût estimé »** (`plan-notion`, en tête du chapitre `Exécution`) : avant
  l'exécution, les médianes du barème pour le type de session que le plan annonce,
  recopiées avec leur date.
- **« Coût réel »** (`executer-plan-notion`, entrée `État final`) : à la clôture,
  `cout-plan.py --page <identifiant de la page>`. Il additionne les sessions qui
  citent la page, sous-agents compris, et recalcule les dollars à partir des
  tokens. La session en cours y est comptée jusqu'à l'instant de la mesure.
  Un modèle absent de la grille est listé à part, « non chiffré », et exclu du
  total : un zéro silencieux ne se produit pas.

## Où partent les tokens

`rapport-tokens.py` répond à une autre question que les deux lignes de coût. Elles
disent combien coûte **un** plan ; lui répartit **tous** les tokens d'une fenêtre
entre projets, skills, sous-agents et modèles, pour voir où ils partent. Il lit
lui-même les journaux de session (`~/.claude/projects/**/*.jsonl`), sans ccusage,
et chiffre sur la même grille que `cout-plan.py`.

```
python3 plugins/plans-notion/skills/_partage/scripts/rapport-tokens.py --since 7d
```

Options (défaut entre parenthèses) :

- `--since` : la fenêtre, en `Nd`, `Nh` ou `AAAA-MM-JJ` (`7d`). Un message plus
  ancien que la fenêtre n'est jamais compté.
- `--projets` : le dossier des journaux (`~/.claude/projects`).
- `--grille` : la grille de tarifs (`grille-tarifs.json`, à côté du script).
- `--seuil-cache` : le seuil des ruptures de cache, en tokens (`100000`).
- `--top` : le nombre de lignes des sections 5 et 6 (`10`).

Lecture seule, sans dépendance. Ordre de grandeur : environ 35 s pour 30 jours de
journaux, soit 8 Go.

Le rapport a six sections. Les sections 1, 2 et 4 répartissent le même total chiffré.
La section 3 n'en montre que la part des sous-agents, en pourcentage de ce total.

- **Projet** : le dernier segment du premier `cwd` de la session qui donne un nom,
  le journal principal d'abord. Pour un worktree, c'est le dépôt : `<dépôt>/.claude/
  worktrees/<nom>` rend le segment qui précède `.claude`, et `…/worktrees/<dépôt>/<nom>`
  rend le segment qui suit `worktrees/`. Un `cwd` hors dépôt (scratchpad, `~/Dev`)
  donne son propre nom. Le nom du dossier de projet (sous `~/.claude/projects/`, ou
  le dossier `ssh-*`) ne sert qu'en repli, quand aucun `cwd` de la session ne donne de nom.
- **Skill** : le champ `attributionSkill` des messages. Le reste part sous « aucun
  skill ». Sur le POC du 2026-10-29, « aucun skill » porte environ 87 % des tokens :
  cette ventilation n'éclaire donc qu'une petite part du total.
- **Sous-agent** : seuls les appels de sous-agents. Le type vient d'`agentType`,
  dans le `<agent>.meta.json` voisin ; à défaut, du `subagent_type` de l'appel
  `Agent` du journal parent (retrouvé par son `toolUseId`, ou, sans `meta.json`,
  par `agentId`). Sinon : « type non résolu ». Cette ligne est notable sur les
  anciens journaux `ssh-*`, qui n'ont pas de `meta.json`.
- **Modèle** : le `model` du message. Un modèle absent de la grille s'affiche
  « non chiffré ». Un message sans nom de modèle sort sous « modèle inconnu », qui
  n'est pas dans la grille, donc « non chiffré » lui aussi.

Les sections 5 et 6 regardent les appels un à un :

- **Ruptures de cache** : les appels dont l'entrée plus l'écriture de cache dépasse
  `--seuil-cache`. Chacun porte son déclencheur, le dernier message `user` qui le
  précède : **humain** (un message humain réel), **notification de session liée**,
  ou **autre message système** (résultat d'outil, message de sous-agent, prompt
  écrit par un script, message injecté).
- **Top des tours** : un tour va d'un message humain réel au suivant, dans la même
  session, sous-agents compris. Les notifications et les messages système ne
  coupent pas un tour. Classement par dollars.

Limites :

- Le rapport ne remplace pas `cout-plan.py`. Il ne sait pas de quel plan vient un
  token : pour le coût d'un plan, c'est `cout-plan.py --page` qui fait foi.
- Il ne voit que les journaux présents dans `--projets`. Un journal supprimé, ou
  resté sur une autre machine, n'est pas compté.
- Dollars d'équivalent API, comme partout dans ce fichier : on ne les paie pas sur
  l'abonnement, et aucun pourcentage de quota n'est écrit.
- Un `cwd` hors dépôt (scratchpad, `~/Dev`, le dossier temporaire des
  `qualite-doc-juge-*`) donne son propre nom : ces sessions apparaissent comme
  autant de projets.
- Un modèle hors grille est listé « non chiffré », sort du total en dollars et
  reste compté en tokens : jamais à zéro.
