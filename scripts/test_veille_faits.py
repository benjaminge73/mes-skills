"""Tests de ``veille_faits.py`` sur des pages **figées** (aucun réseau).

Les pages vivent dans ``scripts/fixtures_veille/`` : une copie intacte et une
copie où une citation a été altérée. Le script est réfuté sur les deux — la
première ne doit rien signaler, la seconde doit signaler le fait touché et
seulement celui-là.
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import veille_faits  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures_veille"
INTACTES = FIXTURES / "pages_intactes"
ALTEREES = FIXTURES / "pages_alterees"
RACINE = Path(__file__).resolve().parents[1]


def _faits():
    return veille_faits.lire_faits((FIXTURES / "faits.md").read_text(encoding="utf-8"))


class LireLesFaits(unittest.TestCase):
    def test_le_tableau_de_la_fixture_donne_trois_faits_complets(self):
        faits = _faits()
        self.assertEqual(len(faits), 3)
        premier = faits[0]
        self.assertEqual(premier.fait, "Plafond de la description")
        self.assertTrue(premier.citation.startswith("the combined `description`"))
        self.assertNotIn("«", premier.citation)
        self.assertEqual(premier.url, "https://code.claude.com/docs/en/skills.md")
        self.assertEqual(premier.verifie, "2026-09-30")
        self.assertIn("check_skills.py", premier.controle)

    def test_le_tableau_reel_est_lisible_et_ses_controles_existent(self):
        faits = veille_faits.lire_faits((RACINE / "docs" / "veille.md").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(faits), 8)
        for f in faits:
            with self.subTest(fait=f.fait):
                self.assertTrue(f.citation.strip())
                self.assertRegex(f.url, r"^https://")
                self.assertRegex(f.verifie, r"^\d{4}-\d{2}-\d{2}$")
                chemins = re.findall(r"`((?:scripts|evals|\.github)/[\w./-]+)`", f.controle)
                self.assertTrue(chemins, f"le contrôle de « {f.fait} » ne cite aucun script")
                for chemin in chemins:
                    self.assertTrue((RACINE / chemin).is_file(), f"{chemin} n'existe pas")

    def test_les_faits_du_tableau_reel_ont_ete_releves_dans_les_pages_de_doc(self):
        faits = veille_faits.lire_faits((RACINE / "docs" / "veille.md").read_text(encoding="utf-8"))
        urls = {f.url for f in faits}
        self.assertIn("https://code.claude.com/docs/en/skills.md", urls)
        self.assertIn("https://code.claude.com/docs/en/sub-agents.md", urls)


class Normaliser(unittest.TestCase):
    def test_espaces_retours_a_la_ligne_et_casse_sont_ignores(self):
        self.assertEqual(veille_faits.normaliser("Keep  `SKILL.md`\n under\t500 LINES."),
                         veille_faits.normaliser("keep `skill.md` under 500 lines."))

    def test_une_valeur_differente_reste_differente(self):
        self.assertNotEqual(veille_faits.normaliser("1,536 characters"),
                            veille_faits.normaliser("2,048 characters"))

    def test_le_html_est_reduit_a_son_texte(self):
        self.assertIn(veille_faits.normaliser("truncated at 1,536 characters"),
                      veille_faits.normaliser("<p>truncated at <b>1,536</b>&nbsp;characters</p>"))


class Verifier(unittest.TestCase):
    def test_des_pages_intactes_ne_signalent_rien(self):
        resultats = veille_faits.verifier(_faits(), veille_faits.lire_dossier(INTACTES))
        self.assertEqual([r.statut for r in resultats], ["trouve"] * 3)
        self.assertEqual(veille_faits.a_signaler(resultats), [])

    def test_une_citation_alteree_signale_ce_fait_et_lui_seul(self):
        resultats = veille_faits.verifier(_faits(), veille_faits.lire_dossier(ALTEREES))
        a_signaler = veille_faits.a_signaler(resultats)
        self.assertEqual([r.fait.fait for r in a_signaler], ["Plafond de la description"])
        self.assertEqual(a_signaler[0].statut, "absent")

    def test_une_page_injoignable_n_est_pas_un_doc_change(self):
        def recuperer(url):
            raise OSError("réseau coupé")
        resultats = veille_faits.verifier(_faits(), recuperer)
        self.assertEqual({r.statut for r in resultats}, {"injoignable"})
        self.assertEqual(veille_faits.a_signaler(resultats), [])

    def test_une_page_est_lue_une_seule_fois_pour_plusieurs_faits(self):
        appels = []
        lecteur = veille_faits.lire_dossier(INTACTES)

        def recuperer(url):
            appels.append(url)
            return lecteur(url)
        veille_faits.verifier(_faits(), recuperer)
        self.assertEqual(len(appels), 2)


class Issues(unittest.TestCase):
    def resultat_absent(self):
        resultats = veille_faits.verifier(_faits(), veille_faits.lire_dossier(ALTEREES))
        return veille_faits.a_signaler(resultats)

    def test_le_titre_et_le_corps_disent_le_fait_l_url_et_le_controle(self):
        r = self.resultat_absent()[0]
        self.assertEqual(veille_faits.titre_issue(r.fait),
                         "Doc Claude changée : Plafond de la description")
        corps = veille_faits.corps_issue(r)
        self.assertIn("https://code.claude.com/docs/en/skills.md", corps)
        self.assertIn("scripts/check_skills.py", corps)
        self.assertIn("the combined `description`", corps)

    def test_une_issue_ouverte_du_meme_titre_empeche_le_doublon(self):
        creees = []
        titre = veille_faits.titre_issue(self.resultat_absent()[0].fait)
        nouvelles = veille_faits.ouvrir_issues(
            self.resultat_absent(), lambda: {titre}, lambda t, c: creees.append(t))
        self.assertEqual((nouvelles, creees), ([], []))

    def test_sans_issue_ouverte_elle_est_creee_une_fois_meme_rejouee(self):
        ouvertes: set[str] = set()

        def creer(titre, corps):
            ouvertes.add(titre)
        premiere = veille_faits.ouvrir_issues(self.resultat_absent(), lambda: set(ouvertes), creer)
        seconde = veille_faits.ouvrir_issues(self.resultat_absent(), lambda: set(ouvertes), creer)
        self.assertEqual(premiere, ["Doc Claude changée : Plafond de la description"])
        self.assertEqual(seconde, [])

    def test_l_api_ignore_les_pull_requests_et_suit_les_pages(self):
        pages = {
            1: [{"title": "Doc Claude changée : A"}] * 100,
            2: [{"title": "Doc Claude changée : B", "pull_request": {}},
                {"title": "Doc Claude changée : C"}],
        }

        class Fausse(veille_faits.GitHubAPI):
            def appel(self, methode, chemin, corps=None):
                page = int(re.search(r"[?&]page=(\d+)", chemin).group(1))
                return pages.get(page, [])
        titres = Fausse("proprietaire/depot", "jeton").titres_ouverts()
        self.assertEqual(titres, {"Doc Claude changée : A", "Doc Claude changée : C"})


class Programme(unittest.TestCase):
    def lancer(self, *args):
        sortie, erreur = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
            code = veille_faits.main(list(args))
        return code, sortie.getvalue(), erreur.getvalue()

    def test_pages_intactes_code_0_et_tous_les_faits_trouves(self):
        code, sortie, _ = self.lancer("--faits", str(FIXTURES / "faits.md"), "--pages", str(INTACTES))
        self.assertEqual(code, 0)
        self.assertEqual(sortie.count("trouvé"), 3)

    def test_pages_alterees_code_1_et_le_fait_est_nomme(self):
        code, sortie, _ = self.lancer("--faits", str(FIXTURES / "faits.md"), "--pages", str(ALTEREES))
        self.assertEqual(code, 1)
        self.assertIn("Plafond de la description", sortie)
        self.assertIn("introuvable", sortie)

    def test_par_defaut_aucune_issue_n_est_creee(self):
        # Sans `--ouvrir-issues`, main() ne doit même pas chercher un jeton.
        code, sortie, erreur = self.lancer("--faits", str(FIXTURES / "faits.md"), "--pages", str(ALTEREES))
        self.assertEqual(code, 1)
        self.assertNotIn("issue créée", sortie + erreur)

    def test_ouvrir_issues_sans_jeton_est_une_panne_claire(self):
        import os
        ancien = {k: os.environ.pop(k, None) for k in ("GITHUB_TOKEN", "GITHUB_REPOSITORY")}
        try:
            code, _, erreur = self.lancer("--faits", str(FIXTURES / "faits.md"),
                                          "--pages", str(ALTEREES), "--ouvrir-issues")
        finally:
            for k, v in ancien.items():
                if v is not None:
                    os.environ[k] = v
        self.assertEqual(code, 2)
        self.assertIn("GITHUB_TOKEN", erreur)


class Workflow(unittest.TestCase):
    def texte(self):
        chemin = RACINE / ".github" / "workflows" / "veille.yml"
        self.assertTrue(chemin.is_file(), "veille.yml est absent")
        return chemin.read_text(encoding="utf-8")

    def test_declencheurs_hebdomadaire_et_manuel(self):
        t = self.texte()
        self.assertRegex(t, r"(?m)^on:")
        self.assertRegex(t, r"schedule:\s*\n\s*- cron: ['\"]?[\d*/, ]+ [\d*/, ]+ \* \* [\d*]")
        self.assertIn("workflow_dispatch:", t)

    def test_permissions_minimales(self):
        t = self.texte()
        bloc = re.search(r"(?m)^permissions:\n((?:  .*\n)+)", t)
        self.assertIsNotNone(bloc, "pas de permissions: au niveau du workflow")
        permissions = dict(re.findall(r"^  (\w[\w-]*): (\w+)", bloc.group(1), re.MULTILINE))
        self.assertEqual(permissions, {"contents": "read", "issues": "write"})

    def test_les_actions_sont_epinglees_par_sha_complet_comme_dans_ci_yml(self):
        t = self.texte()
        usages = re.findall(r"uses: (\S+)", t)
        self.assertTrue(usages)
        for u in usages:
            self.assertRegex(u, r"@[0-9a-f]{40}$", f"{u} n'est pas épinglée par SHA complet")
        ci = (RACINE / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        for u in usages:
            self.assertIn(f"uses: {u}", ci, f"{u} n'est pas le SHA déjà utilisé dans ci.yml")

    def test_aucun_secret_autre_que_github_token_et_aucun_modele(self):
        t = self.texte()
        for secret in re.findall(r"secrets\.(\w+)", t):
            self.assertEqual(secret, "GITHUB_TOKEN")
        self.assertNotRegex(t.lower(), r"anthropic|claude-code|claude_code|npm install")

    def test_le_workflow_appelle_veille_faits_avec_l_option_de_creation(self):
        t = self.texte()
        self.assertIn("scripts/veille_faits.py --ouvrir-issues", t)


if __name__ == "__main__":
    unittest.main()
