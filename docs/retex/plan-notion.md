# Retex : `plan-notion`

Historique daté des règles de `plugins/plans-notion/skills/plan-notion/`. Il explique
aux mainteneurs pourquoi une règle existe ; il ne guide pas l'agent, et ne fait donc
pas partie du plugin. Déplacé de `SKILL.md` à l'étape 18 du plan « mes-skills - Évals
sobres et machine partagée » (2026-10-02), sans changement de sens.

## Suis-je la bonne version ?

Le 2026-09-08, une session a chargé ce skill depuis une copie synchronisée
périmée (`~/.claude/remote/plugins/<hash>/`, version 0.3.0 alors que 0.7.0
était installée) et a travaillé tout un plan sur les mauvaises règles. D'où la garde
de version, désormais jouée par `skills/_partage/scripts/verifier-version.sh`.

## Ne jamais cocher une case

La règle avait été enfouie dans le fichier puis oubliée : Benjamin l'a signalé le
2026-08-26, et elle a été remontée en tête (« Deux règles qui priment sur tout »).

## Le chapitre `Maquette`

Jusqu'au 2026-09-24, la maquette dépendait d'un « si le plan touche à du design »
que rien ne faisait relire, et elle manquait sur des plans qui changeaient un
écran. Le chapitre est devenu obligatoire et toujours présent : il pose la question
à chaque plan, et une dispense devient une phrase que Benjamin lit et peut contester,
au lieu d'un silence.

## Le filtre de l'enquête (§8, passer la main à l'exécution)

Les points 5 à 8 viennent de l'enquête sur les plans passés : la page du plan
elle-même est la source de **11 %** des découvertes manquées à l'exécution — ordre
des étapes faux, preuve de fin impossible à jouer, renvois périmés — et des chiffres
recopiés d'un plan antérieur s'y sont trouvés faux avec des écarts allant jusqu'à
**80 %**. Les points 9 et 10 viennent du relevé des 43 plans du 2026-09-08 au
2026-09-28 : près des trois quarts de ce qui a surpris l'exécution (74,6 % des
surprises libellées) aurait pu être vu avant. Ce filtre coûte quelques minutes à la
passe de plan et évite la découverte en pleine exécution, qui coûte une étape.
