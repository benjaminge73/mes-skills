Le plan est dans `plan.md`. Le cron `sauvegarde-notes` doit ignorer les fichiers `.tmp` : l'étape 1 modifie `scripts/sauvegarde_notes.py` et l'étape C1 lance le cron à la main, par un lancement équivalent depuis le worktree (`env -i`, répertoire courant = `workdir` du job `/home/ubuntu/notes`), avec un critère de succès, une durée maximale de 60 s et les effets externes tranchés. Après le merge et le déploiement, le rejeu réel est `hermes cron run sauvegarde-notes`. Rien n'est codé tant que le plan n'est pas validé, et le script n'est pas touché.

VERIFICATIONS:
- `cron/jobs.json` -> job `sauvegarde-notes` : script `sauvegarde_notes.py`, `workdir` `/home/ubuntu/notes`
- `docs/cron.md` -> interpréteur résolu par Hermes, `workdir` pour répertoire courant, environnement assaini, tick au plus 60 s après `hermes cron run`
- `scripts/sauvegarde_notes.py` -> non modifié, `def sauvegarder(racine):` toujours présent
- `plan.md` -> étape C1 présente, avec lancement équivalent, `env -i`, workdir, critère de succès, durée maximale et rejeu `hermes cron run` après merge
DECOUVERTES:
- aucune
