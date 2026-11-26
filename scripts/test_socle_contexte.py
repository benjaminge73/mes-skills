"""Tests de ``socle-contexte.py`` : le premier appel, le socle, et la taille des pièces du démarrage.

Les journaux sont des ``.jsonl`` écrits dans un dossier temporaire, au format de Claude Code
(une ligne par événement, deux lignes par appel avec le même ``message.id``). Le script tourne
en sous-processus, comme ``test_preparation_prete.py``, et l'on observe sa sortie ``--json``
et son code retour.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "socle-contexte.py"

SESSION = "76b598b9-b9a4-4e2e-8099-95ab6cd26361"


def appel(mid: str, creation: int, lecture: int, entree: int = 2) -> list[dict]:
    """Un appel du modèle : deux lignes ``assistant`` de même ``message.id`` et même usage.

    Le contexte de l'appel est la somme des trois compteurs d'entrée.
    """
    usage = {
        "input_tokens": entree,
        "cache_creation_input_tokens": creation,
        "cache_read_input_tokens": lecture,
        "output_tokens": 300,
    }
    ligne = {
        "type": "assistant",
        "version": "2.1.0",
        "timestamp": "2026-11-20T10:00:00Z",
        "message": {"id": mid, "usage": usage},
    }
    return [ligne, dict(ligne)]


def piece(type_: str, **champs) -> dict:
    return {"type": "attachment", "version": "2.1.0", "attachment": {"type": type_, **champs}}


def delta_outils(noms: list[str]) -> dict:
    return piece("deferred_tools_delta", addedNames=noms, addedLines=[f"- {n}" for n in noms])


def compaction() -> dict:
    return {"type": "system", "subtype": "compact_boundary", "version": "2.1.0"}


def noms_du_demarrage() -> list[str]:
    """699 noms : 500 du serveur alpha, 150 du serveur beta, 45 de plugin_design_figma, 4 natifs."""
    noms = [f"mcp__alpha__outil_{i}" for i in range(500)]
    noms += [f"mcp__beta__outil_{i}" for i in range(150)]
    noms += [f"mcp__plugin_design_figma__outil_{i}" for i in range(45)]
    noms += ["Monitor", "TaskStop", "WebSearch", "ArtifactComments"]
    assert len(noms) == 699
    return noms


def journal_demarrage() -> list[dict]:
    # Premier appel : 2 + 58317 + 25473 = 83792. Delta de 699 noms après lui.
    # Socle : 2 + 24528 + 83790 = 108320, premier appel qui suit le delta.
    return (
        appel("msg_1", 58317, 25473)
        + [delta_outils(noms_du_demarrage())]
        + appel("msg_2", 24528, 83790)
    )


def ecrire_session(dossier: Path, lignes: list[dict]) -> None:
    projet = dossier / "-home-ubuntu-depot-exemple"
    projet.mkdir(parents=True, exist_ok=True)
    with (projet / f"{SESSION}.jsonl").open("w", encoding="utf-8") as f:
        for ligne in lignes:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")


def lancer(dossier: Path, *args: str) -> subprocess.CompletedProcess:
    assert SCRIPT.is_file(), f"socle-contexte.py absent : {SCRIPT}"
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--projets", str(dossier), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class SocleContexte(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dossier = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def rendu_json(self) -> dict:
        r = lancer(self.dossier, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_socle_pris_apres_le_delta_et_non_au_premier_appel(self):
        ecrire_session(self.dossier, journal_demarrage())
        session = self.rendu_json()["sessions"][0]
        self.assertEqual(session["premier_appel"], 83792)
        self.assertEqual(session["socle"], 108320)

    def test_noms_du_delta_comptes_par_serveur(self):
        ecrire_session(self.dossier, journal_demarrage())
        delta = self.rendu_json()["sessions"][0]["pieces"]["deferred_tools_delta"]
        self.assertEqual(delta["noms"], 699)
        self.assertEqual(
            delta["par_serveur"],
            {"alpha": 500, "beta": 150, "plugin_design_figma": 45},
        )
        self.assertEqual(delta["natifs"], 4)

    def test_aucun_journal_lisible_rend_le_code_2(self):
        # Dossier vide : rien à lire. Le message dit « journal », pas une trace Python.
        r = lancer(self.dossier, "--json")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("journal", r.stderr.lower())
        self.assertNotIn("Traceback", r.stderr)

    def test_piece_arrivee_apres_compaction_ignoree(self):
        # Le delta B arrive après une compaction : ce n'est pas une pièce de démarrage.
        # Le socle reste le premier appel qui suit le delta A, et seul A compte.
        ecrire_session(
            self.dossier,
            appel("msg_1", 58317, 25473)
            + [delta_outils(["mcp__alpha__outil_0"])]
            + appel("msg_2", 24528, 83790)
            + [compaction()]
            + [delta_outils([f"mcp__beta__outil_{i}" for i in range(734)])]
            + appel("msg_3", 1000, 40000),
        )
        session = self.rendu_json()["sessions"][0]
        self.assertEqual(session["socle"], 108320)
        self.assertEqual(session["pieces"]["deferred_tools_delta"]["noms"], 1)


if __name__ == "__main__":
    unittest.main()
