"""Tests de ``evals_selection.py`` (le plancher des évals) et des propriétés de
``ci.yml`` qui en dépendent.

Le script est joué comme la CI le joue : en sous-processus, le corps de la PR
dans la variable d'environnement ``PR_BODY`` (jamais en argument), les fichiers
touchés dans un fichier (un chemin par ligne, comme ``git diff --name-only``).
Chaque test fabrique son ``categories.json`` : aucun ne dépend des vrais cas,
sauf la classe ``VraiDepot``, qui vérifie l'exemple du plan sur le vrai fichier.

Le jeu de catégories fabriqué (plugin ``jouet``, et un second plugin ``autre``
pour « une catégorie se cherche dans tous les plugins touchés ») :

    recherche  exerce skills/plan/ et agents/chercheur.md       cas a1 a2
    bruit      exerce skills/plan/                              cas b1
    depart     exerce skills/plan/ et agents/enqueteur.md       cas c1 c2 c3
    execution  exerce skills/executer/ et agents/executant.md   cas d1
    (autre) solo  exerce skills/z/                              cas z1

Les attendus sont écrits à la main : « recherche + bruit » = a1, a2, b1.

Les évals se jouent **à la demande** : le script reçoit les labels de la PR
(``--labels``, un par ligne). Sans le label ``evals``, rien ne se joue, et une PR
qui touche un skill, un agent, un hook ou ``_partage/`` doit dire ``Evals: aucun —
<raison>``. Les helpers posent ``labels="evals"`` par défaut : sauf mention, une
PR de ces tests porte le label.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "scripts" / "evals_selection.py"
CI = RACINE / ".github" / "workflows" / "ci.yml"

CATEGORIES = {
    "_commentaire": "jeu fabriqué pour les tests",
    "jouet": {
        "recherche": {"exerce": ["skills/plan/", "agents/chercheur.md"], "cas": ["a1", "a2"]},
        "bruit": {"exerce": ["skills/plan/"], "cas": ["b1"]},
        "depart": {"exerce": ["skills/plan/", "agents/enqueteur.md"], "cas": ["c1", "c2", "c3"]},
        "execution": {"exerce": ["skills/executer/", "agents/executant.md"], "cas": ["d1"]},
    },
    "autre": {"solo": {"exerce": ["skills/z/"], "cas": ["z1"]}},
}
TOUS_LES_CAS_DE_JOUET = ["a1", "a2", "b1", "c1", "c2", "c3", "d1"]

PLAN = "plugins/jouet/skills/plan/SKILL.md"
EXECUTER = "plugins/jouet/skills/executer/SKILL.md"
CHERCHEUR = "plugins/jouet/agents/chercheur.md"
ENQUETEUR = "plugins/jouet/agents/enqueteur.md"


def jouer_script(fichiers, corps, plugin, categories, cwd, labels="evals"):
    """(code, stdout, stderr) ; ``corps=None`` : PR_BODY n'est pas défini.

    ``labels`` : les labels de la PR, un par ligne (``""`` : aucun label).
    """
    liste = Path(cwd) / "fichiers.txt"
    liste.write_text("".join(f + "\n" for f in fichiers), "utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PR_BODY"}
    if corps is not None:
        env["PR_BODY"] = corps
    argv = [sys.executable, str(SCRIPT), "--plugin", plugin, "--fichiers", str(liste),
            "--labels", labels]
    if categories is not None:
        argv += ["--categories", str(categories)]
    r = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=cwd)
    return r.returncode, r.stdout, r.stderr


class Selection(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)
        self.categories = self.dossier / "categories.json"
        self.categories.write_text(json.dumps(CATEGORIES), "utf-8")

    def jouer(self, fichiers, corps=None, plugin="jouet", categories=None, labels="evals"):
        return jouer_script(fichiers, corps, plugin, categories or self.categories,
                            self.dossier, labels)

    def selection(self, fichiers, corps=None, plugin="jouet", labels="evals"):
        code, sortie, erreur = self.jouer(fichiers, corps, plugin, labels=labels)
        self.assertEqual(code, 0, erreur)
        return json.loads(sortie)


class LigneDuCorpsDePr(Selection):
    def test_une_ligne_absente_joue_tout_et_dit_pourquoi(self):
        s = self.selection([PLAN], corps="Un corps sans la ligne attendue.\n")
        self.assertTrue(s["tout"])
        self.assertEqual(s["cas"], TOUS_LES_CAS_DE_JOUET)
        self.assertIn("Evals", s["pourquoi_tout"])

    def test_sans_variable_pr_body_on_joue_tout(self):
        # Lancement manuel : pas de PR, donc pas de corps.
        s = self.selection([], corps=None)
        self.assertTrue(s["tout"])
        self.assertEqual(s["cas"], TOUS_LES_CAS_DE_JOUET)

    def test_une_ligne_vide_joue_tout(self):
        for corps in ("Evals:", "Evals:   \n", "Evals: — parce que\n"):
            with self.subTest(corps=corps):
                s = self.selection([PLAN], corps=corps)
                self.assertTrue(s["tout"])

    def test_le_mot_tout_joue_tout_quelle_que_soit_la_casse_ou_les_espaces(self):
        for corps in ("Evals: tout", "  evals :  TOUT  ", "EVALS: Tout — je ne sais pas"):
            with self.subTest(corps=corps):
                s = self.selection([PLAN], corps=corps)
                self.assertTrue(s["tout"])
                self.assertEqual(s["cas"], TOUS_LES_CAS_DE_JOUET)

    def test_des_categories_donnent_l_union_de_leurs_cas_et_la_raison(self):
        s = self.selection(
            [PLAN],
            corps="Résumé.\n\nEvals: recherche, bruit — B1 ne touche que la recherche\n\nFin.",
        )
        self.assertFalse(s["tout"])
        self.assertEqual(s["categories"], ["recherche", "bruit"])
        self.assertEqual(s["cas"], ["a1", "a2", "b1"])
        self.assertEqual(s["raison"], "B1 ne touche que la recherche")
        self.assertEqual(s["plugin"], "jouet")
        self.assertEqual(s["pourquoi_tout"], "")

    def test_le_double_tiret_introduit_aussi_la_raison(self):
        s = self.selection([PLAN], corps="Evals: bruit -- essai")
        self.assertEqual(s["categories"], ["bruit"])
        self.assertEqual(s["raison"], "essai")

    def test_un_cas_partage_entre_deux_categories_n_est_joue_qu_une_fois(self):
        categories = json.loads(json.dumps(CATEGORIES))
        categories["jouet"]["bruit"]["cas"] = ["a2", "b1"]  # a2 est déjà dans « recherche »
        self.categories.write_text(json.dumps(categories), "utf-8")
        s = self.selection([PLAN], corps="Evals: recherche, bruit")
        self.assertEqual(s["cas"], ["a1", "a2", "b1"])

    def test_les_fins_de_ligne_windows_d_un_corps_de_pr_sont_tolerees(self):
        s = self.selection([PLAN], corps="Titre\r\n\r\nEvals: bruit — essai\r\nSuite\r\n")
        self.assertEqual(s["categories"], ["bruit"])
        self.assertEqual(s["raison"], "essai")

    def test_la_casse_des_noms_de_categories_n_est_pas_significative(self):
        s = self.selection([PLAN], corps="Evals: Recherche, BRUIT")
        self.assertEqual(s["categories"], ["recherche", "bruit"])

    def test_une_categorie_inconnue_est_refusee_et_les_categories_connues_sont_listees(self):
        code, _, erreur = self.jouer([PLAN], corps="Evals: recherche, fantome")
        self.assertEqual(code, 1)
        self.assertIn("fantome", erreur)
        for connue in ("recherche", "bruit", "depart", "execution", "solo"):
            self.assertIn(connue, erreur)

    def test_une_categorie_d_un_autre_plugin_n_est_pas_inconnue(self):
        # « Une catégorie se cherche dans tous les plugins touchés » : « solo »
        # existe chez « autre », pas chez « jouet ».
        s = self.selection([PLAN], corps="Evals: bruit, solo", plugin="jouet")
        self.assertEqual(s["cas"], ["b1"])
        s = self.selection(["plugins/autre/skills/z/SKILL.md"], corps="Evals: bruit, solo",
                           plugin="autre")
        self.assertEqual(s["cas"], ["z1"])

    def test_la_sortie_a_les_cles_du_contrat(self):
        s = self.selection([PLAN], corps="Evals: bruit")
        self.assertEqual(
            set(s), {"plugin", "tout", "categories", "cas", "raison", "pourquoi_tout"}
        )

    def test_un_corps_hostile_reste_une_donnee_et_ne_change_pas_le_code_de_sortie(self):
        # Le corps d'une PR est une entrée non fiable : il n'est jamais évalué.
        corps = "Evals: bruit; touch pirate ; $(touch pirate) — `touch pirate`"
        code, _, erreur = self.jouer([PLAN], corps=corps)
        self.assertEqual(code, 1, erreur)  # « bruit; touch pirate ; … » : catégorie inconnue
        self.assertFalse((self.dossier / "pirate").exists())


class AVotreDemande(Selection):
    """Les évals ne se jouent que si la PR porte le label ``evals``.

    Sans le label : une PR qui touche un skill, un agent, un hook ou ``_partage/``
    doit porter ``Evals: aucun — <raison>`` ; sinon refus, avec les deux sorties.
    """

    def test_un_skill_touche_sans_label_ni_ligne_aucun_est_refuse_et_les_deux_sorties_sont_dites(self):
        code, sortie, erreur = self.jouer([PLAN], corps="Un corps sans la ligne attendue.\n",
                                          labels="")
        self.assertEqual(code, 1, erreur)
        self.assertEqual(sortie.strip(), "")
        self.assertIn("evals", erreur)            # la sortie « poser le label »
        self.assertIn("Evals: aucun", erreur)     # la sortie « la ligne aucun »

    def test_le_skill_du_vrai_plugin_est_refuse_de_meme_sans_label_ni_ligne(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, erreur = jouer_script(
                ["plugins/plans-notion/skills/plan-notion/SKILL.md"], "", "plans-notion",
                None, tmp, labels="")
        self.assertEqual(code, 1, erreur)
        self.assertIn("skills/plan-notion/SKILL.md", erreur)

    def test_une_ligne_aucun_avec_raison_est_acceptee_et_ne_joue_rien(self):
        s = self.selection([PLAN], corps="Résumé.\n\nEvals: aucun — doc\n", labels="")
        self.assertFalse(s["tout"])
        self.assertEqual(s["categories"], [])
        self.assertEqual(s["cas"], [])
        self.assertEqual(s["raison"], "doc")

    def test_une_ligne_aucun_sans_raison_est_refusee(self):
        for corps in ("Evals: aucun —", "Evals: aucun — ", "Evals: aucun", "Evals: aucun --"):
            with self.subTest(corps=corps):
                code, _, erreur = self.jouer([PLAN], corps=corps, labels="")
                self.assertEqual(code, 1, erreur)
                self.assertIn("raison", erreur)

    def test_le_label_evals_avec_une_ligne_de_categories_joue_les_cas_de_ces_categories(self):
        s = self.selection([PLAN], corps="Evals: bruit — essai", labels="evals")
        self.assertFalse(s["tout"])
        self.assertEqual(s["categories"], ["bruit"])
        self.assertEqual(s["cas"], ["b1"])

    def test_le_label_evals_sans_ligne_joue_tout(self):
        s = self.selection([PLAN], corps="Un corps sans la ligne attendue.\n", labels="evals")
        self.assertTrue(s["tout"])
        self.assertEqual(s["cas"], TOUS_LES_CAS_DE_JOUET)

    def test_le_label_se_reconnait_parmi_d_autres_et_sans_egard_a_la_casse(self):
        for labels in ("bug\nEvals", "EVALS\nbug", "  evals  "):
            with self.subTest(labels=labels):
                s = self.selection([PLAN], corps="Evals: bruit", labels=labels)
                self.assertEqual(s["cas"], ["b1"])

    def test_un_autre_label_ne_vaut_pas_le_label_evals(self):
        for labels in ("", "bug", "review-required\nevals-plus", "pas-evals"):
            with self.subTest(labels=labels):
                code, _, erreur = self.jouer([PLAN], corps="Evals: bruit", labels=labels)
                self.assertEqual(code, 1, erreur)

    def test_sans_label_une_ligne_de_categories_ou_tout_ne_dispense_pas_de_la_ligne_aucun(self):
        for corps in ("Evals: bruit — essai", "Evals: tout", "Evals:"):
            with self.subTest(corps=corps):
                code, _, erreur = self.jouer([PLAN], corps=corps, labels="")
                self.assertEqual(code, 1, erreur)

    def test_sans_label_chaque_dossier_qui_change_un_comportement_demande_la_ligne_aucun(self):
        # Un skill, un agent, un hook, un `_partage/` : les quatre changent ce que les
        # évals mesurent.
        for chemin in (EXECUTER, CHERCHEUR, "plugins/jouet/hooks/hooks.json",
                       "plugins/jouet/skills/_partage/regle.md"):
            with self.subTest(fichier=chemin):
                code, _, erreur = self.jouer([chemin], corps="", labels="")
                self.assertEqual(code, 1, erreur)
                self.assertIn(chemin, erreur)

    def test_sans_label_une_pr_qui_ne_touche_aucun_de_ces_dossiers_passe_sans_ligne(self):
        s = self.selection(
            ["docs/veille.md", "plugins/jouet/.claude-plugin/plugin.json", "README.md",
             "scripts/evals_selection.py", ".github/workflows/ci.yml"],
            corps="", labels="")
        self.assertFalse(s["tout"])
        self.assertEqual(s["cas"], [])

    def test_sans_label_le_skill_d_un_autre_plugin_n_est_pas_a_justifier_ici(self):
        s = self.selection(["plugins/autre/skills/z/SKILL.md"], corps="", labels="")
        self.assertEqual(s["cas"], [])

    def test_aucun_ne_se_combine_pas_avec_une_categorie(self):
        code, _, erreur = self.jouer([PLAN], corps="Evals: aucun, bruit — x", labels="")
        self.assertEqual(code, 1, erreur)
        self.assertIn("aucun", erreur)

    def test_le_label_evals_et_la_ligne_aucun_se_contredisent_et_sont_refuses(self):
        code, _, erreur = self.jouer([PLAN], corps="Evals: aucun — doc", labels="evals")
        self.assertEqual(code, 1, erreur)
        self.assertIn("label", erreur)

    def test_sans_label_un_corps_hostile_reste_une_donnee(self):
        corps = "Evals: aucun — $(touch pirate) ; `touch pirate`"
        s = self.selection([PLAN], corps=corps, labels="")
        self.assertEqual(s["cas"], [])
        self.assertFalse((self.dossier / "pirate").exists())


class FichiersDuSocleCommun(Selection):
    CHEMINS = [
        "plugins/jouet/skills/_partage/regle.md",
        "plugins/jouet/hooks/hooks.json",
        "evals/jouet/a1/prompt.md",
        "evals/outillage/lancer.sh",
        "evals/categories.json",
        "scripts/evals_ab.py",
        "scripts/evals_selection.py",
        ".github/workflows/ci.yml",
    ]

    def test_chacun_de_ces_fichiers_force_tout_malgre_la_ligne_et_est_nomme(self):
        for chemin in self.CHEMINS:
            with self.subTest(fichier=chemin):
                s = self.selection([PLAN, chemin], corps="Evals: bruit")
                self.assertTrue(s["tout"])
                self.assertEqual(s["cas"], TOUS_LES_CAS_DE_JOUET)
                self.assertIn(chemin, s["pourquoi_tout"])

    def test_le_socle_d_un_autre_plugin_ne_force_pas_tout_pour_celui_ci(self):
        s = self.selection(
            [PLAN, "plugins/autre/hooks/hooks.json", "plugins/autre/skills/_partage/x.md",
             "evals/autre/z1/prompt.md"],
            corps="Evals: bruit",
        )
        self.assertFalse(s["tout"])
        self.assertEqual(s["cas"], ["b1"])


class CouvertureDesFichiersTouches(Selection):
    def test_un_skill_exerce_par_une_categorie_choisie_est_couvert(self):
        s = self.selection([PLAN], corps="Evals: bruit")
        self.assertFalse(s["tout"])
        self.assertEqual(s["cas"], ["b1"])

    def test_un_skill_que_les_categories_choisies_n_exercent_pas_est_refuse_et_nomme(self):
        # Le skill d'exécution est touché, la ligne ne choisit que « recherche ».
        code, sortie, erreur = self.jouer([EXECUTER], corps="Evals: recherche")
        self.assertEqual(code, 1)
        self.assertIn("skills/executer/SKILL.md", erreur)
        self.assertIn("execution", erreur)  # la catégorie qui le couvrirait
        self.assertEqual(sortie.strip(), "")

    def test_un_agent_est_couvert_par_son_chemin_exact(self):
        s = self.selection([CHERCHEUR], corps="Evals: recherche")
        self.assertEqual(s["cas"], ["a1", "a2"])
        code, _, erreur = self.jouer([CHERCHEUR], corps="Evals: bruit")
        self.assertEqual(code, 1)
        self.assertIn("agents/chercheur.md", erreur)

    def test_chaque_fichier_touche_doit_etre_couvert_pas_seulement_le_premier(self):
        code, _, erreur = self.jouer([PLAN, EXECUTER], corps="Evals: bruit")
        self.assertEqual(code, 1)
        self.assertIn("skills/executer/SKILL.md", erreur)
        self.assertNotIn("skills/plan/SKILL.md", erreur)
        s = self.selection([PLAN, EXECUTER], corps="Evals: bruit, execution")
        self.assertEqual(s["cas"], ["b1", "d1"])

    def test_un_fichier_que_nulle_categorie_n_exerce_joue_tout_par_prudence(self):
        inconnu = "plugins/jouet/skills/nouveau/SKILL.md"
        s = self.selection([inconnu], corps="Evals: bruit")
        self.assertTrue(s["tout"])
        self.assertEqual(s["cas"], TOUS_LES_CAS_DE_JOUET)
        self.assertIn(inconnu, s["pourquoi_tout"])

    def test_un_fichier_hors_skills_et_agents_ne_demande_aucune_couverture(self):
        s = self.selection(
            ["docs/veille.md", "plugins/jouet/.claude-plugin/plugin.json", "README.md"],
            corps="Evals: bruit",
        )
        self.assertFalse(s["tout"])
        self.assertEqual(s["cas"], ["b1"])

    def test_un_fichier_d_un_autre_plugin_n_est_pas_a_couvrir_ici(self):
        s = self.selection(["plugins/autre/skills/z/SKILL.md"], corps="Evals: bruit")
        self.assertFalse(s["tout"])
        self.assertEqual(s["cas"], ["b1"])

    def test_la_categorie_inconnue_est_refusee_meme_si_tout_est_force_par_un_fichier(self):
        code, _, erreur = self.jouer(
            ["plugins/jouet/hooks/hooks.json"], corps="Evals: fantome"
        )
        self.assertEqual(code, 1)
        self.assertIn("fantome", erreur)


class MessageDeRefus(Selection):
    """Le corps de la PR est relu à chaque run : le message dit quoi faire ensuite."""

    SUITE = ("Corriger la ligne « Evals: » du corps de la PR, puis relancer le run "
             "(Re-run all jobs) ou pousser un commit")

    def test_une_categorie_inconnue_dit_de_corriger_le_corps_puis_de_relancer_le_run(self):
        code, _, erreur = self.jouer([PLAN], corps="Evals: recherche, fantome")
        self.assertEqual(code, 1)
        self.assertIn(self.SUITE.lower(), erreur.lower())

    def test_un_skill_non_couvert_dit_de_corriger_le_corps_puis_de_relancer_le_run(self):
        code, _, erreur = self.jouer([EXECUTER], corps="Evals: recherche")
        self.assertEqual(code, 1)
        self.assertIn(self.SUITE.lower(), erreur.lower())


class Pannes(Selection):
    def test_un_fichier_de_chemins_illisible_est_une_panne(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--plugin", "jouet",
             "--fichiers", str(self.dossier / "n-existe-pas.txt"),
             "--categories", str(self.categories)],
            capture_output=True, text=True, cwd=self.dossier,
        )
        self.assertEqual(r.returncode, 2)
        self.assertIn("n-existe-pas.txt", r.stderr)

    def test_un_categories_json_illisible_est_une_panne(self):
        self.categories.write_text("{ pas du json", "utf-8")
        code, _, erreur = self.jouer([PLAN], corps="Evals: bruit")
        self.assertEqual(code, 2)
        self.assertIn("categories.json", erreur)

    def test_un_categories_json_absent_est_une_panne(self):
        code, _, erreur = self.jouer([PLAN], corps="Evals: bruit",
                                      categories=self.dossier / "absent.json")
        self.assertEqual(code, 2)
        self.assertIn("absent.json", erreur)

    def test_un_plugin_sans_categories_joue_tout_faute_de_mieux(self):
        s = self.selection([PLAN], corps="Evals: bruit", plugin="inconnu-du-fichier")
        self.assertTrue(s["tout"])
        self.assertEqual(s["cas"], [])
        self.assertIn("inconnu-du-fichier", s["pourquoi_tout"])


class VraiDepot(unittest.TestCase):
    """L'exemple du plan, joué sur le vrai ``evals/categories.json``."""

    def jouer(self, fichier, corps):
        with tempfile.TemporaryDirectory() as tmp:
            return jouer_script([fichier], corps, "plans-notion", None, tmp, labels="evals")

    def test_existant_et_bruit_couvrent_plan_notion_avec_cinq_cas(self):
        code, sortie, erreur = self.jouer(
            "plugins/plans-notion/skills/plan-notion/SKILL.md",
            "Evals: existant, bruit — essai",
        )
        self.assertEqual(code, 0, erreur)
        s = json.loads(sortie)
        self.assertFalse(s["tout"])
        self.assertEqual(
            sorted(s["cas"]),
            sorted(["existant-jeu-de-donnees", "existant-jeu-de-questions",
                    "bruit-bounded", "bruit-doc-seule", "report-sans-seuil"]),
        )

    def test_decouvertes_ne_couvre_pas_plan_notion(self):
        code, _, erreur = self.jouer(
            "plugins/plans-notion/skills/plan-notion/SKILL.md", "Evals: decouvertes"
        )
        self.assertEqual(code, 1)
        self.assertIn("skills/plan-notion/SKILL.md", erreur)


