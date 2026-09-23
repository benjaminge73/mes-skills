# mes-skills — la marketplace Claude Code `atelier` de benjaminge73

Les plugins Claude Code qui doivent être chargés **partout** : sur tous les
dépôts, en local comme en session cloud, et mis à jour tout seuls.

| Plugin | Ce qu'il apporte |
|---|---|
| `plans-notion` | Skills `plan-notion` et `executer-plan-notion`, agents `enqueteur` et `relecteur`. Les plans de travail s'écrivent, se relisent et s'exécutent dans Notion plutôt que dans le chat : chaque plan porte un chapitre `Cartes` (carte du dépôt et carte du plan en schémas Mermaid, tenues à jour à chaque passe) et un tableau de chevauchement avec `Dépend de` / `Taille` / `Blocs touchés` par étape ; l'exécution en tire des **vagues** — étapes parallèles dans des worktrees, étapes voisines regroupées dans un même sous-agent — avec rapport de sous-agent à quatre états, décompte des découvertes vérifié et rétrospective en cinq questions ; l'enquêteur est passé de six à treize gestes d'investigation, dont chercher une constante par sa valeur et non par son nom. Une étape testée prouve son rouge avant son vert — commit rouge rejoué par le pilote, `git diff` vide sur les fichiers de test entre rouge et vert ; le relecteur relit chaque étape au regard neuf, sans le contexte de la session qui a écrit le code, jusqu'à `RIEN À SIGNALER` ; la clôture contrôle qu'aucune branche de vague n'a survécu au plan. |
| `methode-de-travail` | Skills `brainstorming`, `systematic-debugging`, `verification-before-completion`. Dialoguer avant de créer, chercher la cause racine avant de corriger, prouver avant d'annoncer que c'est fini : `brainstorming` route désormais chaque demande en Spike / Bounded / Architectural et proportionne la sortie — réponse dans le chat, page de plan allégée, ou page complète ; `verification-before-completion` exige la preuve du rouge sur un test de fonctionnalité neuve, vu échouer avant le code et inchangé jusqu'au vert. |

## Pourquoi ce dépôt est public

Pas par vocation à être partagé : par contrainte technique, et c'est la raison
d'être de ce dépôt séparé.

Dans une session cloud Claude Code, le proxy GitHub n'accorde de credentials
qu'aux **dépôts attachés à la session**. Une marketplace hébergée dans un dépôt
privé est donc inatteignable depuis une session ouverte sur un *autre* dépôt :
le clone échoue sur `could not read Username`. Un dépôt public se clone sans
credentials, depuis n'importe quelle session.

C'est ce qui permet à l'installation ci-dessous de tenir sur **tous** les
dépôts sans rien configurer dépôt par dépôt. Le contenu ici est donc,
délibérément, de la méthode de travail — jamais de la configuration
d'infrastructure, qui reste dans les dépôts privés.

## Installation

### En local — une fois par machine, pas par dépôt

```bash
claude plugin marketplace add benjaminge73/mes-skills
claude plugin install plans-notion@atelier
claude plugin install methode-de-travail@atelier
```

Le scope par défaut est `user` : la marketplace est enregistrée dans
`~/.claude/settings.json` et **s'applique à tous les projets** de la machine.

⚠️ Ne pas déclarer cette marketplace dans le `.claude/settings.json` d'un
dépôt : Claude Code refuse une source réseau déclarée en scope projet — *« a
marketplace on a network location must be declared under
`extraKnownMarketplaces` in USER or managed settings (project/local scope
cannot vouch for it) »*. La déclaration existe, elle n'enregistre rien.

### En session cloud — une fois par environnement, pas par dépôt

Les sessions cloud repartent d'une VM neuve : `~/.claude/` n'y survit pas d'une
session à l'autre, et ni les skills ni les plugins de tes réglages utilisateur
n'y arrivent. Le seul levier par compte et inter-dépôts est le **setup script**
de l'environnement cloud, sur [claude.ai/code](https://claude.ai/code) →
sélecteur d'environnement → **Setup script** :

```bash
#!/bin/bash
claude plugin marketplace add benjaminge73/mes-skills || echo "!! marketplace add : ECHEC"
claude plugin install plans-notion@atelier          || echo "!! install plans-notion : ECHEC"
claude plugin install methode-de-travail@atelier    || echo "!! install methode-de-travail : ECHEC"
```

**Ne jamais laisser une de ces lignes sortir non-zéro** : un setup script qui
échoue fait **échouer le démarrage de la session**. Chaque ligne est donc
rattrapée — `echo` rend 0, exactement comme `|| true`.

