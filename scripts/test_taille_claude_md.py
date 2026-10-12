"""Tests de ``taille-claude-md.py`` sur des dépôts git jetables.

Le script compte les lignes de chaque ``CLAUDE.md``, de chaque
``.claude/rules/*.md`` et de chaque fichier importé par ``@chemin``, chacun à
part. Plafond : 200 lignes, ou la taille du même fichier sur la base (``--base
<réf>``) si elle est plus grande : un cliquet, qui interdit de faire grossir un
fichier au-delà de ce qu'il pèse déjà sur la base. Sans base, il avertit
seulement. Sortie : une ligne par fichier, ``<chemin> <lignes> / <plafond>
<verdict>`` (``OK``, ``AVERT``, ``REFUS``) ; code 0 ou 1.

Chaque cas pose un dépôt git jetable et lance le script en vrai sous-processus.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "taille-claude-md.py"
LIGNE = re.compile(r"^(\S+) (\d+) / (\d+) (\S+)\s*$")


def git(depot, *args):
    subprocess.run(
        ["git", "-C", str(depot), "-c", "user.name=test",
         "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True)


def lignes_de(n):
    return "".join(f"ligne {i}\n" for i in range(1, n + 1))


def jouer(depot, *args):
    r = subprocess.run([sys.executable, str(SCRIPT), "--racine", str(depot), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def relever(sortie):
    """Chemin -> (lignes, plafond, verdict), une entrée par ligne du rapport."""
    rapport = {}
    for ligne in sortie.splitlines():
        m = LIGNE.match(ligne)
        if m:
            rapport[m.group(1)] = (int(m.group(2)), int(m.group(3)), m.group(4))
    return rapport


class DepotJetable(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.depot = Path(self._tmp.name)
        git(self.depot, "init", "-q")

    def ecrire(self, chemin, texte):
        fichier = self.depot / chemin
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(texte, encoding="utf-8")

    def valider(self):
        git(self.depot, "add", "-A")
        git(self.depot, "commit", "-q", "-m", "base")


class Cliquet(DepotJetable):
    def test_un_claude_md_qui_passe_de_184_a_230_lignes_contre_sa_base_est_refuse(self):
        self.ecrire("CLAUDE.md", lignes_de(184))
        self.valider()
        self.ecrire("CLAUDE.md", lignes_de(230))
        code, sortie, erreur = jouer(self.depot, "--base", "HEAD")
        self.assertEqual(code, 1, sortie + erreur)
        self.assertEqual(relever(sortie).get("CLAUDE.md"), (230, 200, "REFUS"), sortie)

    def test_un_fichier_qui_reste_a_sa_taille_de_base_passe_meme_au_dela_de_200(self):
        self.ecrire("CLAUDE.md", lignes_de(1207))
        self.valider()
        code, sortie, erreur = jouer(self.depot, "--base", "HEAD")
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(relever(sortie).get("CLAUDE.md"), (1207, 1207, "OK"), sortie)

    def test_une_ligne_de_plus_que_la_base_au_dela_de_200_est_refusee(self):
        self.ecrire("CLAUDE.md", lignes_de(1207))
        self.valider()
        self.ecrire("CLAUDE.md", lignes_de(1208))
        code, sortie, erreur = jouer(self.depot, "--base", "HEAD")
        self.assertEqual(code, 1, sortie + erreur)
        self.assertEqual(relever(sortie).get("CLAUDE.md"), (1208, 1207, "REFUS"), sortie)


class Importations(DepotJetable):
    def test_un_fichier_importe_par_arobase_est_compte_a_part(self):
        # Le CLAUDE.md ne porte que ses 5 lignes : les 300 lignes de l'import ne
        # s'y ajoutent pas, et l'import a sa propre ligne de rapport.
        self.ecrire("CLAUDE.md", "# Titre\n\n@docs/grand.md\n\nRègle.\n")
        self.ecrire("docs/grand.md", lignes_de(300))
        code, sortie, erreur = jouer(self.depot)
        rapport = relever(sortie)
        self.assertEqual(rapport.get("CLAUDE.md"), (5, 200, "OK"), sortie + erreur)
        self.assertEqual(rapport.get("docs/grand.md"), (300, 200, "AVERT"), sortie + erreur)


class SansBase(DepotJetable):
    def test_sans_base_un_fichier_de_230_lignes_avertit_et_rend_zero(self):
        self.ecrire("CLAUDE.md", lignes_de(230))
        code, sortie, erreur = jouer(self.depot)
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(relever(sortie).get("CLAUDE.md"), (230, 200, "AVERT"), sortie + erreur)


if __name__ == "__main__":
    unittest.main()
