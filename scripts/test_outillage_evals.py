"""Tests des garde-fous de ``evals/outillage/``.

Lancés par la CI (``python3 -m unittest discover -s scripts``), sans
dépendance : ``unittest`` est dans la bibliothèque standard.

Règle de sécurité du fichier : ``preparer-runner.sh`` n'est JAMAIS lancé avec
``GITHUB_ACTIONS=true`` ici. Sur cette machine il ferait un vrai ``sudo`` (levée
d'une restriction AppArmor sur un VPS). Même avec de faux binaires, on n'ouvre
pas cette porte : ``_environnement`` refuse ``true``.

Le script testé se choisit par ``PREPARER_RUNNER`` (défaut : le vrai). C'est ce
qui permet de prouver que le test mord, en le pointant sur un mutant où le
garde-fou est déplacé sous le premier ``sudo``.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PREPARER = Path(
    os.environ.get("PREPARER_RUNNER") or RACINE / "evals" / "outillage" / "preparer-runner.sh"
)
LANCER = RACINE / "evals" / "outillage" / "lancer.sh"
CI = RACINE / ".github" / "workflows" / "ci.yml"
ETAT_MACHINE = (
    RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "etat-machine.py"
)

BASH = shutil.which("bash") or "/bin/bash"

# Commandes qu'aucun chemin « refus » ne doit atteindre.
COMMANDES_INTERDITES_PREPARER = ("sudo", "apt-get", "sysctl", "npm", "bwrap")


class _FauxBinaires:
    """Un dossier de faux exécutables qui laissent une trace puis échouent."""

    def __init__(self, noms: tuple[str, ...]):
        self._tmp = tempfile.TemporaryDirectory(prefix="faux-bin-")
        self.dossier = Path(self._tmp.name) / "bin"
        self.dossier.mkdir()
        self.temoin = Path(self._tmp.name) / "temoin.txt"
        for nom in noms:
            faux = self.dossier / nom
            faux.write_text(
                "#!/bin/sh\n"
                f'echo "{nom} $*" >> "{self.temoin}"\n'
                "exit 99\n"
            )
            faux.chmod(0o755)

    def nettoyer(self) -> None:
        self._tmp.cleanup()

    def traces(self) -> str:
        return self.temoin.read_text() if self.temoin.exists() else ""


def _environnement(faux: _FauxBinaires, github_actions: str | None) -> dict[str, str]:
    """Environnement d'exécution : PATH préfixé des faux binaires, sans jeton."""
    assert github_actions != "true", (
        "interdit : lancer un script d'outillage avec GITHUB_ACTIONS=true "
        "ferait un vrai sudo sur cette machine"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("GITHUB_ACTIONS", "CLAUDE_CODE_OAUTH_TOKEN")
    }
    env["PATH"] = f"{faux.dossier}{os.pathsep}{env.get('PATH', '')}"
    if github_actions is not None:
        env["GITHUB_ACTIONS"] = github_actions
    return env


