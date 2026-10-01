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
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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
        self.env = {**os.environ, "XDG_STATE_HOME": str(self.etat)}

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


if __name__ == "__main__":
    unittest.main()
