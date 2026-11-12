#!/usr/bin/env python3
"""Calcule les vagues d'un plan à partir du tableau « Étape · Fichiers · Dépend de ».

Règle de ``_partage/vagues.md`` (« Calculer les vagues ») : deux étapes vont dans
la même vague si (1) leurs fichiers sont disjoints, (2) aucune ne dépend de
l'autre, (3) aucune ne touche un même fichier partagé (config, README,
``CLAUDE.md``, ``plugin.json``, ``ci.yml``), même dans deux dossiers différents.
Une étape va dans la première vague qui suit ses dépendances et où elle ne gêne
personne. Une étape est identifiée par le numéro en tête de sa cellule : « 3 · écran »,
« D1 · sonder l'API » et « C1 — lancer le cron » sont les étapes ``3``, ``D1`` et ``C1``.

« Dépend de » s'écrit en numéros nus séparés par des virgules (« 1, 3, Q2 »,
``plan-notion/chapitres-questions-execution.md``). Le script lit aussi « étape 5 »,
« étapes 3 et 4 », « étapes 1 à 9 », une parenthèse (« étape 2 (même fichier) ») et
« ; » comme séparateur ; « toutes » veut dire toutes les autres étapes. Les questions
(``Q1``) et « — » sont ignorées sans bruit ; une autre dépendance hors tableau
(« lot 1 mergé ») est ignorée avec un avertissement sur la sortie d'erreur. Une cellule
qui cite une étape d'une façon que le script ne lit pas, ou une étape absente du
tableau, est refusée (code 2) : des vagues calculées sur une dépendance perdue sont
fausses sans que rien ne le montre.

Le tableau est lu dans les deux formats de miroir : HTML (``<table>``, celui de
``composio execute NOTION_GET_PAGE_MARKDOWN``, fichiers en accents graves) et en barres
verticales (celui de l'outil ``notion-fetch`` du connecteur de l'app, fichiers en
``<code>…</code>``).

Usage : vagues.py <page.md|tableau> [--comparer]
  imprime une ligne par vague : « Vague 1 : 1, 5, 6 » ;
  --comparer : signale (code 1) les étapes dont la colonne « Vague » diffère du
  calcul ; une colonne qui n'est pas un numéro (« L2·1 ») est signalée aussi.
Code 2 : fichier illisible, tableau absent, deux lignes au même numéro, « Dépend de »
illisible ou cycle. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import fnmatch
import html
import re
import sys

FICHIERS_PARTAGES = {"readme.md", "claude.md", "plugin.json", "ci.yml", "config.json"}
# Le bleu des retouches enveloppe le texte des cellules dans des <span color="…"> : on les retire.
SPAN = re.compile(r"</?span\b[^>]*>")


COLONNES = {"Étape", "Fichiers touchés", "Dépend de"}
# Le connecteur Notion de l'app (notion-fetch) écrit le code en <code>…</code> (constaté le 2026-11-12).
CODE_HTML = re.compile(r"<code>(.*?)</code>", re.S)
# Une cellule d'un tableau en barres : tout jusqu'à la barre suivante non échappée.
BARRE = re.compile(r"(?<!\\)\|")
SEPARATEUR = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def _cellule(brut: str) -> str:
    brut = SPAN.sub("", brut)
    brut = CODE_HTML.sub(lambda m: f"`{m.group(1)}`", brut)
    return html.unescape(brut).replace("\\|", "|").strip()


def _tableaux_html(texte: str):
    for t in re.findall(r"<table[^>]*>(.*?)</table>", texte, re.S):
        yield [[_cellule(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
               for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)]


def _tableaux_en_barres(texte: str):
    bloc: list[str] = []
    for ligne in texte.splitlines() + [""]:
        if ligne.lstrip().startswith("|"):
            bloc.append(ligne.strip())
            continue
        if bloc:
            lignes = [[_cellule(c) for c in BARRE.split(l.strip("|"))]
                      for l in bloc if not SEPARATEUR.match(l)]
            yield lignes
            bloc = []


def lire_tableau(texte: str):
    """Rend la liste de lignes ``{colonne: cellule}`` du tableau de chevauchement."""
    for lignes in (*_tableaux_html(texte), *_tableaux_en_barres(texte)):
        if lignes and COLONNES <= set(lignes[0]):
            tete = lignes[0]
            return [dict(zip(tete, l)) for l in lignes[1:] if any(l)]
    return None


def fichiers_de(cellule: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cellule)


ID = r"[CDcd]?\d+"


def numero(cellule: str) -> str:
    """« 3 · écran » → ``3``, « D1 · sonder » → ``D1``, « C1 — cron » → ``C1`` ; sinon la tête avant « · »."""
    m = re.match(rf"\s*({ID})\b", cellule)
    return m.group(1).upper() if m else cellule.split("·")[0].strip()


class Illisible(ValueError):
    """Une cellule « Dépend de » que le script ne sait pas lire sans risquer de se tromper."""


VIDES = {"", "—", "–", "-", "aucune", "aucun"}
LISTE = re.compile(rf"^(?:étapes?\s+)?({ID}(?:\s*(?:,|\bet\b|\bà\b|-|–)\s*{ID})*)$", re.I)
PLAGE = re.compile(rf"({ID})\s*(?:\bà\b|-|–)\s*({ID})", re.I)


def dependances(cellule: str, etape: str, ids: list[str]) -> tuple[list[str], list[str]]:
    """Les étapes que cite la cellule, et les dépendances hors tableau à signaler.

    Lève ``Illisible`` si la cellule cite une étape d'une façon non lue, ou une étape
    absente du tableau.
    """
    deps: list[str] = []
    hors: list[str] = []
    for brut in re.split(r"[,;]", re.sub(r"\([^)]*\)", "", cellule)):
        jeton = " ".join(brut.split())
        bas = jeton.lower()
        if bas in VIDES or re.fullmatch(r"q\d+", bas):
            continue
        if bas.startswith("toutes"):
            deps += [o for o in ids if o != etape]
            continue
        m = LISTE.match(jeton)
        if not m:
            if "étape" in bas or re.fullmatch(rf"{ID}\b.*", jeton):
                raise Illisible(
                    f"étape {etape} : « Dépend de » porte « {jeton} », que le script ne lit pas ; "
                    "écrire des numéros nus séparés par des virgules (« 1, 3, Q2 »)")
            hors.append(jeton)
            continue
        cites: list[str] = []
        reste = m.group(1)
        for a, b in PLAGE.findall(reste):
            pa, pb = re.match(r"\D*", a.upper()).group(), re.match(r"\D*", b.upper()).group()
            na, nb = int(a[len(pa):]), int(b[len(pb):])
            if pa != pb or na > nb:
                raise Illisible(f"étape {etape} : plage « {a} à {b} » illisible dans « Dépend de »")
            cites += [f"{pa}{n}" for n in range(na, nb + 1)]
        cites += [x.upper() for x in re.findall(ID, PLAGE.sub("", reste))]
        for c in cites:
            if c not in ids:
                raise Illisible(f"étape {etape} : « Dépend de » cite l'étape {c}, absente du tableau")
            if c != etape:
                deps.append(c)
    return list(dict.fromkeys(deps)), hors


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
        deps[e], hors = dependances(l["Dépend de"], e, ids)
        for h in hors:
            print(f"étape {e} : dépendance hors tableau ignorée, « {h} »", file=sys.stderr)
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
