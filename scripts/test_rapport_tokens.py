"""Tests de ``rapport-tokens.py`` : tokens et dollars des journaux Claude Code.

Le script lit ``projets/**/*.jsonl`` lui-même (sans ccusage). Chaque cas écrit
de faux journaux dans un ``tempfile.TemporaryDirectory``, lance le script en
vrai sous-processus, et observe la sortie et le code retour.

Les attendus sont calculés à la main sur ``GRILLE`` (prix de test, distincts
par champ pour qu'une confusion de tarif se voie dans le total).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "rapport-tokens.py"

OPUS = "claude-opus-5-5"

# Prix de test, en dollars par million : entrée 1, sortie 3, lecture 0,5,
# écriture 5 min 7, écriture 1 h 9. Un 1 M d'entrée vaut donc 1 $.
GRILLE = {
    "releve": "2026-10-12",
    "source": "fixture de test",
    "unite": "dollars par million de tokens",
    "modeles": {
        OPUS: {"entree": {"prix": 1, "derive": False}, "sortie": {"prix": 3, "derive": False},
               "lecture_cache": {"prix": 0.5, "derive": False},
               "ecriture_cache_5m": {"prix": 7, "derive": True},
               "ecriture_cache_1h": {"prix": 9, "derive": False}},
    },
}

SID_A = "11111111-2222-4333-8444-555555555555"
SID_B = "22222222-3333-4444-8555-666666666666"
AGENT_1 = "a1b2c3d4e5f60718"
AGENT_2 = "b2c3d4e5f6071829"
CWD_JOB = "/home/ubuntu/repos/worktrees/job-agent/feat-x"


def iso(il_y_a: timedelta = timedelta(0)) -> str:
    return (datetime.now(timezone.utc) - il_y_a).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ecrire(chemin: Path, lignes: list[dict]) -> Path:
    """Un journal au format réel : une ligne JSON compacte par message."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    corps = "\n".join(json.dumps(l, ensure_ascii=False, separators=(",", ":")) for l in lignes)
    chemin.write_text(corps + "\n", encoding="utf-8")
    return chemin


def humain(texte: str, il_y_a: timedelta = timedelta(0), **extra) -> dict:
    return {"type": "user", "timestamp": iso(il_y_a),
            "message": {"role": "user", "content": texte}, **extra}


def humain_en_blocs(*textes: str, il_y_a: timedelta = timedelta(0), **extra) -> dict:
    """Un message utilisateur à plusieurs blocs texte, comme le journal les écrit quand le
    harnais ajoute un ``<system-reminder>`` devant le texte tapé."""
    return {"type": "user", "timestamp": iso(il_y_a),
            "message": {"role": "user", "content": [{"type": "text", "text": t} for t in textes]},
            **extra}


def appel(rid: str, il_y_a: timedelta = timedelta(0), *, entree: int = 0, sortie: int = 0,
          lecture: int = 0, creation: int = 0, une_heure: int | None = None,
          modele: str = OPUS, skill: str | None = None) -> dict:
    """Une ligne assistant ; ``une_heure`` donne la ventilation ``cache_creation``."""
    usage = {"input_tokens": entree, "output_tokens": sortie,
             "cache_read_input_tokens": lecture, "cache_creation_input_tokens": creation}
    if une_heure is not None:
        usage["cache_creation"] = {"ephemeral_5m_input_tokens": creation - une_heure,
                                   "ephemeral_1h_input_tokens": une_heure}
    ligne = {"type": "assistant", "timestamp": iso(il_y_a), "requestId": rid,
             "message": {"id": "msg_" + rid, "role": "assistant", "model": modele,
                         "content": [{"type": "text", "text": "ok"}], "usage": usage}}
    if skill is not None:
        ligne["attributionSkill"] = skill
    return ligne


