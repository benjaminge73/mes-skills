"""Tests de ``cout-plan.py`` : le coût réel d'un plan Notion, à partir des journaux.

Le script retrouve les sessions dont un journal (``projets/**/*.jsonl``) cite
l'identifiant de la page dans un appel d'outil, demande à ``ccusage session
--json`` leurs tokens, et chiffre ces tokens sur ``grille-tarifs.json``.

Aucun test n'appelle le vrai ``ccusage`` : un faux exécutable ``ccusage``,
posé en tête du PATH, rend une sortie fixée à l'avance. Chaque cas lance le
script en vrai sous-processus, sur un dossier de journaux fabriqué dans un
``tempfile.TemporaryDirectory``, et observe la sortie et le code retour.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "cout-plan.py"

PAGE = "aaaa1111bbbb2222cccc3333dddd4444"
PAGE_TIRET = "aaaa1111-bbbb-2222-cccc-3333dddd4444"
PAGE_AUTRE = "eeee5555ffff6666aaaa7777bbbb8888"

SID_CITE = "11111111-2222-4333-8444-555555555555"
SID_NON = "22222222-3333-4444-8555-666666666666"
SID_HORS = "33333333-4444-4555-8666-777777777777"

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
HAIKU = "claude-haiku-5-5"

# Grille de test : des prix distincts par champ, pour qu'une confusion entre
# lecture et écriture de cache se voie dans le total.
GRILLE = {
    "releve": "2026-10-12",
    "source": "fixture de test",
    "unite": "dollars par million de tokens",
    "modeles": {
        OPUS: {"entree": {"prix": 1, "derive": False}, "sortie": {"prix": 3, "derive": False},
               "lecture_cache": {"prix": 0.5, "derive": False},
               "ecriture_cache_5m": {"prix": 7, "derive": True},
               "ecriture_cache_1h": {"prix": 9, "derive": False}},
        SONNET: {"entree": {"prix": 2, "derive": False}, "sortie": {"prix": 10, "derive": False},
                 "lecture_cache": {"prix": 0.2, "derive": True},
                 "ecriture_cache_5m": {"prix": 2.5, "derive": True},
                 "ecriture_cache_1h": {"prix": 4, "derive": True}},
        HAIKU: {"entree": {"prix": 0.1, "derive": False}, "sortie": {"prix": 0.5, "derive": False},
                "lecture_cache": {"prix": 0.01, "derive": True},
                "ecriture_cache_5m": {"prix": 0.125, "derive": True},
                "ecriture_cache_1h": {"prix": 0.2, "derive": True}},
    },
}


def journal(projets: Path, sid: str, cibles: list[str]) -> None:
    """Écrit ``<projets>/-depot/<sid>.jsonl`` : un appel d'outil par identifiant cité."""
    dossier = projets / "-depot"
    dossier.mkdir(parents=True, exist_ok=True)
    lignes = []
    for i, cible in enumerate(cibles):
        lignes.append(json.dumps({"type": "assistant", "sessionId": sid, "message": {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": f"toolu_{i}",
                         "name": "mcp__notion__notion-fetch", "input": {"id": cible}}]}}))
    if not cibles:
        lignes.append(json.dumps({"type": "user", "sessionId": sid,
                                  "message": {"role": "user", "content": "bonjour"}}))
    (dossier / f"{sid}.jsonl").write_text("\n".join(lignes) + "\n", encoding="utf-8")


def bloc(modele: str, entree: int = 0, sortie: int = 0, lecture: int = 0, creation: int = 0) -> dict:
    """Une entrée ``modelBreakdowns`` de ccusage. Son ``cost`` est volontairement faux."""
    return {"modelName": modele, "inputTokens": entree, "outputTokens": sortie,
            "cacheReadTokens": lecture, "cacheCreationTokens": creation, "cost": 999.0}


def session(sid: str, blocs: list[dict]) -> dict:
    return {"agent": "claude", "period": sid,
            "metadata": {"lastActivity": "2026-10-12T08:00:00.000Z"},
            "modelsUsed": [b["modelName"] for b in blocs], "modelBreakdowns": blocs,
            "totalCost": 999.0, "totalTokens": 0, "inputTokens": 0, "outputTokens": 0,
            "cacheCreationTokens": 0, "cacheReadTokens": 0}


