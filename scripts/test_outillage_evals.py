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
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PREPARER = Path(
    os.environ.get("PREPARER_RUNNER") or RACINE / "evals" / "outillage" / "preparer-runner.sh"
)
LANCER = RACINE / "evals" / "outillage" / "lancer.sh"

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


if __name__ == "__main__":
    unittest.main()
