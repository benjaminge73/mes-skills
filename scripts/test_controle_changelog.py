"""Tests de ``controle-changelog.py`` sur des entrées écrites ici, à la main.

Chaque test pose une entrée dans un dossier temporaire, joue le script comme le
ferait la clôture, et compare le code de retour à celui du brief et la sortie au
défaut nommé. Le contrat testé est celui de la forme (quatre rubriques dans
l'ordre, une source sur chaque ligne de ✨ Nouveau et 🔧 Amélioré, une date dans
l'en-tête), pas le texte des rubriques.

Pannes, une par test :
  1. « Reste à faire » absent : rend 1 et nomme la rubrique.
  2. Une ligne de « Nouveau » sans source : rend 1 et nomme la ligne.
  3. Une rubrique vide, sans « rien » : rend 1 et nomme la rubrique.
  4. Les rubriques dans le désordre : rend 1 et le dit.
  5. Une entrée conforme rend 0 ; une page sans section « Récap » rend 2.
Un test de plus (7) : un en-tête sans date rend 1. La panne 5 ne la couvre pas,
et une date absente passe inaperçue dans une page longue.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "controle-changelog.py"

ENTETE = "## Récap — plan « Exemple » — 2026-10-20\n\nPR : #12 — statut : prête\n\n"

BLOCS = {
    "nouveau": "### ✨ Nouveau\n- Le pilote écrit le récap à chaque clôture (preuve : étape 2)\n\n",
    "ameliore": "### 🔧 Amélioré\n- Le compte rendu du chat garde ses lignes techniques (Étape 4)\n\n",
    "corrige": "### 🐛 Corrigé\nrien\n\n",
    "reste": "### ⏭️ Reste à faire\n- Brancher le contrôle sur la clôture (Étape 5)\n\n",
}
DETAILS = "<details>\n<summary>Côté technique</summary>\n\nDétail technique.\n</details>\n"
ORDRE = ("nouveau", "ameliore", "corrige", "reste")


def entree(ordre=ORDRE, blocs=None, entete=ENTETE):
    corps = {**BLOCS, **(blocs or {})}
    return entete + "".join(corps[c] for c in ordre) + DETAILS


def jouer(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class ControleChangelog(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def _entree(self, texte):
        f = self.dossier / "entree.md"
        f.write_text(texte, encoding="utf-8")
        return f

    def test_entree_conforme_rend_zero_sans_defaut(self):
        code, sortie, erreur = jouer(self._entree(entree()))
        self.assertEqual((code, sortie), (0, ""), erreur)

    def test_sans_reste_a_faire_rend_un_et_nomme_la_rubrique(self):
        texte = entree(ordre=("nouveau", "ameliore", "corrige"))
        code, sortie, erreur = jouer(self._entree(texte))
        self.assertEqual(code, 1, erreur)
        self.assertIn("« Reste à faire » absente", sortie)

    def test_ligne_de_nouveau_sans_source_rend_un_et_nomme_la_ligne(self):
        ligne = "- Le pilote écrit le récap à chaque clôture"
        texte = entree(blocs={"nouveau": f"### ✨ Nouveau\n{ligne}\n\n"})
        numero = texte.splitlines().index(ligne) + 1
        code, sortie, erreur = jouer(self._entree(texte))
        self.assertEqual(code, 1, erreur)
        self.assertIn(f"ligne {numero} : ligne sans source", sortie)

    def test_rubrique_vide_sans_rien_rend_un_et_nomme_la_rubrique(self):
        texte = entree(blocs={"corrige": "### 🐛 Corrigé\n\n"})
        code, sortie, erreur = jouer(self._entree(texte))
        self.assertEqual(code, 1, erreur)
        self.assertIn("« Corrigé » vide", sortie)

    def test_rubriques_dans_le_desordre_rendent_un(self):
        texte = entree(ordre=("nouveau", "corrige", "ameliore", "reste"))
        code, sortie, erreur = jouer(self._entree(texte))
        self.assertEqual(code, 1, erreur)
        self.assertIn("désordre", sortie)

    def test_page_sans_recap_rend_deux(self):
        # Le garde du code 2 : sans script, Python rend 2 lui aussi. Le libellé
        # « Récap » sur la sortie d'erreur distingue le script absent du refus voulu.
        texte = "# Plan\n\n## Exécution\n\nDu texte.\n"
        code, sortie, erreur = jouer(self._entree(texte))
        self.assertEqual(code, 2, sortie)
        self.assertIn("Récap", erreur)

    def test_en_tete_sans_date_rend_un(self):
        texte = entree(entete="## Récap — plan « Exemple »\n\nPR : #12 — statut : prête\n\n")
        code, sortie, erreur = jouer(self._entree(texte))
        self.assertEqual(code, 1, erreur)
        self.assertIn("sans date", sortie)


if __name__ == "__main__":
    unittest.main()
