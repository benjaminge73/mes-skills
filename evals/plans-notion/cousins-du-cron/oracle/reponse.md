Le plan est dans `plan.md`. L'étape 1 ajoute le refus de `git push --force` au hook, l'étape 2 la validation de `plugin.json` dans `deploy.yml`. Comme ni le hook ni le workflow ne tournent pendant la session, l'étape C1 lance le hook à la main avec un JSON d'événement (un cas refusé, un cas qui doit passer), et l'étape C2 rejoue le workflow par act, publication sautée, ou le regarde au premier run avec `gh run watch`. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `plugins/garde/hooks/refuser.py` -> lit `tool_input.command` sur l'entrée standard, code 2 pour refuser
- `.github/workflows/deploy.yml` -> déclenché par `push` sur `main`, publie par `scp`
- `plan.md` -> étapes C1 (hook à la main, JSON sur l'entrée standard) et C2 (act ou premier run, `gh run watch`)
DECOUVERTES:
- aucune
