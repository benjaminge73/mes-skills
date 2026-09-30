Le plan est dans `plan.md`. `format_prix` a quatre appelants dans trois autres modules, dont un sous alias et un désigné par son nom en chaîne ; toutes les étapes en tiennent compte. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `grep -rn format_prix .` -> `core/prix.py:1` (définition), `billing/facture.py:1,5`, `reports/mensuel.py:1` (importé `as fp`), `web/filtres.py:4` (nom en chaîne), `tests/test_prix.py`
- `grep -rn "fp(" .` -> un seul appel sous l'alias : `reports/mensuel.py:5`
- comment `web/filtres.py` appelle la fonction -> `getattr(prix, FILTRES[nom])(*args)` : aucun appel visible par son nom, aucune erreur avant l'exécution
DECOUVERTES:
- appel sous alias : `reports/mensuel.py` importe `format_prix as fp`, une recherche de `format_prix(` le manque
- appel par nom en chaîne : `web/filtres.py` désigne `"format_prix"` dans `FILTRES` puis `getattr` ; le nouveau paramètre y manquera sans erreur de syntaxe, seulement un `TypeError` à l'exécution
