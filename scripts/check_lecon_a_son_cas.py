#!/usr/bin/env python3
"""Une leçon ajoutée à un skill arrive avec son cas d'évaluation.

La règle
--------
Une PR qui touche ``plugins/<p>/skills/`` (``_partage/`` compris),
``plugins/<p>/agents/`` ou ``plugins/<p>/hooks/`` doit aussi :

- toucher ``evals/<p>/`` (un cas ajouté ou changé), **ou**
- porter, dans un de ses commits (``base..tête``), une ligne
  ``Eval-cas: <cas>`` où ``<cas>`` existe dans ``evals/<p>/`` (on peut écrire
  ``<p>/<cas>``), **ou**
- porter ``Eval-cas: aucun — <raison>``.

Pourquoi : la CI vérifie des manifestes et des renvois, jamais la justesse d'une
consigne. Sans cas, une leçon corrigée un jour peut être défaite le lendemain
sans que rien ne rougisse. Le cas, prouvé par un oracle qui passe et un témoin
nul qui échoue, est ce qui tient la leçon (voir ``docs/tester-un-skill.md``).

La dérogation est possible, jamais silencieuse : chaque
``Eval-cas: aucun — …`` est affichée sur la sortie standard, et dans
``$GITHUB_STEP_SUMMARY`` quand il est défini, pour que le relecteur la voie.

Codes de sortie : ``0`` respectée, ``1`` refusée, ``2`` panne (base illisible :
sans base, rien n'est comparé, donc rien n'est vert).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Ce qui déclenche l'exigence : le comportement livré par un plugin.
DECLENCHEUR = re.compile(r"^plugins/([^/]+)/(?:skills|agents|hooks)/")
LIGNE_EVAL_CAS = re.compile(r"^Eval-cas:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
AUCUN = re.compile(r"^aucun[ \t]*(?:—|–|--|-)[ \t]*(\S.*)$", re.IGNORECASE)


class BaseIllisible(RuntimeError):
    """La base de comparaison n'existe pas dans ce clone."""


@dataclass
class Verdict:
    refus: list[str] = field(default_factory=list)
    derogations: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)


def _git(racine: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=racine, capture_output=True, text=True)


def _commits(racine: Path, base: str, tete: str) -> list[tuple[str, str]]:
    sortie = _git(racine, "log", "--format=%H%x1f%B%x1e", f"{base}..{tete}")
    if sortie.returncode != 0:
        raise BaseIllisible(sortie.stderr.strip())
    commits = []
    for bloc in sortie.stdout.split("\x1e"):
        if "\x1f" in bloc:
            sha, message = bloc.split("\x1f", 1)
            commits.append((sha.strip(), message))
    return commits


def _cas_existe(racine: Path, tete: str, plugin: str, cas: str) -> bool:
    if "/" in cas:
        plug, _, cas = cas.partition("/")
        if plug != plugin:
            return False
    if not cas or ".." in cas or cas.startswith("/"):
        return False
    return _git(racine, "cat-file", "-e", f"{tete}:evals/{plugin}/{cas.strip('/')}").returncode == 0


def analyser(racine: Path, base: str, tete: str = "HEAD") -> Verdict:
    for ref in (base, tete):
        if _git(racine, "cat-file", "-e", f"{ref}^{{commit}}").returncode != 0:
            raise BaseIllisible(f"la référence `{ref}` est introuvable dans ce clone")

    diff = _git(racine, "diff", "--no-renames", "--name-only", f"{base}...{tete}")
    if diff.returncode != 0:
        raise BaseIllisible(diff.stderr.strip())
    fichiers = [f for f in diff.stdout.splitlines() if f]

    touches: set[str] = set()
    avec_evals: set[str] = set()
    for f in fichiers:
        m = DECLENCHEUR.match(f)
        if m:
            touches.add(m.group(1))
        if f.startswith("evals/"):
            morceaux = f.split("/")
            if len(morceaux) > 2:
                avec_evals.add(morceaux[1])

    verdict = Verdict(plugins=sorted(touches))
    if not touches:
        return verdict

    trailers: list[tuple[str, str]] = []  # (sha, valeur)
    for sha, message in _commits(racine, base, tete):
        for valeur in LIGNE_EVAL_CAS.findall(message):
            trailers.append((sha[:7], valeur))

    for plugin in sorted(touches):
        if plugin in avec_evals:
            continue
        satisfait = False
        invalides: list[str] = []
        for sha, valeur in trailers:
            aucun = AUCUN.match(valeur)
            if aucun:
                verdict.derogations.append(
                    f"plugin {plugin} : Eval-cas: aucun — {aucun.group(1)} (commit {sha})")
                satisfait = True
            elif valeur.lower().startswith("aucun"):
                invalides.append(f"« Eval-cas: {valeur} » (commit {sha}) : « aucun » demande "
                                 "une raison, « Eval-cas: aucun — <raison> »")
            elif valeur and _cas_existe(racine, tete, plugin, valeur):
                satisfait = True
            else:
                invalides.append(f"« Eval-cas: {valeur} » (commit {sha}) : aucun cas de ce nom "
                                 f"dans evals/{plugin}/")
        if not satisfait:
            message = (f"la PR touche plugins/{plugin}/ (skills, agents ou hooks) sans toucher "
                       f"evals/{plugin}/ ni porter de ligne `Eval-cas:`. Ajouter le cas d'éval de "
                       "la leçon (voir docs/tester-un-skill.md), ou une ligne "
                       "`Eval-cas: <cas existant>` / `Eval-cas: aucun — <raison>` dans un commit.")
            if invalides:
                message += " Lignes invalides : " + " ; ".join(invalides) + "."
            verdict.refus.append(message)
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--racine", type=Path, default=REPO_ROOT)
    parser.add_argument("--base", default=os.environ.get("BASE_REF", "origin/main"),
                        help="base de la PR (défaut : $BASE_REF, sinon origin/main)")
    parser.add_argument("--tete", default="HEAD")
    args = parser.parse_args(argv)

    try:
        verdict = analyser(args.racine, args.base, args.tete)
    except BaseIllisible as panne:
        print(f"Leçon a son cas — comparaison impossible ({panne}). Sans base, rien n'a été "
              "vérifié : faire `git fetch origin main`, ou passer --base / BASE_REF.",
              file=sys.stderr)
        return 2

    if verdict.derogations:
        titre = "Dérogations « Eval-cas: aucun » de cette PR"
        print(f"{titre} :")
        for d in verdict.derogations:
            print(f"  - {d}")
        resume = os.environ.get("GITHUB_STEP_SUMMARY")
        if resume:
            with open(resume, "a", encoding="utf-8") as sortie:
                sortie.write(f"### {titre}\n\n" + "".join(f"- {d}\n" for d in verdict.derogations) + "\n")

    if verdict.refus:
        print("Leçon a son cas — cette PR ne peut pas être fusionnée :\n  "
              + "\n  ".join(verdict.refus), file=sys.stderr)
        return 1

    if verdict.plugins:
        print(f"Leçon a son cas : respectée (plugins touchés : {', '.join(verdict.plugins)})")
    else:
        print("Leçon a son cas : rien d'exigé (la PR ne touche ni skills, ni agents, ni hooks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
