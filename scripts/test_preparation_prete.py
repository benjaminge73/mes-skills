"""Tests de ``preparation-prete.py`` : la porte du statut ``pret``, une panne nommée, un test.

Les pages sont des chaînes écrites dans chaque test (pas de fixture sur disque) :
c'est le format du miroir Notion qui est testé. Le script tourne en sous-processus,
comme ``test_preuves_des_etapes.py``, et l'on observe sa sortie et son code retour.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "preparation-prete.py"

QUESTIONS = (
    "## Questions ouvertes\n\n"
    "### ✅ Q1 — Un choix\n\n- [x] la réponse retenue\nPreuve : commande — `pytest -q` → 12 passés\n\n"
)
TABLEAU = (
    '<table header-row="true">\n<tr><td>Étape</td><td>Fichiers touchés</td><td>Dépend de</td>'
    '<td>Vague</td></tr>\n'
    '<tr><td>1 · un titre</td><td>`a.py`</td><td>—</td><td>1</td></tr>\n'
    '<tr><td>2 · un autre</td><td>`b.py`</td><td>—</td><td>1</td></tr>\n</table>\n\n'
)
EXECUTION = (
    "## Exécution\n\n" + TABLEAU +
    "### Étape 1 — Un titre\n\n- **Preuve de fin** : `pytest a -q` → tout vert\n\n"
    "### Étape 2 — Un autre\n\n- **Preuve de fin** : `pytest b -q` → tout vert\n\n"
)
PUCES_OK = {
    "Relecture": "chapitre Exécution relu le 2026-10-15, une réponse reprise (étape 2)",
    "Questions": "Q1 verte, 1 sur 1",
    "Preuves": "`preuves-des-etapes.py --avant` code 0 ; `verifier-preuves.py` code 0",
    "Répétition": "État de départ présent, suite verte (412 passés)",
    "Maquette": "sans objet — aucune étape à impact fonctionnel",
    "CI": "push sans run, pas d'e2e, `review-required` sans effet, `merge-auto` actif",
    "Vagues": "vague 1 : étapes 1 et 2 (fichiers disjoints)",
    "Pilote": "Sonnet 5.5, medium",
    "Branche": "`feat/le-theme`, worktree `~/repos/worktrees/depot/feat-le-theme`",
    "Orchestration": "sans objet — aucun plan maître",
    "Preuve de l'étape 1": "`pytest a -q` rejouée à blanc : code 1 attendu (étape à faire)",
    "Preuve de l'étape 2": "`pytest b -q` rejouée à blanc : code 1 attendu (étape à faire)",
}
MAITRE = (
    "# [Plan maître] Projet\n\n## Plans\n\n| plan | Statut |\n| --- | --- |\n| A | pret |\n\n"
    "## Croisement\n\nA et B partent ensemble, C attend A.\n\n"
    "## Ordre de merge\n\nA puis C (fichier commun `x.py`).\n\n"
    "## File des actions lourdes\n\nSuite complète de A, puis celle de B.\n\n"
    "## Avancement\n\n- 2026-10-15 : lot préparé.\n"
)


def ouverture(**surcharges):
    """Entrée « Ouverture » complète ; une valeur ``None`` retire la puce, une chaîne la remplace.

    Les clés à espaces ou apostrophe se passent par ``{"Preuve de l'étape 1": …}`` (``**``).
    """
    puces = {**PUCES_OK, **surcharges}
    corps = "".join(f"- **{k}** : {v}\n" for k, v in puces.items() if v is not None)
    return f"### Ouverture\n\n{corps}\n"


def page(questions=QUESTIONS, execution=EXECUTION, journal=None):
    journal = ouverture() if journal is None else journal
    return f"# Plan de test\n\n{questions}{execution}## Journal d'exécution\n\n{journal}"


def jouer(texte, maitre=None, depot=True):
    with tempfile.TemporaryDirectory() as d:
        chemin = Path(d) / "page.md"
        chemin.write_text(texte, encoding="utf-8")
        args = [str(chemin)]
        if depot:
            args += ["--depot", d]
        if maitre is not None:
            m = Path(d) / "maitre.md"
            m.write_text(maitre, encoding="utf-8")
            args += ["--maitre", str(m)]
        r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class PorteDuPret(unittest.TestCase):
    def test_une_preparation_complete_est_prete(self):
        code, sortie, _ = jouer(page())
        self.assertEqual(code, 0, sortie)
        self.assertIn("prêt", sortie)

    def test_sans_entree_ouverture_la_page_n_est_pas_prete(self):
        code, sortie, _ = jouer(page(journal="### Étape 1 — Un titre\n\n- rien\n"))
        self.assertEqual(code, 1)
        self.assertIn("« Ouverture » absente", sortie)

    def test_chaque_puce_manquante_est_nommee(self):
        for cle in PUCES_OK:
            with self.subTest(cle=cle):
                code, sortie, _ = jouer(page(journal=ouverture(**{cle: None})))
                self.assertEqual(code, 1)
                self.assertIn(f"puce **{cle}** absente", sortie)

    def test_une_coquille_ne_compte_pas_comme_une_trace(self):
        for coquille in ("—", "à voir", "aucune", ""):
            with self.subTest(coquille=coquille):
                code, sortie, _ = jouer(page(journal=ouverture(Vagues=coquille)))
                self.assertEqual(code, 1)
                self.assertIn("**Vagues** vide", sortie)

    def test_sans_objet_exige_sa_raison(self):
        for nu in ("sans objet", "sans objet —", "Sans objet : "):
            with self.subTest(nu=nu):
                code, sortie, _ = jouer(page(journal=ouverture(Maquette=nu)))
                self.assertEqual(code, 1)
                self.assertIn("**Maquette** « sans objet » sans raison", sortie)

    def test_sans_objet_avec_raison_est_recevable(self):
        code, sortie, _ = jouer(page(journal=ouverture(Répétition="sans objet — plan de pure doc")))
        self.assertEqual(code, 0, sortie)

    def test_une_question_restee_ouverte_bloque(self):
        ouverte = QUESTIONS + "### 🧭 Q2 — Pas encore tranchée\n\n<callout color=\"orange_bg\">…</callout>\n\n"
        code, sortie, _ = jouer(page(questions=ouverte))
        self.assertEqual(code, 1)
        self.assertIn("question ouverte", sortie)
        self.assertIn("Q2", sortie)

    def test_une_etape_sans_preuve_de_fin_bloque(self):
        sans_preuve = "## Exécution\n\n### Étape 1 — Un titre\n\n- **Fichiers touchés** : `a.py`\n\n"
        code, sortie, _ = jouer(page(execution=sans_preuve))
        self.assertEqual(code, 1)
        self.assertIn("preuves :", sortie)

    def test_c_est_la_derniere_ouverture_qui_compte(self):
        # Préparation refaite après un retour à « valide » : l'ancienne entrée complète
        # ne couvre pas la nouvelle, qui a perdu une puce.
        journal = ouverture() + ouverture(Pilote=None)
        code, sortie, _ = jouer(page(journal=journal))
        self.assertEqual(code, 1)
        self.assertIn("puce **Pilote** absente", sortie)

    def test_un_pilote_qui_n_est_pas_sonnet_medium_bloque(self):
        for pilote in ("Opus 5.5, high", "Sonnet 5.5, high", "Opus 5.5, medium"):
            with self.subTest(pilote=pilote):
                code, sortie, _ = jouer(page(journal=ouverture(Pilote=pilote)))
                self.assertEqual(code, 1)
                self.assertIn("**Pilote** n'est pas Sonnet `medium`", sortie)

    def test_une_derogation_citee_de_benjamin_rend_le_pilote_recevable(self):
        derogation = "Opus 5.5, high — dérogation de Benjamin, 2026-10-19 : « pilote celui-ci en Opus »"
        code, sortie, _ = jouer(page(journal=ouverture(Pilote=derogation)))
        self.assertEqual(code, 0, sortie)

    def test_une_derogation_sans_citation_ne_compte_pas(self):
        code, sortie, _ = jouer(page(journal=ouverture(Pilote="Opus 5.5, high — dérogation de Benjamin")))
        self.assertEqual(code, 1)
        self.assertIn("**Pilote** n'est pas Sonnet `medium`", sortie)

    def test_tous_les_defauts_sont_rendus_d_un_coup(self):
        code, sortie, _ = jouer(page(journal=ouverture(CI=None, Vagues="—")))
        self.assertEqual(code, 1)
        self.assertIn("**CI** absente", sortie)
        self.assertIn("**Vagues** vide", sortie)

    def test_un_chapitre_absent_est_illisible(self):
        for nom, texte in (
            ("Questions ouvertes", f"# P\n\n{EXECUTION}## Journal d'exécution\n\n{ouverture()}"),
            ("Exécution", f"# P\n\n{QUESTIONS}## Journal d'exécution\n\n{ouverture()}"),
            ("Journal d'exécution", f"# P\n\n{QUESTIONS}{EXECUTION}"),
        ):
            with self.subTest(nom=nom):
                code, _, erreur = jouer(texte)
                self.assertEqual(code, 2)
                self.assertIn(nom, erreur)

    def test_sans_argument_le_script_dit_l_usage(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)

    def test_sans_depot_le_script_refuse_de_juger(self):
        code, _, erreur = jouer(page(), depot=False)
        self.assertEqual(code, 2)
        self.assertIn("--depot", erreur)


class ToutesLesEtapesProuvees(unittest.TestCase):
    def test_une_etape_sans_sa_preuve_rejouee_a_blanc_bloque(self):
        # La « Preuve de fin » est écrite, mais personne n'a joué la commande.
        code, sortie, _ = jouer(page(journal=ouverture(**{"Preuve de l'étape 2": None})))
        self.assertEqual(code, 1)
        self.assertIn("puce **Preuve de l'étape 2** absente", sortie)

    def test_une_etape_ajoutee_au_chapitre_exige_sa_puce(self):
        execution = EXECUTION + (
            "### Étape D1 — Une découverte\n\n- **Preuve de fin** : `pytest d -q` → tout vert\n\n")
        code, sortie, _ = jouer(page(execution=execution))
        self.assertEqual(code, 1)
        self.assertIn("puce **Preuve de l'étape D1** absente", sortie)

    def test_une_reponse_tranchee_sans_preuve_bloque(self):
        sans_preuve = "## Questions ouvertes\n\n### ✅ Q1 — Un choix\n\n- [x] la réponse retenue\n\n"
        code, sortie, _ = jouer(page(questions=sans_preuve))
        self.assertEqual(code, 1)
        self.assertIn("réponses : Q1 : sans ligne Preuve", sortie)


class ParalleliserLesEtapes(unittest.TestCase):
    def test_une_colonne_vague_fausse_bloque(self):
        # L'étape 2 dépend de la 1 : elle ne peut pas être dans la même vague.
        faux = EXECUTION.replace("<td>`b.py`</td><td>—</td><td>1</td>",
                                 "<td>`b.py`</td><td>1</td><td>1</td>")
        code, sortie, _ = jouer(page(execution=faux))
        self.assertEqual(code, 1)
        self.assertIn("vagues :", sortie)

    def test_sans_tableau_de_chevauchement_pas_de_pret(self):
        sans_tableau = EXECUTION.replace(TABLEAU, "")
        code, sortie, _ = jouer(page(execution=sans_tableau))
        self.assertEqual(code, 1)
        self.assertIn("vagues :", sortie)


class OrchestrationEntrePlans(unittest.TestCase):
    CITE = {"Orchestration": "plan A du maître https://app.notion.com/p/abc : parti avec B, avant C"}

    def test_un_plan_maitre_cite_sans_sa_page_bloque(self):
        code, sortie, _ = jouer(page(journal=ouverture(**self.CITE)))
        self.assertEqual(code, 1)
        self.assertIn("`--maitre <miroir>` manque", sortie)

    def test_une_page_maitre_complete_rend_zero(self):
        code, sortie, _ = jouer(page(journal=ouverture(**self.CITE)), maitre=MAITRE)
        self.assertEqual(code, 0, sortie)

    def test_chaque_section_du_maitre_est_exigee(self):
        for titre in ("Plans", "Croisement", "Ordre de merge", "File des actions lourdes"):
            with self.subTest(titre=titre):
                sans = MAITRE.replace(f"## {titre}\n", "## Autre\n")
                code, sortie, _ = jouer(page(journal=ouverture(**self.CITE)), maitre=sans)
                self.assertEqual(code, 1)
                self.assertIn(f"section « {titre} » absente", sortie)

    def test_une_section_vide_du_maitre_ne_compte_pas(self):
        vide = MAITRE.replace("A et B partent ensemble, C attend A.\n", "—\n")
        code, sortie, _ = jouer(page(journal=ouverture(**self.CITE)), maitre=vide)
        self.assertEqual(code, 1)
        self.assertIn("section « Croisement » vide", sortie)

    def test_sans_plan_maitre_la_page_maitre_n_est_pas_lue(self):
        code, sortie, _ = jouer(page(), maitre="# rien\n")
        self.assertEqual(code, 0, sortie)


if __name__ == "__main__":
    unittest.main()
