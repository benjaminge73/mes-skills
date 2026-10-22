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
Tests ajoutés après la relecture de l'étape 3 :
  13a. Un numéro nu dans le titre H2 (« (#282) ») ne documente pas la PR ; la PR de la ligne Plan
       reste documentée.
  13b. Un numéro du titre du plan (« Vahiny - Thaïlande #4 ») ne documente pas la PR 4.
  13c. Le lien du plan sur la ligne Plan (« [Plan … #2 - 3e passe](url) ») ne documente ni 2 ni
       3 : seul le segment qui suit « PR : » compte.
  13d. Garde de non-régression (vert avant le correctif) : « (PR #258) » dans le titre H2
       documente 258. La forme non ambiguë reste lue.
  14a. Un Récap cité dans un bloc de code de la page ne rend pas la porte conforme.
  14b. Une entrée datée citée dans un bloc de code du Changelog ne documente pas sa PR.
  15a. Palier 3 de l'entrée du hub : ``--hub-fichier`` est lu comme source d'en-têtes.
  15b. ``--hub-fichier`` sans ``--pr`` : code 2, ``--pr`` nommé.
Tests ajoutés aux relectures 2 et 3 :
  16a/16b. Un numéro cité dans le titre H2 hors de la forme finale « (PR #N) » ne documente rien.
  17. « (voir PR 190) » dans le segment qui suit « PR : » ne documente pas la PR 190.
  18a. « #284 – 2e tentative » : le « 2 » n'est pas une borne B sans dièse (seul « à » l'admet).
  18b. Une plage inversée (« #260 à #258 ») ne documente rien, ni ses bornes.
  18c. Garde, vert avant le correctif : « #258 à 260 » documente 258, 259 et 260.
  18d. « #258–260 » : une borne B sans dièse n'existe qu'avec « à » ; seule 258 est documentée.
  18e. Titre H2 « (PR 150) » sans dièse : la PR 150 reste un trou.
  18f. Plage de plus de 50 numéros (« #100 à #151 ») : ignorée, ses bornes ne comptent pas.
  18g. Garde, vert avant le correctif : une plage de 50 d'écart (« #100 à #150 ») reste acceptée.
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


def entree(date="2026-10-20", ligne_plan="Plan : lien · PR : #12 · Statut : a merger", corps="",
           titre="Plan exemple"):
    """Une entrée du Changelog : H2 daté, ligne Plan, une rubrique, puis le corps donné."""
    return (
        f"## {date} · {titre}\n{ligne_plan}\n\n"
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

    # Panne 13a : un numéro nu dans le titre H2 (« (#282) ») compterait comme documenté.
    # Attendu : dans le titre, seules les formes non ambiguës comptent (PR #N, PR N, pull/N).
    # La PR 290, sur la ligne Plan, est documentée ; la 282 reste un trou.
    def test_numero_nu_dans_le_titre_h2_ne_documente_pas_la_pr(self):
        texte = changelog(entree(
            titre="Hors plan — Revert « Fixer le socle » (#282)",
            ligne_plan="Plan : aucun (hors plan) · PR : https://github.com/o/r/pull/290 · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(282), pr(290)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#282"], sortie)

    # Panne 13b : le numéro du titre du plan (« Vahiny - Thaïlande #4 ») documenterait la PR 4.
    # Attendu : la PR 4 reste un trou ; la PR 12, citée sur la ligne Plan, est documentée.
    def test_numero_du_titre_de_plan_ne_documente_pas_la_pr(self):
        texte = changelog(entree(titre="Vahiny - Thaïlande #4"))
        code, sortie, erreur = self.trous(texte, [pr(4), pr(12)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#4"], sortie)

    # Panne 13c : le lien du plan sur la ligne Plan (« [Plan … #2 - 3e passe](url) ») : la plage
    # « #2 - 3 » documenterait 2 et 3. Attendu : seul le segment qui suit « PR : » compte.
    def test_lien_du_plan_sur_la_ligne_plan_ne_documente_pas_ses_numeros(self):
        texte = changelog(entree(ligne_plan=(
            "Plan : [Plan Vahiny #2 - 3e passe](https://www.notion.so/exemple) · PR : #12 · Statut : a merger")))
        code, sortie, erreur = self.trous(texte, [pr(2), pr(3), pr(12)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#2", "#3"], sortie)

    # Panne 13d, garde de non-régression (vert avant le correctif) : « (PR #258) » dans le titre
    # H2 doit documenter 258. La forme non ambiguë reste lue une fois la règle resserrée.
    def test_pr_dans_le_titre_h2_avec_forme_non_ambigue_documente_la_pr(self):
        texte = changelog(entree(
            titre="Hors plan — Titre de la PR (PR #258)",
            ligne_plan="Plan : aucun (hors plan) · PR : https://github.com/o/r · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(258)])
        self.assertEqual((code, sortie), (0, ""), erreur)

    # Panne 14a : un Récap cité dans un bloc de code (« ``` ») passerait la porte. Attendu : le
    # contenu d'un bloc de code n'est pas une section de la page ; code 1, Récap nommé.
    def test_recap_cite_dans_un_bloc_de_code_ne_compte_pas(self):
        page = self.ecrire("page.md", "# Plan exemple\n\n## Exécution\n\n"
                           "```markdown\n## Récap · 2026-10-20 · Plan exemple\nPlan : lien\n```\n")
        code, sortie, erreur = jouer("--porte", page)
        self.assertEqual(code, 1, erreur)
        self.assertIn("Récap", sortie)

    # Panne 14b : une entrée datée citée dans un bloc de code du Changelog documenterait sa PR.
    # Attendu : la PR 258 n'est pas documentée par l'exemple, et reste un trou.
    def test_entree_citee_dans_un_bloc_de_code_ne_documente_pas_la_pr(self):
        exemple = "```\n## 2026-10-20 · Exemple\nPlan : lien · PR : #258 · Statut : a merger\n```\n"
        code, sortie, erreur = self.trous(changelog(entree(), exemple), [pr(258)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#258"], sortie)

    # Panne 15a : le palier 3 de l'entrée du hub. Sans --hub-fichier, la PR 290 n'est dans aucun
    # en-tête lu (miroir vide) : code 1. Avec --hub-fichier (entrée confiée à Hermes), elle l'est.
    def test_hub_fichier_tient_lieu_d_entree_au_palier_trois(self):
        page = self.ecrire("nue.md", PAGE_SANS_RECAP)
        recap = self.ecrire("recap.md", "## Récap · 2026-10-20 · Plan exemple\nPlan : lien\n\n"
                                        "### ✨ Nouveau\n- rien\n")
        vide = self.ecrire("cl-vide.md", "# Changelog\n")
        hub = self.ecrire("hub.md", entree(
            ligne_plan="Plan : lien · PR : https://github.com/o/r/pull/290 · Statut : a merger"))
        code, sortie, erreur = jouer("--porte", page, "--recap-fichier", recap, "--changelog", vide,
                                     "--pr", 290, "--hub-fichier", hub)
        self.assertEqual((code, sortie), (0, ""), erreur)
        code, sortie, erreur = jouer("--porte", page, "--recap-fichier", recap, "--changelog", vide,
                                     "--pr", 290)
        self.assertEqual(code, 1, erreur)
        self.assertIn("PR #290", sortie)

    # Panne 15b : --hub-fichier sans --pr n'a rien à contrôler : usage erroné, code 2, et le
    # message du script nomme la règle. Le texte d'usage d'argparse contient « --pr N » : une
    # assertion sur « --pr » seul passerait au rouge. On exige donc la phrase du script.
    def test_hub_fichier_sans_pr_rend_deux(self):
        page = self.ecrire("page.md", PAGE_AVEC_RECAP)
        hub = self.ecrire("hub.md", entree())
        code, sortie, erreur = jouer("--porte", page, "--hub-fichier", hub)
        self.assertEqual(code, 2, sortie)
        self.assertIn("--hub-fichier exige --pr N", erreur)

    # Panne 16a : un titre « Hors plan » recopie le titre de la PR, qui peut citer d'autres PR
    # (« … ce que la PR #190 a fait … », « … PR 2 (etapes 8-22) … »). Ces numéros ne documentent
    # rien : seule la forme finale « (PR #N) » en fin de titre compte. Attendu : 190 et 2 restent
    # des trous ; 224 et 250 sont documentées par leur forme finale (et par leur ligne Plan).
    def test_pr_citee_dans_le_titre_d_une_entree_ne_documente_pas_ces_pr(self):
        texte = changelog(
            entree(date="2026-10-21",
                   titre="Hors plan — Corriger ce que la PR #190 a fait en amont (PR #224)",
                   ligne_plan="Plan : aucun (hors plan) · PR : https://github.com/o/r/pull/224 · Statut : mergée"),
            entree(date="2026-10-21",
                   titre="Hors plan — Migration, voir PR 2 (etapes 8-22) (PR #250)",
                   ligne_plan="Plan : aucun (hors plan) · PR : https://github.com/o/r/pull/250 · Statut : mergée"),
        )
        code, sortie, erreur = self.trous(texte, [pr(2), pr(190), pr(224), pr(250)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#2", "#190"], sortie)

    # Panne 16b : le même texte, côté porte. --pr 190 (cité dans un titre seulement) doit rendre
    # 1 ; --pr 224 (forme finale « (PR #224) » dans le titre) doit rendre 0.
    def test_porte_pr_citee_dans_le_titre_seulement_n_est_pas_documentee(self):
        texte = changelog(
            entree(date="2026-10-21",
                   titre="Hors plan — Corriger ce que la PR #190 a fait en amont (PR #224)",
                   ligne_plan="Plan : aucun (hors plan) · PR : https://github.com/o/r · Statut : mergée"))
        page = self.ecrire("page.md", PAGE_AVEC_RECAP)
        c = self.ecrire("changelog.md", texte)
        code, sortie, erreur = jouer("--porte", page, "--changelog", c, "--pr", 190)
        self.assertEqual(code, 1, erreur)
        self.assertIn("PR #190", sortie)
        code, sortie, erreur = jouer("--porte", page, "--changelog", c, "--pr", 224)
        self.assertEqual((code, sortie), (0, ""), erreur)

    # Panne 17 : le segment qui suit « PR : » lit « PR N » en prose, et « (voir PR 190) » documente
    # alors la PR 190. Attendu : seuls « #N », « pull/N » et les plages comptent ; la PR 12, citée
    # par « #12 », est documentée ; la PR 190, citée en prose, reste un trou.
    def test_pr_citee_en_prose_dans_le_segment_pr_ne_documente_pas_la_pr(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #12 (voir PR 190) · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(12), pr(190)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#190"], sortie)

    # Panne 18a : « #284 – 2e tentative » lisait « 2 » comme borne B de la plage 2–284, et
    # documentait les PR 3 et 100. Seul « à » admet une borne B sans dièse. Attendu : seule 284.
    def test_tiret_suivi_de_2e_ne_fait_pas_une_plage_avec_borne_sans_diese(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #284 – 2e tentative · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(3), pr(100), pr(284), pr(285)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#3", "#100", "#285"], sortie)

    # Panne 18b : une plage inversée (« #260 à #258 ») est lue comme « de 258 à 260 ». Attendu :
    # elle ne compte pas du tout, ni ses bornes : 258, 259 et 260 restent des trous.
    def test_plage_inversee_ne_documente_rien(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #260 à #258 · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(258), pr(259), pr(260)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#258", "#259", "#260"], sortie)

    # Garde 18c (vert avant le correctif) : « à » avec une borne B sans dièse reste une plage.
    def test_plage_a_avec_borne_b_sans_diese_documente_chaque_numero(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #258 à 260 · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(258), pr(259), pr(260), pr(261)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#261"], sortie)

    # Panne 18d : « #258–260 » lisait « 260 » comme borne B, et documentait 259 et 260. Attendu :
    # seule la borne A, qui porte son dièse, est documentée.
    def test_plage_a_tiret_avec_borne_b_sans_diese_ne_documente_que_a(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #258–260 · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(258), pr(259), pr(260)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#259", "#260"], sortie)

    # Panne 18e : le titre H2 « (PR 150) », sans dièse, documentait la PR 150. Seule la forme
    # finale « (PR #N) » compte. Attendu : la 150 reste un trou.
    def test_titre_avec_pr_sans_diese_ne_documente_pas_la_pr(self):
        texte = changelog(entree(titre="Vahiny - Autre passe (PR 150)",
                                 ligne_plan="Plan : [lien](u) · PR : aucune (plan natif)"))
        code, sortie, erreur = self.trous(texte, [pr(150)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#150"], sortie)

    # Panne 18f : une plage de plus de 50 numéros (« #100 à #151 », écart 51) est suspecte ;
    # elle est ignorée, ses bornes comprises.
    def test_plage_trop_large_est_ignoree(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #100 à #151 · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(100), pr(151)])
        self.assertEqual(code, 1, erreur)
        self.assertEqual(numeros(sortie), ["#100", "#151"], sortie)

    # Garde 18g (vert avant le correctif) : un écart de 50 (« #100 à #150 ») reste accepté.
    def test_plage_d_ecart_cinquante_reste_acceptee(self):
        texte = changelog(entree(ligne_plan="Plan : lien · PR : #100 à #150 · Statut : mergée"))
        code, sortie, erreur = self.trous(texte, [pr(100), pr(150)])
        self.assertEqual((code, sortie), (0, ""), erreur)


if __name__ == "__main__":
    unittest.main()
