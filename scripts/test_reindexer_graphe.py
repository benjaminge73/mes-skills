"""Tests du hook SessionStart ``reindexer_graphe.py`` (étape 7 du plan).

Le hook réindexe le graphe codebase-memory quand le HEAD du dépôt de la session
a avancé depuis la dernière indexation. Les tests chargent le module par son
chemin et remplacent ``executer`` (le seul point de sortie vers git et node) :
aucune indexation réelle, et jamais le vrai ``~/.cache``. Le ``HOME`` et le
dossier de cache sont redirigés vers un dossier temporaire.

Contrat observé : code de sortie toujours 0, sortie standard toujours vide,
``.head`` réécrit seulement après une indexation réussie.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "plans-notion" / "hooks"
CHEMIN_HOOK = HOOKS / "reindexer_graphe.py"
HOOKS_JSON = HOOKS / "hooks.json"

RACINE = "/Users/exemple/Dev/depot-demo"
# Nom du projet selon la règle du hook : chemin absolu, « / » remplacés par « - », sans « - » initial.
PROJET = "Users-exemple-Dev-depot-demo"
ANCIEN_SHA = "1111111aaaaaaa"
NOUVEAU_SHA = "2222222bbbbbbb"


def charger_hook():
    spec = importlib.util.spec_from_file_location("reindexer_graphe", CHEMIN_HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Executeur:
    """Remplace ``executer`` : répond à git comme un dépôt à ``head``, compte les lancements."""

    def __init__(self, head: str, code_indexation: int = 0, racine: str = RACINE):
        self.head = head
        self.code_indexation = code_indexation
        self.racine = racine
        self.lancements: list[list[str]] = []

    def __call__(self, cmd, timeout):
        if "--show-toplevel" in cmd:
            return 0, self.racine
        if cmd[-1] == "HEAD":
            return 0, self.head
        self.lancements.append(list(cmd))
        return self.code_indexation, ""


class ReindexerGraphe(unittest.TestCase):
    def setUp(self):
        self.hook = charger_hook()
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        base = Path(dossier.name)
        self.cache = base / "cache"
        self.cache.mkdir()
        self.node = base / "node"
        self.node.write_text("")
        self.bin_js = base / "bin.js"
        self.bin_js.write_text("")
        self.base = base
        for patch in (
            mock.patch.dict(os.environ, {"HOME": str(base), "CBM_CACHE_DIR": str(self.cache),
                                         "CBM_BIN_JS": str(self.bin_js)}),
            mock.patch.object(self.hook, "NODE", str(self.node)),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def depot_suivi(self, head_indexe: str | None = None):
        (self.cache / f"{PROJET}.db").write_bytes(b"")
        if head_indexe is not None:
            (self.cache / f"{PROJET}.head").write_text(head_indexe + "\n", encoding="utf-8")

    def lire_head(self, projet: str = PROJET) -> str:
        return (self.cache / f"{projet}.head").read_text(encoding="utf-8").strip()

    def lancer(self, executeur: Executeur, entree: str | None = None):
        if entree is None:
            entree = json.dumps({"cwd": RACINE})
        sortie, erreur = io.StringIO(), io.StringIO()
        with mock.patch.object(self.hook, "executer", executeur), \
                mock.patch("sys.stdin", io.StringIO(entree)), \
                contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
            code = self.hook.main()
        return code, sortie.getvalue(), erreur.getvalue()

    def test_head_deja_indexe_ne_relance_aucune_indexation(self):
        self.depot_suivi(head_indexe=ANCIEN_SHA)
        executeur = Executeur(head=ANCIEN_SHA)
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(executeur.lancements, [])

    def test_head_avance_lance_une_seule_indexation_puis_note_le_nouveau_sha(self):
        self.depot_suivi(head_indexe=ANCIEN_SHA)
        executeur = Executeur(head=NOUVEAU_SHA)
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(len(executeur.lancements), 1)
        cmd = executeur.lancements[0]
        self.assertIn("index_repository", cmd)
        self.assertIn(RACINE, cmd)
        self.assertEqual(self.lire_head(), NOUVEAU_SHA)

    def test_head_absent_avec_depot_suivi_lance_une_indexation(self):
        self.depot_suivi(head_indexe=None)
        executeur = Executeur(head=NOUVEAU_SHA)
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(len(executeur.lancements), 1)
        self.assertEqual(self.lire_head(), NOUVEAU_SHA)

    def test_indexation_en_echec_laisse_le_head_ancien_intact(self):
        # -1 : délai dépassé ou processus introuvable, côté executer.
        for code_echec in (1, 2, -1):
            with self.subTest(code_indexation=code_echec):
                self.depot_suivi(head_indexe=ANCIEN_SHA)
                executeur = Executeur(head=NOUVEAU_SHA, code_indexation=code_echec)
                code, _, _ = self.lancer(executeur)
                self.assertEqual(code, 0)
                self.assertEqual(len(executeur.lancements), 1)
                self.assertEqual(self.lire_head(), ANCIEN_SHA)

    def test_tirets_consecutifs_du_chemin_sont_reduits_pour_retrouver_le_db(self):
        # Panne non couverte jusqu'ici : le chemin /a/-b/c donne « a--b-c » (deux tirets),
        # alors que le serveur écrit « a-b-c ». Sans réduction, le .db n'est jamais trouvé.
        (self.cache / "a-b-c.db").write_bytes(b"")
        executeur = Executeur(head=NOUVEAU_SHA, racine="/a/-b/c")
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(len(executeur.lancements), 1)
        self.assertEqual(self.lire_head("a-b-c"), NOUVEAU_SHA)

    def test_espace_du_chemin_est_remplace_comme_un_slash_pour_retrouver_le_db(self):
        # Panne : le serveur remplace aussi l'espace par « - » (mesuré avec le vrai binaire).
        # Le chemin « /a/-x y/b » donne « a-x-y-b », pas « a--x y-b » ni « a--x-y-b ».
        (self.cache / "a-x-y-b.db").write_bytes(b"")
        executeur = Executeur(head=NOUVEAU_SHA, racine="/a/-x y/b")
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(len(executeur.lancements), 1)
        self.assertEqual(self.lire_head("a-x-y-b"), NOUVEAU_SHA)

    # Noms mesurés avec le vrai binaire 0.10.8 (dépôts jetables, HOME et cache isolés).
    # Le préfixe fixe du dossier de mesure, « private-tmp-claude-501-…-scratchpad-mesure-cases- »,
    # est retiré des noms : seul le suffixe, qui seul compte pour la règle, est repris ici.

    def _db_trouve_par_le_hook(self, racine: str, nom: str) -> int:
        (self.cache / f"{nom}.db").write_bytes(b"")
        executeur = Executeur(head=NOUVEAU_SHA, racine=racine)
        self.lancer(executeur)
        return len(executeur.lancements)

    def test_caracteres_ascii_hors_lettres_et_chiffres_deviennent_des_tirets(self):
        # Panne : le serveur remplace par « - » tout caractère ASCII hors [A-Za-z0-9._-]
        # (espace, ~, +, @, virgule, parenthèses, apostrophe, deux-points, =, #, %).
        # Mesuré : « a.b_c d~e+f@g,h(i)j'k:l=m » -> « a.b_c-d-e-f-g-h-i-j-k-l-m » ;
        # le dossier iCloud « Library/Mobile Documents/com~apple~CloudDocs/depot » -> « …-depot ».
        cas = {
            "/Users/exemple/a.b_c d~e+f@g,h(i)j'k:l=m": "Users-exemple-a.b_c-d-e-f-g-h-i-j-k-l-m",
            "/Users/exemple/Library/Mobile Documents/com~apple~CloudDocs/depot":
                "Users-exemple-Library-Mobile-Documents-com-apple-CloudDocs-depot",
        }
        for racine, nom in cas.items():
            with self.subTest(racine=racine):
                self.assertEqual(self._db_trouve_par_le_hook(racine, nom), 1)

    def test_un_accent_devient_son_hex_utf8_minuscule_sans_separateur(self):
        # Panne : chaque point de code non ASCII est écrit en hexadécimal de ses octets UTF-8,
        # en minuscules, collé au caractère voisin. Mesuré : « éa » -> « c3a9a » ; « éü » ->
        # « c3a9c3bc » ; « é » en fin de nom -> « c3a9 » ; « É » -> « c389 » ; « é ü » -> « c3a9-c3bc ».
        cas = {
            "/Users/exemple/pa-éa": "Users-exemple-pa-c3a9a",
            "/Users/exemple/k-éü": "Users-exemple-k-c3a9c3bc",
            "/Users/exemple/q-é": "Users-exemple-q-c3a9",
            "/Users/exemple/é-x": "Users-exemple-c3a9-x",
            "/Users/exemple/E-Éx": "Users-exemple-E-c389x",
            "/Users/exemple/proj-é ü#x%y": "Users-exemple-proj-c3a9-c3bc-x-y",
        }
        for racine, nom in cas.items():
            with self.subTest(racine=racine):
                self.assertEqual(self._db_trouve_par_le_hook(racine, nom), 1)

    def test_un_caractere_de_3_ou_4_octets_devient_son_hex_utf8(self):
        # Panne : le symbole euro (3 octets UTF-8) et l'emoji (4 octets) suivent la même règle.
        # Mesuré : « e-€x » -> « e-e282acx » ; « e-😀x » -> « e-f09f9880x ».
        cas = {
            "/Users/exemple/e-€x": "Users-exemple-e-e282acx",
            "/Users/exemple/e-😀x": "Users-exemple-e-f09f9880x",
        }
        for racine, nom in cas.items():
            with self.subTest(racine=racine):
                self.assertEqual(self._db_trouve_par_le_hook(racine, nom), 1)

    def test_un_nom_decompose_nfd_garde_la_lettre_et_hexa_seulement_le_combinant(self):
        # Panne : un nom stocké en NFD (« e » suivi de U+0301) n'est pas normalisé par le serveur :
        # le « e » ASCII reste, seul le combinant devient hex. Mesuré : « n-éx » -> « n-ecc81x ».
        # Un hook qui normaliserait en NFC chercherait « n-c3a9x » et ne trouverait rien.
        self.assertEqual(self._db_trouve_par_le_hook("/Users/exemple/n-éx",
                                                     "Users-exemple-n-ecc81x"), 1)

    def test_depot_non_suivi_ne_lance_rien_et_ne_cree_rien_dans_le_cache(self):
        (self.cache / "autre-depot.db").write_bytes(b"")
        avant = sorted(p.name for p in self.cache.iterdir())
        executeur = Executeur(head=NOUVEAU_SHA)
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(executeur.lancements, [])
        self.assertEqual(sorted(p.name for p in self.cache.iterdir()), avant)

    def test_cache_absent_n_est_pas_cree_par_le_hook(self):
        shutil.rmtree(self.cache)
        executeur = Executeur(head=NOUVEAU_SHA)
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(executeur.lancements, [])
        self.assertFalse(self.cache.exists())

    def test_node_ou_bin_js_absent_sort_en_zero_sans_lancer_et_sans_bruit(self):
        absent = self.base / "absent"
        cas = {
            "node absent": mock.patch.object(self.hook, "NODE", str(absent)),
            "bin.js absent": mock.patch.dict(os.environ, {"CBM_BIN_JS": str(absent)}),
        }
        for nom, patch in cas.items():
            with self.subTest(cas=nom), patch:
                self.depot_suivi(head_indexe=ANCIEN_SHA)
                executeur = Executeur(head=NOUVEAU_SHA)
                code, sortie, erreur = self.lancer(executeur)
                self.assertEqual(code, 0)
                self.assertEqual(executeur.lancements, [])
                self.assertEqual(sortie, "")
                self.assertEqual(erreur, "")
                self.assertEqual(self.lire_head(), ANCIEN_SHA)

    def test_verrou_frais_empeche_le_lancement_et_reste_en_place(self):
        self.depot_suivi(head_indexe=ANCIEN_SHA)
        verrou = self.cache / f"{PROJET}.lock"
        verrou.write_text("autre session\n", encoding="utf-8")
        executeur = Executeur(head=NOUVEAU_SHA)
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(executeur.lancements, [])
        self.assertTrue(verrou.exists(), "un verrou pris par une autre session ne se retire pas")

    def test_verrou_perime_de_plus_de_dix_minutes_est_ignore_puis_retire(self):
        self.depot_suivi(head_indexe=ANCIEN_SHA)
        verrou = self.cache / f"{PROJET}.lock"
        verrou.write_text("session morte\n", encoding="utf-8")
        il_y_a_onze_minutes = time.time() - 11 * 60
        os.utime(verrou, (il_y_a_onze_minutes, il_y_a_onze_minutes))
        executeur = Executeur(head=NOUVEAU_SHA)
        code, _, _ = self.lancer(executeur)
        self.assertEqual(code, 0)
        self.assertEqual(len(executeur.lancements), 1)
        self.assertFalse(verrou.exists(), "le verrou posé par le hook est retiré à la fin")

    def test_sortie_standard_reste_vide_et_code_zero_quelle_que_soit_l_entree(self):
        entrees = {
            "JSON illisible": "{pas du json",
            "entrée vide": "",
            "JSON sans cwd": json.dumps({"autre": "chose"}),
            "lancement réel": json.dumps({"cwd": RACINE}),
        }
        for nom, entree in entrees.items():
            with self.subTest(entree=nom):
                self.depot_suivi(head_indexe=ANCIEN_SHA)
                code, sortie, _ = self.lancer(Executeur(head=NOUVEAU_SHA), entree=entree)
                self.assertEqual(code, 0)
                self.assertEqual(sortie, "")

    def test_entree_illisible_en_processus_reel_sort_en_zero_sans_sortie(self):
        self.depot_suivi(head_indexe=ANCIEN_SHA)
        env = {**os.environ, "CBM_CACHE_DIR": str(self.cache)}
        r = subprocess.run([sys.executable, str(CHEMIN_HOOK)], input="{pas du json",
                           capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")


class DelaiDepasse(unittest.TestCase):
    # Marqueur propre à ce processus de test : une autre session lance le même test avec
    # « sleep 47.123 ». Un marqueur commun ferait compter, ou tuer, le sleep de l'autre.
    MARQUEUR = f"sleep 47.{os.getpid()}"
    # Ancré : ne matche que le processus « sleep » lui-même, pas le shell qui le lance
    # ni le shell d'une autre session dont la ligne de commande contient le même texte.
    MOTIF_SURVIVANT = f"^sleep 47\\.{os.getpid()}$"

    def test_un_delai_depasse_tue_aussi_les_petits_enfants(self):
        # Panne : bin.js lance l'indexeur natif en enfant de node. Si le délai ne tue que
        # le pid de tête, l'enfant survit, écrit encore dans le .db, et le verrou est retiré
        # à tort. Ici, « sh » est la tête et « sleep » son petit-enfant.
        hook = charger_hook()
        code, sortie = hook.executer(["sh", "-c", f"{self.MARQUEUR} & wait"], 1)
        time.sleep(1)
        survivants = subprocess.run(["pgrep", "-f", self.MOTIF_SURVIVANT],
                                    capture_output=True, text=True).stdout.split()
        if survivants:
            subprocess.run(["pkill", "-f", self.MOTIF_SURVIVANT])  # nettoyage avant l'échec
        self.assertEqual(survivants, [], "le petit-enfant a survécu au délai")
        self.assertEqual((code, sortie), (-1, ""))


NODE_PATH = Path("/opt/homebrew/opt/node@24/bin/node")


@unittest.skipUnless(NODE_PATH.is_file(), "node absent : le hook ne lance alors aucune indexation")
class ArretParSignal(unittest.TestCase):
    # Marqueur propre à ce processus de test (voir DelaiDepasse) : pgrep ancré sur le sleep seul.
    MARQUEUR = f"sleep 48.{os.getpid()}"
    MOTIF_SURVIVANT = f"^sleep 48\\.{os.getpid()}$"

    @staticmethod
    def _processus_sleep() -> list[str]:
        return subprocess.run(["pgrep", "-f", ArretParSignal.MOTIF_SURVIVANT],
                              capture_output=True, text=True).stdout.split()

    def test_un_sigterm_pendant_l_indexation_tue_l_indexeur_et_retire_le_verrou(self):
        # Panne : start_new_session sort l'indexeur du groupe du hook. Sans gestionnaire de
        # signal, un SIGTERM tue le seul Python : ni le finally ni le kill du groupe ne
        # tournent, l'indexeur survit et le verrou reste 10 minutes. Le faux bin.js lance
        # « sleep » en enfant, comme le vrai bin.js lance l'indexeur natif (spawnSync).
        with tempfile.TemporaryDirectory() as dossier:
            base = Path(dossier)
            cache = base / "cache"
            cache.mkdir()
            depot = base / "depot"
            depot.mkdir()
            faux_bin = base / "bin.js"
            faux_bin.write_text(
                'const { spawnSync } = require("child_process");\n'
                f'spawnSync("sleep", ["48.{os.getpid()}"]);\n', encoding="utf-8")
            identite = ["-c", "user.name=test", "-c", "user.email=test@example.com",
                        "-c", "commit.gpgsign=false"]
            subprocess.run(["git", "init", "-q", str(depot)], check=True, capture_output=True)
            subprocess.run(["git", *identite, "commit", "-q", "--allow-empty", "-m", "init"],
                           cwd=depot, check=True, capture_output=True)
            racine = subprocess.run(["git", "-C", str(depot), "rev-parse", "--show-toplevel"],
                                    capture_output=True, text=True, check=True).stdout.strip()
            projet = charger_hook().nom_du_projet(racine)
            (cache / f"{projet}.db").write_bytes(b"")
            verrou = cache / f"{projet}.lock"
            env = {**os.environ, "CBM_CACHE_DIR": str(cache), "CBM_BIN_JS": str(faux_bin)}

            entree = base / "entree.json"
            entree.write_text(json.dumps({"cwd": str(depot)}), encoding="utf-8")
            code, sortie, lance, verrou_pose = None, "", False, False
            survivants, verrou_restant = [], False
            with entree.open("rb") as flux:
                hook = subprocess.Popen([sys.executable, str(CHEMIN_HOOK)], stdin=flux,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, env=env)
            try:
                for _ in range(100):  # jusqu'à 10 s pour que l'indexeur simulé démarre
                    if self._processus_sleep():
                        lance = True
                        break
                    time.sleep(0.1)
                verrou_pose = verrou.exists()
                hook.send_signal(signal.SIGTERM)
                try:
                    sortie, _ = hook.communicate(timeout=15)
                    code = hook.returncode
                except subprocess.TimeoutExpired:
                    pass  # le hook ne s'arrête pas : le finally le tue
                time.sleep(1)
                survivants = self._processus_sleep()
                verrou_restant = verrou.exists()
            finally:
                if hook.poll() is None:
                    hook.kill()
                    hook.communicate()
                if self._processus_sleep():
                    subprocess.run(["pkill", "-f", self.MOTIF_SURVIVANT])  # nettoyage avant l'échec

        self.assertTrue(lance, "l'indexeur simulé n'a pas démarré : le test ne prouve rien")
        self.assertTrue(verrou_pose, "le hook doit poser le verrou pendant l'indexation")
        self.assertEqual(survivants, [], "l'indexeur a survécu au SIGTERM du hook")
        self.assertFalse(verrou_restant, "le verrou doit être retiré après le SIGTERM")
        self.assertEqual(code, 0)
        self.assertEqual(sortie, "")


class HooksJson(unittest.TestCase):
    def test_hooks_json_reste_valide_et_reindexer_est_declare_asynchrone_au_session_start(self):
        donnees = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        commandes = [h for bloc in donnees["hooks"]["SessionStart"] for h in bloc["hooks"]]
        reindexer = [h for h in commandes if "reindexer_graphe.py" in h.get("command", "")]
        self.assertEqual(len(reindexer), 1)
        self.assertEqual(reindexer[0]["type"], "command")
        self.assertIs(reindexer[0].get("async"), True)
        # Panne voisine : l'ajout ne doit pas retirer le rappel SessionStart déjà présent.
        self.assertTrue(any("rappel_methode_hermes.py" in h.get("command", "") for h in commandes))


if __name__ == "__main__":
    unittest.main()
