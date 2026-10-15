"""Tests de ``qualite-doc.py lecteurs`` : quels passages Markdown relire après une branche.

Chaque test fabrique un dépôt git jetable (une base, puis les commits de la
branche) et lance le vrai script en sous-processus (``sys.executable``), comme
les autres tests de ``scripts/``. Pas d'import : tant que le script n'existe
pas, le rouge est net (code de sortie non nul), pas une erreur de collecte.

Lancés par la CI (``python3 -m unittest discover -s scripts``), sans
dépendance : ``unittest`` est dans la bibliothèque standard.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "qualite-doc.py"


def git(racine: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(racine), *args], check=True,
                       capture_output=True, text=True)
    return r.stdout.strip()


class Depot:
    """Dépôt git jetable : ``commit`` écrit les fichiers (``None`` = supprimé) puis valide."""

    def __init__(self, racine: Path):
        self.racine = racine
        git(racine, "init", "-q")
        git(racine, "config", "user.name", "test")
        git(racine, "config", "user.email", "test@example.invalid")
        git(racine, "config", "commit.gpgsign", "false")

    def commit(self, fichiers: dict, message: str) -> str:
        for chemin, contenu in fichiers.items():
            cible = self.racine / chemin
            if contenu is None:
                cible.unlink()
            else:
                cible.parent.mkdir(parents=True, exist_ok=True)
                cible.write_text(contenu, encoding="utf-8")
        git(self.racine, "add", "-A")
        git(self.racine, "commit", "-q", "-m", message)
        return git(self.racine, "rev-parse", "HEAD")


def lire(racine: Path, base: str, *extra: str):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "lecteurs", "--base", base, "--racine", str(racine), *extra],
        capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def lignes_relevees(rapport: dict, fichier: str) -> list[int]:
    return sorted(p["ligne"] for p in rapport["passages"] if p["fichier"] == fichier)


class LecteursBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.depot = Depot(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def faire(self, base: dict, branche: dict, *extra: str) -> dict:
        """Valide ``base`` puis ``branche`` ; rend le rapport JSON de ``lecteurs``."""
        sha = self.depot.commit(base, "base")
        self.depot.commit(branche, "branche")
        code, sortie, erreur = lire(self.depot.racine, sha, *extra)
        self.assertEqual(code, 0, f"lecteurs a rendu {code} : {erreur}")
        return json.loads(sortie)

    def test_une_fonction_renommee_fait_relever_le_passage_qui_cite_l_ancien_nom(self):
        rapport = self.faire(
            {"scripts/outils.py": "def ancien_calcul(x):\n    return x\n",
             "docs/guide.md": "Le calcul passe par `ancien_calcul()`.\n"},
            {"scripts/outils.py": "def nouveau_calcul(x):\n    return x\n"},
        )
        releves = [p for p in rapport["passages"] if p["fichier"] == "docs/guide.md"]
        self.assertEqual([p["ligne"] for p in releves], [1])
        self.assertIn("ancien_calcul", releves[0]["termes"])

    def test_un_skill_md_touche_ne_releve_pas_les_passages_qui_citent_son_nom_court(self):
        rapport = self.faire(
            {"plugins/x/skills/y/SKILL.md": "---\nname: y\n---\n",
             "docs/liste.md": "Le skill `SKILL.md` décrit la marche.\n"
                              "Le chemin est `plugins/x/skills/y/SKILL.md`.\n"},
            {"plugins/x/skills/y/SKILL.md": "---\nname: y\ndescription: neuf\n---\n"},
        )
        # Le nom court seul (ligne 1) n'est pas un terme ; le chemin complet (ligne 2) l'est.
        self.assertEqual(lignes_relevees(rapport, "docs/liste.md"), [2])

    def test_au_dela_de_max_passages_le_compte_des_passages_omis_est_rendu(self):
        rapport = self.faire(
            {"scripts/deploy.py": "x = 1\n",
             "docs/a.md": "Voir `deploy.py`.\n" * 5},
            {"scripts/deploy.py": "x = 2\n"},
            "--max-passages", "2",
        )
        self.assertEqual([p["ligne"] for p in rapport["passages"]], [1, 2])
        self.assertEqual(rapport["passages_omis"], 3)

    def test_claude_md_ou_readme_a_la_racine_ne_releve_pas_les_passages_qui_citent_son_nom(self):
        # Contrôle intégré : la ligne 3 cite `deploy.py`, qui a bien changé, et doit être relevée.
        rapport = self.faire(
            {"CLAUDE.md": "# Règles\n", "README.md": "# Projet\n",
             "scripts/deploy.py": "x = 1\n",
             "docs/a.md": "Lire `CLAUDE.md`.\nLire `README.md`.\nLancer `deploy.py`.\n"},
            {"CLAUDE.md": "# Règles neuves\n", "README.md": "# Projet neuf\n",
             "scripts/deploy.py": "x = 2\n"},
        )
        self.assertEqual(lignes_relevees(rapport, "docs/a.md"), [3])

    def test_deploy_py_touche_ne_releve_pas_un_passage_qui_ne_cite_que_test_deploy_py(self):
        rapport = self.faire(
            {"scripts/deploy.py": "x = 1\n",
             "scripts/test_deploy.py": "x = 1\n",
             "docs/a.md": "Lancer `test_deploy.py`.\nLancer `deploy.py`.\n"},
            {"scripts/deploy.py": "x = 2\n"},
        )
        self.assertEqual(lignes_relevees(rapport, "docs/a.md"), [2])

    def test_un_md_sous_un_dossier_out_n_est_pas_lu_par_defaut(self):
        # Contrôle intégré : docs/a.md, qui cite le même nom, est bien relevé.
        rapport = self.faire(
            {"scripts/deploy.py": "x = 1\n",
             "out/rapport.md": "Voir `deploy.py`.\n",
             "docs/a.md": "Voir `deploy.py`.\n"},
            {"scripts/deploy.py": "x = 2\n"},
        )
        self.assertEqual({p["fichier"] for p in rapport["passages"]}, {"docs/a.md"})

    def test_une_constante_majuscule_dont_la_valeur_change_fait_relever_ses_passages(self):
        rapport = self.faire(
            {"scripts/config.py": "LIMITE_TENTATIVES = 3\n",
             "docs/a.md": "Le plafond `LIMITE_TENTATIVES` vaut 3.\n"},
            {"scripts/config.py": "LIMITE_TENTATIVES = 5\n"},
        )
        releves = [p for p in rapport["passages"] if p["fichier"] == "docs/a.md"]
        self.assertEqual([p["ligne"] for p in releves], [1])
        self.assertIn("LIMITE_TENTATIVES", releves[0]["termes"])

    def test_un_fichier_renomme_fait_relever_le_passage_qui_cite_son_ancien_chemin(self):
        rapport = self.faire(
            {"scripts/ancien_nom.py": "VALEUR = 1\n",
             "docs/a.md": "Voir `ancien_nom.py`.\n"},
            {"scripts/ancien_nom.py": None,
             "scripts/nouveau_nom.py": "VALEUR = 1\n"},
        )
        releves = [p for p in rapport["passages"] if p["fichier"] == "docs/a.md"]
        self.assertEqual([p["ligne"] for p in releves], [1])
        self.assertIn("ancien_nom.py", releves[0]["termes"])

    # Test en plus, hors liste du brief : la signature d'une fonction qui change (même nom,
    # autres paramètres) est une panne distincte du renommage et du retrait. Sans lui,
    # une mutation qui ne compare plus les signatures survit.
    def test_une_signature_changee_fait_relever_le_passage_qui_cite_la_fonction(self):
        rapport = self.faire(
            {"scripts/outils.py": "def calcul(x):\n    return x\n",
             "docs/a.md": "Appeler `calcul(x)` avant tout.\n"},
            {"scripts/outils.py": "def calcul(x, y):\n    return x\n"},
        )
        releves = [p for p in rapport["passages"] if p["fichier"] == "docs/a.md"]
        self.assertEqual([p["ligne"] for p in releves], [1])
        self.assertIn("calcul", releves[0]["termes"])

    # Test en plus, hors liste du brief : les champs `ligne_modifiee_dans_la_branche` et
    # `extrait_diff` font partie du contrat du JSON. Sans lui, une sortie qui marque
    # toutes les lignes comme inchangées, ou qui ne rend aucun hunk, passerait.
    def test_une_ligne_ajoutee_par_la_branche_est_marquee_et_son_extrait_porte_le_diff(self):
        rapport = self.faire(
            {"scripts/deploy.py": "def lancer():\n    return 1\n",
             "docs/a.md": "Ancienne phrase sur `deploy.py`.\nAutre phrase sur `deploy.py`.\n"},
            {"scripts/deploy.py": "def lancer():\n    return 2\n",
             "docs/a.md": "Nouvelle phrase sur `deploy.py`.\nAutre phrase sur `deploy.py`.\n"},
        )
        par_ligne = {p["ligne"]: p for p in rapport["passages"] if p["fichier"] == "docs/a.md"}
        self.assertTrue(par_ligne[1]["ligne_modifiee_dans_la_branche"])
        self.assertFalse(par_ligne[2]["ligne_modifiee_dans_la_branche"])
        self.assertIn("+    return 2", par_ligne[2]["extrait_diff"])
        self.assertLessEqual(len(par_ligne[2]["extrait_diff"]), 4000)


if __name__ == "__main__":
    unittest.main()
