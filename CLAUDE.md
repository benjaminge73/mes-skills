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

**Trois incidents mesurés :**

- **2026-09-08** : une session a travaillé un plan entier sur une copie
  périmée (copie installée contre arbre de travail).
- **2026-09-10** : le skill `plan-notion` d'une session s'est chargé depuis
  `~/.claude/remote/plugins/f06304eb81541a26/skills/plan-notion` — un instantané
  `@inline` — et son texte prescrivait encore `subagent_type: "enqueteur"`, le
  nom court corrigé la veille en 0.9.0 parce qu'il ne résout pas. La copie
  installée, elle, était à jour ; c'est l'instantané qui gagnait.
- **2026-09-11** : un plan de neuf étapes a été exécuté **en entier** sur
  l'instantané `plans-notion` **0.3.0**, alors que la **0.9.0** était installée.
  Six mineures de règles en arrière, dont la garde « Suis-je la bonne version ? »
  qui aurait justement attrapé le cas. C'est le contrôle d'hygiène écrit à la
  dernière étape de ce plan qui l'a signalé — sur la session qui l'écrivait.

**Le détail qui rend le piège vicieux** : l'instantané du 2026-09-10 avait déjà
été **purgé du disque** dans la même session, qui continuait pourtant de servir
la copie supprimée — le registre des skills est construit au démarrage, la
purge ne l'invalide pas. **Le disque est propre et le comportement reste faux,
jusqu'au redémarrage.**

**Les compteurs d'usage n'aident pas à trancher** : ce sont des totaux de vie,
jamais remis à zéro. `~/.claude.json` (clé `pluginUsage`) porte
`plans-notion@inline` à 47 usages alors que cet instantané n'existe plus,
contre 6 pour `plans-notion@atelier`.

Ce qu'ils disent en revanche sans ambiguïté, c'est **qui gagne**. Relevé du
2026-09-11 sur un compte système où les deux copies coexistaient :
`plans-notion@inline` à **3** usages, `plans-notion@atelier` à **0**. La copie
correctement installée depuis la marketplace n'avait jamais servi une seule
fois : l'instantané la masquait par collision de nom, à chaque démarrage.

## D'où vient un instantané, et pourquoi rien ne le rattrape

Établi le 2026-09-11, en remontant le `0.3.0` de l'incident ci-dessus.

**`plans-notion` n'a jamais été en 0.3.0 dans ce dépôt.** `mes-skills` démarre le
plugin à **0.7.0**, le 2026-09-07. La version 0.3.0 vient d'ailleurs : de
l'historique de `hermes-custom`, sous `plugins/plans-notion/`, autour du
2026-09-03 — l'époque où **ce dépôt-là** était sa propre marketplace. Elle en est
sortie le 2026-09-07 par le commit `1f105b0`, « les skills et le plugin partent
dans mes-skills ».

Un instantané `@inline` est donc **un fossile** : une capture figée, prise à un
instant donné, d'une source qui peut avoir déménagé ou disparu depuis. Trois
conséquences qui se déduisent de là et qu'il faut avoir en tête :

- **`autoUpdate` ne peut rien pour lui.** Il n'a aucun lien avec la marketplace
  `atelier` : ce n'est pas une installation en retard, c'est une copie sans
  canal. Attendre qu'elle se mette à jour, c'est attendre indéfiniment.
- **Le supprimer du disque ne sert à rien.** Les instantanés sont
  **retéléchargés à chaque démarrage** : mesuré le 2026-09-11, dix-sept dossiers
  sous `~/.claude/remote/plugins/<hash>/` tous écrits dans la même seconde que le
  boot de la session, à ~200 ms d'intervalle.
- **Quinze de ces dix-sept sont les plugins officiels d'Anthropic** (`github`,
  `vercel`, `design`, `engineering`, `playwright`, `typescript-lsp`…). Les deux
  autres seulement sont ceux de Benjamin. C'est ce qui rend le tri possible :
  un nom qui n'est pas dans le catalogue officiel et qui apparaît là est, par
  construction, une inscription faite côté `claude.ai`.

**Le traitement est donc côté `claude.ai`, jamais dans un dépôt** : retirer ou
resynchroniser l'inscription sur la surface qui pousse ces `--plugin-dir`.
⚠️ Préférer « mettre à jour » à « supprimer » quand l'option existe : dans une
surface où la marketplace `atelier` n'est pas installée, l'instantané peut être
la **seule** copie présente.

**Ce qui a été écarté** : `disableSideloadFlags` rejette `--plugin-dir`, mais
fait sortir la CLI en erreur — donc casserait Remote Control et Desktop, qui en
passent toujours. Il est en plus de portée « managed settings »
(`/etc/claude-code/managed-settings.json`), absente de ce poste.

**La portée projet a été essayée, et elle est écartée** : déclarer le plugin
dans le `.claude/settings.json` **versionné** d'un dépôt n'enregistre rien —
Claude Code exige le scope `user` ou `managed` pour une marketplace sur source
réseau. C'était séduisant parce que c'est la seule portée qui voyage jusqu'au
cloud, où `/plugin` n'existe pas. Deux sources concordantes le referment :

- `hermes-custom`, commit `1f105b0` du **2026-09-07** : l'essai y avait déjà été
  fait et avait déjà échoué — « la déclaration existait ici et n'installait
  rien » — au point d'être l'une des trois raisons de la scission qui a créé ce
  dépôt-ci ;
- deux sondes du **2026-09-11** : un `.claude/settings.json` volontairement
  cassé, puis un plugin bidon activé en portée projet — ni `claude plugin list`
  ni `claude plugin marketplace list` ne bronchent.

Un essai avait malgré tout été posé sur `vahiny` le 2026-09-11, faute d'avoir lu
l'historique de `hermes-custom` ; il a été annulé le jour même. **Un fichier qui
a l'air de configurer quelque chose et ne configure rien est pire que pas de
fichier** — c'est une dérive silencieuse de plus, dans un dépôt dont tout le
travail du jour consistait à en fermer une.

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
