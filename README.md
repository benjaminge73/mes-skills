# mes-skills — la marketplace Claude Code `atelier` de benjaminge73

Les plugins Claude Code qui doivent être chargés **partout** : sur tous les
dépôts, en local comme en session cloud, et mis à jour tout seuls.

| Plugin | Ce qu'il apporte |
|---|---|
| `plans-notion` | Skills `plan-notion` et `executer-plan-notion`, agent `enqueteur`. Les plans de travail s'écrivent, se relisent et s'exécutent dans Notion plutôt que dans le chat : chaque plan porte un chapitre `Cartes` (carte du dépôt et carte du plan en schémas Mermaid, tenues à jour à chaque passe) et un tableau de chevauchement avec `Dépend de` / `Taille` / `Blocs touchés` par étape ; l'exécution en tire des **vagues** — étapes parallèles dans des worktrees, étapes voisines regroupées dans un même sous-agent — avec rapport de sous-agent à quatre états, décompte des découvertes vérifié et rétrospective en cinq questions ; l'enquêteur est passé de six à douze gestes d'investigation. |
| `methode-de-travail` | Skills `brainstorming`, `systematic-debugging`, `verification-before-completion`. Dialoguer avant de créer, chercher la cause racine avant de corriger, prouver avant d'annoncer que c'est fini : `brainstorming` route désormais chaque demande en Spike / Bounded / Architectural et proportionne la sortie — réponse dans le chat, page de plan allégée, ou page complète. |

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
claude plugin marketplace add benjaminge73/mes-skills || true
claude plugin install plans-notion@atelier || true
claude plugin install methode-de-travail@atelier || true
```

Le `|| true` n'est pas décoratif : un setup script qui sort non-zéro fait
**échouer le démarrage de la session**.

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
python3 - <<'PY' || true
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault("extraKnownMarketplaces", {}).setdefault("atelier", {})["autoUpdate"] = True
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(d, indent=2) + "\n")
PY
```

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
