#!/usr/bin/env bash
# Dépôt de départ du cas plan-leger-eligibilite : un petit script de sauvegarde et son
# fichier sudoers. N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p scripts config

cat > README.md <<'EOF'
# sauvegarde

Script de sauvegarde lancé sur le VPS. Les droits sudo qu'il utilise sont dans `config/sudoers-sauvegarde`.
EOF

cat > scripts/sauvegarde.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
sudo /usr/bin/tar -czf /var/backups/app.tar.gz /srv/app
EOF

cat > config/sudoers-sauvegarde <<'EOF'
ubuntu ALL=(root) NOPASSWD: /usr/bin/tar -czf /var/backups/app.tar.gz /srv/app
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "sauvegarde : version initiale"
