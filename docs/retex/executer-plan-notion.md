# Retex — `executer-plan-notion`

Historique daté des règles du skill `plugins/plans-notion/skills/executer-plan-notion/`.
Il explique aux mainteneurs **pourquoi** une règle existe ; il ne guide pas l'agent,
et le plugin ne le livre pas. Chaque passage est repris tel qu'il figurait dans
`SKILL.md` avant l'étape 19 du plan « Évals sobres et machine partagée » (allègement
sous 500 lignes) ; la règle correspondante reste dans le skill, sans la date.

## Suis-je la bonne version ? (SKILL.md)

> Le 2026-09-08, une session a chargé ce skill depuis une copie synchronisée
> périmée (`~/.claude/remote/plugins/<hash>/`, version 0.3.0 alors que 0.7.0
> était installée) et a travaillé tout un plan sur les mauvaises règles. Un
> skill ne choisit pas d'où il est chargé ; il peut seulement le constater.

Règle conservée : « Suis-je la bonne version ? », désormais le script
`_partage/scripts/verifier-version.sh`.

## Checkout partagé (`ouverture.md`, création de la branche)

> 7 incidents de checkout partagé relevés sur l'historique, la raison même de la
> règle globale `CLAUDE.md` sur les worktrees.

Règle conservée : la branche du plan se crée dans un worktree, jamais dans le
checkout principal.

## Une branche, aucune PR : les deux décisions (`ouverture.md`)

> La raison est comptable, et elle s'est fixée en deux temps. Le 2026-09-03 :
> chaque PR déclenche un run GitHub Actions complet — tests, build, e2e sur
> runner — et un plan de huit étapes en coûtait huit, plus celui de la remontée ;
> le quota mensuel d'Actions s'y consumait, `vahiny` en tête. Le 2026-09-04 :
> même la PR unique de clôture ne s'ouvre plus d'elle-même — la remontée vers
> `main` est un geste vers l'extérieur, et il n'a lieu que sur demande explicite
> de Benjamin (§6).

Règle conservée : un plan = une branche, aucune PR sans demande de Benjamin. [état au 2026-11-06 : la règle a été revue depuis ; la PR s'ouvre désormais à la clôture, prête (`cloture.md`, passage « La PR s'ouvre à la clôture, prête »).]

## Preuve locale, e2e à la clôture (`etapes.md`)

> Décision de Benjamin du 2026-09-03.

Règle conservée : la preuve d'étape = les tests des fichiers impactés ; la suite
complète et les e2e passent une fois, à la clôture.

## Prémisse d'un brief (`brief-du-sous-agent.md`)

> Constaté le 2026-09-24 : un brief affirmait « aucun des trois guides n'a encore
> ce champ » sur la foi d'un `grep` à la mauvaise forme (`^champ:` au lieu de
> `- champ:`) — l'exécutant l'a vu et signalé, mais il aurait tout aussi bien pu
> refaire un travail déjà fait, pour rien.

Règle conservée : une prémisse du brief se vérifie par une commande dont la sortie
est recopiée dans le brief.

## La variante « sur la page » (`journal.md`)

> 11 % des découvertes manquées de l'historique étaient de ce cas précis :
> l'enquête préalable avait lu le dépôt sans se relire elle-même.

Règle conservée : le libellé `découverte — trouvable au plan — sur la page`.

## Décompte des découvertes (`cloture.md`)

> Neuf décomptes faux sur 34 dans l'historique venaient d'un compte de tête.

Règle conservée : le décompte se vérifie par `grep -c`, jamais de tête.

## Preuve doc à la clôture (`cloture.md`, point 2 bis)

> Un passage `.md` qui cite un nom renommé par la branche reste faux sans que rien
> ne le signale : aucun test ne lit la doc. Relire tous les Markdown du dépôt pour
> le voir coûte cher ; d'où le relevé par `qualite-doc.py lecteurs`, limité aux noms
> touchés, puis le juge (`juger`), épinglé sur `claude-haiku-5-5`. Mis en place le
> 2026-10-15 (plan « la preuve doc », étape 6).

Règle conservée : à la clôture, après l'allègement et avant la porte, `lecteurs` puis
`juger` sur la branche ; un passage dont la ligne a été modifiée est traité d'office ;
sans juge (code 3), le pilote relit chaque passage relevé.

## PR de clôture (`cloture.md`)

> décision du 2026-09-04, qui revient sur la PR de clôture automatique du
> 2026-09-03.

Règle conservée : l'exécution s'arrête à la branche, sans PR. [état au 2026-11-06 : la règle a été revue depuis ; la PR s'ouvre désormais à la clôture, prête (`cloture.md`, passage « La PR s'ouvre à la clôture, prête »).]

## Branches de vague survivantes (`cloture.md`)

> Le 2026-09-23 sur `vahiny`, 8 branches de vague ont survécu à leur plan, sans
> filet après coup : plan parent squash-mergé, `git cherry` y rend `+` pour tout.

Règle conservée : contrôle bloquant des branches `<branche-du-plan>-etape-*` avant
de poser `a merger`.

## Une étape relue seule a sa branche d'étape (`vagues.md`, `etapes.md`)

> 2026-11-19 — Une étape `Relecture : étape` se joue dans son worktree, sur sa
> branche d'étape, même seule dans sa vague : sa revue porte sur sa plage de
> commits (`<base>..<tête>`), sans que le checkout partagé la voie avant le report.
> Écarté : une PR par étape, un run de CI chacune.

Règle conservée : une étape `étape` a son worktree et sa branche
`<branche-du-plan>-etape-N` ; une étape `lot` reste sur la branche du plan. La règle
vaut pour les plans dont l'entrée `Ouverture` est écrite après la mise à jour du
plugin ; un plan déjà en cours à ce moment-là garde sa branche unique jusqu'à sa
clôture.
