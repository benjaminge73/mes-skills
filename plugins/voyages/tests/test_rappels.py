"""Tests des rappels « 30 minutes avant » (script pur, aucun réseau réel).

L'horloge est passée en paramètre, l'envoyeur est un faux : rien ne part vers
Telegram. Les attendus (heures UTC, texte du message) sont écrits en dur et
calculés à la main dans les commentaires, jamais dérivés du code. Voyageurs et
lieux sont fictifs (dépôt public) ; le jeton ci-dessous n'ouvre aucun bot.
"""
from __future__ import annotations

import http.server
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = (Path(__file__).resolve().parents[1] / "skills" / "organiser-voyage" / "scripts")
sys.path.insert(0, str(SCRIPTS))

import rappels  # noqa: E402

SCRIPT = SCRIPTS / "rappels.py"
JETON = "123456:FAUX-jeton_pour_test"
CHATS = {"voyageur_a": "1001", "voyageur_b": "1002"}


def utc(texte: str) -> datetime:
    """'2027-04-12T12:00' -> datetime aware en UTC."""
    return datetime.fromisoformat(texte).replace(tzinfo=timezone.utc)


def rappel(**modifs) -> dict:
    # Rome en avril : heure d'été, UTC+2 -> 14 h 30 locale = 12:30 UTC.
    base = {
        "id": "r1",
        "titre": "Galerie des Exemples",
        "ville": "Florence",
        "debut_local": "2027-04-12T14:30",
        "fuseau": "Europe/Rome",
        "lien": "https://exemple.invalid/Voyages/Billets/exemples.pdf",
        "piece_jointe": None,
        "destinataires": ["voyageur_a"],
        "etat": "a_envoyer",
    }
    base.update(modifs)
    return base


class FauxEnvoyeur:
    """Enregistre les appels ; ``pannes`` : chat_id -> exception à lever."""

    def __init__(self, pannes=None):
        self.appels = []
        self.pannes = dict(pannes or {})

    def __call__(self, chat_id, texte, piece_jointe):
        self.appels.append((chat_id, texte, piece_jointe))
        panne = self.pannes.get(chat_id)
        if panne is not None:
            raise panne


