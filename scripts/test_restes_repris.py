"""Tests de ``restes-repris.py`` : une panne nommée, un test.

Les pages et les exports sont écrits dans chaque test (dossier temporaire). Le script
tourne en sous-processus, comme ``test_restes_sans_ligne.py`` : le contrat testé est son
code retour et sa sortie, pas sa structure interne.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "restes-repris.py"

DEPOT = "benjaminge73/mes-skills"
AUTRE_DEPOT = "benjaminge73/hermes-custom"
NON_NOMME = "benjaminge73/vahiny"
ID_A = "3f2a8c1d-9b7e-4a60-a5c1-e2d4f6b8a901"   # export : id avec tirets, comme Notion
URL_A = "https://app.notion.com/p/3f2a8c1d9b7e4a60a5c1e2d4f6b8a901"
ID_B = "7d1e0f2a-3b4c-4d5e-8f6a-0b1c2d3e4f50"
URL_B = "https://app.notion.com/p/7d1e0f2a3b4c4d5e8f6a0b1c2d3e4f50"
ID_C = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
URL_C = "https://app.notion.com/p/a1b2c3d4e5f64a7b8c9d0e1f2a3b4c5d"
TITRE_A = "Hal relance la CI de mes-skills"
TITRE_B = "Benjamin tranche le format de sortie du garde"
TITRE_C = "Relancer le banc de vahiny"


def ligne(titre, depot=DEPOT, id_=ID_A, etat="ouvert"):
    """Une ligne de l'export de ``restes_lignes.py lire``, aux clés de restes.md."""
    return {
        "Reste": titre,
        "Repo": depot,
        "Type": "geste",
        "Pour": "Hal",
        "Plan d'origine": "",
        "Repris par": "",
        "Échéance": "",
        "État": etat,
        "Condition": "la CI repasse au vert",
        "Contexte": "",
        "Journal": "",
        "id": id_,
    }


def page(chapitre=None, repo=DEPOT):
    """Miroir d'une page de plan : une propriété Repo, et le H2 « Restes repris » s'il est donné."""
    texte = "# Plan de test\n\n"
    if repo is not None:
        texte += f"**Repo** : {repo}\n\n"
    texte += "## Cartes\n\n- une carte\n\n"
    if chapitre is not None:
        texte += "## Restes repris\n\n" + "".join(f"{puce}\n" for puce in chapitre) + "\n"
    return texte


