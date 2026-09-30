"""Tests de ``etat-de-depart.sh`` sur des dépôts git fabriqués.

Le script inventorie les garde-fous d'un dépôt (hooks, CI, protections) et
nomme la commande de sa suite. Ce qu'il faut prouver, c'est qu'il **lit** le
dépôt qu'on lui donne : un dépôt vierge doit rendre « aucun » partout, et
chaque garde-fou posé doit ressortir nommé, avec ce qu'il refuse quand c'est
lisible. Un script qui rendrait toujours le même bloc passerait un seul de ces
cas et échouerait les autres.

Chaque dépôt est fabriqué dans un dossier jetable ; ``HOME`` et la config git
globale sont isolés pour que rien du poste (un ``core.hooksPath`` global, les
hooks de ``~/.claude/settings.json``) ne fuie dans l'attendu. ``gh`` est
neutralisé par la variable que le script respecte : aucun test ne touche le
réseau. Aucun test ne joue une vraie suite : ``--sans-repetition`` partout.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "etat-de-depart.sh"


class EtatDeDepart(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.home = base / "home"
        self.home.mkdir()
        self.depot = base / "depot"
        self.depot.mkdir()
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
            "ETAT_DE_DEPART_SANS_GH": "1",
        }
        self.git("init", "-q", "-b", "main")
        self.ecrire("README.md", "depot fabriqué\n")

    # -- fabrication -------------------------------------------------------
    def git(self, *args):
        subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=self.depot,
                       check=True, capture_output=True, env=self.env)

    def ecrire(self, chemin, texte, executable=False):
        p = self.depot / chemin
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texte, encoding="utf-8")
        if executable:
            p.chmod(0o755)

    def figer(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")

    def lancer(self, *options):
        r = subprocess.run([str(SCRIPT), *options, "--sans-repetition", str(self.depot)],
                           capture_output=True, text=True, env=self.env, cwd=self.home)
        self.assertEqual(r.returncode, 0, f"code {r.returncode}\n{r.stdout}\n{r.stderr}")
        return r.stdout

    def ligne(self, sortie, etiquette):
        """La ligne « - <etiquette> : ... » du bloc, ou échec net si elle manque."""
        for l in sortie.splitlines():
            if l.startswith(f"- {etiquette} :"):
                return l
        self.fail(f"pas de ligne « {etiquette} » dans :\n{sortie}")

    # -- dépôt sans aucun garde-fou ----------------------------------------
    def test_depot_sans_garde_fou_dit_aucun_pour_chaque_famille(self):
        self.figer()
        sortie = self.lancer()
        for etiquette in ("Workflows CI", "core.hooksPath", "Hooks git", "pre-commit",
                          "husky", "lefthook", "Hooks Claude Code (dépôt)",
                          "Hooks Claude Code (~/.claude/settings.json)"):
            self.assertIn("aucun", self.ligne(sortie, etiquette), etiquette)

    def test_rulesets_sans_gh_sont_non_verifies_avec_la_raison_et_sans_erreur(self):
        self.figer()
        ligne = self.ligne(self.lancer(), "Rulesets et protection de branche")
        self.assertIn("non vérifié", ligne)
        self.assertIn("gh", ligne)

    def test_hook_git_d_exemple_ne_compte_pas_comme_garde_fou(self):
        # `git init` pose des `*.sample` : un hook inactif n'a jamais refusé un commit.
        self.figer()
        self.assertTrue(list((self.depot / ".git" / "hooks").glob("*.sample")))
        self.assertIn("aucun", self.ligne(self.lancer(), "Hooks git"))

    # -- core.hooksPath ----------------------------------------------------
    def test_core_hookspath_est_nomme_avec_sa_valeur_et_ses_hooks(self):
        self.ecrire(".githooks-perso/pre-commit", "#!/bin/sh\nexit 1\n", executable=True)
        self.figer()
        self.git("config", "core.hooksPath", ".githooks-perso")
        ligne = self.ligne(self.lancer(), "core.hooksPath")
        self.assertIn(".githooks-perso", ligne)
        self.assertIn("pre-commit", ligne)
        self.assertNotIn("aucun", ligne)

    def test_hook_de_git_hooks_masque_par_core_hookspath_n_est_pas_presente_comme_actif(self):
        # Quand `core.hooksPath` est réglé, git n'ouvre plus `.git/hooks` : un
        # `pre-push` exécutable qui s'y trouve ne refusera jamais rien. Le
        # présenter comme garde-fou actif serait affirmer un faux garde-fou.
        self.ecrire(".githooks/pre-commit", "#!/bin/sh\nexit 1\n", executable=True)
        self.figer()
        self.git("config", "core.hooksPath", ".githooks")
        pre_push = self.depot / ".git" / "hooks" / "pre-push"
        pre_push.write_text("#!/bin/sh\nexit 1\n")
        pre_push.chmod(0o755)
        sortie = self.lancer()
        self.assertIn(".githooks", self.ligne(sortie, "core.hooksPath"))
        ligne = self.ligne(sortie, "Hooks git")
        # Soit `pre-push` n'apparaît pas, soit il est dit inactif / masqué / ignoré.
        if "pre-push" in ligne:
            self.assertTrue(any(mot in ligne for mot in ("inactif", "masqué", "ignoré")),
                            f"pre-push présenté comme actif malgré core.hooksPath :\n{ligne}")

    # -- .pre-commit-config.yaml -------------------------------------------
    def test_pre_commit_config_est_nomme_avec_les_id_de_ses_hooks(self):
        self.ecrire(".pre-commit-config.yaml",
                    "repos:\n"
                    "  - repo: https://example.invalid/hooks\n"
                    "    rev: v1\n"
                    "    hooks:\n"
                    "      - id: black\n"
                    "      - id: detect-private-key\n")
        self.figer()
        ligne = self.ligne(self.lancer(), "pre-commit")
        self.assertIn("black", ligne)
        self.assertIn("detect-private-key", ligne)
        self.assertNotIn("aucun", ligne)

    # -- les autres familles du geste 10 -----------------------------------
    def test_hook_git_reel_hors_sample_est_liste(self):
        self.figer()
        pre_push = self.depot / ".git" / "hooks" / "pre-push"
        pre_push.write_text("#!/bin/sh\nexit 1\n")
        pre_push.chmod(0o755)
        ligne = self.ligne(self.lancer(), "Hooks git")
        self.assertIn("pre-push", ligne)
        self.assertNotIn("pre-push.sample", ligne)

    def test_hook_git_non_executable_n_est_pas_presente_comme_actif(self):
        # Git ignore (avec un avertissement) un hook de `.git/hooks` sans droit
        # d'exécution : il ne refusera jamais rien. Le lister comme garde-fou
        # actif serait affirmer un faux garde-fou.
        self.figer()
        pre_push = self.depot / ".git" / "hooks" / "pre-push"
        pre_push.write_text("#!/bin/sh\nexit 1\n")
        pre_push.chmod(0o644)
        ligne = self.ligne(self.lancer(), "Hooks git")
        # Soit `pre-push` n'apparaît pas, soit il est dit inactif / non exécutable.
        if "pre-push" in ligne:
            self.assertTrue(any(mot in ligne for mot in ("inactif", "non exécutable")),
                            f"pre-push non exécutable présenté comme actif :\n{ligne}")

    def test_husky_et_lefthook_sont_nommes_avec_leurs_hooks(self):
        self.ecrire(".husky/pre-commit", "npm test\n")
        self.ecrire("lefthook.yml", "pre-push:\n  commands:\n    lint:\n      run: make lint\n")
        self.figer()
        sortie = self.lancer()
        self.assertIn("pre-commit", self.ligne(sortie, "husky"))
        self.assertIn("pre-push", self.ligne(sortie, "lefthook"))

    def test_workflows_ci_sont_listes_par_nom_de_fichier(self):
        self.ecrire(".github/workflows/ci.yml", "name: ci\non: [push]\n")
        self.figer()
        self.assertIn("ci.yml", self.ligne(self.lancer(), "Workflows CI"))

    def test_hooks_de_settings_claude_du_depot_et_du_poste_sont_lus_separement(self):
        self.ecrire(".claude/settings.json", '{"hooks": {"PreToolUse": [{"matcher": "Bash"}]}}\n')
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "settings.json").write_text('{"hooks": {"Stop": []}}\n')
        self.figer()
        sortie = self.lancer()
        depot = self.ligne(sortie, "Hooks Claude Code (dépôt)")
        poste = self.ligne(sortie, "Hooks Claude Code (~/.claude/settings.json)")
        self.assertIn("PreToolUse", depot)
        self.assertNotIn("Stop", depot)
        self.assertIn("Stop", poste)
        self.assertNotIn("PreToolUse", poste)

    def test_settings_claude_sans_cle_hooks_ne_compte_pas(self):
        self.ecrire(".claude/settings.json", '{"permissions": {"allow": []}}\n')
        self.figer()
        self.assertIn("aucun", self.ligne(self.lancer(), "Hooks Claude Code (dépôt)"))

    # -- répétition à blanc : la commande de suite -------------------------
    def test_suite_sans_indice_est_a_preciser(self):
        self.figer()
        self.assertIn("à préciser", self.ligne(self.lancer(), "Suite du dépôt"))

    def test_suite_devinee_par_ci_locale_est_nommee_mais_pas_jouee(self):
        self.ecrire("scripts/ci_locale.sh", "#!/bin/sh\ntouch ../marqueur-joue\n", executable=True)
        self.figer()
        ligne = self.ligne(self.lancer(), "Suite du dépôt")
        self.assertIn("scripts/ci_locale.sh", ligne)
        self.assertFalse((self.depot / "marqueur-joue").exists())
        self.assertFalse((self.depot.parent / "marqueur-joue").exists())

    def test_suite_ambigue_n_est_pas_devinee(self):
        self.ecrire("package.json", '{"scripts": {"test": "jest"}}\n')
        self.ecrire("pytest.ini", "[pytest]\n")
        self.figer()
        ligne = self.ligne(self.lancer(), "Suite du dépôt")
        self.assertIn("à préciser", ligne)
        self.assertIn("npm test", ligne)
        self.assertIn("pytest", ligne)

    # -- lecture seule -----------------------------------------------------
    def test_le_script_ne_modifie_rien_dans_le_depot_inspecte(self):
        self.ecrire(".pre-commit-config.yaml", "repos:\n  - repo: x\n    hooks:\n      - id: black\n")
        self.ecrire("scripts/ci_locale.sh", "#!/bin/sh\nexit 0\n", executable=True)
        self.figer()
        avant = self._empreinte()
        self.lancer()
        self.assertEqual(avant, self._empreinte())

    def _empreinte(self):
        return sorted((str(p.relative_to(self.depot)), p.stat().st_mtime_ns)
                      for p in self.depot.rglob("*") if p.is_file())

    def test_depot_absent_est_une_erreur_claire_pas_un_bloc_trompeur(self):
        r = subprocess.run([str(SCRIPT), "--sans-repetition", str(self.depot / "inexistant")],
                           capture_output=True, text=True, env=self.env, cwd=self.home)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("inexistant", r.stderr)


if __name__ == "__main__":
    unittest.main()
