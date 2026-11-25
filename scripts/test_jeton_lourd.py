"""Tests du jeton automatique des actions lourdes (hook PreToolUse Bash + enveloppeur).

Deux pièces, deux familles de tests :

* le hook ``plugins/plans-notion/hooks/jeton_lourd.py`` reçoit sur stdin le JSON
  d'un appel Bash et rend soit rien (commande libre), soit une réécriture
  ``updatedInput`` qui enveloppe la commande lourde dans
  ``sous-jeton.sh`` (code 0 dans les deux cas, fail-open) ;
* l'enveloppeur ``skills/_partage/scripts/sous-jeton.sh`` prend le jeton de la
  machine, joue la commande, rend le jeton et son code de sortie.

Les attendus viennent du plan (D1 à D8), pas du code. Pour le hook : une suite
complète est enveloppée, une preuve ciblée ou une commande déjà sous jeton ne
l'est pas, le délai de l'outil Bash est fixé en avant-plan et laissé intact en
arrière-plan, et rtk, s'il est dans le PATH, fournit la commande intérieure.
Pour l'enveloppeur : le jeton se prend, se rend même après un échec, deux
enveloppes ne se chevauchent pas, une enveloppe dans une autre ne se bloque pas,
le plafond d'attente sort en code 75 sans jouer la commande.

Aucun test ne lit le vrai ``~/.local/state`` : chaque cas pose ``XDG_STATE_HOME``
et ``XDG_CONFIG_HOME`` dans un dossier jetable, et un profil machine d'une place.
Les attentes restent courtes (quelques secondes au plus).
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PLUGIN = RACINE / "plugins" / "plans-notion"
HOOK = PLUGIN / "hooks" / "jeton_lourd.py"
SOUS_JETON = PLUGIN / "skills" / "_partage" / "scripts" / "sous-jeton.sh"
ETAT_MACHINE = PLUGIN / "skills" / "_partage" / "scripts" / "etat-machine.py"

# PATH sans rtk : sur ce poste, rtk vit dans ~/.local/bin, absent de ce PATH.
CHEMIN_SANS_RTK = "/usr/bin:/bin"

# Commandes lourdes : le hook les enveloppe. Playwright l'est toujours, même avec un fichier.
LOURDS = [
    ".venv/bin/pytest",
    "pytest -q",
    "python3 -m pytest tests/",
    "timeout 600 pytest -q",
    "uv run pytest",
    "FOO=1 pytest",
    "rtk pytest",
    "pytest -q 2>&1 | tail -5",
    "cd a && pytest",
    "npm run test:unit",
    "npm run e2e",
    "npm test",
    "npx vitest run",
    "npx playwright test a.spec.ts",
    "jest --config jest.config.js",
    "pytest --ignore tests/test_a.py",
    "docker run x",
    "claude plugin eval plugins/plans-notion",
]

# Commandes libres : le hook ne rend rien. Une preuve ciblée, une commande qui ne
# lance pas de suite, ou une commande qui cite déjà le jeton (enveloppeur, prise).
LIBRES = [
    "pytest scripts/test_a.py",
    "pytest -k x",
    "pytest a.py::t",
    "pytest --version",
    "pytest --collect-only",
    "grep pytest x.py",
    'git commit -m "pytest"',
    "cat > notes.md <<'EOF'\npytest -q\nEOF",
    "npx playwright install",
    "npx vitest run src/a.test.ts",
    "npm run build",
    "bash evals/outillage/lancer.sh un-plugin",
    "bash SOUS_JETON_ICI 'pytest'",
    "python3 ETAT_MACHINE_ICI prendre e2e --plan X",
]


def bash(commande: str, **champs) -> dict:
    """Le JSON qu'un appel Bash envoie au hook, avec ses autres champs éventuels."""
    return {"tool_name": "Bash", "tool_input": {"command": commande, **champs}}


def jouer(entree, chemin: str = CHEMIN_SANS_RTK) -> subprocess.CompletedProcess:
    """Lance le hook en vrai sous-processus, comme Claude Code, avec un PATH donné."""
    brut = entree if isinstance(entree, str) else json.dumps(entree)
    env = {**os.environ, "PATH": chemin}
    env.pop("PLANS_NOTION_JETON_PID", None)
    return subprocess.run([sys.executable, str(HOOK)], input=brut, capture_output=True,
                          text=True, timeout=30, env=env)


def faux_rtk(dossier: Path, corps: str) -> str:
    """Pose un faux ``rtk`` dans ``dossier`` ; rend le PATH qui le fait passer en premier."""
    dossier.mkdir(parents=True, exist_ok=True)
    rtk = dossier / "rtk"
    rtk.write_text("#!/bin/sh\n" + corps)
    rtk.chmod(0o755)
    return f"{dossier}:{CHEMIN_SANS_RTK}"


