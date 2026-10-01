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
MODELE = "claude-sonnet-5-5"  # le modèle joué par défaut (étape B9)
AUTRE_MODELE = "claude-opus-5-5"  # un modèle qui n'est pas celui joué


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

    def test_une_aa_dont_un_jeu_a_des_sessions_en_erreur_rend_quatre_et_n_ecrit_pas_de_bruit(self):
        # Un jeu perd 6 sessions sur 9 à une limite de session : ses scores s'effondrent,
        # le rms de l'écart entre les deux jeux est gonflé, et toute A/B qui lirait ce
        # fichier jugerait avec un seuil faux. Même règle que l'A/B : code 4, aucun bruit.
        # Le faux lanceur de la classe rend le même rapport aux deux passages ; celui-ci
        # rend la fixture en panne au premier et sa copie sans erreur au second.
        sain = rapport("tete_session_limite")
        for c in sain["cases"]:
            for passage in c["arms"]["with"]:
                passage["error"] = None
        ecrire(self.racine / "jeu-sain.json", json.dumps(sain))
        ecrire(
            self.lanceur,
            FAUX_LANCEUR.replace(
                'if [ "$marqueur" = "base" ]; then cp "$FAUX_RAPPORT_BASE" "$sortie"; '
                'else cp "$FAUX_RAPPORT_TETE" "$sortie"; fi',
                'if [ "$(grep -c "^APPEL" "$FAUX_JOURNAL")" = "1" ]; '
                'then cp "$FAUX_RAPPORT_TETE" "$sortie"; else cp "$FAUX_RAPPORT_BASE" "$sortie"; fi',
            ),
        )
        self.env["FAUX_RAPPORT_TETE"] = str(FIXTURES / "rapport_tete_session_limite.json")
        self.env["FAUX_RAPPORT_BASE"] = str(self.racine / "jeu-sain.json")
        sortie_bruit = self.racine / "bruit.json"
        code, sortie, erreur = jouer(
            self.argv("--sortie-bruit", str(sortie_bruit), mode="aa"), self.env
        )
        self.assertEqual(code, 4, sortie + erreur)
        self.assertFalse(sortie_bruit.exists())
        self.assertIn("non concluant", sortie.lower())
        self.assertIn("panne d'infrastructure, à relancer", sortie)
        self.assertIn("6 sur 9", sortie)
        self.assertNotIn("Bruit mesuré", sortie)

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
            self.argv("--bruit", self.bruit(modele=AUTRE_MODELE)), self.env
        )
        self.assertEqual(code, 0, sortie)
        self.assertIn(
            f"bruit de {AUTRE_MODELE} ignoré : les cas sont joués sur "
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
        self.env["EVALS_MODELE"] = AUTRE_MODELE
        _, sortie, _ = jouer(self.argv("--bruit", self.bruit(modele=AUTRE_MODELE)), self.env)
        self.assertIn("mesuré en A/A", sortie)
        _, sortie, _ = jouer(self.argv("--bruit", self.bruit(modele=MODELE)), self.env)
        self.assertIn(f"bruit de {MODELE} ignoré : les cas sont joués sur {AUTRE_MODELE}",
                      sortie)

    def test_le_modele_par_defaut_est_claude_sonnet_5_5(self):
        # Écrit en dur : l'attendu ne dérive pas de la constante testée.
        self.assertEqual(evals_ab.MODELE_PAR_DEFAUT, "claude-sonnet-5-5")

    def test_sans_evals_modele_le_modele_joue_est_claude_sonnet_5_5(self):
        del self.env["EVALS_MODELE"]
        ancien = os.environ.pop("EVALS_MODELE", None)
        try:
            _, sortie, _ = jouer(self.argv("--bruit", self.bruit(modele="claude-sonnet-5-5")),
                                 self.env)
            _, sortie_opus, _ = jouer(self.argv("--bruit", self.bruit(modele="claude-opus-5-5")),
                                      self.env)
        finally:
            if ancien is not None:
                os.environ["EVALS_MODELE"] = ancien
        self.assertIn("mesuré en A/A", sortie)
        self.assertNotIn("ignoré", sortie)
        # Le bruit d'Opus, seul fichier du dépôt aujourd'hui, n'est plus celui du modèle joué.
        self.assertIn("bruit de claude-opus-5-5 ignoré : les cas sont joués sur "
                      "claude-sonnet-5-5", sortie_opus)

    def test_le_bruit_ecrit_par_le_mode_aa_porte_le_modele_joue(self):
        self.env["EVALS_MODELE"] = AUTRE_MODELE
        sortie_bruit = self.racine / "bruit-aa.json"
        code, _, _ = jouer(self.argv("--sortie-bruit", str(sortie_bruit), mode="aa"), self.env)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sortie_bruit.read_text("utf-8"))["modele"], AUTRE_MODELE)

    def test_le_bruit_ecrit_par_le_mode_aa_porte_l_effort_joue(self):
        self.env["EVALS_EFFORT"] = "low"
        sortie_bruit = self.racine / "bruit-aa.json"
        code, _, _ = jouer(self.argv("--sortie-bruit", str(sortie_bruit), mode="aa"), self.env)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sortie_bruit.read_text("utf-8"))["effort"], "low")

    def test_le_tableau_dit_le_modele_et_l_effort_joues(self):
        self.env["EVALS_EFFORT"] = "medium"
        _, sortie, _ = jouer(self.argv(), self.env)
        self.assertIn(f"Modèle joué : {MODELE}, effort medium.", sortie)

    def test_sans_evals_effort_le_tableau_dit_l_effort_high(self):
        self.env.pop("EVALS_EFFORT", None)
        ancien = os.environ.pop("EVALS_EFFORT", None)
        try:
            _, sortie, _ = jouer(self.argv(), self.env)
        finally:
            if ancien is not None:
                os.environ["EVALS_EFFORT"] = ancien
        self.assertIn("effort high.", sortie)

    def test_le_fichier_de_bruit_du_depot_declare_son_modele(self):
        bruit = json.loads((Path(__file__).resolve().parents[1] / "evals"
                            / "bruit-plans-notion.json").read_text("utf-8"))
        # Tant que la mesure de Sonnet n'est pas commitée, ce fichier porte Opus ;
        # après, Sonnet. Le contrat testé : il déclare un modèle, sans quoi
        # `filtrer_bruit` l'ignorerait toujours.
        self.assertIsInstance(bruit.get("modele"), str)
        self.assertTrue(bruit["modele"].startswith("claude-"), bruit["modele"])


