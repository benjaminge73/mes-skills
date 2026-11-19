"""Tests de la surface d'outils du sondeur : il ne lit la production que par deux outils Vercel.

Trois gardes, une panne nommée chacun :
(a) les seuls outils MCP du sondeur sont les deux lectures Vercel (erreurs, journaux) ;
(b) aucun autre outil Vercel, et aucun outil Supabase, ne s'ajoute à sa liste ;
(c) le corps nomme ces deux outils et porte la règle de masquage (« ni valeur sensible
    ni donnée personnelle »), sans quoi la sortie d'une lecture de production sort brute.

La liste se lit par ``check_skills.lire_frontmatter``, le même lecteur que la garde de
forme : ce que la CI voit est ce que Claude Code reçoit. Lancé par
``python3 -m unittest scripts.test_sondeur_outils`` ou par la découverte de ``ci_locale.sh``.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_skills  # noqa: E402

SONDEUR = RACINE / "plugins" / "plans-notion" / "agents" / "sondeur.md"
LECTURES_VERCEL = {
    "mcp__claude_ai_Vercel__get_runtime_errors",
    "mcp__claude_ai_Vercel__get_runtime_logs",
}
REGLE_DE_MASQUAGE = "ni valeur sensible ni donnée personnelle"


def _outils(champs: dict) -> list[str]:
    valeur = champs.get("tools", [])
    return [valeur] if isinstance(valeur, str) else list(valeur)


def _corps(texte: str) -> str:
    lignes = texte.splitlines()
    fin = next(i for i in range(1, len(lignes)) if lignes[i].strip() == "---")
    return "\n".join(lignes[fin + 1:])


class SurfaceDOutilsDuSondeur(unittest.TestCase):
    def setUp(self) -> None:
        self.texte = SONDEUR.read_text(encoding="utf-8")
        self.outils = _outils(check_skills.lire_frontmatter(self.texte))

    def test_le_sondeur_ne_lit_la_production_que_par_les_deux_lectures_vercel(self) -> None:
        mcp = {outil for outil in self.outils if outil.startswith("mcp__")}
        self.assertEqual(
            mcp, LECTURES_VERCEL,
            "le sondeur doit lire la production par exactement ces deux outils Vercel de lecture")

    def test_aucun_outil_vercel_d_ecriture_ni_supabase_dans_sa_liste(self) -> None:
        suspects = [
            outil for outil in self.outils
            if (("vercel" in outil.lower() and outil not in LECTURES_VERCEL)
                or "supabase" in outil.lower())
        ]
        self.assertEqual(
            suspects, [],
            "un outil Vercel autre que les deux lectures, ou un outil Supabase, est dans la liste "
            "du sondeur : il n'a rien à faire dans une sonde en lecture")

    def test_le_corps_nomme_les_deux_outils_et_la_regle_de_masquage(self) -> None:
        corps = _corps(self.texte)
        for outil in sorted(LECTURES_VERCEL):
            with self.subTest(outil=outil):
                self.assertIn(outil, corps, "le corps ne nomme pas cet outil de lecture")
        self.assertIn(
            REGLE_DE_MASQUAGE, corps,
            "le corps ne porte pas la règle de masquage : une valeur sensible ou une donnée "
            "personnelle de la production sortirait brute dans le rapport")


if __name__ == "__main__":
    unittest.main()
