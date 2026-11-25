"""Tests de la boucle d'amélioration de la liste (`boucle_liste.py`) : décision, plafond, bilan, quota, cron, PR.

Aucun appel réseau, aucun `claude`, aucun `gh`, aucun `git push` : les dépendances sont remplacées par `Faux` (mesures,
PR, état des PR) ou `ShFaux` (le shell d'`ouvrir_pr`). Les vraies mesures (`rejouer.py`, `juge.py`) ne sont jamais lancées
ici : quand un test touche au chemin réel, `_lancer` est remplacé par un faux avant toute construction.
"""
from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path

import pytest

import boucle_liste as bl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from garde_doc_pr import verifier_doc  # noqa: E402

AUJOURDHUI = datetime.date(2026, 12, 8)
MOIS = "2026-12"
SHA = "a" * 64
LISTE = "A. CONFORMITÉ\n   1. première remarque\n\nRends le verdict\n"
CANDIDAT = bl.Candidat(categorie="D", ligne="Une remarque retenue que la chaîne a manquée")
SECTION = ["--section", "Code"]
ENQUETE = "Enquête"
SECTION_ENQUETE = ["--section", ENQUETE]
CANDIDAT_ENQUETE = bl.Candidat(categorie="", ligne="Une case d'enquête que l'enquêteur a manquée")


def journal(bilan="Bilan de Q2 : 2026-12-07", corps=""):
    entete = "# Journal de test\n\n" + (bilan + "\n\n" if bilan else "")
    return entete + "## Code\n\n### 2026-11-23 — premier passage\n- Ligne candidate : aucune\n" + corps


def journal_enquete(bilan="Bilan de Q2 : 2026-12-07"):
    """Un journal à deux sections : « Code » et « Enquête », chacune avec son premier passage sans candidat."""
    entete = "# Journal de test\n\n" + (bilan + "\n\n" if bilan else "")
    return (entete + "## Code\n\n### 2026-11-23 — premier passage\n- Ligne candidate : aucune\n\n"
            "## Enquête\n\n### 2026-11-23 — premier passage\n- Ligne candidate : aucune\n")


class Faux:
    """Dépendances de test : le journal est un vrai fichier ; mesures, état, PR et état des PR sont fictifs, en mémoire.

    `section` est reçu par chaque méthode qui en a besoin ; `sections_mesurees` note la section de chaque mesure, parallèle
    à `bras_mesures`. Les candidats d'enquête sont ceux de `candidats_enquete`, les autres ceux de « Code »."""

    def __init__(self, chemin, *, mesurer, candidats=(), candidats_enquete=(), jeu=True, pr_echoue=False):
        self.chemin = chemin
        self._mesurer = mesurer
        self._candidats = list(candidats)
        self._candidats_enquete = list(candidats_enquete)
        self._jeu = jeu
        self.pr_echoue = pr_echoue
        self.bras_mesures = []
        self.sections_mesurees = []
        self.budgets = []
        self.prs = []
        self.etats = {}
        self.prs_etat = {}
        self.consultes = []

    def lire_journal(self):
        return self.chemin.read_text()

    def ecrire_journal(self, texte):
        self.chemin.write_text(texte)

    def lire_etat(self, section):
        return dict(self.etats.get(section, {}))

    def ecrire_etat(self, section, etat):
        self.etats[section] = dict(etat)

    def etats_tous(self):
        return [dict(e) for e in self.etats.values()]

    def jeu_present(self):
        return self._jeu

    def liste_texte(self, section=None):
        return LISTE

    def liste_sha(self, section=None):
        return SHA

    def liste_avec(self, candidat, section=None):
        return LISTE + f"CANDIDAT {candidat.ligne}\n"

    def mesurer(self, liste, bras, budget, section=None):
        self.bras_mesures.append(bras)
        self.sections_mesurees.append(section or "Code")
        self.budgets.append(budget)
        return self._mesurer(liste, bras)

    def candidats(self, section=None):
        return list(self._candidats_enquete if section == ENQUETE else self._candidats)

    def ouvrir_pr(self, candidat, iso, section=None):
        if self.pr_echoue:
            raise bl.Souci("gh pr create en échec", reelle=True)
        self.prs.append(candidat)
        return "https://github.com/benjaminge73/mes-skills/pull/999"

    def etat_pr(self, url):
        self.consultes.append(url)
        return self.prs_etat.get(url, {"state": "OPEN", "statusCheckRollup": []})


def mesurer_scripte(hausse):
    """Deux bras de base (bruit 0,10 et 0,15, donc bruit A/A 0,05), puis un bras candidat : rappel +0,05, bruit de base + `hausse`."""
    def mesurer(liste, bras):
        if bras.startswith("base-"):
            return bl.Mesure(rappel=0.60, bruit=0.10 if bras.endswith("-1") else 0.15, cout=1.0)
        return bl.Mesure(rappel=0.65, bruit=0.15 + hausse, cout=1.0)
    return mesurer


def mesurer_exacte(*, rappel=0.65, bruit=0.75, cout=1.0):
    """Base à rappel 0,60, bruits 0,25 et 0,50 (bruit A/A exact : 0,25). Nombres exacts en binaire : pas d'arrondi."""
    def mesurer(liste, bras):
        if bras.startswith("base-"):
            return bl.Mesure(rappel=0.60, bruit=0.25 if bras.endswith("-1") else 0.50, cout=1.0)
        return bl.Mesure(rappel=rappel, bruit=bruit, cout=cout)
    return mesurer


def mesurer_quota(liste, bras):
    raise bl.QuotaAtteint("HTTP 402 : out of extra usage, plafond de dépense atteint")