⚠️ **Mais `|| true` seul est un piège**, et c'est la leçon du 2026-09-11 : si
`marketplace add` échoue (réseau, dépôt injoignable), les deux `install`
échouent avec lui, **silencieusement**, et la session démarre sans plugin de
méthode sans qu'un mot n'apparaisse dans le log. Le `echo` ne change rien au
comportement et rend l'échec lisible — c'est toute la différence, et elle vaut
la peine.

Le script tourne à la première session de l'environnement, puis son résultat
est capturé dans un instantané de filesystem que les sessions suivantes
réutilisent — c'est ce qui fait survivre `~/.claude/plugins/` alors que rien
d'autre ne survit. L'instantané se reconstruit quand tu changes le script ou
au bout d'une semaine environ.

### La mise à jour automatique

Sans elle, l'installation ci-dessus gèle la version au jour où elle a tourné —
et en cloud, l'instantané la gèle jusqu'à sa péremption. Ajouter `autoUpdate`
à l'entrée de marketplace dans `~/.claude/settings.json` :

```json
{
  "extraKnownMarketplaces": {
    "atelier": {
      "source": { "source": "github", "repo": "benjaminge73/mes-skills" },
      "autoUpdate": true
    }
  }
}
```

> *« Whether to automatically update this marketplace and its installed plugins
> on startup »*

Le défaut, pour une marketplace GitHub tierce, est **`false`**. Il n'y a pas
d'option en ligne de commande : cette clé s'écrit dans le fichier. En cloud,
la faire écrire par le setup script, après les installations :

```bash
python3 - <<'PY' || echo "!! autoUpdate : ECHEC"
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
d = json.loads(p.read_text()) if p.exists() else {}
entry = d.setdefault("extraKnownMarketplaces", {}).setdefault("atelier", {})
entry.setdefault("source", {"source": "github", "repo": "benjaminge73/mes-skills"})
entry["autoUpdate"] = True
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(d, indent=2) + "\n")
PY
```

La ligne `entry.setdefault("source", …)` n'est pas de la ceinture-bretelles.
Normalement `marketplace add` a déjà écrit la `source`, et ce `setdefault` ne
fait rien. Mais si cette commande a échoué, la version d'avant écrivait
`{"atelier": {"autoUpdate": true}}` — une entrée de marketplace **sans
source**, donc irrésoluble : elle a l'air déclarée et ne pointe nulle part.

Une session cloud repart d'une VM neuve : elle n'hérite ni de
`~/.claude/settings.json`, ni des hooks du poste. Le setup script est donc
aussi le **seul** levier qui atteint le cloud pour désactiver un instantané
`@inline` qui masquerait `plans-notion@atelier` (voir plus bas, « Les trois
copies du même plugin », pour ce que ça neutralise et ce que ça ne fait pas).
L'écrire à la suite de l'`autoUpdate` ci-dessus, dans le même setup script :

```bash
python3 - <<'PY' || echo "!! enabledPlugins plans-notion@inline : ECHEC"
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault("enabledPlugins", {})["plans-notion@inline"] = False
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(d, indent=2) + "\n")
PY
```

Cette écriture est idempotente — rejouer le setup script réécrit `False` sur
`False`, sans effet de bord — et suit le même schéma lire-modifier-écrire que
le bloc `autoUpdate` ci-dessus, pour ne pas écraser le reste du fichier.

Enfin, **finir le setup script par une vérification**. Sans elle, rien ne dit
jamais si tout ce qui précède a abouti :

```bash
echo "== plugins réellement installés =="
claude plugin list || true
```

Le log du setup devient alors la preuve, au lieu d'une suite de commandes dont
on ne saura jamais le sort. ⚠️ Attention à la façon de lire sa sortie.
`claude plugin list` a **trois** sections, et celle qui montre les copies
poussées par `--plugin-dir` — `Session-only plugins` — n'apparaît **que dans
une invocation qui en a elle-même reçu**. Lancée depuis un setup script qui
n'en reçoit aucun, elle est absente, et la liste paraît saine alors qu'une
copie figée peut masquer la version installée (voir plus bas, « Les trois
copies du même plugin »).

## Les trois copies du même plugin

Un plugin installé depuis cette marketplace n'est **pas forcément** celui
qui pilote une session donnée. Trois copies peuvent coexister, jamais
garanties identiques :

