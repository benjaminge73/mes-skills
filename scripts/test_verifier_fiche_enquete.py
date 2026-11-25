"""Tests de ``verifier-fiche-enquete.py`` : la fiche de l'enquêteur recopie chaque case de la liste.

Le script (``plugins/plans-notion/skills/_partage/scripts/``) lit la liste d'enquête (``listes/enquete.md``,
ses cases ``- [ ] C<n> …``) et la fiche de l'enquêteur (ses cases ``- [x] C<n> … — preuve : …`` ou
``- [ ] C<n> … — sans objet : … / non vérifié : …``). Une case cochée sans preuve, une case non cochée sans
marqueur, une case de la liste absente de la fiche : code 1, une ligne par case fautive sur la sortie
standard. Fiche complète : code 0. Usage ou fichier illisible : code 2.

Les tests lancent le vrai script sur de vrais fichiers temporaires (pas de mock). Sauf les tests qui
disent « liste par défaut », ils passent une petite liste de test ; aucun ne lit la fiche d'un plan réel.

Pannes attrapées :
- ``test_c3_cochee_sans_preuve_sort_en_1_et_nomme_c3`` : la case C3 est cochée sans « — preuve : ».
  C'est la panne nommée par l'étape : une fiche qui affirme une case sans la montrer doit sortir en 1
  et nommer la case.
- ``test_fiche_qui_manque_c7_sort_en_1`` : la fiche ne recopie pas C7. Une case absente doit sortir en 1
  et être nommée, sinon une fiche tronquée passerait pour complète.
- ``test_non_verifie_sans_bash_passe`` : une case non cochée avec « non vérifié : sans Bash » est une
  réponse permise, elle sort en 0. Sans ce test, un script qui refuserait toute case non cochée
  passerait les autres tests.
- ``test_fiche_complete_sort_en_0`` (en plus du budget) : un script qui rendrait toujours 1 passerait les
  tests précédents. Ce test lit la liste par défaut et vérifie qu'une fiche complète sort en 0.
- ``test_usage_sort_en_2`` : sans ``--fiche``, le script affiche son usage et sort en 2, distinct de 1.
  L'assertion sur « usage » écarte le cas où Python lui-même sort en 2 (script introuvable).
- ``test_case_non_cochee_sans_marqueur_sort_en_1`` (en plus du budget) : les quatre tests précédents
  passent si le script accepte toute case non cochée. Ce test attrape ce laxisme : une case non cochée
  sans « sans objet : » ni « non vérifié : » sort en 1 et est nommée.
- ``test_fiche_json_claude_p_lue_comme_texte`` (en plus du budget) : la fiche arrive parfois en sortie
  JSON de ``claude -p`` (champ ``result``). Une fiche complète dans ce JSON doit sortir en 0 ; un script
  qui lirait le JSON brut ne trouverait aucune case et sortirait en 1.
- ``test_preuve_non_verifiee_signalee_sans_refuser`` (budget de l'étape 3) : la case C6 est cochée, mais
  sa preuve dit « (non vérifié) » : une preuve partielle. Le script doit la nommer sur la sortie
  (« preuve partielle : C6 ») et sortir en 0, sans refuser la fiche. Sans ce test, une fiche qui coche
  une case en avouant qu'elle ne l'a pas vérifiée passerait pour complète.
- ``test_preuve_sans_marqueur_non_signalee`` (budget de l'étape 3) : contre-épreuve. Une case cochée dont
  la preuve ne dit pas « non vérifié » (la ligne C0 réelle) ne doit pas être signalée : sortie vide, code 0.
  Sans ce test, un script qui signalerait toute case cochée passerait le test précédent.
- ``test_code_1_avec_preuve_partielle_sur_la_sortie`` (revue de l'étape 3) : une fiche avec un défaut (C0
  cochée sans preuve) et une preuve partielle (C6) sort en 1 et porte les deux lignes, le défaut d'abord.
  Sans ce test, le chemin « code 1 + ligne preuve partielle » ne serait testé par rien : un script qui
  perdrait la ligne partielle quand un défaut existe passerait tous les autres tests.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = (RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts"
          / "verifier-fiche-enquete.py")
LISTE_PAR_DEFAUT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "listes" / "enquete.md"

LISTE_DE_TEST = """# Liste de test

- [ ] C2 Docs — geste ; preuve : forme
- [ ] C3 Gardes — geste ; preuve : forme
- [ ] C7 Valeurs — geste ; preuve : forme
"""

LISTE_C0 = """# Liste de test

- [ ] C0 Objets touchés — geste ; preuve : forme
"""

LISTE_C0_C6 = """# Liste de test

