#!/usr/bin/env python3
"""Porte des preuves d'un plan : chaque étape du chapitre « Exécution » est prouvée.

Pourquoi un script : la règle « une étape sans preuve n'est pas finie » ne tenait
que par la discipline du pilote. Une étape sans « Preuve de fin », ou une étape
dont le journal n'a pas de preuve rejouée, passait jusqu'au push et à la PR sans
que rien ne le voie. Le script relit la page (miroir Notion) et rend un défaut par
étape non prouvée.

Usage : preuves-des-etapes.py <page.md> (--avant | --apres)
  --avant : entre « valide » et la première étape. Chaque étape du chapitre
    « Exécution » porte une « Preuve de fin » non vide, qui n'est pas une coquille
    (« — », « - », « aucune », « à définir », « à voir », casse ignorée).
  --apres : avant le push et l'ouverture de la PR. Chaque étape a une entrée du
    « Journal d'exécution » portant « Preuve », « Commit(s) » et « Découvertes »
    non vides, et un « Verdict » : ``verified``, ou ``unverifiable — <raison>``.
Une étape écrite deux fois dans le chapitre est un défaut dans les deux modes.
Codes : 0 conforme ; 1 au moins un défaut, un par ligne sur la sortie standard
(les défauts d'abord) ; 3 (--apres seulement) aucun défaut mais une étape
``unverifiable``, une ligne « non prouvée : Étape N — <raison> » par étape ;
2 entrée illisible (page, chapitre ou journal absent, aucune étape trouvée).
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# « ### Étape 4 — titre », « ### Étape D1 — titre ». Le numéro n'exige aucune frontière
# après lui : « Étape 3bis » reste l'étape 3, et non une section ignorée sans bruit.
ETAPE = re.compile(r"^###[ \t]+étape[ \t]+(D?\d+)", re.IGNORECASE)
PREUVE_DE_FIN = re.compile(r"^[ \t]*[-*][ \t]+\*\*Preuve de fin\*\*[ \t]*:[ \t]*(.*)$")
# Une clé de champ du journal : au début de la puce, ou après un point (« … . **Commit** : »).
CHAMP = re.compile(
    r"(?:^[ \t]*[-*][ \t]+|\.[ \t]+)\*\*(Preuve|Commits?|D[ée]couvertes|Verdict)\*\*"
    r"[ \t]*(?:\([^)]*\)[ \t]*)?:")
VALEURS_VIDES = {"", "—", "-", "aucune", "à définir", "à voir"}
VERDICT = re.compile(r"\s*`?(verified|unverifiable)(?![\w-])`?(.*)$")
TIRET = re.compile(r"\s*[—–-]+\s*(.*)$")


class Illisible(Exception):
    """Entrée qui ne permet pas de contrôler (code 2)."""


def _titre(ligne: str) -> str:
    return ligne[3:].strip().replace("’", "'").lower()


def _section(texte: str, titre: str, nom: str) -> list[str]:
    """Lignes du chapitre H2 dont le titre commence par ``titre``, jusqu'au H2 suivant."""
    lignes: list[str] = []
    trouvee = dedans = False
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dedans = _titre(ligne).startswith(titre)
            trouvee = trouvee or dedans
            continue
        if dedans:
            lignes.append(ligne)
    if not trouvee:
        raise Illisible(f"chapitre « {nom} » absent")
    return lignes


def _blocs_etapes(lignes: list[str]) -> list[tuple[str, list[str]]]:
    """Découpe les sections « ### Étape <N> » ; tout autre H3 ferme la section en cours."""
    blocs: list[tuple[str, list[str]]] = []
    courant: list[str] | None = None
    for ligne in lignes:
        m = ETAPE.match(ligne)
        if m:
            courant = []
            blocs.append((m.group(1).upper(), courant))
        elif ligne.startswith("### "):
            courant = None
        elif courant is not None:
            courant.append(ligne)
    return blocs


def lire_chapitre(texte: str) -> list[tuple[str, list[str]]]:
    blocs = _blocs_etapes(_section(texte, "exécution", "Exécution"))
    if not blocs:
        raise Illisible("aucune étape trouvée sous « Exécution »")
    return blocs


def lire_journal(texte: str) -> dict[str, list[list[str]]]:
    entrees: dict[str, list[list[str]]] = {}
    lignes = _section(texte, "journal d'exécution", "Journal d'exécution")
    for numero, bloc in _blocs_etapes(lignes):
        entrees.setdefault(numero, []).append(bloc)
    return entrees


