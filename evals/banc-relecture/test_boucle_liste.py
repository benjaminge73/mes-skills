"""Tests de la boucle d'amélioration de la liste (`boucle_liste.py`) : décision, plafond, bilan, quota, cron.

Aucun appel réseau, aucun `claude`, aucun `gh` : les dépendances sont remplacées par `Faux`, dont les mesures sont
écrites dans ce fichier, avant l'appel. Les vraies mesures (`rejouer.py`, `juge.py`) ne sont jamais lancées ici.
"""
from __future__ import annotations

import datetime

import pytest

import boucle_liste as bl

AUJOURDHUI = datetime.date(2026, 12, 8)
SHA = "a" * 64
LISTE = "A. CONFORMITÉ\n   1. première remarque\n\nRends le verdict\n"
CANDIDAT = bl.Candidat(categorie="D", ligne="Une remarque retenue que la chaîne a manquée")


def journal(bilan="Bilan de Q2 : 2026-12-07", corps=""):
    entete = "# Journal de test\n\n" + (bilan + "\n\n" if bilan else "")
    return entete + "## Code\n\n### 2026-11-23 — premier passage\n- Ligne candidate : aucune\n" + corps


class Faux:
    """Dépendances de test : le journal est un vrai fichier, les mesures et les PR sont fictives."""

    def __init__(self, chemin, *, mesurer, candidats=(), jeu=True):
        self.chemin = chemin
        self._mesurer = mesurer
        self._candidats = list(candidats)
        self._jeu = jeu
        self.bras_mesures = []
        self.prs = []

    def lire_journal(self):
        return self.chemin.read_text()

    def ecrire_journal(self, texte):
        self.chemin.write_text(texte)

    def jeu_present(self):
        return self._jeu

    def liste_texte(self):
        return LISTE

    def liste_sha(self):
        return SHA

    def liste_avec(self, candidat):
        return LISTE + f"CANDIDAT {candidat.ligne}\n"

    def mesurer(self, liste, bras):
        self.bras_mesures.append(bras)
        return self._mesurer(liste, bras)

    def candidats(self):
        return list(self._candidats)

    def ouvrir_pr(self, candidat, iso):
        self.prs.append(candidat)
        return "https://github.com/benjaminge73/mes-skills/pull/999"


def mesurer_scripte(hausse):
    """Deux bras de base (bruit 0,10 et 0,15, donc bruit A/A 0,05), puis un bras candidat : rappel +0,05, bruit de base + `hausse`."""
    def mesurer(liste, bras):
        if bras.startswith("base-"):
            return bl.Mesure(rappel=0.60, bruit=0.10 if bras == "base-1" else 0.15, cout=1.0)
        return bl.Mesure(rappel=0.65, bruit=0.15 + hausse, cout=1.0)
    return mesurer


def mesurer_quota(liste, bras):
    raise bl.QuotaAtteint("HTTP 402 : out of extra usage, plafond de dépense atteint")


def lancer(tmp_path, argv, *, texte, mesurer, candidats=(), jeu=True):
    chemin = tmp_path / "journal-checklist.md"
    chemin.write_text(texte)
    faux = Faux(chemin, mesurer=mesurer, candidats=candidats, jeu=jeu)
    code = bl.main(argv, deps=faux, aujourdhui=AUJOURDHUI)
    return code, faux, chemin


SECTION = ["--section", "Code"]


def test_candidate_retenue_quand_le_rappel_monte_et_le_bruit_reste_sous_l_aa(tmp_path, capsys):
    # Panne attrapée : une bonne ligne refusée (règle de décision inversée ou seuil trop strict).
    code, faux, chemin = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_scripte(hausse=0.02),
                                candidats=[CANDIDAT])
    assert code == bl.CODE_PR
    assert faux.prs == [CANDIDAT]
    assert "- Décision : retenue" in chemin.read_text()