def lancer(tmp_path, argv, *, texte, mesurer, candidats=(), candidats_enquete=(), jeu=True, pr_echoue=False, etat=None,
           etats=None, prs=None):
    chemin = tmp_path / "journal-checklist.md"
    chemin.write_text(texte)
    faux = Faux(chemin, mesurer=mesurer, candidats=candidats, candidats_enquete=candidats_enquete, jeu=jeu,
                pr_echoue=pr_echoue)
    if etat is not None:
        faux.etats["Code"] = etat
    faux.etats.update(etats or {})
    faux.prs_etat.update(prs or {})
    code = bl.main(argv, deps=faux, aujourdhui=AUJOURDHUI)
    return code, faux, chemin


def cands(faux):
    return sum(1 for b in faux.bras_mesures if b.startswith("cand-"))


# --- Décision : bornes, plafond, quota -----------------------------------------------------------------------------

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


@pytest.mark.parametrize("bruit_candidat, decision, code_attendu", [
    # Borne incluse : une hausse de bruit égale à celle de l'A/A (0,75 - 0,50 = 0,25) passe.
    (0.75, "retenue", bl.CODE_PR),
    # Au-dessus : 0,8125 - 0,50 = 0,3125 > 0,25, refusée.
    (0.8125, "refusée", bl.CODE_OK),
])
def test_borne_du_bruit_hausse_egale_a_l_aa_passe_et_au_dessus_non(tmp_path, bruit_candidat, decision, code_attendu):
    # Panne attrapée : une borne mal placée (< au lieu de <=) refuse une ligne qui ne dépasse pas le bruit de l'A/A.
    code, faux, chemin = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(bruit=bruit_candidat),
                                candidats=[CANDIDAT])
    assert code == code_attendu
    assert f"- Décision : {decision}" in chemin.read_text()


def test_gain_nul_n_est_pas_retenu_meme_si_le_bruit_reste_sous_l_aa(tmp_path):
    # Panne attrapée : une ligne qui ne fait pas monter le rappel (gain nul) entrerait parce que « gain > 0 »
    # aurait été écrit « gain >= 0 ».
    code, faux, chemin = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(rappel=0.60, bruit=0.50),
                                candidats=[CANDIDAT])
    assert code == bl.CODE_OK
    assert faux.prs == []
    assert "- Décision : refusée" in chemin.read_text()


def test_plafond_atteint_entre_deux_bras_arrete_avant_le_second_candidat(tmp_path):
    # Panne attrapée : le plafond n'est vérifié qu'au début de la boucle, et un second bras part alors que le mois
    # est dépassé. Bases 1 + 1 = 2 dollars ; le premier candidat coûte 3 : 5 dollars atteints, le second ne part pas.
    autre = bl.Candidat(categorie="E", ligne="Une deuxième remarque retenue")
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(bruit=0.9, cout=3.0),
                           candidats=[CANDIDAT, autre])
    assert code == bl.CODE_PLAFOND
    assert cands(faux) == 1
    assert faux.prs == []


def test_cout_cumule_de_cinq_dollars_dans_le_mois_rend_3_sans_rien_mesurer(tmp_path):
    # Panne attrapée : le plafond ne tient pas et la boucle dépense au-delà de 5 dollars dans le mois.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_scripte(hausse=0.02),
                           candidats=[CANDIDAT], etat={"couts": {MOIS: 5.0}})
    assert code == bl.CODE_PLAFOND
    assert faux.bras_mesures == []


@pytest.mark.parametrize("argv_plus, budget_attendu", [
    ([], 3.0),                                  # plafond 5, déjà 2 dépensés ce mois : budget 3
    (["--plafond-mois", "4"], 2.0),             # plafond 4 passé en option : budget 2
])
def test_budget_passe_a_rejouer_est_le_plafond_moins_le_cout_du_mois(tmp_path, argv_plus, budget_attendu):
    # Panne attrapée : rejouer.py reçoit le plafond fixe de 5 dollars au lieu de ce qui reste du mois.
    # Une mesure complète connue (1 dollar) est déclarée : sans elle, le défaut prudent exige le plafond entier.
    code, faux, _ = lancer(tmp_path, SECTION + argv_plus, texte=journal(), mesurer=mesurer_scripte(hausse=0.02),
                           candidats=[CANDIDAT], etat={"couts": {MOIS: 2.0}, "cout_mesure": 1.0})
    assert faux.budgets[0] == pytest.approx(budget_attendu)


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
    assert faux.etats["Code"]["quota"] == "signalé"
    assert "- Quota" not in chemin.read_text()

    code2 = bl.main(["--section", "Code", "--cron"], deps=faux, aujourdhui=AUJOURDHUI)
    sortie2 = capsys.readouterr().out
    assert code2 == 0
    assert sortie2 == bl.SILENCE + "\n"
    assert "- Coût" not in chemin.read_text()


@pytest.mark.parametrize("texte, mesurer, candidats, etat, code_attendu, silence_en_cron", [
    (journal(), mesurer_scripte(hausse=0.02), [CANDIDAT], None, bl.CODE_PR, False),
    (journal(), mesurer_scripte(hausse=0.20), [CANDIDAT], None, bl.CODE_OK, True),
    (journal(), mesurer_scripte(hausse=0.02), [CANDIDAT], {"couts": {MOIS: 5.0}}, bl.CODE_PLAFOND, False),
    (journal(bilan=None), mesurer_scripte(hausse=0.02), [CANDIDAT], None, bl.CODE_BILAN, True),
    (journal(), mesurer_quota, [CANDIDAT], None, bl.CODE_ERREUR, False),
])
def test_mode_cron_sort_en_zero_et_se_tait_ou_dit_une_ligne(tmp_path, capsys, texte, mesurer, candidats, etat,
                                                            code_attendu, silence_en_cron):
    # Panne attrapée : un code non nul en cron fait compter chaque passage comme un échec du superviseur.
    code, _, _ = lancer(tmp_path, SECTION, texte=texte, mesurer=mesurer, candidats=candidats, etat=etat)
    assert code == code_attendu
    capsys.readouterr()

    code_cron, _, _ = lancer(tmp_path, SECTION + ["--cron"], texte=texte, mesurer=mesurer, candidats=candidats,
                             etat=etat)
    sortie = capsys.readouterr().out
    assert code_cron == 0
    if silence_en_cron:
        assert sortie == bl.SILENCE + "\n"
    else:
        assert sortie.strip() and bl.SILENCE not in sortie


