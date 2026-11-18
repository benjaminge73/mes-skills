"""Garde : la règle « case cochée = décision / session pilotable par Hal » reste câblée."""
import pathlib
import unittest

SK = pathlib.Path(__file__).resolve().parent.parent / "plugins/plans-notion/skills"
REGLE = SK / "_partage/pilotable-par-hal.md"


class PilotableParHal(unittest.TestCase):
    def test_la_regle_dit_ses_trois_choses(self):
        t = REGLE.read_text()
        for m in ("même si ce n'est pas", "ne redemande pas", "AskUserQuestion", "Questions en attente", "Courrier de Hal"):
            self.assertIn(m, t)

    def test_le_skill_et_louverture_la_citent(self):
        for f in ("executer-plan-notion/SKILL.md", "executer-plan-notion/ouverture.md"):
            self.assertIn("pilotable-par-hal.md", (SK / f).read_text(), f)


if __name__ == "__main__":
    unittest.main()
