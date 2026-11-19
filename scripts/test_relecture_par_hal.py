"""Garde : les règles de la relecture par Hal tiennent dans les fichiers du skill.

Le texte est lu, jamais exécuté. Chaque cas vérifie une règle écrite là où le
skill la fait appliquer : le cadrage, les deux tours, la case non cochée par Hal,
le repli, la section d'avis, les renvois, la commande ``relire``, la pré-lecture,
la lecture seule et la session Remote Control. Une étape qui réécrit ce texte et
oublie une règle casse ici, pas en plein plan.
"""
from __future__ import annotations

import pathlib
import re
import unittest

SK = pathlib.Path(__file__).resolve().parent.parent / "plugins/plans-notion/skills"
RELECTURE = SK / "_partage/relecture-par-hal.md"
DEMANDER = SK / "_partage/demander-a-hal.md"
PLAN_MAITRE = SK / "plan-notion/plan-maitre.md"
RENVOIS = (SK / "plan-notion/SKILL.md", SK / "plan-notion/enquete.md")
CHEMIN_RENVOI = "${CLAUDE_PLUGIN_ROOT}/skills/_partage/relecture-par-hal.md"


def lire(fichier: pathlib.Path) -> str:
    """Le texte du fichier ; une absence devient un échec lisible, pas une erreur d'import."""
    if not fichier.is_file():
        raise AssertionError(
            f"{fichier.relative_to(SK)} n'existe pas : la relecture par Hal n'est pas encore écrite"
        )
    return fichier.read_text(encoding="utf-8")


def phrases(texte: str) -> list[str]:
    """Découpe en phrases (ponctuation forte ou ligne vide), espaces normalisés."""
    morceaux = re.split(r"\n\s*\n|(?<=[.!?;])\s+", texte)
    return [" ".join(m.split()) for m in morceaux if m.strip()]


def phrase_avec(texte: str, *motifs: str) -> bool:
    """Vrai si une même phrase porte tous les motifs (insensible à la casse)."""
    return any(all(re.search(m, p, re.IGNORECASE) for m in motifs) for p in phrases(texte))


class RelectureParHal(unittest.TestCase):
    def test_a_cadrage_entre_enquete_et_questions(self):
        t = lire(RELECTURE)
        self.assertTrue(re.search(r"cadrage\s+avec\s+hal", t, re.IGNORECASE), "relecture-par-hal.md ne nomme pas le cadrage avec Hal")
        self.assertTrue(
            phrase_avec(t, r"\bHal\b", r"apr[èe]s[^.;!?]*enqu[êe]te[^.;!?]*avant[^.;!?]*questions?"),
            "relecture-par-hal.md ne dit pas que le cadrage avec Hal vient après l'enquête et avant les questions",
        )

    def test_b_deux_tours_au_plus(self):
        t = lire(RELECTURE)
        self.assertTrue(
            re.search(r"\bdeux\s+tours\s+au\s+plus\b|\bjamais\s+plus\s+de\s+deux\s+tours\b", t, re.IGNORECASE),
            "relecture-par-hal.md ne borne pas la relecture à deux tours au plus",
        )

    def test_c_hal_ne_coche_aucune_case(self):
        t = lire(RELECTURE)
        self.assertTrue(
            phrase_avec(t, r"\bHal\b", r"\bcase", r"ne\s+coch|aucune?\s+case|jamais\s+(de\s+|une\s+)?case|ni\s+coch|coch\w*\s+(aucune|jamais|pas)"),
            "relecture-par-hal.md ne dit pas que Hal ne coche aucune case",
        )

    def test_d_repli_second_essai_puis_avis_non_rendu(self):
        t = lire(RELECTURE)
        self.assertTrue(
            re.search(r"(second|deuxi[èe]me|nouvel|une\s+seconde)\s+(essai|tentative|appel)", t, re.IGNORECASE),
            "relecture-par-hal.md ne prévoit pas un second essai quand Hal ne répond pas",
        )
        self.assertTrue(re.search(r"avis\s+non\s+rendu", t, re.IGNORECASE), "relecture-par-hal.md ne dit pas « Avis non rendu » en repli")
        self.assertTrue(
            phrase_avec(
                t, r"\bavis\b",
                r"\bne\s+(?:s['’]|l['’])?(?:invente|fabrique|improvise)\w*\s+jamais"
                r"|\bjamais\b[^.;!?]*\b(?:invent|fabriqu|improvis)\w*"
                r"|\bsans\s+(?:invent|fabriqu|improvis)\w*",
            ),
            "relecture-par-hal.md ne dit pas qu'un avis ne s'invente pas quand Hal ne répond pas",
        )

    def test_e_section_avis_de_hal(self):
        t = lire(RELECTURE)
        self.assertTrue(re.search(r"\bavis\s+de\s+hal\b", t, re.IGNORECASE), "relecture-par-hal.md ne nomme pas la section « Avis de Hal »")

    def test_f_renvoi_depuis_skill_et_enquete(self):
        for fichier in RENVOIS:
            self.assertTrue(CHEMIN_RENVOI in lire(fichier), f"{fichier.relative_to(SK)} ne renvoie pas à relecture-par-hal.md")

    def test_g_commande_relire(self):
        self.assertTrue(
            re.search(r"demander_a_hal\.py\s+relire\b", lire(DEMANDER), re.IGNORECASE),
            "demander-a-hal.md ne documente pas la commande « demander_a_hal.py relire »",
        )

    def test_h_maitre_relu_apres_ses_lecteurs(self):
        t = lire(PLAN_MAITRE)
        self.assertTrue(
            phrase_avec(t, r"relir", r"ma[iî]tre", r"apr[èe]s[^.;!?]*lecteur"),
            "plan-maitre.md ne dit pas de relire le maître après les fiches lecteur de son lot",
        )
        self.assertTrue(
            phrase_avec(t, r"recalc", r"statut", r"relu|relecture", r"sans|une\s+fois"),
            "plan-maitre.md ne dit pas qu'un maître relu une fois passe ses recalculs de Statut sans nouvelle relecture",
        )

    def test_i_prelecture_des_plans_ouverts_par_le_lecteur(self):
        t = lire(RELECTURE)
        self.assertTrue(
            phrase_avec(t, r"pr[ée][-\s]?lectur", r"\blecteur\b"),
            "relecture-par-hal.md ne dit pas que l'agent lecteur pré-lit les plans ouverts",
        )

    def test_j_lecture_seule_et_commandes_jouees_recopiees(self):
        t = lire(RELECTURE)
        self.assertTrue(re.search(r"lecture\s+seule", t, re.IGNORECASE), "relecture-par-hal.md ne dit pas que Hal lit le VPS en lecture seule")
        self.assertTrue(re.search(r"commandes\s+jou[ée]es", t, re.IGNORECASE), "relecture-par-hal.md n'a pas la rubrique « Commandes jouées par Hal »")
        self.assertTrue(
            phrase_avec(t, r"commandes", r"\bavis\b", r"recopi|reprise|reprend|figur|inscri"),
            "relecture-par-hal.md ne dit pas que les commandes de Hal sont recopiées dans l'avis",
        )

    def test_k_remote_control_depuis_le_mac_est_le_vps(self):
        t = lire(RELECTURE)
        self.assertTrue(
            phrase_avec(t, r"Remote\s+Control", r"\bVPS\b", r"\bMac\b"),
            "relecture-par-hal.md ne dit pas qu'une session ouverte depuis le Mac par Remote Control est une session du VPS",
        )


if __name__ == "__main__":
    unittest.main()
