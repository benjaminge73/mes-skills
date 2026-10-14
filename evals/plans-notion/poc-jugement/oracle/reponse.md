Le plan est dans `plan.md`. La formulation A est retenue : elle satisfait les trois critères de `docs/criteres.md`, la formulation B les viole tous les trois. Le jugement a été délégué à l'agent `plans-notion:evaluateur`, sans paramètre `model`. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `docs/criteres.md` -> trois critères : numéro de commande en premier, moins de 60 mots, aucune date de remboursement
- `prompts/accueil_a.md` (agent plans-notion:evaluateur) -> satisfait les trois critères
- `prompts/accueil_b.md` (agent plans-notion:evaluateur) -> viole les trois critères (numéro en fin de consigne, 110 mots, remboursement sous 48 h promis)
- `prompts/accueil_a.md` -> non modifié
DECOUVERTES:
- aucune
