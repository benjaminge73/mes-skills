"""Tests du hook ``UserPromptSubmit`` du plugin nommage-sessions.

Le hook est lancé en vrai sous-processus, avec un JSON figé sur stdin, comme
Claude Code le fait. Haiku est remplacé par un faux ``claude`` placé en tête du
PATH, qui note chacun de ses appels : on vérifie le titre rendu et le nombre
d'appels, sans jamais joindre l'API.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] / "plugins" / "nommage-sessions"
          / "hooks" / "nommer_session.py")


class NommerSession(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.depot = self.tmp / "mon-projet"
        self.depot.mkdir()
        subprocess.run(["git", "init", "-q", str(self.depot)], check=True)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.appels = self.tmp / "appels"
        self.data = self.tmp / "data"
        self.faux_claude("echo 'Plugin de nommage.'")

    def faux_claude(self, corps: str):
        chemin = self.bin / "claude"
        chemin.write_text(f"#!/bin/sh\necho x >> '{self.appels}'\n{corps}\n")
        chemin.chmod(0o755)

    def nb_appels(self) -> int:
        return len(self.appels.read_text().splitlines()) if self.appels.exists() else 0

    def jouer(self, entree, env_en_plus=None) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items()
               if k not in ("NOMMAGE_SESSIONS_INTERNE", "CLAUDE_CODE_REMOTE")}
        env.update(NOMMAGE_SESSIONS_LIEU="VPS", PATH=f"{self.bin}:{os.environ['PATH']}",
                   CLAUDE_PLUGIN_DATA=str(self.data))
        env.update(env_en_plus or {})
        brut = entree if isinstance(entree, str) else json.dumps(entree)
        return subprocess.run([sys.executable, str(SCRIPT)], input=brut, env=env,
                              capture_output=True, text=True, timeout=30)

    def entree(self, **champs) -> dict:
        base = {"session_id": "s1", "prompt": "crée un plugin de nommage",
                "cwd": str(self.depot), "hook_event_name": "UserPromptSubmit"}
        base.update(champs)
        return base

    def titre_rendu(self, r) -> str | None:
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return None
        return json.loads(r.stdout)["hookSpecificOutput"]["sessionTitle"]

    def test_un_titre_sans_prefixe_est_prefixe_du_nom_du_depot(self):
        r = self.jouer(self.entree(session_title="Refonte auth"))
        self.assertEqual(self.titre_rendu(r), "[Mon-projet - VPS] Refonte auth")
        self.assertEqual(self.nb_appels(), 0)

    def test_un_titre_deja_prefixe_n_est_pas_touche(self):
        r = self.jouer(self.entree(session_title="[autre] Refonte auth"))
        self.assertIsNone(self.titre_rendu(r))

    def test_sans_titre_haiku_donne_le_sujet_une_seule_fois(self):
        r = self.jouer(self.entree())
        self.assertEqual(self.titre_rendu(r), "[Mon-projet - VPS] Plugin de nommage")
        r = self.jouer(self.entree(prompt="et ensuite ?"))
        self.assertIsNone(self.titre_rendu(r))
        self.assertEqual(self.nb_appels(), 1)

    def test_haiku_en_echec_puis_titre_genere_lu_dans_le_transcript(self):
        self.faux_claude("echo 'Failed to authenticate' >&2; exit 1")
        self.assertIsNone(self.titre_rendu(self.jouer(self.entree())))
        transcript = self.tmp / "t.jsonl"
        transcript.write_text(json.dumps({"type": "user"}) + "\n" + json.dumps(
            {"type": "ai-title", "aiTitle": "Nommage des sessions", "sessionId": "s1"}) + "\n")
        r = self.jouer(self.entree(prompt="suite", transcript_path=str(transcript)))
        self.assertEqual(self.titre_rendu(r), "[Mon-projet - VPS] Nommage des sessions")
        self.assertEqual(self.nb_appels(), 1)

    def test_une_commande_slash_n_appelle_pas_haiku_ni_ne_consomme_l_essai(self):
        self.assertIsNone(self.titre_rendu(self.jouer(self.entree(prompt="/caveman"))))
        self.assertEqual(self.nb_appels(), 0)
        r = self.jouer(self.entree())
        self.assertEqual(self.titre_rendu(r), "[Mon-projet - VPS] Plugin de nommage")

    def test_un_worktree_porte_le_nom_du_depot(self):
        subprocess.run(["git", "-C", str(self.depot), "-c", "user.name=t", "-c",
                        "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "i"], check=True)
        wt = self.tmp / "dossier-du-worktree"
        subprocess.run(["git", "-C", str(self.depot), "worktree", "add", "-q", str(wt)], check=True)
        r = self.jouer(self.entree(cwd=str(wt), session_title="Sujet"))
        self.assertEqual(self.titre_rendu(r), "[Mon-projet - VPS] Sujet")

    def test_le_projet_vient_du_remote_origin_meme_si_le_dossier_a_un_autre_nom(self):
        for url in ("git@github.com:benjaminge73/vahiny.git",
                    "https://github.com/benjaminge73/vahiny",
                    "http://local_proxy@127.0.0.1:41234/git/benjaminge73/vahiny"):
            subprocess.run(["git", "-C", str(self.depot), "remote", "remove", "origin"],
                           capture_output=True)
            subprocess.run(["git", "-C", str(self.depot), "remote", "add", "origin", url], check=True)
            r = self.jouer(self.entree(session_title="Sujet"))
            self.assertEqual(self.titre_rendu(r), "[Vahiny - VPS] Sujet", url)

    def test_un_alias_remplace_le_nom_du_depot(self):
        subprocess.run(["git", "-C", str(self.depot), "remote", "add", "origin",
                        "https://github.com/benjaminge73/hermes-custom"], check=True)
        self.data.mkdir()
        (self.data / "alias.json").write_text(json.dumps({"hermes-custom": "Hermes"}))
        r = self.jouer(self.entree(session_title="Sujet"))
        self.assertEqual(self.titre_rendu(r), "[Hermes - VPS] Sujet")

    def test_le_lieu_suit_la_machine(self):
        env = {"NOMMAGE_SESSIONS_LIEU": ""}
        r = self.jouer(self.entree(session_title="Sujet"), env_en_plus={**env, "CLAUDE_CODE_REMOTE": "true"})
        self.assertEqual(self.titre_rendu(r), "[Mon-projet - Cloud] Sujet")
        sys_darwin = subprocess.run(
            [sys.executable, "-c", "import platform;print(platform.system())"],
            capture_output=True, text=True).stdout.strip()
        attendu = "Mac" if sys_darwin == "Darwin" else "VPS"
        r = self.jouer(self.entree(session_title="Sujet"), env_en_plus=env)
        self.assertEqual(self.titre_rendu(r), f"[Mon-projet - {attendu}] Sujet")

    def test_hors_depot_le_nom_du_dossier(self):
        dossier = self.tmp / "pas-un-depot"
        dossier.mkdir()
        r = self.jouer(self.entree(cwd=str(dossier), session_title="Sujet"))
        self.assertEqual(self.titre_rendu(r), "[Pas-un-depot - VPS] Sujet")

    def test_une_entree_illisible_laisse_passer_sans_rien_dire(self):
        r = self.jouer("pas du json")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_l_appel_interne_a_haiku_ne_relance_pas_le_hook(self):
        r = self.jouer(self.entree(), env_en_plus={"NOMMAGE_SESSIONS_INTERNE": "1"})
        self.assertIsNone(self.titre_rendu(r))
        self.assertEqual(self.nb_appels(), 0)


if __name__ == "__main__":
    unittest.main()
