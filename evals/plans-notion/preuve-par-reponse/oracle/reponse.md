La passe de contrôle est faite sur `plan.md`. La question Q1 (canal des relances) est tranchée : l'e-mail, sur la réponse de Benjamin du 2026-10-14. Elle n'avait pas de ligne `Preuve :` ; je l'ai ajoutée, avec une lecture de `docs/limites.md` (ligne 3 : le SMS coûte 0,07 € par message et plafonne à 500 par mois, l'e-mail est gratuit). Q2 (fréquence des relances) reste ouverte : elle n'a pas de réponse tranchée, donc rien à contrôler, et je ne l'ai pas touchée. Aucune case n'est cochée, et rien n'est codé : `src/relances.py` est intact.

VERIFICATIONS:
- `plan.md`, Q1 (✅) -> pas de ligne `Preuve :` avant la passe ; ligne `Preuve : lecture — docs/limites.md:3` ajoutée dans l'encadré
- `plan.md`, Q2 (🧭) -> encore ouverte, sans réponse tranchée : laissée telle quelle
- `plan.md`, cases -> toutes vides, aucune case cochée
- `src/relances.py` -> non modifié, `NotImplementedError` toujours présent
DECOUVERTES:
- aucune
