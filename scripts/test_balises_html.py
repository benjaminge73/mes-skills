"""Tests de ``balises-html.py`` : des balises HTML écrites en texte dans une page Notion.

Cause racine (établie) : le connecteur claude.ai lit et écrit le gras en ``<b>…</b>``
et le code en ``<code>…</code>`` ; la commande ``composio`` (API markdown publique) les
enregistre en texte littéral. Le script contrôle (code 1 si une balise traîne hors code)
et convertit en markdown (``nettoyer``). Chaque test du fichier nomme une panne.

Lancé en vrai sous-processus, sur un fichier temporaire.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "balises-html.py"

# Texte réel d'une page de plan : balises échappées (« \<b\> »), fragmentées, et un lien
# automatique « [x](http://x) » posé à l'intérieur du code.
CAS_REEL = r"\<b\>A (\</b\>\<code\>\<b\>[etapes.md](http://etapes.md)\</b\>\</code\>\<b\>) B\</b\>"
CAS_REEL_CONVERTI = "**A (`etapes.md`) B**"


class BalisesHtml(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), f"script absent : {SCRIPT}")
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        self.dossier = Path(temporaire.name)

    def fichier(self, texte: str) -> Path:
        chemin = self.dossier / "page.md"
        chemin.write_text(texte, encoding="utf-8")
        return chemin

    def jouer(self, commande: str, chemin: Path):
        return subprocess.run([sys.executable, str(SCRIPT), commande, str(chemin)],
                              capture_output=True, text=True, timeout=30)

    def controler(self, texte: str):
        return self.jouer("controler", self.fichier(texte))

    def nettoyer(self, texte: str) -> str:
        r = self.jouer("nettoyer", self.fichier(texte))
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.rstrip("\n")

    def test_un_texte_sans_balise_passe_le_controle(self):
        r = self.controler("Texte **gras**, `code`, et une case :\n- [ ] à faire\n- [x] fait\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_une_balise_brute_hors_code_fait_echouer_le_controle_une_ligne_par_occurrence(self):
        r = self.controler("Avant <b>gras</b> après\n")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 2, r.stdout)

    def test_une_balise_echappee_fait_echouer_le_controle(self):
        r = self.controler(r"Avant \<b\>gras\</b\> après" + "\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_les_cinq_familles_de_balises_sont_reconnues(self):
        for balise in ("<b>x</b>", "<strong>x</strong>", "<i>x</i>", "<em>x</em>", "<code>x</code>"):
            with self.subTest(balise=balise):
                self.assertEqual(self.controler(balise + "\n").returncode, 1)

    def test_une_balise_dans_des_backticks_ou_un_bloc_de_code_n_est_pas_signalee(self):
        texte = "Dans `<b>garde</b>` la ligne.\n\n```\n<code>y</code>\n```\n"
        r = self.controler(texte)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_un_fichier_illisible_rend_le_code_2(self):
        r = self.jouer("controler", self.dossier / "absent.md")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_le_cas_reel_est_detecte_par_le_controle(self):
        self.assertEqual(self.controler(CAS_REEL + "\n").returncode, 1)

    def test_le_cas_reel_est_converti_en_markdown(self):
        self.assertEqual(self.nettoyer(CAS_REEL + "\n"), CAS_REEL_CONVERTI)

    def test_nettoyer_est_idempotent(self):
        premier = self.nettoyer(CAS_REEL + "\nAutre <b>ligne</b> ici\n")
        self.assertEqual(self.nettoyer(premier + "\n"), premier)

    def test_les_espaces_de_bord_sortent_du_gras(self):
        self.assertEqual(self.nettoyer("a<b> texte </b>b\n"), "a **texte** b")

    def test_une_case_et_un_contenu_de_code_restent_intacts(self):
        texte = "- [ ] <b>faire</b>\n- [x] fait\n`<b>garde</b>`\n"
        lignes = self.nettoyer(texte).splitlines()
        self.assertEqual(lignes, ["- [ ] **faire**", "- [x] fait", "`<b>garde</b>`"])


if __name__ == "__main__":
    unittest.main()