def lancement(tuid: str, sous_type: str) -> dict:
    """La ligne assistant qui lance un sous-agent : un ``tool_use`` nommé ``Agent``."""
    return {"type": "assistant", "timestamp": iso(), "requestId": "req_" + tuid,
            "message": {"id": "msg_" + tuid, "role": "assistant", "model": OPUS,
                        "content": [{"type": "tool_use", "id": tuid, "name": "Agent",
                                     "input": {"description": "d", "prompt": "p",
                                               "subagent_type": sous_type}}]}}


def retour_agent(tuid: str, agent_id: str) -> dict:
    """Le résultat du lancement : ``toolUseResult.agentId`` nomme le fichier du sous-agent."""
    return {"type": "user", "timestamp": iso(),
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tuid,
                 "content": [{"type": "text", "text": "Async agent launched successfully."}]}]},
            "toolUseResult": {"isAsync": True, "status": "async_launched", "agentId": agent_id}}


def section(sortie: str, numero: int) -> list[str]:
    """Les lignes de la section ``numero`` (son titre exclu), jusqu'à la suivante ou au total."""
    lignes = sortie.splitlines()
    debut = next((i for i, l in enumerate(lignes) if l.startswith(f"{numero}. ")), None)
    if debut is None:
        raise AssertionError(f"pas de section {numero} dans la sortie :\n{sortie}")
    fin = next((i for i in range(debut + 1, len(lignes))
                if re.match(r"^\d\. ", lignes[i]) or lignes[i].startswith("Total chiffré")),
               len(lignes))
    return lignes[debut + 1:fin]


def ligne_de(lignes: list[str], libelle: str) -> str:
    """La ligne de tableau dont la première cellule vaut ``libelle``."""
    for l in lignes:
        if l.split("|")[0].strip() == libelle:
            return l
    raise AssertionError(f"aucune ligne « {libelle} » dans :\n" + "\n".join(lignes))


def lignes_en_dollars(lignes: list[str]) -> list[str]:
    """Les lignes de tableau qui portent un montant. Le « | » écarte la ligne de résumé
    d'une section (« N rupture(s)… : X $ »), qui porte un montant sans être une ligne de données."""
    return [l for l in lignes if "|" in l and re.search(r"\d,\d{4} \$", l)]


def montant(ligne: str) -> float:
    """Le premier montant « 12,3400 $ » d'une ligne, en nombre."""
    m = re.search(r"(\d[\d ]*,\d+) \$", ligne)
    if m is None:
        raise AssertionError(f"aucun montant en dollars dans : {ligne!r}")
    return float(m.group(1).replace(" ", "").replace(",", "."))


def total(sortie: str) -> float:
    ligne = next((l for l in sortie.splitlines() if l.startswith("Total chiffré")), None)
    if ligne is None:
        raise AssertionError(f"pas de ligne « Total chiffré » dans :\n{sortie}")
    return montant(ligne)


