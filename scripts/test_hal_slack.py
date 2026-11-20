"""Le skill dit à une session comment mentionner Hal sur Slack : par identifiant, jamais par nom."""
import unittest
from pathlib import Path

FICHIER = Path(__file__).resolve().parents[1] / "plugins" / "plans-notion" / "skills" / "_partage" / "demander-a-hal.md"


class IdentifiantSlackDeHal(unittest.TestCase):
    def test_l_identifiant_de_mention_et_le_canal_sont_ecrits(self):
        texte = FICHIER.read_text(encoding="utf-8")
        self.assertIn("<@U0BCE143069>", texte)
        self.assertIn("C0BPSR77QP9", texte)

    def test_la_mention_par_nom_est_declaree_inoperante(self):
        texte = FICHIER.read_text(encoding="utf-8")
        self.assertIn("par son identifiant", texte)
        self.assertIn("`@Hal`", texte)


if __name__ == "__main__":
    unittest.main()