class PreparerRunnerRefuseHorsRunner(unittest.TestCase):
    def _lancer(self, github_actions: str | None) -> tuple[subprocess.CompletedProcess, str]:
        faux = _FauxBinaires(COMMANDES_INTERDITES_PREPARER)
        self.addCleanup(faux.nettoyer)
        resultat = subprocess.run(
            [BASH, str(PREPARER)],
            env=_environnement(faux, github_actions),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return resultat, faux.traces()

    def _verifier_refus(self, github_actions: str | None) -> None:
        resultat, traces = self._lancer(github_actions)
        # Aucun faux binaire appelé : le refus précède tout sudo / apt / sysctl.
        self.assertEqual(traces, "", f"commande(s) atteinte(s) avant le refus :\n{traces}")
        self.assertNotEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("hors runner GitHub", resultat.stderr)

    def test_sans_github_actions_refuse_avant_tout_sudo(self):
        self._verifier_refus(None)

    def test_github_actions_false_refuse_avant_tout_sudo(self):
        self._verifier_refus("false")


class LancerSansArgumentsAfficheUsage(unittest.TestCase):
    def _verifier_usage(self, arguments: list[str]) -> None:
        faux = _FauxBinaires(("claude",))
        self.addCleanup(faux.nettoyer)
        resultat = subprocess.run(
            [BASH, str(LANCER), *arguments],
            env=_environnement(faux, None),
            capture_output=True,
            text=True,
            timeout=30,
        )
        # 64 = EX_USAGE (sysexits.h), le code annoncé par l'en-tête du script.
        self.assertEqual(resultat.returncode, 64, resultat.stderr)
        self.assertIn("Usage", resultat.stderr)
        self.assertEqual(faux.traces(), "", "claude a été lancé malgré l'usage invalide")

    def test_sans_argument_code_64_et_claude_jamais_lance(self):
        self._verifier_usage([])

    def test_un_seul_argument_code_64_et_claude_jamais_lance(self):
        self._verifier_usage(["un-plugin"])


class _LancementLocal:
    """Un lancement de ``lancer.sh`` avec un faux ``claude`` et un faux ``gh``.

    Rien n'est réel : ``claude`` laisse une trace dans ``temoin.txt`` puis rend
    ``code_claude`` ; ``gh`` répond ce qu'on lui dit, sans réseau. Le jeton
    machine, lui, est le vrai (``etat-machine.py``), mais son fichier d'état vit
    dans un ``XDG_STATE_HOME`` jetable : le vrai ``~/.local/state`` n'est jamais
    touché, et le vrai ``claude plugin eval`` n'est jamais lancé.

    Le faux ``gh`` imite la sortie de ``gh run list`` (un numéro de run par
    ligne) et de ``gh run view`` (un nom de job en cours par ligne), les deux
    seules commandes dont le lanceur a besoin ; il ne vérifie pas leurs
    arguments.
    """

    def __init__(self, cas: unittest.TestCase, *, runs_en_cours: str = "",
                 jobs_en_cours: str = "", gh_en_echec: bool = False, code_claude: int = 0):
        self.faux = _FauxBinaires(("claude", "gh"))
        cas.addCleanup(self.faux.nettoyer)
        self.tmp = Path(self.faux.dossier).parent
        self.etat = self.tmp / "etat"
        self.etat.mkdir()
        self.sortie = self.tmp / "sortie" / "resultat.json"
        self.qui_pendant_claude = self.tmp / "qui-pendant-claude.txt"
        (self.faux.dossier / "claude").write_text(
            "#!/bin/sh\n"
            f'echo "claude $*" >> "{self.faux.temoin}"\n'
            f'"{sys.executable}" "{ETAT_MACHINE}" qui >> "{self.qui_pendant_claude}"\n'
            f"exit {code_claude}\n"
        )
        (self.faux.dossier / "gh").write_text(
            "#!/bin/sh\n"
            f'echo "gh $*" >> "{self.faux.temoin}"\n'
            + ("echo 'gh : réseau injoignable' >&2\nexit 1\n" if gh_en_echec else
               'case "$1 $2" in\n'
               f'  "run list") printf %s "{runs_en_cours}" ;;\n'
               f'  "run view") printf %s "{jobs_en_cours}" ;;\n'
               "esac\n")
        )
        self.env = _environnement(self.faux, None)
        self.env["XDG_STATE_HOME"] = str(self.etat)
        self.env["TMPDIR"] = str(self.tmp / "traces")
        self.env["EVALS_ATTENDRE"] = "1"

    def lancer(self, **env_en_plus: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [BASH, str(LANCER), "un-plugin", str(self.sortie)],
            env={**self.env, **env_en_plus},
            capture_output=True,
            text=True,
            timeout=60,
        )

    def lancements_de_claude(self) -> list[str]:
        return [l for l in self.faux.traces().splitlines() if l.startswith("claude ")]

    def appels_de_gh(self) -> list[str]:
        return [l for l in self.faux.traces().splitlines() if l.startswith("gh ")]

    def jeton(self, *args: str) -> str:
        return subprocess.run(
            [sys.executable, str(ETAT_MACHINE), "qui", *args],
            env=self.env, capture_output=True, text=True, timeout=30,
        ).stdout.strip()


def _ignorer_si_machine_saturee(cas: unittest.TestCase) -> None:
    """Le jeton refuse une machine saturée (code 4) : ces tests-là n'ont alors rien à prouver."""
    releve = subprocess.run([sys.executable, str(ETAT_MACHINE), "releve"],
                            capture_output=True, text=True, timeout=30)
    if releve.stdout.splitlines()[:1] == ["saturée"]:
        cas.skipTest("la machine est saturée : le jeton refuse, quoi que fasse le lanceur")


JOB_EVALS = "Évals (plans-notion)\nTests\n"


class LancerLocalRefuseSiUnBancTourneEnCi(unittest.TestCase):
    """En local, les évals ne partent pas pendant un banc de CI.

    Mesure du 2026-09-30 : un A/B local lancé pendant deux bancs de CI a
    partagé leur limite de débit et rendu des résultats inexploitables.
    """

    def test_un_job_evals_en_cours_en_ci_fait_refuser_sans_lancer_claude(self):
        lancement = _LancementLocal(self, runs_en_cours="4242\n", jobs_en_cours=JOB_EVALS)
        resultat = lancement.lancer()
        self.assertNotEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("Évals", resultat.stderr)
        self.assertEqual(lancement.lancements_de_claude(), [])
        self.assertEqual(lancement.jeton(), "libre", "le refus ne doit pas avoir pris le jeton")

    def test_un_run_en_cours_sans_job_evals_ne_bloque_pas(self):
        _ignorer_si_machine_saturee(self)
        lancement = _LancementLocal(self, runs_en_cours="4242\n", jobs_en_cours="Tests\nLint\n")
        resultat = lancement.lancer()
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(len(lancement.lancements_de_claude()), 1)

    def test_aucun_run_en_cours_laisse_partir_claude(self):
        _ignorer_si_machine_saturee(self)
        lancement = _LancementLocal(self)
        resultat = lancement.lancer()
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(len(lancement.lancements_de_claude()), 1)

    def test_evals_forcer_passe_outre_le_banc_de_ci_et_le_dit(self):
        _ignorer_si_machine_saturee(self)
        lancement = _LancementLocal(self, runs_en_cours="4242\n", jobs_en_cours=JOB_EVALS)
        resultat = lancement.lancer(EVALS_FORCER="1")
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(len(lancement.lancements_de_claude()), 1)
        self.assertIn("EVALS_FORCER", resultat.stderr)

    def test_gh_en_echec_refuse_car_sans_controle_on_ne_sait_pas(self):
        lancement = _LancementLocal(self, gh_en_echec=True)
        resultat = lancement.lancer()
        self.assertNotEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("EVALS_FORCER", resultat.stderr, "le refus doit dire comment passer outre")
        self.assertEqual(lancement.lancements_de_claude(), [])

    def test_gh_en_echec_ne_bloque_pas_quand_on_force(self):
        _ignorer_si_machine_saturee(self)
        lancement = _LancementLocal(self, gh_en_echec=True)
        resultat = lancement.lancer(EVALS_FORCER="1")
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(len(lancement.lancements_de_claude()), 1)


class LancerLocalPrendLeJetonMachine(unittest.TestCase):
    """En local, les évals sont une action lourde : elles ne partent qu'avec le jeton."""

    def test_jeton_deja_tenu_le_lanceur_attend_puis_refuse_sans_lancer_claude(self):
        lancement = _LancementLocal(self)
        detenteur = subprocess.Popen(["sleep", "60"])
        self.addCleanup(lambda: (detenteur.kill(), detenteur.wait()))
        pris = subprocess.run(
            [sys.executable, str(ETAT_MACHINE), "prendre", "e2e", "--plan", "Plan voisin",
             "--pid", str(detenteur.pid)],
            env=lancement.env, capture_output=True, text=True, timeout=30,
        )
        if pris.returncode == 4:
            self.skipTest("la machine est saturée : le jeton refuse, quoi que fasse le lanceur")
        self.assertEqual(pris.returncode, 0, pris.stderr)

        debut = time.monotonic()
        resultat = lancement.lancer()
        duree = time.monotonic() - debut

        self.assertNotEqual(resultat.returncode, 0, resultat.stderr)
        self.assertGreaterEqual(duree, 1.0, "EVALS_ATTENDRE=1 : le lanceur doit avoir attendu")
        self.assertIn("Plan voisin", resultat.stderr, "le refus doit dire qui tient le jeton")
        self.assertEqual(lancement.lancements_de_claude(), [])

    def test_le_jeton_est_tenu_pendant_claude_au_nom_du_plan_donne(self):
        _ignorer_si_machine_saturee(self)
        lancement = _LancementLocal(self)
        resultat = lancement.lancer(EVALS_PLAN="Plan de test")
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        pendant = lancement.qui_pendant_claude.read_text(encoding="utf-8")
        self.assertIn("evals-locales", pendant)
        self.assertIn("Plan de test", pendant)

    def test_le_jeton_est_rendu_apres_claude_et_le_code_de_claude_est_celui_du_lanceur(self):
        _ignorer_si_machine_saturee(self)
        lancement = _LancementLocal(self, code_claude=2)  # 2 = résultat partiel
        resultat = lancement.lancer()
        self.assertEqual(resultat.returncode, 2, resultat.stderr)
        self.assertEqual(lancement.jeton(), "libre")

    def test_sans_plan_donne_le_jeton_porte_un_titre_par_defaut(self):
        _ignorer_si_machine_saturee(self)
        lancement = _LancementLocal(self)
        resultat = lancement.lancer()
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("évals locales", lancement.qui_pendant_claude.read_text(encoding="utf-8"))

    def test_en_ci_le_lanceur_ne_controle_rien_et_ne_prend_pas_de_jeton(self):
        # Le runner GitHub n'est pas le VPS : ni gh, ni jeton. Faux binaires seulement ;
        # on n'utilise pas _environnement(…, "true") qui l'interdit par prudence pour
        # preparer-runner.sh (sudo) — lancer.sh n'en fait aucun.
        lancement = _LancementLocal(self, runs_en_cours="4242\n", jobs_en_cours=JOB_EVALS)
        resultat = lancement.lancer(GITHUB_ACTIONS="true")
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(len(lancement.lancements_de_claude()), 1)
        self.assertEqual(lancement.appels_de_gh(), [])
        self.assertEqual(lancement.qui_pendant_claude.read_text(encoding="utf-8").strip(), "libre")


def _concurrence_du_job(nom: str = "evals") -> tuple[str, str]:
    """(groupe, cancel-in-progress) du bloc ``concurrency:`` d'un job de ci.yml."""
    texte = CI.read_text(encoding="utf-8")
    job = re.search(rf"^  {re.escape(nom)}:\n(.*?)(?=^  [a-z][\w-]*:\n|\Z)", texte,
                    re.MULTILINE | re.DOTALL)
    assert job, f"job {nom} introuvable dans ci.yml"
    bloc = re.search(
        r"^    concurrency:\n(?:      #.*\n)*      group: (.+)\n(?:      #.*\n)*      cancel-in-progress: (\S+)",
        job.group(1),
        re.MULTILINE,
    )
    assert bloc, f"bloc concurrency (group puis cancel-in-progress) introuvable dans le job {nom}"
    return bloc.group(1).strip(), bloc.group(2)


def _groupe_pour(expression: str, *, pr: str, ref: str, mode: str, plugin: str) -> str:
    """Le nom du groupe que GitHub calculerait pour ce lancement.

    Évalue les ``${{ ... }}`` de l'expression (``||``, ``&&``, ``==``, chaînes,
    contextes) avec les valeurs données ; un contexte vide vaut la chaîne vide,
    comme chez GitHub.
    """
    contextes = {
        "github.event.pull_request.number": pr,
        "github.ref": ref,
        "inputs.mode": mode,
        "matrix.plugin": plugin,
    }

    def valeur(m: re.Match) -> str:
        code = m.group(1)
        for nom in sorted(contextes, key=len, reverse=True):
            code = code.replace(nom, repr(contextes[nom]))
        code = code.replace("||", " or ").replace("&&", " and ")
        return str(eval(code, {"__builtins__": {}}, {}))  # noqa: S307 - expression de notre propre ci.yml

    return re.sub(r"\$\{\{\s*(.*?)\s*\}\}", valeur, expression)


class UnSeulBancALaFoisParPlugin(unittest.TestCase):
    """Deux bancs d'évals d'un même plugin se partagent un groupe et ne s'annulent pas.

    Mesure du 2026-09-30 : trois bancs simultanés ont partagé la limite de débit
    de l'abonnement et rendu des têtes à 50 % et 44 % au lieu de 76 %.
    """

    def setUp(self):
        self.expression, self.annulation = _concurrence_du_job("evals")

    def _groupe(self, *, pr="", ref="refs/heads/x", mode="", plugin="plans-notion") -> str:
        return _groupe_pour(self.expression, pr=pr, ref=ref, mode=mode, plugin=plugin)

    def test_deux_pr_differentes_du_meme_plugin_tombent_dans_le_meme_groupe(self):
        self.assertEqual(self._groupe(pr="12", ref="refs/pull/12/merge"),
                         self._groupe(pr="34", ref="refs/pull/34/merge"))

    def test_une_pr_et_un_lancement_manuel_du_meme_plugin_tombent_dans_le_meme_groupe(self):
        self.assertEqual(self._groupe(pr="12", ref="refs/pull/12/merge"),
                         self._groupe(pr="", ref="refs/heads/main", mode="ab"))

    def test_deux_plugins_ne_se_bloquent_pas_entre_eux(self):
        self.assertNotEqual(self._groupe(plugin="plans-notion"),
                            self._groupe(plugin="methode-de-travail"))

    def test_une_mesure_du_bruit_garde_un_groupe_a_part_du_banc_ab(self):
        self.assertNotEqual(self._groupe(mode="aa"), self._groupe(mode="ab"))
        self.assertNotEqual(self._groupe(mode="aa"), self._groupe(mode=""))

    def test_deux_mesures_du_bruit_du_meme_plugin_partagent_leur_groupe(self):
        self.assertEqual(self._groupe(mode="aa", ref="refs/heads/a"),
                         self._groupe(mode="aa", ref="refs/heads/b"))

    def test_un_second_banc_attend_au_lieu_d_annuler_le_premier(self):
        self.assertEqual(self.annulation, "false")


class LaFumeeAttendDansLeGroupeDesEvals(unittest.TestCase):
    """La fumée puise dans le même abonnement que le banc : même groupe, sans annulation."""

    def test_la_fumee_est_dans_le_groupe_evals_du_plugin_et_n_annule_personne(self):
        groupe, annulation = _concurrence_du_job("fumee")
        expression_evals, _ = _concurrence_du_job("evals")
        for plugin in ("plans-notion", "methode-de-travail"):
            for pr, ref in (("12", "refs/pull/12/merge"), ("34", "refs/pull/34/merge")):
                with self.subTest(plugin=plugin, pr=pr):
                    de_la_fumee = _groupe_pour(groupe, pr=pr, ref=ref, mode="", plugin=plugin)
                    self.assertEqual(de_la_fumee, f"evals-{plugin}")
                    self.assertEqual(
                        de_la_fumee,
                        _groupe_pour(expression_evals, pr="", ref="refs/heads/main", mode="ab",
                                     plugin=plugin))
        self.assertEqual(annulation, "false")


if __name__ == "__main__":
    unittest.main()
