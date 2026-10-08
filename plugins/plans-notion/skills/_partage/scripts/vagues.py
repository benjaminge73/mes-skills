#!/usr/bin/env python3
"""Calcule les vagues d'un plan à partir du tableau « Étape · Fichiers · Dépend de ».

Règle de ``_partage/vagues.md`` (« Calculer les vagues ») : deux étapes vont dans
la même vague si (1) leurs fichiers sont disjoints, (2) aucune ne dépend de
l'autre, (3) aucune ne touche un même fichier partagé (config, README,
``CLAUDE.md``, ``plugin.json``, ``ci.yml``), même dans deux dossiers différents.
Une étape va dans la première vague qui suit ses dépendances et où elle ne gêne
personne. Les dépendances qui ne sont pas des étapes du tableau (``Q1``, ``—``,
« lot 1 mergé ») sont ignorées ; « toutes » veut dire toutes les autres étapes.
Une étape est identifiée par le numéro en tête de sa cellule : « 3 · écran » et
« D1 · sonder l'API » sont les étapes ``3`` et ``D1``, que « Dépend de » cite seuls.

Usage : vagues.py <page.md|tableau> [--comparer]
  imprime une ligne par vague : « Vague 1 : 1, 5, 6 » ;
  --comparer : signale (code 1) les étapes dont la colonne « Vague » diffère du
  calcul ; une colonne qui n'est pas un numéro (« L2·1 ») est signalée aussi.
Code 2 : fichier illisible, tableau absent, deux lignes au même numéro ou cycle. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import fnmatch
import html
import re
import sys

FICHIERS_PARTAGES = {"readme.md", "claude.md", "plugin.json", "ci.yml", "config.json"}


def lire_tableau(texte: str):
    """Rend la liste de lignes ``{colonne: cellule}`` du tableau de chevauchement."""
    for t in re.findall(r"<table[^>]*>(.*?)</table>", texte, re.S):
        lignes = [[html.unescape(c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
                  for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)]
        if lignes and {"Étape", "Fichiers touchés", "Dépend de"} <= set(lignes[0]):
            tete = lignes[0]
            return [dict(zip(tete, l)) for l in lignes[1:] if l]
    return None


def fichiers_de(cellule: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cellule)


def numero(cellule: str) -> str:
    """« 3 · écran » → ``3``, « D1 · sonder » → ``D1`` ; sinon la tête avant « · »."""
    m = re.match(r"\s*(D?\d+)\b", cellule)
    return m.group(1) if m else cellule.split("·")[0].strip()


def se_recouvrent(a: str, b: str) -> bool:
    return a == b or fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)


def partage(chemin: str) -> bool:
    return chemin.rsplit("/", 1)[-1].lower() in FICHIERS_PARTAGES


def en_conflit(fa: list[str], fb: list[str]) -> bool:
    for x in fa:
        for y in fb:
            if se_recouvrent(x, y):
                return True
            if partage(x) and partage(y) and x.rsplit("/", 1)[-1].lower() == y.rsplit("/", 1)[-1].lower():
                return True
    return False


def calculer(lignes) -> dict[str, int]:
    ids = [numero(l["Étape"]) for l in lignes]
    doublons = sorted({e for e in ids if ids.count(e) > 1})
    if doublons:
        raise ValueError("plusieurs lignes portent l'étape " + ", ".join(doublons))
    fichiers = {numero(l["Étape"]): fichiers_de(l["Fichiers touchés"]) for l in lignes}
    deps = {}
    for l in lignes:
        e = numero(l["Étape"])
        bruts = [numero(x) for x in l["Dépend de"].split(",")]
        d = [x for x in bruts if x in ids and x != e]
        if any(x.lower() == "toutes" for x in bruts):  # « toutes » : toutes les autres étapes
            d += [o for o in ids if o != e and o not in d]
        deps[e] = d
    vague: dict[str, int] = {}
    restantes = list(ids)
    while restantes:
        progres = False
        for e in list(restantes):
            if any(d not in vague for d in deps[e]):
                continue
            n = 1 + max((vague[d] for d in deps[e]), default=0)
            while any(vague.get(o) == n and en_conflit(fichiers[e], fichiers[o]) for o in vague):
                n += 1
            vague[e] = n
            restantes.remove(e)
            progres = True
        if not progres:  # cycle de dépendances : on ne devine pas
            raise ValueError("cycle de dépendances entre " + ", ".join(restantes))
    return vague


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    ap.add_argument("--comparer", action="store_true")
    a = ap.parse_args(argv)
    try:
        texte = open(a.page, encoding="utf-8").read()
    except OSError as e:
        print(f"illisible : {e}", file=sys.stderr)
        return 2
    lignes = lire_tableau(texte)
    if not lignes:
        print("aucun tableau « Étape · Fichiers touchés · Dépend de » trouvé", file=sys.stderr)
        return 2
    try:
        vague = calculer(lignes)
    except ValueError as e:
        print(f"impossible : {e}", file=sys.stderr)
        return 2
    for n in sorted(set(vague.values())):
        print(f"Vague {n} : " + ", ".join(e for e in (numero(l["Étape"]) for l in lignes) if vague[e] == n))
    if not a.comparer:
        return 0
    ecarts = []
    for l in lignes:
        e, col = numero(l["Étape"]), l.get("Vague", "")
        if col != str(vague[e]):
            ecarts.append(f"étape {e} : vague calculée {vague[e]}, colonne « {col} »")
    print("\n".join(ecarts))
    return 1 if ecarts else 0


if __name__ == "__main__":
    sys.exit(main())
