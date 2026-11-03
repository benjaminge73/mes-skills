"""Tests de ``verifier-ligne-doc.py`` : jouer en local la garde du job `doc` avant `gh pr ready`.

Chaque test pose un faux dépôt dans un dossier temporaire, avec une garde jouet au contrat de
``ci.yml`` (corps dans PR_BODY, auteur dans PR_AUTHOR), et compare le code rendu. La vraie garde
de ce dépôt est jouée aussi, sur le repli que la règle prescrit et sur une ligne vide.

Pannes, une par test :
  1. Le script rend le code de la garde (0, 1, 4), sans le réinterpréter.
  2. La garde reçoit le corps du fichier et l'auteur, comme dans la CI.
  3. Un dépôt sans garde rend 3 (pas 0 : ce n'est pas un feu vert sur la doc).
  4. La garde Node (``scripts/garde-doc-pr.mjs``, vahiny) est trouvée et jouée par node.
  5. Un fichier de corps absent rend 2 (panne), pas 1 (refus).
  6. La clôture appelle le script avant `gh pr ready`.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/plans-notion/skills/_partage/scripts/verifier-ligne-doc.py"

GARDE_JOUET = """import os, sys
corps = os.environ["PR_BODY"]
print("auteur=" + os.environ["PR_AUTHOR"])
sys.exit(0 if "Doc : ok" in corps else 4 if "Doc :" == corps.strip() else 1)
"""


def jouer(depot: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), "--depot", str(depot), *args],
                          capture_output=True, text=True)


class FauxDepot(unittest.TestCase):
    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dossier)
        (self.dossier / "scripts").mkdir()

    def corps(self, texte: str) -> str:
        chemin = self.dossier / "corps.md"
        chemin.write_text(texte, encoding="utf-8")
        return str(chemin)

    def test_rend_le_code_de_la_garde(self):
        (self.dossier / "scripts/garde_doc_pr.py").write_text(GARDE_JOUET, encoding="utf-8")
        self.assertEqual(jouer(self.dossier, "--corps", self.corps("Doc : ok")).returncode, 0)
        self.assertEqual(jouer(self.dossier, "--corps", self.corps("Doc : à venir")).returncode, 1)
        self.assertEqual(jouer(self.dossier, "--corps", self.corps("Doc :")).returncode, 4)

    def test_la_garde_recoit_l_auteur(self):
        (self.dossier / "scripts/garde_doc_pr.py").write_text(GARDE_JOUET, encoding="utf-8")
        r = jouer(self.dossier, "--corps", self.corps("Doc : ok"), "--auteur", "quelquun")
        self.assertIn("auteur=quelquun", r.stdout)

    def test_sans_garde_rend_3(self):
        r = jouer(self.dossier, "--corps", self.corps("Doc : ok"))
        self.assertEqual(r.returncode, 3)
        self.assertIn("aucune garde", r.stdout)

    @unittest.skipIf(shutil.which("node") is None, "node absent")
    def test_garde_node(self):
        (self.dossier / "scripts/garde-doc-pr.mjs").write_text(
            "process.exit(process.env.PR_BODY.includes('Doc : ok') ? 0 : 1);\n", encoding="utf-8")
        self.assertEqual(jouer(self.dossier, "--corps", self.corps("Doc : ok")).returncode, 0)
        self.assertEqual(jouer(self.dossier, "--corps", self.corps("Doc : non")).returncode, 1)

    def test_corps_absent_est_une_panne(self):
        (self.dossier / "scripts/garde_doc_pr.py").write_text(GARDE_JOUET, encoding="utf-8")
        self.assertEqual(jouer(self.dossier, "--corps", str(self.dossier / "absent.md")).returncode, 2)


class VraieGarde(unittest.TestCase):
    """La garde de ce dépôt, jouée par le script, sur les deux cas du relevé du 2026-11-03."""

    def jouer_corps(self, texte: str) -> int:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(texte)
        self.addCleanup(Path(f.name).unlink)
        return jouer(ROOT, "--corps", f.name).returncode

    def test_repli_prescrit_accepte(self):
        self.assertEqual(self.jouer_corps(
            "Doc : https://app.notion.com/p/402b8cc8aa1d81a2adb3c7cf862d78cd — entrée « 2026-11-03 · X (PR #1) »"), 0)

    def test_ligne_vide_refusee(self):
        self.assertEqual(self.jouer_corps("Résumé\n\nDoc :\n"), 4)


class Cablage(unittest.TestCase):
    def test_la_cloture_joue_le_script_avant_gh_pr_ready(self):
        cloture = " ".join((ROOT / "plugins/plans-notion/skills/executer-plan-notion/cloture.md")
                           .read_text(encoding="utf-8").split())
        self.assertIn("verifier-ligne-doc.py", cloture)
        self.assertLess(cloture.index("verifier-ligne-doc.py"), cloture.index("gh pr ready <n>"))


if __name__ == "__main__":
    unittest.main()