| Copie | Où elle vit | Son canal de mise à jour | Comment savoir si c'est elle qui gagne |
|---|---|---|---|
| **installée** (`@atelier`) | `~/.claude/plugins/cache/atelier/<plugin>/<version>/`, déclarée dans `~/.claude/plugins/installed_plugins.json` | la marketplace `atelier`, avec `autoUpdate: true` dans `~/.claude/settings.json` — elle se met à jour seule | `claude plugin list`, section `Installed plugins` |
| **instantané** (`@inline`) | `~/.claude/remote/plugins/<hash>/` ou `<hash>/<hash>/` | **aucun** — le lanceur `~/.claude/remote/ccd-cli/<version>` la repousse telle quelle à chaque démarrage via des arguments `--plugin-dir`. Supprimer le dossier ne sert à rien, il revient | `claude plugin list`, section `Session-only plugins`, qui **n'apparaît que dans une invocation ayant elle-même reçu des `--plugin-dir`** |
| **synchronisée** (`@synced`) | `~/.claude/plugins/synced/<bucket>/`, pilotée par un `manifest.json` | `claude.ai` | `claude plugin list`, section `Synced from claude.ai` |

`@inline` est le nom d'une **marketplace synthétique** : celle des plugins
passés en ligne de commande par `--plugin-dir` (`@skills-dir`, pour
l'auto-chargement de `~/.claude/skills/`, en est une autre du même genre —
pas une marketplace installée). Ces `--plugin-dir` sont passés par la
surface `claude.ai` / Claude Code Desktop : le lanceur
`~/.claude/remote/ccd-cli/` démarre avec un `--plugin-dir` répété une
quinzaine de fois, un par instantané — aucun ne pointe vers un arbre de
travail.

