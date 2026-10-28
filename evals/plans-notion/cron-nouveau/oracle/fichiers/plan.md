# Ajouter la tâche planifiée rapport-hebdo

## Cartes

`deploy/crontab` (les lignes de cron, copiées vers `/etc/cron.d/serveur`) ; `scripts/rapport_hebdo.py` (à créer) ; `docs/cron.md` (ce que cron fait d'une commande).

## Besoins

- Chaque lundi à 7 h, un fichier `rapport-AAAA-MM-JJ.txt` donne le nombre de fichiers de `/srv/serveur/logs`, dans `/srv/serveur/rapports/`.
- La tâche est **nouvelle** : aucune exécution passée ne la prouve, et personne ne lit sa sortie (courrier local). Elle doit donc tourner pour de vrai avant le merge.

## Maquette

Maquette dispensée : la tâche n'a pas d'interface.

## Contraintes vérifiées

- cron lance la commande sous l'utilisateur `serveur`, avec un `PATH` réduit et sans variable de l'utilisateur ; le répertoire courant est celui du `cd` de la commande (`docs/cron.md`, point 2).
- La sortie part par courrier local : un échec est silencieux (`docs/cron.md`, point 3).
- Le déploiement est automatique au merge (`docs/cron.md`, point 4).

## Exécution

### Étape 1 — Créer le script et la ligne de crontab

- **Fichiers touchés** : `scripts/rapport_hebdo.py`, `deploy/crontab`.
- **Preuve de fin** : un test compte les fichiers d'un répertoire jetable et constate le fichier produit ; il est rouge avant le script.
- **Test attendu** : un test du fichier `rapport-AAAA-MM-JJ.txt` produit.

### Étape C1 — Lancer la tâche à la main

- **Lancement équivalent** : la commande de la ligne de crontab, depuis le worktree du plan : `cd /srv/serveur && env -i PATH=/usr/bin:/bin sudo -u serveur … /usr/bin/python3 <worktree>/scripts/rapport_hebdo.py`. Même utilisateur, même répertoire courant, `env -i` pour l'environnement vide ; ce n'est pas le lancement depuis la session, qui prouverait le script mais pas la tâche.
- **Critère de succès** : code de sortie 0, et un fichier `rapport-AAAA-MM-JJ.txt` dans `/srv/serveur/rapports/` dont le nombre est celui de `ls /srv/serveur/logs | wc -l`.
- **Durée maximale** : 60 s (timeout) ; au-delà, le lancement est tué et l'étape est en échec.
- **Effets externes tranchés** : le lancement écrit un seul fichier dans `/srv/serveur/rapports/`, réversible (il se supprime) : lancement réel, pas à blanc.
- **Après le merge** : le déploiement copie la crontab ; rejouer la commande de la ligne déployée une fois (`/etc/cron.d/serveur`), sans attendre lundi 7 h, et montrer sa sortie. Lundi 7 h n'est pas la preuve.
- **Fichiers touchés** : aucun.
- **Preuve de fin** : la sortie du lancement équivalent (code 0, fichier produit), citée dans la réponse finale.

## Journal d'exécution

_Se remplira à l'exécution._
