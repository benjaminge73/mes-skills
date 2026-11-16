"""Tests de ``restes-sans-ligne.py`` : une panne nommée, un test.

Les pages et les exports sont écrits dans chaque test (dossier temporaire). Le script
tourne en sous-processus, comme ``test_preuves_des_etapes.py`` : le contrat testé est
son code retour et sa sortie, pas sa structure interne.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "restes-sans-ligne.py"

ENTETE = (
    "# Plan de test\n\n## Cartes\n\n- une carte\n\n"
    "## Journal d'exécution\n\n### Ouverture\n\n- **Date** : 2026-11-16.\n\n"
)
URL_LIGNE = "https://app.notion.com/p/3f2a8c1d9b7e4a60a5c1e2d4f6b8a901"
URL_PLAN_DE_SUITE = "https://app.notion.com/p/9c0d1e2f3a4b45c6d7e8f9a0b1c2d3e4"
RESTE = "Benjamin tranche la question Q3 sur le format de sortie"


def page(*etat_final):
    """Page de plan : le H3 « État final » porte les lignes données."""
    corps = "".join(f"{ligne}\n" for ligne in etat_final)
    return ENTETE + "### État final\n\n" + corps + "\n"


def ligne(reste, url=URL_LIGNE):
    """Une ligne de l'export de la base « Restes », au format de restes.md."""
    return {
        "Reste": reste,
        "Pour": "Benjamin",
        "État": "ouvert",
        "Plan d'origine": "https://app.notion.com/p/0a1b2c3d4e5f60718293a4b5c6d7e8f9",
        "url": url,
    }


class _Dossier(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def ecrire(self, nom, texte):
        f = self.dossier / nom
        f.write_text(texte, encoding="utf-8")
        return f

    def ecrire_lignes(self, lignes, nom="lignes.json"):
        return self.ecrire(nom, json.dumps(lignes, ensure_ascii=False))

    def jouer(self, page_fichier, lignes_fichier):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), str(page_fichier), "--lignes", str(lignes_fichier)],
            capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr


class RestesSansLigne(_Dossier):
    def test_reste_qui_attend_un_evenement_sans_ligne_est_signale(self):
        # Panne : un reste en attente, sans ligne dans la base, passe le garde.
        p = self.ecrire("page.md", page(
            "- **Reste à faire** :",
            f"  - {RESTE} : sa réponse gèle le travail.",
        ))
        code, sortie, _ = self.jouer(p, self.ecrire_lignes([]))
        self.assertEqual(code, 1, sortie)
        self.assertIn(f"Reste sans ligne dans la base : {RESTE}", sortie)

    def test_reste_deja_porte_par_un_plan_de_suite_n_est_pas_manquant(self):
        # Panne : un reste repris par une « Reprise du plan #N » est compté comme manquant.
        p = self.ecrire("page.md", page(
            "- **Reste à faire** :",
            f"  - {RESTE}, repris par [Reprise du plan #4]({URL_PLAN_DE_SUITE}).",
        ))
        code, sortie, _ = self.jouer(p, self.ecrire_lignes([]))
        self.assertEqual(code, 0, sortie)

    def test_miroir_du_connecteur_en_html_est_lu(self):
        # Panne : le miroir du connecteur (<b>, <code>) n'est pas lu : la rubrique est
        # introuvable (code 2) ou le reste disparaît (code 0). Un reste doit sortir en 1.
        p = self.ecrire("page.md", page(
            "- <b>Reste à faire</b> :",
            "  - Hal relance <b>la CI</b> de <code>mes-skills</code> : attend un événement.",
        ))
        code, sortie, _ = self.jouer(p, self.ecrire_lignes([]))
        self.assertEqual(code, 1, sortie)
        self.assertIn("Reste sans ligne dans la base : Hal relance la CI de mes-skills", sortie)

    def test_reste_qui_cite_le_lien_de_sa_ligne_est_satisfait(self):
        # Panne : un reste qui cite sa ligne par lien est signalé manquant. Deux formes de
        # lien : markdown, et mention de page du connecteur.
        liens = {
            "markdown": f"[la ligne]({URL_LIGNE})",
            "mention": f'<mention-page url="{URL_LIGNE}">la ligne</mention-page>',
        }
        for forme, lien in liens.items():
            with self.subTest(forme=forme):
                p = self.ecrire("page.md", page(
                    "- **Reste à faire** :",
                    f"  - {RESTE}, voir {lien}.",
                ))
                code, sortie, _ = self.jouer(p, self.ecrire_lignes([ligne(RESTE)]))
                self.assertEqual(code, 0, sortie)

    def test_reste_deja_verse_sans_lien_est_satisfait_par_son_texte(self):
        # Panne : un reste déjà versé dans la base, écrit sans lien, est signalé manquant.
        p = self.ecrire("page.md", page(
            "- **Reste à faire** :",
            f"  - {RESTE} : attend sa réponse.",
        ))
        code, sortie, _ = self.jouer(p, self.ecrire_lignes([ligne(RESTE)]))
        self.assertEqual(code, 0, sortie)

    def test_page_sans_reste_rend_zero(self):
        # Panne : une page sans reste en attente est refusée.
        p = self.ecrire("page.md", page("- **Reste à faire** : rien"))
        code, sortie, _ = self.jouer(p, self.ecrire_lignes([]))
        self.assertEqual(code, 0, sortie)

    def test_puce_d_une_autre_rubrique_n_est_pas_prise_pour_un_reste(self):
        # Panne : la rubrique « Reste à faire » ne s'arrête pas à la clé suivante, et une
        # « Découvertes » de l'« État final » devient un reste manquant.
        p = self.ecrire("page.md", page(
            "- **Reste à faire** : rien",
            "- **Découvertes** : 2 découvertes, la seconde attend Benjamin.",
        ))
        code, sortie, _ = self.jouer(p, self.ecrire_lignes([]))
        self.assertEqual(code, 0, sortie)

    def test_fichier_illisible_rend_2(self):
        # Panne : un fichier absent ou cassé passe pour une page ou un export conforme.
        bonne_page = self.ecrire("page.md", page("- **Reste à faire** : rien"))
        sans_url = {cle: val for cle, val in ligne(RESTE).items() if cle != "url"}
        cas = {
            "page absente": (self.dossier / "absente.md", self.ecrire_lignes([])),
            "export non JSON": (bonne_page, self.ecrire("cassé.json", "[{")),
            "export sans champ url": (bonne_page, self.ecrire_lignes([sans_url], "sans-url.json")),
        }
        for nom, (p, lignes) in cas.items():
            with self.subTest(nom):
                code, sortie, _ = self.jouer(p, lignes)
                self.assertEqual(code, 2, sortie)

    def test_page_sans_etat_final_ou_sans_rubrique_rend_2(self):
        # Panne : une page sans H3 « État final », ou sans rubrique « Reste à faire », donne
        # zéro reste et passe pour conforme.
        cas = {
            "sans H3 État final": ENTETE,
            "sans rubrique Reste à faire": page("- **Découvertes** : aucune"),
        }
        for nom, texte in cas.items():
            with self.subTest(nom):
                p = self.ecrire("page.md", texte)
                code, sortie, _ = self.jouer(p, self.ecrire_lignes([]))
                self.assertEqual(code, 2, sortie)


if __name__ == "__main__":
    unittest.main()
