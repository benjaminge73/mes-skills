"""Tests de ``evals_ab.py`` : comparaison A/B de deux versions d'un plugin.

Lancés par la CI (``python3 -m unittest discover -s scripts``), sans
dépendance et **sans jamais appeler ``claude``** : le lanceur est remplacé par
un faux script qui rend un rapport JSON figé (``scripts/fixtures_evals_ab/``).

Les rapports figés ont la forme réelle de ``claude plugin eval --json``
(2.1.285) : ``rapport_reel.json`` est un vrai rapport, anonymisé ; les autres
en sont dérivés à la main, à l'attendu calculé sur le papier :

    base            alpha 1, beta 2/3, gamma 1, delta 1/3   (moyenne 3/4)
    tete_stable     alpha 1, beta 1/3, gamma 1, delta 2/3   (moyenne 3/4)
    tete_recul_global   alpha 1/3, beta 0, gamma 2/3, delta 1/3 (moyenne 1/3,
                        soit -5/12 : au-dela du bruit global, sans qu'aucun
                        cas ne depasse le bruit par cas)
    tete_recul_cas  gamma s'effondre (1 -> 0), le reste égal (moyenne 1/2)
    tete_amelioree  tout à 1                                 (moyenne 1)

4 cas x 3 passages : bruit estimé racine(2)/racine(4*3) = 0,4082 (global) et
racine(2)/racine(3) = 0,8165 (par cas) : celui d'un *écart* entre deux moyennes
(base, tête), qui portent chacune leur propre bruit, et non celui d'une seule.

Étape B9 (évals ciblées) : ``--cas`` restreint les cas joués (Bonferroni se
calcule alors sur le nombre de cas *joués*) ; un fichier de bruit porte le
modèle qu'il mesure et n'est utilisé que pour ce modèle (``EVALS_MODELE``) ;
un seuil par cas d'au moins 100 points ne peut rien voir : le tableau dit
« non concluant par cas » au lieu de « pas de recul ».

Le seuil **par cas** est corrigé pour les comparaisons multiples (Bonferroni,
bilatéral) : z_n = inv_cdf(1 - 0,05/(2n)) au lieu de 1,96. Valeurs de z_n
écrites en dur ci-dessous (table de la loi normale), jamais recalculées par le
code testé : n=4 -> 2,4977 ; n=9 -> 2,7729 ; n=16 -> 2,9552. Le seuil global
ne change pas.
"""
from __future__ import annotations

import copy
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evals_ab  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures_evals_ab"
MODELE = "claude-opus-5-5"


def rapport(nom: str) -> dict:
    return json.loads((FIXTURES / f"rapport_{nom}.json").read_text("utf-8"))


def jouer(argv: list[str], env: dict | None = None) -> tuple[int, str, str]:
    """Appelle ``evals_ab.main`` et rend (code, stdout, stderr)."""
    sortie, erreur = io.StringIO(), io.StringIO()
    ancien = dict(os.environ)
    os.environ.update(env or {})
    try:
        with redirect_stdout(sortie), redirect_stderr(erreur):
            try:
                code = evals_ab.main(argv)
            except SystemExit as sortie_sys:  # argparse
                code = sortie_sys.code
    finally:
        os.environ.clear()
        os.environ.update(ancien)
    return code, sortie.getvalue(), erreur.getvalue()


# --------------------------------------------------------------------------
# Lecteur du sous-ensemble YAML des cas
# --------------------------------------------------------------------------
class LireYaml(unittest.TestCase):
    def test_une_liste_de_juges_donne_des_mappings_types(self):
        texte = (
            "name: exemple\n"
            "runs: 3\n"
            "graders:\n"
            "  - name: un\n"
            "    type: regex\n"
            "    weight: 1.5\n"
            "    pattern: 'OK'\n"
            "  - name: deux\n"
            "    type: file_exists\n"
            "    exists: false\n"
        )
        attendu = {
            "name": "exemple",
            "runs": 3,
            "graders": [
                {"name": "un", "type": "regex", "weight": 1.5, "pattern": "OK"},
                {"name": "deux", "type": "file_exists", "exists": False},
            ],
        }
        self.assertEqual(evals_ab.lire_yaml(texte), attendu)

    def test_un_mapping_en_ligne_sert_de_cible_fichier(self):
        texte = "target: {source: file, path: \"sortie/*.md\"}\ntags: [a, 'b c']\n"
        attendu = {
            "target": {"source": "file", "path": "sortie/*.md"},
            "tags": ["a", "b c"],
        }
        self.assertEqual(evals_ab.lire_yaml(texte), attendu)

    def test_un_diese_entre_guillemets_n_est_pas_un_commentaire(self):
        texte = "pattern: \"^## Titre\"  # vrai commentaire\nflags: i\n"
        self.assertEqual(
            evals_ab.lire_yaml(texte), {"pattern": "^## Titre", "flags": "i"}
        )

    def test_un_bloc_litteral_garde_ses_lignes(self):
        texte = "criteria: |\n  PASS si A.\n  FAIL si B.\nweight: 2\n"
        self.assertEqual(
            evals_ab.lire_yaml(texte),
            {"criteria": "PASS si A.\nFAIL si B.\n", "weight": 2},
        )

    def test_une_syntaxe_hors_sous_ensemble_est_refusee_pas_mal_lue(self):
        # Une ancre YAML lue de travers changerait silencieusement un juge :
        # mieux vaut un refus net.
        with self.assertRaises(evals_ab.ErreurYaml):
            evals_ab.lire_yaml("base: &ancre\n  type: regex\ncopie: *ancre\n")


class SeparerFrontmatter(unittest.TestCase):
    def test_le_frontmatter_et_le_corps_sont_separes(self):
        texte = "---\ntype: llm\nweight: 2\n---\n\nPASS si la réponse est claire.\n"
        meta, corps = evals_ab.separer_frontmatter(texte)
        self.assertEqual(meta, {"type": "llm", "weight": 2})
        self.assertEqual(corps.strip(), "PASS si la réponse est claire.")

    def test_un_fichier_sans_frontmatter_rend_un_dictionnaire_vide(self):
        meta, corps = evals_ab.separer_frontmatter("juste du texte\n")
        self.assertEqual(meta, {})
        self.assertEqual(corps, "juste du texte\n")


# --------------------------------------------------------------------------
# Lecture des rapports
# --------------------------------------------------------------------------
class LireRapport(unittest.TestCase):
    def test_le_rapport_reel_donne_score_passages_et_cout(self):
        scores = evals_ab.scores_par_cas(rapport("reel"))
        self.assertEqual(list(scores), ["ok"])
        self.assertEqual(scores["ok"].score, 1.0)
        self.assertEqual(scores["ok"].passages, 1)
        self.assertAlmostEqual(evals_ab.cout_rapport(rapport("reel")), 0.028844)

    def test_le_score_d_un_cas_est_la_moyenne_de_ses_passages(self):
        # beta : passages 1, 1, 0 -> 2/3
        scores = evals_ab.scores_par_cas(rapport("base"))
        self.assertAlmostEqual(scores["beta"].score, 2 / 3)
        self.assertEqual(scores["beta"].passages, 3)

    def test_un_rapport_partiel_est_refuse(self):
        # Un rapport tronqué par le plafond de coût comparé à un rapport
        # complet ferait passer des cas non joués pour des reculs.
        with self.assertRaises(evals_ab.ErreurRefus) as ctx:
            evals_ab.verifier_complet(rapport("partiel"), "base")
        self.assertIn("partial", str(ctx.exception))
        self.assertIn("cost_ceiling", str(ctx.exception))

    def test_un_rapport_sans_aucun_cas_est_refuse(self):
        vide = rapport("base")
        vide["cases"] = []
        with self.assertRaises(evals_ab.ErreurRefus):
            evals_ab.verifier_complet(vide, "tête")


