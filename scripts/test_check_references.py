"""Tests du contrôle de frontmatter de ``check_references.py``.

Lancés par la CI (``python3 -m unittest discover -s scripts``), sans
dépendance : ``unittest`` est dans la bibliothèque standard.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_references import erreurs_yaml_scalaires  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