# --------------------------------------------------------------------------
# Propriétés de ci.yml : le plancher, le verdict au nom fixe, le corps de PR
# --------------------------------------------------------------------------
def _job(texte: str, nom: str) -> str:
    """Le texte d'un job de ci.yml : de « <nom>: » au job suivant."""
    m = re.search(rf"^  {re.escape(nom)}:\n(.*?)(?=^  [a-z][\w-]*:\n|\Z)", texte,
                  re.MULTILINE | re.DOTALL)
    assert m, f"job {nom} introuvable dans ci.yml"
    return m.group(1)


class CiYml(unittest.TestCase):
    def setUp(self):
        self.ci = CI.read_text(encoding="utf-8")

    def test_le_corps_du_payload_n_est_plus_lu_car_il_est_perime_au_re_run(self):
        # Un « Re-run » rejoue le payload de l'événement d'origine : son corps est
        # celui du moment de l'ouverture ou de la dernière poussée. On relit par l'API.
        self.assertNotIn("pull_request.body", self.ci)

    def test_aucune_donnee_de_pr_n_est_interpolee_dans_un_run(self):
        # Une interpolation `${{ … }}` dans un `run:` est évaluée avant le shell :
        # un titre, une branche ou un corps de PR y deviendrait du code.
        dangereux = re.compile(
            r"\$\{\{\s*github\.(event\.pull_request\.(title|body|head\.ref|head\.label)"
            r"|head_ref|event\.head_commit\.message)")
        indent_run = None  # indentation de la clé `run:` dont on lit le bloc
        for ligne in self.ci.splitlines():
            if not ligne.strip():
                continue
            indent = len(ligne) - len(ligne.lstrip(" "))
            en_run = re.match(r"^(\s*)(- )?run:", ligne)
            if en_run:
                indent_run = len(en_run.group(1)) + (2 if en_run.group(2) else 0)
                continuer = ligne.split("run:", 1)[1]
                self.assertIsNone(dangereux.search(continuer), ligne)
                continue
            if indent_run is not None and indent > indent_run:
                self.assertIsNone(dangereux.search(ligne), ligne)
            else:
                indent_run = None

    def test_evals_portee_appelle_le_script_et_sort_la_selection(self):
        portee = _job(self.ci, "evals-portee")
        self.assertIn("scripts/evals_selection.py", portee)
        self.assertRegex(portee, r"(?m)^      selection: \$\{\{ steps\.portee\.outputs\.selection \}\}")

    def test_evals_passe_les_cas_le_bruit_et_cinq_agents_en_parallele(self):
        evals = _job(self.ci, "evals")
        self.assertIn("--cas", evals)
        self.assertIn("--bruit", evals)
        self.assertIn("EVALS_CONCURRENCE: '5'", evals)

    def test_evals_joue_sonnet_en_effort_high(self):
        # Décision de Benjamin (étape B9) après la sonde : Sonnet, effort `high`.
        evals = _job(self.ci, "evals")
        self.assertRegex(evals, r"(?m)^      EVALS_MODELE: claude-sonnet-5-5\s*$")
        self.assertRegex(evals, r"(?m)^      EVALS_EFFORT: high\s*$")
        self.assertNotIn("claude-opus", evals)

    def test_la_cle_du_cache_de_la_base_inclut_l_effort(self):
        # Un effort qui change change la mesure : une base jouée en `low` ne peut
        # pas servir une comparaison en `high`.
        evals = _job(self.ci, "evals")
        cle = evals.split("id: cle", 1)[1].split("- name:", 1)[0]
        self.assertRegex(cle, r"echo \"cle=[^\"]*\$EVALS_MODELE[^\"]*\$EVALS_EFFORT")

    def test_le_commentaire_des_parametres_figes_mentionne_l_effort(self):
        evals = _job(self.ci, "evals")
        self.assertRegex(evals, r"# Figés : [^\n]*effort")

    def test_le_lancement_manuel_offre_le_choix_ab_ou_aa_avec_ab_par_defaut(self):
        dispatch = self.ci.split("  workflow_dispatch:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertRegex(dispatch, r"(?m)^    inputs:\n      mode:\n")
        self.assertRegex(dispatch, r"(?m)^        type: choice\s*$")
        self.assertRegex(dispatch, r"(?m)^        default: ab\s*$")
        self.assertRegex(dispatch, r"(?m)^        options:\n          - ab\n          - aa\s*$")
        description = re.search(r"(?m)^        description: (.*)$", dispatch)
        self.assertIsNotNone(description, "l'input `mode` n'a pas de description")
        self.assertIn("deux fois", description.group(1))
        self.assertIn("bruit", description.group(1))

    def test_l_input_mode_ne_passe_que_par_env_jamais_interpole(self):
        # Hors `group:` de la concurrence (une expression, pas un script).
        lignes = [l for l in self.ci.splitlines()
                  if "${{ inputs" in l and not l.lstrip().startswith("group:")]
        self.assertTrue(lignes, "l'input `mode` n'est lu nulle part")
        for ligne in lignes:
            self.assertRegex(ligne, r"^\s+MODE: \$\{\{ inputs\.mode \}\}\s*$")

    def test_aucun_run_n_interpole_un_input_ni_une_donnee_d_evenement(self):
        # `inputs.*` et `github.event.*` sont des entrées : dans un `run:` elles
        # deviendraient du code. Elles passent par `env:`.
        dangereux = re.compile(r"\$\{\{\s*(inputs|github\.event)\b")
        indent_run = None
        vus = 0
        for ligne in self.ci.splitlines():
            if not ligne.strip():
                continue
            indent = len(ligne) - len(ligne.lstrip(" "))
            en_run = re.match(r"^(\s*)(- )?run:", ligne)
            if en_run:
                indent_run = len(en_run.group(1)) + (2 if en_run.group(2) else 0)
                self.assertIsNone(dangereux.search(ligne.split("run:", 1)[1]), ligne)
                vus += 1
                continue
            if indent_run is not None and indent > indent_run:
                self.assertIsNone(dangereux.search(ligne), ligne)
            else:
                indent_run = None
        self.assertGreater(vus, 5, "le balayage n'a lu aucun run")

    def test_le_merge_automatique_lit_le_numero_de_pr_par_env(self):
        merge = _job(self.ci, "merge-auto")
        self.assertRegex(merge, r"(?m)^          PR_NUMBER: \$\{\{ github\.event\.pull_request\.number \}\}\s*$")
        self.assertIn('gh pr merge "$PR_NUMBER"', merge)

    def _etapes(self, job: str) -> list[str]:
        return re.split(r"(?m)^      - ", _job(self.ci, job))[1:]

    def _etape(self, job: str, morceau: str) -> str:
        trouvees = [e for e in self._etapes(job) if morceau in e]
        self.assertEqual(len(trouvees), 1, f"{morceau!r} : {len(trouvees)} étapes")
        return trouvees[0]

    def test_le_mode_aa_joue_tout_le_banc_et_ecrit_le_bruit_sous_runner_temp(self):
        aa = self._etape("evals", "--mode aa")
        self.assertRegex(aa, r"(?m)^        if: .*inputs\.mode == 'aa'")
        self.assertIn("--sortie-bruit", aa)
        self.assertRegex(aa, r"--sortie-bruit \"\$RUNNER_TEMP/[^\"]*bruit-\$PLUGIN\.json\"")
        self.assertRegex(aa, r"(?m)^          MODE: \$\{\{ inputs\.mode \}\}\s*$")
        # Ni cas choisis, ni bruit lu, ni base du cache : l'A/A mesure la tête seule.
        for interdit in ("--cas", "--bruit ", "--reference", "--garder-base"):
            self.assertNotIn(interdit, aa)

    def test_le_mode_aa_ne_lit_ni_n_ecrit_le_cache_de_la_base(self):
        for morceau in ("actions/cache/restore", "actions/cache/save"):
            with self.subTest(etape=morceau):
                etape = self._etape("evals", morceau)
                self.assertRegex(etape, r"if: [^\n]*inputs\.mode != 'aa'")
        base_gardee = self._etape("evals", "id: base")
        self.assertRegex(base_gardee, r"if: [^\n]*inputs\.mode != 'aa'")

    def test_le_mode_ab_habituel_est_saute_en_aa(self):
        ab = self._etape("evals", "--mode ab")
        self.assertRegex(ab, r"(?m)^        if: .*inputs\.mode != 'aa'")

    def test_le_bruit_aa_est_publie_en_artefact_avec_l_action_epinglee(self):
        etape = self._etape("evals", "name: evals-bruit-${{ matrix.plugin }}")
        epingle = self._etape("evals", "name: evals-${{ matrix.plugin }}\n")
        action = re.search(r"uses: (actions/upload-artifact@[0-9a-f]{40})", etape)
        self.assertIsNotNone(action, "l'action d'upload doit être épinglée par SHA")
        self.assertIn(action.group(1), epingle)
        self.assertRegex(etape, r"if: [^\n]*inputs\.mode == 'aa'")
        self.assertIn("evals-bruit", etape.split("path:", 1)[1])

    def test_le_resume_du_mode_aa_dit_de_commiter_le_bruit_en_evals_bruit_plugin_json(self):
        aa = self._etape("evals", "--mode aa")
        self.assertIn("evals-bruit-$PLUGIN", aa)
        self.assertIn("evals/bruit-$PLUGIN.json", aa)
        self.assertIn("GITHUB_STEP_SUMMARY", aa)

    def test_le_jeton_est_aussi_cherche_dans_le_dossier_du_bruit(self):
        controle = self._etape("evals", "Vérifier que l'artefact ne contient pas le jeton")
        self.assertIn("evals-bruit", controle)

    def test_la_pr_ne_rejoue_pas_sur_edition_pas_de_edited_dans_les_types(self):
        # `labeled` s'ajoute aux types par défaut (le label `evals` lance les évals) ;
        # `edited` reste exclu.
        # `edited` produisait un « Verdict des évals » vert sur un SHA dont les
        # évals étaient rouges (une édition de titre saute `evals`), et le verrou
        # de `main` risquait de ne voir que ce dernier statut.
        bloc = self.ci.split("\n  pull_request:\n", 1)[1].split("\n  push:", 1)[0]
        types = re.search(r"(?m)^    types: \[([^\]]*)\]\s*$", bloc)
        if types is not None:  # sans `types:`, c'est le défaut : opened, synchronize, reopened
            liste = {t.strip() for t in types.group(1).split(",")}
            self.assertNotIn("edited", liste)
            self.assertLessEqual(liste, {"opened", "synchronize", "reopened", "labeled"})
        self.assertNotRegex(bloc, r"(?m)^    types:\s*\n")  # pas non plus la forme en liste

    def test_le_commentaire_de_on_dit_pourquoi_pas_edited_et_pourquoi_l_api(self):
        entete = self.ci.split("\njobs:", 1)[0]
        commentaires = "\n".join(l for l in entete.splitlines() if l.lstrip().startswith("#"))
        self.assertIn("edited", commentaires)
        self.assertRegex(commentaires, r"(?is)verdict[^\n]*vert[\s\S]*SHA")
        self.assertRegex(commentaires, r"(?i)\bAPI\b")
        self.assertRegex(commentaires, r"(?i)re-?run")

    def test_aucune_garde_d_edition_ne_subsiste(self):
        for reste in ("EVENT_ACTION", "CORPS_EDITE", "changes.body", "github.event.action"):
            self.assertNotIn(reste, self.ci)
        merge = _job(self.ci, "merge-auto").split("runs-on:", 1)[0]
        self.assertNotIn("edited", merge)
        self.assertNotIn("state == 'open'", self.ci)

    def test_evals_portee_relit_le_corps_par_l_api_avec_le_numero_passe_par_env(self):
        etape = _job(self.ci, "evals-portee").split("id: portee", 1)[1]
        self.assertRegex(etape, r"(?m)^          GH_TOKEN: \$\{\{ github\.token \}\}\s*$")
        self.assertRegex(etape, r"(?m)^          PR_NUMBER: \$\{\{ github\.event\.pull_request\.number \}\}\s*$")
        self.assertRegex(etape, r"(?m)^          REPO: \$\{\{ github\.repository \}\}\s*$")
        appel = re.search(r"PR_BODY=\$\(\s*gh (api|pr view)\b[^\n]*\$PR_NUMBER[^\n]*\)", etape)
        self.assertIsNotNone(appel, "le corps n'est pas relu par `gh api` / `gh pr view`")
        self.assertIn("export PR_BODY", etape)
        # Le corps ne passe jamais par une interpolation `${{ … }}`.
        self.assertNotIn("PR_BODY: ${{", etape)

    def _corps_relu(self) -> str:
        """Le morceau du script d'`evals-portee` qui relit le corps, dédenté."""
        import textwrap
        etape = _job(self.ci, "evals-portee").split("id: portee", 1)[1]
        m = re.search(r"(?ms)^ *# --- corps de la PR \(début\)\n(.*?)^ *# --- corps de la PR \(fin\)", etape)
        self.assertIsNotNone(m, "repères « corps de la PR (début/fin) » absents")
        return textwrap.dedent(m.group(1))

    def _jouer_corps_relu(self, faux_gh: str | None, evenement: str = "pull_request"):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "bin").mkdir()
            trace = tmp / "gh-args.txt"
            if faux_gh is not None:
                gh = tmp / "bin" / "gh"
                gh.write_text(f'#!/bin/sh\necho "$*" >> "{trace}"\n{faux_gh}\n', "utf-8")
                gh.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if k not in ("PR_BODY", "GITHUB_ACTIONS")}
            env.update(PATH=f"{tmp / 'bin'}{os.pathsep}{env['PATH']}", EVENT_NAME=evenement,
                       REPO="proprietaire/depot", PR_NUMBER="42")
            script = "set -euo pipefail\n" + self._corps_relu() + '\nprintf "CORPS=[%s]" "${PR_BODY-}"\n'
            r = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
            appels = trace.read_text("utf-8") if trace.exists() else ""
            return r, appels

    def test_le_corps_relu_est_exporte_dans_pr_body_pour_le_script_de_selection(self):
        r, appels = self._jouer_corps_relu('echo "Evals: bruit — corps à jour"')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("CORPS=[Evals: bruit — corps à jour]", r.stdout)
        self.assertIn("42", appels)
        self.assertIn("proprietaire/depot", appels)

    def test_un_echec_de_l_api_rend_le_job_rouge_sans_repli_silencieux(self):
        r, _ = self._jouer_corps_relu('echo "HTTP 502" >&2; exit 1')
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("CORPS=", r.stdout)  # ni « tout » (corps vide), ni sélection vide
        self.assertIn("::error", r.stdout + r.stderr)

    def test_un_corps_vide_est_un_corps_pas_une_erreur(self):
        r, _ = self._jouer_corps_relu('printf ""')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("CORPS=[]", r.stdout)

    def test_le_lancement_manuel_n_appelle_pas_l_api(self):
        r, appels = self._jouer_corps_relu(None, evenement="workflow_dispatch")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(appels, "")

    def _labels_lus(self) -> str:
        """Le morceau du script d'`evals-portee` qui relit les labels, dédenté."""
        import textwrap
        etape = _job(self.ci, "evals-portee").split("id: portee", 1)[1]
        m = re.search(r"(?ms)^ *# --- labels \(début\)\n(.*?)^ *# --- labels \(fin\)", etape)
        self.assertIsNotNone(m, "repères « labels (début/fin) » absents")
        return textwrap.dedent(m.group(1))

    def _jouer_labels_lus(self, faux_gh: str | None, evenement: str = "pull_request"):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "bin").mkdir()
            trace = tmp / "gh-args.txt"
            if faux_gh is not None:
                gh = tmp / "bin" / "gh"
                gh.write_text(f'#!/bin/sh\necho "$*" >> "{trace}"\n{faux_gh}\n', "utf-8")
                gh.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if k not in ("LABELS", "GITHUB_ACTIONS")}
            env.update(PATH=f"{tmp / 'bin'}{os.pathsep}{env['PATH']}", EVENT_NAME=evenement,
                       REPO="proprietaire/depot", PR_NUMBER="42")
            script = "set -euo pipefail\n" + self._labels_lus() + '\nprintf "LABELS=[%s]" "${LABELS-}"\n'
            r = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
            appels = trace.read_text("utf-8") if trace.exists() else ""
            return r, appels

    def test_les_labels_relus_par_l_api_sont_exportes_pour_la_decision_des_evals(self):
        r, appels = self._jouer_labels_lus('printf "bug\\nevals\\n"')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LABELS=[bug\nevals]", r.stdout)
        self.assertIn("42", appels)

    def test_un_echec_de_l_api_sur_les_labels_rend_le_job_rouge_sans_repli_silencieux(self):
        # Ni « le label est là » (on paierait le banc), ni « il n'y est pas » (on
        # sauterait des évals demandées) : l'incertitude est une panne.
        r, _ = self._jouer_labels_lus('echo "HTTP 502" >&2; exit 1')
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("LABELS=", r.stdout)
        self.assertIn("::error", r.stdout + r.stderr)

    def test_une_pr_sans_label_donne_des_labels_vides_pas_une_erreur(self):
        r, _ = self._jouer_labels_lus('printf ""')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LABELS=[]", r.stdout)

    def test_le_lancement_manuel_vaut_la_demande_du_label_sans_appeler_l_api(self):
        r, appels = self._jouer_labels_lus(None, evenement="workflow_dispatch")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LABELS=[evals]", r.stdout)
        self.assertEqual(appels, "")

    def test_evals_portee_n_a_que_lecture_du_contenu_et_des_pull_requests(self):
        portee = _job(self.ci, "evals-portee")
        bloc = portee.split("    permissions:\n", 1)[1].split("\n    outputs:", 1)[0]
        droits = {l.strip() for l in bloc.splitlines() if l.strip()}
        self.assertEqual(droits, {"contents: read", "pull-requests: read"})

    def test_le_groupe_de_concurrence_de_evals_inclut_le_mode(self):
        # Un `ab` lancé pendant un `aa` payé ne doit plus l'annuler ; `ab` par
        # défaut hors lancement manuel (où `inputs.mode` est vide).
        evals = _job(self.ci, "evals")
        groupe = re.search(r"(?m)^      group: (.*)$", evals)
        self.assertIsNotNone(groupe)
        self.assertIn("inputs.mode || 'ab'", groupe.group(1))
        self.assertIn("matrix.plugin", groupe.group(1))
        self.assertIn("cancel-in-progress: true", evals)

    def test_le_lancement_manuel_ne_merge_rien_et_le_verdict_n_en_depend_pas(self):
        merge = _job(self.ci, "merge-auto")
        self.assertIn("github.event_name == 'pull_request'", merge.split("runs-on:", 1)[0])
        verdict = _job(self.ci, "evals-verdict")
        self.assertNotIn("inputs", verdict)

    def test_la_cle_du_cache_de_la_base_inclut_la_liste_des_cas_joues(self):
        evals = _job(self.ci, "evals")
        cle = evals.split("id: cle", 1)[1].split("- name:", 1)[0]
        self.assertIn("SELECTION", cle)
        self.assertRegex(cle, r"echo \"cle=[^\"]*\$selec")

    def test_le_job_evals_garde_son_nom_fixe_par_plugin(self):
        self.assertIn("name: Évals (${{ matrix.plugin }})", _job(self.ci, "evals"))

    def test_le_verdict_est_un_job_au_nom_fixe_sans_secret_ni_droit(self):
        verdict = _job(self.ci, "evals-verdict")
        self.assertIn("name: Verdict des évals", verdict)
        self.assertIn("needs: [evals-portee, evals]", verdict)
        self.assertRegex(verdict, r"(?m)^    if: always\(\)\s*$")
        self.assertIn("runs-on: ubuntu-latest", verdict)
        self.assertRegex(verdict, r"(?m)^    permissions: \{\}\s*$")
        self.assertNotIn("checkout", verdict)
        self.assertNotIn("secrets.", verdict)

    def test_le_verdict_est_rouge_sur_echec_ou_annulation_de_la_portee_ou_des_evals(self):
        verdict = _job(self.ci, "evals-verdict")
        for amont in ("evals-portee", "evals"):
            with self.subTest(amont=amont):
                self.assertIn(f"needs.{amont}.result", verdict)
        for etat in ("failure", "cancelled"):
            self.assertIn(etat, verdict)
        self.assertIn("exit 1", verdict)

    def test_le_merge_automatique_attend_le_verdict_avec_la_meme_condition(self):
        merge = _job(self.ci, "merge-auto")
        self.assertIn("evals-verdict", merge.split("if:")[0])
        self.assertIn(
            "(needs.evals-verdict.result == 'success' || needs.evals-verdict.result == 'skipped')",
            merge,
        )

    def test_le_yaml_se_charge(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML absent")
        doc = yaml.safe_load(self.ci)
        self.assertIn("evals-verdict", doc["jobs"])
        self.assertEqual(doc["jobs"]["evals-verdict"]["name"], "Verdict des évals")
        self.assertEqual(doc["jobs"]["evals-verdict"]["permissions"], {})


class PorteeDuLabelAjoute(unittest.TestCase):
    """Un ``labeled`` dont le label ajouté n'est pas ``evals`` ne relance pas le banc.

    Le pas ``portee`` d'``evals-portee`` est joué pour de bon, dans un dépôt jetable
    (deux commits, le second change un skill), avec un faux ``gh`` qui répond ce
    que l'API répondrait. On lit ce que le job sort : ``touche`` dans le fichier
    ``GITHUB_OUTPUT``. ``LABEL_AJOUTE`` est le nom du label de l'événement
    ``labeled`` (vide pour ``opened``, ``synchronize`` et ``reopened``).
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        d = self.depot = Path(self._tmp.name) / "depot"
        (d / "bin").mkdir(parents=True)
        (d / "scripts").mkdir()
        (d / "evals" / "jouet").mkdir(parents=True)
        (d / "plugins" / "jouet" / ".claude-plugin").mkdir(parents=True)
        (d / "plugins" / "jouet" / "skills" / "plan").mkdir(parents=True)
        shutil.copy(SCRIPT, d / "scripts" / "evals_selection.py")
        (d / "evals" / "categories.json").write_text(json.dumps(CATEGORIES), "utf-8")
        (d / "evals" / "jouet" / "a1.md").write_text("cas\n", "utf-8")
        (d / "plugins" / "jouet" / ".claude-plugin" / "plugin.json").write_text("{}\n", "utf-8")
        skill = d / "plugins" / "jouet" / "skills" / "plan" / "SKILL.md"
        skill.write_text("v1\n", "utf-8")
        self.git("init", "-q", "-b", "main")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        skill.write_text("v2\n", "utf-8")
        self.git("commit", "-q", "-am", "change le skill")
        self.tete = self.git("rev-parse", "HEAD").strip()
        gh = d / "bin" / "gh"
        gh.write_text('#!/bin/sh\ncase "$*" in *labels*) printf \'%s\' "$FAUX_LABELS";;'
                      ' *) printf \'%s\' "$FAUX_BODY";; esac\n', "utf-8")
        gh.chmod(0o755)

    def git(self, *args):
        r = subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *args],
            cwd=self.depot, capture_output=True, text=True, check=True)
        return r.stdout

    def _pas_portee(self) -> str:
        import textwrap
        ci = CI.read_text(encoding="utf-8")
        run = _job(ci, "evals-portee").split("        run: |\n", 1)[1]
        return textwrap.dedent(run)

    def jouer(self, labels, label_ajoute, corps="Evals: bruit — essai"):
        """(code, sortie du pas, dict de GITHUB_OUTPUT)."""
        d = self.depot
        sortie = d / "github_output.txt"
        sortie.write_text("", "utf-8")
        env = {k: v for k, v in os.environ.items() if k not in ("PR_BODY", "LABELS")}
        env.update(
            PATH=f"{d / 'bin'}{os.pathsep}{env['PATH']}", EVENT_NAME="pull_request",
            GH_TOKEN="x", PR_NUMBER="7", REPO="proprietaire/depot",
            PR_BASE_SHA=self.base, PR_HEAD_SHA=self.tete, RUNNER_TEMP=str(d),
            GITHUB_OUTPUT=str(sortie), GITHUB_STEP_SUMMARY=str(d / "resume.md"),
            FAUX_LABELS=labels, FAUX_BODY=corps, LABEL_AJOUTE=label_ajoute)
        r = subprocess.run(["bash", "-c", self._pas_portee()], cwd=d, env=env,
                           capture_output=True, text=True)
        sorties = dict(l.split("=", 1) for l in sortie.read_text("utf-8").splitlines() if "=" in l)
        return r, sorties

    def test_un_label_etranger_ajoute_sur_une_pr_qui_porte_evals_ne_relance_pas_le_banc(self):
        r, sorties = self.jouer("evals\nreview-required", "review-required")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorties["touche"], "false")
        self.assertEqual(sorties["selection"], "{}")
        self.assertIn("review-required", r.stdout)  # le log dit pourquoi on ne joue pas

    def test_le_label_evals_qui_vient_d_etre_pose_joue_les_evals(self):
        for ajoute in ("evals", "Evals"):
            with self.subTest(label_ajoute=ajoute):
                r, sorties = self.jouer("evals", ajoute)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertEqual(sorties["touche"], "true")
                self.assertEqual(json.loads(sorties["plugins"]), ["jouet"])

    def test_sans_label_ajoute_ni_opened_ni_synchronize_ne_changent_rien(self):
        # `opened`, `synchronize`, `reopened` : pas de label dans l'événement.
        r, sorties = self.jouer("evals", "")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorties["touche"], "true")

    def test_un_label_etranger_ne_dispense_pas_du_controle_label_ou_aucun(self):
        # Sans ce contrôle, un `labeled` étranger rendrait vert un SHA que le run
        # précédent avait rendu rouge (le trou de `edited`).
        r, sorties = self.jouer("review-required", "review-required", corps="")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(sorties["touche"], "false")


def _blocs_run(texte: str):
    """Les corps de ``run:`` d'un workflow, sans PyYAML : (ligne, texte).

    Couvre ``run: |`` / ``run: >`` (avec ou sans ``-``/``+``) : le corps est
    l'ensemble des lignes suivantes plus indentées que la clé ``run:``, lignes
    vides et commentaires compris. Couvre aussi ``run: commande`` sur une ligne.
    """
    lignes = texte.split("\n")
    i = 0
    while i < len(lignes):
        m = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", lignes[i])
        if not m:
            i += 1
            continue
        indent = len(m.group(1))
        reste = m.group(2).strip()
        if re.fullmatch(r"[|>][-+]?\d*", reste):
            debut = i + 1
            corps = []
            i += 1
            while i < len(lignes) and (
                not lignes[i].strip() or len(lignes[i]) - len(lignes[i].lstrip()) > indent
            ):
                corps.append(lignes[i])
                i += 1
            yield debut + 1, "\n".join(corps)
        else:
            yield i + 1, reste
            i += 1


class WorkflowsSansExpressionDansRun(unittest.TestCase):
    def test_aucun_bloc_run_ne_contient_d_expression_meme_en_commentaire(self):
        fautifs = []
        for fichier in sorted((RACINE / ".github" / "workflows").glob("*.yml")):
            for debut, corps in _blocs_run(fichier.read_text(encoding="utf-8")):
                for k, ligne in enumerate(corps.split("\n")):
                    if "${{" in ligne:
                        fautifs.append(f"{fichier.name}:{debut + k}: {ligne.strip()}")
        self.assertEqual(
            fautifs, [],
            "Un bloc `run:` contient `${{` : GitHub évalue les expressions dans tout "
            "le texte d'un `run:`, commentaires bash compris, et un `${{` invalide "
            "(p. ex. `${{ … }}` cité en exemple dans un commentaire) rend le workflow "
            "entier inutilisable (HTTP 422 « failed to parse workflow », aucune CI ne "
            "démarre). Une donnée passe par `env:`, jamais par une interpolation dans "
            "`run:`. Occurrences :\n" + "\n".join(fautifs),
        )

    def test_l_extracteur_voit_un_commentaire_dans_un_bloc_et_ignore_env(self):
        texte = (
            "jobs:\n  a:\n    steps:\n      - name: x\n        env:\n"
            "          V: ${{ github.sha }}\n        run: |\n"
            "          # exemple (`${{ … }}`)\n          echo ok\n"
            "      - run: echo ${{ 1 }}\n      - run: echo propre\n"
        )
        blocs = [c for _, c in _blocs_run(texte)]
        self.assertEqual(len(blocs), 3)
        self.assertEqual([("${{" in c) for c in blocs], [True, True, False])


if __name__ == "__main__":
    unittest.main()
