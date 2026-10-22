La porte du lot refuse le départ : `maitre.md` écrit « P2 attend P1 jusqu'à a merger » et P1 est `en cours`. P2 reste `pret`, aucune étape ne démarre, `refus.md` dit qui attend quoi.

VERIFICATIONS:
- `depart-dans-le-lot.py maitre.md P2 --statuts "P1=en cours" "P2=pret" "P3=pret"` -> code 1, « P2 attend P1 jusqu'à `a merger` : P1 est `en cours` »
- Statut de plan.md -> inchangé, `pret`
DECOUVERTES:
- aucune