# --------------------------------------------------------------------------
# Comparaison et bruit
# --------------------------------------------------------------------------
def comparer(tete: str, bruit=None):
    return evals_ab.comparer(rapport("base"), rapport(tete), bruit=bruit)


def rapport_synthetique(passages_par_cas: dict[str, list[int]]) -> dict:
    """Un rapport à la forme réelle, dont chaque cas porte les passages donnés
    (1 = réussi, 0 = raté) : sert aux scénarios qui n'ont pas de fixture figée."""
    modele = rapport("base")
    passage = modele["cases"][0]["arms"]["with"][0]
    cas = []
    for nom, resultats in passages_par_cas.items():
        c = copy.deepcopy(modele["cases"][0])
        c["name"] = nom
        c["arms"]["with"] = [dict(passage, score=r, passed=bool(r)) for r in resultats]
        cas.append(c)
    return {**modele, "cases": cas}


def jeux_uniformes(n: int, base: float, tete: float, un_cas: str = "c0", passages: int = 3):
    """n cas à ``base`` partout côté base ; côté tête, tous à ``base`` sauf
    ``un_cas`` à ``tete``."""
    noms = [f"c{i}" for i in range(n)]
    rb = rapport_synthetique({nom: [base] * passages for nom in noms})
    rt = rapport_synthetique({nom: [tete if nom == un_cas else base] * passages for nom in noms})
    return rb, rt


class Comparer(unittest.TestCase):
    def test_l_ecart_par_cas_est_tete_moins_base(self):
        c = comparer("tete_stable")
        ecarts = {ligne.nom: ligne.delta for ligne in c.lignes}
        self.assertAlmostEqual(ecarts["alpha"], 0.0)
        self.assertAlmostEqual(ecarts["beta"], -1 / 3)  # 2/3 -> 1/3
        self.assertAlmostEqual(ecarts["gamma"], 0.0)
        self.assertAlmostEqual(ecarts["delta"], 1 / 3)  # 1/3 -> 2/3
        self.assertAlmostEqual(c.delta_moyen, 0.0)

    def test_un_ecart_dans_le_bruit_ne_fait_pas_echouer(self):
        self.assertFalse(comparer("tete_stable").recul)

    def test_un_recul_moyen_au_dela_du_bruit_fait_echouer(self):
        # -5/12 en moyenne, bruit global 0,4082 ; aucun cas isolé ne dépasse
        # 0,8165 (le pire perd 2/3) : c'est bien le seuil global qui parle.
        c = comparer("tete_recul_global")
        self.assertAlmostEqual(c.delta_moyen, -5 / 12)
        self.assertTrue(c.recul)
        self.assertFalse(any(ligne.recul for ligne in c.lignes))

    def test_un_cas_qui_s_effondre_fait_echouer_meme_si_la_moyenne_tient(self):
        # 8 cas x 12 passages, bruit estimé. Un cas perd 1 : moyenne -1/8 = -0,125,
        # sous le seuil global racine(2)/racine(96) = 0,1443 ; mais l'écart du cas
        # (-1) dépasse le seuil par cas de Bonferroni, (2,7344/1,96) x racine(2)/racine(12)
        # = 0,5695. (Avec 4 cas x 3 passages, ce seuil vaut 1,04 : un cas ne peut plus
        # reculer seul, d'où ce jeu plus large que la fixture.)
        base, tete = jeux_uniformes(8, 1, 0, passages=12)
        c = evals_ab.comparer(base, tete)
        self.assertAlmostEqual(c.delta_moyen, -0.125)
        self.assertLess(-c.delta_moyen, c.bruit_global)
        self.assertTrue(c.recul)
        reculs = [ligne.nom for ligne in c.lignes if ligne.recul]
        self.assertEqual(reculs, ["c0"])

    def test_une_amelioration_ne_fait_pas_echouer(self):
        c = comparer("tete_amelioree")
        self.assertAlmostEqual(c.delta_moyen, 0.25)
        self.assertFalse(c.recul)

    def test_un_cas_absent_d_un_des_rapports_est_refuse(self):
        tete = rapport("tete_stable")
        tete["cases"] = tete["cases"][:3]  # sans delta
        with self.assertRaises(evals_ab.ErreurRefus) as ctx:
            evals_ab.comparer(rapport("base"), tete)
        self.assertIn("delta", str(ctx.exception))

    def test_le_bruit_estime_est_celui_d_un_ecart_de_deux_moyennes_pas_d_une_seule(self):
        # On compare deux moyennes (base, tête), chacune bruitée : l'écart est
        # racine(2) fois plus incertain qu'une moyenne seule, qui vaut 1/racine(n*R).
        # n et R viennent du fixture, pas du code testé.
        base = rapport("base")
        n = len(base["cases"])
        r = len(base["cases"][0]["arms"]["with"])
        c = comparer("tete_stable")
        self.assertFalse(c.bruit_mesure)
        self.assertAlmostEqual(c.bruit_global, math.sqrt(2) / math.sqrt(n * r))
        # Par cas : le même √2/√R, élargi par Bonferroni pour n = 4 cas
        # (z_4 = 2,4977 au lieu de 1,96, en dur : table de la loi normale).
        self.assertAlmostEqual(c.bruit_cas, math.sqrt(2) / math.sqrt(r) * 2.4977 / 1.96, places=3)

    def test_un_cas_de_3_sur_3_a_1_sur_3_est_dans_le_bruit_estime_d_un_ecart(self):
        # Scénario de revue : deux références identiques (le vrai écart est nul),
        # R = 3 ; un cas passe de 3/3 à 1/3 par pur hasard. Écart -0,667 < bruit
        # par cas d'un écart 0,816 : pas de recul (avec 1/racine(3) = 0,577, la CI
        # aurait échoué à tort).
        base = rapport_synthetique({"a": [1, 1, 1], "b": [1, 1, 1], "c": [1, 1, 1], "d": [1, 1, 1]})
        tete = rapport_synthetique({"a": [1, 1, 1], "b": [1, 1, 1], "c": [1, 1, 1], "d": [1, 0, 0]})
        c = evals_ab.comparer(base, tete)
        self.assertAlmostEqual(c.lignes[3].delta, -2 / 3)
        self.assertFalse(c.lignes[3].recul)
        self.assertFalse(c.recul)

    def test_un_recul_moyen_de_0_23_sur_10_cas_x_3_passages_est_dans_le_bruit_estime(self):
        # Scénario de revue, écart moyen -7/30 = -0,233 : entre 1/racine(30) = 0,183
        # (bruit d'une seule moyenne, trop étroit) et racine(2)/racine(30) = 0,258.
        # Aucun cas ne perd plus de 2/3, sous le bruit par cas 0,816.
        toutes = [f"c{i}" for i in range(10)]
        base = rapport_synthetique({nom: [1, 1, 1] for nom in toutes})
        tete = rapport_synthetique(
            {
                **{nom: [1, 1, 1] for nom in toutes},
                "c0": [1, 0, 0], "c1": [1, 0, 0],
                "c2": [1, 1, 0], "c3": [1, 1, 0], "c4": [1, 1, 0],
            }
        )
        c = evals_ab.comparer(base, tete)
        self.assertAlmostEqual(c.delta_moyen, -7 / 30)
        self.assertFalse(any(ligne.recul for ligne in c.lignes))
        self.assertFalse(c.recul)

    def test_un_bruit_mesure_remplace_l_estimation(self):
        # Le même recul global (-5/12) devient acceptable si le bruit mesuré
        # en A/A est large : rms des écarts par cas 0,5 -> global
        # 1,96 x 0,5 / racine(4) = 0,49.
        bruit = {"rms_ecarts_cas": 0.5}
        c = comparer("tete_recul_global", bruit=bruit)
        self.assertTrue(c.bruit_mesure)
        self.assertAlmostEqual(c.bruit_global, 0.49)
        # Seuil par cas de Bonferroni pour 4 cas : 2,4977 x 0,5 = 1,2489.
        self.assertAlmostEqual(c.bruit_cas, 1.2489, places=3)
        self.assertFalse(c.recul)

    def test_un_bruit_mesure_n_excuse_pas_un_effondrement_plus_grand_que_lui(self):
        # rms 0,2 -> seuil par cas de Bonferroni (4 cas) 2,4977 x 0,2 = 0,4995 ;
        # gamma perd 1,0 : le recul du cas reste signalé.
        c = comparer("tete_recul_cas", bruit={"rms_ecarts_cas": 0.2})
        gamma = next(ligne for ligne in c.lignes if ligne.nom == "gamma")
        self.assertTrue(gamma.recul)
        self.assertTrue(c.recul)

    def test_un_cas_a_moins_10_points_sur_9_cas_est_dans_le_bruit_mesure_multiple(self):
        # A/A réel du 2026-09-30 : 9 cas x 3 passages, rms 0,0385, deux jeux
        # identiques ; un cas a bougé de -10 pts. Seuil par cas non corrigé
        # 1,96 x 0,0385 = 7,5 pts (faux recul) ; corrigé pour 9 cas :
        # 2,7729 x 0,0385 = 10,7 pts (table de la loi normale) : pas de recul.
        base, tete = jeux_uniformes(9, 1.0, 0.9)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.0385})
        self.assertAlmostEqual(c.lignes[0].delta, -0.10)
        self.assertAlmostEqual(c.bruit_cas, 0.1068, places=3)
        self.assertFalse(c.lignes[0].recul)
        self.assertFalse(c.recul)

    def test_un_cas_a_moins_20_points_sur_16_cas_est_un_recul_et_le_seuil_vaut_11_points(self):
        # 16 cas, rms 0,0385 : z_16 = 2,9552 (~2,95) -> seuil par cas 11,4 pts.
        # Seuil global inchangé : 1,96 x 0,0385 / racine(16) = 0,018865.
        base, tete = jeux_uniformes(16, 1.0, 0.8)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.0385})
        self.assertAlmostEqual(c.bruit_cas, 0.1138, places=3)
        self.assertAlmostEqual(c.bruit_global, 1.96 * 0.0385 / 4, places=6)
        self.assertTrue(c.lignes[0].recul)
        self.assertTrue(c.recul)
        self.assertIn("± 11 pts", evals_ab.tableau_markdown(c, "v1", "v2"))

    def test_pour_un_seul_cas_le_seuil_par_cas_reste_1_96_fois_le_rms(self):
        # n = 1 : aucune comparaison multiple, aucune correction.
        base, tete = jeux_uniformes(1, 1.0, 1.0)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.1})
        self.assertAlmostEqual(c.bruit_cas, 0.196, places=3)
        self.assertAlmostEqual(c.bruit_global, 0.196, places=3)

    def test_le_seuil_global_ne_depend_pas_de_la_correction_par_cas(self):
        # Une seule comparaison (la moyenne) : 1,96 x rms / racine(n), pour n = 9
        # comme pour n = 4 (0,49 plus haut). rms 0,0385, n = 9 -> 0,025.
        base, tete = jeux_uniformes(9, 1.0, 1.0)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.0385})
        self.assertAlmostEqual(c.bruit_global, 1.96 * 0.0385 / 3, places=6)