# Un faux rtk qui réécrit « rewrite X » en « rtk X », comme la vraie réécriture pour pytest.
RTK_REECRIT = r'''if [ "$1" = rewrite ]; then shift; printf 'rtk %s\n' "$*"; exit 0; fi
exit 1
'''


class HookTestCase(unittest.TestCase):
    def reecriture(self, entree, chemin: str = CHEMIN_SANS_RTK) -> dict:
        """La réécriture rendue par le hook : code 0, PreToolUse, sans permissionDecision."""
        r = jouer(entree, chemin)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertTrue(r.stdout.strip(), "une commande lourde doit être réécrite, pas laissée telle quelle")
        spec = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", spec,
                         "le hook réécrit sans décider de la permission (comme rtk)")
        return spec["updatedInput"]

    def assertEnveloppee(self, commande: str, *, interieur: str | None = None,
                         attente: str = "300", chemin: str = CHEMIN_SANS_RTK, **champs):
        """La commande est enveloppée : ``PLANS_NOTION_ATTENTE_MAX=<s> bash <sous-jeton> <intérieur>``."""
        maj = self.reecriture(bash(commande, **champs), chemin)
        jetons = shlex.split(maj["command"])
        self.assertEqual(jetons[:3], [f"PLANS_NOTION_ATTENTE_MAX={attente}", "bash", str(SOUS_JETON)],
                         msg=f"enveloppe attendue pour {commande!r} : {maj['command']!r}")
        self.assertEqual(len(jetons), 4, msg=f"l'intérieur doit être un seul argument : {jetons!r}")
        self.assertEqual(jetons[3], commande if interieur is None else interieur)
        return maj

    def assertLibre(self, entree, chemin: str = CHEMIN_SANS_RTK):
        r = jouer(entree, chemin)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(r.stdout, "", "une commande libre n'est pas réécrite")


class DetectionLourd(HookTestCase):
    def test_une_suite_complete_ou_une_action_lourde_est_enveloppee(self):
        for commande in LOURDS:
            with self.subTest(commande=commande):
                self.assertEnveloppee(commande)


class DetectionLibre(HookTestCase):
    def test_une_preuve_ciblee_ou_une_commande_sous_jeton_ou_sans_suite_passe(self):
        libres = [c.replace("SOUS_JETON_ICI", str(SOUS_JETON))
                  .replace("ETAT_MACHINE_ICI", str(ETAT_MACHINE)) for c in LIBRES]
        for commande in libres:
            with self.subTest(commande=commande):
                self.assertLibre(bash(commande))


class Reecriture(HookTestCase):
    def test_avant_plan_sans_delai_recu_fixe_le_delai_a_dix_minutes_et_le_plafond_a_300(self):
        maj = self.assertEnveloppee("pytest -q")
        self.assertEqual(maj["timeout"], 600000)

    def test_avant_plan_avec_un_delai_de_deux_minutes_le_releve_a_dix_minutes(self):
        maj = self.assertEnveloppee("pytest -q", timeout=120000)
        self.assertEqual(maj["timeout"], 600000, "une suite lourde au délai de 2 min serait tuée")

    def test_run_in_background_faux_reste_en_avant_plan(self):
        # En plus du plan : attrape une détection qui lit la présence de la clé
        # run_in_background et non sa valeur (false compterait alors comme arrière-plan).
        maj = self.assertEnveloppee("pytest -q", run_in_background=False, timeout=120000)
        self.assertEqual(maj["timeout"], 600000)

    def test_arriere_plan_garde_le_delai_de_l_appelant_et_plafonne_l_attente_a_1800(self):
        maj = self.assertEnveloppee("pytest -q", attente="1800", run_in_background=True,
                                    timeout=120000)
        self.assertEqual(maj["timeout"], 120000, "en arrière-plan, le délai de l'outil reste intact")

    def test_les_autres_champs_de_tool_input_sont_recopies(self):
        # updatedInput remplace tout l'objet : les champs non modifiés doivent revenir.
        maj = self.assertEnveloppee("pytest -q", description="Suite complète", timeout=120000)
        self.assertEqual(maj["description"], "Suite complète")
        self.assertEqual(set(maj), {"command", "description", "timeout"})

    def test_rtk_dans_le_path_fournit_la_commande_interieure(self):
        # rtk lit la commande et rend sa réécriture ; c'est elle qui est enveloppée (D7).
        with tempfile.TemporaryDirectory() as tmp:
            chemin = faux_rtk(Path(tmp) / "bin", RTK_REECRIT)
            self.assertEnveloppee("pytest -q", interieur="rtk pytest -q", chemin=chemin)

    def test_rtk_en_echec_ou_muet_garde_la_commande_d_origine(self):
        # En plus du plan, au repli de D7 : un rtk qui échoue ou ne rend rien ne doit
        # pas vider la commande intérieure (sinon la suite ne part pas du tout).
        cas = {
            "rtk en échec": 'echo "erreur" >&2\nexit 1\n',
            "rtk muet": "exit 0\n",
        }
        for nom, corps in cas.items():
            with self.subTest(cas=nom), tempfile.TemporaryDirectory() as tmp:
                chemin = faux_rtk(Path(tmp) / "bin", corps)
                self.assertEnveloppee("pytest -q", interieur="pytest -q", chemin=chemin)