- [ ] C0 Objets touchés — geste ; preuve : forme
- [ ] C6 Contrat d'un outil externe — geste ; preuve : forme
"""

FICHE_COMPLETE = """- [x] C2 Docs — preuve : `grep -rn` rend 0 résultat
- [x] C3 Gardes — preuve : `ci_locale.sh` lu, limite 300 lignes
- [x] C7 Valeurs — preuve : `grep -rn 'seuil'` rend 2 points
"""


class VerifierFicheEnquete(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name)
        self.liste = self.dossier / "liste.md"
        self.liste.write_text(LISTE_DE_TEST, encoding="utf-8")

    def _ecrire(self, nom: str, texte: str) -> Path:
        chemin = self.dossier / nom
        chemin.write_text(texte, encoding="utf-8")
        return chemin

    def _lancer(self, fiche: str, *, liste: Path | None = None) -> subprocess.CompletedProcess:
        fichier_fiche = self._ecrire("fiche.md", fiche)
        commande = [sys.executable, str(SCRIPT), "--fiche", str(fichier_fiche)]
        if liste is not None:
            commande += ["--liste", str(liste)]
        return subprocess.run(commande, capture_output=True, text=True, encoding="utf-8")

    def test_c3_cochee_sans_preuve_sort_en_1_et_nomme_c3(self) -> None:
        fiche = (
            "- [x] C2 Docs — preuve : `grep -rn` rend 0 résultat\n"
            "- [x] C3 Gardes — ce qui refuse le changement\n"
            "- [x] C7 Valeurs — preuve : `grep -rn 'seuil'` rend 2 points\n"
        )
        resultat = self._lancer(fiche, liste=self.liste)
        self.assertEqual(resultat.returncode, 1, resultat.stderr)
        lignes = resultat.stdout.strip().splitlines()
        self.assertEqual(len(lignes), 1, resultat.stdout)
        self.assertTrue(lignes[0].startswith("C3 "), lignes[0])
        self.assertIn("cochée sans preuve", lignes[0])

    def test_fiche_qui_manque_c7_sort_en_1(self) -> None:
        fiche = (
            "- [x] C2 Docs — preuve : `grep -rn` rend 0 résultat\n"
            "- [x] C3 Gardes — preuve : `ci_locale.sh` lu, limite 300 lignes\n"
        )
        resultat = self._lancer(fiche, liste=self.liste)
        self.assertEqual(resultat.returncode, 1, resultat.stderr)
        self.assertIn("C7 absente de la fiche", resultat.stdout)

    def test_non_verifie_sans_bash_passe(self) -> None:
        fiche = (
            "- [ ] C2 Docs — non vérifié : sans Bash, chercher dans docs/ impossible\n"
            "- [x] C3 Gardes — preuve : `ci_locale.sh` lu, limite 300 lignes\n"
            "- [x] C7 Valeurs — preuve : `grep -rn 'seuil'` rend 2 points\n"
        )
        resultat = self._lancer(fiche, liste=self.liste)
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)

    def test_fiche_complete_sort_en_0(self) -> None:
        fiche = "".join(
            f"- [x] C{n} Titre {n} — preuve : sortie {n} observée\n" for n in range(13))
        resultat = self._lancer(fiche)
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)

    def test_usage_sort_en_2(self) -> None:
        resultat = subprocess.run([sys.executable, str(SCRIPT)],
                                  capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(resultat.returncode, 2, resultat.stderr)
        self.assertIn("usage", resultat.stderr.lower())

    def test_case_non_cochee_sans_marqueur_sort_en_1(self) -> None:
        fiche = (
            "- [ ] C2 Docs — pas joué\n"
            "- [x] C3 Gardes — preuve : `ci_locale.sh` lu, limite 300 lignes\n"
            "- [x] C7 Valeurs — preuve : `grep -rn 'seuil'` rend 2 points\n"
        )
        resultat = self._lancer(fiche, liste=self.liste)
        self.assertEqual(resultat.returncode, 1, resultat.stderr)
        self.assertIn("C2 non cochée sans", resultat.stdout)

    def test_fiche_json_claude_p_lue_comme_texte(self) -> None:
        fiche_json = json.dumps({"type": "result", "result": FICHE_COMPLETE}, ensure_ascii=False)
        resultat = self._lancer(fiche_json, liste=self.liste)
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)

    def test_preuve_non_verifiee_signalee_sans_refuser(self) -> None:
        # Ligne C6 réelle d'une fiche d'enquête (identifiants Slack retirés) : cochée, preuve « (non vérifié) ».
        liste = self._ecrire("liste_c0_c6.md", LISTE_C0_C6)
        fiche = (
            "- [x] C0 Objets touchés — preuve : les 54 lignes du tableau ci-dessous (sites 🔴 réels, numéros relus).\n"
            "- [x] C6 Contrat outil externe — preuve : docs/sorties-automatiques.md:17-18, "
            "Contrat de slack_post.post non lu (non vérifié). Contrat natif « stdout d'un cron = livré par Hermes » : "
            "seulement la doc du repo (docs/sorties-automatiques.md:36-38), cron.md natif non lu.\n"
        )
        resultat = self._lancer(fiche, liste=liste)
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertEqual(resultat.stdout.splitlines(), ["preuve partielle : C6"], resultat.stdout)

    def test_preuve_sans_marqueur_non_signalee(self) -> None:
        # Ligne C0 réelle : cochée, preuve sans « non vérifié ». Rien à signaler.
        liste = self._ecrire("liste_c0.md", LISTE_C0)
        fiche = ("- [x] C0 Objets touchés — preuve : les 54 lignes du tableau ci-dessous "
                 "(sites 🔴 réels, numéros relus).\n")
        resultat = self._lancer(fiche, liste=liste)
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertEqual(resultat.stdout, "", resultat.stdout)

    def test_code_1_avec_preuve_partielle_sur_la_sortie(self) -> None:
        # Défaut sur C0 (cochée sans « — preuve : ») et preuve partielle sur C6 dans la même fiche :
        # code 1, et la sortie porte les deux lignes, le défaut d'abord, puis la preuve partielle.
        liste = self._ecrire("liste_c0_c6_bis.md", LISTE_C0_C6)
        fiche = (
            "- [x] C0 Objets touchés\n"
            "- [x] C6 Contrat outil externe — preuve : Contrat de slack_post.post non lu (non vérifié).\n"
        )
        resultat = self._lancer(fiche, liste=liste)
        self.assertEqual(resultat.returncode, 1, resultat.stderr)
        lignes = resultat.stdout.splitlines()
        self.assertEqual(len(lignes), 2, resultat.stdout)
        self.assertTrue(lignes[0].startswith("C0 cochée sans preuve"), lignes[0])
        self.assertEqual(lignes[1], "preuve partielle : C6", resultat.stdout)


if __name__ == "__main__":
    unittest.main()
