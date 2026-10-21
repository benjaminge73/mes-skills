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


def _agent(racine: Path, plugin: str, nom: str, champs: str = "", fixe: bool = True) -> Path:
    """Un agent ; ``fixe`` lui pose ``model`` et ``effort``, que la règle (m) exige de tous."""
    if fixe:
        champs = "model: haiku\neffort: high\n" + champs
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


PHRASE_K = "6. **Un arrêt par `maxTurns` n'est pas un échec.** Reprise au même palier.\n"


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
                "---\nname: a\ndescription: " + "z" * 1600 + "\nmodel: haiku\neffort: high\n---\nCorps.\n")
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
                f"---\nname: ag\ndescription: d\nmodel: haiku\neffort: high\n---\n📄 `{self.renvoi('a')}`\n")
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


class RegleI_CategoriesDesEvals(Depot):
    """Chaque cas d'un plugin est dans une catégorie de evals/categories.json,
    chaque cas cité existe, chaque catégorie a un cas, chaque chemin exercé existe."""

    def evals(self, *cas):
        for nom in cas:
            _ecrire(self.racine / "evals" / "p" / nom / "prompt.md",
                    "---\nmax_turns: 3\n---\nRéponds OK.\n")

    def categories(self, plugin="p", **par_categorie):
        _ecrire(self.racine / "evals" / "categories.json", json.dumps({
            "_commentaire": "ignoré", plugin: par_categorie}))

    def conforme(self):
        self.plugin_conforme()
        self.evals("c1", "c2")
        self.categories(
            un={"exerce": ["skills/s/"], "cas": ["c1"]},
            deux={"exerce": ["skills/s/SKILL.md"], "cas": ["c1", "c2"]},
        )

    def refus_i(self):
        return [a for a in self.controler().refus if a.regle == "i"]

    def test_des_cas_tous_classes_sont_acceptes(self):
        self.conforme()
        self.assertEqual(self.controler().refus, [])

    def test_un_cas_sans_categorie_est_refuse_avec_la_marche_a_suivre(self):
        self.conforme()
        self.evals("orphelin")
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("orphelin", refus[0].message)
        self.assertIn("categories.json", refus[0].message)

    def test_une_categorie_sans_cas_est_refusee_et_nommee(self):
        self.conforme()
        self.categories(
            un={"exerce": ["skills/s/"], "cas": ["c1", "c2"]},
            vide={"exerce": ["skills/s/"], "cas": []},
        )
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("vide", refus[0].message)

    def test_un_cas_cite_qui_n_existe_pas_est_refuse_et_nomme(self):
        self.conforme()
        self.categories(un={"exerce": ["skills/s/"], "cas": ["c1", "c2", "fantome"]})
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("fantome", refus[0].message)

    def test_un_chemin_exerce_qui_n_existe_pas_est_refuse_et_nomme(self):
        self.conforme()
        self.categories(un={"exerce": ["skills/s/", "agents/absent.md"], "cas": ["c1", "c2"]})
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("agents/absent.md", refus[0].message)

    def test_un_chemin_exerce_se_lit_sous_le_plugin_pas_a_la_racine(self):
        self.conforme()
        _ecrire(self.racine / "skills" / "ailleurs" / "SKILL.md", "x\n")  # à la racine du dépôt
        self.categories(un={"exerce": ["skills/s/", "skills/ailleurs/"], "cas": ["c1", "c2"]})
        self.assertEqual(len(self.refus_i()), 1)

    def test_categories_json_absent_alors_qu_un_plugin_a_des_evals_est_refuse(self):
        self.plugin_conforme()
        self.evals("c1")
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("categories.json", refus[0].message)

    def test_un_plugin_absent_de_categories_json_est_refuse(self):
        self.conforme()
        self.categories(plugin="autre", un={"exerce": ["skills/s/"], "cas": ["c1", "c2"]})
        refus = self.refus_i()
        self.assertTrue(refus)
        self.assertIn("p", refus[0].message)

    def test_un_categories_json_illisible_est_refuse_pas_ignore(self):
        self.conforme()
        _ecrire(self.racine / "evals" / "categories.json", "{ pas du json")
        self.assertEqual(len(self.refus_i()), 1)

    def test_un_plugin_sans_dossier_d_evals_n_est_pas_controle(self):
        self.plugin_conforme()
        self.assertEqual(self.controler().refus, [])

    def test_un_dossier_sans_prompt_ni_case_n_est_pas_un_cas(self):
        self.conforme()
        _ecrire(self.racine / "evals" / "p" / "notes" / "lisez-moi.md", "pas un cas\n")
        self.assertEqual(self.refus_i(), [])

    def test_un_cas_a_case_yaml_seul_est_un_cas(self):
        self.conforme()
        _ecrire(self.racine / "evals" / "p" / "yaml-seul" / "case.yaml", "name: x\n")
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("yaml-seul", refus[0].message)

    def test_un_fichier_sous_skills_qu_aucune_categorie_n_exerce_est_refuse_et_nomme(self):
        self.conforme()
        _ecrire(self.racine / "plugins" / "p" / "skills" / "_partage" / "orphelin.md", "x\n")
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("skills/_partage/orphelin.md", refus[0].message)
        self.assertIn("categories.json", refus[0].message)

    def test_un_agent_qu_aucune_categorie_n_exerce_est_refuse_et_nomme(self):
        self.conforme()
        _agent(self.racine, "p", "seul")
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("agents/seul.md", refus[0].message)

    def test_un_fichier_couvert_par_un_dossier_ou_par_son_chemin_exact_est_accepte(self):
        self.conforme()
        _agent(self.racine, "p", "seul")
        _ecrire(self.racine / "plugins" / "p" / "skills" / "_partage" / "regle.md", "x\n")
        _ecrire(self.racine / "plugins" / "p" / "skills" / "_partage" / "scripts" / "outil.sh", "x\n")
        self.categories(
            un={"exerce": ["skills/s/", "agents/seul.md", "skills/_partage/regle.md",
                           "skills/_partage/scripts/"], "cas": ["c1", "c2"]})
        self.assertEqual(self.refus_i(), [])

    def test_un_prefixe_n_en_couvre_pas_un_voisin_au_nom_proche(self):
        self.conforme()
        _ecrire(self.racine / "plugins" / "p" / "skills" / "sosie" / "SKILL.md", "x\n")
        refus = self.refus_i()
        self.assertEqual(len(refus), 1)
        self.assertIn("skills/sosie/SKILL.md", refus[0].message)

    def test_un_plugin_sans_banc_n_a_pas_a_exercer_ses_fichiers(self):
        self.plugin_conforme()
        _ecrire(self.racine / "plugins" / "p" / "skills" / "s" / "libre.md", "x\n")
        self.assertEqual(self.controler().refus, [])

    def test_le_depot_reel_respecte_la_regle(self):
        racine = Path(__file__).resolve().parents[1]
        limites = json.loads((racine / "scripts" / "limites.json").read_text("utf-8"))
        res = check_skills.controler(racine, limites)
        self.assertEqual([a for a in res.refus if a.regle == "i"], [])


