"""Tests de ``plan-en-cours.py``, la fiche locale du plan en cours.

La fiche est lue sans réseau par la garde de fin de tour. Ce qu'il faut
prouver, ce sont les engagements du script, pas son code : une fiche relue
porte ce qu'on y a écrit, une clôture sur une fiche absente ne crée rien,
deux écritures concurrentes ne laissent jamais un JSON tronqué, et un fichier
de session sans ``bridgeSessionId`` ne fait naître aucun identifiant. Le nom
de la fiche est l'identifiant local de la session (celui que la garde reçoit),
l'identifiant claude.ai n'est qu'un champ.

Chaque test vit dans un ``HOME`` et un ``XDG_STATE_HOME`` jetables : aucun ne
lit le vrai ``~/.claude`` ni n'écrit dans le vrai ``~/.local/state``. Les
variables ``CLAUDE*`` du poste sont retirées de l'environnement du script, qui
ne voit que ce que le test lui pose.

Les attendus viennent du plan, pas du code : une fiche se relit telle qu'elle
a été écrite ; ``clore`` sur une fiche absente sort en 1 ; ``reprendre`` depuis
``attendre`` repasse ``en cours`` et compte une relance ; ``attendre`` depuis
``a merger`` se reprend en ``a merger`` ; ``etape`` remet les relances à zéro ;
le dossier des fiches est en mode 700.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "plan-en-cours.py"

PAGE = "3a1b2c3d-0000-4000-8000-000000000001"
WORKTREE = "/home/ubuntu/repos/worktrees/mes-skills/feat-hal-veille-plans"
SESSION_BRIDGE = "cse_bridge01"
SESSION_LOCALE = "loc-1"


class PlanEnCoursTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.racine = Path(tmp.name)
        self.home = self.racine / "home"
        (self.home / ".claude" / "sessions").mkdir(parents=True)
        self.etat = self.racine / "etat"

    # --- outils de test -------------------------------------------------

    def dossier_fiches(self) -> Path:
        return self.etat / "plans-notion" / "plans-en-cours"

    def env(self, pid=None, session_env=None, hote=None) -> dict:
        env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
        env["HOME"] = str(self.home)
        env["XDG_STATE_HOME"] = str(self.etat)
        env.pop("PLAN_EN_COURS_HOTE", None)
        if hote is not None:
            env["PLAN_EN_COURS_HOTE"] = hote
        if pid is not None:
            env["CLAUDE_PID"] = str(pid)
        if session_env is not None:
            env["CLAUDE_CODE_SESSION_ID"] = session_env
        return env

    def poser_session(self, pid: int, donnees: dict) -> None:
        (self.home / ".claude" / "sessions" / f"{pid}.json").write_text(json.dumps(donnees))

    def lancer(self, *args, pid=None, session_env=None, hote=None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env=self.env(pid=pid, session_env=session_env, hote=hote),
            capture_output=True, text=True, timeout=60,
        )

    def ouvrir(self, *extra, pid=None, session_env=None, hote=None) -> subprocess.CompletedProcess:
        return self.lancer(
            "ouvrir", "--page", PAGE, "--titre", "Hal veille",
            "--depot", "benjaminge73/mes-skills", "--branche", "feat/hal-veille-plans",
            "--worktree", WORKTREE, *extra,
            pid=pid, session_env=session_env, hote=hote,
        )

    def lire(self, pid=None, session_env=None) -> dict:
        r = self.lancer("lire", pid=pid, session_env=session_env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    # --- tests ----------------------------------------------------------

    def test_fiche_relue_apres_ouvrir_puis_pr_porte_les_deux(self):
        # Panne nommée : une écriture (`pr`) efface ou perd les champs posés par
        # `ouvrir`, ou ne retient pas le numéro de PR.
        self.poser_session(4242, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-1"})
        r = self.ouvrir(pid=4242)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.lancer("pr", "--numero", "156", pid=4242)
        self.assertEqual(r.returncode, 0, r.stderr)

        fiche = self.lire(pid=4242)
        self.assertEqual(fiche["page_id"], PAGE)
        self.assertEqual(fiche["titre"], "Hal veille")
        self.assertEqual(fiche["depot"], "benjaminge73/mes-skills")
        self.assertEqual(fiche["branche"], "feat/hal-veille-plans")
        self.assertEqual(fiche["worktree"], WORKTREE)
        self.assertEqual(fiche["pr"], 156)
        self.assertEqual(fiche["session_id"], SESSION_BRIDGE)
        for champ in ("raison_attente", "etapes_faites", "etapes_restantes",
                      "relances", "sonnette", "maj", "origine", "etat"):
            self.assertIn(champ, fiche)

    def test_clore_sur_fiche_absente_sort_en_1_sans_rien_creer(self):
        # Panne nommée : `clore` sur une fiche qui n'existe pas sort en 0, ou crée
        # une fiche vide qui ferait croire à une session en cours.
        r = self.lancer("clore", "--session", "cse_absente")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(self.dossier_fiches().exists() and any(self.dossier_fiches().iterdir()))

    def test_ecritures_concurrentes_ne_laissent_jamais_un_json_tronque(self):
        # Panne nommée : une écriture qui vide le fichier avant de le remplir laisse,
        # pendant l'écriture, un JSON tronqué que la garde de fin de tour ne saurait
        # pas lire. La raison d'attente est longue (100 ko) pour élargir la fenêtre
        # où une écriture non atomique se verrait ; sans atomicité, ce test échoue
        # avec forte probabilité, sans certitude.
        self.poser_session(4242, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": SESSION_LOCALE})
        self.assertEqual(self.ouvrir(pid=4242).returncode, 0)
        fichier = self.dossier_fiches() / f"{SESSION_LOCALE}.json"
        codes: list[int] = []

        def ecrivain(lettre: str):
            for i in range(12):
                r = self.lancer("attendre", "--raison", lettre * 100_000, pid=4242)
                codes.append(r.returncode)
                r = self.lancer("etape", "--faite", str(i), "--restantes", "3", pid=4242)
                codes.append(r.returncode)

        fils = [threading.Thread(target=ecrivain, args=(lettre,)) for lettre in ("a", "b")]
        for f in fils:
            f.start()

        erreurs: list[str] = []
        lectures = 0
        while any(f.is_alive() for f in fils):
            try:
                texte = fichier.read_text(encoding="utf-8")
            except FileNotFoundError:
                erreurs.append("fiche absente pendant une écriture")
                continue
            lectures += 1
            try:
                json.loads(texte)
            except json.JSONDecodeError as e:
                erreurs.append(f"JSON tronqué : {e}")
        for f in fils:
            f.join()

        self.assertGreater(lectures, 0)
        self.assertEqual(erreurs, [])
        self.assertEqual(codes, [0] * len(codes), "une écriture concurrente a échoué")
        self.assertEqual(json.loads(fichier.read_text(encoding="utf-8"))["session_id"], SESSION_BRIDGE)

    def test_fichier_de_session_sans_bridgeSessionId_n_invente_aucun_identifiant(self):
        # Panne nommée : sans `bridgeSessionId`, le script invente un identifiant de
        # session, ou pose une sonnette qu'aucune session claude.ai ne peut recevoir.
        # Le `sessionId` local du fichier n'est pas l'identifiant claude.ai : il ne
        # doit ni devenir `session_id`, ni servir de sonnette.
        self.poser_session(4243, {"sessionId": "loc-local-1", "kind": "interactive",
                                  "entrypoint": "claude-desktop"})
        r = self.ouvrir("--sonnette", "trig_09", pid=4243, session_env="loc-local-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pas de sonnette possible", r.stdout)

        fiche = self.lire(pid=4243, session_env="loc-local-1")
        self.assertIsNone(fiche["session_id"])
        self.assertIsNone(fiche["sonnette"])
        self.assertEqual(fiche["origine"], "app de bureau")
        # Panne nommée : sans bridgeSessionId, `session_locale` ne porte pas l'identifiant
        # local de la session, et la garde de fin de tour ne peut pas relier la fiche
        # à sa session. Précondition : le champ existe (sa valeur est l'identifiant local).
        self.assertEqual(fiche.get("session_locale"), "loc-local-1")

        # Aucune clé du tout (ni bridge, ni identifiant de session de l'environnement) :
        # le script refuse au lieu de fabriquer une clé de fiche.
        avant = sorted(p.name for p in self.dossier_fiches().iterdir())
        r = self.ouvrir()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(sorted(p.name for p in self.dossier_fiches().iterdir()), avant)

    def test_fiche_nommee_par_identifiant_local_et_bridge_en_champ(self):
        # Panne nommée : la fiche est nommée par le bridgeSessionId (claude.ai). La garde
        # de fin de tour ne reçoit que l'identifiant local (session_id de l'entrée du
        # hook) : elle ne retrouverait pas la fiche d'une session Remote Control. Le nom
        # du fichier doit être l'identifiant local ; le bridge n'est qu'un champ.
        self.poser_session(4245, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": SESSION_LOCALE,
                                  "entrypoint": "sdk-cli"})
        r = self.ouvrir(pid=4245)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.dossier_fiches() / f"{SESSION_LOCALE}.json").is_file())
        self.assertFalse((self.dossier_fiches() / f"{SESSION_BRIDGE}.json").exists())
        fiche = self.lire(pid=4245)
        self.assertEqual(fiche.get("session_id"), SESSION_BRIDGE)
        self.assertEqual(fiche.get("session_locale"), SESSION_LOCALE)

    def test_sonnette_et_session_id_viennent_du_bridge(self):
        # Panne nommée : la sonnette ou le session_id partent sur l'identifiant local,
        # que claude.ai ne reconnaît pas, au lieu du bridgeSessionId : la session Remote
        # Control ne serait jamais réveillée. Pendant de contrôle : la sonnette suit le
        # bridge, et la fiche d'une session Remote Control reste lisible.
        self.poser_session(4248, {"bridgeSessionId": "cse_bridge05", "sessionId": "loc-5",
                                  "entrypoint": "sdk-cli"})
        r = self.ouvrir("--sonnette", "trig_05", pid=4248)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("pas de sonnette possible", r.stdout)
        fiche = self.lire(pid=4248)
        self.assertEqual(fiche["session_id"], "cse_bridge05")
        self.assertEqual(fiche["sonnette"], "trig_05")
        self.assertEqual(fiche["origine"], "serveur Remote Control")

    def test_fiche_porte_le_nom_d_hote_de_la_machine_distinct_de_l_origine(self):
        # Panne nommée : la fiche ne porte pas le nom d'hôte de la machine. La propriété
        # Machine de Notion reçoit alors l'origine (« serveur Remote Control »…) au lieu du
        # nom que le relevé plans_veille compare à `hostname` : une session du VPS n'est
        # jamais reconnue comme telle. Le nom d'hôte vient d'une surcharge de test
        # (PLAN_EN_COURS_HOTE) pour que l'attendu ne dépende pas du poste ; `origine`
        # reste un champ distinct, il ne sert pas de nom d'hôte.
        self.poser_session(4257, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4257",
                                  "entrypoint": "sdk-cli"})
        r = self.ouvrir(pid=4257, hote="vps-test-4257")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("vps-test-4257", r.stdout)
        fiche = self.lire(pid=4257)
        self.assertEqual(fiche.get("machine"), "vps-test-4257")
        self.assertEqual(fiche["origine"], "serveur Remote Control")

    def test_lire_retrouve_la_fiche_par_identifiant_local_et_par_claude_ai(self):
        # Panne nommée : `lire --session <identifiant local>` ne trouve pas la fiche, alors
        # que l'identifiant local est le seul que la garde de fin de tour possède. Le
        # bridgeSessionId doit retrouver la même fiche (recherche dans les champs).
        self.poser_session(4250, {"bridgeSessionId": "cse_bridge06", "sessionId": "loc-6"})
        self.assertEqual(self.ouvrir(pid=4250).returncode, 0)
        for identifiant in ("loc-6", "cse_bridge06"):
            r = self.lancer("lire", "--session", identifiant)
            self.assertEqual(r.returncode, 0, f"{identifiant} : {r.stderr}")
            self.assertEqual(json.loads(r.stdout)["page_id"], PAGE)

    def test_sans_identifiant_local_la_fiche_est_refusee_et_pas_nommee_par_le_bridge(self):
        # Panne nommée : sans identifiant local (ni CLAUDE_CODE_SESSION_ID, ni sessionId du
        # fichier de session), le script nomme la fiche par le bridgeSessionId, clé que la
        # garde de fin de tour ne peut pas deviner. Il doit sortir en 2 et ne rien écrire.
        # Précondition positive : une session avec identifiant local s'ouvre, sans quoi
        # un script absent (code 2 de Python) passerait ce test.
        self.poser_session(4252, {"bridgeSessionId": "cse_bridge08", "sessionId": "loc-8"})
        self.assertEqual(self.ouvrir(pid=4252).returncode, 0)
        self.poser_session(4251, {"bridgeSessionId": "cse_bridge07"})
        r = self.ouvrir(pid=4251)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse((self.dossier_fiches() / "cse_bridge07.json").exists())

    def test_identifiant_de_session_avec_separateur_de_chemin_est_refuse(self):
        # Panne nommée : `--session ../../x` écrit la fiche hors du dossier des fiches.
        # Le contrôle de forme de l'identifiant est ce qui l'empêche ; le test ne
        # vérifie que l'effet (rien hors du dossier), pas la manière de le vérifier.
        # Précondition positive : avec un identifiant bien formé, `ouvrir` réussit.
        # Sans elle, un script absent (code 2 de Python) passerait ce test.
        ok = self.ouvrir("--session", "cse_valide")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        r = self.ouvrir("--session", "../../x")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse((self.etat / "x.json").exists())
        self.assertFalse((self.etat / "plans-notion" / "x.json").exists())

    def test_attendre_puis_reprendre_repasse_en_cours_et_compte_une_relance(self):
        # Panne nommée : `reprendre` ne repasse pas la fiche en `en cours`, ou ne
        # compte pas la relance ; la garde lit `relances` pour savoir combien de fois
        # la session a été réveillée. Ajouté au-delà de la liste du brief parce que
        # la garde de fin de tour lira exactement ces deux champs.
        self.poser_session(4246, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4246"})
        self.assertEqual(self.ouvrir(pid=4246).returncode, 0)
        self.assertEqual(self.lancer("attendre", "--raison", "relecture humaine", pid=4246).returncode, 0)
        fiche = self.lire(pid=4246)
        self.assertEqual(fiche["etat"], "attente")
        self.assertEqual(fiche["raison_attente"], "relecture humaine")
        self.assertEqual(fiche["relances"], 0)

        self.assertEqual(self.lancer("reprendre", pid=4246).returncode, 0)
        fiche = self.lire(pid=4246)
        self.assertEqual(fiche["etat"], "en cours")
        self.assertIsNone(fiche["raison_attente"])
        self.assertEqual(fiche["relances"], 1)

    def test_cycle_a_merger_attendre_reprendre_restaure_a_merger(self):
        # Panne nommée : `attendre` depuis `a merger` puis `reprendre` remet la fiche en
        # `en cours`. La garde ne réclame alors plus de réveil pour la PR, et la fiche
        # perd l'état qui dit que le plan attend son merge.
        self.poser_session(4253, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4253"})
        self.assertEqual(self.ouvrir(pid=4253).returncode, 0)
        self.assertEqual(self.lancer("pr", "--numero", "9", pid=4253).returncode, 0)
        self.assertEqual(self.lancer("attendre", "--raison", "relecture", pid=4253).returncode, 0)
        self.assertEqual(self.lire(pid=4253)["etat"], "attente")

        self.assertEqual(self.lancer("reprendre", pid=4253).returncode, 0)
        fiche = self.lire(pid=4253)
        self.assertEqual(fiche["etat"], "a merger")
        self.assertEqual(fiche["pr"], 9)
        self.assertEqual(fiche["relances"], 1)

    def test_attendre_deux_fois_puis_reprendre_restaure_l_etat_d_origine(self):
        # Panne nommée : un second `attendre` alors que la fiche est déjà en attente
        # mémorise `attente` comme état d'avant, et `reprendre` rend une fiche en
        # `attente` que la garde laisse passer pour toujours. Le plan doit revenir à
        # `a merger`, pas rester en attente.
        self.poser_session(4254, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4254"})
        self.assertEqual(self.ouvrir(pid=4254).returncode, 0)
        self.assertEqual(self.lancer("pr", "--numero", "10", pid=4254).returncode, 0)
        self.assertEqual(self.lancer("attendre", "--raison", "premier", pid=4254).returncode, 0)
        self.assertEqual(self.lancer("attendre", "--raison", "second", pid=4254).returncode, 0)

        self.assertEqual(self.lancer("reprendre", pid=4254).returncode, 0)
        self.assertEqual(self.lire(pid=4254)["etat"], "a merger")

    def test_attente_reste_un_alias_fonctionnel_de_attendre(self):
        # Panne nommée : le renommage en `attendre` casse les appels qui disent encore
        # `attente` (notes, scripts déjà écrits) : la commande sortirait en 2 au lieu de
        # poser la fiche en attente. Le rc 0 avant toute lecture de la fiche est la
        # précondition : sans lui, un script absent (code 2 de Python) passerait ce test.
        self.poser_session(4255, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4255"})
        self.assertEqual(self.ouvrir(pid=4255).returncode, 0)
        r = self.lancer("attente", "--raison", "relecture", pid=4255)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        fiche = self.lire(pid=4255)
        self.assertEqual(fiche["etat"], "attente")
        self.assertEqual(fiche["raison_attente"], "relecture")
        self.assertEqual(self.lancer("reprendre", pid=4255).returncode, 0)

    def test_etape_remet_les_relances_a_zero(self):
        # Panne nommée : `etape` ne remet pas `relances` à zéro, si bien que la garde compte
        # les relances de toute la session alors que son seuil est « trois relances sans
        # étape nouvelle ». Précondition : deux relances posées avant l'étape, sans quoi un
        # `etape` sans effet passerait ce test.
        self.poser_session(4256, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4256"})
        self.assertEqual(self.ouvrir(pid=4256).returncode, 0)
        for _ in range(2):
            self.assertEqual(self.lancer("attendre", "--raison", "relecture", pid=4256).returncode, 0)
            self.assertEqual(self.lancer("reprendre", pid=4256).returncode, 0)
        self.assertEqual(self.lire(pid=4256)["relances"], 2)

        self.assertEqual(self.lancer("etape", "--faite", "2", "--restantes", "1", pid=4256).returncode, 0)
        self.assertEqual(self.lire(pid=4256)["relances"], 0)

    def test_etape_liste_les_etapes_faites_pas_seulement_des_compteurs(self):
        # Panne nommée : la fiche ne garde que des compteurs (`etapes_faites`,
        # `etapes_restantes`) : après deux `etape`, rien ne dit quelles étapes sont
        # finies, et la fiche ne peut pas les montrer. Attendu : les deux étapes
        # apparaissent comme faites. Les compteurs restent ceux que lit la garde.
        self.poser_session(4258, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4258"})
        self.assertEqual(self.ouvrir(pid=4258).returncode, 0)
        self.assertEqual(self.lancer("etape", "--faite", "1", "--restantes", "2", pid=4258).returncode, 0)
        self.assertEqual(self.lancer("etape", "--faite", "2", "--restantes", "1", pid=4258).returncode, 0)

        fiche = self.lire(pid=4258)
        self.assertEqual(fiche["etapes_liste"], [1, 2])
        self.assertEqual(fiche["etapes_faites"], 2)
        self.assertEqual(fiche["etapes_restantes"], 1)

    def test_fiche_ecrite_sans_liste_reste_lisible_et_etape_la_complete(self):
        # Au-delà du brief (preuve : « une fiche écrite par l'ancienne version doit rester
        # lisible ») : une fiche sans la clé `etapes_liste` doit rester lisible, et `etape`
        # doit la compléter au lieu de sortir en erreur. Panne attrapée : un `etape` qui
        # lit la liste sans la trouver (KeyError) sur une fiche ancienne. Les deux
        # premiers attendus (lecture, `etape` rc 0) passent déjà ; le dernier échoue
        # tant que la liste n'existe pas.
        self.poser_session(4259, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4259"})
        self.assertEqual(self.ouvrir(pid=4259).returncode, 0)
        chemin = self.dossier_fiches() / "loc-4259.json"
        ancienne = json.loads(chemin.read_text(encoding="utf-8"))
        ancienne.pop("etapes_liste", None)
        chemin.write_text(json.dumps(ancienne), encoding="utf-8")

        self.assertEqual(self.lire(pid=4259)["etat"], "en cours")
        self.assertEqual(self.lancer("etape", "--faite", "1", "--restantes", "0", pid=4259).returncode, 0)
        self.assertEqual(self.lire(pid=4259)["etapes_liste"], [1])

    def test_dossier_des_fiches_en_mode_700(self):
        # Panne nommée : les fiches (chemins de worktree, numéros de PR) sont lisibles
        # par d'autres comptes du poste. Le brief fixe le dossier en mode 700 ; le
        # fichier doit l'être aussi, sans bit pour le groupe ni les autres.
        self.poser_session(4247, {"bridgeSessionId": SESSION_BRIDGE, "sessionId": "loc-4247"})
        self.assertEqual(self.ouvrir(pid=4247).returncode, 0)
        self.assertEqual(stat.S_IMODE(os.stat(self.dossier_fiches()).st_mode), 0o700)
        mode_fichier = stat.S_IMODE(os.stat(self.dossier_fiches() / "loc-4247.json").st_mode)
        self.assertEqual(mode_fichier & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