class AvecFile(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.chemin = Path(self._tmp.name) / "rappels.json"

    def ecrire(self, entrees, forme="liste"):
        donnees = entrees if forme == "liste" else {"rappels": entrees}
        self.chemin.write_text(json.dumps(donnees), encoding="utf-8")

    def relire(self):
        donnees = json.loads(self.chemin.read_text(encoding="utf-8"))
        return donnees if isinstance(donnees, list) else donnees["rappels"]

    def traiter(self, maintenant, envoyeur, **kw):
        return rappels.traiter(self.chemin, JETON, CHATS,
                               maintenant=utc(maintenant), envoyeur=envoyeur, **kw)


class Fenetre(AvecFile):
    def test_un_rappel_dont_l_heure_locale_est_convertie_une_seconde_fois_part_deux_heures_trop_tot(self):
        """Panne : l'heure locale convertie deux fois (ou lue comme UTC, ou
        avec le décalage d'hiver un jour d'été) décale l'envoi de 1 à 2 h.

        Attendus UTC calculés à la main, échéance = début - 30 min :
        - Paris 2027-03-27 14:30, hiver UTC+1  -> 13:30 UTC, échéance 13:00 ;
        - Paris 2027-03-28 14:30, jour du passage à l'heure d'été (dernier
          dimanche de mars, 01:00 UTC), UTC+2 -> 12:30 UTC, échéance 12:00 ;
        - Lima 2027-04-12 14:30, UTC-5 toute l'année -> 19:30 UTC, échéance 19:00.
        """
        cas = [
            ("Europe/Paris", "2027-03-27T14:30", "2027-03-27T12:59", "2027-03-27T13:00"),
            ("Europe/Paris", "2027-03-28T14:30", "2027-03-28T11:59", "2027-03-28T12:00"),
            ("America/Lima", "2027-04-12T14:30", "2027-04-12T18:59", "2027-04-12T19:00"),
        ]
        for fuseau, debut, trop_tot, echeance in cas:
            with self.subTest(fuseau=fuseau, debut=debut):
                self.ecrire([rappel(fuseau=fuseau, debut_local=debut)])
                faux = FauxEnvoyeur()
                resume = self.traiter(trop_tot, faux)
                self.assertEqual(faux.appels, [])
                self.assertEqual(resume["a_venir"], ["r1"])
                resume = self.traiter(echeance, faux)
                self.assertEqual(len(faux.appels), 1)
                self.assertEqual(resume["envoyes"], ["r1"])

    def test_un_rappel_avant_la_fenetre_ne_part_pas_et_reste_a_envoyer(self):
        """Panne : un rappel envoyé trop tôt, ou marqué envoyé sans l'être."""
        self.ecrire([rappel()])  # début 12:30 UTC, échéance 12:00 UTC
        faux = FauxEnvoyeur()
        resume = self.traiter("2027-04-12T11:59", faux)
        self.assertEqual(faux.appels, [])
        self.assertEqual(resume, {"envoyes": [], "en_echec": [], "manques": [], "a_venir": ["r1"]})
        self.assertEqual(self.relire()[0]["etat"], "a_envoyer")

    def test_un_rappel_dans_la_fenetre_part_une_fois_avec_le_message_de_la_maquette(self):
        """Panne : rappel non envoyé dans la fenêtre, ou message qui s'écarte
        de la maquette (ligne 1, ville - lieu, heure locale, lien, pièce)."""
        self.ecrire([rappel(piece_jointe="/chemin/exemples.pdf")], forme="objet")
        faux = FauxEnvoyeur()
        resume = self.traiter("2027-04-12T12:10", faux)  # 14 h 10 à Rome, même jour
        attendu = (
            "Rappel - dans 30 min\n"
            "Florence - Galerie des Exemples\n"
            "Aujourd'hui 14 h 30 (heure locale)\n"
            "\n"
            "Billet OneDrive : https://exemple.invalid/Voyages/Billets/exemples.pdf"
        )
        self.assertEqual(faux.appels, [("1001", attendu, "/chemin/exemples.pdf")])
        self.assertEqual(resume["envoyes"], ["r1"])
        entree = self.relire()[0]  # la forme {"rappels": [...]} est conservée
        self.assertEqual(entree["etat"], "envoye")

    def test_le_message_dit_demain_ou_la_date_et_omet_la_ville_et_le_lien_absents(self):
        """Panne : « Aujourd'hui » dit à tort pour un événement du lendemain
        local ou plus lointain ; ligne vide ou « None » quand ville/lien manquent.
        Un test en plus du budget : il attrape la panne de formatage, que
        le test « dans la fenêtre » (même jour, tout renseigné) ne voit pas."""
        # 00:15 le 13 à Rome (UTC+2) = 22:15 UTC le 12 ; il est 21:50 UTC =
        # 23:50 le 12 à Rome : l'événement est « demain » en heure locale.
        self.ecrire([rappel(debut_local="2027-04-13T00:15", ville=None, lien=None)])
        faux = FauxEnvoyeur()
        self.traiter("2027-04-12T21:50", faux)
        self.assertEqual(faux.appels[0][1],
                         "Rappel - dans 30 min\n"
                         "Galerie des Exemples\n"
                         "Demain 0 h 15 (heure locale)")
        # Avance de 48 h : le 10 avril 12:30 UTC, l'événement est le 12 avril.
        self.ecrire([rappel()])
        faux = FauxEnvoyeur()
        self.traiter("2027-04-10T12:30", faux, avance=2880)
        self.assertEqual(faux.appels[0][1].splitlines()[0], "Rappel - dans 48 h")
        self.assertEqual(faux.appels[0][1].splitlines()[2], "12 avril 14 h 30 (heure locale)")

    def test_un_rappel_deja_envoye_n_est_pas_renvoye(self):
        """Panne : rappel envoyé deux fois (cron qui repasse dans la fenêtre)."""
        self.ecrire([rappel(etat="envoye", envoyes_a=["voyageur_a"])])
        faux = FauxEnvoyeur()
        resume = self.traiter("2027-04-12T12:10", faux)
        self.assertEqual(faux.appels, [])
        self.assertEqual(resume, {"envoyes": [], "en_echec": [], "manques": [], "a_venir": []})
        self.assertEqual(self.relire()[0]["etat"], "envoye")

    def test_un_rappel_dont_le_debut_est_passe_est_marque_manque_jamais_envoye_en_retard(self):
        """Panne : rappel envoyé après le début de l'événement, ou perdu sans
        trace. Un test en plus du budget : seule panne « silence » couverte."""
        self.ecrire([rappel()])  # début 12:30 UTC
        faux = FauxEnvoyeur()
        resume = self.traiter("2027-04-12T12:30", faux)
        self.assertEqual(faux.appels, [])
        self.assertEqual(resume["manques"], ["r1"])
        self.assertEqual(self.relire()[0]["etat"], "manque")


class AvanceParEntree(AvecFile):
    def test_un_vol_porte_son_avance_de_3_h_et_part_3_h_avant_le_decollage(self):
        """Panne : le vol suit l'avance par défaut (30 min) et le billet arrive
        trop tard pour l'enregistrement. Début 12:30 UTC, échéance 09:30 UTC."""
        self.ecrire([rappel(avance_min=180, titre="Vol Exempleville-Autreville")])
        faux = FauxEnvoyeur()
        self.assertEqual(self.traiter("2027-04-12T09:29", faux)["a_venir"], ["r1"])
        self.assertEqual(faux.appels, [])
        self.assertEqual(self.traiter("2027-04-12T09:30", faux)["envoyes"], ["r1"])
        self.assertIn("Rappel - dans 3 h", faux.appels[0][1])

    def test_une_entree_sans_avance_propre_garde_l_avance_de_l_appel(self):
        self.ecrire([rappel()])
        faux = FauxEnvoyeur()
        self.assertEqual(self.traiter("2027-04-12T11:59", faux)["a_venir"], ["r1"])
        self.assertEqual(self.traiter("2027-04-12T12:00", faux)["envoyes"], ["r1"])
        self.assertIn("Rappel - dans 30 min", faux.appels[0][1])

    def test_une_avance_invalide_est_signalee_sans_envoi(self):
        self.ecrire([rappel(avance_min="3h")])
        faux = FauxEnvoyeur()
        self.assertEqual(self.traiter("2027-04-12T12:00", faux)["en_echec"], ["r1"])
        self.assertEqual(faux.appels, [])


class Reprise(AvecFile):
    def test_un_envoi_en_echec_est_marque_puis_repris_au_passage_suivant(self):
        """Panne : un envoi raté est perdu en silence, ou marqué envoyé."""
        self.ecrire([rappel()])
        resume = self.traiter("2027-04-12T12:05",
                              FauxEnvoyeur({"1001": RuntimeError("réseau coupé")}))
        self.assertEqual(resume["en_echec"], ["r1"])
        entree = self.relire()[0]
        self.assertEqual(entree["etat"], "echec")
        self.assertEqual(entree["tentatives"], 1)
        self.assertIn("réseau coupé", entree["derniere_erreur"])
        faux = FauxEnvoyeur()
        resume = self.traiter("2027-04-12T12:10", faux)
        self.assertEqual(len(faux.appels), 1)
        self.assertEqual(resume["envoyes"], ["r1"])
        self.assertEqual(self.relire()[0]["etat"], "envoye")

    def test_le_jeton_n_apparait_ni_dans_le_fichier_ni_dans_le_resume(self):
        """Panne : l'exception urllib porte l'URL de l'API, donc le jeton, et
        elle serait recopiée dans la dernière erreur du fichier."""
        self.ecrire([rappel()])
        panne = RuntimeError(f"<urlopen error> https://api.telegram.org/bot{JETON}/sendMessage")
        resume = self.traiter("2027-04-12T12:05", FauxEnvoyeur({"1001": panne}))
        self.assertNotIn(JETON, self.chemin.read_text(encoding="utf-8"))
        self.assertNotIn(JETON, json.dumps(resume))
        self.assertIn("sendMessage", self.relire()[0]["derniere_erreur"])  # l'erreur reste utile

    def test_le_voyageur_qui_a_deja_recu_le_rappel_ne_le_recoit_pas_une_seconde_fois(self):
        """Panne : un billet commun à deux destinataires, dont l'un échoue,
        renvoie le rappel aux deux au passage suivant. Un test en plus du
        budget : l'état par destinataire n'est vu par aucun autre test."""
        self.ecrire([rappel(destinataires=["voyageur_a", "voyageur_b"])])
        resume = self.traiter("2027-04-12T12:05", FauxEnvoyeur({"1002": RuntimeError("panne B")}))
        self.assertEqual(resume["en_echec"], ["r1"])
        faux = FauxEnvoyeur()
        resume = self.traiter("2027-04-12T12:10", faux)
        self.assertEqual([a[0] for a in faux.appels], ["1002"])
        self.assertEqual(resume["envoyes"], ["r1"])

    def test_le_texte_deja_parti_n_est_pas_renvoye_quand_seule_la_piece_jointe_a_echoue(self):
        """Panne : le message est envoyé, la pièce jointe échoue, et le
        passage suivant renvoie le message en double. Un test en plus du
        budget : l'envoi en deux temps (texte puis pièce) a son propre état."""
        self.ecrire([rappel(piece_jointe="/chemin/exemples.pdf")])
        faux = FauxEnvoyeur({"1001": rappels.ErreurEnvoi("document refusé", texte_parti=True)})
        self.traiter("2027-04-12T12:05", faux)
        faux = FauxEnvoyeur()
        resume = self.traiter("2027-04-12T12:10", faux)
        self.assertEqual(faux.appels, [("1001", None, "/chemin/exemples.pdf")])
        self.assertEqual(resume["envoyes"], ["r1"])


class FauxTelegram(http.server.BaseHTTPRequestHandler):
    requetes: list = []
    statut = 200

    def do_POST(self):
        longueur = int(self.headers.get("Content-Length", 0))
        FauxTelegram.requetes.append((self.path, self.headers.get("Content-Type", ""),
                                      self.rfile.read(longueur)))
        corps = json.dumps({"ok": FauxTelegram.statut == 200,
                            "description": "Unauthorized"}).encode()
        self.send_response(FauxTelegram.statut)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *a):
        pass