@pytest.mark.parametrize("kwargs, code_attendu", [
    (dict(jeu=False), 1),                 # jeu de validation absent : erreur réelle, visible au superviseur
    (dict(pr_echoue=True), 1),            # gh en échec : erreur réelle
    (dict(), 0),                          # quota : pas une erreur réelle, rien ne se répare
])
def test_cron_ne_rend_1_que_pour_une_erreur_reelle(tmp_path, capsys, kwargs, code_attendu):
    # Panne attrapée : un superviseur qui ne voit jamais une vraie panne (cron toujours à 0) ou qui répare un quota.
    mesurer = mesurer_quota if not kwargs else mesurer_exacte()
    code, _, _ = lancer(tmp_path, SECTION + ["--cron"], texte=journal(), mesurer=mesurer, candidats=[CANDIDAT],
                        **kwargs)
    sortie = capsys.readouterr().out
    assert code == code_attendu
    assert "Traceback" not in sortie


# --- Section « Enquête » : même boucle et même plafond, sans bilan de Q2 ni liste de relecture ----------------------------

def test_enquete_au_cumul_de_cinq_dollars_du_mois_rend_3_sans_rien_mesurer(tmp_path):
    # Panne attrapée : le plafond n'est pas commun aux sections : une case d'enquête part alors que la relecture a déjà
    # dépensé les 5 dollars du mois.
    code, faux, _ = lancer(tmp_path, SECTION_ENQUETE, texte=journal_enquete(), mesurer=mesurer_scripte(hausse=0.02),
                           candidats_enquete=[CANDIDAT_ENQUETE], etats={"Code": {"couts": {MOIS: 5.0}}})
    assert code == bl.CODE_PLAFOND
    assert faux.bras_mesures == []


def test_enquete_ne_touche_pas_la_section_code(tmp_path):
    # Panne attrapée : une mesure d'enquête qui lit la liste de relecture, compte dans son état, ou écrit dans son journal.
    avant = journal_enquete()
    # Cumul nul : « Enquête » n'a pas de mesure connue, donc son budget exige le plafond entier (règle de P1).
    etat_code = {"couts": {MOIS: 0.0}, "cout_mesure": 1.0}
    code, faux, chemin = lancer(tmp_path, SECTION_ENQUETE, texte=avant, mesurer=mesurer_scripte(hausse=0.02),
                                candidats=[CANDIDAT], candidats_enquete=[CANDIDAT_ENQUETE], etats={"Code": etat_code})
    assert code == bl.CODE_PR
    assert "Code" not in faux.sections_mesurees
    assert faux.prs == [CANDIDAT_ENQUETE]
    assert faux.etats["Code"] == etat_code
    assert bl.lignes_section(chemin.read_text(), "Code") == bl.lignes_section(avant, "Code")


def test_enquete_sans_ligne_bilan_de_q2_mesure_et_ne_rend_pas_5(tmp_path):
    # Panne attrapée : la garde « Bilan de Q2 », faite pour la liste de relecture, bloque aussi l'enquête (code 5).
    code, faux, _ = lancer(tmp_path, SECTION_ENQUETE, texte=journal_enquete(bilan=None),
                           mesurer=mesurer_scripte(hausse=0.02), candidats_enquete=[CANDIDAT_ENQUETE])
    assert code != bl.CODE_BILAN
    assert code == bl.CODE_PR
    assert faux.prs == [CANDIDAT_ENQUETE]


def test_enquete_quota_402_un_seul_message_puis_silence_jusqu_au_succes(tmp_path, capsys):
    # Panne attrapée : un 402 de l'enquête répété à chaque passage dans #arbitrage, ou compté comme une dépense.
    code1, faux, chemin = lancer(tmp_path, SECTION_ENQUETE + ["--cron"], texte=journal_enquete(), mesurer=mesurer_quota,
                                 candidats_enquete=[CANDIDAT_ENQUETE])
    sortie1 = capsys.readouterr().out
    assert code1 == 0
    assert sortie1.count("HTTP 402") == 1
    assert faux.etats[ENQUETE]["quota"] == "signalé"

    code2 = bl.main(SECTION_ENQUETE + ["--cron"], deps=faux, aujourdhui=AUJOURDHUI)
    sortie2 = capsys.readouterr().out
    assert code2 == 0
    assert sortie2 == bl.SILENCE + "\n"
    assert "- Coût" not in chemin.read_text()


def test_enquete_sans_candidat_ne_mesure_pas_la_base_et_se_tait(tmp_path, capsys):
    # Panne attrapée : sans case à mesurer, la base d'enquête part quand même, et chaque passage sort en erreur.
    code, faux, _ = lancer(tmp_path, SECTION_ENQUETE + ["--cron"], texte=journal_enquete(),
                           mesurer=mesurer_scripte(hausse=0.02), candidats_enquete=())
    sortie = capsys.readouterr().out
    assert code == 0
    assert sortie == bl.SILENCE + "\n"
    assert faux.bras_mesures == []


