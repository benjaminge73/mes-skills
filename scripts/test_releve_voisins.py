"""Le relevé des voisins (releve-voisins.py) : qui cite un fichier touché, et dans quel ordre.

Chaque test monte un dépôt jouet dans un dossier temporaire et lance le script comme le ferait le pilote (sous-processus,
sortie lue ligne à ligne). Aucun mock de git : c'est git qui décide de l'historique et du contenu.

Écrit en ``unittest`` pur : la CI le joue avec un ``python3`` sans pytest (``python3 -m unittest discover -s scripts``).
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1]
          / "plugins/plans-notion/skills/_partage/scripts/releve-voisins.py")

LIGNE = re.compile(
    r"^(?P<chemin>\S+) \((?P<type>doc|code|config|test)\) — cite (?P<cite>.+) — co-change (?P<conf>\d+) %$")


def git(depot: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(depot), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, text=True).stdout


def valider(depot: Path, message: str, fichiers: dict[str, str]) -> None:
    for chemin, texte in fichiers.items():
        cible = depot / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte)
    git(depot, "add", "-A")
    git(depot, "commit", "-q", "-m", message)


def releve(depot: Path, *fichiers: str) -> str:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--depot", str(depot), "--fichiers", *fichiers],
        capture_output=True, text=True)
    assert r.returncode == 0, f"le script a rendu {r.returncode} : {r.stderr}"
    return r.stdout


def voisins(sortie: str) -> list[dict]:
    """Une ligne par voisin, au format figé du contrat. Une ligne hors format fait échouer le test."""
    out = []
    for ligne in sortie.splitlines():
        if not ligne.strip():
            continue
        m = LIGNE.match(ligne)
        assert m, f"ligne hors contrat : {ligne!r}"
        out.append({"chemin": m.group("chemin"), "type": m.group("type"), "conf": int(m.group("conf"))})
    return out


class ReleveDesVoisins(unittest.TestCase):

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.depot = Path(tmp.name) / "depot"
        self.depot.mkdir()
        git(self.depot, "init", "-q", "-b", "main")

    def test_le_releve_liste_les_deux_fichiers_qui_citent_le_fichier_touche(self):
        # Panne visée : le script ne retrouve qu'un des deux citants (grep incomplet, ou grep du seul chemin).
        depot = self.depot
        valider(depot, "cron", {"cron/y.md": "Lance a.py chaque nuit.\n"})
        valider(depot, "docs", {"docs/x.md": "Voir a.py pour le détail.\n"})
        valider(depot, "a", {"a.py": "v0\n"})

        chemins = [v["chemin"] for v in voisins(releve(depot, "a.py"))]

        self.assertIn("docs/x.md", chemins)
        self.assertIn("cron/y.md", chemins)

    def test_un_citant_co_modifie_avec_le_fichier_touche_passe_devant(self):
        # Panne visée : le classement ignore le co-change et range les citants dans l'ordre du grep.
        # docs/x.md est modifié trois fois avec a.py ; cron/y.md, cité pareil, jamais.
        depot = self.depot
        valider(depot, "cron", {"cron/y.md": "Lance a.py chaque nuit.\n"})
        valider(depot, "docs", {"docs/x.md": "Voir a.py pour le détail.\n"})
        valider(depot, "a", {"a.py": "v0\n"})
        for i in range(1, 4):
            valider(depot, f"modif {i}", {"a.py": f"v{i}\n", "docs/x.md": f"Voir a.py pour le détail, {i}.\n"})

        chemins = [v["chemin"] for v in voisins(releve(depot, "a.py"))]

        self.assertLess(chemins.index("docs/x.md"), chemins.index("cron/y.md"))

    def test_un_commit_de_25_fichiers_ne_compte_pas_dans_le_co_change(self):
        # Panne visée : le co-change compte les commits « fourre-tout » (plus de 20 fichiers). Ici cron/y.md
        # n'apparaît qu'avec a.py dans un commit de 25 fichiers : sa part doit rester à 0 %.
        # Si le commit comptait, sa part vaudrait 33 % (1 commit sur les 3 où a.py figure).
        depot = self.depot
        valider(depot, "cron", {"cron/y.md": "Lance a.py chaque nuit.\n"})
        valider(depot, "a", {"a.py": "v0\n"})
        gros = {"a.py": "v1\n", "cron/y.md": "Lance a.py chaque nuit. (bis)\n"}
        gros.update({f"bulk/f{i}.txt": f"bruit {i}\n" for i in range(23)})
        valider(depot, "gros commit", gros)
        valider(depot, "a seul", {"a.py": "v2\n"})

        conf = {v["chemin"]: v["conf"] for v in voisins(releve(depot, "a.py"))}

        self.assertEqual(conf["cron/y.md"], 0)

    def test_un_commit_posterieur_a_head_n_existe_pas_pour_le_script(self):
        # Panne visée : le script lit tout l'historique (--all) et voit des commits d'une branche future.
        # cron/y.md co-changerait trois fois avec a.py sur la branche « futur » ; HEAD (main) ne les contient pas.
        depot = self.depot
        valider(depot, "cron", {"cron/y.md": "Lance a.py chaque nuit.\n"})
        valider(depot, "a", {"a.py": "v0\n"})
        git(depot, "checkout", "-q", "-b", "futur")
        for i in range(1, 4):
            valider(depot, f"futur {i}", {"a.py": f"v{i}\n", "cron/y.md": f"Lance a.py chaque nuit ({i}).\n"})
        git(depot, "checkout", "-q", "main")

        conf = {v["chemin"]: v["conf"] for v in voisins(releve(depot, "a.py"))}

        self.assertEqual(conf["cron/y.md"], 0)

    def test_deux_fichiers_separes_par_un_blanc_dans_un_seul_argument_gardent_leurs_citants(self):
        # Panne visée : --fichiers "a.py b.py" (une seule valeur, séparée par un blanc) n'est découpé que sur les
        # virgules : le script cherche un fichier nommé « a.py b.py », ne trouve rien, et rend « aucun voisin »
        # en silence. Les deux citants doivent sortir.
        depot = self.depot
        valider(depot, "cron", {"cron/y.md": "Lance b.py chaque nuit.\n"})
        valider(depot, "docs", {"docs/x.md": "Voir a.py pour le détail.\n"})
        valider(depot, "a et b", {"a.py": "v0\n", "b.py": "v0\n"})

        chemins = [v["chemin"] for v in voisins(releve(depot, "a.py b.py"))]

        self.assertIn("docs/x.md", chemins)
        self.assertIn("cron/y.md", chemins)


if __name__ == "__main__":
    unittest.main()
