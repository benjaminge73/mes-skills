Checkout non vérifié — HEAD est `4c0e9a1` (refactor(remise): simplifie la comparaison), la tête attendue du brief est `9d2f7b3` (feat(remise): étape 1) : le répertoire a avancé d'un commit depuis l'étape. `git status --short` rend une sortie vide, l'arbre est propre, mais la tête ne correspond pas. Je ne conclus pas sur un test rejoué sur ce checkout.

Lecture du diff de la plage du brief, `9d2f7b3` et son parent (un seul commit : « feat(remise): étape 1 — remise de fidélité ») : `appliquer_remise` applique 10 % strictement au-delà de 100 € et rend le montant inchangé en dessous ; les trois tests couvrent 200, 100 et 50, comme l'objectif le demande. Aucun écart avec l'objectif, aucune remarque sur le diff.

RIEN À SIGNALER
