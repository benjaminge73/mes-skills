"""Tests de ``statut-maitre.py`` : le statut hérité d'un plan maître, une règle nommée, un test."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "statut-maitre.py"


def jouer(*statuts):
    r = subprocess.run([sys.executable, str(SCRIPT), *statuts], capture_output=True, text=True)
    sortie = dict(l.split("=", 1) for l in r.stdout.splitlines())
    return r.returncode, sortie, r.stderr


class StatutMaitre(unittest.TestCase):
    def test_un_plan_en_cours_rend_le_maitre_en_cours_meme_si_un_autre_n_a_pas_demarre(self):
        # Le « moins avancé » strict ferait reculer le maître à valide quand on ajoute un plan.
        for lot in (("en cours", "valide"), ("en cours", "pret"), ("en cours", "brouillon", "execute")):
            with self.subTest(lot=lot):
                code, sortie, _ = jouer(*lot)
                self.assertEqual(code, 0)
                self.assertEqual(sortie["statut"], "en cours")
                self.assertEqual(sortie["lot"], "ouvert")

    def test_sans_plan_en_cours_le_maitre_prend_le_moins_avance(self):
        cas = {("valide", "pret"): "valide", ("pret", "pret"): "pret",
               ("a merger", "valide"): "valide", ("execute", "a merger"): "a merger",
               ("brouillon", "en revue"): "brouillon"}
        for lot, attendu in cas.items():
            with self.subTest(lot=lot):
                self.assertEqual(jouer(*lot)[1]["statut"], attendu)

    def test_le_lot_est_ferme_quand_tous_les_plans_sont_au_moins_a_merger(self):
        for lot, statut in ((("a merger", "a merger"), "a merger"), (("a merger", "execute"), "a merger"),
                            (("execute", "execute"), "execute")):
            with self.subTest(lot=lot):
                _, sortie, _ = jouer(*lot)
                self.assertEqual((sortie["statut"], sortie["lot"]), (statut, "ferme"))

    def test_un_lot_non_ferme_accepte_des_plans(self):
        for lot in (("valide", "valide"), ("pret", "a merger"), ("en cours", "execute")):
            with self.subTest(lot=lot):
                self.assertEqual(jouer(*lot)[1]["lot"], "ouvert")

    def test_archive_ne_compte_pas(self):
        self.assertEqual(jouer("archive", "en cours", "execute")[1]["statut"], "en cours")
        self.assertEqual(jouer("archive", "execute", "execute")[1], {"statut": "execute", "lot": "ferme"})
        self.assertEqual(jouer("archive", "archive")[1], {"statut": "archive", "lot": "ferme"})

    def test_un_plan_seul_ne_fait_pas_un_maitre(self):
        code, _, erreur = jouer("en cours")
        self.assertEqual(code, 2)
        self.assertIn("au moins deux plans", erreur)
        self.assertEqual(jouer()[0], 2)

    def test_une_valeur_inconnue_ou_accentuee_est_refusee(self):
        for valeur in ("prêt", "exécuté", "fini", "En cours"):
            with self.subTest(valeur=valeur):
                code, _, erreur = jouer("valide", valeur)
                self.assertEqual(code, 2)
                self.assertIn(valeur, erreur)


if __name__ == "__main__":
    unittest.main()
