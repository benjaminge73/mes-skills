"""Tests de ``check_skills.py`` : une règle = un plugin fabriqué qui la viole
(refus, avec son message) et un plugin conforme (accepté).

Chaque test fabrique son dépôt dans un dossier temporaire : aucun ne lit les
vrais plugins, donc aucun ne change quand un skill change. Lancés par
``python3 -m unittest discover -s scripts -p 'test_*.py'``, sans dépendance.
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_skills  # noqa: E402

PLAFOND_LARGE = {"lignes": 10_000, "octets": 10_000_000}


def _ecrire(chemin: Path, texte: str) -> Path:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")
    return chemin


def _skill(racine: Path, plugin: str, nom: str, description: str = "Un skill.",
           corps: str = "Corps.\n", extra: str = "") -> Path:
    return _ecrire(
        racine / "plugins" / plugin / "skills" / nom / "SKILL.md",
        f"---\nname: {nom}\ndescription: {description}\n{extra}---\n{corps}",
    )


def _agent(racine: Path, plugin: str, nom: str, champs: str = "") -> Path:
    return _ecrire(
        racine / "plugins" / plugin / "agents" / f"{nom}.md",
        f"---\nname: {nom}\ndescription: Un agent.\n{champs}---\nCorps.\n",
    )


def _manifeste(racine: Path, plugin: str, description: str = "Un plugin.") -> Path:
    return _ecrire(
        racine / "plugins" / plugin / ".claude-plugin" / "plugin.json",
        json.dumps({"name": plugin, "version": "1.0.0", "description": description}),
    )


def _limites(racine: Path, **plus) -> dict:
    """Plafonds larges pour chaque SKILL.md présent : seul l'objet du test mord."""
    tailles = {
        p.relative_to(racine).as_posix(): dict(PLAFOND_LARGE)
        for p in racine.glob("plugins/*/skills/*/SKILL.md")
    }
    limites = {"taille_skill_md": tailles, "invariants_en_tete": [],
               "veille_jours_max": 30, "exceptions": []}
    limites.update(plus)
    return limites


def _regles(resultat) -> list[str]:
    return [a.regle for a in resultat.refus]


