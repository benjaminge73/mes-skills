"""Tests des hooks ``PreToolUse`` du plugin plans-notion.

Chaque hook est lancé en vrai sous-processus, avec un JSON figé sur stdin,
comme Claude Code le fait : on observe le code de sortie et le message.
Contrat : refus = code 2 et motif sur stderr ; permis = code 0 sans sortie ;
entrée illisible = code 0 (un garde-fou cassé ne bloque aucune session).
"""
from __future__ import annotations

import json
import os
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


class RefuserGitStash(unittest.TestCase):
    """Hook PreToolUse (Bash) : pas de ``git stash``, sous aucune forme.

    Un hook absent fait échouer ``setUp`` : sans cela, le code 2 que Python rend
    pour un fichier introuvable aurait l'air d'un refus réussi. Le refus doit
    aussi porter son motif (« WIP » : l'alternative), ce qui sépare le rouge
    « le hook ne refuse pas » du rouge « le fichier manque ».
    """
    SCRIPT = "refuser_git_stash.py"

    def setUp(self):
        self.assertTrue((HOOKS / self.SCRIPT).is_file(), f"hook absent : {HOOKS / self.SCRIPT}")

    def refuse(self, commande: str):
        r = jouer(self.SCRIPT, bash(commande))
        self.assertEqual(r.returncode, 2, f"{commande!r} aurait dû être refusée : {r.stderr}")
        self.assertIn("stash", r.stderr)
        self.assertIn("WIP", r.stderr)

    def permis(self, commande: str):
        r = jouer(self.SCRIPT, bash(commande))
        self.assertEqual(r.returncode, 0, f"{commande!r} aurait dû passer : {r.stderr}")
        self.assertEqual(r.stdout + r.stderr, "")

    def test_un_git_stash_nu_est_refuse_avec_le_motif(self):
        self.refuse("git stash")

    def test_git_dash_C_stash_push_est_refuse(self):
        self.refuse("git -C /x stash push")

    def test_les_autres_sous_commandes_de_stash_sont_refusees(self):
        # Panne attrapée en plus : le hook ne reconnaîtrait que « git stash push ».
        for commande in ("git stash pop", "git stash apply", "git stash list"):
            with self.subTest(commande=commande):
                self.refuse(commande)

    def test_stash_apres_une_chaine_est_refuse(self):
        # Panne attrapée en plus : seul le premier segment de la commande serait lu.
        self.refuse("git status && git stash push")

    def test_stash_sur_une_ligne_suivante_est_refuse(self):
        # Panne attrapée en plus : un saut de ligne ne sépare pas deux commandes
        # pour shlex seul ; le découpage du hook doit le compter comme séparateur.
        self.refuse("git status\ngit stash push")

    def test_git_log_n_3_est_permis(self):
        self.permis("git log -n 3")

    def test_git_stash_dans_le_texte_du_message_est_permis(self):
        self.permis("git commit -m 'note: pas de git stash'")

    def test_echo_git_stash_est_permis(self):
        self.permis("echo git stash")

    def test_un_outil_autre_que_bash_est_ignore(self):
        # Panne attrapée en plus : le hook bloquerait un autre outil dont le texte
        # contient « git stash » (lecture d'un fichier, par exemple).
        r = jouer(self.SCRIPT, {"tool_name": "Read", "tool_input": {"command": "git stash"}})
        self.assertEqual(r.returncode, 0)

    def test_une_commande_non_decoupable_laisse_passer(self):
        r = jouer(self.SCRIPT, bash("git stash 'guillemet jamais fermé"))
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
        for valeur in ("brouillon", "en revue", "valide", "pret", "en cours", "a merger", "execute"):
            self.assertIn(valeur, r.stderr)

    def test_un_statut_accentue_en_creation_est_refuse(self):
        r = jouer(self.SCRIPT, self.create("validé"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("Statut", r.stderr)

    def test_un_statut_sans_accent_est_permis(self):
        for valeur in ("execute", "a merger", "en revue", "pret"):
            r = jouer(self.SCRIPT, self.update(valeur))
            self.assertEqual(r.returncode, 0, valeur)
            self.assertEqual(r.stdout + r.stderr, "")
        self.assertEqual(jouer(self.SCRIPT, self.create("brouillon")).returncode, 0)

    def test_toute_valeur_de_plan_accentuee_est_refusee(self):
        for valeur in ("à merger", "Exécuté", "  validé ", "prêt"):
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


class RappelMethodeHermes(unittest.TestCase):
    """Hook SessionStart : rappel de la méthode dans une session lancée par Hermes.

    Le marqueur est la variable ``HERMES_SESSION`` (``code`` ou ``revue``), seul
    contrat avec hermes-custom. Les tests fixent l'environnement eux-mêmes : une
    session Hermes peut porter la variable, et le test ne doit pas en dépendre.
    """
    SCRIPT = "rappel_methode_hermes.py"
    DEMARRAGE = {"hook_event_name": "SessionStart", "source": "startup"}

    def lancer(self, entree, marqueur=None) -> subprocess.CompletedProcess:
        env = {cle: valeur for cle, valeur in os.environ.items() if cle != "HERMES_SESSION"}
        if marqueur is not None:
            env["HERMES_SESSION"] = marqueur
        brut = entree if isinstance(entree, str) else json.dumps(entree)
        return subprocess.run([sys.executable, str(HOOKS / self.SCRIPT)], input=brut,
                              capture_output=True, text=True, timeout=30, env=env)

    def consigne(self, r) -> str:
        """Le texte injecté, ou ``""`` si le hook s'est tu."""
        if r.stdout == "":
            return ""
        sortie = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(sortie["hookEventName"], "SessionStart")
        return sortie["additionalContext"]

    def test_une_session_code_recoit_le_skill_deleguer_a_haiku_nomme(self):
        r = self.lancer(self.DEMARRAGE, marqueur="code")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("plans-notion:deleguer-a-haiku", self.consigne(r))

    def test_une_session_revue_nomme_l_enqueteur_sans_deleguer_l_ecriture(self):
        # Sans l'enquêteur nommé, la session de revue ne sait pas qui lit à sa place.
        r = self.lancer(self.DEMARRAGE, marqueur="revue")
        self.assertEqual(r.returncode, 0, r.stderr)
        consigne = self.consigne(r)
        self.assertIn("plans-notion:enqueteur", consigne)
        self.assertNotIn("deleguer-a-haiku", consigne)
        self.assertNotIn("executant", consigne.lower())

    def test_sans_marqueur_connu_le_hook_se_tait(self):
        # « codes » est une valeur proche : un contrôle par préfixe la prendrait pour « code ».
        for marqueur in (None, "", "autre", "codes"):
            with self.subTest(marqueur=marqueur):
                r = self.lancer(self.DEMARRAGE, marqueur=marqueur)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, "")

    def test_une_entree_illisible_sort_en_zero_sans_rien_rendre(self):
        # Le marqueur est posé à chaque valeur utile : l'entrée illisible doit taire
        # le hook même quand la session est une session Hermes.
        for marqueur in ("code", "revue", None):
            for entree in ("pas du json {", ""):
                with self.subTest(marqueur=marqueur, entree=entree):
                    r = self.lancer(entree, marqueur=marqueur)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    self.assertEqual(r.stdout, "")


# --- garde de fin de tour et retrait des worktrees clos (plan Hal, étape 2) ---

SESSION_LOCALE = "loc-hal-1"
PAGE = "3a1b2c3d-0000-4000-8000-000000000001"
ENV_GIT_IDENTITE = {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid"}


def fiche_de_test(session: str, **champs) -> dict:
    """Une fiche telle que plan-en-cours.py l'écrit à l'ouverture ; ``champs`` la fait évoluer."""
    fiche = {"page_id": PAGE, "titre": "Hal veille", "depot": "benjaminge73/mes-skills",
             "branche": "feat/hal-veille-plans", "worktree": "/nonexistant/worktree",
             "pr": None, "session_id": None, "session_locale": session, "etat": "en cours",
             "raison_attente": None, "etapes_faites": None, "etapes_restantes": None,
             "relances": 0, "sonnette": None, "maj": "2026-11-17T00:00:00Z",
             "origine": "terminal du VPS"}
    fiche.update(champs)
    return fiche


class GardeFinDeTour(unittest.TestCase):
    """Le hook ``Stop`` retient la fin de tour d'un plan en cours, sans réseau ni modèle.

    Contrat observé : sortie vide et code 0 = laisser passer ; sortie JSON
    ``{"decision": "block", "reason": ...}`` et code 0 = retenir la session.
    """
    SCRIPT = "garde_fin_de_tour.py"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.etat = Path(tmp.name) / "etat"
        self.dossier = self.etat / "plans-notion" / "plans-en-cours"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
        self.env["XDG_STATE_HOME"] = str(self.etat)

    def poser(self, **champs):
        self.dossier.mkdir(parents=True, exist_ok=True)
        chemin = self.dossier / f"{SESSION_LOCALE}.json"
        chemin.write_text(json.dumps(fiche_de_test(SESSION_LOCALE, **champs)), encoding="utf-8")

    def lire(self) -> dict:
        return json.loads((self.dossier / f"{SESSION_LOCALE}.json").read_text(encoding="utf-8"))

    def jouer(self, *, stop_hook_active=False, background_tasks=(), session_crons=(), entree=None):
        if entree is None:
            entree = {"session_id": SESSION_LOCALE, "stop_hook_active": stop_hook_active,
                      "last_assistant_message": "étape 2 terminée", "background_tasks": list(background_tasks),
                      "session_crons": list(session_crons)}
        brut = entree if isinstance(entree, str) else json.dumps(entree)
        return subprocess.run([sys.executable, str(HOOKS / self.SCRIPT)], input=brut,
                              capture_output=True, text=True, timeout=30, env=self.env)

    def assertPasse(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def assertBloque(self, r) -> str:
        self.assertEqual(r.returncode, 0, r.stderr)
        decision = json.loads(r.stdout)
        self.assertEqual(decision["decision"], "block")
        self.assertTrue(decision["reason"].strip(), "une retenue sans consigne ne sert à rien")
        return decision["reason"]

    def test_garde_sans_fiche_ne_fait_rien(self):
        # Une session ordinaire n'a pas de fiche : elle ne doit jamais être retenue.
        self.assertPasse(self.jouer())

    def test_garde_fiche_en_cours_bloque_et_compte_une_relance(self):
        self.poser(etat="en cours")
        self.assertBloque(self.jouer())
        self.assertEqual(self.lire()["relances"], 1)

    def test_garde_stop_hook_actif_laisse_passer_sans_compter(self):
        # Sans ce garde, la retenue relance la session qui relance la retenue sans fin.
        self.poser(etat="en cours")
        self.assertPasse(self.jouer(stop_hook_active=True))
        self.assertEqual(self.lire()["relances"], 0)

    def test_garde_fiche_en_attente_laisse_passer(self):
        self.poser(etat="attente", raison_attente="relecture par Benjamin")
        self.assertPasse(self.jouer())

    def test_garde_seuil_de_relances_atteint_laisse_passer(self):
        # Trois relances sans avancée : la garde se tait pour que Hal regarde.
        self.poser(etat="en cours", relances=3)
        self.assertPasse(self.jouer())
        self.assertEqual(self.lire()["relances"], 3)

    def test_garde_fiche_illisible_laisse_passer_sans_erreur(self):
        self.dossier.mkdir(parents=True, exist_ok=True)
        (self.dossier / f"{SESSION_LOCALE}.json").write_text("{ pas du json", encoding="utf-8")
        self.assertPasse(self.jouer())

    def test_garde_entree_illisible_laisse_passer_meme_avec_une_fiche_en_cours(self):
        # La fiche en cours seule bloquerait : le test prouve que c'est l'entrée illisible qui tait la garde.
        self.poser(etat="en cours")
        self.assertPasse(self.jouer(entree="pas du json {"))

    def test_garde_taches_de_fond_en_cours_laissent_passer(self):
        self.poser(etat="en cours")
        self.assertPasse(self.jouer(background_tasks=[{"id": "veille"}]))
        self.assertEqual(self.lire()["relances"], 0)

    def test_garde_reveil_programme_en_cours_laisse_passer(self):
        # Autre panne attrapée : la garde retient une session qui a déjà armé son réveil.
        self.poser(etat="en cours")
        self.assertPasse(self.jouer(session_crons=[{"id": "reveil"}]))

    def test_garde_a_merger_sans_sonnette_ni_reveil_demande_d_armer_un_reveil(self):
        self.poser(etat="a merger", pr=7)
        reason = self.assertBloque(self.jouer())
        self.assertIn("15 minutes", reason)

    def test_garde_a_merger_avec_sonnette_laisse_passer(self):
        self.poser(etat="a merger", pr=7, sonnette="declencheur-1")
        self.assertPasse(self.jouer())

    def test_garde_a_merger_avec_reveil_arme_laisse_passer(self):
        # Autre panne attrapée : la garde réclame un réveil à une session qui en a déjà un.
        self.poser(etat="a merger", pr=7)
        self.assertPasse(self.jouer(session_crons=[{"id": "reveil"}]))


class RetirerWorktreesClos(unittest.TestCase):
    """Le hook ``SessionStart`` retire un worktree dont le plan est fini, et rien d'autre.

    Le cas favorable exige les trois preuves : PR mergée, au SHA de la branche
    locale, arbre du worktree propre. Tout le reste laisse le worktree en place.
    """
    SCRIPT = "retirer_worktrees_clos.py"
    DEPOT = "benjaminge73/mes-skills"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        racine = Path(tmp.name)
        self.principal = racine / "depot"
        self.worktree = racine / "worktrees" / "feat-x"
        self.dossier = racine / "etat" / "plans-notion" / "plans-en-cours"
        self.bin = racine / "bin"
        self.bin.mkdir()
        # Sessions isolées : aucune session réelle du poste ne doit peser sur ces tests.
        self.sessions = racine / "sessions"
        self.sessions.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "GIT_", "PLANS_NOTION_"))}
        self.env["XDG_STATE_HOME"] = str(racine / "etat")
        self.env["PLANS_NOTION_SESSIONS_DIR"] = str(self.sessions)
        self.env["PATH"] = f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}"
        self._depot_avec_un_worktree()

    def _git(self, *args, cwd) -> str:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                           env={**self.env, **ENV_GIT_IDENTITE}, check=True)
        return r.stdout.strip()

    def _depot_avec_un_worktree(self):
        self.principal.mkdir(parents=True)
        self._git("init", "-q", "-b", "main", cwd=self.principal)
        (self.principal / "a.txt").write_text("base\n", encoding="utf-8")
        self._git("add", "a.txt", cwd=self.principal)
        self._git("commit", "-q", "-m", "base", cwd=self.principal)
        self.worktree.parent.mkdir(parents=True)
        self._git("worktree", "add", "-q", "-b", "feat/x", str(self.worktree), cwd=self.principal)
        (self.worktree / "b.txt").write_text("travail\n", encoding="utf-8")
        self._git("add", "b.txt", cwd=self.worktree)
        self._git("commit", "-q", "-m", "travail", cwd=self.worktree)
        self.sha = self._git("rev-parse", "HEAD", cwd=self.worktree)

    def poser_fiche(self, **champs):
        self.dossier.mkdir(parents=True, exist_ok=True)
        fiche = fiche_de_test("loc-retrait-1", pr=7, etat="a merger", branche="feat/x",
                              worktree=str(self.worktree), depot=self.DEPOT, titre="Plan de test")
        fiche.update(champs)
        (self.dossier / "loc-retrait-1.json").write_text(json.dumps(fiche), encoding="utf-8")

    def lire_fiche(self) -> dict:
        return json.loads((self.dossier / "loc-retrait-1.json").read_text(encoding="utf-8"))

    def poser_fiche_de(self, cle: str, *, worktree: Path, branche: str, pr: int):
        """Une seconde fiche, pour un autre worktree : même dépôt, même plan de test."""
        self.dossier.mkdir(parents=True, exist_ok=True)
        fiche = fiche_de_test(cle, pr=pr, etat="a merger", branche=branche,
                              worktree=str(worktree), depot=self.DEPOT, titre=f"Plan {cle}")
        (self.dossier / f"{cle}.json").write_text(json.dumps(fiche), encoding="utf-8")

    def lire_fiche_de(self, cle: str) -> dict:
        return json.loads((self.dossier / f"{cle}.json").read_text(encoding="utf-8"))

    def worktree_au_sha(self, nom: str) -> Path:
        """Un second worktree, branche neuve posée sur le même commit que le premier."""
        chemin = self.worktree.parent / nom
        self._git("worktree", "add", "-q", "-b", f"feat/{nom}", str(chemin), self.sha, cwd=self.principal)
        return chemin

    def poser_session(self, nom: str, donnees):
        """Un fichier ``<nom>.json`` dans le dossier de sessions ; ``donnees`` brut si c'est une chaîne."""
        corps = donnees if isinstance(donnees, str) else json.dumps(donnees)
        (self.sessions / f"{nom}.json").write_text(corps, encoding="utf-8")

    def pid_mort(self) -> int:
        """Le pid d'un processus déjà terminé et attendu : il n'existe plus."""
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()
        return p.pid

    def faux_gh(self, sortie: str | None, code: int = 0):
        """Un ``gh`` jetable sur le PATH : il rend la sortie donnée, sans aucun réseau."""
        corps = "#!/bin/sh\n"
        if sortie is not None:
            corps += f"printf '%s\\n' '{sortie}'\n"
        corps += f"exit {code}\n"
        chemin = self.bin / "gh"
        chemin.write_text(corps, encoding="utf-8")
        chemin.chmod(0o755)

    def pr_dans_cet_etat(self, etat: str, sha: str | None = None):
        self.faux_gh(json.dumps({"state": etat, "headRefOid": sha or self.sha}))

    def jouer(self, cwd: Path | None = None) -> subprocess.CompletedProcess:
        cwd = cwd or self.principal
        entree = json.dumps({"session_id": "loc-session-courante", "cwd": str(cwd)})
        return subprocess.run([sys.executable, str(HOOKS / self.SCRIPT)], input=entree,
                              capture_output=True, text=True, timeout=60, env=self.env, cwd=cwd)

    def assertRienRetire(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.worktree.is_dir(), "le worktree a été retiré alors que la preuve manque")
        self.assertEqual(self.lire_fiche()["etat"], "a merger", "la fiche a été close sans retrait")

    def test_retirer_pr_mergee_au_meme_commit_et_arbre_propre_retire_le_worktree(self):
        self.pr_dans_cet_etat("MERGED")
        self.poser_fiche()
        r = self.jouer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.worktree.exists(), "le worktree clos n'a pas été retiré")
        self.assertEqual(self.lire_fiche()["etat"], "clos")
        # Le hook retire le worktree, jamais la branche : elle doit rester, pour le balayeur.
        self._git("rev-parse", "--verify", "refs/heads/feat/x", cwd=self.principal)

    def test_retirer_arbre_sale_ne_retire_rien(self):
        self.pr_dans_cet_etat("MERGED")
        self.poser_fiche()
        (self.worktree / "b.txt").write_text("modifié sans commit\n", encoding="utf-8")
        self.assertRienRetire(self.jouer())

    def test_retirer_commit_local_en_avance_sur_la_pr_mergee_ne_retire_rien(self):
        self.pr_dans_cet_etat("MERGED", sha=self.sha)
        self.poser_fiche()
        self._git("commit", "-q", "--allow-empty", "-m", "commit ultérieur au merge", cwd=self.worktree)
        self.assertRienRetire(self.jouer())

    def test_retirer_gh_en_panne_ne_retire_rien(self):
        self.faux_gh(None, code=1)
        self.poser_fiche()
        self.assertRienRetire(self.jouer())

    def test_retirer_pr_encore_ouverte_ne_retire_rien(self):
        # Autre panne attrapée : un worktree dont la PR n'est pas encore mergée.
        self.pr_dans_cet_etat("OPEN")
        self.poser_fiche()
        self.assertRienRetire(self.jouer())

    def test_retirer_worktree_de_la_session_courante_ne_retire_rien(self):
        # Autre panne attrapée : le hook retire le dossier où tourne la session qui démarre.
        self.pr_dans_cet_etat("MERGED")
        self.poser_fiche()
        self.assertEqual(self.jouer(cwd=self.worktree).returncode, 0)
        self.assertTrue(self.worktree.is_dir(), "le worktree de la session courante a été retiré")
        self.assertEqual(self.lire_fiche()["etat"], "a merger")

    def test_worktree_d_une_session_vivante_reste_en_place_quand_une_autre_session_demarre(self):
        # Panne attrapée : la session B retire le worktree de la session A, encore vivante, et close sa fiche.
        # La session morte (A' : fichier de session resté là, pid mort) doit, elle, perdre son worktree.
        self.pr_dans_cet_etat("MERGED")
        ecarte = self.worktree_au_sha("y")
        self.poser_fiche_de("loc-vivante", worktree=self.worktree, branche="feat/x", pr=7)
        self.poser_fiche_de("loc-morte", worktree=ecarte, branche="feat/y", pr=8)
        self.poser_session("loc-vivante-pid", {"pid": os.getpid(), "sessionId": "loc-vivante"})
        self.poser_session("loc-morte-pid", {"pid": self.pid_mort(), "sessionId": "loc-morte"})
        fiche_vivante_avant = self.lire_fiche_de("loc-vivante")

        r = self.jouer()

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.worktree.is_dir(), "le worktree d'une session vivante a été retiré")
        self.assertEqual(self.lire_fiche_de("loc-vivante"), fiche_vivante_avant, "la fiche d'une session vivante a bougé")
        self.assertFalse(ecarte.exists(), "le worktree d'une session morte n'a pas été retiré")
        self.assertEqual(self.lire_fiche_de("loc-morte")["etat"], "clos")

    def test_fichier_de_session_illisible_d_un_pid_vivant_ne_retire_rien(self):
        # Panne attrapée : un fichier de session illisible, dont le pid tourne, ne doit pas laisser retirer.
        # Dans le doute, la session est vivante.
        self.pr_dans_cet_etat("MERGED")
        self.poser_fiche()
        self.poser_session(str(os.getpid()), "{ pas du json")
        self.assertRienRetire(self.jouer())

    def test_worktree_dont_la_tete_est_detachee_en_avance_ne_retire_rien(self):
        # Panne attrapée : HEAD détaché et en avance d'un commit, la branche reste au SHA du merge.
        # Le commit serait perdu au retrait.
        self.pr_dans_cet_etat("MERGED", sha=self.sha)
        self.poser_fiche()
        self._git("checkout", "-q", "--detach", cwd=self.worktree)
        self._git("commit", "-q", "--allow-empty", "-m", "commit détaché après le merge", cwd=self.worktree)
        self.assertRienRetire(self.jouer())