class RegleJ_ToursMaximauxDesEvals(Depot):
    """Chaque cas d'un banc déclare ``max_turns`` : sinon le lanceur impose 10 tours."""

    def setUp(self):
        super().setUp()
        self.plugin_conforme()

    def cas(self, nom, prompt=None, case=None):
        if prompt is not None:
            _ecrire(self.racine / "evals" / "p" / nom / "prompt.md", prompt)
        if case is not None:
            _ecrire(self.racine / "evals" / "p" / nom / "case.yaml", case)

    def refus_j(self):
        return [a for a in self.controler().refus if a.regle == "j"]

    def test_max_turns_au_frontmatter_de_prompt_md_suffit(self):
        self.cas("c", prompt="---\nmax_turns: 30\n---\nRéponds OK.\n")
        self.assertEqual(self.refus_j(), [])

    def test_max_turns_sous_execution_dans_case_yaml_suffit(self):
        self.cas("c", prompt="Réponds OK.\n", case=(
            'schema_version: "1.1"\nname: c\n# commentaire\nexecution:\n'
            "  timeout_seconds: 900\n\n  max_turns: 80\ncontext:\n  scaffold_script: f.sh\n"))
        self.assertEqual(self.refus_j(), [])

    def test_un_cas_sans_max_turns_est_refuse_et_nomme(self):
        # Le cas réel du 2026-10-15 : case.yaml + prompt.md, ni l'un ni l'autre ne fixe les tours.
        self.cas("cloture", prompt="Utilise le skill.\n",
                 case='schema_version: "1.1"\nname: cloture\ncontext:\n  scaffold_script: f.sh\n')
        refus = self.refus_j()
        self.assertEqual([a.cible for a in refus], ["evals/p/cloture"])
        self.assertIn("10 tours", refus[0].message)
        self.assertIn("max_turns", refus[0].message)

    def test_max_turns_hors_du_bloc_execution_ne_compte_pas(self):
        self.cas("c", case=('schema_version: "1.1"\nname: c\nexecution:\n  timeout_seconds: 900\n'
                            "context:\n  max_turns: 80\n"))
        self.assertEqual(len(self.refus_j()), 1)

    def test_un_plugin_sans_banc_n_est_pas_concerne(self):
        self.assertEqual(self.refus_j(), [])

    def test_le_depot_reel_respecte_la_regle(self):
        racine = Path(__file__).resolve().parents[1]
        limites = json.loads((racine / "scripts" / "limites.json").read_text("utf-8"))
        res = check_skills.controler(racine, limites)
        self.assertEqual([a for a in res.refus if a.regle == "j"], [])


