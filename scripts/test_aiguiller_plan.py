"""Tests de ``aiguiller-plan.py`` : le juge « léger ou complet » d'une demande de plan.

Chaque test lance le vrai script en sous-processus, avec un faux ``claude`` désigné par
``QUALITE_DOC_CLAUDE`` (même mécanisme que ``test_qualite_doc.py``). Aucun appel réel à un
modèle. Le faux ``claude`` consomme ses réponses dans l'ordre d'arrivée : un passage = un appel.

Les identifiants des cases ne sont pas recopiés ici : ils se lisent dans la checklist
(``listes/aiguillage-plan.md``), comme le fait le script.

Lancés par ``python3 -m unittest scripts.test_aiguiller_plan``, sans dépendance.
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
SCRIPT = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "scripts" / "aiguiller-plan.py"
CHECKLIST = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "listes" / "aiguillage-plan.md"
MODELE = "claude-haiku-5-5"

# Faux ``claude`` : écrit son prompt et son numéro d'appel, puis rend l'enveloppe JSON de
# ``claude -p --output-format json``. Il rend le modèle demandé (--model), sauf si la réponse
# en impose un autre (``modele``) ; ``erreur`` lève ``is_error``.
FAUX_CLAUDE = """#!__PYTHON__
import glob, json, os, sys
dossier = __DOSSIER__
with open(os.path.join(dossier, "reponses.json"), encoding="utf-8") as f:
    reponses = json.load(f)
n = len(glob.glob(os.path.join(dossier, "appel-*.txt")))
with open(os.path.join(dossier, "appel-%03d.txt" % n), "w", encoding="utf-8") as f:
    f.write(sys.stdin.buffer.read().decode("utf-8"))
