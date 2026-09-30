Le plan est dans `plan.md`. Le dépôt contient déjà un jeu de 12 questions de support avec réponse attendue : le banc le réutilise au lieu d'en fabriquer un. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `find . -name "*.jsonl"` puis lecture -> `tests/golden/questions_support.jsonl`, 12 questions (id, question, reponse_attendue), lu par `tests/test_golden.py`
- comment le bot appelle un modèle -> `bot/repondre.py` passe par `bot/llm.py::complete(modele, prompt)`, non branché (`NotImplementedError`)
- où se règle le modèle -> `config.toml`, une seule valeur `modele`
DECOUVERTES:
- jeu de questions existant : `tests/golden/questions_support.jsonl` (12 questions de support avec réponse attendue) sert de base au banc
- client LLM non branché : `bot/llm.py::complete` lève `NotImplementedError`, il faut le brancher pour les trois modèles