class Depot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name)

    def controler(self, limites=None, **kw):
        return check_skills.controler(self.racine, limites or _limites(self.racine), **kw)

    def plugin_conforme(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s")


class ReglesDeBase(Depot):
    def test_un_plugin_conforme_est_accepte(self):
        self.plugin_conforme()
        res = self.controler()
        self.assertEqual(res.refus, [])

    def test_tous_les_plugins_du_depot_sont_joues(self):
        _manifeste(self.racine, "un")
        _manifeste(self.racine, "deux")
        _skill(self.racine, "un", "s", description="x" * 2000)
        _skill(self.racine, "deux", "t", description="y" * 2000)
        res = self.controler()
        cibles = {a.cible for a in res.refus if a.regle == "a"}
        self.assertEqual(len(cibles), 2)


class RegleA_DescriptionTropLongue(Depot):
    def test_description_de_1537_caracteres_est_refusee_avec_son_message(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 1537)
        res = self.controler()
        refus = [a for a in res.refus if a.regle == "a"]
        self.assertEqual(len(refus), 1)
        self.assertIn("1 536", refus[0].message)
        self.assertIn("raccourcir", refus[0].message.lower())

    def test_description_de_1536_caracteres_est_acceptee(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 1536)
        self.assertEqual(self.controler().refus, [])

    def test_when_to_use_compte_avec_la_description(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 1000,
               extra="when_to_use: " + "y" * 600 + "\n")
        self.assertIn("a", _regles(self.controler()))

    def test_un_agent_trop_long_est_refuse_aussi(self):
        _manifeste(self.racine, "p")
        _ecrire(self.racine / "plugins/p/agents/a.md",
                "---\nname: a\ndescription: " + "z" * 1600 + "\n---\nCorps.\n")
        res = self.controler()
        self.assertEqual([a.regle for a in res.refus if a.cible.endswith("a.md")], ["a"])

    def test_un_bloc_replie_compte_le_texte_replie_pas_l_indentation(self):
        # 25 lignes de 60 caractères : replié = 1 524 (ok) ; brut avec
        # indentation et retours à la ligne = 1 575 (trop long si on comptait mal).
        lignes = "\n".join("  " + "m" * 60 for _ in range(25))
        _manifeste(self.racine, "p")
        _ecrire(self.racine / "plugins/p/skills/s/SKILL.md",
                f"---\nname: s\ndescription: >-\n{lignes}\n---\nCorps.\n")
        self.assertEqual(self.controler().refus, [])

    def test_une_valeur_entre_guillemets_est_lue_sans_ses_guillemets(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description='"' + "x" * 1536 + '"')
        self.assertEqual(self.controler().refus, [])


class RegleB_TailleDesSkillMd(Depot):
    def test_un_skill_au_dessus_de_son_plafond_de_lignes_est_refuse(self):
        self.plugin_conforme()
        chemin = "plugins/p/skills/s/SKILL.md"
        (self.racine / chemin).write_text(
            "---\nname: s\ndescription: d\n---\n" + "ligne\n" * 50, encoding="utf-8")
        limites = _limites(self.racine)
        limites["taille_skill_md"][chemin] = {"lignes": 20, "octets": 10_000_000}
        res = self.controler(limites)
        refus = [a for a in res.refus if a.regle == "b"]
        self.assertEqual(len(refus), 1)
        self.assertIn("plafond", refus[0].message)

    def test_un_skill_au_dessus_de_son_plafond_d_octets_est_refuse(self):
        self.plugin_conforme()
        chemin = "plugins/p/skills/s/SKILL.md"
        limites = _limites(self.racine)
        limites["taille_skill_md"][chemin] = {"lignes": 10_000, "octets": 10}
        self.assertIn("b", _regles(self.controler(limites)))

    def test_un_skill_sous_son_plafond_est_accepte(self):
        self.plugin_conforme()
        self.assertEqual(self.controler().refus, [])

    def test_un_skill_sans_plafond_est_refuse_avec_la_marche_a_suivre(self):
        self.plugin_conforme()
        limites = _limites(self.racine)
        limites["taille_skill_md"] = {}
        refus = [a for a in self.controler(limites).refus if a.regle == "b"]
        self.assertEqual(len(refus), 1)
        self.assertIn("limites.json", refus[0].message)


class Cliquet(unittest.TestCase):
    def base(self):
        return {"taille_skill_md": {"x/SKILL.md": {"lignes": 100, "octets": 5000}},
                "veille_jours_max": 30}

    def test_une_hausse_de_plafond_est_refusee(self):
        tete = self.base()
        tete["taille_skill_md"]["x/SKILL.md"]["lignes"] = 101
        anomalies = check_skills.verifier_cliquet(tete, self.base())
        self.assertEqual([a.regle for a in anomalies], ["b"])
        self.assertIn("baisser", anomalies[0].message)

    def test_une_hausse_du_plafond_d_octets_est_refusee(self):
        tete = self.base()
        tete["taille_skill_md"]["x/SKILL.md"]["octets"] = 5001
        self.assertEqual(len(check_skills.verifier_cliquet(tete, self.base())), 1)

    def test_une_baisse_de_plafond_est_acceptee(self):
        tete = self.base()
        tete["taille_skill_md"]["x/SKILL.md"] = {"lignes": 90, "octets": 4000}
        self.assertEqual(check_skills.verifier_cliquet(tete, self.base()), [])

    def test_limites_absent_de_la_base_est_accepte(self):
        self.assertEqual(check_skills.verifier_cliquet(self.base(), None), [])

    def test_un_nouveau_skill_dans_limites_est_accepte(self):
        tete = self.base()
        tete["taille_skill_md"]["y/SKILL.md"] = {"lignes": 10_000, "octets": 10**7}
        self.assertEqual(check_skills.verifier_cliquet(tete, self.base()), [])

    def test_un_plafond_retire_alors_qu_il_existait_est_refuse(self):
        tete = self.base()
        tete["taille_skill_md"] = {}
        self.assertEqual(len(check_skills.verifier_cliquet(tete, self.base())), 1)

    def test_le_seuil_de_veille_ne_peut_que_baisser(self):
        tete = self.base()
        tete["veille_jours_max"] = 60
        self.assertEqual(len(check_skills.verifier_cliquet(tete, self.base())), 1)
        tete["veille_jours_max"] = 15
        self.assertEqual(check_skills.verifier_cliquet(tete, self.base()), [])


class LireLimitesDeLaBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name)
        self._git("init", "-q", "-b", "main")

    def _git(self, *args):
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.racine)}
        subprocess.run(["git", "-c", "commit.gpgsign=false", *args],
                       cwd=self.racine, check=True, capture_output=True, env=env)

    def test_le_fichier_de_la_base_est_lu(self):
        _ecrire(self.racine / "scripts/limites.json", '{"veille_jours_max": 30}')
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")
        self.assertEqual(check_skills.lire_limites_base(self.racine, "main"),
                         {"veille_jours_max": 30})

    def test_limites_absent_de_la_base_rend_none(self):
        _ecrire(self.racine / "a.txt", "x")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")
        self.assertIsNone(check_skills.lire_limites_base(self.racine, "main"))

    def test_une_base_inconnue_est_une_panne_pas_un_vert(self):
        _ecrire(self.racine / "a.txt", "x")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")
        with self.assertRaises(check_skills.BaseIndisponible):
            check_skills.lire_limites_base(self.racine, "origin/inexistante")