class BruitAA(unittest.TestCase):
    def test_le_bruit_aa_derive_des_ecarts_entre_deux_jeux_identiques(self):
        # base vs tete_stable joués comme A/A : écarts par cas 0, -1/3, 0, +1/3.
        # rms = racine((0 + 1/9 + 0 + 1/9) / 4) = 0,2357 ;
        # demi-largeur par cas 1,96 x 0,2357 = 0,4619 ;
        # demi-largeur globale 1,96 x 0,2357 / racine(4) = 0,2310.
        b = evals_ab.bruit_aa(rapport("base"), rapport("tete_stable"))
        self.assertAlmostEqual(b["rms_ecarts_cas"], 0.235702, places=5)
        self.assertAlmostEqual(b["demi_largeur_ic95_cas"], 0.461976, places=5)
        self.assertAlmostEqual(b["demi_largeur_ic95_globale"], 0.230988, places=5)
        self.assertEqual(b["n_cas"], 4)
        self.assertEqual(b["passages"], 3)

    def test_deux_jeux_identiques_donnent_un_bruit_nul(self):
        b = evals_ab.bruit_aa(rapport("base"), rapport("base"))
        self.assertEqual(b["rms_ecarts_cas"], 0.0)


# --------------------------------------------------------------------------
# Présentation
# --------------------------------------------------------------------------
class Presentation(unittest.TestCase):
    def test_le_tableau_marque_le_cas_en_recul_et_le_verdict(self):
        c = comparer("tete_recul_cas", bruit={"rms_ecarts_cas": 0.2})
        tableau = evals_ab.tableau_markdown(c, "v1", "v2")
        lignes = tableau.splitlines()
        gamma = next(ligne for ligne in lignes if "gamma" in ligne)
        self.assertIn("100 %", gamma)
        self.assertIn("0 %", gamma)
        self.assertIn("RECUL", gamma)
        self.assertIn("RECUL", tableau.splitlines()[-1])

    def test_le_tableau_nomme_le_seuil_par_cas_de_bonferroni_et_son_nombre_de_cas(self):
        # rms 0,2, 4 cas : 2,4977 x 0,2 = 0,4995 -> « ± 50 pts ».
        c = comparer("tete_recul_cas", bruit={"rms_ecarts_cas": 0.2})
        tableau = evals_ab.tableau_markdown(c, "v1", "v2")
        self.assertIn("seuil par cas (Bonferroni, 4 cas) : ± 50 pts", tableau)

    def test_le_journal_cree_son_entete_puis_ajoute_sans_la_dupliquer(self):
        with tempfile.TemporaryDirectory() as tmp:
            chemin = Path(tmp) / "evals" / "RESULTATS.md"
            evals_ab.ajouter_au_journal(chemin, "| 2026-01-01 | a |")
            evals_ab.ajouter_au_journal(chemin, "| 2026-01-02 | b |")
            texte = chemin.read_text("utf-8")
        self.assertEqual(texte.count("# Résultats"), 1)
        self.assertEqual(texte.count("| 2026-01-01 | a |"), 1)
        self.assertTrue(texte.index("| 2026-01-01 | a |") < texte.index("| 2026-01-02 | b |"))
        self.assertTrue(texte.endswith("\n"))


