"""Tests de ``preuves-des-etapes.py`` : une panne nommée, un test.

Les pages sont des chaînes écrites dans chaque test (pas de fixture sur disque) :
le format du chapitre « Exécution » et du « Journal d'exécution » tient en
quelques lignes, et c'est ce format qui est testé. Le script tourne en
sous-processus, comme ``test_verifier_preuves.py``, et l'on observe sa sortie
et son code retour.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "preuves-des-etapes.py"

ENTETE = "# Plan de test\n\n## Cartes\n\n- une carte\n\n"
PREUVE_DE_FIN = "- **Preuve de fin** : `pytest -q` → tout vert"

# Les quatre champs d'une entrée de journal conforme, dans l'ordre de la page.
CHAMPS_OK = {
    "Preuve": "- **Preuve** (rejouée par le pilote) : `pytest -q` → 12 passés",
    "Commit": "- **Commit** : `abc1234`. **Modèle** : claude-haiku-5-5",
    "Découvertes": "- **Découvertes** : aucune",
    "Verdict": "- **Verdict** : verified",
}


def jouer(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def chapitre(*etapes):
    return "## Exécution\n\n" + "".join(etapes)


def etape(numero, *puces):
    corps = "".join(f"{p}\n" for p in puces)
    return f"### Étape {numero} — Un titre\n\n{corps}\n"


def journal(*blocs):
    ouverture = "### Ouverture\n\n- **Date** : 2026-10-14.\n\n"
    return "## Journal d'exécution\n\n" + ouverture + "".join(blocs)


def entree(numero, sans=(), remplace=None):
    champs = dict(CHAMPS_OK)
    champs.update(remplace or {})
    for cle in sans:
        champs.pop(cle, None)
    corps = "".join(f"{ligne}\n" for ligne in champs.values())
    return f"### Étape {numero} — Un titre\n\n{corps}\n"


def chapitre_ok(*numeros):
    return chapitre(*(etape(n, PREUVE_DE_FIN) for n in numeros))


def journal_ok(*numeros):
    return journal(*(entree(n) for n in numeros))


def page_ok(numeros=("1", "2", "3")):
    return ENTETE + chapitre_ok(*numeros) + journal_ok(*numeros)


class _Dossier(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def ecrire(self, nom, texte):
        f = self.dossier / nom
        f.write_text(texte, encoding="utf-8")
        return f


class PorteAvant(_Dossier):
    def test_etape_sans_preuve_de_fin_est_nommee_et_refusee(self):
        # Panne : une étape sans « Preuve de fin » passe la porte d'avant.
        p = self.ecrire("p.md", ENTETE + chapitre(
            etape("1", PREUVE_DE_FIN), etape("4", "- **Autre** : rien")))
        code, sortie, _ = jouer(p, "--avant")
        self.assertEqual(code, 1, sortie)
        self.assertIn("Étape 4 : pas de preuve de fin", sortie)
        self.assertNotIn("Étape 1 :", sortie)

    def test_preuve_de_fin_coquille_est_refusee(self):
        # Panne : une valeur qui ne prouve rien (tiret, « aucune », etc.) est acceptée.
        for coquille in ("—", "-", "Aucune", "à définir", "À voir"):
            with self.subTest(coquille=coquille):
                p = self.ecrire("p.md", ENTETE + chapitre(
                    etape("4", f"- **Preuve de fin** : {coquille}")))
                code, sortie, _ = jouer(p, "--avant")
                self.assertEqual(code, 1, sortie)
                self.assertIn("Étape 4 : pas de preuve de fin", sortie)

    def test_toutes_les_preuves_de_fin_presentes_rendent_zero(self):
        # Panne : la porte d'avant refuse un plan entièrement prouvé.
        p = self.ecrire("p.md", page_ok())
        code, sortie, _ = jouer(p, "--avant")
        self.assertEqual(code, 0, sortie)
        self.assertIn("avant : 3 étape(s), toutes ont une preuve de fin", sortie)

    def test_etape_D1_est_reconnue(self):
        # Panne : une étape à numéro « D<n> » est ignorée, donc sa preuve n'est jamais lue.
        p = self.ecrire("p.md", ENTETE + chapitre(etape("1", PREUVE_DE_FIN), etape("D1")))
        code, sortie, _ = jouer(p, "--avant")
        self.assertEqual(code, 1, sortie)
        self.assertIn("Étape D1 : pas de preuve de fin", sortie)

    def test_etape_en_double_dans_le_chapitre_est_refusee(self):
        # Panne : deux sections « Étape 4 » passent pour une seule étape, dans les deux portes.
        for mode in ("--avant", "--apres"):
            with self.subTest(mode=mode):
                p = self.ecrire("p.md", ENTETE + chapitre(
                    etape("4", PREUVE_DE_FIN), etape("4", PREUVE_DE_FIN)) + journal_ok("4"))
                code, sortie, _ = jouer(p, mode)
                self.assertEqual(code, 1, sortie)
                self.assertIn("Étape 4 : en double", sortie)

    def test_page_sans_chapitre_execution_rend_deux(self):
        # Panne : une page sans chapitre « Exécution » passe pour un plan sans étape.
        p = self.ecrire("p.md", ENTETE + "## Questions ouvertes\n\n- rien\n")
        code, sortie, erreur = jouer(p, "--avant")
        self.assertEqual(code, 2, erreur)
        self.assertIn("Exécution", erreur)

    def test_chapitre_sans_etape_rend_deux(self):
        # Panne : un chapitre « Exécution » vide rend zéro étape, donc une porte verte.
        p = self.ecrire("p.md", ENTETE + "## Exécution\n\nDes mots, pas d'étape.\n")
        code, sortie, erreur = jouer(p, "--avant")
        self.assertEqual(code, 2, erreur)
        self.assertIn("aucune étape", erreur)


class PorteApres(_Dossier):
    def test_journal_complet_rend_zero(self):
        # Panne : la porte d'après refuse un journal entièrement vérifié.
        p = self.ecrire("p.md", page_ok())
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 0, sortie)
        self.assertIn("apres : 3 étape(s), toutes verified", sortie)

    def test_etape_sans_entree_de_journal_est_nommee(self):
        # Panne : une étape sans entrée de journal passe la porte d'après.
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal_ok("1", "3"))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 1, sortie)
        self.assertIn("Étape 2 : pas d'entrée de journal", sortie)

    def test_entree_sans_preuve_est_refusee(self):
        # Panne : une entrée sans « Preuve » (ni rejouée) passe.
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
            entree("1"), entree("2", sans=("Preuve",)), entree("3")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 1, sortie)
        self.assertIn("Étape 2 : pas de Preuve", sortie)

    def test_entree_sans_commit_est_refusee(self):
        # Panne : une entrée sans commit, donc sans trace de ce qui a été livré, passe.
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
            entree("1"), entree("2", sans=("Commit",)), entree("3")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 1, sortie)
        self.assertIn("Étape 2 : pas de Commit", sortie)

    def test_entree_sans_decouvertes_est_refusee(self):
        # Panne : une entrée sans ligne « Découvertes » passe.
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
            entree("1"), entree("2", sans=("Découvertes",)), entree("3")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 1, sortie)
        self.assertIn("Étape 2 : pas de Découvertes", sortie)

    def test_verdict_hors_vocabulaire_ou_absent_est_refuse(self):
        # Panne : un verdict « partial » ou absent passe pour une étape vérifiée.
        for ecart in ({"remplace": {"Verdict": "- **Verdict** : partial"}},
                      {"sans": ("Verdict",)}):
            with self.subTest(ecart=ecart):
                p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
                    entree("1"), entree("2", **ecart), entree("3")))
                code, sortie, _ = jouer(p, "--apres")
                self.assertEqual(code, 1, sortie)
                self.assertIn("Étape 2 : Verdict absent ou hors vocabulaire", sortie)

    def test_unverifiable_sans_raison_est_refuse(self):
        # Panne : « unverifiable » sans raison après le tiret passe pour une non-preuve motivée.
        for verdict in ("- **Verdict** : unverifiable", "- **Verdict** : unverifiable —"):
            with self.subTest(verdict=verdict):
                p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
                    entree("1"), entree("2", remplace={"Verdict": verdict}), entree("3")))
                code, sortie, _ = jouer(p, "--apres")
                self.assertEqual(code, 1, sortie)
                self.assertIn("Étape 2 : unverifiable sans raison", sortie)

    def test_unverifiable_avec_raison_rend_trois_et_la_ligne_non_prouvee(self):
        # Panne : une étape non vérifiable avec sa raison est refusée au lieu d'être signalée.
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
            entree("1"),
            entree("2", remplace={"Verdict": "- **Verdict** : unverifiable — pas de moyen de rejouer ici"}),
            entree("3")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 3, sortie)
        self.assertIn("non prouvée : Étape 2 — pas de moyen de rejouer ici", sortie)
        self.assertNotIn("Étape 1", sortie)
        self.assertNotIn("Étape 3", sortie)

    def test_defaut_et_unverifiable_rendent_un_les_defauts_d_abord(self):
        # Panne : un défaut et une non-preuve dans le même plan rendent 3 au lieu de 1,
        # ou sortent dans le mauvais ordre.
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
            entree("1"),
            entree("2", remplace={"Verdict": "- **Verdict** : unverifiable — trop long à rejouer"}),
            entree("3", sans=("Preuve",))))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 1, sortie)
        lignes = sortie.splitlines()
        defaut = next(i for i, l in enumerate(lignes) if "Étape 3 : pas de Preuve" in l)
        non_prouvee = next(i for i, l in enumerate(lignes) if "non prouvée : Étape 2" in l)
        self.assertLess(defaut, non_prouvee, sortie)

    def test_page_sans_journal_rend_deux(self):
        # Panne : une page sans « Journal d'exécution » passe pour un journal vide et conforme.
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1"))
        code, sortie, erreur = jouer(p, "--apres")
        self.assertEqual(code, 2, erreur)
        self.assertIn("Journal", erreur)

    # Test en plus, hors liste du brief : un titre « ### Ouverture » ou « ### État final »
    # du journal, qui n'est pas une étape, ne doit pas absorber la ligne « Commit » qui le
    # suit. Panne attrapée : le bloc de l'étape 2 s'étend jusqu'à « État final » et y
    # trouve un commit, donc la porte passe à tort.
    def test_titres_hors_etape_du_journal_ne_comptent_pas(self):
        texte = (ENTETE + chapitre_ok("1", "2")
                 + "## Journal d'exécution\n\n### Ouverture\n\n- **Commit** : `aaaaaaa`\n\n"
                 + entree("1") + entree("2", sans=("Commit",))
                 + "### État final\n\n- **Commit** : `ccccccc`\n- **Verdict** : verified\n")
        p = self.ecrire("p.md", texte)
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 1, sortie)
        self.assertEqual(sortie.strip(), "Étape 2 : pas de Commit")

    # Test en plus, hors liste du brief : deux entrées de journal pour une même étape
    # (décision du script, non prévue par le brief). Panne : la seconde entrée, vide ou
    # périmée, passe inaperçue derrière la première.
    def test_entree_de_journal_en_double_est_refusee(self):
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2", "3") + journal(
            entree("1"), entree("1", sans=("Preuve",)), entree("2"), entree("3")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 1, sortie)
        self.assertIn("Étape 1 : deux entrées de journal", sortie)

    # Test en plus, hors liste du brief : les deux formes que le brief admet pour le
    # commit (clé après un point, pluriel « Commits »). Panne : une seule forme lue passe
    # pour « pas de Commit » sur une entrée pourtant conforme.
    def test_commit_apres_un_point_et_au_pluriel_sont_lus(self):
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2") + journal(
            entree("1", remplace={"Commit": "- **Modèle** : claude-haiku-5-5. **Commits** : `abc1234`, `def5678`"}),
            entree("2")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 0, sortie)
        self.assertIn("toutes verified", sortie)

    # Panne : le champ « **Commit(s)** » n'est pas lu (le « (s) » sépare le mot du « ** »
    # fermant), donc une entrée conforme passe pour « pas de Commit », et le code 3 (étape
    # non prouvée) n'est jamais atteint pour elle.
    def test_commit_avec_parentheses_s_est_lu(self):
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2") + journal(
            entree("1", remplace={
                "Commit": "- **Commit(s)** : `abc1234`. **Modèle** : claude-haiku-5-5",
                "Verdict": "- **Verdict** : unverifiable — pas de moyen de rejouer ici"}),
            entree("2")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 3, sortie)
        self.assertIn("non prouvée : Étape 1 — pas de moyen de rejouer ici", sortie)

    # Panne : « Preuve » rempli d'une coquille (tiret, « aucune », « à voir ») passe la porte
    # d'après, comme une preuve rejouée.
    def test_preuve_coquille_au_journal_est_refusee(self):
        for coquille in ("—", "-", "aucune", "à voir"):
            with self.subTest(coquille=coquille):
                p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2") + journal(
                    entree("1", remplace={"Preuve": f"- **Preuve** (rejouée par le pilote) : {coquille}"}),
                    entree("2")))
                code, sortie, _ = jouer(p, "--apres")
                self.assertEqual(code, 1, sortie)
                self.assertIn("Étape 1 : pas de Preuve", sortie)

    # Panne : « Commit » rempli d'un tiret seul passe la porte d'après, et l'étape paraît
    # livrée sans trace de commit.
    def test_commit_tiret_seul_est_refuse(self):
        for coquille in ("—", "-"):
            with self.subTest(coquille=coquille):
                p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2") + journal(
                    entree("1", remplace={"Commit": f"- **Commit** : {coquille}"}),
                    entree("2")))
                code, sortie, _ = jouer(p, "--apres")
                self.assertEqual(code, 1, sortie)
                self.assertIn("Étape 1 : pas de Commit", sortie)

    # Panne : « Découvertes » rempli d'un tiret seul passe la porte d'après.
    def test_decouvertes_tiret_seul_est_refuse(self):
        for coquille in ("—", "-"):
            with self.subTest(coquille=coquille):
                p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2") + journal(
                    entree("1", remplace={"Découvertes": f"- **Découvertes** : {coquille}"}),
                    entree("2")))
                code, sortie, _ = jouer(p, "--apres")
                self.assertEqual(code, 1, sortie)
                self.assertIn("Étape 1 : pas de Découvertes", sortie)

    # Garde contre une correction trop large : « Découvertes : aucune » est la valeur que le
    # SKILL écrit quand il n'y a rien à signaler. Panne : un correctif qui réutilise la liste
    # de « Preuve » (où « aucune » est une coquille) la refuserait à tort.
    def test_decouvertes_aucune_est_acceptee(self):
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2") + journal(
            entree("1", remplace={"Découvertes": "- **Découvertes** : aucune"}),
            entree("2")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 0, sortie)
        self.assertIn("toutes verified", sortie)

    # Garde contre une correction trop large : « Commit : aucun (lecture seule) » est une
    # étape sans fichier, légitime. Panne : « aucun » traité comme une coquille, et une étape
    # de lecture seule refusée à tort.
    def test_commit_aucun_pour_une_etape_sans_fichier_est_accepte(self):
        p = self.ecrire("p.md", ENTETE + chapitre_ok("1", "2") + journal(
            entree("1", remplace={"Commit": "- **Commit** : aucun (lecture seule)"}),
            entree("2")))
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 0, sortie)
        self.assertIn("toutes verified", sortie)

    # Test en plus, hors liste du brief : les deux modes sont exclusifs et l'un des deux est
    # obligatoire (argparse). Panne : un mode est choisi en silence, l'autre ignoré.
    def test_avant_et_apres_exclusifs_ou_aucun_rendent_deux(self):
        p = self.ecrire("p.md", page_ok())
        code, _, erreur = jouer(p, "--avant", "--apres")
        self.assertEqual(code, 2, erreur)
        self.assertIn("not allowed", erreur)
        code, _, erreur = jouer(p)
        self.assertEqual(code, 2, erreur)
        self.assertIn("required", erreur)

    # Test en plus, hors liste du brief : page illisible (fichier absent) rend 2, comme les
    # autres pannes d'entrée. Panne : un fichier absent passe pour une page vide et conforme.
    def test_page_illisible_rend_deux(self):
        code, _, erreur = jouer(self.dossier / "absent.md", "--apres")
        self.assertEqual(code, 2, erreur)
        self.assertIn("illisible", erreur)


class FormatReel(_Dossier):
    # Non-régression sur un vrai format : une page fabriquée comme celle d'un plan, avec
    # une puce « Preuve de fin » indentée par tabulation, une entrée qui porte
    # « Preuve (rejouée par le pilote) » et une ligne « Commit » suivie de « Modèle ».
    # Panne : un changement de format qui casse la lecture d'une page réelle.
    def test_format_reel_de_la_page_passe_les_deux_portes(self):
        page = (
            "# Plan réel\n\n## Cartes\n\n- une carte\n\n"
            "## Exécution\n\n"
            "Coût estimé : exécution seule.\n\n"
            "### Étape 1 — Les dépôts suivis\n"
            "- **Choix d'architecture** :\n"
            "\t- `config/docs-veille.json` (créé) : une entrée par dépôt.\n"
            "- **Preuve de fin** : `~/.hermes/hermes-agent/venv/bin/python -m pytest -q tests/test_docs_veille.py -p no:cacheprovider` → tout vert.\n\n"
            "### Étape D1 — Les descriptions du job\n"
            "\t- **Preuve de fin** : `grep -c 'Recos' cron/docs-veille.md` → au moins 1.\n\n"
            "## Journal d'exécution\n"
            "Se remplit à l'implémentation.\n"
            "### Ouverture\n"
            "- **Date** : 2026-10-14. **Pilote** : Sonnet 5.5, medium.\n"
            "### Étape 1 — Les dépôts suivis\n"
            "- **Fait** : `config/docs-veille.json` créé.\n"
            "- **Preuve** (rejouée par le pilote) : rouge `845c2b1`, vert `a97b3a2` → 24 passés.\n"
            "- **Commit** : `845c2b1` (rouge), `a97b3a2` (vert). **Modèle** : `a674232212f02b3c1` → `claude-haiku-5-5`.\n"
            "- **Découvertes** : (a) découverte — trouvable au plan.\n"
            "- **Verdict** : verified\n"
            "### Étape D1 — Les descriptions du job\n"
            "- **Preuve** (rejouée par le pilote) : `grep -c 'Recos' cron/docs-veille.md` → 3.\n"
            "- **Commits** : `1a0bd2d`.\n"
            "- **Découvertes** : aucune.\n"
            "- **Verdict** : verified — rejoué sur le commit vert.\n"
            "### État final\n"
            "- **Verdict** : verified\n\n"
            "## Commentaires repris\n\nAucun pour l'instant.\n"
        )
        p = self.ecrire("p.md", page)
        code, sortie, _ = jouer(p, "--avant")
        self.assertEqual(code, 0, sortie)
        self.assertIn("avant : 2 étape(s)", sortie)
        code, sortie, _ = jouer(p, "--apres")
        self.assertEqual(code, 0, sortie)
        self.assertIn("toutes verified", sortie)


if __name__ == "__main__":
    unittest.main()
