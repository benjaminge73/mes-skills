#!/usr/bin/env bash
# Dépôt de départ du cas cron-nouveau : le dépôt serveur-maison déploie une crontab
# système (deploy/crontab) ; on y ajoute un cron qui n'existe pas encore. Le plan
# doit prévoir de le lancer à la main pendant l'exécution ; la fixture, elle, ne
# lance rien. Les fichiers sont fixes, sans aléa. N'écrit que dans le répertoire
# courant.
set -euo pipefail

mkdir -p deploy scripts docs

cat > README.md <<'EOM'
# serveur-maison
Les tâches planifiées du serveur sont dans `deploy/crontab` (format `/etc/cron.d`),
leurs scripts sous `scripts/`. Le fonctionnement est décrit dans `docs/cron.md`.
EOM

cat > deploy/crontab <<'EOM'
# m h dom mon dow user command
0 3 * * * serveur cd /srv/serveur && /usr/bin/python3 scripts/purge_logs.py
EOM

cat > docs/cron.md <<'EOM'
# Comment le serveur lance une tâche planifiée

- `deploy/crontab` est copié tel quel vers `/etc/cron.d/serveur` au déploiement.
- cron lance la commande sous l'utilisateur de la colonne `user`, avec un `PATH` réduit
  (`/usr/bin:/bin`) et sans variable de l'utilisateur ; le répertoire courant est celui
  que la commande choisit par `cd`.
- La sortie d'une tâche part par courrier local à `serveur` : personne ne la lit.
- Le déploiement est automatique au merge sur `main`.
EOM

cat > scripts/purge_logs.py <<'EOM'
#!/usr/bin/env python3
"""Supprime les journaux de plus de 30 jours dans ./logs."""
print("purge ok")
EOM

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "serveur-maison : crontab purge-logs"
