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


def _agent(racine: Path, plugin: str, nom: str, champs: str = "", fixe: bool = True,
           outils: bool = True) -> Path:
    """Un agent ; ``fixe`` lui pose ``model`` et ``effort``, que la règle (m) exige de tous.

    ``outils`` lui pose une surface d'outils (``disallowedTools``, neutre pour les règles
    g et h) si ``champs`` n'en déclare aucune, que la règle (p) exige de tous.
    """
    if fixe:
        champs = "model: haiku\neffort: high\n" + champs
    if outils and not any(ligne.startswith(("tools:", "disallowedTools:"))
                          for ligne in champs.splitlines()):
        champs += "disallowedTools:\n  - Bash\n"
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
    longueurs = {
        p.relative_to(racine).as_posix(): {"caracteres": 10_000}
        for p in racine.glob("plugins/*/skills/*/SKILL.md")
    }
    limites = {"taille_skill_md": tailles, "longueur_description": longueurs,
               "invariants_en_tete": [], "veille_jours_max": 30, "exceptions": []}
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
                "---\nname: a\ndescription: " + "z" * 1600 + "\nmodel: haiku\neffort: high\n"
                "disallowedTools: [Bash]\n---\nCorps.\n")
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


class RegleO_DescriptionSousSonPlafond(Depot):
    CHEMIN = "plugins/p/skills/s/SKILL.md"

    def test_une_description_plus_longue_que_son_plafond_est_refusee(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 301)
        limites = _limites(self.racine)
        limites["longueur_description"][self.CHEMIN] = {"caracteres": 300}
        refus = [a for a in self.controler(limites).refus if a.regle == "o"]
        self.assertEqual(len(refus), 1)
        self.assertIn("300", refus[0].message)

    def test_une_description_sous_son_plafond_passe(self):
        # Vert avant le code : c'est le garde-fou contre un refus à tort une fois la règle écrite.
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="x" * 299)
        limites = _limites(self.racine)
        limites["longueur_description"][self.CHEMIN] = {"caracteres": 300}
        self.assertEqual(self.controler(limites).refus, [])

    def test_un_skill_sans_plafond_de_description_est_refuse(self):
        # En plus du budget : sans ce refus, un skill ajouté hors de la table échappe
        # à la règle en silence (même garde que la règle b pour la taille).
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", description="Court.")
        limites = _limites(self.racine)
        limites["longueur_description"] = {}
        refus = [a for a in self.controler(limites).refus if a.regle == "o"]
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

    def test_une_hausse_du_plafond_de_description_est_refusee(self):
        base = {"longueur_description": {"x/SKILL.md": {"caracteres": 1000}}}
        tete = {"longueur_description": {"x/SKILL.md": {"caracteres": 1001}}}
        anomalies = check_skills.verifier_cliquet(tete, base)
        self.assertEqual([a.regle for a in anomalies], ["o"])
        self.assertIn("baisser", anomalies[0].message)

    def test_un_plafond_de_description_retire_alors_qu_il_existait_est_refuse(self):
        # Retirer la clé relèverait le plafond à l'infini : même panne que la hausse, sans chiffre.
        base = {"longueur_description": {"x/SKILL.md": {"caracteres": 1000}}}
        tete = {"longueur_description": {}}
        anomalies = check_skills.verifier_cliquet(tete, base)
        self.assertEqual([a.regle for a in anomalies], ["o"])

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
                f"---\nname: ag\ndescription: d\nmodel: haiku\neffort: high\ntools: [Read]\n"
                f"---\n📄 `{self.renvoi('a')}`\n")
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


