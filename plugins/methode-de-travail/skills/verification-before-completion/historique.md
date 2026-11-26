# Historique de `verification-before-completion`

Annexe de `SKILL.md` : provenance, garde de version, et modifications par rapport à l'amont
(obra/superpowers). Le skill ne la lit pas au chargement ; elle répond à « pourquoi cette règle
est-elle là ? ».

Sommaire :

- Provenance
- Garde de version
- Modifications datées

## Provenance

*Adapté de [obra/superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent / Prime
Radiant). Récupéré le 2026-08-03.*

## Garde de version

Le 2026-09-08, une session a chargé le skill `plan-notion` depuis une copie synchronisée
périmée (`~/.claude/remote/plugins/<hash>/`, version 0.3.0 alors que 0.7.0 était installée) et
a travaillé tout un plan sur les mauvaises règles. N'importe quel skill peut être chargé de la
même façon : il ne choisit pas d'où il vient, il peut seulement le constater. D'où la section
« Suis-je la bonne version ? » en tête de `SKILL.md`, qui reste opérante : une garde dans une
annexe ne serait jamais lue au moment où elle sert.

## Modifications datées

- 2026-09-22 — ajout de la section « Suis-je la bonne version ? » en tête.
- 2026-09-23 — ajout du motif « red-first proof » (test inchangé entre rouge et vert).
- 2026-10-28 — ajout de la section « Un cron touché ».