def test_enquete_dry_run_rend_0_et_ne_mesure_rien(tmp_path):
    # Panne attrapée : le dry-run d'enquête lance une mesure, ou rend une erreur sur une section pourtant saine.
    code, faux, _ = lancer(tmp_path, SECTION_ENQUETE + ["--dry-run"], texte=journal_enquete(),
                           mesurer=mesurer_scripte(hausse=0.02), candidats_enquete=[CANDIDAT_ENQUETE])
    assert code == bl.CODE_OK
    assert faux.bras_mesures == []
    assert faux.prs == []


def test_mesure_d_enquete_non_branchee_ne_lance_rien(tmp_path):
    # Panne attrapée : une case d'enquête mesurée par le banc de relecture (rejouer.py, jeu de validation « Code ») au
    # lieu de enquete.py : une dépense sur le mauvais jeu, comptée sous le mauvais nom.
    appels = []

    def sh(argv, cwd=None, env=None):
        appels.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    dep = bl.Dependances(journal=tmp_path / "j.md", sh=sh)
    with pytest.raises(bl.Souci) as e:
        dep.mesurer(LISTE, "cand-x", 5.0, ENQUETE)
    assert e.value.reelle
    assert appels == []


def test_mesure_en_echec_journalise_son_cout_avant_de_lever(tmp_path):
    # Panne attrapée : un juge en échec après 2 dollars de rejeu ne compte rien, et le plafond est sous-évalué.
    def mesurer_echec(liste, bras):
        raise bl.Souci("juge.py en échec", cout=2.0)

    code, faux, chemin = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_echec, candidats=[CANDIDAT])
    assert code == bl.CODE_ERREUR
    assert faux.etats["Code"]["couts"][MOIS] == pytest.approx(2.0)
    assert "- Souci : juge.py en échec" in chemin.read_text()


def test_pr_en_echec_est_notee_puis_reessayee_sans_remesure(tmp_path):
    # Panne attrapée : une ligne dont la PR a échoué marquée « décidée » à tort, ou remesurée à chaque passage.
    code1, faux, chemin = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=[CANDIDAT],
                                 pr_echoue=True)
    assert code1 == bl.CODE_ERREUR
    assert "- PR : échec" in chemin.read_text()
    faux.pr_echoue = False
    code2 = bl.main(SECTION, deps=faux, aujourdhui=AUJOURDHUI)
    assert code2 == bl.CODE_PR
    assert faux.prs == [CANDIDAT]
    assert cands(faux) == 1


def test_candidat_refuse_n_est_pas_remesure_au_passage_suivant(tmp_path):
    # Panne attrapée : chaque passage repaierait la mesure d'une ligne déjà refusée.
    code1, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(bruit=0.9), candidats=[CANDIDAT])
    assert code1 == bl.CODE_OK
    code2 = bl.main(SECTION, deps=faux, aujourdhui=AUJOURDHUI)
    assert code2 == bl.CODE_OK
    assert cands(faux) == 1


# --- Dépendances réelles : état, journal tronqué, candidats --------------------------------------------------------

@pytest.fixture
def donnees(tmp_path, monkeypatch):
    """Un dossier de données de test (jeu de validation présent), à la place de ~/.local/share/banc-relecture."""
    d = tmp_path / "donnees"
    d.mkdir()
    (d / bl.REF_VALIDATION).write_text("[]")
    (d / bl.CAS_VALIDATION).write_text("[]")
    monkeypatch.setattr(bl.banc, "DONNEES", d)
    return d


def test_retenues_tronquees_en_cron_sortent_en_une_ligne_et_0(tmp_path, donnees, capsys):
    # Panne attrapée : un fichier de tri tronqué fait sortir une trace Python dans le cron, donc un passage en échec.
    (donnees / "ombres").mkdir()
    (donnees / "ombres" / "retenues-e1.json").write_text('{"remarques": [')
    chemin = tmp_path / "journal.md"
    chemin.write_text(journal())

    code = bl.main(SECTION + ["--cron", "--dry-run"], deps=bl.Dependances(journal=chemin), aujourdhui=AUJOURDHUI)

    sortie = capsys.readouterr().out
    assert code == 0
    assert "Traceback" not in sortie
    assert len(sortie.strip().splitlines()) == 1


def test_etat_corrompu_en_cron_sort_1_en_une_ligne(tmp_path, donnees, capsys):
    # Panne attrapée : un état de coût illisible remis à zéro en silence, et le plafond ne protège plus rien.
    (donnees / "etat-boucle-code.json").write_text("{")
    chemin = tmp_path / "journal.md"
    chemin.write_text(journal())

    code = bl.main(SECTION + ["--cron"], deps=bl.Dependances(journal=chemin), aujourdhui=AUJOURDHUI)

    sortie = capsys.readouterr().out
    assert code == 1
    assert "Traceback" not in sortie
    assert len(sortie.strip().splitlines()) == 1


def test_candidats_lit_la_categorie_des_remarques_vues_deux_fois(donnees):
    # Panne attrapée : la catégorie d'une remarque n'arrive jamais à la boucle, et la ligne ne tombe pas dans la bonne lettre.
    ombres = donnees / "ombres"
    ombres.mkdir()
    repetee = {"origine": "opus", "verdict": "retenue", "categorie": "D", "gravite": "autre",
               "resume": "Une remarque répétée"}
    unique = {"origine": "opus", "verdict": "retenue", "categorie": "C", "gravite": "autre",
              "resume": "Vue une seule fois"}
    (ombres / "retenues-e1.json").write_text(json.dumps({"id": "e1", "remarques": [repetee, unique]}))
    (ombres / "retenues-e2.json").write_text(json.dumps({"id": "e2", "remarques": [repetee]}))

    assert bl.Dependances(journal=donnees / "j.md").candidats() == [bl.Candidat("D", "Une remarque répétée")]


