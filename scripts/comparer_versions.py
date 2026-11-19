#!/usr/bin/env python3
"""Les scripts de ``_partage`` rendent-ils la même chose qu'avant ?

La règle
--------
Les scripts de ``plugins/<p>/skills/_partage/scripts/`` tournent dans les skills
(``plan-notion``, ``executer-plan-notion``…) : un script qui change de sortie change
le comportement de toutes les sessions qui l'appellent, et aucun test de skill ne
le voit. Ce garde rejoue chaque script sur chaque plan de référence
(``scripts/fixtures_plans/`` par défaut), côté base (``--base``) puis côté tête
(``HEAD``, le commit : les modifications non commitées ne sont pas vues). Chaque
couple est joué deux fois de chaque côté, pour repérer une sortie instable. Un écart est une sortie qui change : code de retour, sortie standard ou
sortie d'erreur.

Un écart voulu se déclare dans un commit de la PR (``base..tête``) :

    Ecart-admis: <script> — <raison>

``<script>`` est le nom du fichier (``vagues.py``), son nom court (``vagues``) ou
son chemin complet. La raison est obligatoire : sans elle, la ligne est refusée.

Pourquoi pas une comparaison par éval : chaque éval coûte de l'argent et de la
durée (voir docs/tester-un-skill.md). Celle-ci ne coûte que quelques secondes de Python.

Un script dont la sortie varie d'une exécution à l'autre sur la même version (horodatage,
hasard) n'est pas comparable : il est listé à part, sans verdict. Un script absent de
la tête est un écart ; un script nouveau n'a pas de base et n'est pas comparé.

Codes de sortie : ``0`` aucun écart non déclaré, ``1`` écart non déclaré ou
déclaration invalide, ``2`` panne (base illisible, ou aucun plan : rien n'est
comparé, donc rien n'est vert).
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLANS_PAR_DEFAUT = REPO_ROOT / "scripts" / "fixtures_plans"
DELAI_S = 30

SCRIPT_PARTAGE = re.compile(r"^plugins/[^/]+/skills/_partage/scripts/[^/]+\.(?:py|sh)$")
LIGNE_ECART = re.compile(r"^Ecart-admis:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
DECLARATION = re.compile(r"^(\S+)[ \t]+(?:—|–|--|-)[ \t]*(\S.*)$")


class Panne(RuntimeError):
    """La comparaison ne peut pas se faire : rien n'est vert."""


@dataclass(frozen=True)
class Sortie:
    code: int
    sortie: str
    erreur: str


@dataclass
class Verdict:
    base_sha: str
    tete_sha: str
    plans: list[str]
    comparables: list[str] = field(default_factory=list)
    nouveaux: list[str] = field(default_factory=list)
    instables: list[str] = field(default_factory=list)
    ecarts: list[str] = field(default_factory=list)      # non déclarés : refusent
    admis: list[str] = field(default_factory=list)       # déclarés : signalés
    inutilises: list[str] = field(default_factory=list)  # déclarés sans écart
    invalides: list[str] = field(default_factory=list)   # refusent

    def refuse(self) -> bool:
        return bool(self.ecarts or self.invalides)

    def rapport(self) -> str:
        lignes = [
            f"Scripts de _partage, base {self.base_sha} → tête {self.tete_sha} : "
            f"{len(self.comparables)} script(s) comparé(s) sur {len(self.plans)} plan(s) "
            f"({', '.join(self.plans)})."
        ]
        if self.instables:
            lignes.append("Non comparés (sortie qui varie d'une exécution à l'autre sur la "
                          "même version) : " + ", ".join(self.instables))
        if self.nouveaux:
            lignes.append("Nouveaux, sans base à comparer : " + ", ".join(self.nouveaux))
        if self.admis:
            lignes.append("Écarts déclarés (Ecart-admis) :")
            lignes += [f"  - {x}" for x in self.admis]
        if self.inutilises:
            lignes.append("Ecart-admis sans écart à admettre (à retirer si le script est "
                          "revenu à l'identique) : " + ", ".join(self.inutilises))
        if self.invalides:
            lignes.append("Lignes Ecart-admis invalides :")
            lignes += [f"  - {x}" for x in self.invalides]
        if self.ecarts:
            lignes.append("Écarts NON déclarés :")
            lignes += [f"  - {x}" for x in self.ecarts]
            lignes.append("Pour admettre un écart voulu, un commit de la PR porte : "
                          "Ecart-admis: <script> — <raison>")
        if not self.ecarts and not self.invalides:
            lignes.append("Aucun écart non déclaré.")
        return "\n".join(lignes)


def _git(racine: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(racine), *args], capture_output=True, text=True)