class RegleK_MaxTurnsDeLExecutant(Depot):
    """L'``executant`` fixe ``maxTurns`` et ``etapes.md`` garde la règle de la sortie partielle."""

    def setUp(self):
        super().setUp()
        self.plugin_conforme()

    def executant(self, frontmatter="maxTurns: 90\n", etapes=PHRASE_K):
        _ecrire(self.racine / "plugins" / "p" / "agents" / "executant.md",
                f"---\nname: executant\ndescription: Exécute une étape.\n{frontmatter}---\nCorps.\n")
        if etapes is not None:
            _ecrire(self.racine / "plugins" / "p" / "skills" / "executer-plan-notion" / "etapes.md", etapes)

    def refus_k(self):
        return [a for a in self.controler().refus if a.regle == "k"]

    def test_un_plugin_sans_executant_n_est_pas_concerne(self):
        self.assertEqual(self.refus_k(), [])

    def test_executant_avec_max_turns_et_la_regle_est_conforme(self):
        self.executant()
        self.assertEqual(self.refus_k(), [])

    def test_executant_sans_max_turns_est_refuse_et_nomme(self):
        self.executant(frontmatter="")
        refus = self.refus_k()
        self.assertEqual([a.cible for a in refus], ["plugins/p/agents/executant.md"])
        self.assertIn("maxTurns", refus[0].message)

    def test_max_turns_non_numerique_est_refuse(self):
        self.executant(frontmatter="maxTurns: beaucoup\n")
        self.assertEqual(len(self.refus_k()), 1)

    def test_la_regle_d_etapes_md_disparue_est_refusee(self):
        self.executant(etapes="6. Un arrêt par la limite est un échec.\n")
        refus = self.refus_k()
        self.assertEqual([a.cible for a in refus], ["plugins/p/skills/executer-plan-notion/etapes.md"])

    def test_le_depot_reel_respecte_la_regle(self):
        racine = Path(__file__).resolve().parents[1]
        limites = json.loads((racine / "scripts" / "limites.json").read_text("utf-8"))
        res = check_skills.controler(racine, limites)
        self.assertEqual([a for a in res.refus if a.regle == "k"], [])