# --------------------------------------------------------------------------
# Pré-vol : les juges gratuits contre l'oracle et contre l'état vide
# --------------------------------------------------------------------------
def ecrire(chemin: Path, texte: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, "utf-8")


class Previol(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.cas = Path(self._tmp.name) / "cas"

    def cas_prose(self, pattern="^OK$", reponse="OK", extra_juge=""):
        ecrire(self.cas / "prompt.md", "---\nmax_turns: 3\n---\n\nRéponds OK.\n")
        ecrire(
            self.cas / "graders" / "reponse.md",
            f"---\ntype: regex\npattern: \"{pattern}\"\n{extra_juge}---\n",
        )
        if reponse is not None:
            ecrire(self.cas / "oracle" / "reponse.md", reponse + "\n")

    def test_un_cas_dont_l_oracle_satisfait_ses_juges_passe(self):
        self.cas_prose()
        self.assertEqual(evals_ab.previol_cas(self.cas).erreurs, [])

    def test_un_oracle_qui_echoue_a_son_propre_juge_est_refuse(self):
        self.cas_prose(pattern="^OK$", reponse="Voici la réponse : plutôt oui")
        erreurs = evals_ab.previol_cas(self.cas).erreurs
        self.assertEqual(len(erreurs), 1)
        self.assertIn("oracle", erreurs[0])
        self.assertIn("reponse", erreurs[0])

    def test_un_juge_qui_passe_sur_un_etat_vide_est_refuse(self):
        # `.*` est vrai de tout, y compris d'une réponse vide : le juge ne
        # distingue pas un bon passage d'un passage nul.
        self.cas_prose(pattern=".*", reponse="OK")
        erreurs = evals_ab.previol_cas(self.cas).erreurs
        self.assertEqual(len(erreurs), 1)
        self.assertIn("vide", erreurs[0])

    def test_un_cas_sans_oracle_est_refuse(self):
        self.cas_prose(reponse=None)
        erreurs = evals_ab.previol_cas(self.cas).erreurs
        self.assertEqual(len(erreurs), 1)
        self.assertIn("oracle", erreurs[0])

    def test_le_flag_i_du_juge_regex_est_honore(self):
        self.cas_prose(pattern="^ok$", reponse="OK", extra_juge="flags: i\n")
        self.assertEqual(evals_ab.previol_cas(self.cas).erreurs, [])

    def test_un_juge_regex_sur_fichier_lit_l_oracle_de_fichiers(self):
        ecrire(
            self.cas / "case.yaml",
            "name: note\n"
            "graders:\n"
            "  - name: titre\n"
            "    type: regex\n"
            "    pattern: '^# Note'\n"
            "    flags: m\n"
            "    target: {source: file, path: 'sortie/note.md'}\n",
        )
        ecrire(self.cas / "oracle" / "fichiers" / "sortie" / "note.md", "# Note\ncorps\n")
        self.assertEqual(evals_ab.previol_cas(self.cas).erreurs, [])

    def test_un_juge_regex_sur_fichier_echoue_si_le_fichier_d_oracle_manque(self):
        ecrire(
            self.cas / "case.yaml",
            "name: note\n"
            "graders:\n"
            "  - name: titre\n"
            "    type: regex\n"
            "    pattern: '^# Note'\n"
            "    target: {source: file, path: 'sortie/note.md'}\n",
        )
        ecrire(self.cas / "oracle" / "reponse.md", "rien\n")
        erreurs = evals_ab.previol_cas(self.cas).erreurs
        self.assertEqual(len(erreurs), 1)
        self.assertIn("titre", erreurs[0])

    def test_file_exists_se_juge_sur_les_fichiers_de_l_oracle(self):
        ecrire(
            self.cas / "case.yaml",
            "name: note\n"
            "graders:\n"
            "  - {name: cree, type: file_exists, path: 'sortie/*.md'}\n",
        )
        ecrire(self.cas / "oracle" / "fichiers" / "sortie" / "note.md", "x\n")
        self.assertEqual(evals_ab.previol_cas(self.cas).erreurs, [])

    def test_file_exists_est_refuse_si_l_oracle_ne_cree_pas_le_fichier(self):
        ecrire(
            self.cas / "case.yaml",
            "name: note\n"
            "graders:\n"
            "  - {name: cree, type: file_exists, path: 'sortie/*.md'}\n",
        )
        ecrire(self.cas / "oracle" / "reponse.md", "x\n")
        erreurs = evals_ab.previol_cas(self.cas).erreurs
        self.assertEqual(len(erreurs), 1)
        self.assertIn("cree", erreurs[0])

    def test_un_juge_negatif_n_est_pas_refuse_pour_passer_sur_l_etat_vide(self):
        # `exists: false` et `not_contains` sont des garde-fous : ils passent
        # sur le vide par nature. On exige seulement que l'oracle les passe.
        ecrire(
            self.cas / "case.yaml",
            "name: garde\n"
            "graders:\n"
            "  - {name: pas-de-fichier, type: file_exists, path: '*.tmp', exists: false}\n"
            "  - {name: pas-d-excuse, type: regex, pattern: 'désolé', match: not_contains}\n"
            "  - {name: repond, type: regex, pattern: '^OK$'}\n",
        )
        ecrire(self.cas / "oracle" / "reponse.md", "OK\n")
        verdict = evals_ab.previol_cas(self.cas)
        self.assertEqual(verdict.erreurs, [])

    def test_un_juge_payant_est_signale_non_verifie_sans_refuser_le_cas(self):
        self.cas_prose()
        ecrire(self.cas / "graders" / "qualite.md", "---\ntype: llm\n---\n\nPASS si clair.\n")
        verdict = evals_ab.previol_cas(self.cas)
        self.assertEqual(verdict.erreurs, [])
        self.assertTrue(any("qualite" in n for n in verdict.non_verifies))


# --------------------------------------------------------------------------
# Bout en bout, sur un vrai petit dépôt git et un faux lanceur
# --------------------------------------------------------------------------
FAUX_LANCEUR = """#!/bin/sh
# Faux lanceur : ne lance aucune évaluation. Il choisit le rapport figé selon
# le marqueur que l'extraction git a posé dans la copie du plugin.
dossier="$1"; sortie="$2"; shift 2
marqueur=$(cat "$dossier/marqueur.txt")
{
  echo "APPEL $marqueur"
  echo "OPTIONS $*"
  echo "DOSSIER $dossier"
  (cd "$dossier" && find evals -type f | sort | sed 's/^/FICHIER /')
} >> "$FAUX_JOURNAL"
if [ "$marqueur" = "base" ]; then cp "$FAUX_RAPPORT_BASE" "$sortie"; else cp "$FAUX_RAPPORT_TETE" "$sortie"; fi
exit "${FAUX_CODE:-0}"
"""


def git(depot: Path, *args: str) -> str:
    resultat = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=depot, check=True, capture_output=True, text=True,
    )
    return resultat.stdout