def faux_ccusage(racine: Path, sessions: list[dict]) -> Path:
    """Pose un ``ccusage`` factice qui rend ``sessions`` ; rend le dossier à mettre en tête du PATH."""
    bin_dir = racine / "bin"
    bin_dir.mkdir()
    fixture = racine / "ccusage.json"
    fixture.write_text(json.dumps({"session": sessions, "totals": {}}), encoding="utf-8")
    exe = bin_dir / "ccusage"
    exe.write_text(f"#!/bin/sh\ncat '{fixture}'\n", encoding="utf-8")
    exe.chmod(0o755)
    return bin_dir


def lancer(projets: Path, grille: Path, path: str, *extra: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PATH"] = path
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--page", PAGE, "--projets", str(projets),
         "--grille", str(grille), *extra],
        capture_output=True, text=True, env=env, timeout=120)


def montant(ligne: str) -> float:
    """Le premier montant « 12,3400 $ » d'une ligne, en nombre."""
    m = re.search(r"(\d[\d ]*,\d+) \$", ligne)
    if m is None:
        raise AssertionError(f"aucun montant en dollars dans : {ligne!r}")
    return float(m.group(1).replace(" ", "").replace(",", "."))


def ligne_du_modele(sortie: str, modele: str) -> str:
    lignes = [l for l in sortie.splitlines() if l.strip().startswith(modele)]
    if not lignes:
        raise AssertionError(f"aucune ligne pour {modele} dans la sortie :\n{sortie}")
    return lignes[0]