class RegleM_ModeleEtEffortDesAgents(Depot):
    """Chaque agent fixe ``model`` et ``effort`` ; ``ouverture.md`` nomme le ``preparateur``."""

    def setUp(self):
        super().setUp()
        self.plugin_conforme()

    def refus_m(self):
        return [a for a in self.controler().refus if a.regle == "m"]

    def ouverture(self, texte):
        _ecrire(self.racine / "plugins" / "p" / "skills" / "executer-plan-notion" / "ouverture.md", texte)

    def test_un_agent_qui_fixe_model_et_effort_est_conforme(self):
        _agent(self.racine, "p", "a", "model: sonnet\neffort: medium\n", fixe=False)
        self.assertEqual(self.refus_m(), [])

    def test_un_agent_sans_model_est_refuse_et_nomme(self):
        _agent(self.racine, "p", "a", "effort: high\n", fixe=False)
        refus = self.refus_m()
        self.assertEqual([a.cible for a in refus], ["plugins/p/agents/a.md"])
        self.assertIn("`model`", refus[0].message)
        self.assertNotIn("`effort`", refus[0].message)

    def test_un_agent_sans_effort_est_refuse(self):
        _agent(self.racine, "p", "a", "model: haiku\n", fixe=False)
        refus = self.refus_m()
        self.assertEqual(len(refus), 1)
        self.assertIn("`effort`", refus[0].message)

    def test_un_agent_sans_aucun_des_deux_les_nomme_tous_les_deux(self):
        _agent(self.racine, "p", "a", fixe=False)
        message = self.refus_m()[0].message
        self.assertIn("`model`", message)
        self.assertIn("`effort`", message)

    def test_preparateur_cite_dans_ouverture_md_est_conforme(self):
        _agent(self.racine, "p", "preparateur", "model: sonnet\neffort: medium\n", fixe=False)
        self.ouverture("Appeler `plans-notion:preparateur`, jamais un `general-purpose`.\n")
        self.assertEqual(self.refus_m(), [])

    def test_preparateur_absent_d_ouverture_md_est_refuse(self):
        _agent(self.racine, "p", "preparateur", "model: sonnet\neffort: medium\n", fixe=False)
        self.ouverture("Préparer le plan.\n")
        refus = self.refus_m()
        self.assertEqual([a.cible for a in refus], ["plugins/p/skills/executer-plan-notion/ouverture.md"])

    def test_la_regle_du_general_purpose_disparue_est_refusee(self):
        _agent(self.racine, "p", "preparateur", "model: sonnet\neffort: medium\n", fixe=False)
        self.ouverture("Appeler `plans-notion:preparateur`.\n")
        self.assertEqual(len(self.refus_m()), 1)

    def test_le_depot_reel_respecte_la_regle(self):
        racine = Path(__file__).resolve().parents[1]
        limites = json.loads((racine / "scripts" / "limites.json").read_text("utf-8"))
        res = check_skills.controler(racine, limites)
        self.assertEqual([a for a in res.refus if a.regle == "m"], [])


class RegleN_SyntaxesNotionInterdites(Depot):
    """Aucun ``skills/**/*.md`` n'écrit ``{color=``, ``<details>`` ni ``<summary>``.

    Panne évitée (constatée le 2026-10-21, mesurée sur une page de test) : le
    connecteur Notion de claude.ai affiche ``{color=…}`` comme texte visible et
    convertit ``<details>`` en bloc ``<toggle>`` avec l'avertissement « legacy
    Markdown ». Une consigne qui écrit ces syntaxes produit une page fausse sans
    erreur.
    """

    SKILL = "plugins/p/skills/s/SKILL.md"
    # Six lignes avant le corps : frontmatter de quatre lignes, un titre, une ligne vide.
    # Le corps commence donc à la ligne 7.
    ENTETE = "---\nname: s\ndescription: Un skill.\n---\n# Titre\n\n"

    def setUp(self):
        super().setUp()
        self.plugin_conforme()

    def refus_n(self):
        return [a for a in self.controler().refus if a.regle == "n"]

    def ecrire_corps(self, chemin_relatif, ligne):
        _ecrire(self.racine / chemin_relatif, self.ENTETE + ligne + "\n")

    def test_color_entre_accolades_est_refuse_avec_fichier_et_ligne(self):
        self.ecrire_corps(self.SKILL, 'Un titre {color="blue"}')
        refus = self.refus_n()
        self.assertEqual([a.cible for a in refus], [self.SKILL])
        self.assertIn("ligne 7", refus[0].message)

    def test_details_est_refuse_avec_fichier_et_ligne(self):
        self.ecrire_corps(self.SKILL, "<details>")
        refus = self.refus_n()
        self.assertEqual([a.cible for a in refus], [self.SKILL])
        self.assertIn("ligne 7", refus[0].message)

    def test_summary_est_refuse_avec_fichier_et_ligne(self):
        self.ecrire_corps(self.SKILL, "<summary>Détail</summary>")
        refus = self.refus_n()
        self.assertEqual([a.cible for a in refus], [self.SKILL])
        self.assertIn("ligne 7", refus[0].message)

    def test_un_fichier_de_partage_est_aussi_refuse(self):
        # Attrape un garde qui ne lirait que ``SKILL.md`` : les fichiers de
        # ``skills/_partage/`` écrivent aussi des pages Notion (même panne, autre fichier).
        partage = "plugins/p/skills/_partage/notion.md"
        self.ecrire_corps(partage, '{color="red"} rouge')
        self.assertEqual([a.cible for a in self.refus_n()], [partage])

    def test_un_skill_sans_ces_syntaxes_passe(self):
        # Témoin nul : la forme admise (couleur par attribut de balise) ne déclenche rien.
        self.ecrire_corps(self.SKILL, 'Un titre <span color="blue">en bleu</span>')
        self.assertEqual(self.refus_n(), [])


