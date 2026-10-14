# Ignorer les fichiers .tmp dans le cron sauvegarde-notes

## Cartes

`scripts/sauvegarde_notes.py` (le script du cron) ; `cron/jobs.json` (le job `sauvegarde-notes`) ; `docs/cron.md` (ce que Hermes fait d'un script de cron).

## Besoins

- Le cron `sauvegarde-notes` ne doit plus copier les fichiers `.tmp`.
- Le changement doit être prouvé par un lancement réel du cron, pas seulement par un test unitaire.

## Maquette

Maquette dispensée : le cron n'a pas d'interface, rien de visible ne change.

## Contraintes vérifiées

- Le job `sauvegarde-notes` a pour `workdir` `/home/ubuntu/notes` : le script copie les `.md` de ce répertoire vers `../sauvegarde/`, soit `/home/ubuntu/sauvegarde/` (`cron/jobs.json`, `scripts/sauvegarde_notes.py`).
- Hermes lance le script avec l'interpréteur du projet, le `workdir` du job pour répertoire courant, et un environnement assaini (`docs/cron.md`, points 2 à 4).
- `hermes cron run <id>` ne lance pas le job tout de suite : il part au prochain tick, 60 s au plus tard, gateway vivante (`docs/cron.md`, point 5).

## Exécution

### Étape 1 — Ignorer les fichiers .tmp

- **Fichiers touchés** : `scripts/sauvegarde_notes.py`.
- **Preuve de fin** : un test place un `.tmp` dans un répertoire jetable et constate qu'il n'est pas copié ; le test est rouge avant le changement.
- **Test attendu** : un test de non-copie des `.tmp`.

### Étape C1 — Lancer le cron à la main

- **Lancement équivalent** : depuis le worktree du plan, `env -i <interpréteur> <worktree>/scripts/sauvegarde_notes.py`, avec pour répertoire courant le `workdir` du job, `/home/ubuntu/notes`. L'interpréteur est celui que Hermes résout pour ce job, pas le `python3` du système.
- **Critère de succès** : code de sortie 0, et la ligne `sauvegarde ok: <n> fichiers` sur la sortie standard.
- **Durée maximale** : 60 s (timeout) ; au-delà, le lancement est tué et l'étape est en échec.
- **Effets externes tranchés** : le script ne copie que vers `../sauvegarde/` (soit `/home/ubuntu/sauvegarde/`), et l'opération est réversible (les copies se suppriment). Le lancement est donc réel, pas à blanc : un lancement à blanc ne prouverait pas la copie.
- **Après le merge et le déploiement** : `hermes cron run sauvegarde-notes`, gateway vivante, attendre le tick (60 s au plus), puis lire `last_status` du job.
- **Fichiers touchés** : aucun.
- **Preuve de fin** : la sortie du lancement équivalent (code 0, ligne `sauvegarde ok`), citée dans la réponse finale.

## Journal d'exécution

_Se remplira à l'exécution._
