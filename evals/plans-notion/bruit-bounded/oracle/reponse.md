Le plan est dans `plan.md` : une seule étape, l'option `--version` lue depuis les métadonnées du paquet. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- suite de tests du dépôt intact -> `python -m unittest discover -s tests` : 2 tests, OK
- version déclarée -> `pyproject.toml:3`, `version = "1.2.0"`
- comment la CLI lit ses arguments -> `argparse` dans `convertisseur/__main__.py`, une seule entrée
DECOUVERTES:
- aucune
