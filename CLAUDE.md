# Travailler sur `mes-skills`

Ce dépôt **est** la marketplace `atelier` : deux plugins Claude Code,
`plans-notion` (skills `plan-notion` et `executer-plan-notion`, agent
`enqueteur`, fichiers `_partage/`) et `methode-de-travail` (`brainstorming`,
`systematic-debugging`, `verification-before-completion`). Ils sont installés en
scope `user` sur le poste et arrivent dans **toutes** les sessions, cloud
comprise. Le README dit l'installation, la mise à jour automatique et la licence ;
ce fichier ne dit que ce qui surprend une session qui travaille **ici**.

## Le piège propre à ce dépôt : trois copies du même skill

Le skill que tu édites dans ce dépôt n'est **pas forcément** celui qui pilote ta
session. Trois copies coexistent, jamais garanties identiques :

1. **L'arbre de travail** — ce dépôt, ici même.
2. **La copie installée**, sous
   `~/.claude/plugins/cache/atelier/<plugin>/<version>/`, figée à la version que
   `~/.claude/plugins/installed_plugins.json` déclare.
3. **Un instantané `@inline`**, sous `~/.claude/remote/plugins/<hash>/<plugin>/`.
   `@inline` est le nom d'une **marketplace synthétique** : celle des plugins
   passés en ligne de commande par `--plugin-dir` (`@skills-dir` pour
   l'auto-chargement de `~/.claude/skills/` et `@synced` pour les copies poussées
   par `claude.ai` sont deux autres marketplaces du même genre — **pas** des
   marketplaces installées ; binaire `claude` 2.1.267 : `var Mp="inline",
   fu="skills-dir", ip="synced", Op="builtin"`, message « This `--plugin-dir`
   copy did not load »). Ces `--plugin-dir` sont passés par la surface
   `claude.ai` / Claude Code Desktop : le lanceur `~/.claude/remote/ccd-cli/`
   démarre avec `--plugin-dir ~/.claude/remote/plugins/<hash>` répété dix-sept
   fois, un par instantané — **aucun ne pointe vers un arbre de travail**.

⚠️ **Ce dépôt n'y est pour rien, et c'est la correction à retenir.** On a cru un
temps que travailler dans `mes-skills` faisait charger le plugin depuis l'arbre
de travail à cause de son `.claude-plugin/marketplace.json`. **C'est faux** :
`mes-skills` n'a même pas de répertoire `.claude/`, et rien dans le dépôt
n'enregistre de marketplace à l'ouverture. Le chargement `@inline` vient de la
surface `claude.ai`, pas d'ici.

**Une modification ici ne change rien à ta session en cours**, quelle que soit
la copie qui te gouverne. Elle prend effet après merge sur `main`, `claude
plugin update <plugin>@atelier`, et un redémarrage. Ne cherche pas à vérifier un
changement de règle en te regardant travailler : lis le fichier.

**Laquelle gagne, et comment le savoir — le seul geste fiable** : chaque
`SKILL.md` porte en tête une section « Suis-je la bonne version ? » dont
l'en-tête annonce le chemin depuis lequel le skill a été chargé. C'est le seul
endroit où la réponse est factuelle.

- chemin sous `~/.claude/plugins/cache/atelier/` → copie installée ;
- chemin sous `~/.claude/remote/plugins/` → instantané `@inline` ;
- chemin dans le dépôt → arbre de travail.

**`ListPlugins` ne peut pas répondre à cette question.** Il n'interroge que les
plugins côté `claude.ai`, jamais un instantané `@inline` ni une marketplace
GitHub installée sur la machine. Seul
`~/.claude/plugins/installed_plugins.json` fait foi pour la copie installée —
et il ne connaît pas les instantanés. **Aucun outil ne montre les trois copies
d'un coup.**

**Deux incidents mesurés :**

- **2026-09-08** : une session a travaillé un plan entier sur une copie
  périmée (copie installée contre arbre de travail).
- **2026-09-10** : le skill `plan-notion` d'une session s'est chargé depuis
  `~/.claude/remote/plugins/f06304eb81541a26/skills/plan-notion` — un instantané
  `@inline` — et son texte prescrivait encore `subagent_type: "enqueteur"`, le
  nom court corrigé la veille en 0.9.0 parce qu'il ne résout pas. La copie
  installée, elle, était à jour ; c'est l'instantané qui gagnait.