class RegleC_InvariantsEnTete(Depot):
    CHEMIN = "plugins/p/skills/s/SKILL.md"

    def marque(self):
        return _limites(self.racine, invariants_en_tete=[self.CHEMIN])

    def test_un_skill_marque_sans_bloc_d_invariants_est_refuse(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", corps="# Titre\n\nDu texte.\n")
        refus = [a for a in self.controler(self.marque()).refus if a.regle == "c"]
        self.assertEqual(len(refus), 1)
        self.assertIn("invariants", refus[0].message.lower())

    def test_un_bloc_dans_les_60_premieres_lignes_est_accepte(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s",
               corps="# Titre\n\n## Invariants\n\n- ne jamais X\n\n## Suite\n\ntexte\n")
        self.assertEqual(self.controler(self.marque()).refus, [])

    def test_un_bloc_apres_la_ligne_60_est_refuse(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s",
               corps="remplissage\n" * 70 + "## Invariants\n\n- ne jamais X\n")
        self.assertIn("c", _regles(self.controler(self.marque())))

    def test_un_bloc_qui_deborde_les_5000_jetons_est_refuse(self):
        # 5 000 jetons estimés à 4 caractères chacun : 20 000 caractères.
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s",
               corps="## Invariants\n\n" + ("- une règle assez longue pour peser\n" * 700))
        refus = [a for a in self.controler(self.marque()).refus if a.regle == "c"]
        self.assertEqual(len(refus), 1)
        self.assertIn("5 000", refus[0].message)

    def test_un_skill_non_marque_n_est_pas_controle(self):
        self.plugin_conforme()
        self.assertEqual(self.controler().refus, [])


