"""Tests du nommage des billets (module pur, sans réseau ni OneDrive).

Les attendus sont écrits en dur, dérivés de la nomenclature, pas du code.
Voyageurs et lieux sont fictifs (dépôt public).
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = (Path(__file__).resolve().parents[1] / "skills" / "organiser-voyage" / "scripts")
sys.path.insert(0, str(SCRIPTS))

import nommer_billet as nb  # noqa: E402

BILLET = {"type": "billet", "date": "2027-04-12", "heure": "14:30",
          "lieu": "Musee des Exemples", "voyageur": "Voyageur A"}


def avec(base, **modifs):
    d = dict(base)
    d.update(modifs)
    return d


class Refus(unittest.TestCase):
    def test_un_nom_construit_sur_un_champ_incertain_ou_absent_est_refuse(self):
        # Panne nommée par le plan : un nom bâti sur une date incertaine partait
        # dans OneDrive. Chaque jeu incomplet doit lever, jamais rendre un nom.
        incomplets = {
            "date absente": {k: v for k, v in BILLET.items() if k != "date"},
            "date vide": avec(BILLET, date=""),
            "date impossible": avec(BILLET, date="2027-02-30"),
            "date signalée incertaine": avec(BILLET, incertains=["date"]),
            "heure absente d'un billet horodaté": {k: v for k, v in BILLET.items() if k != "heure"},
            "lieu absent": avec(BILLET, lieu=None),
            "voyageur absent et billet non multiple": {k: v for k, v in BILLET.items() if k != "voyageur"},
        }
        for cas, champs in incomplets.items():
            with self.subTest(cas=cas):
                with self.assertRaises(nb.ChampIncertain):
                    nb.construire_nom(champs)

    def test_le_cli_refuse_avec_un_code_non_nul_et_un_message_sur_stderr(self):
        # Panne : un refus qui ne se voit pas côté agent (code 0, nom vide).
        res = subprocess.run(
            [sys.executable, str(SCRIPTS / "nommer_billet.py"), "--json",
             json.dumps(avec(BILLET, date=""))],
            capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertEqual(res.stdout, "")
        self.assertIn("date", res.stderr)


class Gabarits(unittest.TestCase):
    def test_billet_vol_train_hebergement_suivent_la_nomenclature(self):
        # Panne : un gabarit qui dérive (séparateurs, « h » de l'heure, extension).
        attendus = [
            (BILLET, "2027-04-12 14h30 - Musee des Exemples - Billet - Voyageur A.pdf"),
            (avec(BILLET, extension="png"),
             "2027-04-12 14h30 - Musee des Exemples - Billet - Voyageur A.png"),
            ({"type": "vol", "date": "2027-05-01", "origine": "Paris", "destination": "Lima",
              "document": "Carte embarquement", "voyageur": "Voyageur B"},
             "2027-05-01 - Vol Paris-Lima - Carte embarquement - Voyageur B.pdf"),
            ({"type": "train", "date": "2027-05-03", "heure": "08h05", "origine": "Lima",
              "destination": "Cusco", "voyageur": "Voyageur A"},
             "2027-05-03 08h05 - Train Lima-Cusco - Billet - Voyageur A.pdf"),
            ({"type": "hebergement", "date": "2027-05-04", "nom": "Hotel des Exemples"},
             "2027-05-04 - Hebergement Hotel des Exemples - Reservation.pdf"),
        ]
        for champs, attendu in attendus:
            with self.subTest(attendu=attendu):
                self.assertEqual(nb.construire_nom(champs), attendu)

    def test_billet_multiple_porte_le_prenom_sinon_un_sur_n(self):
        # Panne : N billets d'une commande qui se nomment pareil et s'écrasent.
        sans_voyageur = {k: v for k, v in BILLET.items() if k != "voyageur"}
        self.assertEqual(
            nb.construire_nom(avec(sans_voyageur, billet=1, sur=2)),
            "2027-04-12 14h30 - Musee des Exemples - Billet - 1 sur 2.pdf")
        self.assertEqual(
            nb.construire_nom(avec(sans_voyageur, billet=2, sur=2)),
            "2027-04-12 14h30 - Musee des Exemples - Billet - 2 sur 2.pdf")
        # Le prénom, quand le billet le porte, l'emporte sur « 1 sur 2 ».
        self.assertEqual(
            nb.construire_nom(avec(BILLET, billet=1, sur=2)),
            "2027-04-12 14h30 - Musee des Exemples - Billet - Voyageur A.pdf")

    def test_billet_commun_omet_le_dernier_champ(self):
        # Panne : un billet commun reçoit le nom d'un seul voyageur, et le rappel ne part qu'à lui.
        sans_voyageur = {k: v for k, v in BILLET.items() if k != "voyageur"}
        self.assertEqual(
            nb.construire_nom(avec(sans_voyageur, commun=True)),
            "2027-04-12 14h30 - Musee des Exemples - Billet.pdf")

    def test_les_caracteres_interdits_dans_onedrive_sont_nettoyes(self):
        # Panne : un « : » ou un « / » du lieu fait échouer le dépôt OneDrive.
        nom = nb.construire_nom(avec(BILLET, lieu='Musee: "des" <Exemples>? / a|b*\\ .'))
        self.assertEqual(nom, "2027-04-12 14h30 - Musee des Exemples ab - Billet - Voyageur A.pdf")
        for c in '"*:<>?/\\|':
            self.assertNotIn(c, nom)


class Collision(unittest.TestCase):
    def test_un_nom_deja_present_n_est_jamais_ecrase(self):
        # Panne : deux billets au même nom, le second écrase le premier.
        nom = "2027-04-12 14h30 - Musee des Exemples - Billet - Voyageur A.pdf"
        self.assertEqual(nb.nom_libre(nom, []), nom)
        self.assertEqual(nb.nom_libre(nom, [nom]),
                         "2027-04-12 14h30 - Musee des Exemples - Billet - Voyageur A (2).pdf")
        deja = [nom, "2027-04-12 14h30 - Musee des Exemples - Billet - Voyageur A (2).pdf"]
        self.assertEqual(nb.nom_libre(nom, deja),
                         "2027-04-12 14h30 - Musee des Exemples - Billet - Voyageur A (3).pdf")
        # OneDrive ignore la casse : « .PDF » en majuscules est une collision.
        self.assertEqual(nb.nom_libre("a.pdf", ["A.PDF"]), "a (2).pdf")


class DossierDuVoyage(unittest.TestCase):
    def test_le_dossier_porte_l_annee_seule_si_le_voyage_depasse_un_mois(self):
        # Panne : un voyage de 3 mois rangé « AAAA-MM » (ou l'inverse).
        # Règle : plus d'un mois = plus de 31 jours (fin - début).
        cas = [
            ("2026-03-10", "2026-03-24", "2026-03 - Destination Exemple"),
            ("2026-03-01", "2026-04-01", "2026-03 - Destination Exemple"),   # 31 jours
            ("2026-03-01", "2026-04-02", "2026 - Destination Exemple"),      # 32 jours
            ("2026-11-20", "2027-02-20", "2026 - Destination Exemple"),
        ]
        for debut, fin, attendu in cas:
            with self.subTest(debut=debut, fin=fin):
                self.assertEqual(nb.nom_dossier_voyage("Destination Exemple", debut, fin), attendu)

    def test_un_dossier_sur_des_dates_incoherentes_est_refuse(self):
        # Panne : un dossier daté sur des dates inversées (fin avant début) part dans OneDrive.
        with self.assertRaises(nb.ChampIncertain):
            nb.nom_dossier_voyage("Destination Exemple", "2026-03-10", "2026-03-01")


if __name__ == "__main__":
    unittest.main()
