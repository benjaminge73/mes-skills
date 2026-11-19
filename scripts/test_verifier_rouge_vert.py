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
- ``test_fichier_du_rouge_hors_des_dossiers_de_test_sort_en_1`` (correctif D2) : un test écrit
  hors de ``tests/`` et sans nom de test (``spec/calc_spec.rb``) n'était pas vu : le script ne
  reconnaissait un test qu'à son dossier ou son nom. Le rouge ne porte que des tests : tout
  fichier qu'il contient en est un.
- ``test_chemin_de_tests_avec_dot_slash_est_normalise`` (correctif D2) : ``--tests ./tests``
  ne reconnaissait aucun fichier sous ``tests/`` (sortie 0). Deux cas : le relecteur (un test du
  rouge réduit à ``pass``), et un fichier sous ``tests/`` absent du rouge, qui isole la
  normalisation (la règle « fichier du rouge » ne le rattrape pas).
- ``test_conftest_ajoute_au_vert_sort_en_1`` (correctif D2) : un ``conftest.py`` ajouté au vert
  fait sauter des tests (``collect_ignore``) sans toucher à aucun fichier de test.
- ``test_rouge_racine_sans_parent_ne_plante_pas`` (correctif D2, en plus du brief) : un rouge
  sans parent n'a pas de ``<rouge>^`` ; le repli doit lire les fichiers du rouge sans planter.
  Le dépôt est configuré avec ``log.showRoot=false`` : ``git show`` y rend une liste vide pour
  le commit racine, ce qui cacherait le fichier du rouge ; le repli ne doit pas dépendre de
  cette option.
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

# Un test RSpec : ``spec/`` n'est pas ``tests/`` et le nom ne suit aucun motif de test.
SPEC = "spec/calc_spec.rb"
SPEC_ROUGE = (
    'require "calc"\n'
    "\n"
    'RSpec.describe "somme" do\n'
    '  it "additionne deux nombres" do\n'
    "    expect(somme(2, 3)).to eq(5)\n"
    "  end\n"
    "end\n"
)
SPEC_VERT_SKIP = SPEC_ROUGE.replace(
    "    expect(somme(2, 3)).to eq(5)\n", '    skip "plus tard"\n', 1)

# Un ``conftest.py`` posé au vert : il fait sauter un test sans toucher à aucun fichier de test.
CONFTEST = "conftest.py"
CONFTEST_VERT = 'collect_ignore = ["tests/test_calc.py"]\n'


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

    def _depot(self, amorce=True):
        self._compteur += 1
        depot = self.dossier / f"depot-{self._compteur}"
        depot.mkdir()
        self._git(depot, "init", "-q")
        self._git(depot, "config", "user.email", "test@example.invalid")
        self._git(depot, "config", "user.name", "test")
        self._git(depot, "config", "commit.gpgsign", "false")
        if amorce:
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

    def _jouer(self, depot, rouge, vert, tests=("tests",)):
        argv = [sys.executable, str(SCRIPT), rouge, vert]
        if tests:
            argv += ["--tests", *tests]
        r = subprocess.run(argv, cwd=depot, env=self.env, capture_output=True, text=True)
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

    def test_fichier_du_rouge_hors_des_dossiers_de_test_sort_en_1(self):
        # Attrape : le spec n'est ni sous tests/ ni nommé test_*. Seul le fait qu'il est dans
        # le commit rouge le fait tenir pour un test ; --tests tests ne le couvre pas.
        depot = self._depot()
        rouge = self._commit(depot, {SPEC: SPEC_ROUGE}, "test(demo): étape 5 — rouge (la somme)")
        vert = self._commit(depot, {SPEC: SPEC_VERT_SKIP}, "feat(demo): étape 5 — la somme")
        code, sortie = self._jouer(depot, rouge, vert)
        self.assertEqual(code, 1, sortie)
        self.assertIn(SPEC, sortie)

    def test_chemin_de_tests_avec_dot_slash_est_normalise(self):
        # Attrape : ``--tests ./tests`` ne reconnaissait aucun fichier sous tests/ (sortie 0).
        # Le premier cas passerait aussi par la règle « fichier du rouge » ; le second, un
        # fichier sous tests/ absent du rouge, ne passe que par la normalisation.
        cas = {
            "test du rouge réduit à pass": {TEST: "pass\n"},
            "fixture hors du rouge ajoutée sous tests/": {"tests/dados.json": '{"cas": 1}\n'},
        }
        for nom, fichiers_du_vert in cas.items():
            with self.subTest(cas=nom):
                depot = self._depot()
                rouge = self._rouge(depot)
                vert = self._commit(depot, fichiers_du_vert, "feat(demo): étape 5 — la somme")
                code, sortie = self._jouer(depot, rouge, vert, tests=("./tests",))
                self.assertEqual(code, 1, sortie)
                self.assertIn("tests/", sortie)

    def test_conftest_ajoute_au_vert_sort_en_1(self):
        # Attrape : un conftest.py ajouté au vert fait sauter des tests (collect_ignore) sans
        # qu'aucun fichier de test ne bouge. Le script doit le dire, avec le mot « lanceur ».
        depot = self._depot()
        rouge = self._rouge(depot)
        vert = self._commit(depot, {CONFTEST: CONFTEST_VERT}, "feat(demo): étape 5 — la somme")
        code, sortie = self._jouer(depot, rouge, vert)
        self.assertEqual(code, 1, sortie)
        self.assertIn(CONFTEST, sortie)
        self.assertIn("configuration du lanceur de tests", sortie)

    def test_rouge_racine_sans_parent_ne_plante_pas(self):
        # Attrape : un rouge racine n'a pas de <rouge>^ ; le repli doit tourner, sans Traceback.
        # log.showRoot=false : git show rendrait une liste vide pour ce commit ; le repli
        # ne doit pas dépendre de cette option, sinon le spec du rouge serait invisible.
        depot = self._depot(amorce=False)
        self._git(depot, "config", "log.showRoot", "false")
        rouge = self._commit(depot, {SPEC: SPEC_ROUGE}, "test(demo): étape 5 — rouge (la somme)")
        vert = self._commit(depot, {SPEC: SPEC_VERT_SKIP}, "feat(demo): étape 5 — la somme")
        code, sortie = self._jouer(depot, rouge, vert)
        self.assertEqual(code, 1, sortie)
        self.assertNotIn("Traceback", sortie)
        self.assertIn(SPEC, sortie)


if __name__ == "__main__":
    unittest.main()
