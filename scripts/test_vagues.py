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

import re
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


def tableau_barres(*lignes):
    """Le même tableau tel que le rend ``notion-fetch`` du connecteur de l'app : en
    barres verticales, les fichiers en ``<code>…</code>`` (miroir du 2026-10-28)."""
    texte = ["| Étape | Fichiers touchés | Dépend de | Vague | Relecture |",
             "| --- | --- | --- | --- | --- |"]
    for etape, fichiers, dep, vague in lignes:
        fichiers = re.sub(r"`([^`]+)`", r"<code>\\1</code>", fichiers)
        texte.append(f"| {etape} | {fichiers} | {dep} | {vague} | étape |")
    return "\n".join(texte) + "\n"


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


class FormatDuConnecteur(Vagues):
    # Constaté le 2026-11-12 : sur un miroir pris par ``notion-fetch``, vagues.py
    # répondait « aucun tableau … trouvé » (code 2), le miroir ``composio`` passait.
    def test_tableau_en_barres_avec_code_html_est_lu(self):
        lignes = (("1 · Le collecteur", "`collecteur.py`, `docs/exploitation.md`", "Q1", "1"),
                  ("2 · Étiqueter A", "`banc.py`, `test_banc.py`", "—", "1"),
                  ("3 · Photo A", "`banc.py`, `docs/exploitation.md`", "Q2, 2", "2"),
                  ("4 · Enquête", "`enqueteur.py`, `docs/exploitation.md`", "Q3, 1, 3", "3"),
                  ("5 · Constat", "aucun", "toutes", "4"))
        page = self._page("## Exécution\n\nCoût estimé : rien.\n\n" + tableau_barres(*lignes)
                          + "\n### Étape 1 — Le collecteur\n\n- <b>Dépend de</b> — Q1.\n")
        code, sortie, erreur = jouer(page, "--comparer")
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(vagues_de(sortie), {"1": 1, "2": 1, "3": 2, "4": 3, "5": 4})

    def test_les_deux_formats_donnent_les_memes_vagues(self):
        lignes = (("1", "`a.py`", "—", "1"), ("2", "`a.py`", "—", "2"), ("3", "`b.py`", "1", "2"))
        html = vagues_de(jouer(self._page(tableau(*lignes)))[1])
        barres = vagues_de(jouer(self._page(tableau_barres(*lignes)))[1])
        self.assertEqual(html, {"1": 1, "2": 2, "3": 2})
        self.assertEqual(barres, html)

    def test_tableau_en_barres_colore_est_lu(self):
        bleu = lambda t: f'<span color="blue">{t}</span>'
        page = self._page(tableau_barres((bleu("1 · garde"), bleu("`a.py`"), bleu("—"), "1"),
                                         ("2", "`a.py`", bleu("1"), "2")))
        code, sortie, erreur = jouer(page, "--comparer")
        self.assertEqual(code, 0, sortie + erreur)


class DependEnToutesLettres(Vagues):
    # Constaté le 2026-11-12 : « étape 5 », « étapes 3 et 4 » ou « étapes 1 à 9 »
    # étaient ignorées sans un mot, et une étape qui dépend de tout partait en vague 1.
    def _cinq(self, dep_de_5):
        """Une chaîne 1 → 2 → 3 → 4 (vagues 1 à 4), puis 5 qui dépend de ``dep_de_5`` :
        si l'étape 4 est lue, 5 part en vague 5 ; sinon elle remonte plus tôt."""
        chaine = [(str(n), f"`f{n}.py`", str(n - 1) if n > 1 else "—", str(n)) for n in range(1, 5)]
        return tableau(*chaine, ("5", "`f5.py`", dep_de_5, "5"))

    def test_formes_ecrites_en_toutes_lettres_sont_lues(self):
        for dep in ("étape 4", "Étape 4", "étapes 3 et 4", "étapes 1 à 4", "étapes 1, 2, 3 et 4",
                    "Q2 ; étape 4 (même fichier)", "1 à 4"):
            with self.subTest(dep=dep):
                code, sortie, erreur = jouer(self._page(self._cinq(dep)), "--comparer")
                self.assertEqual(code, 0, sortie + erreur)
                self.assertEqual(vagues_de(sortie)["5"], 5)

    def test_une_etape_qui_depend_de_toutes_ne_part_pas_en_vague_un(self):
        lignes = [(str(n), f"`f{n}.py`", str(n - 1) if n > 1 else "—", str(n)) for n in range(1, 10)]
        lignes.append(("10", "aucun", "étapes 1 à 9", "10"))
        code, sortie, erreur = jouer(self._page(tableau(*lignes)), "--comparer")
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(vagues_de(sortie)["10"], 10)

    def test_cellule_etape_incomprise_est_refusee_avec_un_message_clair(self):
        code, sortie, erreur = jouer(self._page(self._cinq("étape quatre")))
        self.assertEqual(code, 2, sortie)
        self.assertIn("étape 5", erreur)
        self.assertIn("« étape quatre »", erreur)
        self.assertIn("numéros nus", erreur)

    def test_etape_citee_absente_du_tableau_est_refusee(self):
        code, sortie, erreur = jouer(self._page(self._cinq("7")))
        self.assertEqual(code, 2, sortie)
        self.assertIn("7", erreur)
        self.assertIn("absente du tableau", erreur)

    def test_dependance_hors_tableau_est_signalee_sans_bloquer(self):
        code, sortie, erreur = jouer(self._page(self._cinq("lot 1 mergé, 4")))
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(vagues_de(sortie)["5"], 5)
        self.assertIn("« lot 1 mergé »", erreur)


class EtapesDeCron(Vagues):
    # Une étape C<n> (cron lancé à la main, cron-a-la-main.md) écrite sans « · » était
    # lue comme la cellule entière : « Dépend de » qui citait « C1 » ne la retrouvait pas.
    def test_etape_C1_est_reconnue_et_citee(self):
        page = self._page(tableau(("1", "`a.py`", "—", "1"),
                                  ("C1 — lancer le cron à la main", "aucun", "1", "2"),
                                  ("2", "`b.py`", "C1", "3")))
        code, sortie, erreur = jouer(page, "--comparer")
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(vagues_de(sortie), {"1": 1, "C1": 2, "2": 3})

    def test_etape_citee_en_minuscules_ou_en_toutes_lettres(self):
        page = self._page(tableau(("C1 · cron", "aucun", "—", "1"),
                                  ("D2 · sonde", "`n.md`", "—", "1"),
                                  ("3", "`c.py`", "étapes c1 et d2", "2")))
        code, sortie, erreur = jouer(page, "--comparer")
        self.assertEqual(code, 0, sortie + erreur)
        self.assertEqual(vagues_de(sortie)["3"], 2)


if __name__ == "__main__":
    unittest.main()
