#!/usr/bin/env python3
"""Quels fichiers du dépôt citent un fichier touché par le plan, et lesquels changent avec lui ?

Pourquoi : avant d'écrire un plan, l'enquêteur doit savoir ce qui dépend des fichiers que le plan va toucher (une
doc qui les décrit, un cron qui les lance, un test qui les importe). Une recherche de texte seule ramène trop de
bruit ; le co-change (deux fichiers modifiés dans les mêmes commits) dit lequel compte vraiment. Ce script ne lit
que git, en lecture seule, et ne rejoue rien.

Usage : releve-voisins.py --depot <chemin> --fichiers <liste> [--max 40]

  --depot    : un dépôt git (worktree ou clone). Le relevé porte sur son commit courant (HEAD) : ni les commits
               d'une autre branche, ni les modifications non commitées ne comptent.
  --fichiers : les chemins touchés par le plan, relatifs à la racine du dépôt. Séparés par des espaces, des
               virgules, ou les deux.
  --max      : nombre de voisins gardés (défaut 40).

Pour chaque fichier touché, le script cherche par `git grep -F` le chemin et le nom du fichier (et sa racine si
elle dépasse 5 caractères) au commit courant. Chaque fichier qui cite est classé par sa confiance de co-change :
la part des commits du fichier touché où il figure aussi. Les commits de plus de 20 fichiers ne comptent pas.

Sortie : une ligne Markdown par voisin, du plus au moins lié :
  <chemin> (<type>) — cite <objet> l.<n>[, …] — co-change <confiance>
<type> : doc, code, config ou test. <confiance> : la plus grande part de co-change parmi les fichiers touchés.
Le classement, lui, suit la somme de ces parts, comme `enquete.py releve` : la mesure du banc vaut pour ce script.

Codes :
  0 relevé rendu (sortie sur la sortie standard ; aucun voisin : sortie vide, une note sur l'erreur standard)
  2 usage : dépôt absent ou pas un dépôt git, liste de fichiers vide

Bibliothèque standard uniquement. git est appelé en lecture seule.
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import subprocess
import sys

OK, USAGE = 0, 2

REV = "HEAD"
COMMIT_MAX = 20  # au-delà, un commit est un « fourre-tout » : il ne compte pas dans le co-change
TOP_DEFAUT = 40
OCCURRENCES_MAX = 5  # citations affichées par voisin, le reste se résume en « … »

TYPES_TEST = re.compile(r"(^|/)test_[^/]*$|_test\.[^/]*$|(^|/)tests?/")
TYPES_DOC = {".md", ".rst", ".txt"}
TYPES_CONFIG = {".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".service", ".timer", ".j2"}


def git(depot: str, *args: str) -> str:
    """La sortie de git dans le dépôt, en lecture seule. Une erreur de git rend chaîne vide."""
    r = subprocess.run(["git", "-C", depot, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def type_de(chemin: str) -> str:
    """doc, code, config ou test, d'après le chemin seul (le contenu n'est pas lu)."""
    if TYPES_TEST.search(chemin):
        return "test"
    extension = os.path.splitext(chemin)[1].lower()
    if extension in TYPES_DOC or chemin.split("/", 1)[0] in {"docs", "doc"}:
        return "doc"
    if extension in TYPES_CONFIG:
        return "config"
    return "code"


def motifs_de(chemin: str) -> list[str]:
    """Le nom du fichier, et sa racine si elle dépasse 5 caractères (« a.py » : seul le nom sert)."""
    nom = os.path.basename(chemin)
    racine = nom.rsplit(".", 1)[0]
    return [nom, racine] if len(racine) > 5 and racine != nom else [nom]


def citations(depot: str, touches: set[str]) -> dict[str, list[tuple[str, int]]]:
    """Par fichier qui cite un fichier touché : les (objet cité, numéro de ligne), sans doublon."""
    out: dict[str, list[tuple[str, int]]] = collections.defaultdict(list)
    for touche in sorted(touches):
        for motif in motifs_de(touche):
            sortie = git(depot, "grep", "-n", "-F", "-e", motif, REV)
            for ligne in sortie.splitlines():
                # Forme : « HEAD:<chemin>:<ligne>:<contenu> ».
                reste = ligne[len(REV) + 1:] if ligne.startswith(REV + ":") else ligne
                parties = reste.split(":", 2)
                if len(parties) < 2 or not parties[1].isdigit():
                    continue
                chemin, numero = parties[0], int(parties[1])
                if chemin in touches:
                    continue
                # Une ligne qui cite à la fois le nom et la racine ne compte qu'une fois : le premier objet l'emporte.
                if numero not in {n for _, n in out[chemin]}:
                    out[chemin].append((motif, numero))
    return out


def commits_de(depot: str, chemin: str) -> list[set[str]]:
    """Les fichiers de chaque commit qui touche le chemin, dans l'historique de HEAD."""
    sortie = git(depot, "log", "--format=format:@@", "--name-only", "--full-diff", REV, "--", chemin)
    commits: list[set[str]] = []
    for ligne in sortie.splitlines():
        if ligne == "@@":
            commits.append(set())
        elif ligne.strip() and commits:
            commits[-1].add(ligne)
    return commits