class DepotEtLanceur(unittest.TestCase):
    """Fabrique un dépôt jetable : plugin ``jouet`` à deux versions + cas."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name)
        self.depot = self.racine / "depot"
        self.depot.mkdir()
        git(self.depot, "init", "-q", "-b", "main")
        ecrire(self.depot / "plugins" / "jouet" / "marqueur.txt", "base")
        ecrire(self.depot / "plugins" / "jouet" / "skills" / "s" / "SKILL.md", "v1\n")
        git(self.depot, "add", ".")
        git(self.depot, "commit", "-q", "-m", "v1")
        git(self.depot, "tag", "v-base")
        ecrire(self.depot / "plugins" / "jouet" / "marqueur.txt", "tete")
        ecrire(self.depot / "plugins" / "jouet" / "skills" / "s" / "SKILL.md", "v2\n")
        git(self.depot, "add", ".")
        git(self.depot, "commit", "-q", "-m", "v2")
        git(self.depot, "tag", "v-tete")
        # Un cas valide, avec son oracle (qui ne doit jamais atteindre la copie).
        cas = self.depot / "evals" / "jouet" / "alpha"
        ecrire(cas / "prompt.md", "---\nmax_turns: 3\n---\n\nRéponds OK.\n")
        ecrire(cas / "graders" / "reponse.md", "---\ntype: regex\npattern: \"^OK$\"\n---\n")
        ecrire(cas / "oracle" / "reponse.md", "OK\n")
        git(self.depot, "add", ".")
        git(self.depot, "commit", "-q", "-m", "cas")
        # Faux lanceur et journaux.
        self.lanceur = self.racine / "faux_lanceur.sh"
        ecrire(self.lanceur, FAUX_LANCEUR)
        self.lanceur.chmod(0o755)
        self.journal_appels = self.racine / "appels.log"
        self.journal = self.racine / "RESULTATS.md"
        self.env = {
            "FAUX_JOURNAL": str(self.journal_appels),
            "FAUX_RAPPORT_BASE": str(FIXTURES / "rapport_base.json"),
            "FAUX_RAPPORT_TETE": str(FIXTURES / "rapport_tete_stable.json"),
            "FAUX_CODE": "0",
            "EVALS_MODELE": MODELE,
        }

    def argv(self, *extra: str, mode: str = "ab") -> list[str]:
        return [
            "--plugin", "jouet", "--mode", mode,
            "--base", "v-base", "--tete", "v-tete",
            "--depot", str(self.depot), "--lanceur", str(self.lanceur),
            *extra,
        ]

    def appels(self) -> list[str]:
        if not self.journal_appels.exists():
            return []
        return self.journal_appels.read_text("utf-8").splitlines()

    def instantane_depot(self) -> tuple[str, str]:
        statut = git(self.depot, "status", "--porcelain", "--ignored")
        empreintes = subprocess.run(
            "find . -path ./.git -prune -o -type f -print0 | sort -z | xargs -0 sha256sum",
            shell=True, cwd=self.depot, capture_output=True, text=True, check=True,
        ).stdout
        return statut, empreintes


class Extraction(DepotEtLanceur):
    def test_chaque_copie_porte_le_plugin_a_sa_reference(self):
        base, tete = self.racine / "b", self.racine / "t"
        evals_ab.extraire(self.depot, "v-base", "jouet", base)
        evals_ab.extraire(self.depot, "v-tete", "jouet", tete)
        self.assertEqual((base / "skills" / "s" / "SKILL.md").read_text(), "v1\n")
        self.assertEqual((tete / "skills" / "s" / "SKILL.md").read_text(), "v2\n")
        self.assertEqual((base / "marqueur.txt").read_text(), "base")

    def test_une_reference_inconnue_est_un_refus_lisible(self):
        with self.assertRaises(evals_ab.ErreurRefus) as ctx:
            evals_ab.extraire(self.depot, "n-existe-pas", "jouet", self.racine / "x")
        self.assertIn("n-existe-pas", str(ctx.exception))

    def test_l_assemblage_pose_les_cas_sans_leur_oracle(self):
        # L'agent évalué a accès aux fichiers de la copie : l'oracle (l'état
        # final idéal) ne doit pas s'y trouver.
        copie = self.racine / "copie"
        evals_ab.extraire(self.depot, "v-tete", "jouet", copie)
        evals_ab.assembler(copie, [self.depot / "evals" / "jouet"])
        fichiers = sorted(
            str(p.relative_to(copie)) for p in (copie / "evals").rglob("*") if p.is_file()
        )
        self.assertEqual(
            fichiers,
            ["evals/alpha/graders/reponse.md", "evals/alpha/prompt.md"],
        )

    def test_l_assemblage_ne_touche_pas_le_depot(self):
        avant = self.instantane_depot()
        copie = self.racine / "copie"
        evals_ab.extraire(self.depot, "v-tete", "jouet", copie)
        evals_ab.assembler(copie, [self.depot / "evals" / "jouet"])
        self.assertEqual(self.instantane_depot(), avant)


class BoutEnBout(DepotEtLanceur):
    def test_un_ab_sans_recul_rend_zero_et_un_tableau(self):
        code, sortie, _ = jouer(self.argv(), self.env)
        self.assertEqual(code, 0, sortie)
        self.assertIn("| alpha ", sortie)
        self.assertIn("| beta ", sortie)
        self.assertNotIn("RECUL", sortie)

    def test_un_ab_avec_recul_rend_un(self):
        # Bruit mesuré rms 0,2 (seuil par cas de Bonferroni, 4 cas : 0,4995) :
        # gamma perd 1,0. Sans fichier de bruit, le seuil estimé 1,04 (4 cas x 3
        # passages) ne laisse plus un cas reculer seul.
        bruit = self.racine / "bruit-recul.json"
        ecrire(bruit, json.dumps({"rms_ecarts_cas": 0.2, "modele": MODELE}))
        self.env["FAUX_RAPPORT_TETE"] = str(FIXTURES / "rapport_tete_recul_cas.json")
        code, sortie, _ = jouer(self.argv("--bruit", str(bruit)), self.env)
        self.assertEqual(code, 1, sortie)
        self.assertIn("RECUL", sortie)

    def test_le_lanceur_joue_chaque_reference_sur_sa_propre_copie(self):
        jouer(self.argv(), self.env)
        marqueurs = [ligne for ligne in self.appels() if ligne.startswith("APPEL")]
        self.assertEqual(marqueurs, ["APPEL base", "APPEL tete"])

    def test_les_cas_sont_assembles_dans_les_deux_copies_sans_oracle(self):
        jouer(self.argv(), self.env)
        fichiers = [ligne for ligne in self.appels() if ligne.startswith("FICHIER")]
        self.assertEqual(fichiers.count("FICHIER evals/alpha/prompt.md"), 2)
        self.assertFalse(any("oracle" in f for f in fichiers))

    def test_les_options_apres_deux_tirets_vont_au_lanceur(self):
        jouer(self.argv("--", "--runs", "3", "--model", "haiku"), self.env)
        options = [ligne for ligne in self.appels() if ligne.startswith("OPTIONS")]
        self.assertEqual(options, ["OPTIONS --runs 3 --model haiku"] * 2)

    def test_le_depot_est_intact_apres_un_passage_complet(self):
        avant = self.instantane_depot()
        jouer(self.argv(), self.env)
        self.assertEqual(self.instantane_depot(), avant)

    def test_un_rapport_partiel_est_refuse_avec_code_trois(self):
        self.env["FAUX_RAPPORT_TETE"] = str(FIXTURES / "rapport_partiel.json")
        code, sortie, erreur = jouer(self.argv(), self.env)
        self.assertEqual(code, 3)
        self.assertIn("partial", erreur)

    def test_un_lanceur_qui_rend_deux_signale_un_rapport_partiel(self):
        self.env["FAUX_CODE"] = "2"
        code, _, erreur = jouer(self.argv(), self.env)
        self.assertEqual(code, 3)
        self.assertIn("partiel", erreur)

    def test_un_lanceur_qui_rend_un_seuil_non_atteint_n_est_pas_une_panne(self):
        # `claude plugin eval` rend 1 quand un cas est sous son seuil : c'est
        # le sujet même de la comparaison, pas un échec de lancement.
        self.env["FAUX_CODE"] = "1"
        code, _, _ = jouer(self.argv(), self.env)
        self.assertEqual(code, 0)

    def test_un_lanceur_qui_plante_est_un_refus(self):
        self.env["FAUX_CODE"] = "137"
        code, _, erreur = jouer(self.argv(), self.env)
        self.assertEqual(code, 3)
        self.assertIn("137", erreur)

    def test_un_cas_dont_l_oracle_echoue_est_refuse_avant_tout_jeu(self):
        mauvais = self.depot / "evals" / "jouet" / "casse"
        ecrire(mauvais / "prompt.md", "---\nmax_turns: 3\n---\n\nRéponds OK.\n")
        ecrire(mauvais / "graders" / "r.md", "---\ntype: regex\npattern: \"^OK$\"\n---\n")
        ecrire(mauvais / "oracle" / "reponse.md", "peut-être\n")
        code, _, erreur = jouer(self.argv(), self.env)
        self.assertEqual(code, 3)
        self.assertIn("casse", erreur)
        self.assertEqual(self.appels(), [])  # rien n'a été joué, donc rien payé

    def test_les_temporaires_sont_supprimes_sauf_si_on_les_garde(self):
        jouer(self.argv(), self.env)
        dossiers = [l.split(" ", 1)[1] for l in self.appels() if l.startswith("DOSSIER")]
        self.assertEqual(len(dossiers), 2)
        self.assertFalse(any(Path(d).exists() for d in dossiers))

        self.journal_appels.unlink()
        jouer(self.argv("--conserver"), self.env)
        gardes = [l.split(" ", 1)[1] for l in self.appels() if l.startswith("DOSSIER")]
        try:
            self.assertTrue(all(Path(d).exists() for d in gardes))
        finally:
            for d in gardes:
                shutil.rmtree(Path(d).parents[1], ignore_errors=True)

    def test_avec_reference_la_base_n_est_pas_rejouee(self):
        code, sortie, _ = jouer(
            self.argv("--reference", str(FIXTURES / "rapport_base.json")), self.env
        )
        self.assertEqual(code, 0, sortie)
        marqueurs = [l for l in self.appels() if l.startswith("APPEL")]
        self.assertEqual(marqueurs, ["APPEL tete"])

    def test_une_reference_partielle_est_refusee(self):
        code, _, erreur = jouer(
            self.argv("--reference", str(FIXTURES / "rapport_partiel.json")), self.env
        )
        self.assertEqual(code, 3)
        self.assertIn("partial", erreur)

    def test_un_banc_prive_ajoute_ses_cas_aux_deux_copies(self):
        prive = self.racine / "prive"
        cas = prive / "secret"
        ecrire(cas / "prompt.md", "---\nmax_turns: 3\n---\n\nRéponds OK.\n")
        ecrire(cas / "graders" / "r.md", "---\ntype: regex\npattern: \"^OK$\"\n---\n")
        ecrire(cas / "oracle" / "reponse.md", "OK\n")
        jouer(self.argv("--prive", str(prive)), self.env)
        fichiers = [l for l in self.appels() if l.startswith("FICHIER")]
        self.assertEqual(fichiers.count("FICHIER evals/secret/prompt.md"), 2)
        self.assertEqual(fichiers.count("FICHIER evals/alpha/prompt.md"), 2)

    def test_un_meme_cas_dans_le_public_et_le_prive_est_refuse_avant_tout_jeu(self):
        prive = self.racine / "prive"
        doublon = prive / "alpha"  # « alpha » existe déjà dans le banc public
        ecrire(doublon / "prompt.md", "---\nmax_turns: 3\n---\n\nRéponds OK.\n")
        ecrire(doublon / "graders" / "r.md", "---\ntype: regex\npattern: \"^OK$\"\n---\n")
        ecrire(doublon / "oracle" / "reponse.md", "OK\n")
        code, _, erreur = jouer(self.argv("--prive", str(prive)), self.env)
        self.assertEqual(code, 3)
        self.assertIn("alpha", erreur)
        self.assertEqual(self.appels(), [])  # rien n'a été joué, donc rien payé

    def test_le_journal_recoit_une_ligne_avec_versions_bruit_et_commande(self):
        code, _, _ = jouer(self.argv("--journal", str(self.journal)), self.env)
        self.assertEqual(code, 0)
        texte = self.journal.read_text("utf-8")
        lignes = [l for l in texte.splitlines() if l.startswith("| ") and "v-base" in l]
        self.assertEqual(len(lignes), 1)
        self.assertIn("v-tete", lignes[0])
        self.assertIn("jouet", lignes[0])
        self.assertIn("±", lignes[0])
        self.assertIn("--plugin jouet", lignes[0])  # la commande jouée

    def test_sans_journal_aucun_fichier_de_resultats_n_est_ecrit(self):
        jouer(self.argv(), self.env)
        self.assertFalse(self.journal.exists())
        self.assertFalse((self.depot / "evals" / "RESULTATS.md").exists())

    def test_le_mode_aa_ecrit_un_bruit_reutilisable_par_bruit(self):
        sortie_bruit = self.racine / "bruit.json"
        code, sortie, _ = jouer(
            self.argv("--sortie-bruit", str(sortie_bruit), mode="aa"), self.env
        )
        self.assertEqual(code, 0, sortie)
        # Mode aa : la même référence (la tête) est jouée deux fois.
        marqueurs = [l for l in self.appels() if l.startswith("APPEL")]
        self.assertEqual(marqueurs, ["APPEL tete", "APPEL tete"])
        bruit = json.loads(sortie_bruit.read_text("utf-8"))
        self.assertIn("rms_ecarts_cas", bruit)
        self.assertIn("demi_largeur_ic95_globale", bruit)

        # Et le fichier est réellement consommé par un A/B : rms 0,5 rend
        # acceptable le recul global de -5/12 (cf. tests de comparaison).
        ecrire(sortie_bruit, json.dumps({"rms_ecarts_cas": 0.5, "modele": MODELE}))
        self.env["FAUX_RAPPORT_TETE"] = str(FIXTURES / "rapport_tete_recul_global.json")
        code, _, _ = jouer(self.argv("--bruit", str(sortie_bruit)), self.env)
        self.assertEqual(code, 0)
        code, _, _ = jouer(self.argv(), self.env)  # sans bruit mesuré : recul
        self.assertEqual(code, 1)

    def test_une_option_de_ligne_de_commande_inconnue_est_un_echec_d_usage(self):
        code, _, _ = jouer(["--n-importe-quoi"], self.env)
        self.assertEqual(code, 2)


# --------------------------------------------------------------------------
# Étape B9 : des cas choisis (--cas), un bruit qui porte son modèle, un seuil
# qui dit quand il ne voit rien
# --------------------------------------------------------------------------
# Faux lanceur qui écrit un rapport dont les cas sont ceux **réellement
# assemblés** dans la copie (3 passages, tous réussis) : ce qui est joué se lit
# dans le rapport, donc dans le nombre de cas du tableau.
LANCEUR_QUI_LIT_LES_CAS = """#!/bin/sh
dossier="$1"; sortie="$2"; shift 2
python3 - "$dossier" "$sortie" <<'PY'
import json, pathlib, sys
copie, sortie = pathlib.Path(sys.argv[1]), sys.argv[2]
noms = sorted(p.name for p in (copie / "evals").iterdir() if p.is_dir())
passage = {"score": 1, "passed": True, "costUsd": 0, "judgeCostUsd": 0}
cas = [{"name": n, "arms": {"with": [passage, passage, passage]}, "aggregates": {"score": 1}}
       for n in noms]
