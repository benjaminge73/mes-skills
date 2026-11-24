Liste parcourue
A conformité au plan : rien
B retrait ou renommage incomplet : rien
C tests qui ne testent rien : rien
D robustesse des entrées : rien
E bugs de correction : rien
F concurrence et état : rien
G sécurité et ressources : rien
H performance : rien
Hors liste : rien

Plage `<base>..<tête>` : un commit, « feat(remise): étape 1 — remise de fidélité ». `python3 -m unittest` rejoué en lecture seule : 3 tests, OK.

Lecture du diff : `appliquer_remise` applique 10 % strictement au-delà de 100 € et rend le montant inchangé en dessous. Les trois tests attrapent leur panne : 200 doit rendre 180, 100 doit rester 100 (un `>=` le ferait rendre 90), 50 doit rester 50. Aucun écart avec l'objectif, aucune remarque sur le diff.

RIEN À SIGNALER