ENTETE_FICHE = "| Catégorie | Cas au 2026-10-16 | Cas mesurés le 2026-09-30 | Un bras, 3 passages | Un passage |"
SEPARATEUR_FICHE = "|---|---|---|---|---|"
LIGNES_CONFORMES = (
    "| `un` | 1 | 1 | 1 $ | 0,3 $ |",
    "| `deux` | 2 | 2 | 2 $ | 0,6 $ |",
    "| **tout le banc** | 2 | 2 | 3 $ | 0,9 $ |",
)


class RegleL_ComptesDuTableauDeCouts(Depot):
    """Le tableau « Cas au … » de la fiche « claude plugin eval » compte les cas de
    chaque catégorie de evals/categories.json, et sa ligne « tout le banc » leur total
    distinct. Un tableau resté à 16 cas pour un banc qui en compte davantage ne doit plus passer."""

    def setUp(self):
        super().setUp()
        self.plugin_conforme()
        for nom in ("c1", "c2"):
            _ecrire(self.racine / "evals" / "p" / nom / "prompt.md",
                    "---\nmax_turns: 3\n---\nRéponds OK.\n")
        _ecrire(self.racine / "evals" / "categories.json", json.dumps({"p": {
            "un": {"exerce": ["skills/s/"], "cas": ["c1"]},
            "deux": {"exerce": ["skills/s/SKILL.md"], "cas": ["c1", "c2"]},
        }}))

    def fiche(self, *lignes, entete=ENTETE_FICHE):
        # Un tableau d'une autre section, qui porte des comptes faux : la règle ne le lit pas.
        _ecrire(self.racine / "plugins" / "p" / "skills" / "_partage" / "outils-et-quotas.md", (
            "# Outils\n\n## Autre section\n\n"
            "| Catégorie | Cas au 2026-10-16 |\n|---|---|\n| `un` | 99 |\n\n"
            "## Fiche — claude plugin eval\n\nTexte de la fiche.\n\n"
            + "\n".join([entete, SEPARATEUR_FICHE, *lignes])
            + "\n\nLa suite.\n"))

    def refus_l(self):
        return [a for a in self.controler().refus if a.regle == "l"]

    def test_une_fiche_conforme_est_acceptee(self):
        self.fiche(*LIGNES_CONFORMES)
        self.assertEqual(self.refus_l(), [])

    def test_un_compte_faux_est_refuse_et_nomme_avec_le_lu_et_l_attendu(self):
        self.fiche("| `un` | 7 | 1 $ | 1 $ | 0,3 $ |", LIGNES_CONFORMES[1], LIGNES_CONFORMES[2])
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("`un`", refus[0].message)
        self.assertIn("compte 7 cas", refus[0].message)
        self.assertIn("1 dans", refus[0].message)

    def test_une_categorie_sans_ligne_est_refusee_et_nommee(self):
        self.fiche(LIGNES_CONFORMES[0], LIGNES_CONFORMES[2])
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("`deux`", refus[0].message)

    def test_une_ligne_de_categorie_inconnue_est_refusee_et_nommee(self):
        self.fiche(LIGNES_CONFORMES[0], LIGNES_CONFORMES[1],
                   "| `fantome` | 0 | 0 | 0 $ | 0 $ |", LIGNES_CONFORMES[2])
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("`fantome`", refus[0].message)

    def test_un_total_qui_additionne_les_cas_au_lieu_de_les_dedoublonner_est_refuse(self):
        # c1 est dans « un » et dans « deux » : 1 + 2 = 3 lignes, 2 cas distincts.
        self.fiche(LIGNES_CONFORMES[0], LIGNES_CONFORMES[1], "| **tout le banc** | 3 | 2 | 3 $ | 0,9 $ |")
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("donne 3 cas", refus[0].message)
        self.assertIn("en compte 2 distincts", refus[0].message)

    def test_une_ligne_tout_le_banc_absente_est_refusee(self):
        self.fiche(LIGNES_CONFORMES[0], LIGNES_CONFORMES[1])
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("tout le banc", refus[0].message)

    def test_un_compte_non_entier_est_refuse_sans_planter(self):
        self.fiche("| `un` | environ 1 | 1 $ | 1 $ | 0,3 $ |", LIGNES_CONFORMES[1], LIGNES_CONFORMES[2])
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("`un`", refus[0].message)

    def test_une_colonne_cas_au_absente_est_refusee(self):
        self.fiche(*LIGNES_CONFORMES, entete="| Catégorie | Cas mesurés le 2026-09-30 | Un passage |")
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("Cas au", refus[0].message)

    def test_une_fiche_sans_section_ni_tableau_est_refusee(self):
        _ecrire(self.racine / "plugins" / "p" / "skills" / "_partage" / "outils-et-quotas.md",
                "# Outils\n\nRien de chiffré.\n")
        refus = self.refus_l()
        self.assertEqual(len(refus), 1)
        self.assertIn("tableau", refus[0].message)

    def test_un_plugin_sans_fiche_n_est_pas_controle(self):
        self.assertEqual(self.refus_l(), [])

    def test_des_categories_illisibles_sont_signalees_par_i_seule(self):
        # La panne de categories.json relève de la règle (i) : (k) ne la double pas.
        self.fiche(*LIGNES_CONFORMES)
        _ecrire(self.racine / "evals" / "categories.json", "{ pas du json")
        self.assertEqual(self.refus_l(), [])
        self.assertEqual(len([a for a in self.controler().refus if a.regle == "i"]), 1)

    def test_le_depot_reel_respecte_la_regle(self):
        racine = Path(__file__).resolve().parents[1]
        limites = json.loads((racine / "scripts" / "limites.json").read_text("utf-8"))
        res = check_skills.controler(racine, limites)
        self.assertEqual([a for a in res.refus if a.regle == "l"], [])


