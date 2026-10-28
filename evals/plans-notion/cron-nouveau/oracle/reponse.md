Le plan est dans `plan.md`. La tâche `rapport-hebdo` est nouvelle : l'étape 1 crée `scripts/rapport_hebdo.py` et la ligne de `deploy/crontab`, et l'étape C1 la lance à la main pendant l'exécution, par un lancement équivalent (même utilisateur `serveur`, `cd /srv/serveur`, `env -i`), avec un critère de succès, une durée maximale de 60 s et les effets externes tranchés. Après le merge et le déploiement, la commande de la ligne déployée est rejouée une fois : la preuve n'attend pas lundi 7 h. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `deploy/crontab` -> une ligne, `purge_logs.py`, utilisateur `serveur`, `cd /srv/serveur`
- `docs/cron.md` -> utilisateur de la colonne `user`, `PATH` réduit, sortie par courrier local, déploiement au merge
- `scripts/purge_logs.py` -> non modifié
- `plan.md` -> étape C1 présente, avec lancement équivalent, `env -i`, utilisateur, répertoire du job, critère de succès, durée maximale et rejeu après merge
DECOUVERTES:
- aucune
