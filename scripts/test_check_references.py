"""Tests des contrôles de ``check_references.py`` : frontmatter et renvois de phase.

Lancés par la CI (``python3 -m unittest discover -s scripts``), sans
dépendance : ``unittest`` est dans la bibliothèque standard.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_references import (  # noqa: E402
    erreurs_yaml_scalaires,
    phases_absentes,
    renvois_phase,
)


class ErreursYamlScalaires(unittest.TestCase):
    def test_deux_points_espace_dans_une_valeur_nue_casse_le_yaml(self):
        # Cas réel du 2026-09-23 : l'agent relecteur se serait chargé sans
        # aucune métadonnée (ni model, ni effort, ni disallowedTools).
        bloc = [
            "name: relecteur",
            "description: Rend un verdict classé dans trois catégories qui "
            "justifient son existence : écart au plan, bug de correction.",
        ]
        erreurs = erreurs_yaml_scalaires(bloc)
        self.assertEqual(len(erreurs), 1)
        self.assertIn("description", erreurs[0])

    def test_une_valeur_nue_ne_peut_pas_commencer_par_un_accent_grave(self):
        bloc = ["description: `RIEN À SIGNALER` ou `REMARQUES (n)`"]
        self.assertEqual(len(erreurs_yaml_scalaires(bloc)), 1)

    def test_diese_precede_d_un_espace_coupe_la_valeur_en_commentaire(self):
        bloc = ["description: le geste #13 et le geste suivant"]
        self.assertEqual(len(erreurs_yaml_scalaires(bloc)), 1)

    def test_une_valeur_entre_guillemets_peut_tout_contenir(self):
        bloc = [
            'description: "trois catégories : écart, bug, test # vide"',
            "name: 'x: y'",
        ]
        self.assertEqual(erreurs_yaml_scalaires(bloc), [])

    def test_listes_blocs_et_tirets_ne_sont_pas_des_valeurs_nues(self):
        bloc = [
            "model: opus",
            "disallowedTools:",
            "  - Edit",
            "  - Write",
            "description: >",
            "  suite : sur plusieurs lignes, où tout est permis",
            "tools: [Read, Grep]",
            "effort: low",
        ]
        self.assertEqual(erreurs_yaml_scalaires(bloc), [])

    def test_deux_points_colles_et_url_restent_valides(self):
        bloc = [
            "description: voir https://code.claude.com/docs et le ratio 3:1",
        ]
        self.assertEqual(erreurs_yaml_scalaires(bloc), [])


class RenvoisDePhase(unittest.TestCase):
    def test_renvoi_vers_une_phase_existante_est_accepte_meme_avant_son_titre(self):
        # Un skill cite « Phase 1 » dans son introduction, avant le titre :
        # une lecture en une passe la refuserait à tort.
        lignes = [
            "Si la Phase 1 n'est pas finie, ne pas proposer de correctif.",
            "",
            "### Phase 1: Enquête",
            "",
            "### Phase 2: Analyse",
            "Passer à la Phase 2 une fois l'enquête close.",
        ]
        self.assertEqual(phases_absentes(lignes), [])
        self.assertEqual(len(renvois_phase(lignes)), 2)

    def test_phase_4_5_absente_est_refusee_meme_si_la_phase_4_existe(self):
        # Une lecture qui tronquerait « 4.5 » à « 4 » accepterait ce renvoi,
        # puisque la phase 4 existe : le numéro décimal doit être lu entier.
        lignes = [
            "### Phase 1: Enquête",
            "### Phase 4: Mise en œuvre",
            "",
            "Voir la Phase 4.5 pour la suite.",
        ]
        self.assertEqual(phases_absentes(lignes), [(4, "4.5")])

    def test_fichier_sans_titre_phase_est_ignore(self):
        # Sans aucun titre « Phase N », la mention est une formule libre :
        # rien à désigner, donc aucun renvoi à juger.
        lignes = [
            "Voir la Phase 4.5 du plan, puis la Phase 9.",
            "## Titre ordinaire",
            "Phase 2 dans la prose, pas dans un titre.",
        ]
        self.assertEqual(phases_absentes(lignes), [])
        self.assertEqual(renvois_phase(lignes), [])


if __name__ == "__main__":
    unittest.main()
