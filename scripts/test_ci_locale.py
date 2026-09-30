"""Tests de ``ci_locale.sh``, la seule liste des contrôles.

Le danger que ces tests ferment : deux listes qui divergent. La CI recopiait
ses commandes, ``CLAUDE.md`` et ``README.md`` en énuméraient d'autres, et un
contrôle ajouté à l'une passait inaperçu des deux autres. Ici on vérifie que
la CI appelle le script, que le script appelle tous les contrôles du dossier,
et que les deux fichiers de doc renvoient au script au lieu d'énumérer.

Aucun test ne joue le script en entier (il rejouerait ces tests).
"""
from __future__ import annotations

import os
import re
import subprocess
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "scripts" / "ci_locale.sh"
CI = RACINE / ".github" / "workflows" / "ci.yml"


def _job(texte: str, nom: str) -> str:
    """Le texte d'un job de ci.yml : de « <nom>: » au job suivant."""
    m = re.search(rf"^  {re.escape(nom)}:\n(.*?)(?=^  [a-z][\w-]*:\n|\Z)", texte,
                  re.MULTILINE | re.DOTALL)
    assert m, f"job {nom} introuvable dans ci.yml"
    return m.group(1)


def _jouer(*args, env=None):
    return subprocess.run(["bash", str(SCRIPT), *args], cwd=RACINE, text=True,
                          capture_output=True, env={**os.environ, **(env or {})})


class ListeUnique(unittest.TestCase):
    def test_le_script_existe_et_sa_syntaxe_est_valide(self):
        self.assertTrue(SCRIPT.is_file(), "scripts/ci_locale.sh est absent")
        verif = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(verif.returncode, 0, verif.stderr)

    def test_le_script_appelle_chaque_controle_du_dossier_scripts(self):
        texte = SCRIPT.read_text(encoding="utf-8")
        controles = sorted(p.name for p in (RACINE / "scripts").glob("check_*.py"))
        controles.append("plugin_version_guard.py")
        self.assertGreaterEqual(len(controles), 3)
        for nom in controles:
            with self.subTest(controle=nom):
                self.assertIn(nom, texte, f"ci_locale.sh n'appelle pas {nom}")

    def test_le_script_joue_les_tests_et_la_validation_par_la_cli(self):
        texte = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("unittest discover -s scripts -p 'test_*.py'", texte)
        self.assertIn("plugin validate", texte)

    def test_le_script_dit_que_le_job_evals_n_y_est_pas(self):
        texte = SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(texte, r"(?i)evals.*(runner|payant)")

    def test_la_ci_appelle_le_script_au_lieu_de_recopier_les_commandes(self):
        ci = CI.read_text(encoding="utf-8")
        for job in ("garde", "validation"):
            with self.subTest(job=job):
                corps = _job(ci, job)
                self.assertIn("scripts/ci_locale.sh", corps)
                self.assertNotRegex(corps, r"python3 scripts/(check_|plugin_version_guard)")
                self.assertNotIn("unittest discover", corps)
                self.assertNotIn("claude plugin validate", corps)

    def test_les_jobs_de_la_ci_qui_ne_relevent_pas_du_script_sont_intacts(self):
        ci = CI.read_text(encoding="utf-8")
        for job in ("evals-portee", "evals", "merge-auto"):
            self.assertRegex(ci, rf"(?m)^  {job}:\n", f"job {job} disparu de ci.yml")
        self.assertIn("needs: [garde, validation, evals-portee, evals]", ci)

    def test_claude_md_et_readme_renvoient_au_script_sans_enumerer(self):
        for nom in ("CLAUDE.md", "README.md"):
            with self.subTest(fichier=nom):
                texte = (RACINE / nom).read_text(encoding="utf-8")
                self.assertIn("scripts/ci_locale.sh", texte)
                self.assertNotRegex(texte, r"(?m)^python3 scripts/check_")
                self.assertNotRegex(texte, r"(?m)^claude plugin validate")

    def test_une_base_illisible_arrete_le_script_avant_tout_controle(self):
        res = _jouer("garde", env={"BASE_REF": "origin/branche-qui-n-existe-pas"})
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("origin/branche-qui-n-existe-pas", res.stdout + res.stderr)

    def test_une_cli_claude_absente_est_dite_clairement(self):
        res = _jouer("validation", env={"CLAUDE_BIN": "claude-introuvable-xyz"})
        self.assertEqual(res.returncode, 3, res.stdout + res.stderr)
        sortie = res.stdout + res.stderr
        self.assertIn("claude-introuvable-xyz", sortie)
        self.assertIn("npm install -g", sortie)

    def test_un_argument_inconnu_est_refuse(self):
        res = _jouer("nimportequoi")
        self.assertEqual(res.returncode, 2)
        self.assertIn("garde", res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