**Le détail qui rend le piège vicieux** : l'instantané du 2026-09-10 avait déjà
été **purgé du disque** dans la même session, qui continuait pourtant de servir
la copie supprimée — le registre des skills est construit au démarrage, la
purge ne l'invalide pas. **Le disque est propre et le comportement reste faux,
jusqu'au redémarrage.**

**Les compteurs d'usage n'aident pas à trancher** : ce sont des totaux de vie,
jamais remis à zéro. `~/.claude.json` (clé `pluginUsage`) porte
`plans-notion@inline` à 47 usages alors que cet instantané n'existe plus,
contre 6 pour `plans-notion@atelier`.

**Ce qui a été écarté** : `disableSideloadFlags` rejette `--plugin-dir`, mais
fait sortir la CLI en erreur — donc casserait Remote Control et Desktop, qui en
passent toujours. Il est en plus de portée « managed settings »
(`/etc/claude-code/managed-settings.json`), absente de ce poste.

**Le remède en cours d'essai** : déclarer le plugin dans le
`.claude/settings.json` **versionné** d'un dépôt (portée projet) — la seule
portée qui voyage jusqu'au cloud, où `/plugin` n'existe pas. Un premier essai
vient d'être posé sur `vahiny`. ⚠️ **Son effet n'est pas prouvé** : ni `claude
plugin list` ni `claude plugin marketplace list` ne lisent ce fichier (sondé le
2026-09-11 avec un fichier volontairement cassé, puis un plugin bidon — aucune
des deux commandes ne bronche). À traiter comme un essai en cours, pas une
solution acquise.

## La règle qui refuse une PR : bouger la version

**Toute PR qui touche un fichier sous `plugins/<nom>/` doit changer la `version`
de `plugins/<nom>/.claude-plugin/plugin.json`.** Claude Code compare cette
chaîne, jamais le contenu des fichiers : sans bump, `plugin update` répond
« already at the latest version » et personne ne voit le travail. La CI le refuse
(`scripts/plugin_version_guard.py`). Un fichier hors `plugins/` — ce fichier-ci,
le README, `docs/`, `scripts/` — n'exige aucun bump.

## Avant de pousser

```bash
python3 scripts/check_marketplace.py     # le manifeste et le disque concordent
python3 scripts/check_references.py      # renvois ${CLAUDE_PLUGIN_ROOT}/… et frontmatters
claude plugin validate .                 # le schéma de la marketplace
claude plugin validate plugins/<nom>     # le schéma d'un plugin
```

La CI rejoue exactement ces quatre contrôles, avec la **dernière** CLI publiée,
non épinglée. Deux conséquences vérifiées le 2026-09-08 : elle valide des choses
que la CLI du poste ne valide pas encore, et un job rouge sans changement dans la
PR peut signaler une dérive du format en amont plutôt qu'une régression locale.

⚠️ **Le frontmatter d'un `SKILL.md` est du YAML.** Un deux-points suivi d'une
espace dans une `description` non citée casse le parsing, et le skill se charge
alors avec des métadonnées vides, **sans rien dire**. En cas de doute, une
description longue s'écrit en bloc (`description: >-`).

## Ouvrir une PR ici, c'est demander la publication

La CI merge seule toute PR verte (job `merge-auto`, décision de Benjamin du
2026-09-09). Sur ce dépôt, la règle générale « aucune PR vers `main` sans
demande explicite » se lit donc autrement : **c'est l'ouverture de la PR qui
est la demande**, puisqu'il n'y a plus de geste entre le vert et la mise en
ligne.

Trois choses la retiennent : une PR en brouillon, une PR ouverte par quelqu'un
d'autre, et le label **`review-required`**, qui est la porte de sortie quand on
veut relire malgré le vert. C'est le même nom et le même sens que sur `vahiny`
et `kanban_mAIster_ATI4`. Poser ce label est le geste correct pour une
modification dont on n'est pas sûr ; ouvrir la PR sans lui vaut publication.

⚠️ Ce que la CI vérifie, ce sont des manifestes, des renvois et un numéro de
version. **Elle ne dit rien de la justesse d'une consigne.** Une phrase fausse
dans un `SKILL.md` passe au vert et part dans toutes les sessions.

## Pas de déploiement

Rien ne se déploie depuis ce dépôt : les postes **tirent** `main`, par
`claude plugin update` ou par l'`autoUpdate` de la marketplace au démarrage.
Merger sur `main` avec la version bumpée *est* la mise à disposition. C'est
pourquoi la CI n'a pas de job de livraison, et n'en aura pas.