def _vide(valeur: str) -> bool:
    v = valeur.strip().strip("`*").strip().rstrip(".").strip().lower()
    return v in VALEURS_VIDES


def preuve_de_fin(bloc: list[str]) -> str:
    for ligne in bloc:
        m = PREUVE_DE_FIN.match(ligne)
        if m:
            return m.group(1)
    return ""


def _nom_champ(brut: str) -> str:
    if brut.startswith("Commit"):
        return "Commit"
    if brut.startswith("D"):
        return "Découvertes"
    return brut


def champs(bloc: list[str]) -> dict[str, str]:
    """Valeur de chaque champ du journal (première occurrence) ; une valeur va jusqu'à la clé suivante."""
    trouves: dict[str, str] = {}
    for ligne in bloc:
        cles = list(CHAMP.finditer(ligne))
        for i, m in enumerate(cles):
            fin = cles[i + 1].start() if i + 1 < len(cles) else len(ligne)
            trouves.setdefault(_nom_champ(m.group(1)), ligne[m.end():fin].strip())
    return trouves


def verdict(valeur: str) -> tuple[str | None, str]:
    """(mot, raison) : mot vaut « verified », « unverifiable », ou None (absent, hors vocabulaire)."""
    m = VERDICT.match(valeur)
    if m is None:
        return None, ""
    tiret = TIRET.match(m.group(2))
    return m.group(1), (tiret.group(1).strip() if tiret else "")


def _etiquette(numero: str) -> str:
    return f"Étape {numero}"


def _doublons(blocs: list[tuple[str, list[str]]]) -> list[str]:
    compte = Counter(numero for numero, _ in blocs)
    return [f"{_etiquette(n)} : en double dans « Exécution » ({c} fois)"
            for n, c in compte.items() if c > 1]


def controler_avant(texte: str) -> tuple[list[str], list[str], int]:
    blocs = lire_chapitre(texte)
    defauts = [f"{_etiquette(n)} : pas de preuve de fin"
               for n, bloc in blocs if _vide(preuve_de_fin(bloc))]
    defauts += _doublons(blocs)
    return defauts, [], len(dict.fromkeys(n for n, _ in blocs))


def controler_apres(texte: str) -> tuple[list[str], list[str], int]:
    blocs = lire_chapitre(texte)
    journal = lire_journal(texte)
    defauts = _doublons(blocs)
    non_prouvees: list[str] = []
    numeros = list(dict.fromkeys(n for n, _ in blocs))
    for numero in numeros:
        etiq = _etiquette(numero)
        entrees = journal.get(numero, [])
        if not entrees:
            defauts.append(f"{etiq} : pas d'entrée de journal")
            continue
        if len(entrees) > 1:
            defauts.append(f"{etiq} : deux entrées de journal")
        val = champs(entrees[0])
        for nom in ("Preuve", "Commit", "Découvertes"):
            if not val.get(nom, "").strip():
                defauts.append(f"{etiq} : pas de {nom}")
        mot, raison = verdict(val.get("Verdict", ""))
        if mot is None:
            defauts.append(f"{etiq} : Verdict absent ou hors vocabulaire")
        elif mot == "unverifiable":
            if re.search(r"\w", raison):
                non_prouvees.append(f"non prouvée : {etiq} — {raison}")
            else:
                defauts.append(f"{etiq} : unverifiable sans raison")
    return defauts, non_prouvees, len(numeros)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--avant", action="store_true",
                      help="chaque étape a une preuve de fin")
    mode.add_argument("--apres", action="store_true",
                      help="chaque étape a une entrée de journal prouvée")
    a = ap.parse_args(argv)
    try:
        texte = Path(a.page).read_text(encoding="utf-8")
        if a.avant:
            defauts, non_prouvees, n = controler_avant(texte)
        else:
            defauts, non_prouvees, n = controler_apres(texte)
    except (OSError, ValueError, Illisible) as e:
        print(f"illisible : {e}", file=sys.stderr)
        return 2
    for ligne in [*defauts, *non_prouvees]:
        print(ligne)
    if defauts:
        return 1
    if non_prouvees:
        return 3
    if a.avant:
        print(f"avant : {n} étape(s), toutes ont une preuve de fin")
    else:
        print(f"apres : {n} étape(s), toutes verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
