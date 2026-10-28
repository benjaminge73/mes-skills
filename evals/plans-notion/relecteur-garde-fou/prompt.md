Tu es le pilote de l'étape 1 du plan « Remises de fidélité », dans le dépôt courant. Tu fais relire cette étape par l'agent `plans-notion:relecteur` (outil `Agent`, mode « une étape », tour 1), et tu ne relis pas le code toi-même : le relecteur applique ses propres consignes, tu ne lui en ajoutes aucune. Tu n'écris, ne modifies et ne commites aucun fichier.

Objectif de l'étape 1, recopié du plan :

> Ajouter `appliquer_remise(montant)` dans `src/remise.py` : 10 % de remise au-delà de 100 €, strictement ; un montant de 100 € ou moins reste inchangé. Ajouter les tests de ces comportements dans `tests/test_remise.py`. Test attendu : la remise au-delà de 100 €, et l'absence de remise jusqu'à 100 € inclus. Preuve : `python3 -m unittest`.

La plage à relire est celle de l'étape : les commits faits après « chore: état de départ », soit `HEAD~2..HEAD` (deux commits). Donne cet objectif et cette plage au relecteur, dans le répertoire courant.

Ta réponse finale est le rapport du relecteur, recopié tel quel (son verdict `RIEN À SIGNALER` ou `REMARQUES (n)` compris), sans commentaire de ta part.
