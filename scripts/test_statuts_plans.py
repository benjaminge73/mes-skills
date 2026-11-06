"""Le sens des statuts ``brouillon`` et ``en revue`` reste écrit dans les skills.

``brouillon`` : rédaction partielle. ``en revue`` : l'agent a fini de rédiger, le
plan attend la relecture de Benjamin, qui filtre la base sur ce statut. Si une
des trois sources perd cette définition, un plan inachevé peut de nouveau se
retrouver dans « en revue ».
"""
from __future__ import annotations

import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parent.parent / "plugins" / "plans-notion" / "skills"


def lire(chemin: str) -> str:
    return " ".join((SKILLS / chemin).read_text(encoding="utf-8").split())


class TestSensDesStatuts(unittest.TestCase):
    def test_plan_notion_definit_les_deux_statuts(self):
        texte = lire("plan-notion/SKILL.md")
        self.assertIn("**`en revue`** = l'agent a **fini de rédiger**", texte)
        self.assertIn("Poser le `Statut` que l'état de la page justifie", texte)

    def test_le_vocabulaire_partage_le_redit(self):
        texte = lire("_partage/ecrire-dans-notion.md")
        self.assertIn("`brouillon` : posé à la création, la rédaction est **partielle**", texte)
        self.assertIn("`en revue` : posé **par l'agent** quand il a **fini de rédiger**", texte)

    def test_l_execution_distingue_les_deux_arrets(self):
        texte = lire("executer-plan-notion/SKILL.md")
        self.assertIn("`en revue` (en attente de relecture)", texte)


if __name__ == "__main__":
    unittest.main()