class CoutPlan(unittest.TestCase):

    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), f"cout-plan.py absent : {SCRIPT}")
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name)
        self.projets = self.racine / "projets"
        self.projets.mkdir()
        self.grille = self.racine / "grille.json"
        self.grille.write_text(json.dumps(GRILLE), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_une_session_qui_ne_cite_pas_la_page_n_est_pas_comptee(self):
        # Attrape : le script compte toutes les sessions que ccusage rend, au
        # lieu de ne retenir que celles dont un journal cite la page.
        journal(self.projets, SID_CITE, [PAGE_TIRET])
        journal(self.projets, SID_NON, [PAGE_AUTRE])
        bin_dir = faux_ccusage(self.racine, [
            session(SID_CITE, [bloc(OPUS, entree=1_000_000)]),
            session(SID_NON, [bloc(OPUS, entree=5_000_000)]),
        ])
        r = lancer(self.projets, self.grille, f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(SID_CITE, r.stdout)
        self.assertNotIn(SID_NON, r.stdout)
        self.assertNotIn("6 000 000", r.stdout, "les 5 000 000 entrées de la session non citée sont comptées")

    def test_un_modele_absent_de_la_grille_est_liste_a_part_jamais_chiffre_a_zero(self):
        # Attrape : un modèle hors grille sort chiffré à 0 $ au lieu d'être
        # signalé, et le total le fait disparaître en silence.
        journal(self.projets, SID_HORS, [PAGE])
        bin_dir = faux_ccusage(self.racine, [
            session(SID_HORS, [bloc(OPUS, entree=1_000_000),
                               bloc("claude-inconnu-9", entree=500)]),
        ])
        r = lancer(self.projets, self.grille, f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("hors grille", r.stdout)
        # Seules les lignes de modèle comptent : la ligne de session liste aussi
        # les modèles qu'elle a employés, et elle n'est pas un chiffrage.
        lignes = [l for l in r.stdout.splitlines() if l.strip().startswith("claude-inconnu-9")]
        self.assertTrue(lignes, f"le modèle hors grille n'apparaît pas :\n{r.stdout}")
        for l in lignes:
            self.assertIn("non chiffré", l, f"modèle hors grille présenté comme chiffré : {l!r}")
            self.assertNotIn("0,0000 $", l, f"modèle hors grille chiffré à zéro : {l!r}")

    def test_ccusage_absent_donne_un_message_clair_et_le_code_2(self):
        # Attrape : une trace Python au lieu d'un message, ou un autre code de
        # sortie quand l'outil externe manque.
        journal(self.projets, SID_CITE, [PAGE])
        vide = self.racine / "vide"
        vide.mkdir()
        r = lancer(self.projets, self.grille, str(vide))
        self.assertEqual(r.returncode, 2, f"code {r.returncode}, attendu 2 :\n{r.stderr}")
        self.assertIn("ccusage", r.stderr)
        self.assertIn("ccusage@20.0.30", r.stderr, "le message ne dit pas comment l'installer")
        self.assertNotIn("Traceback", r.stderr)

    def test_le_cout_suit_la_grille_champ_par_champ(self):
        # Attrape (non nommé au brief) : un champ de tarif lu à la place d'un
        # autre (lecture de cache prise pour l'écriture, sortie pour entrée),
        # ou le $ de ccusage repris à la place du calcul sur la grille.
        # Attendu calculé à la main : opus 1 M entrée à 1 $, 2 M sortie à 3 $,
        # 4 M lecture à 0,5 $, 1 M écriture 5 min à 7 $ = 16 $ ; haiku 10 M
        # lecture à 0,01 $ = 0,10 $ ; total 16,10 $.
        journal(self.projets, SID_CITE, [PAGE])
        bin_dir = faux_ccusage(self.racine, [
            session(SID_CITE, [
                bloc(OPUS, entree=1_000_000, sortie=2_000_000, lecture=4_000_000, creation=1_000_000),
                bloc(HAIKU, lecture=10_000_000),
            ]),
        ])
        r = lancer(self.projets, self.grille, f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(montant(ligne_du_modele(r.stdout, OPUS)), 16.0, places=4)
        self.assertAlmostEqual(montant(ligne_du_modele(r.stdout, HAIKU)), 0.10, places=4)
        total = [l for l in r.stdout.splitlines() if l.lower().startswith("total")]
        self.assertTrue(total, f"pas de ligne de total :\n{r.stdout}")
        self.assertAlmostEqual(montant(total[0]), 16.10, places=4)


GRILLE_REELLE = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "grille-tarifs.json"

# Prix relevés sur la page tarifs d'Anthropic le 2026-10-12, en dollars par
# million de tokens ; pour Haiku 5.5, le palier « prompt jusqu'à 100 000
# tokens ». Écrits à la main, jamais lus dans la grille.
PAGE_TARIFS = {
    OPUS: {"entree": 4, "sortie": 20, "ecriture_cache_5m": 5, "ecriture_cache_1h": 8, "lecture_cache": 0.2},
    SONNET: {"entree": 2, "sortie": 10, "ecriture_cache_5m": 2.5, "ecriture_cache_1h": 4, "lecture_cache": 0.1},
    HAIKU: {"entree": 0.1, "sortie": 0.5, "ecriture_cache_5m": 0.125, "ecriture_cache_1h": 0.2, "lecture_cache": 0.01},
}


class GrilleReelle(unittest.TestCase):
    """Ce test lit la vraie grille du dépôt, pas une fixture : c'est le contrôle du fait porteur de docs/veille.md."""

    def test_la_grille_du_depot_porte_les_prix_de_la_page_et_une_lecture_de_cache_a_5_pour_cent_de_l_entree(self):
        # Attrape : la grille du dépôt porte un prix qui ne vient pas de la page.
        # Panne réelle au 2026-10-12 : la lecture de cache de Sonnet 5.5 valait
        # 0,20 $ (coefficient 0,10 × entrée déduit) au lieu de 0,10 $ relevé,
        # soit 0,05 × l'entrée. Le test rend la liste complète des écarts.
        grille = json.loads(GRILLE_REELLE.read_text(encoding="utf-8"))
        ecarts = []
        for modele, releve in PAGE_TARIFS.items():
            portee = grille["modeles"].get(modele, {})
            for champ, prix_page in releve.items():
                prix_grille = portee.get(champ, {}).get("prix")
                if prix_grille is None or abs(float(prix_grille) - prix_page) > 1e-9:
                    ecarts.append(f"{modele} {champ} : grille {prix_grille}, page {prix_page}")
        for modele in (OPUS, SONNET):
            portee = grille["modeles"].get(modele, {})
            entree = portee.get("entree", {}).get("prix")
            lecture = portee.get("lecture_cache", {}).get("prix")
            if entree is None or lecture is None or abs(float(lecture) - 0.05 * float(entree)) > 1e-9:
                ecarts.append(f"{modele} lecture_cache : grille {lecture}, attendu 0,05 × entrée ({entree})")
        self.assertEqual(ecarts, [], "écarts entre grille-tarifs.json et la page tarifs :\n" + "\n".join(ecarts))


if __name__ == "__main__":
    unittest.main()
