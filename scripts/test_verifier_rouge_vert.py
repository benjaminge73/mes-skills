"""Tests de ``verifier-rouge-vert.py`` : le commit vert ne retouche pas les tests du rouge.

Le script (``plugins/plans-notion/skills/_partage/scripts/``) compare deux SHA : le commit
rouge (tests seuls) et le commit vert (code). Un fichier de test modifié, supprimé ou ajouté
entre les deux : code 1 et la liste des fichiers. Seul le code bougé : code 0. SHA inconnu :
code 2, distinct, pour qu'une panne de lecture ne passe pas pour une triche.

Les tests montent de vrais dépôts git jetables (pas de mock) dans un dossier temporaire, avec
un HOME isolé : aucun ne touche le vrai dépôt ni la config git du poste.

Pannes attrapées :
- ``test_skip_ajoute_au_vert_...`` : un test désactivé (``@unittest.skip``, ``xfail``,
  ``skipTest``) passe au vert sans que personne le voie. Un script qui ne lit que le code
  laisserait passer la triche la plus courante.
- ``test_assertion_retiree_ou_remplacee_...`` : une assertion supprimée, ou remplacée par
  ``assert True`` ou ``pass``, fait passer le test sans rien tester.
- ``test_seul_le_code_bouge_sort_en_0`` : le contrat du cas légitime. Un script qui sort en 1
  sur tout commit vert deviendrait un faux rouge, et la preuve serait contournée.
- ``test_sha_inconnu_sort_en_2`` : un SHA faux rend un code distinct et nomme le SHA. Sans
  cela, une faute de frappe ressemble à une réussite (code 0) ou à un écart de test (code 1).
- ``test_fichier_de_test_supprime_au_vert_sort_en_1`` (en plus du budget du brief) : supprimer
  le fichier de test efface les assertions d'un coup, sans aucune ligne « assertion » retirée
  dans le diff. Les tests ci-dessus ne le voient pas : ``bons-tests.md`` (règle 8) le range
  pourtant parmi les gestes de contournement.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = (RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts"
          / "verifier-rouge-vert.py")
TEST = "tests/test_calc.py"
CODE = "calc.py"
CODE_VERT = "def somme(a, b):\n    return a + b\n"

# Le commit rouge : deux tests qui échouent tant que ``calc.somme`` n'existe pas.
TEST_ROUGE = (
    "import unittest\n"
    "\n"
    "from calc import somme\n"
    "\n"
    "\n"
    "class TestSomme(unittest.TestCase):\n"
    "    def test_somme_de_deux_nombres(self):\n"
    "        self.assertEqual(somme(2, 3), 5)\n"
    "        self.assertEqual(somme(3, 2), 5)\n"
    "\n"
    "    def test_somme_avec_zero(self):\n"
    "        self.assertEqual(somme(4, 0), 4)\n"
)

# Des façons de désactiver le test, chacune en une ligne ajoutée au rouge.
DESACTIVATIONS = {
    "@unittest.skip": (
        "    def test_somme_de_deux_nombres",
        '    @unittest.skip("plus tard")\n    def test_somme_de_deux_nombres'),
    "@pytest.mark.xfail": (
        "    def test_somme_de_deux_nombres",
        "    @pytest.mark.xfail\n    def test_somme_de_deux_nombres"),
    "self.skipTest dans le corps": (
        "        self.assertEqual(somme(2, 3), 5)\n",
        '        self.skipTest("plus tard")\n        self.assertEqual(somme(2, 3), 5)\n'),
}

# Des façons d'affaiblir une assertion, chacune en une ligne du rouge touchée.
AFFAIBLISSEMENTS = {
    "assertion retirée": ("        self.assertEqual(somme(3, 2), 5)\n", ""),
    "assertion remplacée par assert True": ("        self.assertEqual(somme(2, 3), 5)\n",
                                            "        assert True\n"),
    "assertion remplacée par pass": ("        self.assertEqual(somme(2, 3), 5)\n",
                                     "        pass\n"),
}


class VerifierRougeVert(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
        self.env["HOME"] = str(self.dossier / "home")
        self.env["GIT_CONFIG_NOSYSTEM"] = "1"
        self._compteur = 0

    def _git(self, depot, *args):
        r = subprocess.run(["git", *args], cwd=depot, env=self.env,
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def _depot(self):
        self._compteur += 1
        depot = self.dossier / f"depot-{self._compteur}"
        depot.mkdir()
        self._git(depot, "init", "-q")
        self._git(depot, "config", "user.email", "test@example.invalid")
        self._git(depot, "config", "user.name", "test")
        self._git(depot, "config", "commit.gpgsign", "false")
        self._commit(depot, {"README.md": "demo\n"}, "chore: amorce")
        return depot

    def _commit(self, depot, fichiers, message):
        """Écrit les fichiers (``None`` = suppression), committe, rend le SHA."""
        for chemin, contenu in fichiers.items():
            fichier = depot / chemin
            if contenu is None:
                fichier.unlink()
                continue
            fichier.parent.mkdir(parents=True, exist_ok=True)
            fichier.write_text(contenu, encoding="utf-8")
        self._git(depot, "add", "-A")
        self._git(depot, "commit", "-q", "-m", message)
        return self._git(depot, "rev-parse", "HEAD")

    def _rouge(self, depot):
        return self._commit(depot, {TEST: TEST_ROUGE},
                            "test(demo): étape 5 — rouge (la somme)")

    def _jouer(self, depot, rouge, vert):
        r = subprocess.run([sys.executable, str(SCRIPT), rouge, vert], cwd=depot,
                           env=self.env, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def test_skip_ajoute_au_vert_sort_en_1(self):
        for nom, (avant, apres) in DESACTIVATIONS.items():
            with self.subTest(desactivation=nom):
                depot = self._depot()
                rouge = self._rouge(depot)
                vert = self._commit(depot, {TEST: TEST_ROUGE.replace(avant, apres, 1)},
                                    "feat(demo): étape 5 — la somme")
                code, sortie = self._jouer(depot, rouge, vert)
                self.assertEqual(code, 1, sortie)
                self.assertIn(TEST, sortie)

    def test_assertion_retiree_ou_remplacee_au_vert_sort_en_1(self):
        for nom, (avant, apres) in AFFAIBLISSEMENTS.items():
            with self.subTest(affaiblissement=nom):
                depot = self._depot()
                rouge = self._rouge(depot)
                vert = self._commit(depot, {TEST: TEST_ROUGE.replace(avant, apres, 1)},
                                    "feat(demo): étape 5 — la somme")
                code, sortie = self._jouer(depot, rouge, vert)
                self.assertEqual(code, 1, sortie)
                self.assertIn(TEST, sortie)

    def test_seul_le_code_bouge_sort_en_0(self):
        depot = self._depot()
        rouge = self._rouge(depot)
        vert = self._commit(depot, {CODE: CODE_VERT}, "feat(demo): étape 5 — la somme")
        code, sortie = self._jouer(depot, rouge, vert)
        self.assertEqual(code, 0, sortie)

    def test_sha_inconnu_sort_en_2(self):
        depot = self._depot()
        rouge = self._rouge(depot)
        vert = self._commit(depot, {CODE: CODE_VERT}, "feat(demo): étape 5 — la somme")
        inconnu = "f" * 40
        code, sortie = self._jouer(depot, rouge, inconnu)
        self.assertEqual(code, 2, sortie)
        self.assertIn(inconnu, sortie)

    def test_fichier_de_test_supprime_au_vert_sort_en_1(self):
        depot = self._depot()
        rouge = self._rouge(depot)
        vert = self._commit(depot, {TEST: None, CODE: CODE_VERT},
                            "feat(demo): étape 5 — la somme")
        code, sortie = self._jouer(depot, rouge, vert)
        self.assertEqual(code, 1, sortie)
        self.assertIn(TEST, sortie)


if __name__ == "__main__":
    unittest.main()