class RefuserRevueSansAvis(unittest.TestCase):
    """Hook PreToolUse : pas de passage à « en revue » sans avis de Hal au registre.

    Lancé en sous-processus, avec le registre (``HERMES_RELECTURES_DIR``) et le
    script de Hal (``PLANS_NOTION_DEMANDER_A_HAL``) dans un dossier temporaire.
    Un hook absent fait échouer ``setUp`` : sans cela, le code 2 que Python rend
    pour un fichier introuvable aurait l'air d'un refus réussi.
    """
    SCRIPT = "refuser_revue_sans_avis.py"
    PAGE = "3a1f5c2e-8b7d-4e6a-9f10-2c3d4e5f6a7b"
    PAGE_MAITRE = "7c9e0d1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f"

    def setUp(self):
        self.assertTrue((HOOKS / self.SCRIPT).is_file(), f"hook absent : {HOOKS / self.SCRIPT}")
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        self.racine = Path(temporaire.name)
        self.registre = self.racine / "relectures"
        self.registre.mkdir()
        self.hal = self.racine / "demander_a_hal.py"
        self.hal.write_text("RELECTURE_DISPONIBLE = True\n", encoding="utf-8")
        self.env = {**os.environ,
                    "PLANS_NOTION_DEMANDER_A_HAL": str(self.hal),
                    "HERMES_RELECTURES_DIR": str(self.registre)}

    def jouer(self, entree) -> subprocess.CompletedProcess:
        brut = entree if isinstance(entree, str) else json.dumps(entree)
        return subprocess.run([sys.executable, str(HOOKS / self.SCRIPT)], input=brut,
                              capture_output=True, text=True, timeout=30, env=self.env)

    def refuse(self, entree):
        r = self.jouer(entree)
        self.assertEqual(r.returncode, 2, f"aurait dû être refusée : {r.stderr}")
        self.assertIn("relire", r.stderr)

    def permis(self, entree):
        r = self.jouer(entree)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout + r.stderr, "")

    def poser_registre(self, *tours, page=PAGE):
        fichier = self.registre / f"{page.replace('-', '')}.json"
        fichier.write_text(json.dumps({"page": f"https://www.notion.so/{page.replace('-', '')}",
                                       "tours": list(tours)}), encoding="utf-8")

    @staticmethod
    def tour(numero, issue="ok", verdict="OK", reserves=0):
        return {"tour": numero, "date": "2026-11-19T09:00:00+00:00", "issue": issue,
                "verdict": verdict, "reserves": reserves, "duree_s": 120,
                "commandes": [], "ecritures": []}

    def mise_a_jour(self, statut, page=PAGE):
        return {"tool_name": OUTIL_UPDATE,
                "tool_input": {"page_id": page, "command": "update_properties",
                               "properties": {"Statut": statut}}}

    def creation(self, statut):
        return {"tool_name": OUTIL_CREATE,
                "tool_input": {"pages": [{"properties": {"Titre": "t", "Statut": statut}}]}}

    def composio(self, slug, charge):
        return bash(f"composio execute {slug} -d '{json.dumps(charge, ensure_ascii=False)}'")

    def test_une_mise_en_revue_sans_registre_est_refusee_et_cite_relire(self):
        self.refuse(self.mise_a_jour("en revue"))

    def test_un_tour_1_ok_au_registre_permet_la_mise_en_revue(self):
        self.poser_registre(self.tour(1, verdict="OK"))
        self.permis(self.mise_a_jour("en revue"))

    def test_un_tour_1_avec_reserves_seul_refuse_la_mise_en_revue(self):
        self.poser_registre(self.tour(1, verdict="RESERVES", reserves=2))
        self.refuse(self.mise_a_jour("en revue"))

    def test_un_tour_2_rendu_permet_la_mise_en_revue(self):
        self.poser_registre(self.tour(1, verdict="RESERVES", reserves=2),
                            self.tour(2, verdict="RESERVES", reserves=1))
        self.permis(self.mise_a_jour("en revue"))

    def test_deux_tours_en_echec_ne_bloquent_pas_la_session(self):
        self.poser_registre(self.tour(1, issue="delai", verdict=None),
                            self.tour(2, issue="code", verdict=None))
        r = self.jouer(self.mise_a_jour("en revue"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_deux_echecs_au_tour_1_valent_un_avis_rendu(self):
        # relire fait un appel par exécution : le repli « la session relance une fois »
        # peut noter deux échecs tous deux au tour 1. Ils valent un avis rendu.
        self.poser_registre(self.tour(1, issue="delai", verdict=None),
                            self.tour(1, issue="code", verdict=None))
        self.permis(self.mise_a_jour("en revue"))

    def test_deux_echecs_au_tour_2_apres_un_tour_1_reserve_valent_un_avis_rendu(self):
        self.poser_registre(self.tour(1, verdict="RESERVES", reserves=2),
                            self.tour(2, issue="delai", verdict=None),
                            self.tour(2, issue="code", verdict=None))
        self.permis(self.mise_a_jour("en revue"))

    def test_un_seul_echec_note_ne_permet_pas_la_mise_en_revue(self):
        with self.subTest("au tour 1"):
            self.poser_registre(self.tour(1, issue="delai", verdict=None))
            self.refuse(self.mise_a_jour("en revue"))
        with self.subTest("au tour 2, après un tour 1 réservé"):
            self.poser_registre(self.tour(1, verdict="RESERVES", reserves=2),
                                self.tour(2, issue="code", verdict=None))
            self.refuse(self.mise_a_jour("en revue"))

    def test_une_page_de_plan_maitre_sans_registre_est_refusee_comme_les_autres(self):
        # Le hook ne voit que page_id : un plan maître n'a aucune exemption.
        self.refuse(self.mise_a_jour("en revue", page=self.PAGE_MAITRE))

    def test_sans_script_de_hal_ou_sans_son_marqueur_le_hook_reste_inactif(self):
        with self.subTest("script absent"):
            self.hal.unlink()
            self.assertEqual(self.jouer(self.mise_a_jour("en revue")).returncode, 0)
        with self.subTest("script sans RELECTURE_DISPONIBLE"):
            self.hal.write_text("print('autre chose')\n", encoding="utf-8")
            self.assertEqual(self.jouer(self.mise_a_jour("en revue")).returncode, 0)

    def test_un_passage_a_brouillon_n_est_pas_bloque(self):
        self.permis(self.mise_a_jour("brouillon"))

    def test_une_creation_de_page_en_revue_sans_avis_est_refusee(self):
        self.refuse(self.creation("en revue"))

    def test_composio_qui_pose_en_revue_sans_avis_est_refuse_en_ligne_et_depuis_un_fichier(self):
        charge = {"page_id": self.PAGE, "properties": {"Statut": "en revue"}}
        with self.subTest("charge en ligne"):
            self.refuse(self.composio("NOTION_UPDATE_PAGE", charge))
        with self.subTest("charge dans un fichier"):
            fichier = self.racine / "charge.json"
            fichier.write_text(json.dumps(charge, ensure_ascii=False), encoding="utf-8")
            self.refuse(bash(f"composio execute NOTION_UPDATE_PAGE -d @{fichier}"))

    def test_composio_appele_par_chemin_absolu_pose_la_meme_garde(self):
        charge = {"page_id": self.PAGE, "properties": {"Statut": "en revue"}}
        fichier = self.racine / "charge.json"
        fichier.write_text(json.dumps(charge, ensure_ascii=False), encoding="utf-8")
        with self.subTest("chemin absolu, charge en ligne"):
            self.refuse(bash(f"~/.local/bin/composio execute NOTION_UPDATE_PAGE "
                             f"-d '{json.dumps(charge, ensure_ascii=False)}'"))
        with self.subTest("chemin absolu, charge dans un fichier"):
            self.refuse(bash(f"~/.local/bin/composio execute NOTION_UPDATE_PAGE -d @{fichier}"))

    def test_charge_collee_a_son_option_est_lue_comme_une_charge_en_fichier(self):
        charge = {"page_id": self.PAGE, "properties": {"Statut": "en revue"}}
        fichier = self.racine / "charge.json"
        fichier.write_text(json.dumps(charge, ensure_ascii=False), encoding="utf-8")
        with self.subTest("--data=@fichier"):
            self.refuse(bash(f"composio execute NOTION_UPDATE_PAGE --data=@{fichier}"))
        with self.subTest("-d@fichier"):
            self.refuse(bash(f"composio execute NOTION_UPDATE_PAGE -d@{fichier}"))

    def test_une_entree_illisible_laisse_passer_avec_un_mot_sur_stderr(self):
        for entree in ("pas du json {", ""):
            with self.subTest(entree=entree):
                r = self.jouer(entree)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotEqual(r.stderr.strip(), "")

    def test_composio_markdown_qui_cite_en_revue_est_permis(self):
        # NOTION_UPDATE_PAGE est le préfixe de NOTION_UPDATE_PAGE_MARKDOWN : seul le slug
        # entier, avec une charge qui pose Statut, est refusé.
        charge = {"page_id": self.PAGE, "type": "update_content",
                  "update_content": {"content_updates": [
                      {"old_str": "Statut : brouillon", "new_str": "Statut : en revue"}]}}
        self.permis(self.composio("NOTION_UPDATE_PAGE_MARKDOWN", charge))

    # L'id Notion est les 32 derniers caractères hexadécimaux de l'adresse : un titre qui
    # finit par un caractère hexadécimal (« revue » finit par e) ne doit pas décaler l'id.
    IDENT = "396b8cc8aa1d8009b32fdd28f3ed3b20"

    def avis_pour_id(self, ident, *tours):
        (self.registre / f"{ident}.json").write_text(json.dumps({"tours": list(tours)}), encoding="utf-8")

    def test_adresse_dont_le_titre_finit_par_e_retrouve_son_avis(self):
        self.avis_pour_id(self.IDENT, self.tour(1, verdict="OK"))
        url = f"https://www.notion.so/Hal-relit-le-plan-avant-qu-il-passe-en-revue-{self.IDENT}"
        self.permis(self.mise_a_jour("en revue", page=url))

    def test_adresse_dont_le_titre_finit_par_decafe_retrouve_son_avis(self):
        self.avis_pour_id(self.IDENT, self.tour(1, verdict="OK"))
        url = f"https://www.notion.so/Essai-decafe-{self.IDENT}"
        self.permis(self.mise_a_jour("en revue", page=url))

    def test_adresse_avec_requete_et_ancre_ne_lit_pas_les_hexadecimaux_de_la_requete(self):
        self.avis_pour_id(self.IDENT, self.tour(1, verdict="OK"))
        url = f"https://www.notion.so/Essai-decafe-{self.IDENT}?v=0123456789abcdef0123456789abcdef#bloc"
        self.permis(self.mise_a_jour("en revue", page=url))

    def test_uuid_avec_tirets_et_id_nu_retrouvent_le_meme_avis(self):
        self.avis_pour_id(self.IDENT, self.tour(1, verdict="OK"))
        with self.subTest("UUID avec tirets"):
            self.permis(self.mise_a_jour("en revue", page="396b8cc8-aa1d-8009-b32f-dd28f3ed3b20"))
        with self.subTest("id nu"):
            self.permis(self.mise_a_jour("en revue", page=self.IDENT))


if __name__ == "__main__":
    unittest.main()