class EnvoyeurTelegram(unittest.TestCase):
    """L'envoyeur par défaut contre un faux serveur local (aucun réseau réel).
    Tests en plus du budget : le multipart est construit à la main, et rien
    d'autre ne l'exerce."""

    def setUp(self):
        FauxTelegram.requetes = []
        FauxTelegram.statut = 200
        self.serveur = http.server.HTTPServer(("127.0.0.1", 0), FauxTelegram)
        threading.Thread(target=self.serveur.serve_forever, daemon=True).start()
        self.addCleanup(self.serveur.server_close)
        self.addCleanup(self.serveur.shutdown)
        self.base = f"http://127.0.0.1:{self.serveur.server_port}"
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def envoyeur(self):
        return rappels.envoyeur_telegram(JETON, base=self.base)

    def test_la_piece_jointe_part_comme_document_pour_un_pdf_et_comme_photo_pour_un_png(self):
        """Panne : pièce jointe non envoyée, ou PNG du QR envoyé comme
        document (Telegram n'affiche alors pas l'image)."""
        pdf = self.dossier / "billet.pdf"
        pdf.write_bytes(b"%PDF-contenu-fictif")
        png = self.dossier / "qr.png"
        png.write_bytes(b"\x89PNG-contenu-fictif")
        envoi = self.envoyeur()
        envoi("1001", "Bonjour", str(pdf))
        envoi("1001", None, str(png))
        chemins = [r[0] for r in FauxTelegram.requetes]
        self.assertEqual(chemins, [f"/bot{JETON}/sendMessage", f"/bot{JETON}/sendDocument",
                                   f"/bot{JETON}/sendPhoto"])
        _, type_contenu, corps = FauxTelegram.requetes[1]
        self.assertTrue(type_contenu.startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="chat_id"', corps)
        self.assertIn(b"1001", corps)
        self.assertIn(b'name="document"; filename="billet.pdf"', corps)
        self.assertIn(b"%PDF-contenu-fictif", corps)
        self.assertIn(b'name="photo"; filename="qr.png"', FauxTelegram.requetes[2][2])
        self.assertIn(b"Bonjour", FauxTelegram.requetes[0][2])

    def test_une_erreur_http_de_l_api_est_levee_sans_le_jeton(self):
        """Panne : l'erreur de l'API (jeton refusé) remonte avec l'URL, donc
        avec le jeton."""
        FauxTelegram.statut = 401
        with self.assertRaises(rappels.ErreurEnvoi) as ctx:
            self.envoyeur()("1001", "Bonjour", None)
        self.assertNotIn(JETON, str(ctx.exception))
        self.assertIn("401", str(ctx.exception))


class LigneDeCommande(AvecFile):
    def lancer(self, entree_standard, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--file", str(self.chemin), *args],
                              input=entree_standard, capture_output=True, text=True, timeout=60)

    def test_la_ligne_de_commande_lit_le_jeton_sur_l_entree_standard_et_rend_le_code_du_resume(self):
        """Panne : jeton lu en argument (visible dans ps), jeton recopié dans
        la sortie, code 0 malgré un échec. Un test en plus du budget : le
        contrat de la CLI (aucun envoi réel : une entrée à venir, une invalide)."""
        entree = json.dumps({"jeton": JETON, "destinataires": CHATS})
        self.ecrire([rappel(id="futur", debut_local="2027-04-12T14:30")])
        p = self.lancer(entree, "--maintenant", "2027-04-12T10:00:00Z")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["a_venir"], ["futur"])
        self.ecrire([rappel(id="casse", fuseau="Mars/Olympus")])
        p = self.lancer(entree, "--maintenant", "2027-04-12T10:00:00Z")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stdout)["en_echec"], ["casse"])
        self.assertNotIn(JETON, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