class RegleD_AgentsCitesDansPluginJson(Depot):
    def test_un_agent_absent_de_la_description_est_refuse_et_nomme(self):
        _manifeste(self.racine, "p", description="Un plugin avec l'agent alpha.")
        _agent(self.racine, "p", "alpha")
        _agent(self.racine, "p", "beta")
        refus = [a for a in self.controler().refus if a.regle == "d"]
        self.assertEqual(len(refus), 1)
        self.assertIn("beta", refus[0].message)
        self.assertNotIn("alpha", refus[0].message)
        self.assertTrue(refus[0].cible.endswith("plugin.json"))

    def test_tous_les_agents_cites_est_accepte(self):
        _manifeste(self.racine, "p", description="Agents alpha et beta.")
        _agent(self.racine, "p", "alpha")
        _agent(self.racine, "p", "beta")
        self.assertEqual(self.controler().refus, [])

    def test_un_plugin_sans_agents_n_a_rien_a_citer(self):
        self.plugin_conforme()
        self.assertEqual(self.controler().refus, [])


class RegleE_Compagnons(Depot):
    def partage(self, nom):
        return _ecrire(self.racine / f"plugins/p/skills/_partage/{nom}.md", "# x\n")

    def renvoi(self, nom):
        return f"${{CLAUDE_PLUGIN_ROOT}}/skills/_partage/{nom}.md"

    def test_un_fichier_partage_que_personne_ne_cite_est_refuse(self):
        self.plugin_conforme()
        self.partage("orphelin")
        refus = [a for a in self.controler().refus if a.regle == "e"]
        self.assertEqual(len(refus), 1)
        self.assertIn("orphelin.md", refus[0].message)

    def test_un_fichier_cite_par_un_skill_est_accepte(self):
        _manifeste(self.racine, "p")
        self.partage("a")
        _skill(self.racine, "p", "s", corps=(
            f"Ses compagnons sont les fichiers partagés\n  `{self.renvoi('a')}`, livrés.\n"))
        self.assertEqual(self.controler().refus, [])

    def test_un_fichier_cite_seulement_par_un_agent_est_accepte(self):
        _manifeste(self.racine, "p", description="agent ag")
        self.partage("a")
        _skill(self.racine, "p", "s")
        _ecrire(self.racine / "plugins/p/agents/ag.md",
                f"---\nname: ag\ndescription: d\n---\n📄 `{self.renvoi('a')}`\n")
        self.assertEqual(self.controler().refus, [])

    def test_un_compagnon_cite_dans_le_corps_mais_absent_de_la_liste_est_refuse(self):
        _manifeste(self.racine, "p")
        self.partage("a")
        self.partage("b")
        _skill(self.racine, "p", "s", corps=(
            f"📄 `{self.renvoi('b')}`\n\n"
            f"Ses compagnons sont les fichiers partagés\n  `{self.renvoi('a')}`, livrés.\n"))
        refus = [a for a in self.controler().refus if a.regle == "e"]
        self.assertEqual(len(refus), 1)
        self.assertIn("b.md", refus[0].message)
        self.assertIn("compagnons", refus[0].message)

    def test_une_liste_complete_est_acceptee(self):
        _manifeste(self.racine, "p")
        self.partage("a")
        self.partage("b")
        _skill(self.racine, "p", "s", corps=(
            f"📄 `{self.renvoi('b')}`\n\n"
            f"Ses compagnons sont les fichiers partagés\n  `{self.renvoi('a')}`,\n"
            f"  `{self.renvoi('b')}`, livrés.\n"))
        self.assertEqual(self.controler().refus, [])

    def test_un_skill_qui_cite_du_partage_sans_liste_de_compagnons_est_refuse(self):
        _manifeste(self.racine, "p")
        self.partage("a")
        _skill(self.racine, "p", "s", corps=f"📄 `{self.renvoi('a')}`\n")
        refus = [a for a in self.controler().refus if a.regle == "e"]
        self.assertEqual(len(refus), 1)
        self.assertIn("compagnons", refus[0].message)


