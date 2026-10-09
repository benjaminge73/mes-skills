"""Tests de ``vagues.py`` sur le tableau figé du plan « Évals sobres ».

Les attendus viennent de la règle de ``_partage/vagues.md`` (fichiers
disjoints, aucune dépendance entre les deux étapes, aucun fichier partagé touché
par les deux), appliquée à la main sur la fixture — pas de la colonne « Vague »
seule. Sur ce tableau, la colonne est cohérente avec la règle pour les étapes
1 à 7 et 13 ; elle ne l'est pas partout (étape 8 regroupée avec la 7 :
la règle les sépare puisque 8 dépend de 7 ; vagues « L2·n » et « 7 (avant 15) »
qui ne sont pas des numéros), et ces lignes sont signalées par ``--comparer``,
pas forcées.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "vagues.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures_plans" / "tableau_execution.html"


def jouer(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def tableau(*lignes):
    """Un tableau Notion minimal : (étape, fichiers, dépend de, vague)."""
    html = ['<table header-row="true">', "<tr>", *(f"<td>{c}</td>" for c in
            ("Étape", "Fichiers touchés", "Dépend de", "Vague", "Relecture")), "</tr>"]
    for etape, fichiers, dep, vague in lignes:
        html += ["<tr>", f"<td>{etape}</td>", f"<td>{fichiers}</td>", f"<td>{dep}</td>",
                 f"<td>{vague}</td>", "<td>étape</td>", "</tr>"]
    html.append("</table>")
    return "\n".join(html)


def vagues_de(sortie):
    """``{étape: n° de vague}`` lu sur les lignes « Vague n : a, b »."""
    res = {}
    for ligne in sortie.splitlines():
        if ligne.startswith("Vague "):
            tete, _, etapes = ligne.partition(":")
            for e in etapes.split(","):
                res[e.strip()] = int(tete.split()[1])
    return res


class Vagues(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def _page(self, contenu):
        f = self.dossier / "page.md"
        f.write_text(contenu)
        return f

    def test_tableau_du_plan_donne_les_vagues_de_la_colonne_la_ou_elle_est_coherente(self):
        code, sortie, _ = jouer(FIXTURE)
        self.assertEqual(code, 0, sortie)
        v = vagues_de(sortie)
        # La chaîne 1 → 2 → 3 → 4 : dépendances déclarées, et ci.yml partagé.
        self.assertEqual([v["1"], v["2"], v["3"], v["4"]], [1, 2, 3, 4])
        # Fichiers disjoints, dépendances seulement vers des questions : même vague que 1.
        self.assertEqual([v["5"], v["6"], v["7"], v["13"]], [1, 1, 1, 1])

    def test_etape_regroupee_dependant_d_une_autre_est_separee_par_la_regle(self):
        # 8 dépend de 7 (et touche les mêmes fichiers) : la règle ne les met pas ensemble,
        # alors que la colonne du plan les regroupe en vague 1.
        _, sortie, _ = jouer(FIXTURE)
        v = vagues_de(sortie)
        self.assertGreater(v["8"], v["7"])

    def test_comparer_signale_les_ecarts_avec_la_colonne_vague(self):
        code, sortie, _ = jouer(FIXTURE, "--comparer")
        self.assertEqual(code, 1, sortie)
        self.assertRegex(sortie, r"(?m)^étape 8 : .*calculée 2.*colonne « 1 »")
        self.assertRegex(sortie, r"(?m)^étape 16 : .*colonne « L2·1 »")
        self.assertNotRegex(sortie, r"(?m)^étape [1-7] : ")

    def test_fichiers_disjoints_sans_dependance_vont_dans_la_meme_vague(self):
        page = self._page(tableau(("1", "`a.py`", "—", "1"), ("2", "`b.py`", "—", "1")))
        code, sortie, _ = jouer(page, "--comparer")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(vagues_de(sortie), {"1": 1, "2": 1})

    def test_meme_fichier_separe_les_etapes(self):
        page = self._page(tableau(("1", "`a.py`, `x.py`", "—", "1"), ("2", "`a.py`", "—", "2")))
        self.assertEqual(vagues_de(jouer(page)[1]), {"1": 1, "2": 2})

    def test_fichier_partage_de_meme_nom_dans_deux_dossiers_separe_les_etapes(self):
        # Deux README.md de dossiers différents : intersection vide, mais fichier partagé.
        page = self._page(tableau(("1", "`README.md`", "—", "1"),
                                  ("2", "`bancs/skills/README.md`", "—", "2")))
        self.assertEqual(vagues_de(jouer(page)[1]), {"1": 1, "2": 2})

    def test_dependance_a_une_etape_separe_meme_avec_fichiers_disjoints(self):
        page = self._page(tableau(("1", "`a.py`", "—", "1"), ("2", "`b.py`", "1", "2")))
        self.assertEqual(vagues_de(jouer(page)[1]), {"1": 1, "2": 2})

    def test_dependances_qui_ne_sont_pas_des_etapes_sont_ignorees(self):
        page = self._page(tableau(("1", "`a.py`", "Q1, lot 1 mergé, toutes", "1"),
                                  ("2", "`b.py`", "—", "1")))
        # Q1 et « lot 1 mergé » sont ignorées ; « toutes » ne l'est pas : 1 passe après 2.
        self.assertEqual(vagues_de(jouer(page)[1]), {"1": 2, "2": 1})

    def test_toutes_est_insensible_a_la_casse(self):
        page = self._page(tableau(("1", "`a.py`", "Toutes", "1"), ("2", "`b.py`", "—", "1")))
        self.assertEqual(vagues_de(jouer(page)[1]), {"1": 2, "2": 1})

    def test_etape_dependant_de_toutes_vient_apres_toutes_les_autres_sur_le_tableau_du_plan(self):
        v = vagues_de(jouer(FIXTURE)[1])
        autres = [n for e, n in v.items() if e != "15"]
        self.assertGreater(v["15"], max(autres))

    def test_etape_ecrite_numero_et_titre_garde_ses_dependances(self):
        # Constaté le 2026-10-08 sur un plan Vahiny : la cellule « Étape » portait
        # « 1 · titre » et « Dépend de » portait « 1 » — toutes les dépendances
        # tombaient, l'étape 21 (dépend de 2, 10, 15, 16, 20) se retrouvait en vague 1.
        nus = (("1", "`a.py`", "—", "1"), ("2", "`b.py`", "1", "2"),
               ("3", "`c.py`", "1, 2", "3"), ("4", "`d.py`", "—", "1"))
        titres = (("1 · garde de lecture", "`a.py`", "—", "1"),
                  ("2 · migration, puis index", "`b.py`", "1", "2"),
                  ("3 · écran", "`c.py`", "1, 2", "3"),
                  ("4 · doc", "`d.py`", "—", "1"))
        attendu = {"1": 1, "2": 2, "3": 3, "4": 1}
        self.assertEqual(vagues_de(jouer(self._page(tableau(*nus)))[1]), attendu)
        code, sortie, _ = jouer(self._page(tableau(*titres)), "--comparer")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(vagues_de(sortie), attendu)

    def test_etape_de_decouverte_ecrite_numero_et_titre_garde_ses_dependances(self):
        titres = (("D1 · sonder l'API", "`notes.md`", "—", "1"),
                  ("1 · client", "`a.py`", "D1", "2"),
                  ("2 · toutes les autres", "`b.py`", "toutes", "3"))
        code, sortie, _ = jouer(self._page(tableau(*titres)), "--comparer")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(vagues_de(sortie), {"D1": 1, "1": 2, "2": 3})

    def test_comparer_nomme_l_etape_par_son_numero(self):
        page = self._page(tableau(("1 · a", "`a.py`", "—", "1"), ("2 · b", "`b.py`", "1", "1")))
        code, sortie, _ = jouer(page, "--comparer")
        self.assertEqual(code, 1, sortie)
        self.assertRegex(sortie, r"(?m)^étape 2 : vague calculée 2, colonne « 1 »$")

    def test_deux_lignes_au_meme_numero_sont_un_echec_net(self):
        page = self._page(tableau(("1 · a", "`a.py`", "—", "1"), ("1 · b", "`b.py`", "—", "1")))
        code, _, erreur = jouer(page)
        self.assertEqual(code, 2)
        self.assertIn("1", erreur)

    def test_la_page_entiere_est_acceptee_et_le_bon_tableau_choisi(self):
        autre = "<table header-row=\"true\">\n<tr>\n<td>Hypothèse</td>\n<td>Statut</td>\n</tr>\n</table>\n"
        page = self._page("## Contraintes\n" + autre + "## Exécution\n"
                          + tableau(("1", "`a.py`", "—", "1")))
        self.assertEqual(vagues_de(jouer(page)[1]), {"1": 1})

    def test_cellules_colorees_par_notion_sont_lues_comme_du_texte(self):
        # Le bleu des retouches enveloppe chaque morceau de cellule dans un
        # <span color="blue"> — en-tête compris — et coupe une liste de fichiers en
        # plusieurs spans. Constaté le 2026-10-09 (plan Vahiny #3) : le tableau n'était
        # plus reconnu, il fallait lancer vagues.py sur une copie nettoyée.
        bleu = lambda t: f'<span color="blue">{t}</span>'
        page = self._page(tableau(
            (bleu("1 · garde"), bleu("`a.py`") + bleu(", ") + bleu("`x.py`"), bleu("—"), bleu("1")),
            (bleu("2 · fusion"), bleu("`a.py`"), bleu("1"), bleu("2")),
            (bleu("3 · doc"), bleu("`b.md`"), bleu("—"), bleu("1")),
        ).replace("<td>Étape</td>", "<td>" + bleu("Étape") + "</td>"))
        code, sortie, erreur = jouer(page, "--comparer")
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(vagues_de(sortie), {"1": 1, "2": 2, "3": 1})

    def test_page_sans_tableau_de_chevauchement_est_un_echec_net(self):
        code, _, erreur = jouer(self._page("rien ici\n"))
        self.assertEqual(code, 2)
        self.assertIn("tableau", erreur)


if __name__ == "__main__":
    unittest.main()
