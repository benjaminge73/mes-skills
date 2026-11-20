"""Tests de ``fraicheur-depot.py`` : un cas délicat, un test.

Chaque test monte un « distant » nu et un clone dans un dossier temporaire ; le script
tourne en sous-processus (le contrat testé est son code retour et sa sortie).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "fraicheur-depot.py"
ENV = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def git(d, *a):
    r = subprocess.run(["git", *ENV, "-C", str(d), *a], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def commit(d, nom, texte="x\n"):
    (Path(d) / nom).write_text(texte)
    git(d, "add", nom)
    git(d, "commit", "-qm", nom)


def lancer(d, *args):
    r = subprocess.run([sys.executable, str(SCRIPT), "--depot", str(d), *args], capture_output=True, text=True)
    return r.returncode, r.stdout


class Fraicheur(unittest.TestCase):
    def monter(self, principale="main"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        t = Path(tmp.name)
        git(t, "init", "-q", "--bare", "-b", principale, "distant")
        git(t, "clone", "-q", "distant", "local")
        local, autre = t / "local", t / "autre"
        git(local, "checkout", "-q", "-B", principale)
        commit(local, "a.txt")
        git(local, "push", "-q", "-u", "origin", principale)
        git(t, "clone", "-q", "distant", "autre")
        return t, local, autre, principale

    def test_a_jour(self):
        _, local, _, _ = self.monter()
        self.assertEqual(lancer(local)[0], 0)

    def test_en_retard_sans_appliquer_ne_change_rien(self):
        _, local, autre, b = self.monter()
        commit(autre, "b.txt"); git(autre, "push", "-q", "origin", b)
        avant = git(local, "rev-parse", "HEAD")
        code, sortie = lancer(local)
        self.assertEqual(code, 1, sortie)
        self.assertEqual(git(local, "rev-parse", "HEAD"), avant)

    def test_master_detecte_et_fast_forward(self):
        _, local, autre, b = self.monter("master")
        commit(autre, "b.txt"); git(autre, "push", "-q", "origin", b)
        code, sortie = lancer(local, "--appliquer")
        self.assertEqual(code, 0, sortie)
        self.assertIn("origin/master", sortie)
        self.assertTrue((local / "b.txt").exists())

    def test_branche_de_travail_rebasee(self):
        _, local, autre, b = self.monter()
        git(local, "checkout", "-q", "-b", "feat/x"); commit(local, "f.txt")
        commit(autre, "b.txt"); git(autre, "push", "-q", "origin", b)
        code, sortie = lancer(local, "--appliquer")
        self.assertEqual(code, 0, sortie)
        self.assertTrue((local / "b.txt").exists() and (local / "f.txt").exists())
        self.assertNotIn("force-with-lease", sortie)  # pas encore poussée

    def test_branche_deja_poussee_propose_force_with_lease(self):
        _, local, autre, b = self.monter()
        git(local, "checkout", "-q", "-b", "feat/x"); commit(local, "f.txt")
        git(local, "push", "-q", "-u", "origin", "feat/x")
        commit(autre, "b.txt"); git(autre, "push", "-q", "origin", b)
        code, sortie = lancer(local, "--appliquer")
        self.assertEqual(code, 0, sortie)
        self.assertIn("--force-with-lease", sortie)

    def test_modifications_non_commitees_arretent(self):
        _, local, autre, b = self.monter()
        commit(autre, "b.txt"); git(autre, "push", "-q", "origin", b)
        (local / "a.txt").write_text("modifié\n")
        avant = git(local, "rev-parse", "HEAD")
        code, sortie = lancer(local, "--appliquer")
        self.assertEqual(code, 3, sortie)
        self.assertEqual(git(local, "rev-parse", "HEAD"), avant)
        self.assertEqual((local / "a.txt").read_text(), "modifié\n")

    def test_conflit_de_rebase_abandonne_et_dit_les_fichiers(self):
        _, local, autre, b = self.monter()
        git(local, "checkout", "-q", "-b", "feat/x"); commit(local, "a.txt", "ma version\n")
        commit(autre, "a.txt", "leur version\n"); git(autre, "push", "-q", "origin", b)
        avant = git(local, "rev-parse", "HEAD")
        code, sortie = lancer(local, "--appliquer")
        self.assertEqual(code, 3, sortie)
        self.assertIn("a.txt", sortie)
        self.assertEqual(git(local, "rev-parse", "HEAD"), avant)
        self.assertEqual(git(local, "status", "--porcelain"), "")

    def test_sans_reseau_dit_que_la_fraicheur_nest_pas_verifiee(self):
        t, local, _, _ = self.monter()
        git(local, "remote", "set-url", "origin", str(t / "disparu"))
        code, sortie = lancer(local, "--appliquer")
        self.assertEqual(code, 4, sortie)
        self.assertIn("NON vérifiée", sortie)

    def test_pas_un_depot(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(lancer(d)[0], 2)


if __name__ == "__main__":
    unittest.main()
