"""Tests de ``qualite-doc.py`` : ``lecteurs`` (quels passages relire après une branche) et ``juger``.

Chaque test fabrique un dépôt git jetable (une base, puis les commits de la
branche) et lance le vrai script en sous-processus (``sys.executable``), comme
les autres tests de ``scripts/``. Pas d'import : tant que le script n'existe
pas, le rouge est net (code de sortie non nul), pas une erreur de collecte.

Lancés par la CI (``python3 -m unittest discover -s scripts``), sans
dépendance : ``unittest`` est dans la bibliothèque standard.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "qualite-doc.py"
GRILLE = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "grille-doc.md"
MODELE = "claude-haiku-5-5"


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

    # Panne : la base avance après le point de branchement, et ce qu'elle a changé
    # (renommage g -> h, constante LIMITE 3 -> 5) ressort comme touché par la branche,
    # alors que la branche ne touche qu'à `autre`. Le relevé doit se faire au merge-base.
    def test_une_base_qui_avance_apres_le_branchement_ne_fait_pas_relever_ce_qu_elle_seule_a_change(self):
        racine = self.depot.racine
        self.depot.commit(
            {"scripts/outils.py": "def g(x):\n    return x\n\ndef autre(x):\n    return x\n\nLIMITE = 3\n",
             "docs/a.md": "Appeler `h()` ici.\nLe plafond `LIMITE` vaut 3.\nAppeler `autre()` ici.\n"},
            "point de branchement")
        principale = git(racine, "symbolic-ref", "--short", "HEAD")
        git(racine, "checkout", "-q", "-b", "branche")
        self.depot.commit(
            {"scripts/outils.py": "def g(x):\n    return x\n\ndef autre(x, y=0):\n    return x\n\nLIMITE = 3\n"},
            "branche : seule autre change (signature)")
        git(racine, "checkout", "-q", principale)
        base = self.depot.commit(
            {"scripts/outils.py": "def h(x):\n    return x\n\ndef autre(x):\n    return x\n\nLIMITE = 5\n"},
            "main : g renommé en h, LIMITE à 5")
        git(racine, "checkout", "-q", "branche")
        code, sortie, erreur = lire(racine, base)
        self.assertEqual(code, 0, f"lecteurs a rendu {code} : {erreur}")
        rapport = json.loads(sortie)
        self.assertEqual(lignes_relevees(rapport, "docs/a.md"), [3])

    # Trou connu : la borne droite `(?![\w-])` peut être retirée sans qu'aucun test ne
    # bronche. Un terme suivi d'un chiffre ou d'un tiret n'est pas le même nom ; la
    # ligne 3, qui cite le vrai nom, sert de témoin.
    def test_un_terme_suivi_d_un_chiffre_ou_d_un_tiret_ne_releve_pas_le_passage(self):
        rapport = self.faire(
            {"scripts/deploy.py": "x = 1\n",
             "docs/a.md": "Lancer `deploy.py2`.\nLancer `deploy.py-old`.\nLancer `deploy.py`.\n"},
            {"scripts/deploy.py": "x = 2\n"},
        )
        self.assertEqual(lignes_relevees(rapport, "docs/a.md"), [3])


# Faux exécutable de ``claude`` : écrit par le test dans son dossier temporaire. Chaque appel
# consomme une réponse (cyclique), garde son prompt reçu sur l'entrée standard et le dossier
# de travail d'où il a été lancé. Les tests ne vérifient pas les arguments de ``subprocess.run``.
FAUX_CLAUDE = """#!{python}
import glob, json, os, sys
dossier = {dossier!r}
with open(os.path.join(dossier, "reponses.json"), encoding="utf-8") as f:
    reponses = json.load(f)
n = len(glob.glob(os.path.join(dossier, "prompt-*.txt")))
with open(os.path.join(dossier, "prompt-%03d.txt" % n), "w", encoding="utf-8") as f:
    f.write(sys.stdin.buffer.read().decode("utf-8"))
