"""Tests de ``compter-cases.py`` sur une page figée.

La fixture ``fixtures_plans/questions_ouvertes.md`` est la section « Questions
ouvertes » d'une vraie sortie ``notion-fetch`` (le plan « Évals sobres et machine
partagée »). Le compte attendu est fait à la main, relu sur la fixture : une case
cochée par question, sauf Q9 qui en a deux (« Deux jetons lourds » et
« Autre / complément »). Le script doit rendre ce compte, et signaler une case
cochée en plus quand on le compare à un relevé plus ancien.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "compter-cases.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures_plans" / "questions_ouvertes.md"

ATTENDU = {f"Q{n}": 1 for n in range(1, 15)}
ATTENDU["Q9"] = 2


def jouer(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class CompterCases(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def _releve(self, contenu):
        f = self.dossier / "releve.json"
        f.write_text(json.dumps(contenu))
        return f

    def test_sans_releve_imprime_le_compte_de_la_fixture(self):
        code, sortie, erreur = jouer(FIXTURE)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sortie), ATTENDU)
        self.assertIn("total : 15", erreur)

    def test_la_sortie_standard_redirigee_sert_de_releve_au_recompte(self):
        # Le geste du SKILL : `compter-cases.py page.md > releve.json`, puis
        # `--releve releve.json`. Une ligne « total : n » dans le fichier le
        # rendait illisible (code 2) et le recompte ne comparait jamais rien.
        _, sortie, _ = jouer(FIXTURE)
        releve = self.dossier / "releve.json"
        releve.write_text(sortie)
        code, sortie2, erreur = jouer(FIXTURE, "--releve", releve)
        self.assertEqual(code, 0, erreur + sortie2)

    def test_releve_identique_rend_zero(self):
        code, sortie, _ = jouer(FIXTURE, "--releve", self._releve(ATTENDU))
        self.assertEqual(code, 0, sortie)

    def test_une_case_en_plus_est_signalee_pour_la_bonne_question(self):
        page = self.dossier / "page.md"
        texte = FIXTURE.read_text()
        # Cocher une seconde case dans Q3 : la première option non cochée suivant son titre.
        debut = texte.index("### ✅ Q3")
        coche = texte.index("- [ ]", debut)
        page.write_text(texte[:coche] + "- [x]" + texte[coche + len("- [ ]"):])
        code, sortie, _ = jouer(page, "--releve", self._releve(ATTENDU))
        self.assertEqual(code, 1, sortie)
        lignes = [l for l in sortie.splitlines() if l.strip()]
        self.assertEqual(len(lignes), 1, sortie)
        self.assertIn("Q3", lignes[0])
        self.assertIn("2 cochées, relevé 1", lignes[0])
        self.assertIn("une case en plus", lignes[0])

    def test_les_cases_hors_questions_ouvertes_ne_comptent_pas(self):
        page = self.dossier / "page.md"
        page.write_text("## Cartes\n- [x] une tâche\n\n" + FIXTURE.read_text()
                        + "- [x] hors section\n")
        code, sortie, _ = jouer(page, "--releve", self._releve(ATTENDU))
        self.assertEqual(code, 0, sortie)


if __name__ == "__main__":
    unittest.main()