class LanceurModeleEtEffort(unittest.TestCase):
    """``evals/outillage/lancer.sh`` avec un faux ``claude`` dans le ``PATH`` : le
    faux écrit dans un fichier ce qu'il a reçu (arguments et effort), rien
    d'autre. Aucun vrai appel, aucun jeton réel (un jeton factice sert à vérifier
    que le lanceur ne l'affiche pas).

    Hors CI, le lanceur contrôle les bancs de CI avec ``gh`` puis prend le jeton
    machine : un faux ``gh`` (aucun run en cours) et un ``XDG_STATE_HOME`` jetable
    simulent ces deux gardes, de sorte que ni le vrai ``gh`` (réseau) ni le vrai
    ``~/.local/state`` ne sont touchés. Le jeton lui-même reste le vrai script, et
    il refuse une machine saturée : le relevé de ``/proc`` n'étant pas injectable
    depuis le lanceur, les tests sont alors sautés."""

    LANCEUR = Path(__file__).resolve().parents[1] / "evals" / "outillage" / "lancer.sh"
    ETAT_MACHINE = (Path(__file__).resolve().parents[1] / "plugins" / "plans-notion"
                    / "skills" / "_partage" / "scripts" / "etat-machine.py")
    JETON = "jeton-factice-a-ne-jamais-afficher"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name)
        self.bin = self.racine / "bin"
        self.bin.mkdir()
        self.trace = self.racine / "trace.txt"
        faux = self.bin / "claude"
        faux.write_text(
            "#!/bin/sh\n"
            f'echo "effort=${{CLAUDE_CODE_EFFORT_LEVEL-<absent>}}" >> "{self.trace}"\n'
            f'echo "args=$*" >> "{self.trace}"\n'
            "exit 0\n", "utf-8")
        faux.chmod(0o755)
        # Faux gh : aucun run en cours (sortie vide, code 0), sans réseau.
        gh = self.bin / "gh"
        gh.write_text("#!/bin/sh\nexit 0\n", "utf-8")
        gh.chmod(0o755)
        releve = subprocess.run([sys.executable, str(self.ETAT_MACHINE), "releve"],
                                capture_output=True, text=True, timeout=30)
        if releve.stdout.splitlines()[:1] == ["saturée"]:
            self.skipTest("la machine est saturée : le jeton refuse, quoi que fasse le lanceur")

    def _lancer(self, **env_extra) -> tuple[subprocess.CompletedProcess, str]:
        assert "GITHUB_ACTIONS" not in env_extra, "jamais de GITHUB_ACTIONS=true dans un test"
        env = {k: v for k, v in os.environ.items()
               if k not in ("GITHUB_ACTIONS", "EVALS_MODELE", "EVALS_EFFORT",
                            "EVALS_MAX_COUT_USD", "CLAUDE_CODE_EFFORT_LEVEL", "TMPDIR")}
        env["PATH"] = f"{self.bin}{os.pathsep}{env.get('PATH', '')}"
        env["TMPDIR"] = str(self.racine / "traces")
        env["XDG_STATE_HOME"] = str(self.racine / "etat")
        env["CLAUDE_CODE_OAUTH_TOKEN"] = self.JETON
        env.update(env_extra)
        r = subprocess.run(
            ["bash", str(self.LANCEUR), str(self.racine / "plugin"), str(self.racine / "sortie.json")],
            env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r, self.trace.read_text("utf-8")

    def test_sans_evals_effort_claude_recoit_l_effort_high(self):
        _, trace = self._lancer()
        self.assertIn("effort=high\n", trace)

    def test_evals_effort_devient_claude_code_effort_level(self):
        _, trace = self._lancer(EVALS_EFFORT="low")
        self.assertIn("effort=low\n", trace)

    def test_un_evals_effort_vide_retombe_sur_high(self):
        _, trace = self._lancer(EVALS_EFFORT="")
        self.assertIn("effort=high\n", trace)

    def test_evals_effort_est_la_seule_source_meme_si_l_environnement_porte_deja_un_effort(self):
        # Une session interactive peut avoir CLAUDE_CODE_EFFORT_LEVEL dans son
        # environnement : la mesure ne doit pas en dépendre.
        _, trace = self._lancer(CLAUDE_CODE_EFFORT_LEVEL="low")
        self.assertIn("effort=high\n", trace)

    def test_le_modele_par_defaut_du_lanceur_est_claude_sonnet_5_5(self):
        _, trace = self._lancer()
        self.assertIn("--model claude-sonnet-5-5", trace)
        self.assertNotIn("claude-opus", trace)

    def test_evals_modele_remplace_le_modele_du_lanceur(self):
        _, trace = self._lancer(EVALS_MODELE="claude-opus-5-5")
        self.assertIn("--model claude-opus-5-5", trace)

    def test_le_lanceur_n_affiche_ni_le_jeton_ni_l_environnement(self):
        r, _ = self._lancer(EVALS_EFFORT="high")
        self.assertNotIn(self.JETON, r.stdout + r.stderr)
        self.assertNotIn("CLAUDE_CODE_EFFORT_LEVEL=", r.stdout + r.stderr)

    def test_le_lanceur_ne_contient_aucune_commande_qui_affiche_l_environnement(self):
        code = [l for l in self.LANCEUR.read_text("utf-8").splitlines()
                if l.strip() and not l.lstrip().startswith("#")]
        for ligne in code:
            self.assertNotRegex(ligne, r"^\s*(env|printenv|set -x|export -p|declare -x)(\s|$)", ligne)

    def test_l_en_tete_documente_les_deux_variables_et_leurs_defauts(self):
        entete = "\n".join(l for l in self.LANCEUR.read_text("utf-8").splitlines()
                           if l.startswith("#"))
        self.assertRegex(entete, r"EVALS_MODELE[^\n]*claude-sonnet-5-5")
        self.assertRegex(entete, r"EVALS_EFFORT[^\n]*high")
        self.assertIn("CLAUDE_CODE_EFFORT_LEVEL", entete)


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

# --------------------------------------------------------------------------
# Étape 3 : une base réutilisée par contenu (--base-rapport, clé par empreinte)
# --------------------------------------------------------------------------
# Faux lanceur qui note son appel, puis écrit un rapport dont les cas sont ceux
# réellement assemblés (3 passages, tous réussis) : c'est la tête.
LANCEUR_QUI_NOTE_ET_LIT_LES_CAS = """#!/bin/sh
dossier="$1"; sortie="$2"; shift 2
echo "APPEL $(cat "$dossier/marqueur.txt")" >> "$FAUX_JOURNAL"
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


class BaseReprise(DepotEtLanceur):
    """``--base-rapport`` : la base vient d'un rapport déjà joué, on en extrait les cas choisis.

    Le rapport figé ``rapport_base_16_cas.json`` porte seize cas (alpha à 1,
    beta à 2/3 sur trois passages, les autres à 1). Le banc du dépôt jetable en
    a trois : alpha, beta, et ``epsilon`` (que le rapport ne porte pas).
    """

    def setUp(self):
        super().setUp()
        CasChoisis.ajouter_cas(self, "beta")
        CasChoisis.ajouter_cas(self, "epsilon")
        lanceur = self.racine / "lanceur_note_et_lit.sh"
        ecrire(lanceur, LANCEUR_QUI_NOTE_ET_LIT_LES_CAS)
        lanceur.chmod(0o755)
        self.lanceur = lanceur
        self.rapport_16 = FIXTURES / "rapport_base_16_cas.json"

    def test_une_base_extraite_de_seize_cas_donne_un_tableau_des_seuls_cas_choisis_sans_jouer_la_base(self):
        code, sortie, erreur = jouer(
            self.argv("--base-rapport", str(self.rapport_16), "--cas", "alpha", "--cas", "beta"),
            self.env,
        )
        self.assertEqual(code, 0, erreur)
        # Seule la tête a été jouée : la base vient du rapport.
        self.assertEqual([l for l in self.appels() if l.startswith("APPEL")], ["APPEL tete"])
        # Un tableau à deux cas, ceux qu'on a choisis, et aucun des quatorze autres.
        self.assertIn("2 cas \u00d7 3 passages", sortie)
        self.assertIn("alpha", sortie)
        self.assertIn("beta", sortie)
        self.assertNotIn("cas-03", sortie)
        # La base de ces deux cas : (1 + 2/3) / 2 = 83 %, pas la moyenne des seize.
        self.assertIn("83 %", sortie)
        self.assertIn("base reprise du cache", erreur)

    def test_un_cas_choisi_absent_du_rapport_est_refuse_et_nomme_avant_tout_jeu(self):
        code, sortie, erreur = jouer(
            self.argv("--base-rapport", str(self.rapport_16), "--cas", "alpha", "--cas", "epsilon"),
            self.env,
        )
        self.assertEqual(code, 3, sortie)
        self.assertIn("epsilon", erreur)
        self.assertEqual(self.appels(), [])  # ni base ni tête jouées : rien payé

    def test_un_rapport_de_base_partiel_est_refuse_meme_extrait(self):
        code, _, erreur = jouer(
            self.argv("--base-rapport", str(FIXTURES / "rapport_partiel.json"), "--cas", "alpha"),
            self.env,
        )
        self.assertEqual(code, 3)
        self.assertIn("partial", erreur)
        self.assertEqual(self.appels(), [])

    def test_base_rapport_et_reference_ensemble_sont_refuses_avant_tout_jeu(self):
        code, _, _ = jouer(
            self.argv("--base-rapport", str(self.rapport_16), "--reference", str(self.rapport_16)),
            self.env,
        )
        self.assertEqual(code, 3)
        self.assertEqual(self.appels(), [])


class CleDuCacheDeLaBase(unittest.TestCase):
    """Le pas « Clé du cache de la base » de ci.yml, joué pour de bon.

    Un dépôt jetable (un plugin-jouet, un banc de deux cas) et le corps
    ``run:`` du pas exécuté par bash avec les variables que le job lui donne.
    On lit ce qu'il écrit dans ``GITHUB_OUTPUT`` : ``cle_tout`` (la clé d'une
    base complète) et ``cle_ecriture`` (la clé sous laquelle ce run sauve sa
    base : la complète si tout est joué, sinon celle de la sélection).
    """

    TOUT = '{"jouet": {"tout": true}}'

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.depot = Path(self._tmp.name) / "depot"
        d = self.depot
        d.mkdir()
        git(d, "init", "-q", "-b", "main")
        ecrire(d / "plugins" / "jouet" / "skills" / "s" / "SKILL.md", "v1\n")
        ecrire(d / "evals" / "jouet" / "alpha" / "prompt.md", "Réponds OK.\n")
        ecrire(d / "evals" / "jouet" / "beta" / "prompt.md", "Réponds NON.\n")
        ecrire(d / "evals" / "outillage" / "preparer-runner.sh", "CLAUDE_CODE_VERSION=2.1.285\n")
        ecrire(d / "evals" / "outillage" / "lancer.sh", "#!/bin/sh\n")
        ecrire(d / "README.md", "doc\n")
        self.valider("base")
        self.sha_base = self.sha()

    def valider(self, message: str) -> None:
        git(self.depot, "add", ".")
        git(self.depot, "commit", "-q", "-m", message)

    def sha(self) -> str:
        return git(self.depot, "rev-parse", "HEAD").strip()

    def cles(self, sha: str, selection: str = TOUT, **env) -> dict:
        import textwrap
        ci = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml").read_text("utf-8")
        pas = ci.split("- name: Clé du cache de la base", 1)[1].split("\n      - name:", 1)[0]
        corps = textwrap.dedent(pas.split("        run: |\n", 1)[1])
        sortie = self.depot / "github_output.txt"
        sortie.write_text("", "utf-8")
        e = {k: v for k, v in os.environ.items() if not k.startswith(("EVALS_", "GITHUB_"))}
        e.update(PLUGIN="jouet", BASE_SHA=sha, SELECTION=selection, GITHUB_OUTPUT=str(sortie),
                 EVALS_MODELE=MODELE, EVALS_EFFORT="high", EVALS_RUNS="3")
        e.update(env)
        r = subprocess.run(["bash", "-c", corps], cwd=self.depot, env=e, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return dict(l.split("=", 1) for l in sortie.read_text("utf-8").splitlines() if "=" in l)

    def test_un_merge_de_doc_sur_main_ne_change_pas_la_cle_de_la_base(self):
        avant = self.cles(self.sha_base)
        ecrire(self.depot / "docs" / "note.md", "une note\n")
        ecrire(self.depot / "README.md", "doc modifiée\n")
        self.valider("doc")
        apres = self.cles(self.sha())
        self.assertNotEqual(self.sha(), self.sha_base)
        self.assertEqual(avant["cle_tout"], apres["cle_tout"])

    def test_un_changement_du_plugin_a_la_base_change_la_cle(self):
        avant = self.cles(self.sha_base)
        ecrire(self.depot / "plugins" / "jouet" / "skills" / "s" / "SKILL.md", "v2\n")
        self.valider("skill")
        self.assertNotEqual(avant["cle_tout"], self.cles(self.sha())["cle_tout"])

    def test_un_cas_dont_le_contenu_change_change_la_cle(self):
        avant = self.cles(self.sha_base)
        ecrire(self.depot / "evals" / "jouet" / "alpha" / "prompt.md", "Réponds autre chose.\n")
        self.valider("cas")
        self.assertNotEqual(avant["cle_tout"], self.cles(self.sha_base)["cle_tout"])

    def test_le_modele_et_l_effort_changent_la_cle(self):
        ref = self.cles(self.sha_base)["cle_tout"]
        self.assertNotEqual(ref, self.cles(self.sha_base, EVALS_MODELE=AUTRE_MODELE)["cle_tout"])
        self.assertNotEqual(ref, self.cles(self.sha_base, EVALS_EFFORT="low")["cle_tout"])

    def test_la_cle_de_la_base_complete_ne_depend_pas_de_la_selection(self):
        selection = '{"jouet": {"tout": false, "cas": ["alpha"]}}'
        self.assertEqual(
            self.cles(self.sha_base)["cle_tout"], self.cles(self.sha_base, selection)["cle_tout"]
        )

    def test_une_base_complete_se_sauve_sous_la_cle_tout_et_une_selection_sous_sa_propre_cle(self):
        complete = self.cles(self.sha_base)
        self.assertEqual(complete["cle_ecriture"], complete["cle_tout"])
        self.assertTrue(complete["cle_tout"].endswith("-tout"), complete["cle_tout"])

        un = self.cles(self.sha_base, '{"jouet": {"tout": false, "cas": ["alpha"]}}')
        deux = self.cles(self.sha_base, '{"jouet": {"tout": false, "cas": ["alpha", "beta"]}}')
        deux_autre_ordre = self.cles(self.sha_base, '{"jouet": {"tout": false, "cas": ["beta", "alpha"]}}')
        for sel in (un, deux):
            self.assertIn("-sel-", sel["cle_ecriture"])
            self.assertNotEqual(sel["cle_ecriture"], sel["cle_tout"])
            self.assertTrue(sel["cle_ecriture"].startswith(sel["cle_tout"][: -len("tout")]))
        self.assertNotEqual(un["cle_ecriture"], deux["cle_ecriture"])
        self.assertEqual(deux["cle_ecriture"], deux_autre_ordre["cle_ecriture"])

    def test_sans_selection_pour_le_plugin_la_base_jouee_est_la_complete(self):
        r = self.cles(self.sha_base, "{}")
        self.assertEqual(r["cle_ecriture"], r["cle_tout"])


# --------------------------------------------------------------------------
# Étape 4 : le coût annoncé avant (--estimer), et compté en A/A
# --------------------------------------------------------------------------
def rapport_a_couts_distincts(couts: dict[str, list[tuple[float, float]]]) -> dict:
    """Un rapport où chaque passage porte son coût (jeu, juge) : des montants tous
    différents, pour qu'une somme sur le mauvais ensemble de cas se voie."""
    cas = [
        {"name": nom, "arms": {"with": [
            {"score": 1, "passed": True, "costUsd": jeu, "judgeCostUsd": juge}
            for jeu, juge in passages]}, "aggregates": {"score": 1}}
        for nom, passages in couts.items()
    ]
    return {"schemaVersion": 1, "cases": cas}


