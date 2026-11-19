"""Garde : une étape déjà validée et confiée à Hal se transmet sans « go » de Benjamin."""
import pathlib
import unittest

SK = pathlib.Path(__file__).resolve().parent.parent / "plugins/plans-notion/skills"
DEMANDER = SK / "_partage/demander-a-hal.md"
CITANTS = (
    SK / "executer-plan-notion/cloture.md",
    SK / "executer-plan-notion/etapes.md",
    SK / "_partage/pilotable-par-hal.md",
)


def section(texte: str, titre: str, suivant: str) -> str:
    """Le texte entre le titre ``titre`` et le titre ``suivant`` (sans les inclure)."""
    debut = texte.index(titre)
    return texte[debut : texte.index(suivant, debut)]


class GoDejaValide(unittest.TestCase):
    def test_demander_a_hal_porte_la_transmission_validee(self):
        t = DEMANDER.read_text()
        t = DEMANDER.read_text()
        for m in ("déjà validé", "--valide", "--plafond", "dépassement"):
            self.assertTrue(m in t, f"demander-a-hal.md ne dit pas « {m} » : la transmission validée n'y est pas")

    def test_cloture_etapes_et_regle_pilotable_citent_la_transmission(self):
        for f in CITANTS:
            t = f.read_text()
            self.assertTrue("demander-a-hal.md" in t, f"{f.name} ne renvoie pas à demander-a-hal.md")
            self.assertTrue("déjà validé" in t, f"{f.name} ne dit pas « déjà validé » : la transmission n'y est pas")

    def test_depenser_reste_borne_par_ce_que_benjamin_a_valide(self):
        t = DEMANDER.read_text()
        paragraphe = section(t, "## 4. Ce qu'on ne demande pas", "## 5.")
        ligne = next(l for l in paragraphe.splitlines() if "dépenser de l'argent" in l)
        self.assertTrue(
            "au-delà de ce que Benjamin a validé" in ligne,
            f"la ligne « dépenser de l'argent » ne borne plus la dépense par ce que Benjamin a validé : {ligne!r}",
        )


if __name__ == "__main__":
    unittest.main()