def _ref_existe(racine: Path, ref: str) -> bool:
    return _git(racine, "cat-file", "-e", f"{ref}^{{commit}}").returncode == 0


def _sha(racine: Path, ref: str) -> str:
    return _git(racine, "rev-parse", "--short=7", ref).stdout.strip()


def _commits(racine: Path, base: str, tete: str) -> list[tuple[str, str]]:
    sortie = _git(racine, "log", "--format=%H%x1f%B%x1e", f"{base}..{tete}")
    if sortie.returncode != 0:
        raise Panne(sortie.stderr.strip())
    commits = []
    for bloc in sortie.stdout.split("\x1e"):
        if "\x1f" in bloc:
            sha, message = bloc.split("\x1f", 1)
            commits.append((sha.strip(), message))
    return commits


def _extraire(racine: Path, ref: str, dest: Path) -> None:
    """Le dépôt tel qu'à ``ref``, écrit dans ``dest`` (le dépôt n'est pas touché)."""
    r = subprocess.run(["git", "-C", str(racine), "archive", "--format=tar", ref],
                       capture_output=True)
    if r.returncode != 0:
        raise Panne(f"git archive {ref} a échoué : "
                    f"{r.stderr.decode('utf-8', 'replace').strip()}")
    dest.mkdir(parents=True)
    racine_dest = dest.resolve()
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tar:
        for m in tar.getmembers():
            cible = (racine_dest / m.name).resolve()
            if racine_dest not in cible.parents:
                raise Panne(f"chemin suspect dans l'archive de {ref} : {m.name}")
            if m.isdir():
                cible.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                cible.parent.mkdir(parents=True, exist_ok=True)
                cible.write_bytes(tar.extractfile(m).read())
                cible.chmod(m.mode & 0o777 or 0o644)
            # Les liens ne sont pas extraits : aucun script de _partage n'en est un.


def _preparer(racine: Path, ref: str, arbre: Path) -> None:
    """Remet ``arbre`` dans l'état de ``ref`` : même chemin pour les deux versions,
    pour que les messages d'erreur (chemins dans les tracebacks) soient comparables."""
    for nom in ("depot", "home"):
        shutil.rmtree(arbre / nom, ignore_errors=True)
    _extraire(racine, ref, arbre / "depot")
    (arbre / "home").mkdir()


def _scripts(depot: Path) -> list[str]:
    trouves = []
    for chemin in depot.glob("plugins/*/skills/_partage/scripts/*"):
        rel = chemin.relative_to(depot).as_posix()
        if chemin.is_file() and SCRIPT_PARTAGE.match(rel):
            trouves.append(rel)
    return sorted(trouves)