class Repli(HookTestCase):
    """Fail-open : une entrée qu'on ne lit pas, ou un autre outil, passe sans sortie."""

    def test_json_illisible_passe_sans_sortie(self):
        self.assertLibre("{pas du json")

    def test_un_outil_autre_que_bash_passe_meme_si_son_texte_cite_pytest(self):
        self.assertLibre({"tool_name": "Read", "tool_input": {"command": "pytest -q"}})


class EnveloppeurTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.marque = self.base / "joue.txt"
        # Une place, et des seuils qui ne saturent jamais : seule la prise compte.
        self.profil = self.base / "profil.json"
        self.profil.write_text(json.dumps(
            {"places_lourdes": 1, "seuil_mem_disponible_ko": 0, "seuil_mem_full_avg60": 100}))
        self.env = {**os.environ,
                    "XDG_STATE_HOME": str(self.base / "etat"),
                    "XDG_CONFIG_HOME": str(self.base / "config"),
                    "PLANS_NOTION_MACHINE_PROFIL": str(self.profil),
                    "PLANS_NOTION_ATTENTE_MAX": "20",
                    "PLANS_NOTION_ATTENTE_PALIER": "1",
                    "PLANS_NOTION_ATTENTE_SATUREE": "1"}
        self.env.pop("PLANS_NOTION_JETON_PID", None)

    def enveloppe(self, commande: str, env: dict | None = None, timeout: int = 90):
        return subprocess.run(["bash", str(SOUS_JETON), commande], capture_output=True,
                              text=True, env=env or self.env, timeout=timeout)

    def etat(self, *args: str, env: dict | None = None):
        return subprocess.run([sys.executable, str(ETAT_MACHINE), *args], capture_output=True,
                              text=True, env=env or self.env, timeout=30)

    def qui(self) -> str:
        return self.etat("qui").stdout.strip()

    def tenir_le_jeton(self) -> subprocess.Popen:
        """Un détenteur vivant (un ``sleep``) qui prend l'unique place, hors de l'enveloppe."""
        tenant = subprocess.Popen(["sleep", "60"])
        self.addCleanup(lambda: (tenant.kill(), tenant.wait()))
        pris = self.etat("prendre", "tenue", "--plan", "Tenu ailleurs", "--pid", str(tenant.pid))
        self.assertEqual(pris.returncode, 0, msg=pris.stderr)
        return tenant


