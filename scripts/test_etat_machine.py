"""Tests de ``etat-machine.py`` sur des racines ``/proc`` fabriquées.

Le script dit si la machine peut recevoir une action lourde : ``libre``,
``chargée`` ou ``saturée``. Ce qu'il faut prouver, c'est qu'il **lit** la
racine ``/proc`` qu'on lui donne et que le verdict suit les règles du plan, pas
l'état du poste où le test tourne : chaque cas fabrique sa propre racine
(``loadavg``, ``meminfo``, ``cpuinfo``, ``pressure/*``, un dossier par
processus) et la passe par ``--proc``. Aucun test ne lit le vrai ``/proc``, et
aucun n'écrit dans le vrai ``~/.local/state`` : ``XDG_STATE_HOME`` pointe vers
un dossier jetable.

Les attendus viennent des règles du plan, pas du code : ``chargée`` si la
pression CPU « some » sur 10 s atteint 50 ou si une famille lourde tourne hors
du détenteur du jeton ; ``saturée`` si la pression mémoire « full » sur 60 s
atteint 40 ou s'il reste moins de 1,5 Go disponibles ; la charge moyenne
figure dans les causes mais ne décide jamais. Le script est lancé comme un vrai
processus : on observe sa sortie et son code de retour.

Le jeton des actions lourdes (``prendre``, ``rendre``, ``qui``) se prouve de la
même façon : le détenteur est un PID de la racine ``/proc`` fabriquée (vivant
tant que son dossier existe, mort quand on le supprime), et l'état vit sous
``XDG_STATE_HOME``. Codes de sortie attendus : 0 accordé, 3 refusé car occupé,
4 refusé car la machine est saturée.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "etat-machine.py"


class FauxProc:
    """Une racine ``/proc`` fabriquée : calme par défaut, 6 cœurs, 5 Go libres."""

    def __init__(self, dossier: Path, *, cpus=6, charge="0.50 0.40 0.30",
                 cpu_some_avg10=1.0, mem_full_avg60=0.0, mem_disponible_ko=5_000_000):
        self.racine = dossier
        (dossier / "pressure").mkdir(parents=True)
        (dossier / "loadavg").write_text(f"{charge} 1/300 12345\n")
        (dossier / "cpuinfo").write_text(
            "".join(f"processor\t: {i}\nmodel name\t: faux\n\n" for i in range(cpus)))
        (dossier / "meminfo").write_text(
            f"MemTotal:       11000000 kB\nMemFree:         1000000 kB\n"
            f"MemAvailable:   {mem_disponible_ko} kB\n")
        self.pression(cpu_some_avg10=cpu_some_avg10, mem_full_avg60=mem_full_avg60)

    def pression(self, *, cpu_some_avg10, mem_full_avg60):
        (self.racine / "pressure" / "cpu").write_text(
            f"some avg10={cpu_some_avg10:.2f} avg60=0.00 avg300=0.00 total=1\n")
        (self.racine / "pressure" / "memory").write_text(
            "some avg10=0.00 avg60=0.00 avg300=0.00 total=1\n"
            f"full avg10=0.00 avg60={mem_full_avg60:.2f} avg300=0.00 total=1\n")

    def processus(self, pid, argv, ppid=1, demarrage=1000):
        """Ajoute un processus vivant : ``cmdline`` (arguments séparés par NUL) et ``stat``."""
        dossier = self.racine / str(pid)
        dossier.mkdir()
        (dossier / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
        # Format de proc(5) : « pid (comm) état ppid … » ; démarrage = champ 22.
        champs_apres_ppid = ["0"] * 17 + [str(demarrage)] + ["0"] * 10
        (dossier / "stat").write_text(
            f"{pid} ({Path(argv[0]).name[:15]}) S {ppid} " + " ".join(champs_apres_ppid) + "\n")


class EtatMachineTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        self.etat = self.base / "etat"
        self.proc = FauxProc(self.base / "proc")
        # Le profil machine du poste ne doit jamais interférer : config jetable, variable retirée.
        self.env = {**os.environ, "XDG_STATE_HOME": str(self.etat),
                    "XDG_CONFIG_HOME": str(self.base / "config")}
        self.env.pop("PLANS_NOTION_MACHINE_PROFIL", None)

    def lancer(self, *args, proc=None, env=None):
        racine = (proc or self.proc).racine
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--proc", str(racine)],
            capture_output=True, text=True, env=env or self.env, timeout=30)

    def releve(self, *args, proc=None):
        """Le relevé en JSON, après avoir vérifié que le script a tourné."""
        r = self.lancer("releve", "--json", *args, proc=proc)
        self.assertEqual(r.returncode, 0, msg=f"stderr: {r.stderr}")
        return json.loads(r.stdout)


class Verdict(EtatMachineTestCase):
    def test_machine_calme_est_libre_et_ne_nomme_aucune_famille(self):
        rel = self.releve()
        self.assertEqual(rel["verdict"], "libre")
        self.assertEqual(rel["familles"], [])

    def test_forte_charge_moyenne_seule_ne_rend_pas_la_machine_chargee(self):
        # POC du 2026-10-01 : la charge moyenne met 1 à 2 minutes à retomber
        # après une action. Charge 7 sur 6 cœurs, pression CPU sur 10 s à 5 % :
        # la machine est libre, et la charge est citée sans décider.
        self.proc.pression(cpu_some_avg10=5.0, mem_full_avg60=0.0)
        (self.proc.racine / "loadavg").write_text("7.00 6.50 6.00 1/300 12345\n")
        rel = self.releve()
        self.assertEqual(rel["verdict"], "libre")
        charge = [c for c in rel["causes"] if c["code"] == "charge-moyenne"]
        self.assertEqual(len(charge), 1)
        self.assertFalse(charge[0]["decisive"])

    def test_pression_cpu_sur_10s_a_60_rend_chargee(self):
        self.proc.pression(cpu_some_avg10=60.0, mem_full_avg60=0.0)
        rel = self.releve()
        self.assertEqual(rel["verdict"], "chargée")
        decisives = [c["code"] for c in rel["causes"] if c["decisive"]]
        self.assertEqual(decisives, ["pression-cpu"])

    def test_seuil_de_pression_cpu_est_inclusif_a_50(self):
        for valeur, attendu in ((49.9, "libre"), (50.0, "chargée")):
            with self.subTest(cpu_some_avg10=valeur):
                self.proc.pression(cpu_some_avg10=valeur, mem_full_avg60=0.0)
                self.assertEqual(self.releve()["verdict"], attendu)

    def test_pression_memoire_full_a_45_rend_saturee(self):
        self.proc.pression(cpu_some_avg10=1.0, mem_full_avg60=45.0)
        rel = self.releve()
        self.assertEqual(rel["verdict"], "saturée")
        decisives = [c["code"] for c in rel["causes"] if c["decisive"]]
        self.assertEqual(decisives, ["pression-memoire"])

    def test_seuil_de_pression_memoire_est_inclusif_a_40(self):
        for valeur, attendu in ((39.9, "libre"), (40.0, "saturée")):
            with self.subTest(mem_full_avg60=valeur):
                self.proc.pression(cpu_some_avg10=1.0, mem_full_avg60=valeur)
                self.assertEqual(self.releve()["verdict"], attendu)

    def test_moins_de_1_5_go_disponible_rend_saturee(self):
        # 1,5 Go = 1 572 864 ko : un ko de moins sature, pile 1,5 Go non.
        for ko, attendu in ((1_572_863, "saturée"), (1_572_864, "libre")):
            with self.subTest(MemAvailable_ko=ko):
                (self.proc.racine / "meminfo").write_text(
                    f"MemTotal: 11000000 kB\nMemAvailable: {ko} kB\n")
                self.assertEqual(self.releve()["verdict"], attendu)

    def test_saturee_l_emporte_sur_chargee(self):
        self.proc.pression(cpu_some_avg10=90.0, mem_full_avg60=75.0)
        self.proc.processus(300, ["pytest", "-q"])
        self.assertEqual(self.releve()["verdict"], "saturée")

    def test_machine_sans_pression_ni_meminfo_ne_fait_pas_planter_le_releve(self):
        # Hors Linux ou conteneur sans PSI : on répond sur ce qu'on lit.
        (self.proc.racine / "pressure" / "cpu").unlink()
        (self.proc.racine / "pressure" / "memory").unlink()
        (self.proc.racine / "meminfo").unlink()
        rel = self.releve()
        self.assertEqual(rel["verdict"], "libre")


class FamillesLourdes(EtatMachineTestCase):
    def test_un_pytest_et_un_navigateur_sans_tete_rendent_chargee_avec_les_deux_noms(self):
        self.proc.processus(400, ["/usr/bin/python3", "-m", "pytest", "-q", "tests/"])
        self.proc.processus(401, ["/snap/chromium/1/chrome", "--headless=new", "--no-sandbox",
                                  "about:blank"])
        rel = self.releve()
        self.assertEqual(rel["verdict"], "chargée")
        self.assertEqual(sorted(rel["familles"]), ["navigateur-sans-tete", "suite-de-tests"])

    def test_chaque_famille_lourde_rend_chargee_sous_son_nom(self):
        cas = {
            "suite-de-tests": ["node", "/repo/node_modules/vitest/vitest.mjs", "run"],
            "navigateur-sans-tete": ["/ms-playwright/chromium_headless_shell-1/headless_shell",
                                     "--remote-debugging-pipe"],
            "claude-plugin-eval": ["claude", "plugin", "eval", "--runs", "3"],
            "conteneur-de-runner": ["/opt/gha-runner/bin/Runner.Worker", "spawnclient", "3", "4"],
            "session-claude-rejeu": ["claude", "-p", "--model", "sonnet", "rejoue ce cas"],
        }
        for nom, argv in cas.items():
            with self.subTest(famille=nom):
                racine = self.base / f"proc-{nom}"
                faux = FauxProc(racine)
                faux.processus(500, argv)
                rel = self.releve(proc=faux)
                self.assertEqual(rel["verdict"], "chargée")
                self.assertIn(nom, rel["familles"])

    def test_un_grep_ou_un_editeur_qui_citent_pytest_ne_sont_pas_une_suite_de_tests(self):
        self.proc.processus(600, ["grep", "-rn", "pytest", "scripts/"])
        self.proc.processus(601, ["vim", "test_pytest_plugin.py"])
        self.proc.processus(602, ["claude", "remote-control", "--name", "vps"])
        self.proc.processus(603, ["/opt/gha-runner/bin/Runner.Listener", "run"])
        rel = self.releve()
        self.assertEqual(rel["verdict"], "libre")
        self.assertEqual(rel["familles"], [])

    def test_un_docker_run_qui_heberge_un_serveur_mcp_n_est_pas_un_conteneur_de_runner(self):
        # Relevé réel du 2026-10-01 sur le VPS : des serveurs MCP vivent des
        # heures dans `docker run -i --rm … stdio` sans rien peser. Seul
        # Runner.Worker (un job de runner en cours) compte.
        self.proc.processus(610, ["/usr/bin/docker", "run", "-i", "--rm", "-e", "TOKEN",
                                  "ghcr.io/github/github-mcp-server", "stdio"])
        rel = self.releve()
        self.assertEqual(rel["verdict"], "libre")
        self.assertEqual(rel["familles"], [])

    def test_une_famille_lourde_descendante_du_detenteur_ne_compte_pas(self):
        # Le détenteur du jeton (PID 700) a lancé la suite : elle ne rend pas la
        # machine « chargée » pour lui-même, ni ses sous-processus, à n'importe
        # quelle profondeur.
        self.proc.processus(700, ["bash", "preuve.sh"])
        self.proc.processus(701, ["bash", "-c", "lance"], ppid=700)
        self.proc.processus(702, ["python3", "-m", "pytest"], ppid=701)
        self.proc.processus(703, ["/snap/chromium/1/chrome", "--headless"], ppid=702)
        rel = self.releve("--hors-pid", "700")
        self.assertEqual(rel["verdict"], "libre")
        self.assertEqual(rel["familles"], [])

    def test_une_famille_lourde_hors_du_detenteur_rend_chargee_meme_si_le_detenteur_travaille(self):
        self.proc.processus(700, ["bash", "preuve.sh"])
        self.proc.processus(702, ["python3", "-m", "pytest"], ppid=700)
        self.proc.processus(800, ["python3", "-m", "pytest"], ppid=1)  # une autre session
        rel = self.releve("--hors-pid", "700")
        self.assertEqual(rel["verdict"], "chargée")
        self.assertEqual(rel["familles"], ["suite-de-tests"])


class SortieTexte(EtatMachineTestCase):
    def test_sans_json_la_premiere_ligne_est_le_verdict_seul_pour_un_script_shell(self):
        self.proc.pression(cpu_some_avg10=60.0, mem_full_avg60=0.0)
        r = self.lancer("releve")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "chargée")
        self.assertGreater(len(r.stdout.splitlines()), 1, "les causes suivent le verdict")


class Jeton(EtatMachineTestCase):
    """Le jeton des actions lourdes : deux places, des détenteurs, des PID qui font foi."""

    def setUp(self):
        super().setUp()
        for pid in (900, 901, 902, 903):
            self.proc.processus(pid, ["bash", f"session-{pid}.sh"])

    def prendre(self, action="e2e", pid=900, plan="Plan A", *extra, **kw):
        return self.lancer("prendre", action, "--plan", plan, "--pid", str(pid), *extra, **kw)

    def qui(self):
        r = self.lancer("qui", "--json")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        return json.loads(r.stdout)["detenteurs"]

    # -- exclusion mutuelle : deux places, la troisième attend ou échoue ---------
    def test_la_troisieme_prise_attend_puis_echoue_apres_attendre_1(self):
        self.assertEqual(self.prendre("e2e", 900, "Plan A").returncode, 0)
        self.assertEqual(self.prendre("suite", 901, "Plan B").returncode, 0)
        debut = time.monotonic()
        troisieme = self.prendre("lint", 902, "Plan C", "--attendre", "1")
        duree = time.monotonic() - debut
        self.assertEqual(troisieme.returncode, 3, msg=troisieme.stderr)
        self.assertGreaterEqual(duree, 0.9, "elle doit avoir attendu la seconde demandée")
        self.assertEqual([d["pid"] for d in self.qui()], [900, 901],
                         "les détenteurs n'ont pas changé")
        # Le refus cite tous les détenteurs, pas seulement le premier.
        self.assertIn("Plan A", troisieme.stderr)
        self.assertIn("Plan B", troisieme.stderr)

    def test_sans_attendre_la_troisieme_prise_est_refusee_sur_le_champ(self):
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        self.assertEqual(self.prendre("suite", 901).returncode, 0)
        self.assertEqual(self.prendre("lint", 902).returncode, 3)

    def test_une_prise_qui_attend_obtient_une_place_des_qu_une_est_rendue(self):
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        self.assertEqual(self.prendre("suite", 901).returncode, 0)
        troisieme = subprocess.Popen(
            [sys.executable, str(SCRIPT), "prendre", "lint", "--plan", "Plan C", "--pid", "902",
             "--attendre", "20", "--proc", str(self.proc.racine)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=self.env)
        self.addCleanup(troisieme.kill)
        time.sleep(0.5)
        self.assertIsNone(troisieme.poll(), "elle attend tant que les deux places sont tenues")
        self.assertEqual(self.lancer("rendre", "--pid", "900").returncode, 0)
        self.assertEqual(troisieme.wait(timeout=15), 0)
        self.assertEqual([d["pid"] for d in self.qui()], [901, 902])

    def test_des_prises_simultanees_ne_donnent_que_deux_places(self):
        racine = str(self.proc.racine)
        procs = [subprocess.Popen(
            [sys.executable, str(SCRIPT), "prendre", "e2e", "--plan", f"Plan {pid}",
             "--pid", str(pid), "--proc", racine],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=self.env)
            for pid in (900, 901, 902)]
        codes = sorted(p.wait(timeout=30) for p in procs)
        self.assertEqual(codes, [0, 0, 3])
        self.assertEqual(len(self.qui()), 2)

    def test_rendre_libere_le_jeton_pour_la_prise_suivante(self):
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        self.assertEqual(self.lancer("rendre", "--pid", "900").returncode, 0)
        self.assertEqual(self.qui(), [])
        self.assertEqual(self.prendre("suite", 901).returncode, 0)

    def test_rendre_par_un_pid_sans_place_ne_libere_pas_les_places_des_detenteurs(self):
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        self.assertEqual(self.prendre("suite", 901).returncode, 0)
        self.lancer("rendre", "--pid", "902")
        self.assertEqual([d["pid"] for d in self.qui()], [900, 901])
        self.assertEqual(self.prendre("lint", 902).returncode, 3)

    def test_reprendre_avec_le_meme_pid_ne_se_bloque_pas_soi_meme(self):
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        self.assertEqual(len(self.qui()), 1)
        # Reprendre ne consomme pas une seconde place : la deuxième reste libre.
        self.assertEqual(self.prendre("suite", 901).returncode, 0)
        self.assertEqual([d["pid"] for d in self.qui()], [900, 901])

    # -- détenteur mort ---------------------------------------------------------
    def test_un_jeton_tenu_par_un_pid_mort_est_repris(self):
        self.assertEqual(self.prendre("e2e", 900, "Plan A").returncode, 0)
        shutil.rmtree(self.proc.racine / "900")  # la session de Plan A est morte sans rendre
        reprise = self.prendre("suite", 901, "Plan B")
        self.assertEqual(reprise.returncode, 0, msg=reprise.stderr)
        detenteurs = self.qui()
        self.assertEqual([(d["pid"], d["action"], d["plan"]) for d in detenteurs],
                         [(901, "suite", "Plan B")])

    def test_un_pid_reutilise_par_un_autre_processus_ne_garde_pas_le_jeton(self):
        # Le noyau recycle les PID : 900 existe encore, mais c'est un autre
        # processus (autre heure de démarrage) que celui qui avait pris le jeton.
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        shutil.rmtree(self.proc.racine / "900")
        self.proc.processus(900, ["firefox"], demarrage=987654)
        self.assertEqual(self.prendre("suite", 901).returncode, 0)

    def test_qui_n_affiche_pas_un_detenteur_mort(self):
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        shutil.rmtree(self.proc.racine / "900")
        self.assertEqual(self.qui(), [])

    def test_un_fichier_d_etat_illisible_vaut_jeton_libre(self):
        dossier = self.etat / "plans-notion"
        dossier.mkdir(parents=True)
        (dossier / "lourd.lock").write_text("{pas du json")
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)

    # -- qui --------------------------------------------------------------------
    def test_qui_dit_l_action_et_le_plan_du_detenteur(self):
        self.assertEqual(self.prendre("e2e vahiny", 900, "Plan A — refonte").returncode, 0)
        detenteurs = self.qui()
        self.assertEqual(len(detenteurs), 1)
        self.assertEqual(detenteurs[0]["pid"], 900)
        self.assertEqual(detenteurs[0]["action"], "e2e vahiny")
        self.assertEqual(detenteurs[0]["plan"], "Plan A — refonte")
        self.assertTrue(detenteurs[0]["depuis"], "l'heure de la prise est écrite")

    def test_qui_sur_un_jeton_libre_ne_nomme_personne(self):
        self.assertEqual(self.qui(), [])
        r = self.lancer("qui")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[0], "libre")

    def test_qui_en_texte_nomme_l_action_et_le_plan_pour_un_humain(self):
        self.prendre("suite hermes", 900, "Plan Z")
        sortie = self.lancer("qui").stdout
        self.assertIn("suite hermes", sortie)
        self.assertIn("Plan Z", sortie)

    # -- saturation -------------------------------------------------------------
    def test_le_jeton_est_refuse_si_la_machine_est_saturee(self):
        self.proc.pression(cpu_some_avg10=1.0, mem_full_avg60=45.0)
        r = self.prendre("e2e", 900)
        self.assertEqual(r.returncode, 4, msg=r.stderr)
        self.assertEqual(self.qui(), [], "aucun jeton n'a été posé")

    def test_une_machine_chargee_accorde_quand_meme_le_jeton(self):
        # Seule la saturation refuse : « chargée » veut dire « prévenir les
        # autres », pas « ne pas y aller ».
        self.proc.pression(cpu_some_avg10=80.0, mem_full_avg60=0.0)
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)

    def test_une_saturee_ne_fait_pas_attendre_meme_avec_attendre(self):
        self.proc.pression(cpu_some_avg10=1.0, mem_full_avg60=45.0)
        debut = time.monotonic()
        r = self.prendre("e2e", 900, "Plan A", "--attendre", "5")
        self.assertEqual(r.returncode, 4)
        self.assertLess(time.monotonic() - debut, 4, "attendre n'arrange pas une saturation")

    # -- lien avec le relevé ----------------------------------------------------
    def test_ce_que_le_detenteur_lance_ne_rend_pas_le_releve_chargee_pour_lui_meme(self):
        self.proc.processus(910, ["python3", "-m", "pytest"], ppid=900)
        self.assertEqual(self.releve()["verdict"], "chargée", "sans jeton, une suite pèse")
        self.assertEqual(self.prendre("suite", 900).returncode, 0)
        rel = self.releve()
        self.assertEqual(rel["verdict"], "libre")
        self.assertEqual(rel["familles"], [])

    def test_la_suite_d_une_autre_session_reste_comptee_malgre_le_jeton(self):
        self.proc.processus(910, ["python3", "-m", "pytest"], ppid=900)
        self.proc.processus(920, ["python3", "-m", "pytest"], ppid=1)
        self.assertEqual(self.prendre("suite", 900).returncode, 0)
        self.assertEqual(self.releve()["familles"], ["suite-de-tests"])
        self.assertEqual(self.releve()["verdict"], "chargée")

    # -- où vit l'état, qui est le détenteur par défaut ------------------------
    def test_l_etat_vit_sous_xdg_state_home_plans_notion_lourd_lock(self):
        self.assertEqual(self.prendre("e2e", 900).returncode, 0)
        self.assertTrue((self.etat / "plans-notion" / "lourd.lock").is_file())

    def test_sans_xdg_state_home_l_etat_va_sous_home_local_state(self):
        home = self.base / "home"
        env = {k: v for k, v in self.env.items() if k != "XDG_STATE_HOME"}
        env["HOME"] = str(home)
        r = self.prendre("e2e", 900, env=env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertTrue((home / ".local" / "state" / "plans-notion" / "lourd.lock").is_file())

    def test_sans_pid_le_detenteur_est_le_processus_parent_du_script(self):
        # `prendre` est appelé depuis un script shell qui continue ensuite : le
        # détenteur est ce shell, pas le Python qui s'arrête aussitôt.
        moi = os.getpid()
        self.proc.processus(moi, ["bash", "preuve.sh"])
        r = self.lancer("prendre", "e2e", "--plan", "Plan A")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual([d["pid"] for d in self.qui()], [moi])

    def test_prendre_pour_un_pid_inexistant_est_refuse_sans_poser_de_jeton(self):
        r = self.prendre("e2e", 4242)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.qui(), [])


class ProfilMachine(EtatMachineTestCase):
    """Le profil machine : ``PLANS_NOTION_MACHINE_PROFIL``, ou le fichier par défaut.

    Sans profil, le VPS garde ses valeurs (deux places, seuils d'origine). Avec un
    profil, ses clés remplacent les constantes du module ; une erreur de profil
    sort en code 2, sur toutes les commandes, avec un message « profil machine : ».
    """

    def setUp(self):
        super().setUp()
        for pid in (900, 901, 902, 903, 904):
            self.proc.processus(pid, ["bash", f"session-{pid}.sh"])

    def poser_profil(self, contenu: str) -> Path:
        """Écrit le profil hors du dépôt et pose la variable qui le désigne."""
        chemin = self.base / "profil.json"
        chemin.write_text(contenu)
        self.env["PLANS_NOTION_MACHINE_PROFIL"] = str(chemin)
        return chemin

    def prendre(self, pid, plan="Plan A"):
        return self.lancer("prendre", "e2e", "--plan", plan, "--pid", str(pid))

    def assertProfilRefuse(self, r, chemin):
        """Code 2, et un message « profil machine : » qui cite le fichier fautif."""
        self.assertEqual(r.returncode, 2, msg=r.stdout + r.stderr)
        self.assertIn("profil machine :", r.stderr)
        self.assertIn(str(chemin), r.stderr)

    def test_sans_profil_le_jeton_garde_deux_places_comme_sur_le_vps(self):
        self.assertEqual(self.prendre(900).returncode, 0)
        self.assertEqual(self.prendre(901).returncode, 0)
        troisieme = self.prendre(902)
        self.assertEqual(troisieme.returncode, 3, msg=troisieme.stderr)

    def test_profil_places_lourdes_4_accorde_quatre_prises_et_refuse_la_cinquieme(self):
        # Profil du Mac (POC du 2026-10-16). Le libellé « machine » est une clé valide.
        self.poser_profil('{"machine": "mac-m1max-64go", "places_lourdes": 4}')
        for pid in (900, 901, 902, 903):
            with self.subTest(prise=pid):
                self.assertEqual(self.prendre(pid).returncode, 0)
        cinquieme = self.prendre(904)
        self.assertEqual(cinquieme.returncode, 3, msg=cinquieme.stderr)
        self.assertIn("(4 sur 4)", cinquieme.stderr)

    def test_seuil_memoire_disponible_du_profil_rend_saturee_une_machine_libre_par_defaut(self):
        # 5 Go libres : « libre » avec les seuils d'origine (1,5 Go). Le profil relève
        # le seuil à 6 Go : la même machine devient « saturée », et le détail cite 5,7 Go.
        self.assertEqual(self.releve()["verdict"], "libre")
        self.poser_profil('{"seuil_mem_disponible_ko": 6000000}')
        rel = self.releve()
        self.assertEqual(rel["verdict"], "saturée")
        detail = [c["detail"] for c in rel["causes"] if c["code"] == "memoire-disponible"]
        self.assertEqual(len(detail), 1)
        self.assertIn("seuil 5.7 Go", detail[0])

    def test_json_invalide_est_une_erreur_code_2_sur_toutes_les_commandes(self):
        chemin = self.poser_profil('{"places_lourdes": 4,')
        commandes = {
            "releve": ["releve"],
            "prendre": ["prendre", "e2e", "--plan", "Plan A", "--pid", "900"],
            "rendre": ["rendre", "--pid", "900"],
            "qui": ["qui"],
        }
        for nom, args in commandes.items():
            with self.subTest(commande=nom):
                self.assertProfilRefuse(self.lancer(*args), chemin)

    def test_cle_inconnue_est_une_erreur_et_non_une_faute_de_frappe_passee_en_silence(self):
        chemin = self.poser_profil('{"places_lourd": 4}')
        self.assertProfilRefuse(self.prendre(900), chemin)

    def test_places_lourdes_zero_est_une_erreur_code_2(self):
        chemin = self.poser_profil('{"places_lourdes": 0}')
        self.assertProfilRefuse(self.prendre(900), chemin)

    def test_variable_posee_vers_un_fichier_absent_est_une_erreur_sans_repli(self):
        absent = self.base / "n-existe-pas.json"
        self.env["PLANS_NOTION_MACHINE_PROFIL"] = str(absent)
        self.assertProfilRefuse(self.prendre(900), absent)

    def test_sans_variable_le_profil_par_defaut_sous_xdg_config_home_est_lu(self):
        # Aucune variable posée : c'est le fichier par défaut qui fait foi.
        defaut = self.base / "config" / "plans-notion" / "machine.json"
        defaut.parent.mkdir(parents=True)
        defaut.write_text('{"places_lourdes": 3}')
        for pid in (900, 901, 902):
            with self.subTest(prise=pid):
                self.assertEqual(self.prendre(pid).returncode, 0)
        self.assertEqual(self.prendre(903).returncode, 3)

    def test_valeur_de_mauvais_type_est_une_erreur_y_compris_un_booleen(self):
        # Garde-fou : en Python, ``True`` est un ``int``. Sans contrôle de type,
        # ``{"places_lourdes": true}`` donnerait une seule place sans rien dire.
        for contenu in ('{"places_lourdes": true}', '{"places_lourdes": "4"}',
                        '{"seuil_cpu_some_avg10": "50"}'):
            with self.subTest(profil=contenu):
                chemin = self.poser_profil(contenu)
                self.assertProfilRefuse(self.prendre(900), chemin)

    def test_seuil_de_pression_infini_par_1e999_est_une_erreur_code_2(self):
        # json.loads lit 1e999 comme inf sans passer par parse_constant : seul le
        # contrôle de plage (0 à 100) le refuse. Un seuil infini ne serait jamais atteint.
        chemin = self.poser_profil('{"seuil_cpu_some_avg10": 1e999}')
        r = self.prendre(900)
        self.assertProfilRefuse(r, chemin)
        self.assertIn("entre 0 et 100", r.stderr)

    def test_seuil_de_pression_negatif_est_une_erreur_code_2(self):
        chemin = self.poser_profil('{"seuil_mem_full_avg60": -1}')
        r = self.prendre(900)
        self.assertProfilRefuse(r, chemin)
        self.assertIn("entre 0 et 100", r.stderr)

    def test_seuil_de_pression_au_dessus_de_100_est_une_erreur_code_2(self):
        # Une pression PSI est un pourcentage : au-delà de 100, le seuil ne peut plus
        # être atteint, c'est une faute de saisie.
        chemin = self.poser_profil('{"seuil_cpu_some_avg10": 101}')
        r = self.prendre(900)
        self.assertProfilRefuse(r, chemin)
        self.assertIn("entre 0 et 100", r.stderr)

    def test_seuil_de_pression_entier_geant_est_une_erreur_code_2_sans_traceback(self):
        # Un entier de 401 chiffres : float() dans la comparaison de finitude levait
        # OverflowError, sortie en traceback (rc 1) au lieu du code 2 promis.
        for cle in ("seuil_cpu_some_avg10", "seuil_mem_full_avg60"):
            with self.subTest(cle=cle):
                chemin = self.poser_profil('{"%s": %s}' % (cle, "1" + "0" * 400))
                r = self.prendre(900)
                self.assertProfilRefuse(r, chemin)
                self.assertIn("entre 0 et 100", r.stderr)
                self.assertNotIn("Traceback", r.stderr)

    def test_seuils_de_pression_aux_bornes_0_et_100_sont_acceptes(self):
        # Contrôle : les bornes restent permises. ``releve`` renvoie toujours 0 (le
        # verdict est dans le JSON), donc seul le message d'erreur de profil compte.
        self.poser_profil('{"seuil_mem_full_avg60": 0, "seuil_cpu_some_avg10": 100}')
        r = self.lancer("releve", "--json")
        self.assertNotIn("profil machine", r.stderr)
        self.assertEqual(r.returncode, 0, msg=r.stderr)


if __name__ == "__main__":
    unittest.main()
