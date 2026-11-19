"""Tests de ``comparer_versions.py`` : la sortie des scripts de ``_partage``.

Le contrat : un script qui change de sortie sur un plan de référence fait un
écart, sauf si un commit de la PR le déclare (``Ecart-admis: <script> — <raison>``).

Les tests montent un vrai dépôt git jetable (pas de mock) : un script et un plan,
une base et une tête, et on lance le garde en ligne de commande.

Pannes attrapées :
- ``test_meme_sortie_...`` : un garde qui compare le texte du script au lieu de
  sa sortie crierait à chaque modification, même sans effet (ici : un commentaire).
  C'est aussi le cas « une version identique ne donne aucun écart ».
- ``test_sortie_changee_...`` : un écart réel passe inaperçu (la panne à éviter).
- ``test_ecart_declare_...`` : une déclaration valide n'exempte pas la PR (faux rouge).
- ``test_declaration_sans_raison_...`` (en plus du budget du brief) : une
  déclaration sans raison exempterait n'importe quel écart ; la forme est refusée,
  comme ``Eval-cas: aucun`` sans raison.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
COMPARER = RACINE / "scripts" / "comparer_versions.py"
SCRIPT = "plugins/demo/skills/_partage/scripts/sortie.py"
V1 = "import sys\nprint('sortie v1 pour', sys.argv[1])\n"
V2 = "import sys\nprint('sortie v2 pour', sys.argv[1])\n"


def _git(depot: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        cwd=depot, capture_output=True, text=True, check=True,
    )


class DepotDeDeux(unittest.TestCase):
    """Un dépôt jetable : un script, un plan, un commit de base."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        racine = Path(self._tmp.name)
        self.depot = racine / "depot"
        self.plans = racine / "plans"
        self.depot.mkdir()
        self.plans.mkdir()
        (self.plans / "plan.md").write_text("# Plan de test\n", encoding="utf-8")
        _git(self.depot, "init", "-q")
        self.base = self._commiter(SCRIPT, V1, "feat: script de test")

    def tearDown(self):
        self._tmp.cleanup()

    def _commiter(self, chemin: str, contenu: str, message: str) -> str:
        cible = self.depot / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")
        _git(self.depot, "add", "-A")
        _git(self.depot, "commit", "-q", "-m", message)
        return _git(self.depot, "rev-parse", "HEAD").stdout.strip()

    def _comparer(self, base: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(COMPARER), "--racine", str(self.depot),
             "--base", base, "--plans", str(self.plans)],
            capture_output=True, text=True, encoding="utf-8",
        )


class MemeSortie(DepotDeDeux):
    def test_meme_sortie_malgre_un_fichier_modifie_ne_donne_aucun_ecart(self):
        self._commiter(SCRIPT, V1 + "# commentaire sans effet sur la sortie\n", "docs: commentaire")
        res = self._comparer(self.base)
        sortie = res.stdout + res.stderr
        self.assertEqual(res.returncode, 0, sortie)
        self.assertIn("Aucun écart non déclaré", sortie)


class SortieChangee(DepotDeDeux):
    def test_sortie_changee_sur_un_plan_est_signalee_sans_declaration(self):
        self._commiter(SCRIPT, V2, "fix: sortie v2")
        res = self._comparer(self.base)
        sortie = res.stdout + res.stderr
        self.assertEqual(res.returncode, 1, sortie)
        self.assertIn("Écarts NON déclarés", sortie)
        self.assertIn("sortie.py", sortie)
        self.assertIn("plan.md", sortie)


class EcartDeclare(DepotDeDeux):
    def test_ecart_declare_par_un_commit_ne_bloque_pas(self):
        self._commiter(SCRIPT, V2, "fix: sortie v2\n\nEcart-admis: sortie.py — la sortie v2 est voulue")
        res = self._comparer(self.base)
        sortie = res.stdout + res.stderr
        self.assertEqual(res.returncode, 0, sortie)
        self.assertIn("déclarés", sortie)
        self.assertIn("sortie.py", sortie)


class DeclarationSansRaison(DepotDeDeux):
    def test_declaration_sans_raison_est_refusee_et_n_exempte_pas(self):
        self._commiter(SCRIPT, V2, "fix: sortie v2\n\nEcart-admis: sortie.py")
        res = self._comparer(self.base)
        sortie = res.stdout + res.stderr
        self.assertEqual(res.returncode, 1, sortie)
        self.assertIn("invalide", sortie)


if __name__ == "__main__":
    unittest.main()
