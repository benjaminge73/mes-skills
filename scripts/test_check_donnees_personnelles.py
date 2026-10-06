"""Tests de ``check_donnees_personnelles.py`` sur un arbre jetable.

Le garde est lancé en vrai sous-processus sur un faux dépôt (``--racine``) :
on lui donne des fichiers, on lit sa sortie et son code de retour. Aucune
valeur de ces fixtures n'est réelle (adresses et numéros d'exemple), et
``HOME`` pointe vers un dossier jetable pour que la liste de motifs connus
du poste ne s'invite jamais dans un test.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_donnees_personnelles.py"


class Garde(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.racine = base / "depot"
        self.maison = base / "maison"
        self.maison.mkdir()
        for racine in ("plugins/voyages", "evals/voyages"):
            (self.racine / racine).mkdir(parents=True)

    def poser(self, chemin, texte, binaire=False):
        p = self.racine / chemin
        p.parent.mkdir(parents=True, exist_ok=True)
        if binaire:
            p.write_bytes(texte)
        else:
            p.write_text(texte, encoding="utf-8")
        return p

    def jouer(self, **env):
        propre = {k: v for k, v in os.environ.items() if k != "MOTIFS_PERSONNELS"}
        propre["HOME"] = str(self.maison)
        propre.update(env)
        r = subprocess.run([sys.executable, str(SCRIPT), "--racine", str(self.racine)],
                           capture_output=True, text=True, env=propre)
        return r.returncode, r.stdout + r.stderr


class DonneesPubliees(Garde):
    def test_panne_l_adresse_reelle_publiee_passe_le_garde(self):
        self.poser("plugins/voyages/skills/s/SKILL.md", "Écrire à prenom.nom@gmail.com\n")
        code, sortie = self.jouer()
        self.assertEqual(code, 1, sortie)
        self.assertIn("plugins/voyages/skills/s/SKILL.md:1 : adresse e-mail", sortie)

    def test_panne_un_identifiant_telegram_passe_le_garde(self):
        self.poser("evals/voyages/cas/prompt.md", "ligne 1\nchat_id: 123456789\n")
        self.poser("evals/voyages/cas/groupe.md", "groupe -1001234567890 voyage\n")
        code, sortie = self.jouer()
        self.assertEqual(code, 1, sortie)
        self.assertIn("evals/voyages/cas/prompt.md:2 : identifiant numérique long", sortie)
        self.assertIn("evals/voyages/cas/groupe.md:1 : identifiant numérique long", sortie)

    def test_panne_un_numero_de_telephone_publie_passe_le_garde(self):
        for i, numero in enumerate(("06 12 34 56 78", "06.12.34.56.78", "+33 6 12 34 56 78",
                                    "+44 20 7946 0958")):
            with self.subTest(numero=numero):
                self.poser(f"plugins/voyages/tel{i}.md", f"Appeler le {numero} avant 18 h.\n")
                code, sortie = self.jouer()
                self.assertEqual(code, 1, sortie)
                self.assertIn(f"plugins/voyages/tel{i}.md:1 : numéro de téléphone", sortie)
                (self.racine / f"plugins/voyages/tel{i}.md").unlink()

    def test_panne_un_chemin_de_profil_hermes_ou_de_repertoire_personnel_passe_le_garde(self):
        self.poser("plugins/voyages/a.md", "cd ~/.hermes/profiles/mon-profil/skills\n")
        self.poser("plugins/voyages/b.md", "voir /home/prenom/documents/billets\n")
        self.poser("plugins/voyages/c.md", "voir /Users/prenom/Documents/billets\n")
        code, sortie = self.jouer()
        self.assertEqual(code, 1, sortie)
        self.assertIn("plugins/voyages/a.md:1 : chemin de profil Hermes", sortie)
        self.assertIn("plugins/voyages/b.md:1 : chemin de répertoire personnel", sortie)
        self.assertIn("plugins/voyages/c.md:1 : chemin de répertoire personnel", sortie)

    def test_panne_un_motif_connu_de_la_liste_hors_depot_passe_le_garde(self):
        liste = self.maison / "motifs.txt"
        liste.write_text("# un motif par ligne\n\nzorglub dupontel\n", encoding="utf-8")
        self.poser("evals/voyages/cas/prompt.md", "Voyageur : Zorglub Dupontel, 2 places\n")
        code, sortie = self.jouer(MOTIFS_PERSONNELS=str(liste))
        self.assertEqual(code, 1, sortie)
        self.assertIn("evals/voyages/cas/prompt.md:1 : motif connu", sortie)

    def test_panne_la_liste_par_defaut_du_poste_n_est_pas_lue(self):
        defaut = self.maison / ".config" / "mes-skills" / "motifs-personnels.txt"
        defaut.parent.mkdir(parents=True)
        defaut.write_text("zorglub\n", encoding="utf-8")
        self.poser("plugins/voyages/n.md", "Merci Zorglub.\n")
        code, sortie = self.jouer()
        self.assertEqual(code, 1, sortie)
        self.assertIn("plugins/voyages/n.md:1 : motif connu", sortie)

    def test_panne_la_valeur_trouvee_est_recopiee_dans_le_log(self):
        liste = self.maison / "motifs.txt"
        liste.write_text("zorglub\n", encoding="utf-8")
        valeurs = ("prenom.nom@gmail.com", "06 12 34 56 78", "123456789",
                   "/home/prenom/documents", ".hermes/profiles/mon-profil", "zorglub")
        self.poser("plugins/voyages/tout.md", "\n".join(f"ligne {v}" for v in valeurs) + "\n")
        code, sortie = self.jouer(MOTIFS_PERSONNELS=str(liste))
        self.assertEqual(code, 1, sortie)
        for valeur in valeurs:
            with self.subTest(valeur=valeur):
                self.assertNotIn(valeur, sortie)
        # Le garde a bien vu les six lignes : sans ça, la preuve ci-dessus serait vide.
        for numero in range(1, 7):
            self.assertIn(f"plugins/voyages/tout.md:{numero} :", sortie)


class FauxPositifs(Garde):
    def test_panne_un_faux_positif_d_exemple_bloque_a_tort(self):
        self.poser("plugins/voyages/exemples.md", "\n".join([
            "De : voyageur-a@example.invalid",
            "De : voyageur-b@example.com",
            "De : voyageur-c@billets.example",
            "De : voyageur-d@serveur.test",
            "empreinte 3f2a9c7e1b4d5a6f708192a3b4c5d6e7f8091a2b",
            "empreinte 1234567890123456789012345678901234567890 (40 chiffres : trop long pour un identifiant)",
            "rappel 2026-10-06T12:00:00+02:00",
            "horodatage 20261006120000 et 20261006",
            "uuid 12345678-1234-1234-1234-123456789012",
            "version 1.2.3, build 2026.10.06",
            "plage 06-10-2026 au 09-10-2026",
            "dossier /home/user/billets et ~/.config/exemple",
            "Python 3.14.0 @ staticmethod",
            "",
        ]))
        code, sortie = self.jouer()
        self.assertEqual(code, 0, sortie)

    def test_panne_un_faux_positif_assume_ne_peut_pas_etre_marque_ok(self):
        self.poser("plugins/voyages/doc.md",
                   "contact : prenom.nom@gmail.com  <!-- donnees-personnelles: ok -->\n"
                   "autre : autre.nom@gmail.com\n")
        code, sortie = self.jouer()
        self.assertEqual(code, 1, sortie)
        self.assertNotIn("doc.md:1 :", sortie)   # la ligne marquée passe
        self.assertIn("plugins/voyages/doc.md:2 : adresse e-mail", sortie)  # la voisine reste vue

    def test_panne_les_binaires_et_pycache_font_rougir_le_garde_a_tort(self):
        # Chaque exécution des tests laisse des .pyc sous plugins/voyages/ : un
        # garde qui les lisait serait rouge en local sans rien de publié.
        self.poser("plugins/voyages/__pycache__/x.cpython-314.pyc",
                   b"\x00\x01prenom.nom@gmail.com\x00", binaire=True)
        self.poser("plugins/voyages/billet.pdf", b"%PDF\x00\x00 123456789012 \xff\xfe", binaire=True)
        code, sortie = self.jouer()
        self.assertEqual(code, 0, sortie)


class Usage(Garde):
    def test_panne_une_racine_absente_ne_doit_pas_passer_pour_un_depot_propre(self):
        (self.racine / "evals/voyages").rmdir()
        code, sortie = self.jouer()
        self.assertEqual(code, 2, sortie)

    def test_panne_une_liste_de_motifs_introuvable_ne_doit_pas_desactiver_le_garde(self):
        self.poser("plugins/voyages/ok.md", "rien\n")
        code, sortie = self.jouer(MOTIFS_PERSONNELS=str(self.maison / "absente.txt"))
        self.assertEqual(code, 2, sortie)


if __name__ == "__main__":
    unittest.main()