# --- Ouverture de la PR : le shell est remplacé, rien ne sort du poste ----------------------------------------------

LISTE_FIXTURE = "A. CONFORMITÉ\n   1. première\n\nD. ROBUSTESSE\n   1. troisième\n\nRends le verdict\n"
PLUGIN_FIXTURE = '{\n  "name": "plans-notion",\n  "version": "0.76.1"\n}\n'
URL_PR = "https://github.com/benjaminge73/mes-skills/pull/999"


def contient(argv, morceau):
    return any(morceau in a for a in argv)


class ShFaux:
    """Remplace le shell d'`ouvrir_pr` : aucun git, gh ni script réel. Le worktree « créé » reçoit les fichiers
    d'origine ; les gardes et `gh` répondent selon le réglage du test ; le commit enregistre ce qu'il contient."""

    def __init__(self, *, garde=0, evals=0, gh=0, veille=0):
        self.garde, self.evals, self.gh, self.veille = garde, evals, gh, veille
        self.appels = []
        self.au_commit = None

    def __call__(self, argv, cwd=None, env=None):
        argv = [str(a) for a in argv]
        self.appels.append(argv)
        rc, sortie = 0, ""
        if "worktree" in argv and "add" in argv:
            chemin = Path(argv[-2])
            for rel, texte in ((bl.LISTE_REL, LISTE_FIXTURE), (bl.PLUGIN_JSON, PLUGIN_FIXTURE), (bl.JOURNAL_REL, "")):
                (chemin / rel).parent.mkdir(parents=True, exist_ok=True)
                (chemin / rel).write_text(texte)
        elif contient(argv, "garde_doc_pr.py"):
            rc = self.garde
        elif contient(argv, "evals_selection.py"):
            rc = self.evals
        elif contient(argv, "check_veille.py"):
            rc = self.veille
        elif "commit" in argv:
            chemin = Path(argv[2])
            self.au_commit = {"liste": (chemin / bl.LISTE_REL).read_text(),
                              "plugin": (chemin / bl.PLUGIN_JSON).read_text(),
                              "journal": (chemin / bl.JOURNAL_REL).read_text(),
                              "message": argv[argv.index("-m") + 1]}
        elif argv[0] == "gh":
            rc, sortie = self.gh, URL_PR
        return subprocess.CompletedProcess(argv, rc, sortie, "erreur simulée" if rc else "")


def creations(sh):
    return [a for a in sh.appels if a[0] == "gh" and "create" in a]


def ouvrir(tmp_path, sh):
    (tmp_path / "j.md").write_text(journal())
    dep = bl.Dependances(journal=tmp_path / "j.md", sh=sh, racine=tmp_path / "wt")
    return dep.ouvrir_pr(CANDIDAT, AUJOURDHUI.isoformat())


def test_ouvrir_pr_ouvre_la_pr_prete_avec_un_corps_que_la_garde_accepte(tmp_path):
    # Panne attrapée : une PR sans ligne Doc acceptée par la garde, ou en brouillon (merge-auto ne la prendrait pas).
    sh = ShFaux()
    assert ouvrir(tmp_path, sh) == URL_PR

    (creation,) = creations(sh)
    assert "--draft" not in creation
    corps = creation[creation.index("--body") + 1]
    ok, raison = verifier_doc(corps, bl.AUTEUR_PR)
    assert ok, raison
    assert any(l.startswith("Evals: revue-hors-plan") for l in corps.splitlines())


def test_ouvrir_pr_commite_la_ligne_le_bump_le_journal_et_la_trace_eval(tmp_path):
    # Panne attrapée : une PR sans bump de version (plugin update répond « déjà à jour »), ou sans trailer Eval-cas
    # (check_lecon_a_son_cas refuse), ou un commit qui n'emporte pas le journal des mesures.
    sh = ShFaux()
    ouvrir(tmp_path, sh)

    assert "   2. Une remarque retenue que la chaîne a manquée" in sh.au_commit["liste"]
    assert '"version": "0.76.2"' in sh.au_commit["plugin"]
    assert sh.au_commit["journal"] == (tmp_path / "j.md").read_text()
    assert "Eval-cas: aucun — ligne mesurée par le banc" in sh.au_commit["message"]


def test_ouvrir_pr_retire_son_worktree_a_la_fin(tmp_path):
    # Panne attrapée : un worktree qui reste sur le disque après chaque PR, et le suivant qui échoue à le recréer.
    ouvrir(tmp_path, ShFaux())
    assert not (tmp_path / "wt" / "boucle-liste-pr-2026-12-08").exists()


def test_garde_doc_refusee_arrete_avant_push_et_pr(tmp_path):
    # Panne attrapée : une PR poussée et ouverte alors que la garde Doc l'a refusée.
    sh = ShFaux(garde=1)
    with pytest.raises(bl.Souci) as e:
        ouvrir(tmp_path, sh)
    assert e.value.reelle is False
    assert creations(sh) == []
    assert not any("push" in a for a in sh.appels)
    assert not (tmp_path / "wt" / "boucle-liste-pr-2026-12-08").exists()


def test_evals_refusee_arrete_avant_push_et_pr(tmp_path):
    # Panne attrapée : une PR ouverte alors que la sélection des évals la refuse.
    sh = ShFaux(evals=1)
    with pytest.raises(bl.Souci):
        ouvrir(tmp_path, sh)
    assert creations(sh) == []
    assert not any("push" in a for a in sh.appels)


