"""Tests de ``perimetre-etape.py`` : l'étape n'a touché que les fichiers de sa liste fermée.

Le script (``plugins/plans-notion/skills/_partage/scripts/``) compare ``git diff --name-only``
entre le SHA d'avant l'étape et ``HEAD`` à la liste des fichiers du brief. Un fichier touché
hors de la liste : code 1, le fichier sur la sortie standard. Tout conforme : code 0. Base
inconnue : code 2, distinct, pour qu'une faute de frappe sur le SHA ne passe pas pour un
périmètre respecté.

Les tests montent de vrais dépôts git jetables (pas de mock) dans un dossier temporaire, avec
un HOME isolé : aucun ne touche le dépôt de travail ni la config git du poste.

Pannes attrapées :
- ``test_fichier_hors_liste_sort_en_1`` : l'exécutant a touché ``docs/notes.md``, hors du brief.
  C'est la dérive même que le contrôle existe pour voir. La liste passe ici en options répétées
  (``--fichiers a --fichiers b``), et chacun des deux fichiers listés est touché : si une
  option est perdue (argparse ``store``, ou seule la première lue), le fichier correspondant
  sort hors liste et le test échoue. Si l'analyse de la liste casse, le script sort en 2.
- ``test_diff_conforme_sort_en_0`` : le cas légitime. Un script qui sort en 1 sur tout diff
  ferait un faux rouge à chaque retour conforme. La liste passe ici séparée par des virgules.
- ``test_base_inconnue_sort_en_2`` : un SHA qui n'existe pas rend un code distinct et nomme le
  SHA. Sans cela, une base fausse ressemblerait à un périmètre respecté (0) ou à une dérive (1).
- ``test_renommage_depuis_un_fichier_hors_liste_sort_en_1`` (en plus du budget du brief) : un
  fichier hors liste renommé vers un fichier listé. Avec la détection des renommages de git,
  ``--name-only`` ne rend que le nouveau nom, qui est listé : le script sortirait en 0 alors
  que l'ancien chemin a été touché. ``--no-renames`` rend les deux chemins.
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
          / "perimetre-etape.py")
SHA_INCONNU = "0" * 40
CODE = "def somme(a, b):\n    return a + b\n"
TEST = "def test_somme():\n    assert somme(1, 2) == 3\n"
# Assez de texte pour que la détection de renommage de git le reconnaisse sans hésiter.
NOTES = "Une page de notes, assez longue pour que la détection de renommage la reconnaisse.\n" * 3


class PerimetreEtape(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        racine = Path(tmp.name)
        (racine / "home").mkdir()
        self.depot = racine / "depot"
        self.depot.mkdir()
        self.env = {
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(racine / "home"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_AUTHOR_NAME": "essai",
            "GIT_AUTHOR_EMAIL": "essai@exemple.invalid",
            "GIT_COMMITTER_NAME": "essai",
            "GIT_COMMITTER_EMAIL": "essai@exemple.invalid",
        }
        self._git("init", "-q")
        self.base = self._commit("base", {"src/calc.py": CODE})

    def _git(self, *args: str) -> str:
        r = subprocess.run(["git", *args], cwd=self.depot, env=self.env,
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def _commit(self, message: str, fichiers: dict[str, str]) -> str:
        for chemin, contenu in fichiers.items():
            cible = self.depot / chemin
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_text(contenu, encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _lancer(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.depot,
                              env=self.env, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=60)

    def test_fichier_hors_liste_sort_en_1(self) -> None:
        self._commit("étape", {"src/calc.py": CODE + "# ajout\n", "tests/test_calc.py": TEST,
                               "docs/notes.md": NOTES})
        r = self._lancer("--base", self.base,
                         "--fichiers", "src/calc.py", "--fichiers", "tests/test_calc.py")
        self.assertEqual(r.returncode, 1, msg=r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["docs/notes.md"])

    def test_diff_conforme_sort_en_0(self) -> None:
        self._commit("étape", {"src/calc.py": CODE + "# ajout\n", "tests/test_calc.py": TEST})
        r = self._lancer("--base", self.base, "--fichiers", "src/calc.py,tests/test_calc.py")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(r.stdout, "")

    def test_base_inconnue_sort_en_2(self) -> None:
        self._commit("étape", {"src/calc.py": CODE + "# ajout\n"})
        r = self._lancer("--base", SHA_INCONNU, "--fichiers", "src/calc.py")
        self.assertEqual(r.returncode, 2, msg=r.stdout)
        self.assertIn(SHA_INCONNU, r.stderr)

    def test_renommage_depuis_un_fichier_hors_liste_sort_en_1(self) -> None:
        ancien = self._commit("notes", {"docs/ancien.md": NOTES})
        self._git("mv", "docs/ancien.md", "src/nouveau.py")
        self._commit("étape", {})
        r = self._lancer("--base", ancien, "--fichiers", "src/nouveau.py")
        self.assertEqual(r.returncode, 1, msg=r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["docs/ancien.md"])


if __name__ == "__main__":
    unittest.main()
