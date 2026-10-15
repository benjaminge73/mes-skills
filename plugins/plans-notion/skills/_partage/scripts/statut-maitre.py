#!/usr/bin/env python3
"""Statut hérité d'un plan maître, et état de son lot, calculés depuis les ``Statut`` des plans.

Pourquoi un script : le statut d'un plan maître est dérivé, et un statut dérivé
écrit de tête se périme dès que Benjamin change à la main le statut d'un plan.
Le pilote lit les ``Statut`` actuels des plans du lot (une requête sur la base,
jamais la colonne recopiée dans la page maître) et passe ce script à chaque
événement : ajout d'un plan, changement de statut, clôture.

Usage : statut-maitre.py <statut> <statut> [<statut> …]   (un argument par plan du lot)
Règle : l'ordre est brouillon < en revue < valide < pret < en cours < a merger <
execute. ``archive`` ne compte pas dans le calcul (tout archivé : ``archive``).
Dès qu'un plan est ``en cours``, le maître l'est aussi ; sinon il prend le statut du
plan le moins avancé. Le lot est ``ferme`` quand le statut est ``a merger`` ou
au-delà (aucun plan ne démarre ni n'avance plus, seules les PR attendent), sinon
``ouvert`` : un plan ne s'ajoute qu'à un lot ouvert.
Sortie : deux lignes, ``statut=<valeur>`` et ``lot=ouvert|ferme``.
Codes : 0 calculé ; 2 moins de deux plans passés, ou une valeur inconnue (une
valeur accentuée, « prêt », « exécuté », est inconnue : les valeurs sont sans accents).
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import sys

ORDRE = ("brouillon", "en revue", "valide", "pret", "en cours", "a merger", "execute")


def calculer(statuts: list[str]) -> tuple[str, str]:
    comptes = [s for s in statuts if s != "archive"]
    if not comptes:
        return "archive", "ferme"
    statut = "en cours" if "en cours" in comptes else min(comptes, key=ORDRE.index)
    return statut, "ferme" if ORDRE.index(statut) >= ORDRE.index("a merger") else "ouvert"


def main(argv: list[str] | None = None) -> int:
    statuts = [a.strip() for a in (sys.argv[1:] if argv is None else argv)]
    if len(statuts) < 2:
        print("usage : statut-maitre.py <statut> <statut> […] — un plan maître couvre au moins "
              "deux plans", file=sys.stderr)
        return 2
    inconnus = [s for s in statuts if s not in ORDRE + ("archive",)]
    if inconnus:
        print(f"valeur inconnue : {', '.join(repr(s) for s in inconnus)} — valeurs admises : "
              f"{', '.join(ORDRE + ('archive',))}", file=sys.stderr)
        return 2
    statut, lot = calculer(statuts)
    print(f"statut={statut}\nlot={lot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
