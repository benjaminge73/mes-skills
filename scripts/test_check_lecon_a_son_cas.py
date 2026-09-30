"""Tests de ``check_lecon_a_son_cas.py`` sur un dépôt git fabriqué.

Chaque test construit un vrai dépôt (une base, puis une branche de PR) : la
règle lit des commits et des chemins, pas des chaînes, donc c'est ce qu'on lui
donne à lire. Aucun test ne touche au dépôt réel.
"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_lecon_a_son_cas as lecon  # noqa: E402


class DepotGit(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.ecrire("plugins/p/skills/s/SKILL.md", "---\nname: s\ndescription: d\n---\nv1\n")
        self.ecrire("plugins/p/skills/_partage/x.md", "x v1\n")
        self.ecrire("plugins/p/agents/a.md", "---\nname: a\ndescription: d\n---\nv1\n")
        self.ecrire("plugins/p/hooks/h.json", "{}\n")
        self.ecrire("plugins/q/skills/t/SKILL.md", "---\nname: t\ndescription: d\n---\nv1\n")
        self.ecrire("evals/p/cas-un/case.yaml", "id: cas-un\n")
        self.ecrire("evals/q/cas-q/case.yaml", "id: cas-q\n")
        self.ecrire("docs/notes.md", "v1\n")
        self.commit("base")
        self.git("checkout", "-q", "-b", "pr")

    def git(self, *args):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
        subprocess.run(["git", "-c", "commit.gpgsign=false", *args],
                       cwd=self.racine, check=True, capture_output=True, env=env)

    def ecrire(self, chemin, texte):
        p = self.racine / chemin
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texte, encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def verdict(self):
        return lecon.analyser(self.racine, "main", "HEAD")


class DeclencheurEtCas(DepotGit):
    def test_un_skill_touche_sans_cas_est_refuse_avec_la_marche_a_suivre(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix: un skill")
        v = self.verdict()
        self.assertEqual(len(v.refus), 1)
        self.assertIn("evals/p/", v.refus[0])
        self.assertIn("Eval-cas:", v.refus[0])

    def test_un_skill_touche_avec_un_fichier_de_evals_du_plugin_est_accepte(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.ecrire("evals/p/cas-deux/case.yaml", "id: cas-deux\n")
        self.commit("fix: un skill et son cas")
        self.assertEqual(self.verdict().refus, [])

    def test_le_cas_d_un_autre_plugin_ne_couvre_pas(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.ecrire("evals/q/cas-deux/case.yaml", "id: x\n")
        self.commit("fix")
        self.assertEqual(len(self.verdict().refus), 1)

    def test_eval_cas_vers_un_cas_existant_est_accepte(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix: un skill\n\nEval-cas: cas-un")
        self.assertEqual(self.verdict().refus, [])

    def test_eval_cas_vers_un_cas_inexistant_est_refuse(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix: un skill\n\nEval-cas: cas-fantome")
        v = self.verdict()
        self.assertEqual(len(v.refus), 1)
        self.assertIn("cas-fantome", v.refus[0])

    def test_eval_cas_aucun_avec_raison_est_accepte_et_liste(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix: typo\n\nEval-cas: aucun — faute de frappe, aucun comportement")
        v = self.verdict()
        self.assertEqual(v.refus, [])
        self.assertEqual(len(v.derogations), 1)
        self.assertIn("faute de frappe", v.derogations[0])
        self.assertIn("p", v.derogations[0])

    def test_eval_cas_aucun_sans_raison_est_refuse(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix\n\nEval-cas: aucun")
        self.assertEqual(len(self.verdict().refus), 1)

    def test_la_ligne_peut_etre_dans_n_importe_quel_commit_de_la_pr(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix: un skill\n\nEval-cas: cas-un")
        self.ecrire("docs/notes.md", "v2\n")
        self.commit("docs: autre chose")
        self.assertEqual(self.verdict().refus, [])

    def test_une_pr_sur_docs_seul_n_exige_rien(self):
        self.ecrire("docs/notes.md", "v2\n")
        self.commit("docs: notes")
        v = self.verdict()
        self.assertEqual((v.refus, v.derogations), ([], []))

    def test_agents_hooks_et_partage_declenchent_comme_les_skills(self):
        for chemin in ("plugins/p/agents/a.md", "plugins/p/hooks/h.json",
                       "plugins/p/skills/_partage/x.md"):
            with self.subTest(chemin=chemin):
                self.git("checkout", "-q", "-B", "pr", "main")
                self.ecrire(chemin, "modifié\n")
                self.commit("fix")
                self.assertEqual(len(self.verdict().refus), 1)

    def test_deux_plugins_touches_exigent_un_cas_chacun(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.ecrire("plugins/q/skills/t/SKILL.md", "v2\n")
        self.ecrire("evals/p/cas-deux/case.yaml", "id: x\n")
        self.commit("fix")
        v = self.verdict()
        self.assertEqual(len(v.refus), 1)
        self.assertIn("q", v.refus[0])


class Sortie(DepotGit):
    def test_les_derogations_vont_au_resume_de_l_etape_quand_il_existe(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix\n\nEval-cas: aucun — typo")
        resume = self.racine / "resume.md"
        sortie = io.StringIO()
        ancien = os.environ.get("GITHUB_STEP_SUMMARY")
        os.environ["GITHUB_STEP_SUMMARY"] = str(resume)
        try:
            with contextlib.redirect_stdout(sortie):
                code = lecon.main(["--racine", str(self.racine), "--base", "main"])
        finally:
            if ancien is None:
                os.environ.pop("GITHUB_STEP_SUMMARY", None)
            else:
                os.environ["GITHUB_STEP_SUMMARY"] = ancien
        self.assertEqual(code, 0)
        self.assertIn("typo", sortie.getvalue())
        self.assertIn("typo", resume.read_text(encoding="utf-8"))

    def test_un_refus_donne_le_code_1(self):
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            code = lecon.main(["--racine", str(self.racine), "--base", "main"])
        self.assertEqual(code, 1)

    def test_une_base_illisible_est_une_panne_pas_un_vert(self):
        with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()):
            code = lecon.main(["--racine", str(self.racine), "--base", "origin/inexistante"])
        self.assertEqual(code, 2)
        self.assertIn("origin/inexistante", err.getvalue())


if __name__ == "__main__":
    unittest.main()