with open(os.path.join(dossier, "cwd-%03d.txt" % n), "w", encoding="utf-8") as f:
    f.write(os.getcwd())
sys.stdout.write(reponses[n % len(reponses)])
"""


def sortie_juge(texte, cout=0.01, modeles=(MODELE,), erreur=False) -> str:
    """Sortie brute de ``claude -p --output-format json`` : un objet JSON, rendu en texte."""
    return json.dumps({
        "type": "result",
        "is_error": erreur,
        "result": texte,
        "total_cost_usd": cout,
        "modelUsage": {m: {"costUSD": cout} for m in modeles},
    })


def verdict(exact, confiance, raison="motif") -> str:
    """Le texte ``result`` attendu d'un vote : l'objet JSON que la grille demande."""
    return json.dumps({"exact": exact, "confiance": confiance, "raison": raison})


def passage(ligne=1, extrait="+    return 2") -> dict:
    return {"fichier": "docs/a.md", "ligne": ligne, "texte": f"Ligne {ligne} : `deploy.py`.",
            "termes": ["deploy.py"], "extrait_diff": extrait}


class FauxClaude:
    def __init__(self, dossier: Path, reponses: list[str]):
        self.dossier = dossier
        self.exe = dossier / "claude"
        (dossier / "reponses.json").write_text(json.dumps(reponses), encoding="utf-8")
        self.exe.write_text(FAUX_CLAUDE.format(python=sys.executable, dossier=str(dossier)),
                            encoding="utf-8")
        self.exe.chmod(0o755)

    def prompts(self) -> list[str]:
        return [p.read_text(encoding="utf-8") for p in sorted(self.dossier.glob("prompt-*.txt"))]

    def cwds(self) -> list[str]:
        return [p.read_text(encoding="utf-8") for p in sorted(self.dossier.glob("cwd-*.txt"))]


class Juger(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dossier = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def juger(self, entree, exe: Path, *extra: str):
        """Écrit ``entree`` (liste ou dict ``passages``) et lance ``juger`` ; rend (code, stdout, stderr)."""
        fichier = self.dossier / "entree.json"
        fichier.write_text(json.dumps(entree, ensure_ascii=False), encoding="utf-8")
        env = {**os.environ, "QUALITE_DOC_CLAUDE": str(exe)}
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "juger", "--entree", str(fichier), *extra],
            capture_output=True, text=True, encoding="utf-8", env=env)
        return r.returncode, r.stdout, r.stderr

    def test_deux_votes_divergents_font_retenir_le_plus_pessimiste(self):
        faux = FauxClaude(self.dossier, [sortie_juge(verdict(True, 0.9)),
                                         sortie_juge(verdict(False, 0.7))])
        code, sortie, erreur = self.juger([passage()], faux.exe)
        self.assertEqual(code, 0, erreur)
        v = json.loads(sortie)["verdicts"][0]
        self.assertAlmostEqual(v["score"], 0.7)
        self.assertFalse(v["exact"])

    def test_un_autre_modele_servi_fait_echouer_avec_le_code_5(self):
        faux = FauxClaude(self.dossier,
                          [sortie_juge(verdict(True, 0.9), modeles=("claude-autre-modele",))])
        code, sortie, erreur = self.juger([passage()], faux.exe)
        self.assertEqual(code, 5, erreur)
        self.assertNotIn("Traceback", erreur)

    def test_claude_absent_rend_le_code_3_avec_un_message_nomme(self):
        absent = self.dossier / "absent" / "claude"
        code, sortie, erreur = self.juger([passage()], absent)
        self.assertEqual(code, 3, erreur)
        self.assertIn("juge indisponible", erreur)
        self.assertNotIn("Traceback", erreur)

    def test_un_result_illisible_compte_comme_douteux_et_jamais_comme_exact(self):
        faux = FauxClaude(self.dossier, [sortie_juge("je ne sais pas, aucun objet ici")])
        code, sortie, erreur = self.juger([passage()], faux.exe)
        self.assertEqual(code, 0, erreur)
        rapport = json.loads(sortie)
        v = rapport["verdicts"][0]
        self.assertFalse(v["exact"])
        self.assertEqual(v["score"], 1.0)
        self.assertEqual(v["raison"], "réponse illisible")
        self.assertEqual([d["ligne"] for d in rapport["douteux"]], [1])

    def test_le_seuil_separe_les_douteux_et_compte_le_seuil_lui_meme(self):
        # Le score exactement égal au seuil (0,5) est douteux : la comparaison est ≥.
        faux = FauxClaude(self.dossier, [sortie_juge(verdict(False, c)) for c in (0.3, 0.5, 0.6)])
        code, sortie, erreur = self.juger([passage(1), passage(2), passage(3)], faux.exe,
                                          "--votes", "1", "--seuil", "0.5")
        self.assertEqual(code, 0, erreur)
        self.assertEqual([d["ligne"] for d in json.loads(sortie)["douteux"]], [2, 3])

    def test_max_cout_atteint_rend_le_code_4_avec_le_partiel_et_le_compte_non_juge(self):
        faux = FauxClaude(self.dossier, [sortie_juge(verdict(False, 0.2), cout=0.5)])
        code, sortie, erreur = self.juger([passage(1), passage(2), passage(3)], faux.exe,
                                          "--votes", "1", "--max-cout", "0.6")
        self.assertEqual(code, 4, erreur)
        rapport = json.loads(sortie)
        self.assertEqual(rapport["passages_non_juges"], 1)
        self.assertEqual(len(rapport["verdicts"]), 2)

    def test_une_liste_nue_de_passages_est_acceptee(self):
        faux = FauxClaude(self.dossier, [sortie_juge(verdict(True, 0.9))])
        code, sortie, erreur = self.juger([passage()], faux.exe, "--votes", "1")
        self.assertEqual(code, 0, erreur)
        self.assertEqual(len(json.loads(sortie)["verdicts"]), 1)

    def test_le_prompt_porte_la_grille_et_l_extrait_du_diff(self):
        marque = "retour_neuf_7f3a"
        faux = FauxClaude(self.dossier, [sortie_juge(verdict(True, 0.9))])
        code, sortie, erreur = self.juger([passage(extrait=f"+    return {marque}")], faux.exe,
                                          "--votes", "1")
        self.assertEqual(code, 0, erreur)
        prompts = faux.prompts()
        self.assertEqual(len(prompts), 1)
        # La grille est lue telle quelle depuis le dépôt : le juge reçoit ses critères, sans copie.
        self.assertIn(GRILLE.read_text(encoding="utf-8"), prompts[0])
        self.assertIn(marque, prompts[0])

    # Test en plus, hors liste du brief : le juge ne doit jamais tourner dans le dépôt, sinon
    # les hooks et les CLAUDE.md du dépôt entreraient dans son contexte. Sans lui, un juge lancé
    # depuis la racine du dépôt passerait tous les autres tests.
    def test_le_juge_tourne_hors_du_depot(self):
        faux = FauxClaude(self.dossier, [sortie_juge(verdict(True, 0.9))])
        code, sortie, erreur = self.juger([passage()], faux.exe, "--votes", "1")
        self.assertEqual(code, 0, erreur)
        cwd = Path(faux.cwds()[0]).resolve()
        self.assertNotIn(RACINE, [cwd, *cwd.parents])

    # Test en plus, hors liste du brief : Haiku suit souvent le format ```json. Sans ce test,
    # un extracteur qui ne lit que le texte nu rendrait douteux un verdict pourtant exact.
    def test_le_json_entoure_de_cloture_markdown_est_lu(self):
        faux = FauxClaude(self.dossier,
                          [sortie_juge("```json\n" + verdict(True, 0.9) + "\n```")])
        code, sortie, erreur = self.juger([passage()], faux.exe, "--votes", "1")
        self.assertEqual(code, 0, erreur)
        rapport = json.loads(sortie)
        self.assertTrue(rapport["verdicts"][0]["exact"])
        self.assertEqual(rapport["douteux"], [])


if __name__ == "__main__":
    unittest.main()
