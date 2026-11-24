"""Tests de la boucle d'amélioration de la liste (`boucle_liste.py`) : décision, plafond, bilan, quota, cron, PR.

Aucun appel réseau, aucun `claude`, aucun `gh`, aucun `git push` : les dépendances sont remplacées par `Faux` (mesures,
PR) ou `ShFaux` (le shell d'`ouvrir_pr`). Les vraies mesures (`rejouer.py`, `juge.py`) ne sont jamais lancées ici.
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


def journal(bilan="Bilan de Q2 : 2026-12-07", corps=""):
    entete = "# Journal de test\n\n" + (bilan + "\n\n" if bilan else "")
    return entete + "## Code\n\n### 2026-11-23 — premier passage\n- Ligne candidate : aucune\n" + corps


class Faux:
    """Dépendances de test : le journal est un vrai fichier ; mesures, état et PR sont fictifs, en mémoire."""

    def __init__(self, chemin, *, mesurer, candidats=(), jeu=True, pr_echoue=False):
        self.chemin = chemin
        self._mesurer = mesurer
        self._candidats = list(candidats)
        self._jeu = jeu
        self.pr_echoue = pr_echoue
        self.bras_mesures = []
        self.budgets = []
        self.prs = []
        self.etats = {}

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

    def liste_texte(self):
        return LISTE

    def liste_sha(self):
        return SHA

    def liste_avec(self, candidat):
        return LISTE + f"CANDIDAT {candidat.ligne}\n"

    def mesurer(self, liste, bras, budget):
        self.bras_mesures.append(bras)
        self.budgets.append(budget)
        return self._mesurer(liste, bras)

    def candidats(self):
        return list(self._candidats)

    def ouvrir_pr(self, candidat, iso):
        if self.pr_echoue:
            raise bl.Souci("gh pr create en échec", reelle=True)
        self.prs.append(candidat)
        return "https://github.com/benjaminge73/mes-skills/pull/999"


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


def lancer(tmp_path, argv, *, texte, mesurer, candidats=(), jeu=True, pr_echoue=False, etat=None):
    chemin = tmp_path / "journal-checklist.md"
    chemin.write_text(texte)
    faux = Faux(chemin, mesurer=mesurer, candidats=candidats, jeu=jeu, pr_echoue=pr_echoue)
    if etat is not None:
        faux.etats["Code"] = etat
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
    code, faux, _ = lancer(tmp_path, SECTION + argv_plus, texte=journal(), mesurer=mesurer_scripte(hausse=0.02),
                           candidats=[CANDIDAT], etat={"couts": {MOIS: 2.0}})
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

    def __init__(self, *, garde=0, evals=0, gh=0):
        self.garde, self.evals, self.gh = garde, evals, gh
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
    assert not (tmp_path / "wt" / "boucle-liste-2026-12-08").exists()


def test_garde_doc_refusee_arrete_avant_push_et_pr(tmp_path):
    # Panne attrapée : une PR poussée et ouverte alors que la garde Doc l'a refusée.
    sh = ShFaux(garde=1)
    with pytest.raises(bl.Souci) as e:
        ouvrir(tmp_path, sh)
    assert e.value.reelle is False
    assert creations(sh) == []
    assert not any("push" in a for a in sh.appels)
    assert not (tmp_path / "wt" / "boucle-liste-2026-12-08").exists()


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
    assert not (tmp_path / "wt" / "boucle-liste-2026-12-08").exists()


def test_bump_monte_le_patch_et_garde_le_reste_du_fichier():
    # Panne attrapée : une version qui ne monte pas (plugin update répond « déjà à jour ») ou un fichier réécrit de travers.
    assert json.loads(bl.bump_patch(PLUGIN_FIXTURE)) == {"name": "plans-notion", "version": "0.76.2"}
