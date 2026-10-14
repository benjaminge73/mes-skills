"""Tests de ``verifier-preuves.py`` : une panne nommée, un test.

Les pages sont des chaînes écrites dans chaque test (pas de fixture sur disque) :
le format « Questions ouvertes » et « Décisions » tient en quelques lignes, et
c'est ce format qui est testé. Le script tourne en sous-processus, comme
``test_compter_cases.py``, et l'on observe sa sortie et son code retour.

Le modèle servi, lui, vient d'une transcription synthétique fabriquée dans le
test (``<racine>/projects/-home-x/sess-1/subagents/agent-<id>.jsonl``) : le script
appelle ``modele-sous-agent.py`` en vrai sous-processus, il n'est pas simulé.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "verifier-preuves.py"

AGENT_ID = "9f8e7d6c5b4a"
ENTETE = "# Plan de test\n\n## Cartes\n\n- une carte\n\n## Questions ouvertes\n\n"


def jouer(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def plan(*blocs):
    return ENTETE + "".join(blocs)


def question(n, *lignes, icone="✅"):
    corps = "".join(f"{ligne}\n" for ligne in lignes)
    return f"### {icone} Q{n} — Une question\n\n- [x] la réponse retenue\n{corps}\n"


def poc(modele="claude-haiku-5-5", agent="plans-notion:sondeur", agent_id=AGENT_ID):
    return f"Preuve : POC — agent {agent} · {agent_id} · {modele} (résultat en une phrase)"


class VerifierPreuves(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)

    def ecrire(self, nom, texte):
        f = self.dossier / nom
        f.write_text(texte, encoding="utf-8")
        return f

    def transcription(self, modele):
        # Forme de modele-sous-agent.py : <racine>/projects/<projet>/<session>/subagents/agent-<id>.jsonl
        racine = self.dossier / "claude"
        sub = racine / "projects" / "-home-x" / "sess-1" / "subagents"
        sub.mkdir(parents=True, exist_ok=True)
        ligne = json.dumps({"type": "assistant",
                            "message": {"role": "assistant", "content": "x", "model": modele}})
        (sub / f"agent-{AGENT_ID}.jsonl").write_text(ligne + "\n", encoding="utf-8")
        return racine

    # Pannes, une par test.

    def test_une_reponse_tranchee_sans_preuve_est_refusee(self):
        p = self.ecrire("p.md", plan(question(1)))
        code, sortie, _ = jouer(p)
        self.assertEqual(code, 1, sortie)
        self.assertIn("Q1", sortie)
        self.assertIn("sans ligne Preuve", sortie)

    def test_une_dispense_sans_raison_est_refusee(self):
        p = self.ecrire("p.md", plan(question(1, "Preuve : dispense — préférence de style")))
        code, sortie, _ = jouer(p)
        self.assertEqual(code, 1, sortie)
        self.assertIn("Q1", sortie)
        self.assertIn("dispense sans raison", sortie)

    def test_un_poc_sans_agent_id_est_refuse(self):
        # Le deuxième champ du POC n'est pas un jeton hexadécimal : l'agentId manque.
        p = self.ecrire("p.md", plan(question(
            1, "Preuve : POC — agent plans-notion:sondeur · (sans id) · claude-haiku-5-5 (résultat)")))
        code, sortie, _ = jouer(p)
        self.assertEqual(code, 1, sortie)
        self.assertIn("sans agentId", sortie)

    def test_un_poc_servi_par_opus_est_refuse(self):
        racine = self.transcription("claude-opus-5-5")
        p = self.ecrire("p.md", plan(question(1, poc(modele="claude-opus-5-5"))))
        code, sortie, _ = jouer(p, "--transcripts", racine)
        self.assertEqual(code, 1, sortie)
        self.assertIn("Opus", sortie)

    def test_un_modele_cite_different_du_servi_est_refuse(self):
        # Cité Sonnet, servi Haiku : aucun des deux ne contient l'autre.
        racine = self.transcription("claude-haiku-5-5")
        p = self.ecrire("p.md", plan(question(1, poc(modele="claude-sonnet-5-5"))))
        code, sortie, _ = jouer(p, "--transcripts", racine)
        self.assertEqual(code, 1, sortie)
        self.assertIn("différent", sortie)

    def test_une_lecture_vers_un_fichier_absent_est_refusee(self):
        depot = self.dossier / "depot"
        depot.mkdir()
        p = self.ecrire("p.md", plan(question(1, "Preuve : lecture — _partage/absent.md:12 (la règle)")))
        code, sortie, _ = jouer(p, "--depot", depot)
        self.assertEqual(code, 1, sortie)
        self.assertIn("introuvable", sortie)
        self.assertIn("_partage/absent.md", sortie)

    def test_une_question_ouverte_n_est_pas_controlee(self):
        p = self.ecrire("p.md", plan(
            question(1, "Preuve : dispense — parce que préférence de style"),
            question(2, icone="🧭")))
        code, sortie, _ = jouer(p)
        self.assertEqual(code, 0, sortie)
        self.assertIn("1 réponse(s)", sortie)

    def test_un_plan_natif_sans_preuve_est_refuse_et_un_conforme_passe(self):
        natif = ("# Plan\n\n## Décisions\n\n"
                 "- D1 — on garde la forme A\n"
                 "- D2 — on écarte B · Preuve : dispense — parce que choix de forme\n")
        p = self.ecrire("n.md", natif)
        code, sortie, _ = jouer(p, "--format", "natif")
        self.assertEqual(code, 1, sortie)
        self.assertIn("D1", sortie)
        self.assertNotIn("D2", sortie)

        conforme = ("# Plan\n\n## Décisions\n\n"
                    "- D1 — on garde A · Preuve : dispense — parce que choix de forme\n")
        p2 = self.ecrire("c.md", conforme)
        code2, sortie2, _ = jouer(p2, "--format", "natif")
        self.assertEqual(code2, 0, sortie2)

    def test_une_page_illisible_rend_deux(self):
        code, _, erreur = jouer(self.dossier / "absent.md")
        self.assertEqual(code, 2, erreur)
        self.assertIn("illisible", erreur)

        sans_section = self.ecrire("sans.md", "# Plan\n\n## Cartes\n\n- rien\n")
        code, _, erreur = jouer(sans_section)
        self.assertEqual(code, 2, erreur)
        self.assertIn("Questions ouvertes", erreur)

    # Cas conformes : le script ne doit pas rendre 1 à tout.

    def test_les_quatre_types_valides_rendent_zero(self):
        p = self.ecrire("p.md", plan(
            question(1, poc()),
            question(2, "Preuve : `commande` — `ls` → 3 fichiers"),
            question(3, "Preuve : lecture — plans/x.md:3 (le passage)"),
            question(4, "Preuve : dispense — parce que préférence de style")))
        code, sortie, _ = jouer(p)
        self.assertEqual(code, 0, sortie)
        self.assertIn("4 réponse(s)", sortie)

    def test_poc_du_sondeur_servi_en_haiku_rend_zero(self):
        racine = self.transcription("claude-haiku-5-5")
        p = self.ecrire("p.md", plan(question(1, poc())))
        code, sortie, _ = jouer(p, "--transcripts", racine)
        self.assertEqual(code, 0, sortie)

    def test_lecture_dont_le_fichier_existe_par_suffixe_rend_zero(self):
        # « _partage/poc.md » n'existe pas à la racine du dépôt : il en est le suffixe.
        depot = self.dossier / "depot"
        (depot / "plugins" / "plans-notion" / "skills" / "_partage").mkdir(parents=True)
        (depot / "plugins" / "plans-notion" / "skills" / "_partage" / "poc.md").write_text("x\n", encoding="utf-8")
        p = self.ecrire("p.md", plan(question(1, "Preuve : lecture — _partage/poc.md:226 (la section)")))
        code, sortie, _ = jouer(p, "--depot", depot)
        self.assertEqual(code, 0, sortie)

    def test_poc_d_un_general_purpose_est_refuse(self):
        # Un agent non nommé tourne sur le modèle de la session : pas un POC valide.
        p = self.ecrire("p.md", plan(question(1, poc(agent="general-purpose"))))
        code, sortie, _ = jouer(p)
        self.assertEqual(code, 1, sortie)
        self.assertIn("POC sans agent nommé valide", sortie)

    # Test en plus, hors liste de la brief. Il attrape une autre panne : le contrôle
    # de lecture qui cherche une URL ou un chemin « ~ » dans le dépôt et rend
    # « fichier introuvable » pour une doc externe, ce qui rejetterait une preuve valide.
    def test_une_lecture_externe_n_est_pas_cherchee_dans_le_depot(self):
        depot = self.dossier / "depot"
        depot.mkdir()
        p = self.ecrire("p.md", plan(
            question(1, "Preuve : lecture — https://code.claude.com/docs/en/skills.md:12 (la consigne)"),
            question(2, "Preuve : lecture — ~/.claude/rules/x.md:3 (la règle)")))
        code, sortie, _ = jouer(p, "--depot", depot)
        self.assertEqual(code, 0, sortie)

    # Revue de la page réelle (étape 5) : quatre pannes, un test par panne.

    def test_une_prose_qui_cite_la_forme_preuve_n_est_pas_une_ligne_de_preuve(self):
        # La prose qui cite « Preuve : POC » au milieu d'une phrase n'est pas une ligne
        # de preuve : seule une ligne qui commence par « Preuve : » en est une.
        depot = self.dossier / "depot"
        (depot / "plans").mkdir(parents=True)
        (depot / "plans" / "x.md").write_text("x\n", encoding="utf-8")
        prose = "**Forme citée** : une `Preuve : POC` cite l'identifiant de l'agent, sans le prouver."
        p = self.ecrire("p.md", plan(question(1, prose, "Preuve : lecture — plans/x.md:1 (le passage)")))
        code, sortie, _ = jouer(p, "--depot", depot)
        self.assertEqual(code, 0, sortie)

    def test_dispense_avec_elision_de_parce_que(self):
        # « parce qu'aucun » (élision) vaut « parce que » suivi d'un mot, avec l'apostrophe
        # droite comme avec l'apostrophe typographique.
        for apostrophe in ("'", "’"):
            with self.subTest(apostrophe=apostrophe):
                p = self.ecrire("p.md", plan(question(
                    1, f"Preuve : dispense — parce qu{apostrophe}aucun comportement n{apostrophe}est mesurable")))
                code, sortie, _ = jouer(p)
                self.assertEqual(code, 0, sortie)

    def test_lecture_externe_sans_numero_de_ligne(self):
        # Un chemin externe (domaine, « ~ ») se passe de « :ligne ». Le contre-test : un
        # chemin interne sans « :ligne » reste refusé, pour la même raison d'écart.
        p = self.ecrire("p.md", plan(
            question(1, "Preuve : lecture — code.claude.com/docs/en/sub-agents.md "
                        "(sans modèle à l'appel, le sous-agent prend celui de la session)"),
            question(2, "Preuve : lecture — ~/.hermes/hermes-agent/website/docs/x.md (ce que dit le passage)")))
        code, sortie, _ = jouer(p, "--depot", self.dossier)
        self.assertEqual(code, 0, sortie)

        depot = self.dossier / "depot"
        depot.mkdir()
        interne = self.ecrire("i.md", plan(question(1, "Preuve : lecture — plans/x.md (le passage)")))
        code2, sortie2, _ = jouer(interne, "--depot", depot)
        self.assertEqual(code2, 1, sortie2)
        self.assertIn("sans chemin:ligne", sortie2)

    def test_un_poc_servi_par_deux_modeles_est_refuse(self):
        # Transcription mêlant deux modèles servis : tout modèle servi doit correspondre
        # au modèle cité, pas un seul. Le modèle qui diffère doit être nommé.
        racine = self.dossier / "claude"
        sub = racine / "projects" / "-home-x" / "sess-1" / "subagents"
        sub.mkdir(parents=True)
        lignes = [json.dumps({"type": "assistant",
                              "message": {"role": "assistant", "content": "x", "model": m}})
                  for m in ("claude-haiku-5-5", "claude-sonnet-5-5")]
        (sub / f"agent-{AGENT_ID}.jsonl").write_text("\n".join(lignes) + "\n", encoding="utf-8")
        p = self.ecrire("p.md", plan(question(1, poc(modele="claude-haiku-5-5"))))
        code, sortie, _ = jouer(p, "--transcripts", racine)
        self.assertEqual(code, 1, sortie)
        self.assertIn("différent", sortie)
        self.assertIn("claude-sonnet-5-5", sortie)

    # Revue 2 : « :// » et « hors dépôt » ne comptent que dans le jeton du chemin ou avant
    # lui, jamais dans le détail qui le suit. Le dépôt est fourni pour que le chemin
    # interne soit réellement cherché (sans --depot, tout chemin passe).

    def test_lecture_interne_absente_avec_url_dans_le_detail_est_refusee(self):
        # Panne : une URL dans le détail faisait passer pour externe un chemin interne absent.
        p = self.ecrire("p.md", plan(question(
            1, "Preuve : lecture — plans/absent.md:3 (voir https://exemple.org)")))
        code, sortie, _ = jouer(p, "--depot", RACINE)
        self.assertEqual(code, 1, sortie)
        self.assertIn("introuvable", sortie)

    def test_lecture_interne_absente_avec_hors_depot_apres_le_chemin_est_refusee(self):
        # Panne : « hors dépôt » placé après le chemin rendait le chemin interne absent conforme.
        depot = self.dossier / "depot"
        depot.mkdir()
        p = self.ecrire("p.md", plan(question(
            1, "Preuve : lecture — plans/absent.md:3 — confirmé, rien hors dépôt")))
        code, sortie, _ = jouer(p, "--depot", depot)
        self.assertEqual(code, 1, sortie)
        self.assertIn("introuvable", sortie)

    def test_hors_depot_avant_le_chemin_est_accepte(self):
        # Garde : « hors dépôt » avant le chemin reste le marqueur valide. Le dépôt vide
        # rend l'essai discriminant : sans le marqueur, cron.md serait introuvable.
        depot = self.dossier / "depot"
        depot.mkdir()
        p = self.ecrire("p.md", plan(question(
            1, "Preuve : lecture — hors dépôt — cron.md:925 (ce que dit le passage)")))
        code, sortie, _ = jouer(p, "--depot", depot)
        self.assertEqual(code, 0, sortie)

    def test_schema_dans_le_chemin_reste_externe_et_accepte(self):
        # Garde : un schéma qui fait partie du jeton du chemin rend le chemin externe.
        depot = self.dossier / "depot"
        depot.mkdir()
        p = self.ecrire("p.md", plan(question(
            1, "Preuve : lecture — https://code.claude.com/docs/en/x.md (ce que dit le passage)")))
        code, sortie, _ = jouer(p, "--depot", depot)
        self.assertEqual(code, 0, sortie)


if __name__ == "__main__":
    unittest.main()
