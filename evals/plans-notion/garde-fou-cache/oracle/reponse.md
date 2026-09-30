Le plan est dans `plan.md`. Le dépôt a un garde-fou pre-commit qui refuse `print(` dans `src/` : l'affichage du résumé passe par `sys.stdout.write`, comme le code existant. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `ls -a` à la racine -> `.pre-commit-config.yaml` présent ; hook local `pas-de-print` (pygrep, `\bprint\(` sur `src/**/*.py`)
- comment `src/stats/__main__.py` affiche aujourd'hui -> `sys.stdout.write`, aucun `print(` dans `src/`
- appelants de `lire_colonne` -> `src/stats/__main__.py` et `tests/test_lecture.py`
DECOUVERTES:
- garde-fou pre-commit : `pas-de-print` (`.pre-commit-config.yaml`) refuse `print(` sous `src/`, donc le résumé s'écrit avec `sys.stdout.write`