json.dump({"schemaVersion": 1, "cases": cas}, open(sortie, "w"))
PY
exit 0
"""


class CasChoisis(DepotEtLanceur):
    def ajouter_cas(self, nom: str) -> None:
        cas = self.depot / "evals" / "jouet" / nom
        ecrire(cas / "prompt.md", "---\nmax_turns: 3\n---\n\nRéponds OK.\n")
        ecrire(cas / "graders" / "reponse.md", "---\ntype: regex\npattern: \"^OK$\"\n---\n")
        ecrire(cas / "oracle" / "reponse.md", "OK\n")

    def fichiers_poses(self) -> list[str]:
        return [l for l in self.appels() if l.startswith("FICHIER")]

    def test_assembler_ne_copie_que_les_cas_demandes(self):
        self.ajouter_cas("beta")
        self.ajouter_cas("gamma")
        copie = self.racine / "copie"
        evals_ab.extraire(self.depot, "v-tete", "jouet", copie)
        poses = evals_ab.assembler(copie, [self.depot / "evals" / "jouet"], cas=["gamma", "alpha"])
        self.assertEqual(sorted(poses), ["alpha", "gamma"])
        self.assertEqual(
            sorted(p.name for p in (copie / "evals").iterdir()), ["alpha", "gamma"]
        )

    def test_assembler_sans_liste_de_cas_les_pose_tous(self):
        self.ajouter_cas("beta")
        copie = self.racine / "copie"
        evals_ab.extraire(self.depot, "v-tete", "jouet", copie)
        poses = evals_ab.assembler(copie, [self.depot / "evals" / "jouet"])
        self.assertEqual(sorted(poses), ["alpha", "beta"])

    def test_assembler_refuse_un_nom_de_cas_inconnu_et_le_nomme(self):
        copie = self.racine / "copie"
        evals_ab.extraire(self.depot, "v-tete", "jouet", copie)
        with self.assertRaises(evals_ab.ErreurRefus) as ctx:
            evals_ab.assembler(copie, [self.depot / "evals" / "jouet"], cas=["alpha", "fantome"])
        self.assertIn("fantome", str(ctx.exception))

    def test_cas_ne_joue_que_ces_cas_dans_les_deux_copies(self):
        self.ajouter_cas("beta")
        self.ajouter_cas("gamma")
        code, sortie, _ = jouer(self.argv("--cas", "alpha", "--cas", "beta"), self.env)
        self.assertEqual(code, 0, sortie)
        fichiers = self.fichiers_poses()
        for cas in ("alpha", "beta"):
            self.assertEqual(fichiers.count(f"FICHIER evals/{cas}/prompt.md"), 2, cas)
        self.assertFalse(any("gamma" in f for f in fichiers))
        self.assertFalse(any("oracle" in f for f in fichiers))

    def test_sans_cas_tous_les_cas_sont_joues(self):
        self.ajouter_cas("beta")
        jouer(self.argv(), self.env)
        fichiers = self.fichiers_poses()
        self.assertEqual(fichiers.count("FICHIER evals/alpha/prompt.md"), 2)
        self.assertEqual(fichiers.count("FICHIER evals/beta/prompt.md"), 2)

    def test_un_nom_de_cas_inconnu_est_refuse_avec_code_trois_avant_tout_jeu(self):
        code, _, erreur = jouer(self.argv("--cas", "alpha", "--cas", "fantome"), self.env)
        self.assertEqual(code, 3)
        self.assertIn("fantome", erreur)
        self.assertEqual(self.appels(), [])  # rien n'a été joué, donc rien payé

    def test_le_seuil_de_bonferroni_se_calcule_sur_les_cas_joues_pas_sur_ceux_du_banc(self):
        # Trois cas au banc, deux joués : z_2 = inv_cdf(1 - 0,05/4) = 2,2414
        # (table de la loi normale) ; rms 0,1 -> seuil par cas 0,2241 = 22 pts.
        # Avec les trois cas du banc, z_3 = 2,3940 donnerait 24 pts.
        self.ajouter_cas("beta")
        self.ajouter_cas("gamma")
        lanceur = self.racine / "lanceur_lecteur.sh"
        ecrire(lanceur, LANCEUR_QUI_LIT_LES_CAS)
        lanceur.chmod(0o755)
        bruit = self.racine / "bruit.json"
        ecrire(bruit, json.dumps({"rms_ecarts_cas": 0.1, "modele": MODELE}))
        argv = [a for a in self.argv("--cas", "alpha", "--cas", "beta", "--bruit", str(bruit))]
        argv[argv.index("--lanceur") + 1] = str(lanceur)
        code, sortie, erreur = jouer(argv, self.env)
        self.assertEqual(code, 0, erreur)
        self.assertIn("2 cas \u00d7 3 passages", sortie)
        self.assertIn("seuil par cas (Bonferroni, 2 cas) : \u00b1 22 pts", sortie)
        self.assertNotIn("gamma", sortie)


class BruitEtModele(DepotEtLanceur):
    def bruit(self, **champs) -> str:
        chemin = self.racine / "bruit.json"
        ecrire(chemin, json.dumps({"rms_ecarts_cas": 0.2, **champs}))
        return str(chemin)

    def test_un_bruit_du_bon_modele_est_utilise(self):
        code, sortie, _ = jouer(self.argv("--bruit", self.bruit(modele=MODELE)), self.env)
        self.assertEqual(code, 0, sortie)
        self.assertIn("mesuré en A/A", sortie)
        self.assertNotIn("ignoré", sortie)

    def test_un_bruit_d_un_autre_modele_est_ignore_et_le_tableau_le_dit(self):
        code, sortie, _ = jouer(
            self.argv("--bruit", self.bruit(modele="claude-sonnet-5-5")), self.env
        )
        self.assertEqual(code, 0, sortie)
        self.assertIn(
            "bruit de claude-sonnet-5-5 ignoré : les cas sont joués sur "
            f"{MODELE} — seuil estimé", sortie)
        self.assertIn("estimé", sortie.split("Bruit (")[1].split(",")[0])
        self.assertNotIn("mesuré en A/A", sortie)

    def test_un_bruit_sans_modele_est_ignore_lui_aussi(self):
        code, sortie, _ = jouer(self.argv("--bruit", self.bruit()), self.env)
        self.assertEqual(code, 0, sortie)
        self.assertIn("ignoré", sortie)
        self.assertIn("seuil estimé", sortie)
        self.assertNotIn("mesuré en A/A", sortie)

    def test_le_modele_joue_vient_de_evals_modele(self):
        self.env["EVALS_MODELE"] = "claude-sonnet-5-5"
        _, sortie, _ = jouer(self.argv("--bruit", self.bruit(modele="claude-sonnet-5-5")), self.env)
        self.assertIn("mesuré en A/A", sortie)
        _, sortie, _ = jouer(self.argv("--bruit", self.bruit(modele=MODELE)), self.env)
        self.assertIn(f"bruit de {MODELE} ignoré : les cas sont joués sur claude-sonnet-5-5",
                      sortie)

    def test_sans_evals_modele_le_modele_joue_est_claude_opus_5_5(self):
        del self.env["EVALS_MODELE"]
        ancien = os.environ.pop("EVALS_MODELE", None)
        try:
            _, sortie, _ = jouer(self.argv("--bruit", self.bruit(modele="claude-opus-5-5")),
                                 self.env)
        finally:
            if ancien is not None:
                os.environ["EVALS_MODELE"] = ancien
        self.assertIn("mesuré en A/A", sortie)
        self.assertNotIn("ignoré", sortie)

    def test_le_bruit_ecrit_par_le_mode_aa_porte_le_modele_joue(self):
        self.env["EVALS_MODELE"] = "claude-sonnet-5-5"
        sortie_bruit = self.racine / "bruit-aa.json"
        code, _, _ = jouer(self.argv("--sortie-bruit", str(sortie_bruit), mode="aa"), self.env)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sortie_bruit.read_text("utf-8"))["modele"],
                         "claude-sonnet-5-5")

    def test_le_fichier_de_bruit_du_depot_declare_son_modele(self):
        bruit = json.loads((Path(__file__).resolve().parents[1] / "evals"
                            / "bruit-plans-notion.json").read_text("utf-8"))
        self.assertEqual(bruit["modele"], "claude-opus-5-5")


class SeuilQuiNePeutRienVoir(unittest.TestCase):
    """Un seuil par cas d'au moins 100 points ne peut jamais être franchi (un
    score va de 0 à 1) : afficher « pas de recul » serait une affirmation sans
    contenu. Le run de la PR #17 avait affiché « seuil par cas ± 123 pts »."""

    def test_16_cas_x_3_passages_sans_bruit_donnent_un_seuil_de_123_points(self):
        # Sur le papier : racine(2)/racine(3) x 2,9552/1,96 = 0,8165 x 1,5078 = 1,231.
        base, tete = jeux_uniformes(16, 1.0, 0.0)
        c = evals_ab.comparer(base, tete)
        self.assertAlmostEqual(c.bruit_cas, 1.231, places=2)
        self.assertFalse(any(ligne.recul for ligne in c.lignes))

    def test_un_seuil_de_100_points_ou_plus_ne_produit_jamais_pas_de_recul(self):
        for n in (4, 9, 16):
            with self.subTest(cas=n):
                base, tete = jeux_uniformes(n, 1.0, 1.0)
                c = evals_ab.comparer(base, tete)
                self.assertGreaterEqual(c.bruit_cas, 1.0)
                tableau = evals_ab.tableau_markdown(c, "v1", "v2")
                self.assertNotIn("pas de recul au-delà du bruit", tableau)
                self.assertIn(
                    "non concluant par cas — aucun fichier de bruit mesuré pour ce modèle",
                    tableau)
                self.assertIn(
                    "**Verdict : pas de recul de la moyenne ; non concluant par cas.**",
                    tableau)

    def test_un_recul_de_la_moyenne_reste_un_recul_meme_avec_un_seuil_aveugle(self):
        base, tete = jeux_uniformes(4, 1.0, 1.0)
        tete = rapport_synthetique({f"c{i}": [0, 0, 0] for i in range(4)})
        c = evals_ab.comparer(base, tete)
        self.assertTrue(c.recul)
        self.assertIn("RECUL", evals_ab.tableau_markdown(c, "v1", "v2").splitlines()[-1])

    def test_un_seuil_mesure_sous_100_points_garde_le_verdict_habituel(self):
        base, tete = jeux_uniformes(16, 1.0, 1.0)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.0385})
        tableau = evals_ab.tableau_markdown(c, "v1", "v2")
        self.assertIn("**Verdict : pas de recul au-delà du bruit.**", tableau)
        self.assertNotIn("non concluant", tableau)

    def test_un_bruit_mesure_trop_large_est_dit_non_concluant_sans_pretendre_qu_il_manque(self):
        base, tete = jeux_uniformes(4, 1.0, 1.0)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.5})  # 2,4977 x 0,5 > 1
        tableau = evals_ab.tableau_markdown(c, "v1", "v2")
        self.assertIn("non concluant par cas", tableau)
        self.assertNotIn("aucun fichier de bruit mesuré", tableau)
        self.assertNotIn("pas de recul au-delà du bruit", tableau)

    def test_les_lignes_d_un_tableau_aveugle_ne_disent_pas_dans_le_bruit(self):
        base, tete = jeux_uniformes(4, 1.0, 0.0)  # c0 tombe de 100 points
        tete = rapport_synthetique(
            {"c0": [0, 0, 0], "c1": [1, 1, 1], "c2": [1, 1, 1], "c3": [1, 1, 1]})
        c = evals_ab.comparer(base, tete)
        ligne = next(l for l in evals_ab.tableau_markdown(c, "v1", "v2").splitlines()
                     if l.startswith("| c0 "))
        self.assertNotIn("dans le bruit", ligne)
        self.assertIn("non concluant", ligne)

    def test_un_seuil_aveugle_ne_change_pas_le_code_de_sortie(self):
        # Pas de rouge pour ça : le code de sortie ne dépend que du recul mesuré.
        self.assertFalse(evals_ab.comparer(*jeux_uniformes(16, 1.0, 1.0)).recul)


class SeuilGlobalElargi(unittest.TestCase):
    def test_moins_de_cas_joues_que_mesures_elargit_le_seuil_global_et_le_tableau_le_dit(self):
        # Bruit mesuré sur 16 cas (rms 0,0385) : global 1,96 x 0,0385 / 4 = 1,9 pts.
        # 4 cas joués : 1,96 x 0,0385 / 2 = 3,8 pts.
        base, tete = jeux_uniformes(4, 1.0, 1.0)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.0385, "n_cas": 16})
        self.assertAlmostEqual(c.bruit_global, 1.96 * 0.0385 / 2, places=6)
        tableau = evals_ab.tableau_markdown(c, "v1", "v2")
        self.assertIn("4 cas joués sur 16", tableau)
        self.assertIn("seuil global élargi", tableau)

    def test_autant_de_cas_que_mesures_n_ajoute_aucune_ligne(self):
        base, tete = jeux_uniformes(16, 1.0, 1.0)
        c = evals_ab.comparer(base, tete, bruit={"rms_ecarts_cas": 0.0385, "n_cas": 16})
        self.assertNotIn("élargi", evals_ab.tableau_markdown(c, "v1", "v2"))


if __name__ == "__main__":
    unittest.main()
