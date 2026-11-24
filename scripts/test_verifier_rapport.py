"""Tests de ``verifier-rapport.py`` : le rapport d'un exécutant coche une case prouvée par champ de l'étape.

Le script (``plugins/plans-notion/skills/_partage/scripts/``) lit le brief d'une étape (ses puces
``- **Champ** : valeur``) et le rapport (ses cases ``- [x] <champ> — preuve : …``). Une case
manquante, non cochée ou cochée sans preuve : code 1, la case nommée sur la sortie standard.
Tout coché avec preuve : code 0. Entrée illisible ou brief sans champ : code 2.

Les tests lancent le vrai script sur de vrais fichiers temporaires (pas de mock). Aucun ne lit
le dépôt de travail.

Pannes attrapées :
- ``test_case_test_attendu_cochee_sans_preuve_sort_en_1`` : la case « Test attendu » est cochée
  sans sa preuve. C'est la panne nommée par l'étape : un rapport DONE qui affirme le test sans
  le montrer doit sortir en 1, et nommer la case.
- ``test_rapport_complet_sort_en_0`` (en plus du budget) : un script qui rendrait toujours 1
  passerait le test précédent. Ce test vérifie qu'un rapport complet, qui ne coche pas le champ
  des métadonnées du pilote (« Dépend de »), sort en 0.
- ``test_case_manquante_sort_en_1`` (en plus du budget) : un rapport qui omet la ligne « Test
  attendu » au lieu de la cocher sans preuve. Sans ce test, l'omission passerait en 0.
- ``test_brief_absent_sort_en_2`` (en plus du budget) : un brief introuvable doit sortir en 2,
  distinct de 0 et de 1. Sans ce test, une faute de chemin pourrait passer pour un rapport
  conforme ou pour une case manquante.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = (RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts"
          / "verifier-rapport.py")

BRIEF = """# Étape 4 — exemple

- **Fichiers touchés** : `scripts/exemple.py`
- **Preuve de fin** : `pytest -q` vert
- **Test attendu** : un rapport DONE dont la case « Test attendu » est cochée sans preuve rend 1.
- **Dépend de** : Q3
"""

RAPPORT_SANS_PREUVE_DU_TEST = """**État** : DONE

- [x] Fichiers touchés — preuve : `git diff --name-only` rend `scripts/exemple.py`
- [x] Preuve de fin — preuve : `3 passed in 0.02s`
- [x] Test attendu
"""

RAPPORT_COMPLET = """**État** : DONE

- [x] Fichiers touchés — preuve : `git diff --name-only` rend `scripts/exemple.py`
- [x] Preuve de fin — preuve : `3 passed in 0.02s`
- [x] Test attendu — preuve : rouge `1 failed`, vert `1 passed`
"""

RAPPORT_SANS_LA_CASE_TEST = """**État** : DONE

- [x] Fichiers touchés — preuve : `git diff --name-only` rend `scripts/exemple.py`
- [x] Preuve de fin — preuve : `3 passed in 0.02s`
"""


class VerifierRapport(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name)

    def _lancer(self, rapport: str) -> subprocess.CompletedProcess:
        brief = self.dossier / "brief.md"
        brief.write_text(BRIEF, encoding="utf-8")
        fichier_rapport = self.dossier / "rapport.md"
        fichier_rapport.write_text(rapport, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--brief", str(brief), "--rapport", str(fichier_rapport)],
            capture_output=True, text=True, encoding="utf-8")

    def test_case_test_attendu_cochee_sans_preuve_sort_en_1(self) -> None:
        resultat = self._lancer(RAPPORT_SANS_PREUVE_DU_TEST)
        self.assertEqual(resultat.returncode, 1, resultat.stdout + resultat.stderr)
        self.assertIn("Test attendu", resultat.stdout)
        self.assertNotIn("Preuve de fin", resultat.stdout)

    def test_rapport_complet_sort_en_0(self) -> None:
        resultat = self._lancer(RAPPORT_COMPLET)
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)

    def test_case_manquante_sort_en_1(self) -> None:
        resultat = self._lancer(RAPPORT_SANS_LA_CASE_TEST)
        self.assertEqual(resultat.returncode, 1, resultat.stdout + resultat.stderr)
        self.assertIn("Test attendu", resultat.stdout)

    def test_brief_absent_sort_en_2(self) -> None:
        resultat = subprocess.run(
            [sys.executable, str(SCRIPT), "--brief", str(self.dossier / "absent.md"),
             "--rapport", str(self.dossier / "absent.md")],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(resultat.returncode, 2, resultat.stdout + resultat.stderr)


if __name__ == "__main__":
    unittest.main()