class _Dossier(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def ecrire(self, nom, texte):
        f = self.dossier / nom
        f.write_text(texte, encoding="utf-8")
        return f

    def ecrire_export(self, lignes, nom="lignes.json"):
        """Export en JSON-lines, la forme que rend ``restes_lignes.py lire``."""
        return self.ecrire(nom, "".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lignes))

    def jouer(self, page_fichier, lignes_fichier, depots=None):
        argv = [sys.executable, str(SCRIPT), str(page_fichier), "--lignes", str(lignes_fichier)]
        if depots is not None:
            argv += ["--depots", depots]
        r = subprocess.run(argv, capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr


class RestesRepris(_Dossier):
    def test_ligne_ouverte_absente_du_chapitre_rend_1_et_la_nomme(self):
        # Panne : une ligne ouverte du dépôt, oubliée par le plan, passe le garde.
        p = self.ecrire("page.md", page(chapitre=["- [" + TITRE_B + "](" + URL_B + ") — reprise."]))
        lignes = self.ecrire_export([ligne(TITRE_A)])
        code, sortie, _ = self.jouer(p, lignes)
        self.assertEqual(code, 1, sortie)
        self.assertIn(TITRE_A, sortie)
        self.assertIn(DEPOT, sortie)
        self.assertIn(ID_A, sortie)

    def test_ligne_ouverte_citee_dans_le_chapitre_rend_0(self):
        # Panne : une ligne reprise, citée par son lien ou par son titre seul, est signalée
        # oubliée. Un export en tableau JSON, accepté aussi, doit rendre le même verdict.
        citations = {
            "par le lien de la ligne": f"- [{TITRE_A}]({URL_A}) — reprise, Pour Hal.",
            "par le titre seul": f"- {TITRE_A} — reprise, Pour Hal.",
        }
        for forme, puce in citations.items():
            with self.subTest(forme=forme):
                p = self.ecrire("page.md", page(chapitre=[puce]))
                code, sortie, _ = self.jouer(p, self.ecrire_export([ligne(TITRE_A)]))
                self.assertEqual(code, 0, sortie)
        p = self.ecrire("page.md", page(chapitre=[f"- [{TITRE_A}]({URL_A}) — reprise."]))
        tableau = self.ecrire("tableau.json", json.dumps([ligne(TITRE_A)], ensure_ascii=False))
        code, sortie, _ = self.jouer(p, tableau)
        self.assertEqual(code, 0, sortie)

    def test_laissee_ouverte_sans_raison_rend_1(self):
        # Panne : une ligne « laissée ouverte » sans raison passe comme si elle était reprise
        # (ou comme si elle avait une raison). Avec une raison, la même puce rend 0.
        sans_raison = {
            "tiret seul": f"- [{TITRE_A}]({URL_A}) — laissée ouverte",
            "deux-points vide": f"- [{TITRE_A}]({URL_A}) — laissée ouverte :",
        }
        for forme, puce in sans_raison.items():
            with self.subTest(forme=forme):
                p = self.ecrire("page.md", page(chapitre=[puce]))
                code, sortie, _ = self.jouer(p, self.ecrire_export([ligne(TITRE_A)]))
                self.assertEqual(code, 1, sortie)
                self.assertIn(TITRE_A, sortie)
        avec_raison = f"- [{TITRE_A}]({URL_A}) — laissée ouverte : hors sujet, Benjamin tranche."
        p = self.ecrire("page.md", page(chapitre=[avec_raison]))
        code, sortie, _ = self.jouer(p, self.ecrire_export([ligne(TITRE_A)]))
        self.assertEqual(code, 0, sortie)

    def test_second_depot_non_cite_rend_1_quel_que_soit_le_mode_de_lecture(self):
        # Panne : un plan à deux dépôts ne contrôle que le premier : la ligne ouverte du
        # second, absente du chapitre, passe. Les dépôts viennent de --depots, ou de la
        # propriété Repo quand --depots est absent.
        p = self.ecrire("page.md", page(
            chapitre=[f"- [{TITRE_A}]({URL_A}) — reprise."],
            repo=f"{DEPOT}, {AUTRE_DEPOT}"))
        lignes = self.ecrire_export([ligne(TITRE_A), ligne(TITRE_B, AUTRE_DEPOT, ID_B)])
        for mode, depots in {"--depots": f"{DEPOT},{AUTRE_DEPOT}", "propriété Repo": None}.items():
            with self.subTest(mode=mode):
                code, sortie, _ = self.jouer(p, lignes, depots)
                self.assertEqual(code, 1, sortie)
                self.assertIn(TITRE_B, sortie)
                self.assertIn(AUTRE_DEPOT, sortie)
                self.assertNotIn(TITRE_A, sortie)

    def test_ligne_d_un_depot_non_nomme_est_ignoree(self):
        # Panne : une ligne ouverte d'un dépôt que le plan ne touche pas bloque le garde.
        p = self.ecrire("page.md", page(chapitre=[f"- [{TITRE_A}]({URL_A}) — reprise."]))
        lignes = self.ecrire_export([ligne(TITRE_A), ligne(TITRE_C, NON_NOMME, ID_C)])
        code, sortie, _ = self.jouer(p, lignes)
        self.assertEqual(code, 0, sortie)

    def test_export_illisible_rend_2(self):
        # Panne : un export cassé ou incomplet passe pour une base sans ligne ouverte (code 0).
        # Un fichier vide compte aussi : une sortie de commande vide peut être un échec muet.
        p = self.ecrire("page.md", page(chapitre=[]))
        sans_id = {cle: val for cle, val in ligne(TITRE_A).items() if cle != "id"}
        cas = {
            "export absent": self.dossier / "absent.json",
            "JSON cassé": self.ecrire("casse.json", '{"Reste": "' + "\n"),
            "ligne sans id": self.ecrire_export([sans_id], "sans-id.json"),
            "fichier vide": self.ecrire("vide.json", ""),
        }
        for nom, lignes in cas.items():
            with self.subTest(nom):
                code, sortie, erreur = self.jouer(p, lignes)
                self.assertEqual(code, 2, sortie)
                self.assertIn("illisible", erreur)

    def test_sans_depot_lisible_rend_2(self):
        # Panne : ni --depots ni propriété Repo : le garde rend 0 et ne contrôle rien. Test
        # au-delà du budget de la fiche (règle 7) : c'est la seule voie où le contrôle se
        # tait sans bruit, et le relecteur doit la voir.
        p = self.ecrire("page.md", page(chapitre=[], repo=None))
        code, sortie, erreur = self.jouer(p, self.ecrire_export([ligne(TITRE_A)]))
        self.assertEqual(code, 2, sortie)
        self.assertIn("dépôt", erreur)


if __name__ == "__main__":
    unittest.main()