class RegleF_ChampsIgnoresDesAgentsDePlugin(Depot):
    def test_hooks_mcpservers_et_permissionmode_sont_refuses(self):
        for champ in ("hooks", "mcpServers", "permissionMode"):
            with self.subTest(champ=champ):
                self.racine_neuve()
                _manifeste(self.racine, "p", description="agent ag")
                _agent(self.racine, "p", "ag", champs=f"{champ}: x\n")
                refus = [a for a in self.controler().refus if a.regle == "f"]
                self.assertEqual(len(refus), 1)
                self.assertIn(champ, refus[0].message)
                self.assertIn("ignor", refus[0].message)

    def racine_neuve(self):
        import shutil
        shutil.rmtree(self.racine / "plugins", ignore_errors=True)

    def test_un_agent_sans_ces_champs_est_accepte(self):
        _manifeste(self.racine, "p", description="agent ag")
        _agent(self.racine, "p", "ag", champs="model: sonnet\n")
        self.assertEqual(self.controler().refus, [])


class RegleG_MemoireEtLectureSeule(Depot):
    def agent(self, champs):
        _manifeste(self.racine, "p", description="agent ag")
        _agent(self.racine, "p", "ag", champs=champs)

    def test_disallowedtools_write_avec_memory_est_refuse(self):
        self.agent("disallowedTools:\n  - Write\nmemory: project\n")
        refus = [a for a in self.controler().refus if a.regle == "g"]
        self.assertEqual(len(refus), 1)
        self.assertIn("memory", refus[0].message)

    def test_disallowedtools_edit_avec_memory_est_refuse(self):
        self.agent("disallowedTools: [Edit]\nmemory: user\n")
        self.assertIn("g", _regles(self.controler()))

    def test_une_liste_d_outils_sans_write_ni_edit_avec_memory_est_refusee(self):
        self.agent("tools:\n  - Read\n  - Grep\nmemory: project\n")
        self.assertIn("g", _regles(self.controler()))

    def test_lecture_seule_sans_memory_est_accepte(self):
        self.agent("disallowedTools:\n  - Write\n  - Edit\n")
        self.assertEqual(self.controler().refus, [])

    def test_un_agent_qui_peut_ecrire_peut_avoir_une_memoire(self):
        self.agent("memory: project\n")
        self.assertEqual(self.controler().refus, [])

    def test_disallowedtools_sans_write_ni_edit_avec_memory_est_accepte(self):
        self.agent("disallowedTools:\n  - Bash\nmemory: project\n")
        self.assertEqual(self.controler().refus, [])


class RegleH_PasDeMemoireDAgentVersionnee(Depot):
    def test_un_dossier_agent_memory_est_refuse(self):
        self.plugin_conforme()
        _ecrire(self.racine / ".claude/agent-memory/relecteur/MEMORY.md", "x")
        refus = [a for a in self.controler().refus if a.regle == "h"]
        self.assertEqual(len(refus), 1)
        self.assertIn(".claude/agent-memory", refus[0].cible)

    def test_agent_memory_local_est_refuse_aussi(self):
        self.plugin_conforme()
        _ecrire(self.racine / ".claude/agent-memory-local/x/MEMORY.md", "x")
        self.assertIn("h", _regles(self.controler()))

    def test_un_depot_sans_memoire_d_agent_est_accepte(self):
        self.plugin_conforme()
        _ecrire(self.racine / ".claude/settings.json", "{}")
        self.assertEqual(self.controler().refus, [])


