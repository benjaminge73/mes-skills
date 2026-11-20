# Fin de passe : le Statut se décide

Dernier geste de **toute** passe qui a écrit une page de plan (création, réponse à des
commentaires, retouche) : relire le `Statut` et trancher, avant la réponse finale. Benjamin
ne filtre que sur `en revue` ; un plan fini resté `brouillon` est pour lui un plan qui n'existe pas.

1. Les critères sont ceux de « Rappel de vocabulaire » (`ecrire-dans-notion.md`) :
   questions posées avec leur recommandation, preuves et POC dans la page, `Exécution`
   écrit, filtre de l'enquête passé (`plan-notion/SKILL.md` §8, point 2).
2. Tous remplis → poser `en revue` (sur le VPS, `relire` d'abord : `_partage/relecture-par-hal.md`). Un
   `Statut` déjà au-delà de `brouillon` ne recule jamais.
3. Un critère manque → `brouillon` reste, et la réponse dit en **une ligne** lequel manque
   et pourquoi. Pas de plan « presque fini » sans cette ligne.

Garde : le hook `rappeler_revue.py` retient **une fois** la fin de tour d'une session qui a écrit
une page de plan sans la sortir de `brouillon` ; il ne décide rien à la place de la session.