**Le fait central** : quand deux copies portent le **même nom de plugin**,
l'instantané masque l'installée. Mesuré le 2026-09-22 : trois instantanés
`plans-notion` **0.3.0** masquent la **0.11.0** installée — une version qui
n'a jamais existé dans ce dépôt (il démarre le plugin à 0.7.0), héritée de
l'historique de `hermes-custom` d'avant la scission (voir `CLAUDE.md`,
« D'où vient un instantané, et pourquoi rien ne le rattrape »).

### Le diagnostic en une commande

```bash
python3 scripts/copies_installees.py
```

Il réunit, en lecture seule, les trois vues qu'aucun outil existant ne
montre d'un coup : les plugins `atelier` installés, tous les instantanés
`@inline` trouvés sous `~/.claude/remote/plugins/` avec leur version, et les
`--plugin-dir` réellement passés aux processus `claude` vivants (lus dans
`/proc`). Il sort en **code 1** dès qu'un instantané masque une copie
installée à une version différente — le cas qui masque silencieusement une
mise à jour — et en **0** sinon, y compris quand rien n'a été trouvé du
tout.

### Le levier qui neutralise un instantané

Une ligne dans `~/.claude/settings.json` suffit à désactiver un instantané :

```json
"enabledPlugins": { "plans-notion@inline": false }
```

Elle est en scope utilisateur, donc elle vaut pour toutes les sessions
locales. ⚠️ Elle **désactive**, elle ne **supprime** pas : l'instantané
continue d'être retéléchargé à chaque démarrage, il n'est simplement plus
chargé. La clé est **exacte**, pas un motif : un instantané qui reviendrait
sous un autre nom passerait au travers. Et seule la valeur `false` est
honorée depuis des réglages **utilisateur** : activer un plugin par cette
clé exige des réglages administrateur.

En session cloud, `~/.claude/settings.json` ne survit pas d'une VM à
l'autre — c'est le setup script (« Installation → En session cloud »
ci-dessus) qui doit écrire cette ligne à chaque démarrage d'environnement ;
le bloc exact est reproduit là-bas, à la suite de l'`autoUpdate`.

### Comment le repérer autrement

**Laquelle gagne, et comment le savoir — le geste le plus fiable** : chaque
`SKILL.md` porte en tête une section « Suis-je la bonne version ? » dont
l'en-tête annonce le chemin depuis lequel le skill a été chargé. C'est le
seul endroit où la réponse est factuelle :

- chemin sous `~/.claude/plugins/cache/atelier/` → copie installée ;
- chemin sous `~/.claude/remote/plugins/` → instantané `@inline` ;
- chemin dans un dépôt de travail → arbre de travail (le cas d'un
  contributeur de ce dépôt, pas d'un usage normal du plugin).

**`ListPlugins` ne peut pas répondre à cette question.** Il n'interroge que
les plugins côté `claude.ai`, jamais un instantané `@inline` ni une
marketplace GitHub installée sur la machine. Seul
`~/.claude/plugins/installed_plugins.json` fait foi pour la copie installée
— et il ne connaît pas les instantanés. **Aucun outil ne montre les trois
copies d'un coup** — c'est pour ça que `scripts/copies_installees.py`
existe.

**Les compteurs d'usage n'aident pas à trancher quelle version est à jour**
— ce sont des totaux de vie, jamais remis à zéro — mais ils disent sans
ambiguïté **qui a gouverné les sessions passées**. `~/.claude.json` (clé
`pluginUsage`) a porté `plans-notion@inline` à 47 usages alors que cet
instantané n'existait déjà plus sur le disque. Et relevé du 2026-09-11 sur
un compte où les deux copies coexistaient : `plans-notion@inline` à **3**
usages, `plans-notion@atelier` à **0** — la copie correctement installée
depuis la marketplace n'avait jamais servi une seule fois, masquée par
collision de nom à chaque démarrage.

### Incidents mesurés

- **2026-09-08** : une session a travaillé un plan entier sur une copie
  périmée (copie installée contre arbre de travail, pour un contributeur de
  ce dépôt).
- **2026-09-10** : un skill s'est chargé depuis
  `~/.claude/remote/plugins/f06304eb81541a26/skills/plan-notion` — un
  instantané `@inline`, déjà purgé du disque dans la même session sans que
  ça change quoi que ce soit : le registre des skills est construit au
  démarrage, la purge ne l'invalide pas — et son texte prescrivait encore un
  nom de sous-agent corrigé la veille sur la copie installée. L'instantané
  gagnait quand même.
- **2026-09-11** : un plan de neuf étapes a été exécuté **en entier** sur
  l'instantané `plans-notion` **0.3.0**, alors que la **0.9.0** était
  installée — six mineures de règles en arrière, dont la garde « Suis-je la
  bonne version ? » qui aurait justement attrapé le cas. C'est un contrôle
  d'hygiène écrit à la dernière étape de ce même plan qui l'a signalé.

## Contribuer

### La règle qui compte : bouger la version

**Toute PR qui touche un fichier sous `plugins/<nom>/` doit faire changer la
`version` de `plugins/<nom>/.claude-plugin/plugin.json`.**

Ce que Claude Code compare pour décider qu'un plugin a changé, c'est cette
chaîne — jamais le contenu des fichiers. Sans bump, `plugin update` répond
« already at the latest version » et aucune session ne voit le travail.
La panne est muette des deux côtés : la CI est verte, la mise à jour annonce
un succès, et rien n'a bougé. `scripts/plugin_version_guard.py` la refuse en
CI ; il vient de `hermes-custom`, où le mode de défaillance a coûté six jours
et quatre PR invisibles.

Deux cas seulement n'exigent aucun bump : un plugin qui naît (pas de version
de base à dépasser) et un plugin qui disparaît.

### La CI, et pourquoi il n'y a pas de CD

`.github/workflows/ci.yml` joue deux jobs. `garde` vérifie la cohérence de la
marketplace (`scripts/check_marketplace.py`, le manifeste et le disque
concordent) et, sur une PR, que la version d'un plugin touché a bien bougé
(`scripts/plugin_version_guard.py`, la règle ci-dessus). `validation` fait
valider chaque manifeste par la CLI Claude Code elle-même (`claude plugin
validate` sur la racine, puis sur chaque `plugins/<nom>/`) et fait tourner
`scripts/check_references.py`, qui attrape les renvois `${CLAUDE_PLUGIN_ROOT}/…`
pointant dans le vide entre fichiers de skill, ainsi que les frontmatters de
skill et d'agent incomplets ou mal nommés.

Il n'y a pas de job de déploiement (CD, *continuous delivery*) parce qu'il n'y
a rien à déployer : ce dépôt n'est pas un service qui tourne quelque part, il
est tiré directement par les clients (`claude plugin update`, ou l'`autoUpdate`
de la marketplace décrit plus haut). Le bump de version *est* la mise à
disposition — dès qu'il est sur `main`, le plugin est disponible.

Un détail à connaître avant de chercher une régression dans son propre diff :
l'étape « Installer la CLI Claude Code » du job `validation` n'épingle
délibérément aucune version (`npm install -g @anthropic-ai/claude-code`). Un
job `validation` qui devient rouge sans qu'aucun fichier de la PR n'y touche
peut donc signaler que le format des manifestes de plugin a changé en amont,
pas une régression introduite ici — à vérifier avant de fouiller le diff.

### Vérifier avant de pousser

```bash
python3 scripts/check_marketplace.py     # le manifeste et le disque concordent
claude plugin validate .                 # le schéma de la marketplace
claude plugin validate plugins/<nom>     # le schéma d'un plugin
python3 scripts/check_references.py      # renvois ${CLAUDE_PLUGIN_ROOT}/… et frontmatters
```

Pour essayer une version en cours sans la publier :

```bash
claude --plugin-dir ./plugins/<nom>
```

## Licence

`plugins/methode-de-travail/skills/` dérive de
[obra/superpowers](https://github.com/obra/superpowers) (MIT) — voir
`plugins/methode-de-travail/LICENSE-SUPERPOWERS.txt`.
