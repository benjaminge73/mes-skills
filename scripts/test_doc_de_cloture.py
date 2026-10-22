"""Tests de ``doc-de-cloture.py`` sur des fixtures écrites ici, dans un dossier temporaire.

Le script a deux usages : la porte de clôture (``--porte``) et le rattrapage des trous
(``--trous``). Chaque test pose ses fixtures (une page de plan, un miroir du Changelog,
un JSON de ``gh pr list``), joue le script comme le ferait la clôture, et compare le code
de retour et la sortie à ce que disent les règles. Les attendus sont écrits à la main
d'après ces règles, pas d'après le code.

Règle centrale : une PR n'est documentée que si son numéro figure dans l'en-tête d'une
entrée du Changelog (H2 daté ou « Récap », puis la ligne ``Plan :`` juste après). Une PR
citée ailleurs (toggle « Côté technique », phrase du corps) reste un trou.

Pannes, une par test :
  1. Une page sans H2 « Récap » rend 1 par ``--porte``, et la sortie nomme le Récap.
  2. Une PR citée seulement dans le bloc ``<toggle>Côté technique`` est un trou (cas #258).
  3. Une PR citée seulement dans une phrase d'absence du corps est un trou.
  4. Une ligne ``Plan :`` avec un lien ``pull/N`` sous un H2 daté documente la PR.
  5a. ``--trous`` exclut les PR de dépendances (auteur ``app/dependabot``, label ``dependencies``).
  5b. ``--trous`` exclut les PR mergées avant ``--depuis``, et garde celles du jour même.
Extras, chacun pour une panne que les cinq ci-dessus ne couvrent pas :
  6. ``--lot`` dispense de l'entrée, pas du Récap.
  7. ``--recap-fichier`` (palier 3) est accepté s'il existe avec un H2 Récap ; absent, il ne
     vaut pas d'exception.
  8. ``--sauf`` retire le numéro donné de la liste.
  9. Une plage « #258 à #260 » documente chaque numéro qu'elle contient, et pas le suivant.
  10. La frontière de mot : « #258 » ne documente pas « #25 ».
  11. « Récap » en minuscules passe la porte (casse indifférente).
  12a. Fichier absent : code 2, le nom du fichier sur la sortie d'erreur.
  12b. JSON invalide : code 2, le nom du fichier sur la sortie d'erreur.
  12c. ``--changelog`` sans ``--pr`` (et l'inverse) : code 2, l'option manquante nommée.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "doc-de-cloture.py"

PAGE_AVEC_RECAP = (
    "# Plan exemple\n\n## Exécution\n\nDu texte.\n\n"
    "## Récap · 2026-10-20 · Plan exemple\n"
    "Plan : lien · PR : #12 · Statut : a merger\n\n"
    "### ✨ Nouveau\n- Le pilote écrit le récap (Étape 2)\n\n"
)
PAGE_SANS_RECAP = "# Plan exemple\n\n## Exécution\n\nDu texte.\n"


def entree(date="2026-10-20", ligne_plan="Plan : lien · PR : #12 · Statut : a merger", corps=""):
    """Une entrée du Changelog : H2 daté, ligne Plan, une rubrique, puis le corps donné."""
    return (
        f"## {date} · Plan exemple\n{ligne_plan}\n\n"
        "### ✨ Nouveau\n- Une ligne (Étape 1)\n\n"
        + corps
    )


def changelog(*entrees):
    return "# Changelog\n\n" + "\n".join(entrees)


def pr(numero, merge="2026-10-15", auteur="benjaminge73", labels=()):
    """Une entrée de ``gh pr list --json number,title,mergedAt,author,labels``."""
    return {
        "number": numero,
        "title": f"Titre de la PR {numero}",
        "mergedAt": f"{merge}T10:00:00Z",
        "author": {"login": auteur},
        "labels": [{"name": nom} for nom in labels],
    }


def jouer(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def lignes(sortie):
    return [ligne for ligne in sortie.splitlines() if ligne.strip()]


def numeros(sortie):
    """Le numéro (``#N``) de chaque ligne de sortie, dans l'ordre où le script les rend."""
    return [ligne.split(" ")[0] for ligne in lignes(sortie)]


class DocDeCloture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def ecrire(self, nom, texte):
        f = self.dossier / nom
        f.write_text(texte, encoding="utf-8")
        return f

    def fichier_prs(self, *prs):
        return self.ecrire("prs.json", json.dumps(list(prs)))

    def trous(self, texte_changelog, prs, *extra):
        c = self.ecrire("changelog.md", texte_changelog)
        return jouer("--trous", "--changelog", c, "--prs", self.fichier_prs(*prs),
                     "--depuis", "2026-10-01", *extra)

    # Panne 1 : une page sans « Récap » passerait la porte.
    def test_page_sans_recap_rend_un_et_nomme_le_recap(self):
        page = self.ecrire("page.md", PAGE_SANS_RECAP)
        code, sortie, erreur = jouer("--porte", page)
        self.assertEqual(code, 1, erreur)
        self.assertIn("Récap", sortie)

    # Panne 2 : le toggle « Côté technique » compterait comme en-tête (cas réel #258).
    def test_pr_citee_seulement_dans_le_toggle_cote_technique_est_un_trou(self):
        toggle = (
            "<toggle>Côté technique\n\n"
            "\tLe correctif de la PR #258 touche le script.\n"
            "</toggle>\n"
        )
        code, sortie, erreur = self.trous(changelog(entree(corps=toggle)), [pr(258)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#258"], sortie)

    # Panne 3 : une phrase du corps qui cite un numéro n'est pas un en-tête.
    def test_pr_citee_seulement_dans_une_phrase_d_absence_est_un_trou(self):
        corps = "### 🐛 Corrigé\nLa PR #258 n'a pas d'entrée dans ce Changelog.\n\n"
        code, sortie, erreur = self.trous(changelog(entree(corps=corps)), [pr(258)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#258"], sortie)

    # Panne 4 : le lien « pull/N » de la ligne Plan ne serait pas reconnu.
    def test_ligne_plan_avec_url_pull_documente_la_pr(self):
        texte = changelog(entree(
            ligne_plan="Plan : lien · PR : https://github.com/o/r/pull/261 · Statut : a merger"))
        code, sortie, erreur = self.trous(texte, [pr(261)])
        self.assertEqual((code, sortie), (0, ""), erreur)
        page = self.ecrire("page.md", PAGE_AVEC_RECAP)
        code, sortie, erreur = jouer("--porte", page, "--changelog",
                                     self.ecrire("changelog.md", texte), "--pr", 261)
        self.assertEqual((code, sortie), (0, ""), erreur)

    # Panne 5a : une PR de dépendances compterait comme trou. La PR 302, sans rapport, reste
    # listée : c'est le témoin qui montre que la liste n'est pas vide par défaut.
    def test_trous_exclut_les_pr_de_dependances(self):
        prs = [pr(300, auteur="app/dependabot"), pr(301, labels=["dependencies"]), pr(302)]
        code, sortie, erreur = self.trous(changelog(entree()), prs)
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#302"], sortie)

    # Panne 5b : une PR mergée avant --depuis compterait comme trou, ou la borne serait
    # exclusive (la PR mergée le jour même disparaîtrait).
    def test_trous_exclut_les_pr_mergees_avant_depuis(self):
        prs = [pr(280, merge="2026-09-30"), pr(281, merge="2026-10-01")]
        code, sortie, erreur = self.trous(changelog(entree()), prs)
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#281"], sortie)

    # Extra 6 : --lot dispense de l'entrée, pas du Récap.
    def test_lot_dispense_l_entree_mais_pas_le_recap(self):
        c = self.ecrire("changelog.md", changelog(entree()))
        page_nue = self.ecrire("nue.md", PAGE_SANS_RECAP)
        code, sortie, erreur = jouer("--porte", page_nue, "--changelog", c, "--pr", 999, "--lot")
        self.assertEqual(code, 1, erreur)
        self.assertIn("Récap", sortie)
        self.assertNotIn("999", sortie)
        page = self.ecrire("page.md", PAGE_AVEC_RECAP)
        code, sortie, erreur = jouer("--porte", page, "--changelog", c, "--pr", 999, "--lot")
        self.assertEqual((code, sortie), (0, ""), erreur)

    # Extra 7 : le palier 3 (Récap dans un fichier confié à Hermes) n'est une exception que
    # si le fichier existe et porte un H2 Récap.
    def test_recap_fichier_existant_tient_lieu_de_recap(self):
        page = self.ecrire("nue.md", PAGE_SANS_RECAP)
        recap = self.ecrire("recap.md", "## Récap · 2026-10-20 · Plan exemple\nPlan : lien\n\n"
                                        "### ✨ Nouveau\n- rien\n")
        code, sortie, erreur = jouer("--porte", page, "--recap-fichier", recap)
        self.assertEqual((code, sortie), (0, ""), erreur)
        code, sortie, erreur = jouer("--porte", page, "--recap-fichier",
                                     self.dossier / "absent-recap.md")
        self.assertEqual(code, 1, erreur)

    # Extra 8 : --sauf retire le numéro donné ; le 259, non cité, reste listé.
    def test_sauf_retire_les_numeros_donnes(self):
        code, sortie, erreur = self.trous(changelog(entree()), [pr(258), pr(259)], "--sauf", "258")
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#259"], sortie)

    # Extra 9 : une plage documente chaque numéro inclus, pas le suivant.
    def test_plage_documente_chaque_numero_inclus(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #258 à #260 · Statut : a merger"))
        prs = [pr(n) for n in (258, 259, 260, 261)]
        code, sortie, erreur = self.trous(texte, prs)
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#261"], sortie)

    # Extra 9b : la borne B d'une plage s'écrit parfois sans son « # » (« #258 à 260 »). Panne :
    # seule la borne A serait lue, et 259 et 260 resteraient des trous alors qu'elles ont leur
    # entrée. Attendu : 258 à 260 documentées, 261 (hors plage) listée seule.
    def test_plage_dont_la_borne_b_n_a_pas_de_diese_documente_chaque_numero(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #258 à 260 · Statut : a merger"))
        prs = [pr(n) for n in (258, 259, 260, 261)]
        code, sortie, erreur = self.trous(texte, prs)
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#261"], sortie)

    # Extra 10 : une recherche de sous-chaîne prendrait « #25 » dans « #258 ».
    def test_frontiere_de_mot_25_n_est_pas_couvert_par_258(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #258 · Statut : a merger"))
        code, sortie, erreur = self.trous(texte, [pr(25), pr(258)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#25"], sortie)

    # Extra 11 : « Récap » reconnu seulement avec sa majuscule rendrait 1 ici.
    def test_recap_en_minuscules_passe_la_porte(self):
        page = self.ecrire("page.md", "# Plan\n\n## récap · 2026-10-20 · Plan exemple\n\nTexte.\n")
        code, sortie, erreur = jouer("--porte", page)
        self.assertEqual((code, sortie), (0, ""), erreur)

    # Extra 12a : un fichier absent doit sortir en code 2, le nom du fichier sur stderr.
    def test_fichier_absent_rend_deux_et_le_nomme(self):
        code, sortie, erreur = jouer("--porte", self.dossier / "absent.md")
        self.assertEqual(code, 2, sortie)
        self.assertEqual(sortie, "")
        self.assertIn("absent.md", erreur)

    # Extra 12b : un JSON invalide doit sortir en code 2, le nom du fichier sur stderr.
    def test_json_invalide_rend_deux_et_nomme_le_fichier(self):
        prs = self.ecrire("prs-casse.json", '[{"number": 258,')
        c = self.ecrire("changelog.md", changelog(entree()))
        code, sortie, erreur = jouer("--trous", "--changelog", c, "--prs", prs, "--depuis", "2026-10-01")
        self.assertEqual(code, 2, sortie)
        self.assertIn("prs-casse.json", erreur)

    # Extra 12c : --changelog et --pr vont ensemble, dans les deux sens.
    def test_changelog_et_pr_vont_ensemble(self):
        page = self.ecrire("page.md", PAGE_AVEC_RECAP)
        c = self.ecrire("changelog.md", changelog(entree()))
        code, sortie, erreur = jouer("--porte", page, "--changelog", c)
        self.assertEqual(code, 2, sortie)
        self.assertIn("--pr", erreur)
        code, sortie, erreur = jouer("--porte", page, "--pr", 12)
        self.assertEqual(code, 2, sortie)
        self.assertIn("--changelog", erreur)


if __name__ == "__main__":
    unittest.main()
