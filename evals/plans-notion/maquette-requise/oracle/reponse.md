Le plan est dans `plan.md`, avec une maquette de la page du panier dans son état cible. Le libellé « Valider » n'est pas qu'à un endroit : il est aussi dans un test e2e et dans l'e-mail de confirmation, ce que les étapes couvrent. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `grep -rn "Valider" .` -> `web/i18n/fr.json:5` (la clé `panier.valider`), `tests/e2e/panier.spec.js:5` (sélection du bouton par son nom), `web/templates/emails/confirmation.txt:3` (texte de l'e-mail)
- où le gabarit lit son libellé -> `web/templates/panier.html:19` par la clé `t("panier.valider")`, pas de texte en dur
- autres usages de la clé `panier.valider` -> aucun
DECOUVERTES:
- test e2e couplé au libellé : `tests/e2e/panier.spec.js` clique sur le bouton par son nom « Valider » ; il casserait au renommage
- e-mail de confirmation : `web/templates/emails/confirmation.txt` cite « Valider » dans sa phrase ; le libellé changé la rendrait fausse