def cochange(depot: str, touches: set[str]) -> tuple[collections.Counter, collections.Counter]:
    """Par fichier : (somme des parts de co-change, plus grande part). Les parts sont celles de chaque fichier touché."""
    somme: collections.Counter = collections.Counter()
    plus_grande: collections.Counter = collections.Counter()
    for touche in touches:
        commits = commits_de(depot, touche)
        n = len(commits)
        if not n:
            continue
        compte: collections.Counter = collections.Counter()
        for fichiers in commits:
            if len(fichiers) > COMMIT_MAX:
                continue
            for p in fichiers - touches:
                compte[p] += 1
        for p, c in compte.items():
            part = c / n
            somme[p] += part
            plus_grande[p] = max(plus_grande[p], part)
    return somme, plus_grande


def citations_en_texte(occurrences: list[tuple[str, int]]) -> str:
    """« a.py l.3, l.9 ; a l.5 » : groupé par objet cité, dans l'ordre d'apparition."""
    groupes: dict[str, list[int]] = collections.OrderedDict()
    for objet, numero in occurrences[:OCCURRENCES_MAX]:
        groupes.setdefault(objet, []).append(numero)
    texte = " ; ".join(f"{objet} " + ", ".join(f"l.{n}" for n in numeros) for objet, numeros in groupes.items())
    return texte + (", …" if len(occurrences) > OCCURRENCES_MAX else "")


def releve(depot: str, touches: set[str], maximum: int) -> list[str]:
    """Les lignes Markdown du relevé, du voisin le plus lié au moins lié."""
    cites = citations(depot, touches)
    somme, plus_grande = cochange(depot, touches)
    classes = sorted(cites, key=lambda p: (-round(somme[p], 3), -len(cites[p]), p))[:maximum]
    return [
        f"{p} ({type_de(p)}) — cite {citations_en_texte(cites[p])} — co-change {round(100 * plus_grande[p])} %"
        for p in classes
    ]


def construire_parseur() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Relevé des voisins d'un plan : qui cite les fichiers touchés, et co-change.")
    ap.add_argument("--depot", required=True, metavar="CHEMIN", help="le dépôt git (worktree ou clone)")
    ap.add_argument("--fichiers", required=True, nargs="+", metavar="FICHIER",
                    help="les chemins touchés, relatifs à la racine du dépôt (espaces ou virgules)")
    ap.add_argument("--max", type=int, default=TOP_DEFAUT, metavar="N", help="voisins gardés (défaut 40)")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = construire_parseur().parse_args(argv)
    touches = {f.strip().removeprefix("./") for x in a.fichiers for f in x.split(",") if f.strip()}
    if not touches:
        print("refus : aucune liste de fichiers (--fichiers).", file=sys.stderr)
        return USAGE
    if not git(a.depot, "rev-parse", "--verify", "-q", REV).strip():
        print(f"refus : {a.depot} n'est pas un dépôt git avec un commit HEAD.", file=sys.stderr)
        return USAGE
    lignes = releve(a.depot, touches, a.max)
    if lignes:
        print("\n".join(lignes))
    else:
        print("aucun voisin : aucun fichier ne cite les fichiers touchés au commit courant.", file=sys.stderr)
    return OK


if __name__ == "__main__":
    sys.exit(main())
