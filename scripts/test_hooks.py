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
import tempfile
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


def exit_plan_mode(plan: str) -> dict:
    return {"tool_name": "ExitPlanMode", "tool_input": {"plan": plan}}


def entree_fichier_de_plan(chemin: str) -> dict:
    return {"tool_name": "ExitPlanMode", "tool_input": {"planFilePath": chemin}}


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


PLAN_SANS_NOTION = "## Plan\n1. Étape un\n2. Étape deux"


class RappelDelegationApresExitPlanMode(unittest.TestCase):
    """Hook PostToolUse sur ExitPlanMode : rappel de déléguer, jamais bloquant.

    Le texte du plan vient de ``tool_input.plan``, sinon du fichier
    ``planFilePath`` (dans ``tool_input`` ou ``tool_response``). Les témoins des
    tests (b) et (d) — le même plan sans URL rend le rappel — sont là pour que le
    silence du cas Notion ne soit pas gagné par un script muet.
    """
    SCRIPT = "rappel_delegation.py"

    def test_un_plan_sans_url_notion_rend_le_rappel_de_delegation(self):
        r = jouer(self.SCRIPT, exit_plan_mode(PLAN_SANS_NOTION))
        self.assertEqual(r.returncode, 0, r.stderr)
        rappel = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(rappel["hookEventName"], "PostToolUse")
        self.assertIn("plans-notion:deleguer-a-haiku", rappel["additionalContext"])
        self.assertIn("executant", rappel["additionalContext"])

    def test_un_plan_qui_cite_une_page_notion_ne_rend_rien(self):
        # Témoin : sans lui, un script qui ne rend jamais rien passerait le test.
        self.assertIn("additionalContext", jouer(self.SCRIPT, exit_plan_mode(PLAN_SANS_NOTION)).stdout)
        for url in ("https://www.notion.so/Plan-abc123", "https://app.notion.com/p/abc123"):
            with self.subTest(url=url):
                r = jouer(self.SCRIPT, exit_plan_mode(f"Suivi : {url}\n1. Étape un"))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, "")

    def test_une_entree_illisible_sort_en_zero_sans_rien_rendre(self):
        for entree in ("pas du json {", ""):
            with self.subTest(entree=entree):
                r = jouer(self.SCRIPT, entree)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, "")

    def test_un_plan_lu_dans_un_fichier_qui_cite_notion_ne_rend_rien(self):
        # Témoin : le même plan sans URL, lu dans le même fichier, rend le rappel.
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "plan.md"
            chemin.write_text(PLAN_SANS_NOTION, encoding="utf-8")
            self.assertIn("additionalContext",
                          jouer(self.SCRIPT, entree_fichier_de_plan(str(chemin))).stdout)
            for url in ("https://www.notion.so/Plan-abc123", "https://app.notion.com/p/abc123"):
                with self.subTest(url=url):
                    chemin.write_text(f"Suivi : {url}\n1. Étape un", encoding="utf-8")
                    r = jouer(self.SCRIPT, entree_fichier_de_plan(str(chemin)))
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual(r.stdout, "")

    def test_un_plan_lu_dans_un_fichier_sans_url_rend_le_rappel(self):
        # Le plan n'est pas dans tool_input.plan : le chemin est dans tool_input, ou dans tool_response.
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "plan.md"
            chemin.write_text(PLAN_SANS_NOTION, encoding="utf-8")
            entrees = {
                "chemin dans tool_input": entree_fichier_de_plan(str(chemin)),
                "chemin dans tool_response": {"tool_name": "ExitPlanMode", "tool_input": {},
                                              "tool_response": {"planFilePath": str(chemin)}},
            }
            for nom, entree in entrees.items():
                with self.subTest(nom=nom):
                    r = jouer(self.SCRIPT, entree)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertIn("plans-notion:deleguer-a-haiku",
                                  json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_un_json_valide_sans_plan_ni_chemin_rend_le_rappel_par_defaut(self):
        # PostToolUse ne part que si ExitPlanMode a réussi : un plan a été approuvé.
        entrees = (
            {"tool_name": "ExitPlanMode", "tool_input": {}},
            {"tool_input": "pas un objet"},
            {"tool_name": "ExitPlanMode", "tool_input": {"planFilePath": "/chemin/qui/n/existe/pas.md"}},
            [],
        )
        for entree in entrees:
            with self.subTest(entree=entree):
                r = jouer(self.SCRIPT, entree)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("additionalContext", r.stdout)


def lecture(reponse, agent=None) -> dict:
    """Sortie d'un outil lu par le pilote ; ``agent`` présent = un sous-agent la porte."""
    entree = {"tool_name": "Read", "tool_input": {"file_path": "/notes.md"}, "tool_response": reponse}
    if agent is not None:
        entree["agent_id"] = agent
    return entree


class SignalerLecturePilote(unittest.TestCase):
    """Hook PostToolUse sur Read|Bash|Grep|notion-fetch : rappel si la sortie dépasse 20 000 caractères.

    Le pilote se reconnaît à l'absence de ``agent_id`` ; un sous-agent le porte.
    Les témoins (b) et (c) rendent le rappel sur la même entrée sans ``agent_id``
    ou à 25 000 caractères, pour qu'un script muet ne passe pas le silence.
    """
    SCRIPT = "signaler_lecture_pilote.py"

    def test_une_lecture_de_25000_caracteres_sans_agent_id_rend_le_rappel(self):
        r = jouer(self.SCRIPT, lecture("a" * 25000))
        self.assertEqual(r.returncode, 0, r.stderr)
        rappel = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(rappel["hookEventName"], "PostToolUse")
        self.assertIn("Lecture de 25000 caractères dans le contexte du pilote", rappel["additionalContext"])
        self.assertIn("_partage/lecture-deleguee.md", rappel["additionalContext"])

    def test_la_meme_lecture_portee_par_un_sous_agent_ne_rend_rien(self):
        # Témoin : sans agent_id, la même entrée rend le rappel.
        self.assertIn("additionalContext", jouer(self.SCRIPT, lecture("a" * 25000)).stdout)
        for agent in ("agent-123", ""):
            with self.subTest(agent_id=agent):
                r = jouer(self.SCRIPT, lecture("a" * 25000, agent=agent))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, "")

    def test_une_lecture_de_5000_caracteres_ne_rend_rien(self):
        # Témoin : la même entrée à 25 000 caractères rend le rappel.
        self.assertIn("additionalContext", jouer(self.SCRIPT, lecture("a" * 25000)).stdout)
        r = jouer(self.SCRIPT, lecture("a" * 5000))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_une_entree_illisible_sort_en_zero_sans_rien_rendre(self):
        # Témoin : une entrée valide de 25 000 caractères rend le rappel.
        self.assertIn("additionalContext", jouer(self.SCRIPT, lecture("a" * 25000)).stdout)
        for entree in ("pas du json {", "", [], {"tool_name": "Read"}):
            with self.subTest(entree=entree):
                r = jouer(self.SCRIPT, entree)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, "")

    # Extra (hors budget de l'étape, justifié) : la panne « seuil mal placé à la frontière »
    # (``>=`` pour ``>``, ou seuil recopié à 20 001 ou 24 999) n'est pas vue par 5 000 et 25 000.
    def test_le_seuil_de_20000_caracteres_est_strict(self):
        self.assertEqual(jouer(self.SCRIPT, lecture("a" * 20000)).stdout, "")
        r = jouer(self.SCRIPT, lecture("a" * 20001))
        self.assertNotEqual(r.stdout, "", r.stderr)
        self.assertIn("Lecture de 20001 caractères", json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])

    # Extra (justifié) : la panne « objet ignoré, ou compté en octets encodés » n'est pas vue par
    # les tests de chaîne. Un objet se mesure à sa sérialisation JSON sans échappement :
    # '{"a": "' (7) + 20000 é + '"}' (2) = 20009 caractères, et 120009 si ensure_ascii était vrai.
    def test_une_sortie_objet_se_mesure_a_sa_serialisation_sans_echappement(self):
        r = jouer(self.SCRIPT, lecture({"a": "é" * 20000}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Lecture de 20009 caractères", json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
