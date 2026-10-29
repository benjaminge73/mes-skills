"""Tests de scripts/garde_doc_pr.py : la ligne `Doc :` d'une description de PR.

Les raisons refusées sont celles relevées sur des PR réelles le 2026-10-28.
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from garde_doc_pr import doc_pas_encore_ecrite, verifier_doc  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "garde_doc_pr.py"
WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
NOTION = "https://app.notion.com/p/0123456789abcdef0123456789abcdef"


class Accepte(unittest.TestCase):
    def test_lien_notion(self):
        self.assertTrue(verifier_doc(f"Résumé\n\nDoc : {NOTION}\n")[0])

    def test_lien_notion_en_gras(self):
        self.assertTrue(verifier_doc(f"**Doc :** {NOTION}")[0])

    def test_sans_objet_avec_raison(self):
        ok, _ = verifier_doc("Doc : sans objet — optimisation interne de la CI, sans effet sur les plugins")
        self.assertTrue(ok)

    def test_sans_objet_lot(self):
        ok, _ = verifier_doc("Doc : sans objet — lot X, entrée consolidée à la fermeture du lot")
        self.assertTrue(ok)

    def test_une_ligne_valide_suffit(self):
        self.assertTrue(verifier_doc(f"Doc :\nDoc : {NOTION}")[0])

    def test_dependabot_sans_corps(self):
        self.assertTrue(verifier_doc(None, "dependabot[bot]")[0])
        self.assertTrue(verifier_doc("", "app/dependabot")[0])


class Refuse(unittest.TestCase):
    def test_aucune_ligne(self):
        ok, raison = verifier_doc("Une PR sans rien.\n\nEvals: aucun — doc")
        self.assertFalse(ok)
        self.assertIn("aucune ligne", raison)

    def test_ligne_vide(self):
        self.assertFalse(verifier_doc("Doc :")[0])

    def test_lien_qui_n_est_pas_notion(self):
        ok, raison = verifier_doc("Doc : https://github.com/o/r/pull/12")
        self.assertFalse(ok)
        self.assertIn("pas un lien Notion", raison)

    def test_sans_objet_sans_raison(self):
        self.assertFalse(verifier_doc("Doc : sans objet")[0])

    def test_raison_trop_courte(self):
        self.assertFalse(verifier_doc("Doc : sans objet — doc")[0])

    def test_raisons_relevees(self):
        for raison in [
            "changement de style, la page projet Notion n'a pas été consultée.",
            "dépôt sans Changelog de projet (pas de job `doc` dans la CI).",
            "pas de Changelog applicable à ce dépôt (aucun job `doc` dans la CI).",
            "réglage de la watchlist documenté dans docs/watchlist.md, README et .env.example",
            "entrée à venir",
        ]:
            with self.subTest(raison=raison):
                ok, message = verifier_doc(f"Doc : sans objet — {raison}")
                self.assertFalse(ok)
                self.assertIn("raison refusée", message)

    def test_auteur_humain_controle(self):
        self.assertFalse(verifier_doc("", "benjaminge73")[0])


class Cli(unittest.TestCase):
    def jouer(self, env):
        base = {k: v for k, v in os.environ.items() if k not in ("PR_BODY", "PR_AUTHOR")}
        return subprocess.run([sys.executable, str(SCRIPT)], env={**base, **env},
                              capture_output=True, text=True)

    def test_codes(self):
        self.assertEqual(self.jouer({"PR_BODY": f"Doc : {NOTION}"}).returncode, 0)
        refus = self.jouer({"PR_BODY": "Doc : sans objet"})
        self.assertEqual(refus.returncode, 1)
        self.assertIn("::error", refus.stdout)
        # rien d'écrit encore : code 4, distinct d'une valeur fausse
        self.assertEqual(self.jouer({"PR_BODY": "rien"}).returncode, 4)
        self.assertEqual(self.jouer({}).returncode, 2)
        self.assertEqual(self.jouer({"PR_AUTHOR": "dependabot[bot]"}).returncode, 0)



class PasEncoreEcrite(unittest.TestCase):
    """Une PR qui vient de s'ouvrir n'a pas encore sa ligne : code 4, distinct du refus d'une valeur fausse."""

    def test_ligne_absente_ou_vide_attend(self):
        self.assertTrue(doc_pas_encore_ecrite("Une PR sans rien."))
        self.assertTrue(doc_pas_encore_ecrite("Doc :"))
        self.assertTrue(doc_pas_encore_ecrite("Doc : \n\n**Doc :** "))
        self.assertTrue(doc_pas_encore_ecrite(None))

    def test_une_valeur_fausse_n_attend_pas(self):
        # elle est fausse, pas absente : refusée tout de suite
        self.assertFalse(doc_pas_encore_ecrite("Doc : sans objet"))
        self.assertFalse(doc_pas_encore_ecrite("Doc : https://github.com/o/r/pull/12"))
        self.assertFalse(doc_pas_encore_ecrite("Doc : sans objet — pas de job doc dans la CI"))

    def test_une_ligne_valide_n_attend_pas(self):
        self.assertFalse(doc_pas_encore_ecrite(f"Doc : {NOTION}"))

    def test_dependabot_n_attend_pas(self):
        self.assertFalse(doc_pas_encore_ecrite("", "dependabot[bot]"))

    def test_code_de_sortie(self):
        def lancer(corps):
            env = {**os.environ, "PR_BODY": corps, "PR_AUTHOR": "benjaminge73"}
            return subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True).returncode
        self.assertEqual(lancer("Doc :"), 4)
        self.assertEqual(lancer("Doc : sans objet"), 1)
        self.assertEqual(lancer(f"Doc : {NOTION}"), 0)


class PasDAttenteSurRunner(unittest.TestCase):
    """Le job `doc` lit le corps une fois : plus de relecture toutes les 20 s pendant 10 min
    sur un runner facturé (2026-10-29). C'est doc-relance.yml qui le relance sur `edited`."""

    def test_le_job_doc_n_attend_pas(self):
        ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        job = ci.split("\n  doc:\n", 1)[1].split("\n  merge-auto:\n", 1)[0]
        self.assertRegex(job, r"(?m)^    timeout-minutes: [12]$")
        self.assertRegex(job, r"(?m)^    needs: validation$")
        for attente in ("sleep", "while ", "SECONDS"):
            self.assertNotIn(attente, job)

    def test_doc_relance_vise_le_job_doc(self):
        relance = (WORKFLOWS / "doc-relance.yml").read_text(encoding="utf-8")
        self.assertIn("types: [edited]", relance)
        self.assertIn("github.event.changes.body != null", relance)
        self.assertIn('select(.name == "Ligne Doc de la description")', relance)
        self.assertIn("gh run rerun --job", relance)
        self.assertNotIn("--failed", relance)


if __name__ == "__main__":
    unittest.main()