def test_gh_en_echec_est_une_erreur_reelle_et_retire_le_worktree(tmp_path):
    # Panne attrapée : un gh en échec avalé (pas de souci visible, la ligne se croit ouverte) ou rendu comme donnée.
    sh = ShFaux(gh=1)
    with pytest.raises(bl.Souci) as e:
        ouvrir(tmp_path, sh)
    assert e.value.reelle is True
    assert not (tmp_path / "wt" / "boucle-liste-pr-2026-12-08").exists()


def test_bump_monte_le_patch_et_garde_le_reste_du_fichier():
    # Panne attrapée : une version qui ne monte pas (plugin update répond « déjà à jour ») ou un fichier réécrit de travers.
    assert json.loads(bl.bump_patch(PLUGIN_FIXTURE)) == {"name": "plans-notion", "version": "0.76.2"}


# --- Passe de relecture « plan entier » : décisions hors journal, budget, PR en vol, regroupement -------------------

URL_PR7 = "https://github.com/benjaminge73/mes-skills/pull/7"
EN_VOL = {"candidats": {CANDIDAT.ligne: {"statut": "en vol", "pr": URL_PR7, "categorie": "D", "liste": SHA}}}


def test_refus_et_base_persistes_hors_journal_au_passage_suivant(tmp_path):
    # Panne attrapée : un worktree neuf, dont le journal ne porte pas les entrées de la première passe, remesure une
    # ligne déjà refusée et la base : la décision ne vivait que dans le journal de travail.
    chemin = tmp_path / "journal-checklist.md"
    chemin.write_text(journal())
    faux = Faux(chemin, mesurer=mesurer_exacte(bruit=0.9), candidats=[CANDIDAT])
    assert bl.main(SECTION, deps=faux, aujourdhui=AUJOURDHUI) == bl.CODE_OK
    assert "- Décision : refusée" in chemin.read_text()
    avant = list(faux.bras_mesures)
    chemin.write_text(journal())
    assert bl.main(SECTION, deps=faux, aujourdhui=AUJOURDHUI) == bl.CODE_OK
    assert faux.bras_mesures == avant


def test_worktree_de_pr_porte_un_nom_distinct_du_lancement(tmp_path):
    # Panne attrapée : le worktree de PR porte le nom du dossier de lancement, et son nettoyage efface le lancement.
    sh = ShFaux()
    ouvrir(tmp_path, sh)
    (ajout,) = [a for a in sh.appels if "worktree" in a and "add" in a]
    assert Path(ajout[-2]).name == "boucle-liste-pr-2026-12-08"


def test_ouvrir_pr_refuse_un_worktree_qui_contient_le_depot_sans_rien_effacer(tmp_path):
    # Panne attrapée : un worktree de PR posé sur le dépôt de lancement, puis effacé par le nettoyage de fin.
    sh = ShFaux()
    (tmp_path / "j.md").write_text(journal())
    dep = bl.Dependances(journal=tmp_path / "j.md", sh=sh, racine=bl.DEPOT)
    with pytest.raises(bl.Souci) as e:
        dep.ouvrir_pr(CANDIDAT, AUJOURDHUI.isoformat())
    assert e.value.reelle is True
    assert sh.appels == []
    assert (bl.DEPOT / ".git").exists()


@pytest.mark.parametrize("chemin, interdit", [
    (bl.DEPOT, True),                    # le dépôt lui-même
    (bl.DEPOT.parent, True),             # un dossier qui contient le dépôt
    (bl.DEPOT / "wt", True),             # un dossier posé dans le dépôt
    (bl.DEPOT.parent / "wt", False),     # un frère du dépôt : le cas normal
])
def test_chemin_de_pr_interdit_s_il_egale_contient_ou_est_dans_le_depot(chemin, interdit):
    # Panne attrapée : `_retirer` efface un chemin qui recouvre le dépôt de lancement.
    assert bl.chemin_interdit(chemin, bl.DEPOT) is interdit


def test_budget_inconnu_exige_le_plafond_entier_avant_une_mesure(tmp_path):
    # Panne attrapée : sans mesure complète connue, une mesure part avec 4,50 dollars restants sur 5.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=[CANDIDAT],
                           etat={"couts": {MOIS: 0.5}})
    assert code == bl.CODE_PLAFOND
    assert faux.bras_mesures == []


def test_budget_restant_sous_le_cout_d_une_mesure_connue_ne_lance_rien(tmp_path):
    # Panne attrapée : 1 dollar restant, une mesure qui en coûte 2 part quand même, et le mois dépasse le plafond.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=[CANDIDAT],
                           etat={"couts": {MOIS: 4.0}, "cout_mesure": 2.0})
    assert code == bl.CODE_PLAFOND
    assert faux.bras_mesures == []


def test_mesure_complete_n_est_pas_repayee_quand_la_suivante_est_bloquee(tmp_path):
    # Panne attrapée : le bras 1 de la base payé à chaque passage, le bras 2 n'arrivant jamais (coût sans fin).
    chemin = tmp_path / "journal-checklist.md"
    chemin.write_text(journal())
    faux = Faux(chemin, mesurer=mesurer_exacte(bruit=0.9), candidats=[CANDIDAT])
    assert bl.main(SECTION + ["--plafond-mois", "1.5"], deps=faux, aujourdhui=AUJOURDHUI) == bl.CODE_PLAFOND
    chemin.write_text(journal())   # worktree neuf : le journal ne porte pas le bras 1 payé au passage précédent
    assert bl.main(SECTION, deps=faux, aujourdhui=AUJOURDHUI) == bl.CODE_OK
    assert faux.bras_mesures.count(f"base-{bl._sha8(LISTE)}-1") == 1


