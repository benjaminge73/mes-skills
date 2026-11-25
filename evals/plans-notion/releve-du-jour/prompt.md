---
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Bash]
---
Tu es le pilote d'un plan qui change `config/sudoers.d/ubuntu-exec` dans le dépôt courant : ce fichier porte les droits de la session de l'exécutant. Avant d'écrire l'étape, fais le relevé du jour du VPS avec le script `releve-du-jour.py` du plugin `plans-notion` (`skills/_partage/scripts/releve-du-jour.py`), en lui passant ce fichier par son option `--objets` (chemin relatif au répertoire courant). Le relevé est en lecture seule : tu ne modifies, n'écris et ne commites rien, et tu n'enquêtes pas toi-même sur le droit que contient le fichier.

Ta réponse finale : la fiche rendue par le relevé, recopiée telle quelle, puis, pour chaque ligne `SECURITE`, une question d'office à Benjamin en une phrase.
