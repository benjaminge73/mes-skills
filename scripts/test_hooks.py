"""Tests des hooks ``PreToolUse`` du plugin plans-notion.

Chaque hook est lancé en vrai sous-processus, avec un JSON figé sur stdin,
comme Claude Code le fait : on observe le code de sortie et le message.
Contrat : refus = code 2 et motif sur stderr ; permis = code 0 sans sortie ;
entrée illisible = code 0 (un garde-fou cassé ne bloque aucune session).
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "plans-notion" / "hooks"
OUTIL_UPDATE = "mcp__claude_ai_Notion__notion-update-page"
OUTIL_CREATE = "mcp__claude_ai_Notion__notion-create-pages"


def jouer(script: str, entree) -> subprocess.CompletedProcess:
    brut = entree if isinstance(entree, str) else json.dumps(entree)
    return subprocess.run([sys.executable, str(HOOKS / script)], input=brut,
                          capture_output=True, text=True, timeout=30)


def bash(commande: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": commande}}


class RefuserNoVerify(unittest.TestCase):
    SCRIPT = "refuser_no_verify.py"

    def refuse(self, commande: str):
        r = jouer(self.SCRIPT, bash(commande))
        self.assertEqual(r.returncode, 2, f"{commande!r} aurait dû être refusée : {r.stderr}")
        self.assertIn("--no-verify", r.stderr)

    def permis(self, commande: str):
        r = jouer(self.SCRIPT, bash(commande))
        self.assertEqual(r.returncode, 0, f"{commande!r} aurait dû passer : {r.stderr}")
        self.assertEqual(r.stdout + r.stderr, "")

    def test_un_commit_avec_no_verify_est_refuse_avec_le_motif(self):
        self.refuse('git commit --no-verify -m "x"')

    def test_un_commit_avec_n_court_est_refuse(self):
        self.refuse('git commit -n -m "x"')

    def test_les_options_groupees_nm_sont_refusees(self):
        self.refuse('git commit -nm "x"')

    def test_git_dash_C_commit_no_verify_est_refuse(self):
        self.refuse('git -C /tmp/depot commit --no-verify -m "x"')

    def test_no_verify_apres_une_chaine_est_refuse(self):
        self.refuse('git add -A && git commit --no-verify -m "x"')

    def test_S_sans_keyid_ne_masque_pas_le_n_suivant(self):
        # -S a une valeur facultative, collée : le mot suivant n'est pas sa valeur.
        self.refuse('git commit -S -n -m "x"')

    def test_gpg_sign_sans_valeur_ne_masque_pas_no_verify(self):
        self.refuse('git commit --gpg-sign --no-verify -m "x"')

    def test_S_colle_a_un_keyid_contenant_n_est_permis(self):
        self.permis('git commit -Sabcn -m "x"')

    def test_un_commit_ordinaire_est_permis(self):
        self.permis('git commit -m "x"')

    def test_n_dans_le_texte_du_message_est_permis(self):
        self.permis('git commit -m "ajoute -n"')

    def test_no_verify_dans_le_texte_du_message_est_permis(self):
        self.permis('git commit -m "retire --no-verify du script"')

    def test_n_d_une_autre_commande_git_est_permis(self):
        self.permis("git log -n 3")

    def test_un_outil_autre_que_bash_est_ignore(self):
        r = jouer(self.SCRIPT, {"tool_name": "Read", "tool_input": {"command": "git commit -n"}})
        self.assertEqual(r.returncode, 0)

    def test_une_commande_non_decoupable_laisse_passer(self):
        r = jouer(self.SCRIPT, bash('git commit -m "guillemet jamais fermé'))
        self.assertEqual(r.returncode, 0)

    def test_un_json_illisible_laisse_passer_avec_un_mot_sur_stderr(self):
        r = jouer(self.SCRIPT, "pas du json {")
        self.assertEqual(r.returncode, 0)
        self.assertNotEqual(r.stderr.strip(), "")


class RefuserStatutAccentue(unittest.TestCase):
    SCRIPT = "refuser_statut_accentue.py"

    def update(self, statut, nom="Statut"):
        return {"tool_name": OUTIL_UPDATE,
                "tool_input": {"page_id": "x", "command": "update_properties",
                               "properties": {nom: statut}}}

    def create(self, statut):
        return {"tool_name": OUTIL_CREATE,
                "tool_input": {"pages": [{"properties": {"Titre": "t", "Statut": statut}}]}}

    def test_un_statut_accentue_en_mise_a_jour_est_refuse_avec_les_valeurs_admises(self):
        r = jouer(self.SCRIPT, self.update("exécuté"))
        self.assertEqual(r.returncode, 2)
        for valeur in ("brouillon", "en revue", "valide", "en cours", "a merger", "execute", "archive"):
            self.assertIn(valeur, r.stderr)

    def test_un_statut_accentue_en_creation_est_refuse(self):
        r = jouer(self.SCRIPT, self.create("validé"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("Statut", r.stderr)

    def test_un_statut_sans_accent_est_permis(self):
        for valeur in ("execute", "a merger", "en revue"):
            r = jouer(self.SCRIPT, self.update(valeur))
            self.assertEqual(r.returncode, 0, valeur)
            self.assertEqual(r.stdout + r.stderr, "")
        self.assertEqual(jouer(self.SCRIPT, self.create("brouillon")).returncode, 0)

    def test_toute_valeur_de_plan_accentuee_est_refusee(self):
        for valeur in ("à merger", "archivé", "Exécuté", "  validé "):
            r = jouer(self.SCRIPT, self.update(valeur))
            self.assertEqual(r.returncode, 2, valeur)

    def test_un_statut_accentue_d_une_autre_base_est_permis(self):
        # Une base qui n'est pas Plans Claude (fiches de cours : « prête », « à rejouer »)
        # a le droit d'avoir ses propres valeurs accentuées dans un champ « Statut ».
        for valeur in ("prête", "à rejouer", "à préparer"):
            r = jouer(self.SCRIPT, self.update(valeur))
            self.assertEqual(r.returncode, 0, f"{valeur!r} : {r.stderr}")
            self.assertEqual(r.stdout + r.stderr, "")
        self.assertEqual(jouer(self.SCRIPT, self.create("prête")).returncode, 0)

    def test_un_accent_dans_une_autre_propriete_est_permis(self):
        r = jouer(self.SCRIPT, self.update("é accentué", nom="Résumé"))
        self.assertEqual(r.returncode, 0)

    def test_une_mise_a_jour_sans_propriete_est_permise(self):
        r = jouer(self.SCRIPT, {"tool_name": OUTIL_UPDATE,
                                "tool_input": {"page_id": "x", "command": "replace_content"}})
        self.assertEqual(r.returncode, 0)

    def test_un_json_illisible_laisse_passer_avec_un_mot_sur_stderr(self):
        r = jouer(self.SCRIPT, "")
        self.assertEqual(r.returncode, 0)
        self.assertNotEqual(r.stderr.strip(), "")


if __name__ == "__main__":
    unittest.main()
