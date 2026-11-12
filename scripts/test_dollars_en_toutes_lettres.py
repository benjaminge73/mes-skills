"""Garde : la ligne « Coût estimé » ne devient pas une formule dans Notion.

Constaté le 2026-11-12 sur deux pages de plan : une ligne recopiée du barème
(« plan seul, médiane 14 $ ; exécution seule, médiane 28 $ ») porte deux signes
« $ » dans le même paragraphe, et Notion prend ce qui est entre eux pour une
formule en ligne (du LaTeX) : les chiffres et le texte du milieu disparaissent
dans une équation. Ce test lit les consignes qui font écrire cette ligne : elles
doivent écrire « dollars » en toutes lettres, en donner un exemple sans signe
« $ », et le piège doit être noté dans ``ecrire-dans-notion.md``.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SKILLS = RACINE / "plugins" / "plans-notion" / "skills"
CONSIGNE = SKILLS / "plan-notion" / "chapitres-questions-execution.md"
BAREME = SKILLS / "_partage" / "cout-des-plans.md"
PIEGES = SKILLS / "_partage" / "ecrire-dans-notion.md"

# Un exemple de la ligne, écrit en code inline : `Coût estimé : …`.
EXEMPLE = re.compile(r"`(Coût estimé :[^`]+)`")
# Un signe « $ » que Notion lit comme borne de formule : ni échappé (« \$ »), ni
# celui d'une variable du plugin (« ${CLAUDE_PLUGIN_ROOT} »).
DOLLAR_NU = re.compile(r"(?<!\\)\$(?!\{)")


def paragraphe(texte: str, debut: str) -> str:
    """Le paragraphe (jusqu'à la ligne vide) qui commence par ``debut``."""
    i = texte.index(debut)
    fin = texte.find("\n\n", i)
    return texte[i:] if fin < 0 else texte[i:fin]


def exemples(texte: str) -> list[str]:
    return EXEMPLE.findall(texte)


class DollarsEnToutesLettres(unittest.TestCase):
    def test_la_consigne_ecrit_dollars_en_toutes_lettres_avec_un_exemple(self):
        texte = CONSIGNE.read_text(encoding="utf-8")
        consigne = paragraphe(texte, "**En tête du chapitre, avant le tableau, une ligne `Coût estimé")
        self.assertIn("dollars", consigne)
        self.assertIn("toutes lettres", consigne)
        ex = exemples(consigne)
        self.assertTrue(ex, "la consigne ne donne aucun exemple `Coût estimé : …`")
        for e in ex:
            self.assertIn("dollars", e)
            self.assertNotRegex(e, DOLLAR_NU)

    def test_le_bareme_donne_l_exemple_sans_signe_dollar(self):
        texte = BAREME.read_text(encoding="utf-8")
        lecture = texte[texte.index("## Lire les deux lignes de coût"):]
        ex = exemples(lecture)
        self.assertTrue(ex, "cout-des-plans.md ne donne aucun exemple `Coût estimé : …`")
        for e in ex:
            self.assertIn("dollars", e)
            self.assertNotRegex(e, DOLLAR_NU)

    def test_aucun_exemple_de_la_ligne_ne_porte_de_signe_dollar_nu(self):
        # Partout dans le plugin : un exemple qui reviendrait au « $ » refait la formule.
        for f in sorted(SKILLS.rglob("*.md")):
            for e in exemples(f.read_text(encoding="utf-8")):
                with self.subTest(fichier=f.relative_to(RACINE).as_posix(), exemple=e):
                    self.assertNotRegex(e, DOLLAR_NU)

    def test_le_piege_est_note_dans_ecrire_dans_notion(self):
        texte = PIEGES.read_text(encoding="utf-8")
        self.assertRegex(texte, r"(?m)^## Sept pièges de l'API Notion")
        piege = texte[texte.index("7. **"):]
        piege = piege[:piege.index("\n\n")]
        for mot in ("formule", "dollars", r"\$"):
            self.assertIn(mot, piege)


if __name__ == "__main__":
    unittest.main()