demande = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "?"
reponse = reponses[n % len(reponses)]
print(json.dumps({
    "type": "result",
    "is_error": reponse.get("erreur", False),
    "result": reponse["texte"],
    "total_cost_usd": 0.01,
    "modelUsage": {reponse.get("modele", demande): {"costUSD": 0.01}},
}))
"""


def ids_de_la_checklist() -> list[str]:
    """Les identifiants des cases, lus dans le fichier (lignes ``- [ ] A<n> …``)."""
    return re.findall(r"^- \[ \] (A\d+) ", CHECKLIST.read_text(encoding="utf-8"), re.MULTILINE)


def faux_claude(dossier: Path, reponses: list[dict]) -> Path:
    (dossier / "reponses.json").write_text(json.dumps(reponses), encoding="utf-8")
    exe = dossier / "claude"
    exe.write_text(FAUX_CLAUDE.replace("__PYTHON__", sys.executable)
                   .replace("__DOSSIER__", repr(str(dossier))), encoding="utf-8")
    exe.chmod(0o755)
    return exe


def appel(texte: str, **extra) -> dict:
    """Une réponse du faux claude : son texte ``result``, et au besoin ``modele`` ou ``erreur``."""
    return {"texte": texte, **extra}


def passage(surcharges: dict | None = None, omettre: tuple = ()) -> str:
    """Le texte d'un passage : une case par identifiant de la checklist, « non » avec preuve par défaut.

    ``surcharges`` remplace ``(reponse, preuve)`` pour un identifiant ; ``omettre`` retire des identifiants.
    """
    surcharges = surcharges or {}
    cases = []
    for ident in ids_de_la_checklist():
        if ident in omettre:
            continue
        reponse, preuve = surcharges.get(ident, ("non", f"preuve de {ident}"))
        cases.append({"id": ident, "reponse": reponse, "preuve": preuve})
    return json.dumps({"cases": cases}, ensure_ascii=False)


class Aiguillage(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dossier = Path(self._tmp.name)
        self.demande = self.dossier / "demande.md"
        self.demande.write_text("Corriger une faute de frappe dans le README d'un plugin.\n",
                                encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def aiguiller(self, exe: Path):
        """Lance le script ; rend (code, sortie standard, sortie d'erreur)."""
        env = {**os.environ, "QUALITE_DOC_CLAUDE": str(exe)}
        r = subprocess.run([sys.executable, str(SCRIPT), "--demande", str(self.demande)],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        return r.returncode, r.stdout, r.stderr

    def appels(self) -> int:
        return len(list(self.dossier.glob("appel-*.txt")))

    def sortie(self, stdout: str) -> dict:
        try:
            objet = json.loads(stdout)
        except json.JSONDecodeError:
            self.fail(f"la sortie standard n'est pas un objet JSON : {stdout!r}")
        self.assertIsInstance(objet, dict)
        return objet

    def assertComplet(self, code: int, stdout: str) -> dict:
        """Le verdict « complet » : code 1, verdict « complet » sur la sortie standard, aucune erreur."""
        sortie = self.sortie(stdout)
        self.assertEqual(code, 1, f"code {code} au lieu de 1 (complet) ; sortie : {stdout!r}")
        self.assertEqual(sortie["verdict"], "complet")
        self.assertNotIn("erreur", sortie)
        return sortie

    # Attrape : un plan léger jamais rendu, ou rendu alors que les deux passages disent « non » partout.
    # Attendu : code 0, verdict « léger », deux passages valides, deux appels, aucun motif.
    # Le faux claude rend le modèle demandé : le défaut (claude-haiku-5-5) passe donc bien par --model.
    def test_deux_passages_tout_non_avec_preuve_rendent_leger(self):
        exe = faux_claude(self.dossier, [appel(passage()), appel(passage())])
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.sortie(stdout)
        self.assertEqual(code, 0, f"code {code} au lieu de 0 (léger) ; sortie : {stdout!r}")
        self.assertEqual(sortie["verdict"], "léger")
        self.assertEqual(sortie["modele"], MODELE)
        self.assertEqual([p["valide"] for p in sortie["passages"]], [True, True])
        self.assertEqual(sortie["motifs"], [])
        self.assertTrue(sortie["a_valider_par_benjamin"])
        self.assertEqual(self.appels(), 2)

    # Attrape : une case « doute » lue comme « non », ou un arrêt au premier passage.
    # Attendu : code 1, verdict « complet », la case nommée dans les motifs, deux passages joués.
    def test_une_case_en_doute_rend_complet(self):
        exe = faux_claude(self.dossier, [appel(passage({"A5": ("doute", "rien ne dit si ça lit des données")}))] * 2)
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.assertComplet(code, stdout)
        self.assertTrue(any("A5" in m for m in sortie["motifs"]), sortie["motifs"])
        self.assertEqual(self.appels(), 2)

    # Attrape : une case « oui » (la demande touche ce que la case demande) rendue léger.
    # Attendu : code 1, verdict « complet », la case nommée dans les motifs.
    def test_une_case_oui_rend_complet(self):
        exe = faux_claude(self.dossier, [appel(passage({"A2": ("oui", "la demande touche un secret")}))] * 2)
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.assertComplet(code, stdout)
        self.assertTrue(any("A2" in m for m in sortie["motifs"]), sortie["motifs"])

    # Attrape : une réponse en prose (sans JSON) lue comme un plan léger, ou qui fait planter le script.
    # Attendu : code 1, verdict « complet », passage marqué invalide.
    def test_une_reponse_qui_n_est_pas_du_json_rend_complet(self):
        exe = faux_claude(self.dossier, [appel("Je ne peux pas trancher sur cette demande.")] * 2)
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.assertComplet(code, stdout)
        self.assertFalse(sortie["passages"][0]["valide"])

    # Attrape : une checklist à laquelle un passage répond sans une de ses cases (une case perdue en route
    # compte comme « non » par défaut, donc « léger »).
    # Attendu : code 1, verdict « complet », passage invalide, la case manquante nommée.
    def test_une_case_manquante_rend_complet(self):
        exe = faux_claude(self.dossier, [appel(passage(omettre=("A7",)))] * 2)
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.assertComplet(code, stdout)
        self.assertFalse(sortie["passages"][0]["valide"])
        self.assertIn("A7", sortie["passages"][0]["raison"])

    # Attrape : un « non » sans preuve (la règle exige une preuve pour léger) rendu léger.
    # Attendu : code 1, verdict « complet », passage invalide.
    def test_une_preuve_vide_rend_complet(self):
        exe = faux_claude(self.dossier, [appel(passage({"A4": ("non", "   ")}))] * 2)
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.assertComplet(code, stdout)
        self.assertFalse(sortie["passages"][0]["valide"])

    # Attrape : un désaccord entre les deux passages tranché en faveur du premier (ou du dernier)
    # au lieu de rendre complet. Attendu : code 1, verdict « complet », les deux passages joués,
    # dans les deux ordres.
    def test_un_desaccord_entre_passages_rend_complet(self):
        cas = {
            "premier tout non, second un oui": [appel(passage()), appel(passage({"A6": ("oui", "trois fichiers")}))],
            "premier un doute, second tout non": [appel(passage({"A6": ("doute", "à voir")})), appel(passage())],
        }
        for nom, reponses in cas.items():
            with self.subTest(nom):
                self.dossier.joinpath("appel-000.txt").unlink(missing_ok=True)
                self.dossier.joinpath("appel-001.txt").unlink(missing_ok=True)
                exe = faux_claude(self.dossier, reponses)
                code, stdout, _ = self.aiguiller(exe)
                self.assertComplet(code, stdout)
                self.assertEqual(self.appels(), 2)

    # Attrape : un script qui lit « claude absent » comme un verdict (ou comme un plan léger).
    # Attendu : code 2, verdict « complet » avec une erreur nommée, raison sur la sortie d'erreur.
    # Le script absent rendrait aussi code 2 ; c'est la sortie JSON qui rend ce test rouge tant qu'il n'existe pas.
    def test_claude_introuvable_rend_code_2_et_complet(self):
        code, stdout, stderr = self.aiguiller(Path("claude-introuvable-sur-ce-poste"))
        sortie = self.sortie(stdout)
        self.assertEqual(code, 2, f"code {code} au lieu de 2 ; sortie : {stdout!r}")
        self.assertEqual(sortie["verdict"], "complet")
        self.assertIn("erreur", sortie)
        self.assertTrue(stderr.strip(), "la raison doit aussi partir sur la sortie d'erreur")

    # Attrape : un modèle servi autre que celui demandé, accepté comme avis valide.
    # Attendu : code 2, verdict « complet », erreur nommée.
    def test_modele_servi_inattendu_rend_code_2_et_complet(self):
        exe = faux_claude(self.dossier, [appel(passage(), modele="claude-autre-modele")] * 2)
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.sortie(stdout)
        self.assertEqual(code, 2, f"code {code} au lieu de 2 ; sortie : {stdout!r}")
        self.assertEqual(sortie["verdict"], "complet")
        self.assertIn("erreur", sortie)

    # Attrape : un appel en échec (claude rend is_error) lu comme un passage valide. C'est une panne
    # nommée du contrat (appel en échec → code 2), qu'aucun autre test ne couvre.
    # Attendu : code 2, verdict « complet », erreur nommée.
    def test_appel_en_echec_rend_code_2_et_complet(self):
        exe = faux_claude(self.dossier, [appel(passage(), erreur=True)] * 2)
        code, stdout, _ = self.aiguiller(exe)
        sortie = self.sortie(stdout)
        self.assertEqual(code, 2, f"code {code} au lieu de 2 ; sortie : {stdout!r}")
        self.assertEqual(sortie["verdict"], "complet")
        self.assertIn("erreur", sortie)


if __name__ == "__main__":
    unittest.main()