def _executer(arbre: Path, script: str, plan: str) -> Sortie:
    commande = [sys.executable, script] if script.endswith(".py") else ["bash", script]
    commande.append(f"../plans/{plan}")
    env = {
        "PATH": os.environ.get("PATH", os.defpath),
        "HOME": str(arbre / "home"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONUTF8": "1",
        "GIT_CEILING_DIRECTORIES": str(arbre),
    }
    try:
        r = subprocess.run(commande, cwd=arbre / "depot", env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, timeout=DELAI_S)
    except subprocess.TimeoutExpired:
        return Sortie(-1, "", f"délai de {DELAI_S} s dépassé")
    return Sortie(r.returncode, r.stdout.decode("utf-8", "replace"),
                  r.stderr.decode("utf-8", "replace"))


def _sorties(arbre: Path, scripts: list[str], plans: list[str]) -> dict[tuple[str, str], Sortie | None]:
    """Chaque couple (script, plan) joué deux fois : None si les deux sorties diffèrent."""
    res: dict[tuple[str, str], Sortie | None] = {}
    for script in scripts:
        for plan in plans:
            premiere = _executer(arbre, script, plan)
            seconde = _executer(arbre, script, plan)
            res[(script, plan)] = premiere if premiere == seconde else None
    return res


def _detail(a: Sortie, b: Sortie) -> str:
    morceaux = []
    if a.code != b.code:
        morceaux.append(f"code de retour {a.code} → {b.code}")
    if a.sortie != b.sortie:
        morceaux.append("sortie standard modifiée")
    if a.erreur != b.erreur:
        morceaux.append("sortie d'erreur modifiée")
    return " ; ".join(morceaux)


def _cibler(token: str, scripts: list[str]) -> list[str]:
    if "/" in token:
        return [s for s in scripts if s == token]
    cibles = []
    for s in scripts:
        nom = s.rsplit("/", 1)[-1]
        if token in (nom, nom.rsplit(".", 1)[0]):
            cibles.append(s)
    return cibles


def _declarations(racine: Path, base: str, tete: str, scripts: list[str],
                  verdict: Verdict) -> dict[str, list[str]]:
    declares: dict[str, list[str]] = {}
    for sha, message in _commits(racine, base, tete):
        for valeur in LIGNE_ECART.findall(message):
            court = sha[:7]
            m = DECLARATION.match(valeur)
            if not m:
                verdict.invalides.append(
                    f"« Ecart-admis: {valeur} » (commit {court}) : la forme est "
                    "« Ecart-admis: <script> — <raison> », la raison est obligatoire")
                continue
            token, raison = m.group(1), m.group(2)
            cibles = _cibler(token, scripts)
            if not cibles:
                verdict.invalides.append(
                    f"« Ecart-admis: {token} » (commit {court}) : aucun script de ce nom "
                    "dans _partage/scripts/")
            elif len(cibles) > 1:
                verdict.invalides.append(
                    f"« Ecart-admis: {token} » (commit {court}) : plusieurs scripts portent "
                    f"ce nom ({', '.join(cibles)}) : donner le chemin complet")
            else:
                declares.setdefault(cibles[0], []).append(f"{raison} (commit {court})")
    return declares


def analyser(racine: Path, base: str, plans_dir: Path, tete: str = "HEAD") -> Verdict:
    for ref in (base, tete):
        if not _ref_existe(racine, ref):
            raise Panne(f"la référence `{ref}` est introuvable dans ce clone")
    plans = (sorted(p.name for p in plans_dir.iterdir() if p.is_file())
             if plans_dir.is_dir() else [])
    if not plans:
        raise Panne(f"aucun plan dans {plans_dir} : rien n'est rejoué")

    verdict = Verdict(base_sha=_sha(racine, base), tete_sha=_sha(racine, tete), plans=plans)
    with tempfile.TemporaryDirectory(prefix="comparer-versions-") as tmp:
        arbre = Path(tmp)
        (arbre / "plans").mkdir()
        for nom in plans:
            shutil.copy2(plans_dir / nom, arbre / "plans" / nom)

        _preparer(racine, base, arbre)
        scripts_base = _scripts(arbre / "depot")
        _preparer(racine, tete, arbre)
        scripts_tete = _scripts(arbre / "depot")
        communs = sorted(set(scripts_base) & set(scripts_tete))
        sorties_tete = _sorties(arbre, communs, plans)
        _preparer(racine, base, arbre)
        sorties_base = _sorties(arbre, communs, plans)

    declarations = _declarations(racine, base, tete,
                                 sorted(set(scripts_base) | set(scripts_tete)), verdict)
    verdict.nouveaux = sorted(set(scripts_tete) - set(scripts_base))

    bruts: list[tuple[str, str, str]] = []  # (script, plan, détail) ; plan "" = script absent
    for script in scripts_base:
        if script not in scripts_tete:
            bruts.append((script, "", "script absent de la tête (supprimé ou déplacé)"))
            continue
        couples = [(p, sorties_base[(script, p)], sorties_tete[(script, p)]) for p in plans]
        if any(a is None or b is None for _, a, b in couples):
            verdict.instables.append(script)
            continue
        verdict.comparables.append(script)
        for plan, a, b in couples:
            if a != b:
                bruts.append((script, plan, _detail(a, b)))

    touches = {script for script, _, _ in bruts}
    for script, plan, detail in bruts:
        cible = f"{script} : {detail}" if not plan else f"{script} sur {plan} : {detail}"
        if script in declarations:
            verdict.admis.append(f"{cible} — {' ; '.join(declarations[script])}")
        else:
            verdict.ecarts.append(cible)
    verdict.inutilises = sorted(s for s in declarations if s not in touches)
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--racine", type=Path, default=REPO_ROOT)
    parser.add_argument("--base", default=os.environ.get("BASE_REF", "origin/main"),
                        help="base de la PR (défaut : $BASE_REF, sinon origin/main)")
    parser.add_argument("--tete", default="HEAD")
    parser.add_argument("--plans", type=Path, default=PLANS_PAR_DEFAUT,
                        help="dossier des plans de référence (défaut : scripts/fixtures_plans)")
    args = parser.parse_args(argv)

    try:
        verdict = analyser(args.racine, args.base, args.plans, args.tete)
    except Panne as panne:
        print(f"Sortie des scripts de _partage — comparaison impossible ({panne}). "
              "Rien n'est comparé, donc rien n'est vert : faire `git fetch origin main`, "
              "ou passer --base / BASE_REF.", file=sys.stderr)
        return 2

    print(verdict.rapport())
    return 1 if verdict.refuse() else 0


if __name__ == "__main__":
    raise SystemExit(main())
