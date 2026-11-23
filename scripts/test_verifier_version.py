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

    def _url_main(self, contenu):
        """Fabrique le plugin.json « main » et rend son URL file:// (curl la lit)."""
        fichier = self.dossier / "main" / ".claude-plugin" / "plugin.json"
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(contenu)
        return fichier.as_uri()

    def _main(self, version):
        return self._url_main(json.dumps({"name": "plans-notion", "version": version}))

    def _jouer(self, racine, installed, main_url=""):
        # Par défaut la vérification réseau est désactivée : les tests restent hors réseau.
        env = dict(os.environ, INSTALLED_PLUGINS_JSON=str(installed), PLUGIN_MAIN_URL=main_url)
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

    def test_copie_installee_plus_ancienne_que_main_rend_un_code_1_et_la_commande(self):
        racine = self._plugin("0.62.1")
        code, sortie = self._jouer(racine, self._installe("0.62.1", racine),
                                   main_url=self._main("0.75.0"))
        self.assertEqual(code, 1, sortie)
        self.assertIn("0.62.1", sortie)
        self.assertIn("0.75.0", sortie)
        self.assertIn("en retard", sortie)
        self.assertIn("claude plugin update plans-notion@atelier", sortie)

    def test_copie_a_jour_sur_main_est_a_jour(self):
        racine = self._plugin("0.75.0")
        code, sortie = self._jouer(racine, self._installe("0.75.0", racine),
                                   main_url=self._main("0.75.0"))
        self.assertEqual(code, 0, sortie)
        self.assertIn("à jour", sortie)

    def test_installee_plus_recente_que_main_ne_previent_pas(self):
        # Garde contre une comparaison de simple différence de chaînes : une copie
        # plus neuve que main (branche pas encore fusionnée) n'est pas « en retard ».
        racine = self._plugin("0.80.0")
        code, sortie = self._jouer(racine, self._installe("0.80.0", racine),
                                   main_url=self._main("0.75.0"))
        self.assertEqual(code, 0, sortie)
        self.assertNotIn("en retard", sortie)

    def test_main_injoignable_reste_silencieuse_et_ne_change_pas_le_code(self):
        racine = self._plugin("0.75.0")
        absent = (self.dossier / "n-existe-pas.json").as_uri()
        code, sortie = self._jouer(racine, self._installe("0.75.0", racine), main_url=absent)
        self.assertEqual(code, 0, sortie)
        self.assertNotIn("en retard", sortie)

    def test_main_au_contenu_non_json_reste_silencieuse(self):
        racine = self._plugin("0.62.1")
        non_json = self._url_main("<html>page d'erreur</html>")
        code, sortie = self._jouer(racine, self._installe("0.62.1", racine), main_url=non_json)
        self.assertEqual(code, 0, sortie)
        self.assertNotIn("en retard", sortie)

    def test_ecart_local_et_copie_en_retard_se_cumulent_dans_un_message(self):
        racine = self._plugin("0.3.0", "copie-perimee")
        code, sortie = self._jouer(racine, self._installe("0.62.1", self.dossier / "installe"),
                                   main_url=self._main("0.75.0"))
        self.assertEqual(code, 1, sortie)
        self.assertIn("0.3.0", sortie)
        self.assertIn("en retard", sortie)

    def test_comparaison_de_versions_numerique_et_non_alphabetique(self):
        # Alphabétiquement « 0.10.0 » < « 0.9.0 » : une comparaison de chaînes ne verrait
        # aucun retard. Numériquement 0.10.0 > 0.9.0, donc la copie 0.9.0 est en retard.
        racine = self._plugin("0.9.0")
        code, sortie = self._jouer(racine, self._installe("0.9.0", racine),
                                   main_url=self._main("0.10.0"))
        self.assertEqual(code, 1, sortie)
        self.assertIn("en retard", sortie)


if __name__ == "__main__":
    unittest.main()