class RegleP_SurfaceDOutilsDesAgents(Depot):
    """Chaque agent de ``agents/`` déclare sa surface d'outils : ``tools`` ou ``disallowedTools``.

    Panne évitée : un agent sans liste reçoit tous les outils de la session, MCP compris,
    et son frontmatter ne dit nulle part ce qu'il peut faire. Le ``preparateur`` a tourné
    ainsi depuis sa création, sans que personne le voie.
    """

    def agent(self, champs, outils=True):
        _manifeste(self.racine, "p", description="agent ag")
        _agent(self.racine, "p", "ag", champs=champs, outils=outils)

    def refus_p(self):
        return [a for a in self.controler().refus if a.regle == "p"]

    def test_un_agent_sans_tools_ni_disallowedtools_est_refuse_et_nomme(self):
        # Attrape une règle qui ne lirait pas la surface d'outils : l'agent passerait en silence.
        self.agent("", outils=False)
        refus = self.refus_p()
        self.assertEqual([a.cible for a in refus], ["plugins/p/agents/ag.md"])
        self.assertIn("tools", refus[0].message)
        self.assertIn("disallowedTools", refus[0].message)

    def test_un_agent_qui_declare_tools_passe(self):
        self.agent("tools:\n  - Bash\n  - Read\n")
        self.assertEqual(self.refus_p(), [])

    def test_un_agent_qui_declare_disallowedtools_passe(self):
        # Témoin nul : la forme du relecteur, qui garde presque tout et se prive d'Edit et Write.
        self.agent("disallowedTools:\n  - Edit\n  - Write\n")
        self.assertEqual(self.refus_p(), [])


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
        _ecrire(self.racine / "plugins" / "p" / "skills" / "_partage" / "outils-connecteurs-et-evals.md", (
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
        _ecrire(self.racine / "plugins" / "p" / "skills" / "_partage" / "outils-connecteurs-et-evals.md",
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


PREFIXE_SKILL = "---\nname: s\ndescription: Un skill.\n---\n"


def _texte_de_taille(taille: int) -> str:
    """Un SKILL.md de exactement ``taille`` caractères (``len``, pas octets), frontmatter valide."""
    return PREFIXE_SKILL + "x" * (taille - len(PREFIXE_SKILL) - 1) + "\n"


class BudgetDeTaille(Depot):
    """Règle (q) : un SKILL.md tient sous 25 000 caractères, un fichier de ``skills/_partage/``
    sous 30 000. Une exception datée couvre un fichier, jusqu'à son plafond, et ne monte pas.

    Pannes attrapées : le seuil SKILL et sa frontière, le seuil des ``_partage`` et sa frontière,
    une exception qui laisse grossir le fichier au-delà de son plafond, un fichier hors exception
    qui échappe au seuil à cause d'un voisin excepté, une exception qui survit au passage sous le
    seuil, une exception sans ``levee_par``, et une exception sur un ``_partage`` ignorée.
    """
    SKILL = "plugins/p/skills/s/SKILL.md"
    AUTRE_SKILL = "plugins/p/skills/t/SKILL.md"
    PARTAGE = "plugins/p/skills/_partage/gros.md"
    CITATION = "Ses compagnons sont les fichiers partagés : `_partage/gros.md`.\n"

    def skill_de(self, taille: int, chemin: str = SKILL) -> None:
        _manifeste(self.racine, "p")
        _ecrire(self.racine / chemin, _texte_de_taille(taille))

    def partage_de(self, taille: int) -> None:
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", corps=self.CITATION)
        _ecrire(self.racine / self.PARTAGE, "x" * taille)

    def exception_sur(self, chemin: str, caracteres: int, **plus) -> dict:
        exc = {"caracteres": caracteres, "date": "2026-11-21",
               "raison": "passif de taille", "levee_par": "étape 7b"}
        exc.update(plus)
        return {"exceptions": {chemin: exc}}

    def refus_q(self, limites=None) -> list:
        return [a for a in self.controler(limites).refus if a.regle == "q"]

    def test_un_skill_de_25001_caracteres_est_refuse_et_nomme(self):
        self.skill_de(25_001)
        refus = self.refus_q()
        self.assertEqual([a.cible for a in refus], [self.SKILL])
        self.assertIn("25 000", refus[0].message)

    def test_un_skill_de_25000_caracteres_passe(self):
        # Vert avant le code : la frontière exacte ne doit pas refuser à tort.
        self.skill_de(25_000)
        self.assertEqual(self.refus_q(), [])

    def test_un_fichier_partage_de_30001_caracteres_est_refuse_et_nomme(self):
        self.partage_de(30_001)
        refus = self.refus_q()
        self.assertEqual([a.cible for a in refus], [self.PARTAGE])
        self.assertIn("30 000", refus[0].message)

    def test_un_fichier_partage_de_30000_caracteres_passe(self):
        # Garde le seuil des _partage distinct de celui des SKILL.md : appliquer 25 000 aux
        # _partage ferait échouer ce test (un fichier de 26 000 à 30 000 est légitime).
        self.partage_de(30_000)
        self.assertEqual(self.refus_q(), [])

    def test_une_exception_couvre_un_skill_jusqu_a_son_plafond(self):
        self.skill_de(30_000)
        res = self.controler(_limites(self.racine,
                                      budget_caracteres=self.exception_sur(self.SKILL, 30_000)))
        self.assertEqual([a for a in res.refus if a.regle == "q"], [])
        excusees = [(a, exc) for a, exc in res.excusees if a.regle == "q"]
        self.assertEqual(len(excusees), 1)
        self.assertEqual(excusees[0][1]["levee_par"], "étape 7b")

    def test_une_exception_couvre_aussi_un_fichier_de_partage(self):
        # Sans ce test, une exception posée sur un _partage (outils-et-quotas.md) serait ignorée.
        self.partage_de(30_500)
        res = self.controler(_limites(self.racine,
                                      budget_caracteres=self.exception_sur(self.PARTAGE, 30_500)))
        self.assertEqual([a for a in res.refus if a.regle == "q"], [])
        self.assertEqual([a.cible for a, _ in res.excusees if a.regle == "q"], [self.PARTAGE])

    def test_une_exception_ne_laisse_pas_grossir_le_fichier_au_dela_de_son_plafond(self):
        self.skill_de(30_001)
        refus = self.refus_q(_limites(self.racine,
                                      budget_caracteres=self.exception_sur(self.SKILL, 30_000)))
        self.assertEqual([a.cible for a in refus], [self.SKILL])

    def test_un_fichier_hors_exception_est_juge_au_seuil_meme_si_un_voisin_est_excepte(self):
        self.skill_de(30_000)
        self.skill_de(25_001, chemin=self.AUTRE_SKILL)
        refus = self.refus_q(_limites(self.racine,
                                      budget_caracteres=self.exception_sur(self.SKILL, 30_000)))
        self.assertEqual([a.cible for a in refus], [self.AUTRE_SKILL])

    def test_une_exception_dont_le_fichier_repasse_sous_le_seuil_est_perimee(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s")
        refus = self.refus_q(_limites(self.racine,
                                      budget_caracteres=self.exception_sur(self.SKILL, 30_000)))
        self.assertEqual(len(refus), 1)
        self.assertIn("périmée", refus[0].message)

    def test_une_exception_sans_levee_par_ne_couvre_rien(self):
        self.skill_de(30_000)
        exc = self.exception_sur(self.SKILL, 30_000)
        del exc["exceptions"][self.SKILL]["levee_par"]
        self.assertIn("q", [a.regle for a in self.controler(
            _limites(self.racine, budget_caracteres=exc)).refus])

    def test_sans_exceptions_le_budget_redevient_bloquant(self):
        # --sans-exceptions doit juger la règle (q) comme les autres : le SKILL de 30 000 caractères
        # que l'exception couvrait doit être refusé au seuil de 25 000, pas excusé.
        self.skill_de(30_000)
        res = self.controler(_limites(self.racine,
                                      budget_caracteres=self.exception_sur(self.SKILL, 30_000)),
                             sans_exceptions=True)
        self.assertEqual([a.cible for a in res.refus if a.regle == "q"], [self.SKILL])
        self.assertEqual([a for a, _ in res.excusees if a.regle == "q"], [])


class CliquetDuBudget(unittest.TestCase):
    """Le cliquet tient les exceptions de la règle (q) : un plafond ne monte pas, une exception
    nouvelle ne s'ajoute pas une fois la table en base, et la table peut se vider (7b)."""
    CHEMIN = "plugins/p/skills/s/SKILL.md"

    def base(self, exceptions):
        return {"budget_caracteres": {"exceptions": exceptions}, "veille_jours_max": 30}

    def exception(self, caracteres):
        return {"caracteres": caracteres, "date": "2026-11-21",
                "raison": "passif", "levee_par": "étape 7b"}

    def test_le_plafond_d_une_exception_ne_monte_pas(self):
        ancien = self.base({self.CHEMIN: self.exception(30_000)})
        nouveau = self.base({self.CHEMIN: self.exception(30_001)})
        anomalies = check_skills.verifier_cliquet(nouveau, ancien)
        self.assertEqual([a.regle for a in anomalies], ["q"])

    def test_une_exception_ajoutee_alors_que_la_base_a_la_table_est_refusee(self):
        ancien = self.base({})
        nouveau = self.base({self.CHEMIN: self.exception(30_000)})
        self.assertEqual([a.regle for a in check_skills.verifier_cliquet(nouveau, ancien)], ["q"])

    def test_la_table_introduite_par_la_pr_est_acceptee(self):
        # Intérim : la base d'avant cette règle n'a pas la table, sa première version passe.
        nouveau = self.base({self.CHEMIN: self.exception(30_000)})
        self.assertEqual(check_skills.verifier_cliquet(nouveau, {"veille_jours_max": 30}), [])

    def test_une_exception_retiree_est_acceptee(self):
        # La sortie de 7b : retirer une exception est le but, il ne doit jamais être refusé.
        ancien = self.base({self.CHEMIN: self.exception(30_000)})
        self.assertEqual(check_skills.verifier_cliquet(self.base({}), ancien), [])

    def test_un_plafond_d_exception_qui_baisse_est_accepte(self):
        ancien = self.base({self.CHEMIN: self.exception(30_000)})
        nouveau = self.base({self.CHEMIN: self.exception(29_000)})
        self.assertEqual(check_skills.verifier_cliquet(nouveau, ancien), [])

    def test_la_cle_budget_retiree_alors_que_la_base_la_porte_est_refusee(self):
        # Sans ce test, une PR retire la clé entière (base avec table, tête sans clé), puis une PR
        # suivante la réintroduit avec une exception neuve : la base n'ayant plus la clé, la
        # « table introduite par la PR » la laisse passer. Retirer la clé doit donc être refusé.
        ancien = self.base({})
        nouveau = {"veille_jours_max": 30}
        self.assertEqual([a.regle for a in check_skills.verifier_cliquet(nouveau, ancien)], ["q"])


class FichierLuEnRoute(Depot):
    """Règle (q), extension : un fichier Markdown qu'un SKILL.md désigne comme à lire (renvoi
    ``📄 `${CLAUDE_PLUGIN_ROOT}/…` ``) tient sous 25 000 octets, sauf exception datée
    (``taille_fichier_lu`` de ``scripts/limites.json``) qui le couvre jusqu'à son plafond.

    Pannes attrapées : un fichier lu de 30 000 octets qui passe sans que personne le voie, un
    seuil mesuré en caractères (14 000 « é » font 28 000 octets), une exception qui laisse grossir
    le fichier, une exception qui survit au passage sous le seuil, une exception sans ``levee_par``,
    une exception qui n'est pas retirée avec ``--sans-exceptions``, et un fichier non Markdown ou
    non désigné jugé à tort.
    """
    LU = "plugins/p/skills/s/lu.md"
    RENVOI = "📄 `${CLAUDE_PLUGIN_ROOT}/skills/s/lu.md` : à lire à la première étape.\n"

    def lu_texte(self, texte: str) -> None:
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", corps=self.RENVOI)
        _ecrire(self.racine / self.LU, texte)

    def lu_de(self, octets: int) -> None:
        self.lu_texte("x" * octets)

    def table_sur(self, chemin: str, plafond: int, **plus) -> dict:
        exc = {"plafond": plafond, "date": "2026-11-23",
               "raison": "lu en route, à découper dans un plan suivant", "levee_par": "plan suivant"}
        exc.update(plus)
        return {"plafond_octets": 25_000, "exceptions": {chemin: exc}}

    def refus_lu(self, limites=None, **kw) -> list:
        return [a for a in self.controler(limites, **kw).refus if a.regle == "q"]

    def test_un_fichier_lu_de_30000_octets_sans_exception_est_refuse_et_nomme(self):
        self.lu_de(30_000)
        refus = self.refus_lu()
        self.assertEqual([a.cible for a in refus], [self.LU])
        self.assertIn("25 000", refus[0].message)

    def test_un_fichier_lu_de_24000_octets_passe(self):
        # Vert avant le code : le seuil ne doit pas refuser un fichier qui y tient.
        self.lu_de(24_000)
        self.assertEqual(self.refus_lu(), [])

    def test_le_seuil_se_mesure_en_octets_et_non_en_caracteres(self):
        # 14 000 « é » : 14 000 caractères, 28 000 octets. Au-dessus du seuil en octets seulement.
        self.lu_texte("é" * 14_000)
        self.assertEqual([a.cible for a in self.refus_lu()], [self.LU])

    def test_une_exception_couvre_un_fichier_lu_jusqu_a_son_plafond(self):
        self.lu_de(30_000)
        res = self.controler(_limites(self.racine, taille_fichier_lu=self.table_sur(self.LU, 30_000)))
        self.assertEqual([a for a in res.refus if a.regle == "q"], [])
        excusees = [(a, exc) for a, exc in res.excusees if a.regle == "q"]
        self.assertEqual([a.cible for a, _ in excusees], [self.LU])
        self.assertEqual(excusees[0][1]["levee_par"], "plan suivant")

    def test_une_exception_ne_laisse_pas_grossir_le_fichier_lu_au_dela_de_son_plafond(self):
        self.lu_de(30_001)
        refus = self.refus_lu(_limites(self.racine, taille_fichier_lu=self.table_sur(self.LU, 30_000)))
        self.assertEqual([a.cible for a in refus], [self.LU])

    def test_une_exception_dont_le_fichier_repasse_sous_le_seuil_est_perimee(self):
        self.lu_de(24_000)
        refus = self.refus_lu(_limites(self.racine, taille_fichier_lu=self.table_sur(self.LU, 30_000)))
        self.assertEqual(len(refus), 1)
        self.assertIn("périmée", refus[0].message)

    def test_une_exception_sans_levee_par_ne_couvre_rien(self):
        self.lu_de(30_000)
        table = self.table_sur(self.LU, 30_000)
        del table["exceptions"][self.LU]["levee_par"]
        refus = self.refus_lu(_limites(self.racine, taille_fichier_lu=table))
        self.assertEqual([a.cible for a in refus], [self.LU])

    def test_sans_exceptions_le_fichier_lu_redevient_bloquant(self):
        self.lu_de(30_000)
        res = self.controler(_limites(self.racine, taille_fichier_lu=self.table_sur(self.LU, 30_000)),
                             sans_exceptions=True)
        self.assertEqual([a.cible for a in res.refus if a.regle == "q"], [self.LU])
        self.assertEqual([a for a, _ in res.excusees if a.regle == "q"], [])

    def test_un_script_designe_par_un_renvoi_est_ignore(self):
        # Un .py désigné n'est pas du texte lu en route : la règle ne le mesure pas.
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s", corps="📄 `${CLAUDE_PLUGIN_ROOT}/skills/s/outil.py`\n")
        _ecrire(self.racine / "plugins/p/skills/s/outil.py", "x" * 30_000)
        self.assertEqual(self.refus_lu(), [])

    def test_un_fichier_de_plugin_non_designe_n_est_pas_juge(self):
        _manifeste(self.racine, "p")
        _skill(self.racine, "p", "s")
        _ecrire(self.racine / "plugins/p/skills/s/orphelin.md", "x" * 30_000)
        self.assertEqual(self.refus_lu(), [])

    def test_le_depot_reel_respecte_la_regle_des_fichiers_lus(self):
        racine = Path(__file__).resolve().parents[1]
        limites = json.loads((racine / "scripts" / "limites.json").read_text("utf-8"))
        res = check_skills.controler(racine, limites)
        self.assertEqual([a for a in res.refus if a.regle == "q"], [])


class CliquetFichierLu(unittest.TestCase):
    """Le cliquet tient la règle des fichiers lus : le plafond par défaut ne monte pas, le plafond
    d'une exception ne monte pas, une exception neuve ne s'ajoute pas une fois la table en base,
    et la clé ne disparaît pas."""
    CHEMIN = "plugins/p/skills/s/lu.md"

    def base(self, plafond_octets=25_000, exceptions=None):
        return {"taille_fichier_lu": {"plafond_octets": plafond_octets,
                                      "exceptions": exceptions or {}},
                "veille_jours_max": 30}

    def exception(self, plafond):
        return {"plafond": plafond, "date": "2026-11-23", "raison": "lu en route",
                "levee_par": "plan suivant"}

    def test_le_plafond_par_defaut_ne_monte_pas(self):
        anomalies = check_skills.verifier_cliquet(self.base(plafond_octets=26_000), self.base())
        self.assertEqual([a.regle for a in anomalies], ["q"])

    def test_le_plafond_d_une_exception_ne_monte_pas(self):
        ancien = self.base(exceptions={self.CHEMIN: self.exception(31_000)})
        nouveau = self.base(exceptions={self.CHEMIN: self.exception(31_001)})
        self.assertEqual([a.regle for a in check_skills.verifier_cliquet(nouveau, ancien)], ["q"])

    def test_une_exception_ajoutee_alors_que_la_base_a_la_table_est_refusee(self):
        nouveau = self.base(exceptions={self.CHEMIN: self.exception(31_000)})
        self.assertEqual([a.regle for a in check_skills.verifier_cliquet(nouveau, self.base())], ["q"])

    def test_la_table_introduite_par_la_pr_est_acceptee(self):
        # Intérim : la base d'avant cette règle n'a pas la clé, sa première version passe.
        nouveau = self.base(exceptions={self.CHEMIN: self.exception(31_000)})
        self.assertEqual(check_skills.verifier_cliquet(nouveau, {"veille_jours_max": 30}), [])

    def test_une_exception_retiree_et_une_baisse_de_plafond_sont_acceptees(self):
        ancien = self.base(exceptions={self.CHEMIN: self.exception(31_000)})
        self.assertEqual(check_skills.verifier_cliquet(self.base(), ancien), [])
        moins = self.base(exceptions={self.CHEMIN: self.exception(30_000)})
        self.assertEqual(check_skills.verifier_cliquet(moins, ancien), [])

    def test_la_cle_retiree_alors_que_la_base_la_porte_est_refusee(self):
        # Retirer la clé relèverait la table à l'infini, comme pour budget_caracteres.
        self.assertEqual([a.regle for a in check_skills.verifier_cliquet(
            {"veille_jours_max": 30}, self.base())], ["q"])


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
