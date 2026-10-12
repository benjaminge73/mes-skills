# Lecture déléguée : le pilote fait lire, il ne lit pas

Règle du pilote, la session qui conduit un plan : `plan-notion` (conception),
`executer-plan-notion` et `deleguer-a-haiku` (exécution). Ces trois skills y renvoient.

## La règle

Le pilote n'ouvre pas lui-même un fichier de plus de 200 lignes, une sortie de
commande de plus de 200 lignes, ni une page Notion de cette taille. Il pose la question
à un agent Haiku, qui lit et rend une réponse courte, sourcée (`fichier:ligne`) :

- du **code**, pour le comprendre : l'agent `enqueteur` ;
- une **commande** ou un **comptage** : l'agent `sondeur`. Son brief doit porter la
  question chiffrée, la commande exacte, le plafond d'appels et de coût, et le chemin du
  scratchpad ; sans ces quatre éléments, il rend `NEEDS_CONTEXT` sans rien jouer
  (`agents/sondeur.md`, « Ce que le brief te donne ») ;
- une **étape** d'exécution : l'agent `executant`.

## Ce qui reste au pilote

- Les rapports d'agents : ils sont courts, et les relire est la preuve.
- Les diffs courts.
- Les relevés de page Notion, avant toute écriture, puis le recompte après
  (`ecrire-dans-notion.md`).

## Pourquoi, en chiffres

Prix en dollars par million de tokens, relevés le 2026-10-12 dans `grille-tarifs.json` :

- pilote Opus 5.5 (conception) : écriture du cache en 1 h à 8 $, puis lecture à 0,20 $ à chaque tour ;
- pilote Sonnet 5.5 (exécution) : écriture en 1 h à 4 $, puis lecture à 0,10 $ à chaque tour ;
- agent Haiku 5.5 : écriture du cache en 5 min à 0,125 $, puis lecture à 0,01 $ à chaque tour de l'agent.

Ce que le pilote lit est payé à l'écriture de son cache, puis relu à chaque tour
suivant. Ce qu'un agent Haiku lit ne revient pas dans le contexte du pilote, qui ne
reçoit que la réponse courte. Les sessions pilotes écrivent leur cache en 1 h, les
sous-agents en 5 min (mesure du 2026-10-12, citée dans `cout-plan.py`). Le tarif
d'entrée de Haiku, 0,10 $, vaut pour un prompt jusqu'à 100 000 tokens ; au-delà, la
grille donne 0,50 $.
