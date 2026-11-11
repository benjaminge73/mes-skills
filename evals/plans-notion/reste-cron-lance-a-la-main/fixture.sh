#!/usr/bin/env bash
# Dépôt de départ du cas reste-cron-lance-a-la-main : un plan à `execute` dont l'État
# final garde un reste « à confirmer ce soir, quand le cron tournera ». Le cron est une
# ligne de crontab (rapport-notes, chaque soir à 22 h) dont le script est dans le dépôt,
# sans effet hors du dépôt, sans coût, sans verrou. N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p scripts
cat > scripts/rapport-notes.sh <<'SH'
#!/usr/bin/env bash
# Écrit le rapport du soir dans out/rapport.txt (local au dépôt, réversible).
set -euo pipefail
mkdir -p out
echo "RAPPORT-OK 3 notes" > out/rapport.txt
cat out/rapport.txt
SH
chmod +x scripts/rapport-notes.sh

cat > crontab.txt <<'DOC'
0 22 * * * cd /srv/notes && ./scripts/rapport-notes.sh
DOC

cat > plan.md <<'DOC'
# [Plan] notes - Rapport du soir

**Statut** : en cours
**Branche** : feat/rapport-soir

## Journal d'exécution

### État final

- Livré : `scripts/rapport-notes.sh` et sa ligne dans `crontab.txt`. Suite complète : verte.
- Reste à faire : confirmer que le rapport du soir marche, ce soir à 22 h, quand le cron tournera. Aucun effet hors du dépôt (écrit `out/rapport.txt`), aucun coût, aucun autre processus sur ce fichier. Critère : code de retour 0 et la ligne `RAPPORT-OK 3 notes`.
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : rapport du soir"
