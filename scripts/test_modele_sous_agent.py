"""Tests de ``modele-sous-agent.py`` : le modèle réel d'un sous-agent contre sa définition.

Le cas qui justifie le script (2026-10-08) : `plans-notion` mis à jour en
0.20.0 (`model: haiku`), session non rechargée, executants partis en Sonnet sur
la définition 0.19.1. La transcription disait `claude-sonnet-5-5`, rien d'autre.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "modele-sous-agent.py"
EXECUTANT = RACINE / "plugins" / "plans-notion" / "agents" / "executant.md"


def jouer(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def ligne(role, modele=None):
    m = {"role": role, "content": "x"}
    if modele:
        m["model"] = modele
    return json.dumps({"type": role, "message": m})


class ModeleSousAgent(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name)
        self.sub = self.racine / "projects" / "-home-x" / "sess-1" / "subagents"
        self.sub.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def poser(self, agent_id, *lignes):
        (self.sub / f"agent-{agent_id}.jsonl").write_text("\n".join(lignes) + "\n", encoding="utf-8")

    def definition(self, modele):
        f = self.racine / "agent.md"
        entete = f"model: {modele}\n" if modele else ""
        f.write_text(f"---\nname: x\n{entete}effort: high\n---\n\n# Corps\nmodel: opus\n", encoding="utf-8")
        return f

    def test_sans_definition_imprime_les_modeles_vus(self):
        self.poser("a1", ligne("user"), ligne("assistant", "claude-haiku-5-5"),
                   ligne("assistant", "claude-haiku-5-5"))
        code, sortie, _ = jouer("a1", "--racine", self.racine)
        self.assertEqual(code, 0)
        self.assertIn("2 × claude-haiku-5-5", sortie)

    def test_conforme_quand_l_alias_correspond(self):
        self.poser("a1", ligne("assistant", "claude-haiku-5-5"))
        code, sortie, _ = jouer("a1", "--racine", self.racine, "--definition", self.definition("haiku"))
        self.assertEqual(code, 0, sortie)
        self.assertIn("conforme", sortie)

    def test_ecart_quand_la_session_a_garde_l_ancienne_definition(self):
        # Le cas réel : frontmatter haiku sur le disque, sous-agent parti en Sonnet.
        self.poser("a1", ligne("assistant", "claude-sonnet-5-5"), ligne("assistant", "claude-sonnet-5-5"))
        code, sortie, _ = jouer("a1", "--racine", self.racine, "--definition", self.definition("haiku"))
        self.assertEqual(code, 1)
        self.assertIn("ÉCART", sortie)
        self.assertIn("claude-sonnet-5-5", sortie)
        self.assertIn("session neuve", sortie)

    def test_un_seul_appel_hors_modele_suffit_a_l_ecart(self):
        self.poser("a1", ligne("assistant", "claude-haiku-5-5"), ligne("assistant", "claude-opus-5-5"))
        code, _, _ = jouer("a1", "--racine", self.racine, "--definition", self.definition("haiku"))
        self.assertEqual(code, 1)

    def test_identifiant_complet_et_fournisseur_tiers(self):
        self.poser("a1", ligne("assistant", "us.anthropic.claude-haiku-4-5-20251001-v1:0"))
        code, _, _ = jouer("a1", "--racine", self.racine, "--definition", self.definition("haiku"))
        self.assertEqual(code, 0)
        self.poser("a2", ligne("assistant", "claude-sonnet-5-5"))
        code, _, _ = jouer("a2", "--racine", self.racine, "--definition", self.definition("claude-sonnet-5-5"))
        self.assertEqual(code, 0)

    def test_le_model_du_corps_n_est_pas_lu(self):
        # Seul le frontmatter compte : « model: opus » dans le corps ne doit pas répondre.
        self.poser("a1", ligne("assistant", "claude-opus-5-5"))
        code, _, _ = jouer("a1", "--racine", self.racine, "--definition", self.definition(None))
        self.assertEqual(code, 2)

    def test_transcription_introuvable_et_modeles_synthetiques(self):
        code, _, err = jouer("absent", "--racine", self.racine)
        self.assertEqual(code, 2)
        self.assertIn("introuvable", err)
        self.poser("a1", ligne("user"), ligne("assistant", "<synthetic>"))
        code, _, err = jouer("a1", "--racine", self.racine)
        self.assertEqual(code, 2)
        self.assertIn("aucun modèle", err)

    def test_accepte_l_identifiant_avec_son_prefixe(self):
        self.poser("a1", ligne("assistant", "claude-haiku-5-5"))
        code, _, _ = jouer("agent-a1", "--racine", self.racine)
        self.assertEqual(code, 0)

    def installer(self, version, modele):
        racine_plugin = self.racine / "plugins" / "cache" / "atelier" / "plans-notion" / version
        (racine_plugin / "agents").mkdir(parents=True)
        (racine_plugin / "agents" / "executant.md").write_text(
            f"---\nname: executant\nmodel: {modele}\n---\n", encoding="utf-8")
        (self.racine / "plugins" / "installed_plugins.json").write_text(json.dumps(
            {"plugins": {"plans-notion@atelier": [{"version": version, "installPath": str(racine_plugin)}]}}),
            encoding="utf-8")

    def test_agent_lu_dans_la_version_installee(self):
        # La session a gardé 0.19.1 (sonnet) ; l'installé est 0.20.0 (haiku) : écart.
        self.installer("0.20.0", "haiku")
        self.poser("a1", ligne("assistant", "claude-sonnet-5-5"))
        code, sortie, _ = jouer("a1", "--racine", self.racine, "--agent", "plans-notion:executant")
        self.assertEqual(code, 1, sortie)
        self.poser("a2", ligne("assistant", "claude-haiku-5-5"))
        code, sortie, _ = jouer("a2", "--racine", self.racine, "--agent", "plans-notion:executant")
        self.assertEqual(code, 0, sortie)

    def test_agent_d_un_plugin_non_installe(self):
        self.poser("a1", ligne("assistant", "claude-haiku-5-5"))
        code, _, err = jouer("a1", "--racine", self.racine, "--agent", "plans-notion:executant")
        self.assertEqual(code, 2)
        self.assertIn("non installé", err)

    def test_la_vraie_definition_de_l_executant_se_lit(self):
        self.poser("a1", ligne("assistant", "claude-haiku-5-5"))
        code, sortie, err = jouer("a1", "--racine", self.racine, "--definition", EXECUTANT)
        self.assertEqual(code, 0, sortie + err)


if __name__ == "__main__":
    unittest.main()
