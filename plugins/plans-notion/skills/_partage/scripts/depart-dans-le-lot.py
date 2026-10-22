#!/usr/bin/env python3
"""Un plan couvert par un plan maître ne démarre que si le ``Croisement`` du maître le permet.

Pourquoi un script : « entre plans, le parallèle est le défaut, seule une ressource
partagée ou une dépendance fait attendre » tenait à la lecture du pilote, et une
session qui ouvrait un plan seul, sans avoir lu son maître, le passait ``en cours``
pendant que le plan dont il dépend n'avait pas atterri. Le ``Statut`` = ``en cours`` d'un
plan du lot ne se pose qu'une fois ce script à 0.

Usage : depart-dans-le-lot.py <maitre.md> <Pn> --statuts "P1=en cours" "P2=pret" …
``<maitre.md>`` est le miroir de ``notion-fetch`` de la page maître ; ``<Pn>`` est
l'identifiant du plan qui veut démarrer ; ``--statuts`` donne les ``Statut`` actuels des
plans du lot, lus par une requête sur la base (jamais la colonne recopiée dans la page).

Convention de la page maître. La section « Plans » nomme chaque plan par un identifiant
``P1``, ``P2``… (une cellule du tableau). La section « Croisement » écrit chaque
contrainte en une phrase :
  - ``P3 attend P1 jusqu'à a merger`` : P3 ne démarre qu'une fois P1 au moins à ce statut
    (``execute`` si « jusqu'à » est omis : P1 est alors sur ``main``) ;
  - ``P2 exclut P4`` : P2 et P4 ne tournent pas ensemble (port e2e, base locale…) ; P2 ne
    démarre pas tant que P4 est ``en cours``, et réciproquement.
Rien d'autre ne retient un plan : le parallèle est le défaut. Un plan ``archive`` ne retient
personne.

Codes : 0 départ permis ; 1 départ refusé, un motif par ligne ; 2 entrée illisible (section
« Plans » ou « Croisement » absente, plan absent du tableau « Plans », statut manquant ou
inconnu) : lire le Croisement à la main et demander à Benjamin plutôt que démarrer.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ORDRE = ("brouillon", "en revue", "valide", "pret", "en cours", "a merger", "execute")
STATUTS = "|".join(re.escape(s) for s in ORDRE)
MARQUES = r"[\s*`_]*"
CONTRAINTE = re.compile(
    rf"\bP(\d+)\b{MARQUES}(attend|exclut){MARQUES}\bP(\d+)\b"
    rf"(?:{MARQUES}jusqu['’]à{MARQUES}({STATUTS})\b)?", re.IGNORECASE)
IDENTIFIANT = re.compile(r"\bP(\d+)\b")
H2 = re.compile(r"^##[ \t]+(.*)$")


class Illisible(Exception):
    """Entrée qui ne permet pas de contrôler (code 2)."""


def section(texte: str, nom: str) -> str:
    lignes = texte.splitlines()
    debut = next((i for i, l in enumerate(lignes)
                  if (m := H2.match(l)) and m.group(1).strip().lower().startswith(nom.lower())), None)
    if debut is None:
        raise Illisible(f"page maître : section « {nom} » absente")
    fin = next((j for j in range(debut + 1, len(lignes)) if H2.match(lignes[j])), len(lignes))
    return "\n".join(lignes[debut + 1:fin])


def lire_statuts(args: list[str]) -> dict[str, str]:
    statuts: dict[str, str] = {}
    for a in args:
        cle, sep, valeur = a.partition("=")
        cle, valeur = cle.strip().upper(), valeur.strip()
        if not sep or not re.fullmatch(r"P\d+", cle):
            raise Illisible(f"--statuts attend « Pn=statut », reçu « {a} »")
        if valeur not in ORDRE + ("archive",):
            raise Illisible(f"statut inconnu pour {cle} : « {valeur} » (valeurs sans accents : "
                            f"{', '.join(ORDRE + ('archive',))})")
        statuts[cle] = valeur
    return statuts


def refus(cible: str, croisement: str, statuts: dict[str, str]) -> list[str]:
    motifs: list[str] = []
    for m in CONTRAINTE.finditer(croisement):
        a, verbe, b = f"P{m.group(1)}", m.group(2).lower(), f"P{m.group(3)}"
        if cible not in (a, b):
            continue
        if verbe == "attend":
            if a != cible:
                continue
            seuil = (m.group(4) or "execute").lower()
            lu = statuts.get(b)
            if lu is None:
                raise Illisible(f"statut de {b} non fourni (--statuts)")
            if lu != "archive" and ORDRE.index(lu) < ORDRE.index(seuil):
                motifs.append(f"{cible} attend {b} jusqu'à `{seuil}` : {b} est `{lu}`")
        else:
            autre = b if a == cible else a
            lu = statuts.get(autre)
            if lu is None:
                raise Illisible(f"statut de {autre} non fourni (--statuts)")
            if lu == "en cours":
                motifs.append(f"{cible} et {autre} ne tournent pas ensemble : {autre} est `en cours`")
    return motifs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("maitre")
    ap.add_argument("plan")
    ap.add_argument("--statuts", nargs="+", required=True)
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 2
    cible = a.plan.strip().upper()
    try:
        texte = Path(a.maitre).read_text(encoding="utf-8")
        statuts = lire_statuts(a.statuts)
        if not re.fullmatch(r"P\d+", cible):
            raise Illisible(f"identifiant de plan attendu (P1, P2…), reçu « {a.plan} »")
        if cible not in {f"P{n}" for n in IDENTIFIANT.findall(section(texte, "Plans"))}:
            raise Illisible(f"{cible} n'est pas dans la section « Plans » de la page maître")
        motifs = refus(cible, section(texte, "Croisement"), statuts)
    except (Illisible, OSError) as erreur:
        print(f"illisible : {erreur}", file=sys.stderr)
        return 2
    if motifs:
        print("\n".join(motifs))
        return 1
    print(f"départ permis : le Croisement ne retient pas {cible}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