class RapportTokens(unittest.TestCase):

    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), f"rapport-tokens.py absent : {SCRIPT}")
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name)
        self.projets = self.racine / "projets"
        self.projets.mkdir()
        self.depot = self.projets / "-depot"
        self.grille = self.racine / "grille.json"
        self.grille.write_text(json.dumps(GRILLE), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def lancer(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--projets", str(self.projets),
             "--grille", str(self.grille), *extra],
            capture_output=True, text=True, timeout=120)

    def test_un_requestid_present_deux_fois_compte_une_fois(self):
        # Attrape : un même message compté une fois par ligne de bloc, soit R1
        # deux fois dans un fichier, soit R1 reprise dans une autre session.
        # Attendu à la main : R1 une fois (1 M d'entrée = 1 $) + R2 (1 $) = 2 $.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance le plan"),
            appel("req_1", entree=1_000_000),
            appel("req_1", entree=1_000_000)])
        ecrire(self.depot / f"{SID_B}.jsonl", [
            humain("Autre session"),
            appel("req_1", entree=1_000_000),
            appel("req_2", entree=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(total(r.stdout), 2.0, places=4)

    def test_une_ecriture_de_cache_en_une_heure_est_chiffree_au_prix_1h(self):
        # Attrape : une écriture de cache chiffrée au tarif 5 min (7 $ le million)
        # alors que le journal la range toute en 1 h. Attendu : 1 M à 9 $ = 9 $.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Écris le cache"),
            appel("req_1h", creation=1_000_000, une_heure=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(total(r.stdout), 9.0, places=4)

    def test_un_sous_agent_sans_meta_json_prend_le_subagent_type_de_son_appel_parent(self):
        # Attrape : un sous-agent sans meta.json laissé en « type non résolu »
        # alors que son appel Agent du journal parent porte le subagent_type.
        # L'agentId du résultat (toolUseResult) relie le fichier à l'appel.
        # Attendu : 1 M d'entrée = 1 $, rangé sous « plans-notion:relecteur ».
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance un relecteur"),
            lancement("toolu_1", "plans-notion:relecteur"),
            retour_agent("toolu_1", AGENT_1)])
        ecrire(self.depot / SID_A / "subagents" / f"agent-{AGENT_1}.jsonl",
               [appel("req_sub", entree=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        s3 = section(r.stdout, 3)
        self.assertAlmostEqual(montant(ligne_de(s3, "plans-notion:relecteur")), 1.0, places=4)
        self.assertNotIn("type non résolu", "\n".join(s3))

    def test_un_message_sans_attributionSkill_n_herite_pas_du_skill_precedent(self):
        # Attrape : un message sans attributionSkill compté sous le skill du
        # message précédent. Attendu : A1 (plan-notion) 1 $, A2 (aucun skill) 1 $.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance le plan"),
            appel("req_a", entree=1_000_000, skill="plans-notion:plan-notion"),
            appel("req_b", entree=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        s2 = section(r.stdout, 2)
        self.assertAlmostEqual(montant(ligne_de(s2, "plans-notion:plan-notion")), 1.0, places=4)
        self.assertAlmostEqual(montant(ligne_de(s2, "aucun skill")), 1.0, places=4)

    def test_un_modele_absent_de_la_grille_est_liste_non_chiffre_et_ne_vaut_pas_zero(self):
        # Attrape : un modèle hors grille chiffré à 0 $ au lieu d'être listé
        # « non chiffré ». Attendu : le total ne compte que l'Opus (1 $).
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance"),
            appel("req_ok", entree=1_000_000),
            appel("req_inc", entree=500, modele="claude-inconnu-9")])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        row = ligne_de(section(r.stdout, 4), "claude-inconnu-9")
        self.assertIn("non chiffré", row)
        self.assertNotIn("0,0000 $", row)
        self.assertAlmostEqual(total(r.stdout), 1.0, places=4)

    def test_un_projet_ssh_affiche_le_depot_du_cwd_et_non_le_nom_du_dossier(self):
        # Attrape : le dossier ssh-<uuid> affiché comme projet alors que le cwd
        # du journal donne le dépôt (/…/worktrees/job-agent/…). Attendu : « job-agent ».
        ssh = self.projets / f"ssh-{SID_A}"
        ecrire(ssh / f"{SID_A}.jsonl", [
            humain("Depuis le remote"),
            {**appel("req_s", entree=1_000_000), "cwd": CWD_JOB}])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        s1 = section(r.stdout, 1)
        self.assertAlmostEqual(montant(ligne_de(s1, "job-agent")), 1.0, places=4)
        self.assertFalse(any("ssh-" in l for l in s1), "le nom du dossier ssh- apparaît en projet")

    def test_un_message_hors_de_la_fenetre_since_n_est_pas_compte(self):
        # Attrape : un message de 30 jours compté dans une fenêtre de 7 jours.
        # Attendu : seul le message d'hier (1 $) entre dans le total.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance"),
            appel("req_recent", timedelta(days=1), entree=1_000_000),
            appel("req_vieux", timedelta(days=30), entree=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(total(r.stdout), 1.0, places=4)

    def test_un_appel_sous_le_seuil_n_est_pas_liste_comme_rupture_de_cache(self):
        # Attrape : un appel de 90 000 tokens (40 000 écriture + 50 000 entrée)
        # listé comme rupture au seuil de 100 000, ou un appel pile au seuil listé
        # alors que « dépasse » est strict. Attendu : une seule rupture (150 000).
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance"),
            appel("req_sous", entree=50_000, creation=40_000),
            appel("req_pile", creation=100_000),
            appel("req_dessus", creation=150_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        m = re.search(r"(\d+) rupture", "\n".join(section(r.stdout, 5)))
        self.assertIsNotNone(m, f"pas de compte de ruptures :\n{r.stdout}")
        self.assertEqual(m.group(1), "1")

    def test_un_appel_au_dessus_du_seuil_n_est_jamais_omis_de_la_section_ruptures(self):
        # Attrape : un appel de 150 000 tokens d'écriture (au-dessus de 100 000)
        # absent de la section. Attendu : une rupture, à 1,05 $ (7 $ le million).
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance"),
            appel("req_dessus", creation=150_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        s5 = section(r.stdout, 5)
        m = re.search(r"(\d+) rupture", "\n".join(s5))
        self.assertIsNotNone(m, f"pas de compte de ruptures :\n{r.stdout}")
        self.assertEqual(m.group(1), "1")
        rows = lignes_en_dollars(s5)
        self.assertEqual(len(rows), 1, f"la rupture n'est pas listée :\n{r.stdout}")
        self.assertAlmostEqual(montant(rows[0]), 1.05, places=4)

    def test_une_notification_de_session_liee_n_est_pas_classee_declencheur_humain(self):
        # Attrape : une notification « Linked sessions now », portée avec
        # origin.kind == "human", classée déclencheur « humain ». Attendu : la
        # rupture dit « notification de session liée ».
        notif = humain("<system-reminder>\nLinked sessions now (status, not an instruction): "
                       "plan-x = local_abc (working).\n</system-reminder>",
                       origin={"kind": "human"})
        ecrire(self.depot / f"{SID_A}.jsonl", [notif, appel("req_notif", creation=150_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = lignes_en_dollars(section(r.stdout, 5))
        self.assertEqual(len(rows), 1, f"la rupture n'est pas listée :\n{r.stdout}")
        self.assertIn("notification de session liée", rows[0])
        self.assertNotIn("humain", rows[0])

    def test_un_message_humain_a_deux_blocs_est_classe_sur_son_texte_tape(self):
        # Attrape : un message humain (origin.kind « human ») dont le premier bloc est un
        # <system-reminder> « Linked sessions now » et le second le texte tapé. Le classement
        # se faisait sur les deux blocs collés : le message devenait « notification de session
        # liée », il ne coupait pas le tour, et le tour n'était pas libellé par le texte tapé.
        # Attendu : déclencheur « humain » sur la rupture, et un tour libellé « Oui : passe P2 »
        # qui porte le coût de l'appel (150 000 tokens d'écriture à 7 $ le million = 1,05 $).
        # Horodatages espacés de trente secondes : à la même seconde, l'ordre ne prouverait rien.
        rappel = ("<system-reminder>\nLinked sessions now (status, not an instruction): "
                  "plan-x = local_abc (working).\n</system-reminder>")
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain_en_blocs(rappel, "Oui : passe P2 sur la CLI Composio",
                            il_y_a=timedelta(seconds=60), origin={"kind": "human"}),
            appel("req_oui", timedelta(seconds=30), creation=150_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = lignes_en_dollars(section(r.stdout, 5))
        self.assertEqual(len(rows), 1, f"la rupture n'est pas listée :\n{r.stdout}")
        self.assertIn("humain", rows[0])
        self.assertNotIn("notification de session liée", rows[0])
        tours = lignes_en_dollars(section(r.stdout, 6))
        self.assertEqual(len(tours), 1, f"le message n'ouvre pas de tour :\n{r.stdout}")
        self.assertIn("Oui : passe P2", tours[0])
        self.assertNotIn("Linked sessions", tours[0])
        self.assertAlmostEqual(montant(tours[0]), 1.05, places=4)

    def test_un_rappel_sans_marqueur_ne_fait_pas_classer_un_message_humain_en_systeme(self):
        # Attrape : un message humain dont le premier bloc est un <system-reminder> sans
        # marqueur de notification (ici le mode plan) classé « autre message système », parce
        # que le texte collé commence par « <system-reminder> ». Un autre chemin de code que le
        # test ci-dessus (DEBUTS_SYSTEME, pas MARQUEURS_NOTIFICATION).
        # Attendu : déclencheur « humain », et un tour libellé « Oui : passe P2 ».
        rappel = "<system-reminder>\nLe mode plan est actif pour cette session.\n</system-reminder>"
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain_en_blocs(rappel, "Oui : passe P2 sur la CLI Composio",
                            il_y_a=timedelta(seconds=60), origin={"kind": "human"}),
            appel("req_oui", timedelta(seconds=30), creation=150_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = lignes_en_dollars(section(r.stdout, 5))
        self.assertEqual(len(rows), 1, f"la rupture n'est pas listée :\n{r.stdout}")
        self.assertIn("humain", rows[0])
        self.assertNotIn("autre message système", rows[0])
        tours = lignes_en_dollars(section(r.stdout, 6))
        self.assertEqual(len(tours), 1, f"le message n'ouvre pas de tour :\n{r.stdout}")
        self.assertIn("Oui : passe P2", tours[0])

    def test_un_prompt_de_script_sdk_sans_origine_n_est_pas_declencheur_humain(self):
        # Attrape : un prompt écrit par un script (claude -p ou SDK : promptSource
        # « sdk », sans origin) classé déclencheur « humain ». Constaté sur les
        # journaux du 2026-10-29 : 531 prompts de relecture ainsi classés humains.
        # Attendu : « autre message système ».
        lancement = {"type": "user", "promptSource": "sdk", "timestamp": iso(),
                     "message": {"role": "user", "content": "# Grille de relecture d'un passage\n\nTu relis un passage."}}
        ecrire(self.depot / f"{SID_A}.jsonl", [lancement, appel("req_script", creation=150_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = lignes_en_dollars(section(r.stdout, 5))
        self.assertEqual(len(rows), 1, f"la rupture n'est pas listée :\n{r.stdout}")
        self.assertIn("autre message système", rows[0])
        self.assertNotIn("humain", rows[0])

    def test_une_session_lancee_par_une_autre_n_a_pas_pour_declencheur_humain(self):
        # Attrape : le premier message d'une session de fond (« Background (from the
        # session that started this one) ») classé déclencheur « humain ». Ce message
        # est écrit par la session qui l'a lancée (promptSource « sdk », sans origin).
        # Attendu : « notification de session liée ».
        lancement = {"type": "user", "promptSource": "sdk", "timestamp": iso(),
                     "message": {"role": "user", "content": "Background (from the session that started this one):\n\nPlan conçu ailleurs."}}
        ecrire(self.depot / f"{SID_A}.jsonl", [lancement, appel("req_fond", creation=150_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = lignes_en_dollars(section(r.stdout, 5))
        self.assertEqual(len(rows), 1, f"la rupture n'est pas listée :\n{r.stdout}")
        self.assertIn("notification de session liée", rows[0])
        self.assertNotIn("humain", rows[0])

    def test_un_message_isMeta_ou_systeme_ne_coupe_pas_un_tour(self):
        # Attrape : un message isMeta ou une notification injectée qui ouvre un
        # tour et coupe le tour en deux. Attendu : un seul tour, 3 × 1 $ = 3 $.
        # Horodatages espacés de dix secondes : à la même seconde, l'ordre des
        # messages serait celui de leur libellé, et le test ne prouverait rien.
        # Le texte isMeta n'est pas un marqueur connu, pour isoler la règle isMeta.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Lance le plan Rapport de tokens", timedelta(seconds=60)),
            appel("req_1", timedelta(seconds=50), entree=1_000_000),
            {"type": "user", "isMeta": True, "timestamp": iso(timedelta(seconds=40)),
             "message": {"role": "user", "content": "Contexte ajouté par le harnais."}},
            appel("req_2", timedelta(seconds=30), entree=1_000_000),
            {"type": "user", "origin": {"kind": "peer"}, "timestamp": iso(timedelta(seconds=20)),
             "message": {"role": "user", "content": "Another Claude session sent a message: ok"}},
            appel("req_3", timedelta(seconds=10), entree=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = lignes_en_dollars(section(r.stdout, 6))
        self.assertEqual(len(rows), 1, f"le tour est coupé :\n{r.stdout}")
        self.assertAlmostEqual(montant(rows[0]), 3.0, places=4)
        self.assertIn("Lance le plan Rapport de tokens", rows[0])

    def test_un_agent_jsonl_a_la_racine_d_un_dossier_ssh_est_un_sous_agent_pas_une_session(self):
        # Attrape : un agent-*.jsonl posé à la racine d'un dossier ssh-* compté
        # comme une session (il n'apparaîtrait alors pas en section 3). Attendu :
        # sous-agent « plans-notion:lecteur », 1 $.
        ssh = self.projets / f"ssh-{SID_B}"
        ecrire(ssh / f"agent-{AGENT_2}.jsonl", [appel("req_lect", entree=1_000_000)])
        (ssh / f"agent-{AGENT_2}.meta.json").write_text(
            json.dumps({"agentType": "plans-notion:lecteur", "toolUseId": "toolu_9"}), encoding="utf-8")
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(montant(ligne_de(section(r.stdout, 3), "plans-notion:lecteur")), 1.0, places=4)

    def test_aucun_message_dans_la_fenetre_rend_le_code_1(self):
        # Attrape : une fenêtre vide rendue comme un rapport à zéro, ou une trace
        # Python au lieu du code 1 annoncé. Les deux messages datent de 30 jours.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Vieux", timedelta(days=30)),
            appel("req_v", timedelta(days=30), entree=1)])
        r = self.lancer()
        self.assertEqual(r.returncode, 1, f"code {r.returncode}, attendu 1 :\n{r.stdout}\n{r.stderr}")
        self.assertNotIn("Traceback", r.stderr)

    def test_une_grille_illisible_rend_le_code_2_sans_trace_python(self):
        # Attrape : une grille au JSON cassé qui fait tomber le script avec une
        # trace Python, ou qui sort avec un autre code que 2.
        self.grille.write_text("{pas du json", encoding="utf-8")
        ecrire(self.depot / f"{SID_A}.jsonl", [humain("Lance"), appel("req_1", entree=1)])
        r = self.lancer()
        self.assertEqual(r.returncode, 2, f"code {r.returncode}, attendu 2 :\n{r.stderr}")
        self.assertIn("grille", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_un_dossier_de_journaux_absent_rend_le_code_2_sans_trace_python(self):
        # Attrape : un dossier de journaux introuvable rendu comme une trace
        # Python, ou avec un autre code que 2.
        absent = self.racine / "absent"
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--projets", str(absent), "--grille", str(self.grille)],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 2, f"code {r.returncode}, attendu 2 :\n{r.stderr}")
        self.assertIn("dossier", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_un_tour_sans_appel_s_affiche_a_zero_dollar_et_jamais_non_chiffre(self):
        # Attrape : un tour sans aucun appel (message humain resté sans réponse dans
        # la fenêtre) affiché « non chiffré », ce qui laisse croire à un modèle hors
        # grille. Attendu : une ligne à 0,0000 $, sans la mention « non chiffré ».
        ecrire(self.depot / f"{SID_A}.jsonl", [humain("Question sans réponse")])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        # Le libellé du tour est en dernière colonne : la ligne se repère par lui.
        rows = [l for l in section(r.stdout, 6) if "Question sans réponse" in l]
        self.assertEqual(len(rows), 1, f"le tour sans appel n'est pas listé :\n{r.stdout}")
        self.assertNotIn("non chiffré", rows[0], f"tour sans appel affiché « non chiffré » : {rows[0]!r}")
        self.assertAlmostEqual(montant(rows[0]), 0.0, places=4)

    def test_top_ne_liste_que_le_nombre_de_tours_demande_les_plus_chers(self):
        # Attrape (panne non nommée au brief) : la liste des tours tronquée à un
        # seul tour quand --top 2 est demandé, ou les tours rangés dans le mauvais
        # ordre. Trois tours de 1, 2 et 3 $ ; --top 2 doit rendre 3 $ puis 2 $.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Premier tour", timedelta(seconds=100)),
            appel("req_t1", timedelta(seconds=99), entree=1_000_000),
            humain("Deuxième tour", timedelta(seconds=80)),
            appel("req_t2", timedelta(seconds=79), entree=2_000_000),
            humain("Troisième tour", timedelta(seconds=60)),
            appel("req_t3", timedelta(seconds=59), entree=3_000_000)])
        r = self.lancer("--top", "2")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = lignes_en_dollars(section(r.stdout, 6))
        self.assertEqual(len(rows), 2, f"--top 2 ne rend pas deux tours :\n{r.stdout}")
        self.assertAlmostEqual(montant(rows[0]), 3.0, places=4)
        self.assertAlmostEqual(montant(rows[1]), 2.0, places=4)
        self.assertIn("Troisième tour", rows[0])
        self.assertIn("Deuxième tour", rows[1])

    def test_top_ne_liste_que_les_ruptures_les_plus_cheres_mais_les_compte_toutes(self):
        # Attrape (panne non nommée au brief) : la section des ruptures qui liste plus
        # de --top lignes, ou qui ne compte que les lignes affichées. Trois ruptures de
        # 1,05 $, 1,40 $ et 2,10 $ ; --top 2 doit en lister 2,10 $ puis 1,40 $, et
        # annoncer les trois dans l'en-tête de la section.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            appel("req_r1", creation=150_000),
            appel("req_r2", creation=200_000),
            appel("req_r3", creation=300_000)])
        r = self.lancer("--top", "2")
        self.assertEqual(r.returncode, 0, r.stderr)
        s5 = section(r.stdout, 5)
        m = re.search(r"(\d+) rupture", "\n".join(s5))
        self.assertIsNotNone(m, f"pas de compte de ruptures :\n{r.stdout}")
        self.assertEqual(m.group(1), "3")
        # Le coût total de la section compte les trois ruptures, pas seulement les deux listées.
        resume = next(l for l in s5 if "rupture(s)" in l)
        self.assertAlmostEqual(montant(resume), 4.55, places=4)
        rows = lignes_en_dollars(s5)
        self.assertEqual(len(rows), 2, f"--top 2 ne liste pas deux ruptures :\n{r.stdout}")
        self.assertAlmostEqual(montant(rows[0]), 2.1, places=4)
        self.assertAlmostEqual(montant(rows[1]), 1.4, places=4)

    def test_le_cout_suit_la_grille_champ_par_champ(self):
        # Attrape (panne non nommée au brief) : un champ de tarif lu à la place d'un
        # autre, la lecture de cache au prix de l'entrée par exemple. Attendu à la
        # main, sur la grille de test : entrée 1 M à 1 $, sortie 2 M à 3 $, lecture
        # 4 M à 0,5 $, écriture 5 min 1 M à 7 $ = 16 $.
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Tous les champs"),
            appel("req_champs", entree=1_000_000, sortie=2_000_000,
                  lecture=4_000_000, creation=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(total(r.stdout), 16.0, places=4)

    def test_un_sous_agent_sans_meta_ni_appel_parent_est_range_type_non_resolu(self):
        # Attrape : un sous-agent sans meta.json rangé sous un type inventé au lieu
        # de « type non résolu », dans deux cas : aucun journal parent (SID_A), ou
        # un parent qui porte le résultat du lancement sans l'appel Agent (SID_B).
        # Attendu : 1 $ + 1 $ = 2 $ sous « type non résolu ».
        ecrire(self.depot / SID_A / "subagents" / f"agent-{AGENT_1}.jsonl",
               [appel("req_orphelin", entree=1_000_000)])
        ecrire(self.depot / f"{SID_B}.jsonl",
               [humain("Parent sans appel Agent"), retour_agent("toolu_perdu", AGENT_2)])
        ecrire(self.depot / SID_B / "subagents" / f"agent-{AGENT_2}.jsonl",
               [appel("req_orphelin2", entree=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(montant(ligne_de(section(r.stdout, 3), "type non résolu")), 2.0, places=4)

    def test_un_worktree_claude_affiche_le_depot_et_non_le_nom_du_worktree(self):
        # Attrape : un worktree <dépôt>/.claude/worktrees/<nom> affiché sous son nom de
        # worktree (« gracious-aryabhata-8fbbc4 ») au lieu du dépôt. Attendu : « job-agent ».
        cwd = "/home/ubuntu/repos/github/benjaminge73/job-agent/.claude/worktrees/gracious-aryabhata-8fbbc4"
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Dans le worktree"),
            {**appel("req_wt", entree=1_000_000), "cwd": cwd}])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        s1 = section(r.stdout, 1)
        self.assertAlmostEqual(montant(ligne_de(s1, "job-agent")), 1.0, places=4)
        self.assertFalse(any("gracious-aryabhata" in l for l in s1), "le nom du worktree apparaît en projet")

    def test_un_premier_cwd_racine_passe_au_cwd_suivant_et_non_au_dossier_ssh(self):
        # Attrape : une session dont le premier cwd est « / » (aucun nom de dépôt)
        # qui retombe sur le dossier ssh-<uuid> sans regarder les cwd suivants.
        # Attendu : « job-agent », donné par le cwd de la ligne suivante.
        ssh = self.projets / f"ssh-{SID_A}"
        ecrire(ssh / f"{SID_A}.jsonl", [
            {**humain("Premier message à la racine"), "cwd": "/"},
            {**appel("req_racine", entree=1_000_000), "cwd": CWD_JOB}])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        s1 = section(r.stdout, 1)
        self.assertAlmostEqual(montant(ligne_de(s1, "job-agent")), 1.0, places=4)
        self.assertFalse(any("ssh-" in l for l in s1), "le nom du dossier ssh- apparaît en projet")

    def test_un_requestid_sur_deux_lignes_garde_la_ligne_la_plus_complete(self):
        # Attrape : Claude Code écrit parfois la même requête sur deux lignes, la
        # première avec un output_tokens partiel (2), la seconde complète (1 000 000).
        # Un script qui garde la première compte 2 tokens de sortie au lieu d'un million.
        # Attendu : une requête à 1 000 000 de sortie = 3 $ (sortie à 3 $ le million).
        ecrire(self.depot / f"{SID_A}.jsonl", [
            humain("Sortie partielle puis complète"),
            appel("req_part", sortie=2),
            appel("req_part", sortie=1_000_000)])
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(total(r.stdout), 3.0, places=4)

    def test_un_agent_de_workflow_sous_subagents_est_un_sous_agent_pas_une_session(self):
        # Attrape : un agent-*.jsonl rangé sous <session>/subagents/workflows/wf_*/
        # compté comme une session de plus. Attendu : un sous-agent « plans-notion:relecteur »
        # à 1 $, et « 1 session(s), 1 sous-agent(s) » dans l'en-tête.
        ecrire(self.depot / f"{SID_A}.jsonl", [humain("Lance un workflow"), appel("req_main", entree=1_000_000)])
        wf = self.depot / SID_A / "subagents" / "workflows" / "wf_x"
        ecrire(wf / f"agent-{AGENT_1}.jsonl", [appel("req_wf", entree=1_000_000)])
        (wf / f"agent-{AGENT_1}.meta.json").write_text(
            json.dumps({"agentType": "plans-notion:relecteur"}), encoding="utf-8")
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 session(s), 1 sous-agent(s)", r.stdout)
        self.assertAlmostEqual(montant(ligne_de(section(r.stdout, 3), "plans-notion:relecteur")), 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
