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
    "### ✅ Q1 — Un choix\n\n<callout color=\"green_bg\">**Q1 — réponse**</callout>\n\n"
)
EXECUTION = (
    "## Exécution\n\n"
    "### Étape 1 — Un titre\n\n- **Preuve de fin** : `pytest -q` → tout vert\n\n"
)
PUCES_OK = {
    "Relecture": "chapitre Exécution relu le 2026-10-15, une réponse reprise (étape 2)",
    "Questions": "Q1 verte, 1 sur 1",
    "Preuves": "`preuves-des-etapes.py --avant` code 0 ; `verifier-preuves.py` code 0",
    "Répétition": "État de départ présent, suite verte (412 passés)",
    "Maquette": "sans objet — aucune étape à impact fonctionnel",
    "CI": "push sans run, pas d'e2e, `review-required` sans effet, `merge-auto` actif",
    "Vagues": "vague 1 : étapes 1 et 2 ; vague 2 : étape 3",
    "Pilote": "Sonnet 5.5, high",
    "Branche": "`feat/le-theme`, worktree `~/repos/worktrees/depot/feat-le-theme`",
}


def ouverture(**surcharges):
    """Entrée « Ouverture » complète ; une valeur ``None`` retire la puce, une chaîne la remplace."""
    puces = {**PUCES_OK, **surcharges}
    corps = "".join(f"- **{k}** : {v}\n" for k, v in puces.items() if v is not None)
    return f"### Ouverture\n\n{corps}\n"


def page(questions=QUESTIONS, execution=EXECUTION, journal=None):
    journal = ouverture() if journal is None else journal
    return f"# Plan de test\n\n{questions}{execution}## Journal d'exécution\n\n{journal}"


def jouer(texte):
    with tempfile.TemporaryDirectory() as d:
        chemin = Path(d) / "page.md"
        chemin.write_text(texte, encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(chemin)],
                           capture_output=True, text=True)
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


if __name__ == "__main__":
    unittest.main()
