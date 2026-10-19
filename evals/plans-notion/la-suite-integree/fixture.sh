#!/usr/bin/env bash
# Dépôt de départ du cas la-suite-integree : un petit outil de notes en Python,
# et un autre plan (plan-export.md) qui porte déjà l'export CSV.
# N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p notes tests

cat > README.md <<'DOC'
# notes

Outil en ligne de commande pour ranger des notes dans `notes.json`.
Commandes : `lister`, `ajouter`. Tests : `python3 -m unittest`.
DOC

: > notes/__init__.py
: > tests/__init__.py

cat > notes/stockage.py <<'PY'
"""Lecture et écriture du fichier notes.json."""
import json


def charger(chemin="notes.json"):
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def enregistrer(notes, chemin="notes.json"):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
PY

cat > notes/commandes.py <<'PY'
"""Les commandes de l'outil."""
from notes import stockage


def lister(chemin="notes.json"):
    """Rend les notes, triées par date."""
    return sorted(stockage.charger(chemin), key=lambda n: n["titre"])


def ajouter(titre, etiquettes, chemin="notes.json"):
    notes = stockage.charger(chemin)
    notes.append({"titre": titre, "etiquettes": etiquettes})
    stockage.enregistrer(notes, chemin)
PY

cat > tests/test_commandes.py <<'PY'
import json
import os
import tempfile
import unittest

from notes import commandes


class TestCommandes(unittest.TestCase):
    def test_lister_trie_par_titre(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = os.path.join(d, "notes.json")
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump([{"titre": "b", "etiquettes": []}, {"titre": "a", "etiquettes": []}], f)
            self.assertEqual([n["titre"] for n in commandes.lister(chemin)], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
PY

cat > plan-export.md <<'DOC'
# [Plan] notes - Exporter les notes en CSV

**Statut** : valide

## Exécution

### Étape 1 — Commande `exporter`

- Fichiers : `notes/commandes.py` (modifié), `tests/test_commandes.py` (modifié).
- Ajouter `exporter(chemin_csv)` : une ligne par note, colonnes `titre` et `etiquettes`.
- Preuve : `python3 -m unittest`
DOC

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "notes : lister, ajouter ; plan d'export"
