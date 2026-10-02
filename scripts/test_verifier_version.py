"""Tests de ``verifier-version.sh`` : la garde « Suis-je la bonne version ? ».

Le script compare la version et le chemin du plugin **chargé** (la racine passée
en argument) à ce que ``installed_plugins.json`` dit d'installé. Écart de version
ou de chemin : code 1 et un message qui dit l'écart et le geste. Fichier
introuvable : code 2, distinct, pour qu'on ne prenne pas une panne de lecture pour
un écart. Chaque cas fabrique son ``installed_plugins.json`` (variable
``INSTALLED_PLUGINS_JSON``) : aucun test ne lit le vrai ``~/.claude``.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "verifier-version.sh"


class VerifierVersion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def _plugin(self, version, nom="charge"):
        racine = self.dossier / nom
        (racine / ".claude-plugin").mkdir(parents=True)
        (racine / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "plans-notion", "version": version}, indent=2) + "\n")
        return racine

    def _installe(self, version, chemin):
        fichier = self.dossier / "installed_plugins.json"
        fichier.write_text(json.dumps({"version": 2, "plugins": {
            "plans-notion@atelier": [{"scope": "user", "version": version,
                                      "installPath": str(chemin)}]}}))
        return fichier

    def _jouer(self, racine, installed):
        env = dict(os.environ, INSTALLED_PLUGINS_JSON=str(installed))
        r = subprocess.run(["bash", str(SCRIPT), str(racine)], env=env,
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def test_meme_version_et_meme_chemin_est_a_jour(self):
        racine = self._plugin("0.18.0")
        code, sortie = self._jouer(racine, self._installe("0.18.0", racine))
        self.assertEqual(code, 0, sortie)
        self.assertIn("à jour", sortie)

    def test_deux_versions_differentes_rendent_un_code_non_nul_et_un_message(self):
        racine = self._plugin("0.3.0", "copie-perimee")
        installe = self.dossier / "installe"
        code, sortie = self._jouer(racine, self._installe("0.7.0", installe))
        self.assertEqual(code, 1, sortie)
        self.assertIn("0.3.0", sortie)
        self.assertIn("0.7.0", sortie)
        self.assertIn("claude plugin update plans-notion@atelier", sortie)

    def test_meme_version_mais_chemin_charge_different_de_l_install_path(self):
        racine = self._plugin("0.18.0", "copie-synchronisee")
        code, sortie = self._jouer(racine, self._installe("0.18.0", self.dossier / "ailleurs"))
        self.assertEqual(code, 1, sortie)
        self.assertIn(str(self.dossier / "ailleurs"), sortie)

    def test_installed_plugins_introuvable_rend_un_code_distinct(self):
        racine = self._plugin("0.18.0")
        code, sortie = self._jouer(racine, self.dossier / "absent.json")
        self.assertEqual(code, 2, sortie)
        self.assertIn("installed_plugins.json", sortie)

    def test_plugin_json_introuvable_rend_un_code_distinct(self):
        racine = self.dossier / "vide"
        racine.mkdir()
        code, sortie = self._jouer(racine, self._installe("0.18.0", racine))
        self.assertEqual(code, 2, sortie)
        self.assertIn("plugin.json", sortie)


if __name__ == "__main__":
    unittest.main()
