#!/usr/bin/env bash
# Dépôt de départ du cas cron-a-la-main : le dépôt hermes-maison pilote un cron
# Hermes, « sauvegarde-notes », dont le script doit désormais ignorer les fichiers
# .tmp. Le plan doit prévoir de lancer ce cron à la main pendant l'exécution ; la
# fixture, elle, ne lance rien. Les fichiers sont fixes, sans aléa. N'écrit que
# dans le répertoire courant.
set -euo pipefail

mkdir -p cron scripts docs

cat > README.md <<'EOF'
# hermes-maison
Crons Hermes du poste : les jobs sont dans `cron/jobs.json`, leurs scripts sous `scripts/`.
Ce que Hermes fait d'un script de cron est décrit dans `docs/cron.md`.
EOF

cat > cron/jobs.json <<'EOF'
{
  "jobs": [
    {
      "id": "sauvegarde-notes",
      "schedule": "30 2 * * *",
      "script": "sauvegarde_notes.py",
      "workdir": "/home/ubuntu/notes",
      "no_agent": true
    }
  ]
}
EOF

cat > docs/cron.md <<'EOF'
# Comment Hermes lance un script de cron

- Le script doit résider sous `$HERMES_HOME/scripts/`.
- L'interpréteur est celui du projet, résolu par Hermes, et non le `python3` du système.
- Le répertoire courant est le champ `workdir` du job ; à défaut, le dossier du script.
- L'environnement est assaini : aucun identifiant de fournisseur n'y passe.
- `hermes cron run <id>` ne lance pas le job tout de suite : il part au prochain tick du planificateur, au plus 60 s plus tard, gateway vivante.
EOF

cat > scripts/sauvegarde_notes.py <<'EOF'
#!/usr/bin/env python3
"""Copie les notes Markdown du répertoire courant vers ../sauvegarde/."""
import shutil
from pathlib import Path


def sauvegarder(racine):
    destination = Path(racine).resolve().parent / "sauvegarde"
    destination.mkdir(exist_ok=True)
    fichiers = [f for f in Path(racine).iterdir() if f.is_file() and f.suffix == ".md"]
    for fichier in sorted(fichiers):
        shutil.copy2(fichier, destination / fichier.name)
    return len(fichiers)


if __name__ == "__main__":
    print(f"sauvegarde ok: {sauvegarder('.')} fichiers")
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "hermes-maison : cron sauvegarde-notes"
