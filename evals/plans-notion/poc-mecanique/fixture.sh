#!/usr/bin/env bash
# Dépôt de départ du cas poc-mecanique : un module de reporting qui doit recevoir
# le journal des commandes. Deux options de livraison (export unique, export
# paginé) ; le choix dépend d'un comptage d'enregistrements, seuil écrit dans
# docs/export.md. Le fichier data/commandes.csv compte 1843 enregistrements (lignes
# de données, hors en-tête) : nombre fixe, généré sans aléa. N'écrit que dans le
# répertoire courant.
set -euo pipefail

mkdir -p export data docs

cat > README.md <<'EOF'
# reporting-commandes

Module qui prépare le journal des commandes pour l'import du reporting.

Le seuil d'export se lit dans `docs/export.md`.
EOF

cat > docs/export.md <<'EOF'
# Export du journal des commandes

Le reporting importe le journal depuis `data/commandes.csv`.

- au-delà de 2 000 enregistrements, il faut paginer l'export ;
- en deçà, un export unique suffit.

Un enregistrement est une ligne de données, l'en-tête exclu.
EOF

cat > export/__init__.py <<'EOF'
"""reporting-commandes : export du journal."""
EOF

cat > export/exporter.py <<'EOF'
def exporter_unique(commandes, sortie):
    """Écrit tout le journal dans un seul fichier. Pas encore branché."""
    raise NotImplementedError("export unique à écrire après validation du plan")
EOF

awk 'BEGIN {
  print "id,client,montant_centimes"
  for (i = 1; i <= 1843; i++) printf "%d,client-%d,%d\n", i, i % 97, (i * 37) % 20000 + 100
}' > data/commandes.csv

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "reporting-commandes : journal et seuil d'export"
