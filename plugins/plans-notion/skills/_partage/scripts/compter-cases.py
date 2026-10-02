#!/usr/bin/env python3
"""Recompte les cases cochées (``- [x]``) de chaque question d'une page Notion.

Pourquoi un script : le relevé des réponses se faisait à l'œil, et une case en
plus ou en moins fausse tout ce qui en découle. La page est une sortie de
``notion-fetch``. Sous le H2 « Questions ouvertes », chaque H3 portant un « Qn »
est une question ; on compte ses lignes ``- [x]`` (indentation libre, dans un
``<callout>``) jusqu'au H3 ou H2 suivant.

Usage : compter-cases.py <page.md> [--releve <releve.json>]
  sans --releve : imprime le relevé (JSON {"Q1": 1, …}) puis « total : n » ;
  avec --releve : compare ; 0 si identique, 1 sinon, une ligne par écart.
Code 2 : fichier illisible ou section « Questions ouvertes » absente.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

CASE = re.compile(r"^\s*- \[[xX]\]")
QUESTION = re.compile(r"^###\s+.*?\b(Q\d+)\b")


def compter(texte: str) -> dict[str, int]:
    comptes: dict[str, int] = {}
    dans_section, courante = False, None
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dans_section = ligne[3:].strip().lower().startswith("questions ouvertes")
            courante = None
            continue
        if not dans_section:
            continue
        if ligne.startswith("### "):
            m = QUESTION.match(ligne)
            courante = m.group(1) if m else None
            if courante:
                comptes.setdefault(courante, 0)
            continue
        if courante and CASE.match(ligne):
            comptes[courante] += 1
    return comptes


def _cle(q: str) -> int:
    return int(q[1:])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    ap.add_argument("--releve")
    a = ap.parse_args(argv)
    try:
        texte = open(a.page, encoding="utf-8").read()
        releve = json.load(open(a.releve, encoding="utf-8")) if a.releve else None
    except (OSError, ValueError) as e:
        print(f"illisible : {e}", file=sys.stderr)
        return 2
    comptes = compter(texte)
    if not comptes:
        print("aucune question trouvée sous « Questions ouvertes »", file=sys.stderr)
        return 2
    if releve is None:
        print(json.dumps(dict(sorted(comptes.items(), key=lambda kv: _cle(kv[0])))))
        print(f"total : {sum(comptes.values())}")
        return 0
    ecarts = []
    for q in sorted(set(comptes) | set(releve), key=_cle):
        n, r = comptes.get(q, 0), releve.get(q, 0)
        if n == r:
            continue
        sens = "une case en plus" if n > r else "une case en moins"
        if abs(n - r) > 1:
            sens = f"{abs(n - r)} cases d'écart"
        ecarts.append(f"{q} : {n} cochées, relevé {r} — {sens}")
    print("\n".join(ecarts))
    return 1 if ecarts else 0


if __name__ == "__main__":
    sys.exit(main())