class ExceptionsDatees(Depot):
    def exception(self, **plus):
        exc = {"regle": "a", "cible": "plugins/p/skills/s/SKILL.md",
               "date": "2026-09-30", "raison": "défaut connu",
               "levee_par": "étape B7"}
        exc.update(plus)
        return exc

    def depot_fautif(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 2000)

    def test_une_exception_datee_n_est_pas_bloquante_et_reste_visible(self):
        self.depot_fautif()
        res = self.controler(_limites(self.racine, exceptions=[self.exception()]))
        self.assertEqual(res.refus, [])
        self.assertEqual(len(res.excusees), 1)
        anomalie, exc = res.excusees[0]
        self.assertEqual(anomalie.regle, "a")
        self.assertEqual(exc["levee_par"], "étape B7")

    def test_sans_exceptions_le_defaut_redevient_bloquant(self):
        self.depot_fautif()
        res = self.controler(_limites(self.racine, exceptions=[self.exception()]),
                             sans_exceptions=True)
        self.assertEqual(_regles(res), ["a"])
        self.assertEqual(res.excusees, [])

    def test_une_exception_qui_ne_correspond_plus_a_rien_est_refusee(self):
        self.plugin_conforme()
        res = self.controler(_limites(self.racine, exceptions=[self.exception()]))
        refus = [a for a in res.refus if a.regle == "exception"]
        self.assertEqual(len(refus), 1)
        self.assertIn("périmée", refus[0].message)

    def test_une_exception_sans_date_ni_raison_ni_levee_est_refusee(self):
        self.depot_fautif()
        for champ in ("date", "raison", "levee_par"):
            with self.subTest(champ=champ):
                exc = self.exception()
                del exc[champ]
                res = self.controler(_limites(self.racine, exceptions=[exc]))
                self.assertIn("exception", _regles(res))
                self.assertIn("a", _regles(res))

    def test_l_exception_d_une_autre_regle_n_excuse_pas(self):
        self.depot_fautif()
        res = self.controler(_limites(self.racine,
                                      exceptions=[self.exception(regle="d")]))
        self.assertIn("a", _regles(res))


class SortieDuProgramme(Depot):
    def test_les_exceptions_sont_affichees_a_chaque_passage(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 2000)
        limites = _limites(self.racine, exceptions=[{
            "regle": "a", "cible": "plugins/p/skills/s/SKILL.md",
            "date": "2026-09-30", "raison": "défaut connu", "levee_par": "étape B7"}])
        _ecrire(self.racine / "scripts/limites.json", json.dumps(limites))
        _ecrire(self.racine / "docs/garde-fous.md", REGISTRE_MINIMAL)
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            code = check_skills.main(["--racine", str(self.racine), "--sans-base"])
        self.assertEqual(code, 0, sortie.getvalue())
        self.assertIn("EXCEPTION", sortie.getvalue())
        self.assertIn("étape B7", sortie.getvalue())

    def test_une_regle_violee_donne_le_code_1(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 2000)
        _ecrire(self.racine / "scripts/limites.json", json.dumps(_limites(self.racine)))
        _ecrire(self.racine / "docs/garde-fous.md", REGISTRE_MINIMAL)
        erreur = io.StringIO()
        with contextlib.redirect_stderr(erreur), contextlib.redirect_stdout(io.StringIO()):
            code = check_skills.main(["--racine", str(self.racine), "--sans-base"])
        self.assertEqual(code, 1)
        self.assertIn("(a)", erreur.getvalue())


REGISTRE_MINIMAL = """# Registre

| Règle | Ce qu'elle protège | Origine | Garde | Où il tourne | Statut |
| --- | --- | --- | --- | --- | --- |
| Exemple | rien | test | réglage GitHub | GitHub | réglage |
"""


