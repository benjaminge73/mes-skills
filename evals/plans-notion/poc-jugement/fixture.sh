#!/usr/bin/env bash
# Dépôt de départ du cas poc-jugement : un bot de support doit adopter une consigne
# d'accueil, en deux formulations (A et B). Le choix relève d'un jugement, qui se
# fonde sur les trois critères écrits dans docs/criteres.md. Les fichiers sont
# fixes, sans aléa. N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p docs prompts

cat > README.md <<'EOF'
# assistant-support

Module de consigne d'accueil du bot de support.

Les critères d'une bonne consigne sont dans `docs/criteres.md`.
EOF

cat > docs/criteres.md <<'EOF'
# Critères d'une bonne consigne d'accueil

1. Demander le numéro de commande avant toute autre chose.
2. Tenir en moins de 60 mots.
3. Ne jamais promettre de date de remboursement.
EOF

cat > prompts/accueil_a.md <<'EOF'
# Consigne d'accueil — formulation A

Accueille le client avec courtoisie et remercie-le de son message. Demande-lui d'abord son numéro de commande, avant toute autre question. Écoute ensuite sa demande et dis clairement ce que tu peux faire pour lui. Reste concis et ne promets aucune date de remboursement.
EOF

cat > prompts/accueil_b.md <<'EOF'
# Consigne d'accueil — formulation B

Tu es l'assistant de support d'une équipe qui tient vraiment à ses clients, et chaque message compte pour nous. Commence par accueillir la personne avec chaleur, en lui montrant que tu as pris le temps de lire ce qu'elle nous écrit et que son problème nous importe. Explique-lui avec bienveillance que tu vas l'aider du mieux que tu peux, sans jamais la laisser seule face à sa difficulté. Quand la conversation avance et que le ton s'est apaisé, demande-lui enfin son numéro de commande, pour pouvoir retrouver son dossier. Précise aussi qu'elle recevra un remboursement sous 48 h dès que le dossier sera validé.
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "assistant-support : consignes d'accueil A et B"
