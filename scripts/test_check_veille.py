"""Tests de ``check_veille.py`` : refuser une PR de skill quand la dernière
passe de veille est trop vieille.

Le dépôt est fabriqué (une base, puis une branche de PR) et la date de
référence est injectée : aucun test ne dépend du jour où il tourne.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_veille  # noqa: E402

RACINE_REELLE = Path(__file__).resolve().parents[1]


def journal(*dates: str) -> str:
    entrees = "".join(f"\n### {d} — passe\n\nSources lues : x.\n" for d in dates)
    return ("# La veille\n\n## 1. Les sources\n\nx\n\n## 2. Les faits porteurs\n\nx\n\n"
            f"## 3. Le journal des passes\n{entrees}")


class DepotVeille(unittest.TestCase):
    AUJOURDHUI = date(2026, 9, 30)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v1\n")
        self.ecrire("plugins/p/skills/_partage/x.md", "v1\n")
        self.ecrire("plugins/p/agents/a.md", "v1\n")
        self.ecrire("plugins/p/hooks/h.json", "{}\n")
        self.ecrire("docs/notes.md", "v1\n")
        self.ecrire("scripts/limites.json", json.dumps({"veille_jours_max": 30}))
        self.ecrire("docs/veille.md", journal("2026-09-30"))
        self.commit("base")
        self.git("checkout", "-q", "-b", "pr")

    def git(self, *args):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
        subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=self.racine,
                       check=True, capture_output=True, env=env)

    def ecrire(self, chemin, texte):
        p = self.racine / chemin
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texte, encoding="utf-8")

    def commit(self, message="c"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def journal_de(self, *dates):
        self.ecrire("docs/veille.md", journal(*dates))

    def verdict(self, seuil=30):
        return check_veille.analyser(self.racine, "main", "HEAD", self.AUJOURDHUI, seuil)


class SeuilDe30Jours(DepotVeille):
    def test_un_journal_de_31_jours_et_une_pr_de_skill_est_refuse(self):
        self.journal_de("2026-08-30")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        v = self.verdict()
        self.assertEqual(len(v.refus), 1)
        self.assertIn("31 jours", v.refus[0])
        self.assertIn("docs/veille.md", v.refus[0])
        self.assertIn("chercheur", v.refus[0])

    def test_un_journal_de_29_jours_est_accepte(self):
        self.journal_de("2026-09-01")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        self.assertEqual(self.verdict().refus, [])

    def test_exactement_30_jours_est_accepte_seul_le_dela_est_refuse(self):
        self.journal_de("2026-08-31")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        self.assertEqual(self.verdict().refus, [])

    def test_une_pr_sur_docs_seul_n_exige_rien_meme_avec_un_journal_perime(self):
        self.journal_de("2026-01-01")
        self.ecrire("docs/notes.md", "v2\n")
        self.commit("docs")
        self.assertEqual(self.verdict().refus, [])

    def test_c_est_l_entree_la_plus_recente_qui_compte_pas_la_derniere_ligne(self):
        self.journal_de("2026-09-25", "2026-01-01")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        self.assertEqual(self.verdict().refus, [])

    def test_une_pr_qui_ajoute_l_entree_du_jour_passe(self):
        self.journal_de("2026-01-01")
        self.commit("journal ancien")
        self.git("checkout", "-q", "-B", "pr2", "HEAD")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.journal_de("2026-01-01", "2026-09-30")
        self.commit("fix + passe")
        v = check_veille.analyser(self.racine, "main", "HEAD", self.AUJOURDHUI, 30)
        self.assertEqual(v.refus, [])

    def test_un_journal_sans_aucune_entree_datee_est_refuse(self):
        self.ecrire("docs/veille.md", "# La veille\n\n## 3. Le journal des passes\n\nrien\n")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        self.assertEqual(len(self.verdict().refus), 1)

    def test_un_fichier_de_veille_absent_est_refuse(self):
        (self.racine / "docs/veille.md").unlink()
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        self.assertEqual(len(self.verdict().refus), 1)

    def test_agents_hooks_et_partage_declenchent_comme_les_skills(self):
        self.journal_de("2026-08-01")
        self.commit("journal ancien")
        for chemin in ("plugins/p/agents/a.md", "plugins/p/hooks/h.json",
                       "plugins/p/skills/_partage/x.md"):
            with self.subTest(chemin=chemin):
                self.git("checkout", "-q", "-B", "pr3", "main")
                self.journal_de("2026-08-01")
                self.ecrire(chemin, "modifié\n")
                self.commit("fix")
                self.assertEqual(len(self.verdict().refus), 1)

    def test_le_seuil_vient_de_l_argument_donc_de_limites_json(self):
        self.journal_de("2026-09-20")
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")
        self.assertEqual(self.verdict(seuil=30).refus, [])
        self.assertEqual(len(self.verdict(seuil=9).refus), 1)


class Programme(DepotVeille):
    def lancer(self, *args, env=None):
        sortie, erreur = io.StringIO(), io.StringIO()
        ancien = {k: os.environ.get(k) for k in (env or {})}
        os.environ.update(env or {})
        try:
            with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
                code = check_veille.main(["--racine", str(self.racine), "--base", "main", *args])
        finally:
            for k, v in ancien.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        return code, sortie.getvalue(), erreur.getvalue()

    def pr_de_skill_avec_journal(self, jour):
        self.journal_de(jour)
        self.ecrire("plugins/p/skills/s/SKILL.md", "v2\n")
        self.commit("fix")

    def test_la_date_de_reference_est_un_argument(self):
        self.pr_de_skill_avec_journal("2026-08-30")
        code, _, erreur = self.lancer("--aujourdhui", "2026-09-30")
        self.assertEqual(code, 1, erreur)
        code, _, erreur = self.lancer("--aujourdhui", "2026-09-29")
        self.assertEqual(code, 0, erreur)

    def test_la_date_de_reference_peut_venir_d_une_variable(self):
        self.pr_de_skill_avec_journal("2026-08-30")
        code, _, _ = self.lancer(env={"VEILLE_AUJOURDHUI": "2026-09-30"})
        self.assertEqual(code, 1)

    def test_le_seuil_est_lu_dans_limites_json(self):
        self.pr_de_skill_avec_journal("2026-09-20")
        self.ecrire("scripts/limites.json", json.dumps({"veille_jours_max": 5}))
        self.commit("seuil")
        code, _, _ = self.lancer("--aujourdhui", "2026-09-30")
        self.assertEqual(code, 1)

    def test_une_base_illisible_est_une_panne_pas_un_vert(self):
        sortie = io.StringIO()
        with contextlib.redirect_stderr(sortie), contextlib.redirect_stdout(io.StringIO()):
            code = check_veille.main(["--racine", str(self.racine), "--base", "origin/absente",
                                      "--aujourdhui", "2026-09-30"])
        self.assertEqual(code, 2)
        self.assertIn("origin/absente", sortie.getvalue())


class DansLeDepotReel(unittest.TestCase):
    def test_ci_locale_appelle_check_veille(self):
        texte = (RACINE_REELLE / "scripts" / "ci_locale.sh").read_text(encoding="utf-8")
        self.assertIn("check_veille.py", texte)

    def test_le_registre_dit_la_veille_en_place(self):
        registre = (RACINE_REELLE / "docs" / "garde-fous.md").read_text(encoding="utf-8")
        lignes = [l for l in registre.splitlines() if l.startswith("| Veille")]
        self.assertEqual(len(lignes), 1)
        self.assertIn("`scripts/check_veille.py`", lignes[0])
        self.assertIn("`veille.yml`", lignes[0])
        self.assertTrue(lignes[0].rstrip(" |").endswith("en place"), lignes[0])

    def test_le_journal_reel_porte_la_premiere_passe_du_2026_09_30(self):
        texte = (RACINE_REELLE / "docs" / "veille.md").read_text(encoding="utf-8")
        self.assertIn(date(2026, 9, 30), check_veille.dates_du_journal(texte))

    def test_la_regle_de_veille_est_dite_dans_les_trois_documents(self):
        for nom in ("CLAUDE.md", "docs/tester-un-skill.md"):
            with self.subTest(fichier=nom):
                texte = (RACINE_REELLE / nom).read_text(encoding="utf-8")
                self.assertIn("docs/veille.md", texte)
                self.assertIn("chercheur", texte)
        gabarit = (RACINE_REELLE / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
        self.assertIn("veille", gabarit.lower())

    def test_le_seuil_de_limites_json_est_de_30_jours(self):
        limites = json.loads((RACINE_REELLE / "scripts" / "limites.json").read_text(encoding="utf-8"))
        self.assertEqual(limites["veille_jours_max"], 30)


if __name__ == "__main__":
    unittest.main()