def test_candidate_refusee_quand_le_bruit_depasse_celui_de_l_aa(tmp_path):
    # Panne attrapée : une ligne qui ajoute du bruit au-delà de l'A/A passerait dans la liste.
    code, faux, chemin = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_scripte(hausse=0.20),
                                candidats=[CANDIDAT])
    assert code == bl.CODE_OK
    assert faux.prs == []
    assert "- Décision : refusée" in chemin.read_text()


def test_cout_cumule_de_cinq_dollars_dans_le_mois_rend_3_sans_rien_mesurer(tmp_path):
    # Panne attrapée : le plafond ne tient pas et la boucle dépense au-delà de 5 dollars dans le mois.
    texte = journal(corps="\n### 2026-12-02 — mesure précédente\n- Coût : 5.000 dollars\n")
    code, faux, _ = lancer(tmp_path, SECTION, texte=texte, mesurer=mesurer_scripte(hausse=0.02),
                           candidats=[CANDIDAT])
    assert code == bl.CODE_PLAFOND
    assert faux.bras_mesures == []


def test_sans_ligne_bilan_de_q2_rend_5_sans_rien_mesurer(tmp_path):
    # Panne attrapée : la liste de relecture bougerait avant le bilan de Q2, pendant l'ombre.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(bilan=None), mesurer=mesurer_scripte(hausse=0.02),
                           candidats=[CANDIDAT])
    assert code == bl.CODE_BILAN
    assert faux.bras_mesures == []


def test_quota_un_seul_message_au_premier_passage_puis_silence_sans_cout(tmp_path, capsys):
    # Panne attrapée : un 402 compté comme dépense, ou un message répété chaque passage dans #arbitrage.
    code1, faux, chemin = lancer(tmp_path, ["--section", "Code", "--cron"], texte=journal(), mesurer=mesurer_quota,
                                 candidats=[CANDIDAT])
    sortie1 = capsys.readouterr().out
    assert code1 == 0
    assert sortie1.count("HTTP 402") == 1
    assert "- Quota : signalé" in chemin.read_text()

    code2 = bl.main(["--section", "Code", "--cron"], deps=faux, aujourdhui=AUJOURDHUI)
    sortie2 = capsys.readouterr().out
    assert code2 == 0
    assert sortie2 == bl.SILENCE + "\n"
    assert "- Coût" not in chemin.read_text()


@pytest.mark.parametrize("texte, mesurer, candidats, code_attendu, silence_en_cron", [
    (journal(), mesurer_scripte(hausse=0.02), [CANDIDAT], bl.CODE_PR, False),
    (journal(), mesurer_scripte(hausse=0.20), [CANDIDAT], bl.CODE_OK, True),
    (journal(corps="\n### 2026-12-02 — mesure\n- Coût : 5.000 dollars\n"), mesurer_scripte(hausse=0.02), [CANDIDAT],
     bl.CODE_PLAFOND, False),
    (journal(bilan=None), mesurer_scripte(hausse=0.02), [CANDIDAT], bl.CODE_BILAN, True),
    (journal(), mesurer_quota, [CANDIDAT], bl.CODE_ERREUR, False),
])
def test_mode_cron_sort_toujours_en_zero_et_se_tait_ou_dit_une_ligne(tmp_path, capsys, texte, mesurer, candidats,
                                                                    code_attendu, silence_en_cron):
    # Panne attrapée : un code non nul en cron fait compter chaque passage comme un échec du superviseur.
    code, _, _ = lancer(tmp_path, SECTION, texte=texte, mesurer=mesurer, candidats=candidats)
    assert code == code_attendu
    capsys.readouterr()

    code_cron, _, _ = lancer(tmp_path, SECTION + ["--cron"], texte=texte, mesurer=mesurer, candidats=candidats)
    sortie = capsys.readouterr().out
    assert code_cron == 0
    if silence_en_cron:
        assert sortie == bl.SILENCE + "\n"
    else:
        assert sortie.strip() and bl.SILENCE not in sortie
