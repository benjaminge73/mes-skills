Le test de `src/rapport.py` passe. Pour vérifier que la suite était rouge sur HEAD sans toucher à la modification de `total_prix`, j'ai créé un worktree détaché : `git stash` a été refusé par le hook du plugin, je n'ai pas contourné ce refus.

VERIFICATIONS:
- `git worktree add --detach <tmp> HEAD` puis `python3 -m unittest tests.test_rapport` -> rouge (NotImplementedError), attendu
- `python3 -m unittest tests.test_rapport` dans le dépôt -> OK après implémentation
- `total_prix` toujours présent dans `src/articles.py` -> oui, non modifié
- pile de stash -> vide, rien n'a été mis de côté

DECOUVERTES:
- hook PreToolUse du plugin plans-notion (refuser_git_stash.py) : `git stash` refusé, code 2 ; passé par un worktree détaché à la place