class Enveloppeur(EnveloppeurTestCase):
    def test_la_prise_est_annoncee_sur_la_sortie_d_erreur(self):
        r = self.enveloppe("true")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("jeton pris", r.stderr)

    def test_le_code_de_la_commande_est_rendu_et_le_jeton_rendu_apres_un_echec(self):
        r = self.enveloppe("exit 7")
        self.assertEqual(r.returncode, 7, msg=r.stderr)
        self.assertEqual(self.qui(), "libre", "le jeton doit être rendu même après un échec")

    def test_deux_enveloppees_en_parallele_ne_se_chevauchent_pas(self):
        # Chaque commande note son début et sa fin ; avec une place, la seconde ne
        # démarre qu'après la fin de la première.
        commande = "date +%s.%N; sleep 1; date +%s.%N"
        procs = [subprocess.Popen(["bash", str(SOUS_JETON), commande], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, env=self.env)
                 for _ in range(2)]
        intervalles = []
        for p in procs:
            sortie, erreur = p.communicate(timeout=60)
            self.assertEqual(p.returncode, 0, msg=erreur)
            debut, fin = (float(x) for x in sortie.split())
            intervalles.append((debut, fin))
        (_, fin_1), (debut_2, _) = sorted(intervalles)
        self.assertGreaterEqual(debut_2, fin_1,
                                "la seconde enveloppée a démarré pendant la première")

    def test_une_enveloppe_dans_une_autre_ne_reprend_pas_le_jeton(self):
        # L'intérieur est une enveloppe : elle voit le jeton tenu par la première et
        # ne se bloque pas elle-même. Sans cette règle, elle attendrait le plafond de 20 s.
        commande = f"bash {shlex.quote(str(SOUS_JETON))} {shlex.quote('echo interieur')}"
        debut = time.monotonic()
        r = self.enveloppe(commande)
        duree = time.monotonic() - debut
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("interieur", r.stdout)
        self.assertLess(duree, 15, "l'enveloppe intérieure a attendu son propre jeton")

    def test_un_prendre_dans_l_enveloppe_est_accorde_sans_nouvelle_entree(self):
        # Un enfant bash du détenteur (son PID n'est pas le détenteur) fait « prendre » :
        # l'ancêtre tient déjà le jeton, la prise est accordée.
        interieur = (f"{shlex.quote(sys.executable)} {shlex.quote(str(ETAT_MACHINE))} "
                     "prendre dedans --plan Dedans --pid $$")
        commande = f"bash -c {shlex.quote(interieur)}"
        debut = time.monotonic()
        r = self.enveloppe(commande)
        duree = time.monotonic() - debut
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("accordé", r.stdout)
        self.assertLess(duree, 15, "la prise intérieure a attendu le jeton qu'elle tenait")

    def test_le_plafond_atteint_sort_en_75_en_citant_le_detenteur_sans_jouer_la_commande(self):
        tenant = self.tenir_le_jeton()
        env = {**self.env, "PLANS_NOTION_ATTENTE_MAX": "2"}
        r = self.enveloppe(f"touch {shlex.quote(str(self.marque))}", env=env)
        self.assertEqual(r.returncode, 75, msg=r.stderr)
        self.assertIn(str(tenant.pid), r.stderr, "le refus doit citer le PID du détenteur")
        self.assertFalse(self.marque.exists(), "sans jeton, la commande n'est pas jouée")
        self.assertIn(str(tenant.pid), self.qui(), "le détenteur n'a pas été dérangé")

    def test_machine_saturee_attend_puis_sort_en_75_sans_refus_immediat(self):
        profil = self.base / "saturee.json"
        profil.write_text(json.dumps({"places_lourdes": 1,
                                      "seuil_mem_disponible_ko": 1_000_000_000_000,
                                      "seuil_mem_full_avg60": 100}))
        env = {**self.env, "PLANS_NOTION_MACHINE_PROFIL": str(profil),
               "PLANS_NOTION_ATTENTE_MAX": "3"}
        debut = time.monotonic()
        r = self.enveloppe(f"touch {shlex.quote(str(self.marque))}", env=env)
        duree = time.monotonic() - debut
        self.assertEqual(r.returncode, 75, msg=r.stderr)
        self.assertGreaterEqual(duree, 2.0, "une machine saturée s'attend, elle ne refuse pas sur le champ")
        self.assertFalse(self.marque.exists(), "sans jeton, la commande n'est pas jouée")

    def test_profil_invalide_laisse_partir_la_commande_avec_un_avertissement(self):
        casse = self.base / "casse.json"
        casse.write_text('{"places_lourdes": 4,')
        env = {**self.env, "PLANS_NOTION_MACHINE_PROFIL": str(casse)}
        r = self.enveloppe("echo passe", env=env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("passe", r.stdout)
        self.assertIn("profil", r.stderr, "l'avertissement doit dire pourquoi le jeton n'a pas été pris")

    def test_pid_du_jeton_vivant_dans_l_environnement_evite_la_prise(self):
        tenant = self.tenir_le_jeton()
        env = {**self.env, "PLANS_NOTION_JETON_PID": str(tenant.pid),
               "PLANS_NOTION_ATTENTE_MAX": "2"}
        r = self.enveloppe("echo passe", env=env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("passe", r.stdout)
        self.assertNotIn("jeton pris", r.stderr, "le PID du jeton est vivant : pas de prise")
        self.assertIn(str(tenant.pid), self.qui())

    def test_pid_du_jeton_mort_dans_l_environnement_ne_bloque_pas_la_prise(self):
        # En plus du plan : attrape une garde qui testerait la présence de la variable
        # au lieu de la vie du PID ; un PID mort ne tient pas le jeton.
        mort = subprocess.Popen(["true"])
        mort.wait()
        env = {**self.env, "PLANS_NOTION_JETON_PID": str(mort.pid)}
        r = self.enveloppe("echo passe", env=env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("jeton pris", r.stderr, "un PID mort ne vaut pas jeton déjà tenu")


if __name__ == "__main__":
    unittest.main()