class ShSorties:
    """Remplace `_lancer` : rejouer.py écrit `n` sorties à 0,25 dollar et rend 0 ; tout autre appel est noté, rien ne part."""

    def __init__(self, n):
        self.n, self.appels = n, []

    def __call__(self, argv, cwd=None, env=None):
        argv = [str(a) for a in argv]
        self.appels.append(argv)
        if any(a.endswith("rejouer.py") for a in argv):
            dossier = bl.banc.DONNEES / "sorties" / argv[2]
            dossier.mkdir(parents=True, exist_ok=True)
            for i in range(self.n):
                (dossier / f"{i}.json").write_text(json.dumps({"id": i, "total_cost_usd": 0.25, "result": "ok"}))
        return subprocess.CompletedProcess(argv, 0, "", "")


def test_sorties_incompletes_refusees_avant_le_juge_avec_leur_cout(donnees, monkeypatch):
    # Panne attrapée : une mesure coupée par le plafond jugée sur ses seules sorties, et sa dépense perdue.
    (donnees / bl.CAS_VALIDATION).write_text(json.dumps([{"id": 1}, {"id": 2}, {"id": 3}]))
    sh = ShSorties(n=2)
    monkeypatch.setattr(bl, "_lancer", sh)
    with pytest.raises(bl.Souci) as e:
        bl.Dependances().mesurer(LISTE, "cand-test", 5.0)
    assert "2 sur 3" in str(e.value)
    assert e.value.cout == pytest.approx(0.5)
    assert not any(a.endswith("juge.py") for argv in sh.appels for a in argv)


def test_rejeu_ne_lance_pas_un_cas_de_plus_tant_que_son_cout_est_inconnu():
    # Panne attrapée : six cas partent ensemble avant qu'un seul coût soit connu, et le plafond saute.
    import rejouer
    b = rejouer.Budget(plafond=1.0, par=6)
    assert b.demarrer() is True
    assert b.demarrer() is False
    b.terminer(0.5, compte=True)
    assert b.demarrer() is False   # reste 0,5 dollar, lot moyen 6 × 0,5 = 3 dollars


def test_rejeu_ne_depasse_pas_le_plafond_en_lancant_des_cas_en_vol():
    # Panne attrapée : le plafond vérifié cas par cas, alors que les cas en vol ne sont pas encore payés.
    import rejouer
    b = rejouer.Budget(plafond=2.0, par=2)
    assert b.demarrer() is True
    b.terminer(0.5, compte=True)           # coût moyen 0,5 : un lot de deux cas = 1,0
    lances = [b.demarrer() for _ in range(3)]
    assert lances == [True, True, False]
    assert b.depense + b.en_vol * 0.5 <= b.plafond


def test_rejeu_n_ecarte_aucun_cas_pendant_que_le_premier_cout_est_inconnu():
    # Panne attrapée : six threads, le premier cas en vol, les cinq autres refusés « plafond » et jamais rejoués : la
    # passe rend des sorties incomplètes, donc une mesure jugée à tort et payée pour rien.
    import rejouer
    import threading
    import time
    b = rejouer.Budget(plafond=100.0, par=6)
    resultats = []

    def cas():
        resultats.append(b.demarrer(attendre=True))
        time.sleep(0.02)
        b.terminer(0.1, compte=True)

    fils = [threading.Thread(target=cas, daemon=True) for _ in range(6)]
    for f in fils:
        f.start()
    for f in fils:
        f.join(timeout=5)
    assert len(resultats) == 6 and all(resultats)


def test_garde_de_veille_refusee_arrete_avant_push_et_pr(tmp_path):
    # Panne attrapée : une PR poussée alors que la garde de veille la refuse (la CI ne ferait que la répéter après coup).
    sh = ShFaux(veille=1)
    with pytest.raises(bl.Souci) as e:
        ouvrir(tmp_path, sh)
    assert e.value.reelle is False
    assert creations(sh) == []
    assert not any("push" in a for a in sh.appels)
    assert not (tmp_path / "wt" / "boucle-liste-pr-2026-12-08").exists()


def test_garde_de_veille_en_panne_est_une_erreur_reelle(tmp_path):
    # Panne attrapée : une garde de veille qui plante (base illisible) prise pour un refus ordinaire.
    sh = ShFaux(veille=2)
    with pytest.raises(bl.Souci) as e:
        ouvrir(tmp_path, sh)
    assert e.value.reelle is True
    assert creations(sh) == [] and not any("push" in a for a in sh.appels)


@pytest.mark.parametrize("payload, attendu", [
    ({"state": "MERGED", "statusCheckRollup": []}, "mergée"),
    ({"state": "CLOSED", "statusCheckRollup": []}, "fermée"),
    ({"state": "OPEN", "statusCheckRollup": [{"conclusion": "FAILURE"}]}, "rouge"),
    ({"state": "OPEN", "statusCheckRollup": [{"state": "FAILURE"}]}, "rouge"),   # contrôle de commit (StatusContext)
    ({"state": "OPEN", "statusCheckRollup": [{"conclusion": "SUCCESS"}, {"status": "IN_PROGRESS", "conclusion": ""}]},
     "ouverte"),
])
def test_etat_de_pr_lu_sur_github(payload, attendu):
    # Panne attrapée : une PR rouge ou fermée sans merge lue comme « ouverte », et la boucle attend pour rien.
    assert bl.classer_pr(payload) == attendu


def test_etat_pr_en_echec_est_une_erreur_reelle(tmp_path):
    # Panne attrapée : une lecture d'état qui échoue rendue comme une PR ouverte, donc attendue sans fin.
    sh = lambda argv, cwd=None, env=None: subprocess.CompletedProcess(argv, 1, "", "HTTP 401")
    with pytest.raises(bl.Souci) as e:
        bl.Dependances(journal=tmp_path / "j.md", sh=sh).etat_pr(URL_PR7)
    assert e.value.reelle is True