class CoutAnnonceAvant(DepotEtLanceur):
    """``--estimer`` additionne, sur un rapport déjà joué, le coût des cas choisis.

    Rapport de la base, calculé à la main (3 passages par cas, jeu + juge) :
      alpha  0,40 + 0,50 + 0,30 + 3 x 0,05 = 1,35 $
      beta   0,70 + 0,60 + 0,55 + 3 x 0,10 = 2,15 $
      gamma  3,00 + 3,00 + 3,00            = 9,00 $  (jamais choisi)
    """

    def setUp(self):
        super().setUp()
        CasChoisis.ajouter_cas(self, "beta")
        self.rapport_source = self.racine / "rapport-source.json"
        ecrire(self.rapport_source, json.dumps(rapport_a_couts_distincts({
            "alpha": [(0.40, 0.05), (0.50, 0.05), (0.30, 0.05)],
            "beta": [(0.70, 0.10), (0.60, 0.10), (0.55, 0.10)],
            "gamma": [(3.00, 0.0), (3.00, 0.0), (3.00, 0.0)],
        })))

    def estimer(self, *extra: str):
        return jouer(
            self.argv("--base-rapport", str(self.rapport_source), "--cas", "alpha",
                      "--cas", "beta", "--estimer", *extra),
            self.env,
        )

    def test_l_estimation_somme_au_centime_le_cout_des_seuls_cas_choisis(self):
        code, sortie, erreur = self.estimer()
        self.assertEqual(code, 0, erreur)
        self.assertIn("$3.50", sortie)  # 1,35 + 2,15 ; ni gamma, ni le total du rapport (12,50)

    def test_estimer_ne_joue_aucun_bras(self):
        # Test en plus de celui de la somme : la panne est autre (l'estimation
        # lancerait quand même les évals, et coûterait ce qu'elle annonce).
        code, _, erreur = self.estimer()
        self.assertEqual(code, 0, erreur)
        self.assertEqual(self.appels(), [])

    def test_l_estimation_suit_le_nombre_de_passages_demande_et_non_celui_du_rapport(self):
        # Test en plus : le rapport source a 3 passages par cas, la CI en demande
        # `--runs 2`. Coût moyen par passage x 2 : 3,50 x 2/3 = 2,33 $.
        code, sortie, erreur = self.estimer("--", "--runs", "2")
        self.assertEqual(code, 0, erreur)
        self.assertIn("$2.33", sortie)

    def test_estimer_sans_rapport_ou_lire_les_couts_est_un_refus_et_ne_joue_rien(self):
        # Test en plus : sans rapport, aucun montant n'est dérivable ; mieux vaut
        # un refus lisible qu'un « $0.00 » qui annoncerait gratuit.
        code, sortie, erreur = jouer(self.argv("--cas", "alpha", "--estimer"), self.env)
        self.assertEqual(code, 3, sortie)
        self.assertIn("--base-rapport", erreur)
        self.assertEqual(self.appels(), [])


