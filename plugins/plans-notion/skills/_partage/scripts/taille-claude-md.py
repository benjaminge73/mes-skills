#!/usr/bin/env python3
"""Compte les lignes des ``CLAUDE.md`` d'un dépôt et refuse celui qui grossit trop.

Pourquoi un script : Claude Code charge chaque ``CLAUDE.md`` en entier à chaque
session, et la doc officielle vise moins de 200 lignes par fichier. Un fichier
plus long ne casse rien, mais il consomme du contexte à chaque session et ses
premières règles se diluent. Le script mesure ; le rangement se fait d'après
``ranger-claude-md.md``.

Ce qui est compté, chaque fichier à part :
  - chaque ``CLAUDE.md`` du dépôt (racine et sous-dossiers) ;
  - chaque ``.claude/rules/**/*.md`` ;
  - chaque fichier importé par ``@chemin`` dans l'un des précédents, en
    récursif (profondeur 5, comme la doc). Un import n'est compté que dans sa
    propre ligne de rapport, jamais dans le fichier qui l'importe.

Plafond : 200 lignes, ou la taille du même fichier sur la base (``--base``) si
elle est plus grande. C'est un cliquet : on ne fait pas grossir un fichier au-delà
de ce qu'il pèse déjà sur la base. Sans ``--base``, rien à comparer : au-delà de
200 lignes, le fichier donne un avertissement et le code reste 0.

Usage : taille-claude-md.py [--racine <dossier>] [--base <réf git>]
Sortie : une ligne par fichier, ``<chemin> <lignes> / <plafond> <verdict>``.
Verdict : ``OK``, ``AVERT`` (sans base, au-delà de 200) ou ``REFUS`` (avec base).
Codes : 0 rien à refuser, 1 au moins un REFUS, 2 base introuvable ou racine absente.
Bibliothèque standard uniquement ; git est requis si ``--base`` est donné.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PLAFOND = 200
PROFONDEUR_MAX = 5
EXCLUS = {".git", "node_modules", ".venv", "venv", "__pycache__"}
IMPORT = re.compile(r"(?<!\S)@(\S+)")
CLOTURE = re.compile(r"^\s*(```|~~~)")


def est_a_compter(rel: tuple[str, ...]) -> bool:
    if rel[-1] == "CLAUDE.md":
        return True
    # .claude/rules/**/*.md
    return rel[-1].endswith(".md") and any(
        rel[i] == ".claude" and rel[i + 1] == "rules" for i in range(len(rel) - 2))


def fichiers_du_depot(racine: Path) -> list[Path]:
    trouves = []
    for dossier, sous_dossiers, fichiers in os.walk(racine):
        sous_dossiers[:] = [d for d in sous_dossiers if d not in EXCLUS]
        for nom in fichiers:
            chemin = Path(dossier, nom)
            if est_a_compter(chemin.relative_to(racine).parts):
                trouves.append(chemin)
    return trouves


def importes(fichier: Path, racine: Path) -> list[Path]:
    """Fichiers ``@chemin`` cités hors bloc de code, s'ils existent dans le dépôt."""
    trouves = []
    dans_cloture = False
    for ligne in fichier.read_text(encoding="utf-8", errors="replace").splitlines():
        if CLOTURE.match(ligne):
            dans_cloture = not dans_cloture
            continue
        if dans_cloture:
            continue
        for m in IMPORT.finditer(ligne):
            cible = (fichier.parent / m.group(1)).resolve()
            if cible.is_file() and cible.is_relative_to(racine):
                trouves.append(cible)
    return trouves


def a_compter(racine: Path) -> list[Path]:
    """Les fichiers de cadrage et tout ce qu'ils importent, chacun une seule fois."""
    vus: list[Path] = []
    a_voir = [(f, 0) for f in fichiers_du_depot(racine)]
    while a_voir:
        fichier, profondeur = a_voir.pop(0)
        if fichier in vus:
            continue
        vus.append(fichier)
        if profondeur < PROFONDEUR_MAX:
            a_voir.extend((cible, profondeur + 1) for cible in importes(fichier, racine))
    return sorted(vus)


def compter_lignes(texte: str) -> int:
    return len(texte.splitlines())


def base_existe(racine: Path, base: str) -> bool:
    r = subprocess.run(
        ["git", "-C", str(racine), "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
        capture_output=True)
    return r.returncode == 0


def lignes_sur_la_base(racine: Path, base: str, fichier: Path) -> int | None:
    """Lignes du même fichier sur la base, ou None s'il n'y existe pas."""
    rel = fichier.relative_to(racine).as_posix()
    r = subprocess.run(["git", "-C", str(racine), "show", f"{base}:./{rel}"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return compter_lignes(r.stdout.decode("utf-8", errors="replace"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--racine", type=Path, default=Path("."))
    parser.add_argument("--base", default=None,
                        help="référence git dont on lit la taille des fichiers (cliquet)")
    args = parser.parse_args(argv)

    racine = args.racine.resolve()
    if not racine.is_dir():
        print(f"taille-claude-md : racine absente ({racine}).", file=sys.stderr)
        return 2
    if args.base is not None and not base_existe(racine, args.base):
        print(f"taille-claude-md : base « {args.base} » introuvable dans ce dépôt.",
              file=sys.stderr)
        return 2

    refus = False
    for fichier in a_compter(racine):
        lignes = compter_lignes(fichier.read_text(encoding="utf-8", errors="replace"))
        rel = fichier.relative_to(racine).as_posix()
        if args.base is None:
            plafond = PLAFOND
            verdict = "AVERT" if lignes > PLAFOND else "OK"
        else:
            sur_la_base = lignes_sur_la_base(racine, args.base, fichier)
            plafond = PLAFOND if sur_la_base is None else max(PLAFOND, sur_la_base)
            verdict = "REFUS" if lignes > plafond else "OK"
        refus = refus or verdict == "REFUS"
        print(f"{rel} {lignes} / {plafond} {verdict}")
    return 1 if refus else 0


if __name__ == "__main__":
    raise SystemExit(main())