def test_etat_pr_rend_le_json_de_gh(tmp_path):
    # Panne attrapée : la réponse de gh perdue en route, et la PR déclarée sans état.
    sh = lambda argv, cwd=None, env=None: subprocess.CompletedProcess(
        argv, 0, json.dumps({"state": "MERGED", "statusCheckRollup": []}), "")
    assert bl.Dependances(journal=tmp_path / "j.md", sh=sh).etat_pr(URL_PR7)["state"] == "MERGED"


def test_pr_ouverte_non_mergee_n_est_ni_remesuree_ni_rouverte(tmp_path):
    # Panne attrapée : une PR encore ouverte (pas mergée) comptée comme décidée, ou rouverte en double.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=[CANDIDAT],
                           etat=EN_VOL, prs={URL_PR7: {"state": "OPEN", "statusCheckRollup": [{"conclusion": "SUCCESS"}]}})
    assert code == bl.CODE_OK
    assert faux.consultes == [URL_PR7]
    assert faux.bras_mesures == [] and faux.prs == []


def test_pr_rouge_est_signalee_et_rien_n_est_mesure_ni_ouvert(tmp_path, capsys):
    # Panne attrapée : une PR rouge laissée muette, et la boucle mesure la suite par-dessus.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=[CANDIDAT],
                           etat=EN_VOL, prs={URL_PR7: {"state": "OPEN", "statusCheckRollup": [{"conclusion": "FAILURE"}]}})
    assert code == bl.CODE_OK
    assert "échec" in capsys.readouterr().out
    assert faux.bras_mesures == [] and faux.prs == []


def test_pr_mergee_passe_decidee_et_la_ligne_n_est_pas_remesuree(tmp_path):
    # Panne attrapée : une ligne mergée remesurée parce que l'état ne la reconnaît pas comme décidée.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=[CANDIDAT],
                           etat=EN_VOL, prs={URL_PR7: {"state": "MERGED", "statusCheckRollup": []}})
    assert code == bl.CODE_OK
    assert not any(b.startswith("cand-") for b in faux.bras_mesures)
    assert faux.etats["Code"]["candidats"][CANDIDAT.ligne]["statut"] == "mergée"


def test_pr_fermee_sans_merge_est_signalee_une_fois_et_la_ligne_reste_decidee(tmp_path, capsys):
    # Panne attrapée : une PR fermée à la main rouverte à chaque passage, ou muette.
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=[CANDIDAT],
                           etat=EN_VOL, prs={URL_PR7: {"state": "CLOSED", "statusCheckRollup": []}})
    assert "fermée sans merge" in capsys.readouterr().out
    assert faux.etats["Code"]["candidats"][CANDIDAT.ligne]["statut"] == "fermée"
    assert bl.main(SECTION, deps=faux, aujourdhui=AUJOURDHUI) == bl.CODE_OK
    assert faux.prs == [] and not any(b.startswith("cand-") for b in faux.bras_mesures)


def test_pr_ouverte_seulement_dans_le_journal_est_suivie_sans_doublon(tmp_path, capsys):
    # Panne attrapée : état perdu, le journal seul dit « PR ouverte » : la ligne serait remesurée et rouverte.
    corps = (f"### 2026-11-20 — candidat « {CANDIDAT.ligne[:60]} »\n- Ligne candidate : {CANDIDAT.ligne}\n"
             f"- Catégorie : D\n- PR : {URL_PR7}\n")
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(corps=corps), mesurer=mesurer_exacte(),
                           candidats=[CANDIDAT],
                           prs={URL_PR7: {"state": "OPEN", "statusCheckRollup": [{"conclusion": "FAILURE"}]}})
    assert "échec" in capsys.readouterr().out
    assert faux.prs == [] and faux.bras_mesures == []


def test_regrouper_deux_resumes_differents_de_meme_categorie_donnent_un_candidat():
    # Panne attrapée : deux libellés différents d'une même catégorie, vus chacun dans une étape, ne comptent pour rien.
    a = {"origine": "opus", "categorie": "D", "resume": "Garde absente avant le push"}
    b = {"origine": "opus", "categorie": "D", "resume": "Pas de garde avant le push, ni de test"}
    assert bl.regrouper([("e1", a), ("e2", b)]) == [bl.Candidat("D", "Garde absente avant le push")]


def test_regrouper_une_seule_etape_ne_fait_pas_un_candidat():
    # Panne attrapée : deux remarques d'une même étape comptées comme deux étapes.
    a = {"origine": "opus", "categorie": "D", "resume": "Garde absente avant le push"}
    b = {"origine": "opus", "categorie": "D", "resume": "Pas de test du garde"}
    assert bl.regrouper([("e1", a), ("e1", b)]) == []


def test_regrouper_sans_categorie_ne_donne_pas_de_candidat_mesurable(tmp_path):
    # Panne attrapée : une remarque sans lettre mesurée quand même, et insérée dans une catégorie au hasard.
    a = {"origine": "opus", "resume": "Garde absente."}
    b = {"origine": "opus", "resume": "garde absente"}
    cands_sans = bl.regrouper([("e1", a), ("e2", b)])
    assert [c.categorie for c in cands_sans] == [""]
    code, faux, _ = lancer(tmp_path, SECTION, texte=journal(), mesurer=mesurer_exacte(), candidats=cands_sans)
    assert code == bl.CODE_OK
    assert not any(x.startswith("cand-") for x in faux.bras_mesures)
