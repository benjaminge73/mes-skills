#!/usr/bin/env python3
"""Contrôle la forme d'une entrée de changelog : le H2 « Récap » d'une page de plan,
ou une entrée du Changelog du projet (le même format).

Pourquoi un script : le récap est lu par quelqu'un qui n'ouvrira pas le plan. Une
rubrique oubliée, une ligne sans source, une date absente ne se voient pas à l'œil
dans une page longue ; ça se compte. Même principe que ``compter-cases.py``.

Usage : controle-changelog.py <entree.md>
  Lit la première section dont le titre H2 commence par « Récap » (casse indifférente)
  ou par une date (AAAA-MM-JJ ou JJ/MM/AAAA : l'en-tête d'une entrée du Changelog du hub,
  « ## AAAA-MM-JJ · titre »), jusqu'au prochain titre H1 ou H2. Les sections suivantes
  ne sont pas contrôlées. Vérifie :
  - l'en-tête (le H2 et les lignes avant la première rubrique) porte une date ISO
    (AAAA-MM-JJ) ou JJ/MM/AAAA ;
  - les quatre rubriques sont présentes, dans l'ordre : Nouveau, Amélioré, Corrigé,
    Reste à faire. Une rubrique se reconnaît à son libellé, en titre ou en gras, avec
    ou sans son emoji ;
  - chaque rubrique a du contenu ; « rien » suffit ;
  - chaque ligne de « Nouveau » ou « Amélioré » (ou toute ligne commençant par ✨ ou 🔧)
    finit par une source entre parenthèses qui cite « Étape N » ou « preuve : ».
    Une ligne « rien » n'en demande pas.
  Le corps d'une rubrique s'arrête au titre suivant, à tout autre titre, ou à un
  ``<details>`` (le bloc « Côté technique »).

Sortie : sans défaut, rien. Sinon un défaut par ligne sur la sortie standard, avec son
numéro de ligne.
Codes : 0 conforme ; 1 défauts ; 2 entrée illisible ou aucune entrée (« Récap » ni date
en tête de H2) trouvée (le motif part sur la sortie d'erreur).
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import re
import sys

RUBRIQUES = ("Nouveau", "Amélioré", "Corrigé", "Reste à faire")
RUBRIQUES_A_SOURCER = ("Nouveau", "Amélioré")

TITRE_RUBRIQUE = re.compile(
    r"^(?:#{1,6}\s+|\*\*)\s*(?:[✨🔧🐛⏭]️?\s*)?\**\s*"
    r"(Nouveau|Amélioré|Corrigé|Reste à faire)\b"
)
TITRE_HAUT = re.compile(r"^#{1,2}\s")
TITRE = re.compile(r"^#{1,6}\s")
PUCE_DE_LIGNE = re.compile(r"^\s*(?:[-*]\s+)?[✨🔧]")
PUCE = re.compile(r"^[\s\-*•]+")
SOURCE = re.compile(
    r"\((?=[^()]*(?:étape\s+\d+|preuve\s*:))[^()]*\)\s*$", re.IGNORECASE
)
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b")


def _contenu(ligne: str) -> str:
    """Le texte d'une ligne sans sa puce ni ses espaces ; vide si la ligne ne dit rien."""
    return PUCE.sub("", ligne).strip()


def _ouvre_une_entree(ligne: str) -> bool:
    """Vrai si la ligne ouvre une entrée : un H2 « Récap », ou un H2 qui commence par une date."""
    if not ligne.startswith("## "):
        return False
    titre = ligne[3:].strip()
    return titre.lower().startswith("récap") or DATE.match(titre) is not None


def _section_recap(lignes: list[str]) -> tuple[int, int] | None:
    """Indices (début, fin exclue) de la première entrée, ou None si elle est absente."""
    debut = None
    for i, ligne in enumerate(lignes):
        if debut is None:
            if _ouvre_une_entree(ligne):
                debut = i
        elif TITRE_HAUT.match(ligne):
            return debut, i
    return None if debut is None else (debut, len(lignes))


def controler(texte: str) -> list[str]:
    """Renvoie la liste des défauts ; lève ValueError si aucune entrée n'est trouvée."""
    lignes = texte.splitlines()
    borne = _section_recap(lignes)
    if borne is None:
        raise ValueError("section « Récap » ou entrée datée (## AAAA-MM-JJ) absente")
    debut, fin = borne

    titres = []  # (indice, libellé) de chaque rubrique, dans l'ordre du document
    for i in range(debut + 1, fin):
        m = TITRE_RUBRIQUE.match(lignes[i])
        if m:
            titres.append((i, m.group(1)))

    defauts = []
    premier = titres[0][0] if titres else fin
    entete = "\n".join(lignes[debut:premier])
    if not DATE.search(entete):
        defauts.append(f"ligne {debut + 1} : en-tête sans date (AAAA-MM-JJ ou JJ/MM/AAAA)")

    libelles = [libelle for _, libelle in titres]
    for r in RUBRIQUES:
        if r not in libelles:
            defauts.append(f"rubrique « {r} » absente")
        elif libelles.count(r) > 1:
            defauts.append(f"rubrique « {r} » en double")
    vues = list(dict.fromkeys(libelles))
    if vues != [r for r in RUBRIQUES if r in vues]:
        defauts.append("rubriques dans le désordre : " + " · ".join(vues))

    for k, (i, libelle) in enumerate(titres):
        fin_corps = titres[k + 1][0] if k + 1 < len(titres) else fin
        corps = []
        for j in range(i + 1, fin_corps):
            if lignes[j].startswith("<details") or TITRE.match(lignes[j]):
                break
            corps.append(j)

        if not any(_contenu(lignes[j]) for j in corps):
            defauts.append(f"ligne {i + 1} : rubrique « {libelle} » vide (écrire « rien » si rien à dire)")

        for j in corps:
            texte_ligne = _contenu(lignes[j])
            if not texte_ligne or texte_ligne.lower().rstrip(".") == "rien":
                continue
            demande_source = libelle in RUBRIQUES_A_SOURCER or PUCE_DE_LIGNE.match(lignes[j])
            if demande_source and not SOURCE.search(lignes[j]):
                defauts.append(
                    f"ligne {j + 1} : ligne sans source "
                    "(Étape N ou preuve : entre parenthèses, en fin de ligne)"
                )
    return defauts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("entree")
    a = ap.parse_args(argv)
    try:
        with open(a.entree, encoding="utf-8") as f:
            texte = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"illisible : {e}", file=sys.stderr)
        return 2
    try:
        defauts = controler(texte)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    for defaut in defauts:
        print(defaut)
    return 1 if defauts else 0


if __name__ == "__main__":
    sys.exit(main())