class Registre(Depot):
    def registre(self, *lignes):
        entete = ("| Règle | Ce qu'elle protège | Origine | Garde | Où il tourne | Statut |\n"
                  "| --- | --- | --- | --- | --- | --- |\n")
        _ecrire(self.racine / "docs/garde-fous.md", entete + "\n".join(lignes) + "\n")

    def ligne(self, garde, statut="en place"):
        return f"| Une règle | Elle protège X | 2026-09-30, incident | {garde} | CI | {statut} |"

    def base(self):
        _ecrire(self.racine / "scripts/check_x.py", "# x\n")
        _ecrire(self.racine / "scripts/ci_locale.sh", "#!/bin/bash\n")
        _ecrire(self.racine / ".github/workflows/ci.yml",
                "jobs:\n  garde:\n    runs-on: x\n  evals:\n    runs-on: x\n")
        _ecrire(self.racine / "evals/p/un-cas/case.yaml", "x: 1\n")

    def test_des_gardes_existants_sont_acceptes(self):
        self.base()
        self.registre(self.ligne("`scripts/check_x.py`, job `ci.yml#evals`"),
                      self.ligne("`ci_locale.sh` et `evals/p/un-cas`"))
        self.assertEqual(check_skills.verifier_registre(self.racine), [])

    def test_un_script_cite_qui_n_existe_pas_est_refuse(self):
        self.base()
        self.registre(self.ligne("`scripts/fantome.py`"))
        anomalies = check_skills.verifier_registre(self.racine)
        self.assertEqual(len(anomalies), 1)
        self.assertIn("fantome.py", anomalies[0].message)

    def test_un_job_cite_qui_n_existe_pas_est_refuse(self):
        self.base()
        self.registre(self.ligne("`ci.yml#absent`"))
        anomalies = check_skills.verifier_registre(self.racine)
        self.assertEqual(len(anomalies), 1)
        self.assertIn("absent", anomalies[0].message)

    def test_un_cas_d_eval_cite_qui_n_existe_pas_est_refuse(self):
        self.base()
        self.registre(self.ligne("`evals/p/inconnu`"))
        self.assertEqual(len(check_skills.verifier_registre(self.racine)), 1)

    def test_une_ligne_en_place_sans_aucun_garde_verifiable_est_refusee(self):
        self.base()
        self.registre(self.ligne("de la vigilance"))
        anomalies = check_skills.verifier_registre(self.racine)
        self.assertEqual(len(anomalies), 1)
        self.assertIn("garde", anomalies[0].message)

    def test_un_garde_prevu_n_est_pas_verifie_mais_doit_dire_son_etape(self):
        self.base()
        self.registre(self.ligne("`scripts/pas_encore.py`", "prévu — étape B5"))
        self.assertEqual(check_skills.verifier_registre(self.racine), [])
        self.registre(self.ligne("`scripts/pas_encore.py`", "prévu"))
        self.assertEqual(len(check_skills.verifier_registre(self.racine)), 1)

    def test_un_garde_manquant_est_admis_et_un_statut_inconnu_ne_l_est_pas(self):
        self.base()
        self.registre(self.ligne("manquant", "manquant — à décider"))
        self.assertEqual(check_skills.verifier_registre(self.racine), [])
        self.registre(self.ligne("`scripts/check_x.py`", "bientôt"))
        self.assertEqual(len(check_skills.verifier_registre(self.racine)), 1)

    def test_un_registre_absent_ou_vide_est_refuse(self):
        self.base()
        self.assertEqual(len(check_skills.verifier_registre(self.racine)), 1)
        _ecrire(self.racine / "docs/garde-fous.md", "# Registre\n\nRien.\n")
        self.assertEqual(len(check_skills.verifier_registre(self.racine)), 1)


class LireFrontmatter(unittest.TestCase):
    def test_scalaire_liste_bloc_et_flux(self):
        texte = ("---\nname: a\ndescription: >-\n  premiere\n  seconde\n"
                 "tools:\n  - Read\n  - Grep\ndisallowedTools: [Edit, Write]\n"
                 "model: sonnet\n---\ncorps\n")
        champs = check_skills.lire_frontmatter(texte)
        self.assertEqual(champs["name"], "a")
        self.assertEqual(champs["description"], "premiere seconde")
        self.assertEqual(champs["tools"], ["Read", "Grep"])
        self.assertEqual(champs["disallowedTools"], ["Edit", "Write"])
        self.assertEqual(champs["model"], "sonnet")


if __name__ == "__main__":
    unittest.main()
