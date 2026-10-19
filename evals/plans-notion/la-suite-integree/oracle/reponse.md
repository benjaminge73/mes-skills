Le plan est dans `plan.md`. Les trois restes sont triés : la docstring de `lister` entre dans le plan (étape 2), l'export CSV reste dans `plan-export.md` et la suite le cite, le passage à SQLite devient un plan à part, cité aussi.

VERIFICATIONS:
- `grep -rn "triées" notes/` -> `notes/commandes.py:6`, la docstring de `lister` dit « date », le code trie par titre
- `plan-export.md` -> porte déjà l'export CSV (étape 1)
DECOUVERTES:
- docstring de `lister` : dit « triées par date », le tri est par titre ; ajoutée au plan, étape 2
