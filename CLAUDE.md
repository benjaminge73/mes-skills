# Travailler sur `mes-skills`

Ce dépôt **est** la marketplace `atelier` : deux plugins Claude Code,
`plans-notion` (skills `plan-notion` et `executer-plan-notion`, agent
`enqueteur`, fichiers `_partage/`) et `methode-de-travail` (`brainstorming`,
`systematic-debugging`, `verification-before-completion`). Ils sont installés en
scope `user` sur le poste et arrivent dans **toutes** les sessions, cloud
comprise. Le README dit l'installation, la mise à jour automatique et la licence ;
ce fichier ne dit que ce qui surprend une session qui travaille **ici**.

## Le piège propre à ce dépôt : deux copies du même skill

Le skill que tu édites dans ce dépôt n'est **pas** celui qui pilote ta session.
Celui qui te pilote est la copie installée, sous
`~/.claude/plugins/cache/atelier/<plugin>/<version>/`, figée à la version que
`~/.claude/plugins/installed_plugins.json` déclare.

Deux conséquences, et elles vont dans les deux sens :

- **Une modification ici ne change rien à ta session en cours.** Elle prend effet
  après merge sur `main`, `claude plugin update <plugin>@atelier`, et un
  redémarrage. Ne cherche pas à vérifier un changement de règle en te regardant
  travailler : lis le fichier.
- **Pour savoir quelle règle te gouverne à cette seconde, lis la copie
  installée**, pas l'arbre de travail. Les deux divergent dès qu'une branche est
  ouverte ici, et c'est normal.

Chaque `SKILL.md` porte en tête une section « Suis-je la bonne version ? » avec
la commande qui compare les deux. Elle existe parce qu'une session a travaillé un
plan entier sur une copie périmée, le 2026-09-08.

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
d'autre, et le label **`ne-pas-merger`**, qui est la porte de sortie quand on
veut relire malgré le vert. Poser ce label est le geste correct pour une
modification dont on n'est pas sûr ; ouvrir la PR sans lui vaut publication.

⚠️ Ce que la CI vérifie, ce sont des manifestes, des renvois et un numéro de
version. **Elle ne dit rien de la justesse d'une consigne.** Une phrase fausse
dans un `SKILL.md` passe au vert et part dans toutes les sessions.

## Pas de déploiement

Rien ne se déploie depuis ce dépôt : les postes **tirent** `main`, par
`claude plugin update` ou par l'`autoUpdate` de la marketplace au démarrage.
Merger sur `main` avec la version bumpée *est* la mise à disposition. C'est
pourquoi la CI n'a pas de job de livraison, et n'en aura pas.