class RegistreDeLaRegleL(unittest.TestCase):
    """La ligne du registre qui dit que le tableau de coûts des évals suit le banc."""

    RACINE = Path(__file__).resolve().parents[1]

    def ligne(self, debut):
        texte = (self.RACINE / "docs" / "garde-fous.md").read_text("utf-8")
        trouvees = [l for l in texte.splitlines()
                    if l.startswith("|") and l.split("|")[1].strip().startswith(debut)]
        self.assertEqual(len(trouvees), 1, f"une ligne « {debut}… » attendue au registre")
        return [c.strip() for c in trouvees[0].strip().strip("|").split("|")]

    def test_la_regle_l_est_au_registre_et_en_place(self):
        cellules = self.ligne("Le tableau de coûts des évals suit le banc")
        self.assertIn("scripts/check_skills.py", cellules[3])
        self.assertIn("(règle l)", cellules[3])
        self.assertTrue(cellules[5].startswith("en place"))


class RegistreDuLotB9(unittest.TestCase):
    """Les lignes du registre que l'étape B9 doit poser, sur le vrai dépôt."""

    RACINE = Path(__file__).resolve().parents[1]

    def lignes(self):
        texte = (self.RACINE / "docs" / "garde-fous.md").read_text("utf-8")
        return [l for l in texte.splitlines() if l.startswith("|")]

    def ligne(self, debut):
        trouvees = [l for l in self.lignes() if l.split("|")[1].strip().startswith(debut)]
        self.assertEqual(len(trouvees), 1, f"une ligne « {debut}… » attendue au registre")
        return [c.strip() for c in trouvees[0].strip().strip("|").split("|")]

    def test_le_registre_reste_coherent(self):
        self.assertEqual(check_skills.verifier_registre(self.RACINE), [])

    def test_la_regle_des_categories_est_au_registre_et_en_place(self):
        cellules = self.ligne("Chaque cas d'éval a sa catégorie")
        self.assertIn("scripts/check_skills.py", cellules[3])
        self.assertIn("evals/categories.json", cellules[3])
        self.assertTrue(cellules[5].startswith("en place"))

    def test_le_plancher_des_evals_est_au_registre_et_en_place(self):
        cellules = self.ligne("Plancher des évals")
        self.assertIn("scripts/evals_selection.py", cellules[3])
        self.assertIn("ci.yml#evals-portee", cellules[3])
        self.assertTrue(cellules[5].startswith("en place"))

    def test_le_verdict_au_nom_fixe_est_au_registre_et_exige_par_le_ruleset(self):
        cellules = self.ligne("Verdict des évals au nom fixe")
        self.assertIn("ci.yml#evals-verdict", cellules[3])
        self.assertTrue(cellules[5].startswith("en place"))
        self.assertIn("exigé par le ruleset", " ".join(cellules))
        self.assertNotIn("pas encore", " ".join(cellules))


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
