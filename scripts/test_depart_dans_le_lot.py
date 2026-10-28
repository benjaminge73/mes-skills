"""Tests de ``depart-dans-le-lot.py`` : un plan du lot ne démarre que si le Croisement du maître le permet."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SKILLS = RACINE / "plugins" / "plans-notion" / "skills"
SCRIPT = SKILLS / "_partage" / "scripts" / "depart-dans-le-lot.py"

MAITRE = """# [Plan maître] demo - Trois plans

## Plans

| Id | Plan | Statut |
|---|---|---|
| P1 | Socle | en cours |
| P2 | Interface | pret |
| P3 | Doc | pret |
| P4 | Migration | valide |

## Croisement

- **P2** attend **P1** jusqu'à `a merger` : l'interface appelle le socle.
- P3 attend P1 : la doc décrit ce qui est sur main.
- P2 exclut P4 : même port e2e.
- P1, P3 et P4 partent ensemble, le reste est parallèle.

## Ordre de merge

P1 puis P2.
"""


def jouer(plan, *statuts, maitre=MAITRE):
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "maitre.md"
        page.write_text(maitre, encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(page), plan, "--statuts", *statuts],
                           capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


TOUS = ("P1=en cours", "P2=pret", "P3=pret", "P4=valide")


class DepartDansLeLot(unittest.TestCase):
    def test_un_plan_qui_attend_un_autre_en_cours_ne_demarre_pas(self):
        code, sortie, _ = jouer("P2", *TOUS)
        self.assertEqual(code, 1)
        self.assertIn("P2 attend P1 jusqu'à `a merger` : P1 est `en cours`", sortie)

    def test_le_seuil_est_atteint_quand_le_plan_attendu_arrive_au_statut_demande(self):
        for lu in ("a merger", "execute"):
            with self.subTest(lu=lu):
                self.assertEqual(jouer("P2", f"P1={lu}", "P2=pret", "P3=pret", "P4=valide")[0], 0)

    def test_sans_jusqu_a_le_seuil_est_execute(self):
        # P3 attend P1 : la doc décrit ce qui est sur main, `a merger` ne suffit pas.
        self.assertEqual(jouer("P3", "P1=a merger", "P2=pret", "P3=pret", "P4=valide")[0], 1)
        self.assertEqual(jouer("P3", "P1=execute", "P2=pret", "P3=pret", "P4=valide")[0], 0)

    def test_un_plan_archive_ne_retient_personne(self):
        self.assertEqual(jouer("P3", "P1=archive", "P2=pret", "P3=pret", "P4=valide")[0], 0)

    def test_deux_plans_exclus_ne_tournent_pas_ensemble_dans_les_deux_sens(self):
        for plan, autre, statuts in (("P2", "P4", ("P1=execute", "P2=pret", "P3=pret", "P4=en cours")),
                                     ("P4", "P2", ("P1=execute", "P2=en cours", "P3=pret", "P4=pret"))):
            with self.subTest(plan=plan):
                code, sortie, _ = jouer(plan, *statuts)
                self.assertEqual(code, 1)
                self.assertIn(f"{plan} et {autre} ne tournent pas ensemble", sortie)

    def test_le_parallele_est_le_defaut(self):
        # P4 n'attend rien et P2 n'est pas en cours : il part, même si P1 n'a pas fini.
        self.assertEqual(jouer("P4", *TOUS)[0], 0)

    def test_un_plan_hors_du_tableau_plans_est_illisible(self):
        code, _, erreur = jouer("P9", *TOUS)
        self.assertEqual(code, 2)
        self.assertIn("P9", erreur)

    def test_un_statut_manquant_ou_accentue_est_illisible(self):
        self.assertEqual(jouer("P2", "P2=pret")[0], 2)
        self.assertEqual(jouer("P2", "P1=en cours", "P2=prêt")[0], 2)

    def test_sans_section_croisement_le_depart_est_illisible_et_non_permis(self):
        sans = MAITRE.replace("## Croisement", "## Autre chose")
        self.assertEqual(jouer("P2", *TOUS, maitre=sans)[0], 2)

    def test_chaque_endroit_qui_passe_un_plan_en_cours_renvoie_au_script(self):
        # Le script ne se joue pas tout seul : ce qui tient la règle, c'est qu'elle soit écrite
        # là où un plan démarre (porte d'entrée, ouverture, page maître) et dans les invariants.
        for chemin in ("executer-plan-notion/SKILL.md", "executer-plan-notion/ouverture.md",
                       "plan-notion/plan-maitre.md"):
            with self.subTest(fichier=chemin):
                texte = " ".join((SKILLS / chemin).read_text(encoding="utf-8").split())
                self.assertIn("depart-dans-le-lot.py", texte)
        maitre = (SKILLS / "plan-notion" / "plan-maitre.md").read_text(encoding="utf-8")
        self.assertIn("## Un plan du lot ne s'exécute pas seul", maitre)

    def test_la_session_suit_la_pr_jusqu_au_merge_et_met_les_plans_a_jour(self):
        # Règle de Benjamin du 2026-10-22 : pas d'arrêt à l'ouverture de la PR. Le garde tient
        # la présence de la règle à ses deux endroits, pas son usage par une session.
        for chemin, attendu in (("_partage/remontee-sur-main.md", "La session ne part pas à l'ouverture de la PR"),
                                ("executer-plan-notion/cloture.md", "sans quitter la PR"),
                                ("executer-plan-notion/SKILL.md", "suit la PR jusqu'au merge")):
            with self.subTest(fichier=chemin):
                texte = " ".join((SKILLS / chemin).read_text(encoding="utf-8").split())
                self.assertIn(attendu, texte)

    def test_le_maitre_se_reverifie_quand_le_contenu_d_un_plan_change(self):
        for chemin in ("plan-notion/plan-maitre.md", "_partage/ecrire-dans-notion.md"):
            with self.subTest(fichier=chemin):
                texte = " ".join((SKILLS / chemin).read_text(encoding="utf-8").split())
                self.assertIn("Le maître se revérifie aussi quand le contenu d'un plan change", texte)

    def test_les_plans_du_lot_sont_des_sous_elements_et_jamais_deplaces(self):
        texte = " ".join((SKILLS / "plan-notion" / "plan-maitre.md").read_text(encoding="utf-8").split())
        self.assertIn("## Les plans du lot, sous-éléments du maître", texte)
        self.assertIn("Jamais `notion-move-pages` sous la page maître", texte)

    def test_le_rattachement_se_relit_des_deux_cotes_et_jamais_par_la_page(self):
        # Vu le 2026-10-22 : un plan glissé dans le corps du maître quitte la base, et une relation
        # à sens unique ne l'affiche pas sous lui. Le garde tient les deux phrases de la règle.
        texte = " ".join((SKILLS / "plan-notion" / "plan-maitre.md").read_text(encoding="utf-8").split())
        self.assertIn("devient une simple sous-page hors de la base", texte)
        self.assertIn("Relire les deux côtés, dans le même tour", texte)
        self.assertIn("avec la liste complète de ses enfants", texte)

    def test_le_deuxieme_plan_d_un_projet_cree_le_maitre(self):
        # Relevé du 2026-10-28 : Benjamin a dû demander le maître à une session qui venait de créer
        # trois plans. Le garde tient la règle à ses trois endroits et la coquille qui la rend sûre
        # (`à définir` est une coquille pour preparation-prete.py : aucun plan du lot ne passe `pret`
        # avant que le Croisement soit écrit), pas l'usage par une session.
        maitre = " ".join((SKILLS / "plan-notion" / "plan-maitre.md").read_text(encoding="utf-8").split())
        self.assertIn("## Le deuxième plan d'un projet crée le maître", maitre)
        self.assertIn("à chaque création d'une page de plan", maitre)
        self.assertIn("même si les deux ne sont pas créés le même jour", maitre)
        self.assertIn("portent la seule ligne `à définir`", maitre)
        for chemin in ("plan-notion/SKILL.md", "_partage/plan-de-suite.md"):
            with self.subTest(fichier=chemin):
                texte = " ".join((SKILLS / chemin).read_text(encoding="utf-8").split())
                self.assertIn("Le deuxième plan d'un projet crée le maître", texte)

    def test_la_coquille_du_maitre_n_est_pas_une_orchestration(self):
        # La coquille écrite à la naissance du maître doit être refusée par la porte `pret`.
        import importlib.util
        chemin = SKILLS / "_partage" / "scripts" / "preparation-prete.py"
        spec = importlib.util.spec_from_file_location("preparation_prete", chemin)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        coquille = "\n".join(f"## {nom}\n\nà définir\n" for nom in
                             ("Plans", "Croisement", "Ordre de merge", "File des actions lourdes"))
        defauts = module.defauts_maitre(coquille)
        for nom in ("Croisement", "Ordre de merge", "File des actions lourdes"):
            self.assertTrue(any(nom in d and "vide" in d for d in defauts), (nom, defauts))


if __name__ == "__main__":
    unittest.main()