class CoutDeLAA(DepotEtLanceur):
    def test_le_mode_aa_ecrit_le_cout_des_deux_passages_joues(self):
        # Les rapports figés `base` et `tete_stable` coûtent chacun 0,36 $ (4 cas
        # x 3 passages x 0,03 $) : l'A/A, qui les joue tous les deux, coûte 0,72 $.
        code, sortie, erreur = jouer(
            self.argv("--sortie-bruit", str(self.racine / "bruit.json"), mode="aa"), self.env
        )
        self.assertEqual(code, 0, erreur)
        self.assertIn("$0.72", sortie)


class FumeeEtPlanchers(DepotEtLanceur):
    """``--fumee`` : le test de fumée juge une tête seule, catégorie par catégorie.

    ``rapport_tete_session_limite.json`` est dérivé du vrai rapport de la tête de
    la PR #19 (trois cas sur seize, 3 passages chacun, ramenés à l'essentiel) :

      appelants                  1 · 1 · 1                  aucune session en erreur
      existant-jeu-de-questions  0,83 · 0,83 · 0,17         3 sessions en erreur
      maquette-requise           0,10 · 0,10 · 0,10         3 sessions en erreur

    soit 6 sessions en erreur sur 9. Les planchers de ces tests sont ceux du plan
    (depart 0,82 ; existant 0,65 ; maquette 0,80), écrits ici à la main : le test
    ne lit jamais ``evals/categories.json`` du vrai dépôt.
    """

    PLANCHERS = {"depart": 0.82, "existant": 0.65, "maquette": 0.80}
    CAS = {
        "depart": "appelants",
        "existant": "existant-jeu-de-questions",
        "maquette": "maquette-requise",
    }

    def setUp(self):
        super().setUp()
        self.ecrire_categories(self.PLANCHERS)

    def ecrire_categories(self, planchers: dict[str, float | None]) -> None:
        categories = {}
        for nom, plancher in planchers.items():
            categorie = {"exerce": ["skills/s/"], "cas": [self.CAS[nom]]}
            if plancher is not None:
                categorie["plancher"] = plancher
            categories[nom] = categorie
        ecrire(self.depot / "evals" / "categories.json", json.dumps({"jouet": categories}))

    def rapport_sain(self, scores: dict[str, float]) -> Path:
        """Le rapport figé, sans aucune session en erreur, dont chaque passage
        d'un cas vaut le score donné pour ce cas."""
        r = json.loads((FIXTURES / "rapport_tete_session_limite.json").read_text("utf-8"))
        for c in r["cases"]:
            for passage in c["arms"]["with"]:
                passage["error"] = None
                passage["score"] = scores[c["name"]]
        chemin = self.racine / "rapport-sain.json"
        ecrire(chemin, json.dumps(r))
        return chemin

    def fumee(self, rapport_json: Path | str):
        return jouer(self.argv("--fumee", "--tete-rapport", str(rapport_json)), self.env)

    def test_une_session_en_erreur_rend_la_fumee_rouge_et_non_concluante(self):
        code, sortie, erreur = self.fumee(FIXTURES / "rapport_tete_session_limite.json")
        # 4 : « panne d'infrastructure, à relancer », jamais 1 (recul) ni 0 (vert).
        self.assertEqual(code, 4, sortie + erreur)
        self.assertIn("ROUGE", sortie)
        self.assertIn("6 sur 9", sortie)  # les sessions en erreur sont comptées à part
        self.assertEqual(self.appels(), [])  # le rapport est jugé, rien n'est joué

    def test_une_categorie_a_0_60_pour_un_plancher_de_0_70_est_nommee_sous_plancher(self):
        self.PLANCHERS = {**self.PLANCHERS, "maquette": 0.70}
        self.ecrire_categories(self.PLANCHERS)
        chemin = self.rapport_sain(
            {"appelants": 1.0, "existant-jeu-de-questions": 0.9, "maquette-requise": 0.60}
        )
        code, sortie, erreur = self.fumee(chemin)
        self.assertEqual(code, 1, sortie + erreur)
        verdicts = [ligne for ligne in sortie.splitlines() if ligne.startswith("tirage")]
        self.assertEqual(len(verdicts), 3)  # un verdict par tirage
        for ligne in verdicts:
            self.assertIn("ROUGE", ligne)
            self.assertIn("maquette", ligne)
            self.assertNotIn("existant", ligne)  # seule la catégorie fautive est nommée
            self.assertNotIn("depart", ligne)

    def test_un_rapport_sain_rend_la_fumee_verte(self):
        chemin = self.rapport_sain(
            {"appelants": 1.0, "existant-jeu-de-questions": 0.9, "maquette-requise": 0.9}
        )
        code, sortie, erreur = self.fumee(chemin)
        self.assertEqual(code, 0, sortie + erreur)
        self.assertNotIn("ROUGE", sortie)

    def test_une_categorie_sans_plancher_est_refusee_et_nommee_jamais_un_plancher_a_zero(self):
        self.ecrire_categories({**self.PLANCHERS, "maquette": None})
        chemin = self.rapport_sain(
            {"appelants": 1.0, "existant-jeu-de-questions": 0.9, "maquette-requise": 0.0}
        )
        # Une maquette à 0 passerait sous un plancher implicite de 0 : le refus l'empêche.
        code, sortie, erreur = self.fumee(chemin)
        self.assertEqual(code, 3, sortie)
        self.assertIn("maquette", erreur)
        self.assertNotIn("VERT", sortie)

    def test_un_ab_dont_la_tete_a_des_sessions_en_erreur_rend_quatre_et_non_un(self):
        # Test construit pour la panne réelle de la PR #19 : la tête a perdu 6 sessions
        # sur 9 à une limite de session, ses scores s'effondrent. Sans la règle, cet
        # effondrement se lirait « RECUL » (code 1) alors que rien n'a été mesuré.
        base = json.loads((FIXTURES / "rapport_tete_session_limite.json").read_text("utf-8"))
        for c in base["cases"]:
            for passage in c["arms"]["with"]:
                passage["error"], passage["score"] = None, 1.0
        ecrire(self.racine / "base-saine.json", json.dumps(base))
        bruit = self.racine / "bruit.json"
        ecrire(bruit, json.dumps({"rms_ecarts_cas": 0.05, "modele": MODELE}))
        self.env["FAUX_RAPPORT_BASE"] = str(self.racine / "base-saine.json")
        self.env["FAUX_RAPPORT_TETE"] = str(FIXTURES / "rapport_tete_session_limite.json")
        # Témoin : la même tête sans la panne est bien un recul.
        sans_panne = json.loads((FIXTURES / "rapport_tete_session_limite.json").read_text("utf-8"))
        for c in sans_panne["cases"]:
            for passage in c["arms"]["with"]:
                passage["error"] = None
        ecrire(self.racine / "tete-sans-panne.json", json.dumps(sans_panne))
        temoin = dict(self.env, FAUX_RAPPORT_TETE=str(self.racine / "tete-sans-panne.json"))
        code_temoin, _, erreur_temoin = jouer(self.argv("--bruit", str(bruit)), temoin)
        self.assertEqual(code_temoin, 1, erreur_temoin)
        # La panne, elle, n'est pas un recul.
        code, sortie, erreur = jouer(self.argv("--bruit", str(bruit)), self.env)
        self.assertEqual(code, 4, sortie + erreur)
        self.assertNotIn("RECUL", sortie)
        self.assertIn("6 sur 9", sortie)

    def test_la_fumee_ne_joue_que_la_tete_avec_un_seul_passage(self):
        # Test en plus des cinq attendus : la panne est coûteuse et autre. Une fumée
        # qui rejouerait la base, ou garderait les 3 passages d'un A/B, coûterait
        # six fois le prix annoncé sans que rien dans le verdict ne le montre.
        ecrire(
            self.depot / "evals" / "categories.json",
            json.dumps({"jouet": {"unique": {"exerce": ["skills/s/"], "cas": ["alpha"], "plancher": 0.5}}}),
        )
        code, sortie, erreur = jouer(self.argv("--fumee"), self.env)
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual([l for l in self.appels() if l.startswith("APPEL")], ["APPEL tete"])
        self.assertEqual([l for l in self.appels() if l.startswith("OPTIONS")], ["OPTIONS --runs 1"])


if __name__ == "__main__":
    unittest.main()
