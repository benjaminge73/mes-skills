#!/usr/bin/env python3
"""Le rapport d'un exécutant coche-t-il une case prouvée pour chaque champ de son étape ?

Pourquoi : le rapport à quatre états laissait le pilote juger « à l'œil » si la commande de
preuve était bien jouée et si le test attendu existait. Ici, chaque champ de l'étape devient
une case, et une case se coche avec sa preuve sur la même ligne. Le script ne juge pas la
vérité de la preuve (il ne rejoue rien) : il refuse une case absente, non cochée, ou cochée
sans preuve.

Usage : verifier-rapport.py --brief <fichier> --rapport <fichier>

  --brief   : le brief de l'étape. Ses champs sont les puces ``- **Champ** : valeur``, sauf les
              champs que tient le pilote (``CHAMPS_DU_PILOTE``), qui ne deviennent pas des cases.
  --rapport : le rapport de l'exécutant. Une case par ligne :
              ``- [x] <champ> — preuve : <sortie bornée ou référence>``.

Codes :
  0 chaque champ de l'étape a une case cochée avec une preuve (rien sur la sortie)
  1 au moins une case manque, n'est pas cochée, ou est cochée sans preuve : une ligne par case
    sur la sortie standard, la case nommée (« case manquante », « case non cochée »,
    « case sans preuve »)
  2 usage : option absente, fichier illisible, brief sans champ

Une preuve vide, ou faite seulement de tirets et de ponctuation (« — », « - », « ... »), compte
comme absente. Le contenu de la preuve n'est pas lu au-delà de cela.

Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OK, INCOMPLET, USAGE = 0, 1, 2

# Puces du brief : ``- **Champ** : valeur``. L'objectif, en prose, n'en est pas une.
CHAMP_DU_BRIEF = re.compile(r"^[ \t]*[-*][ \t]+\*\*(?P<champ>[^*\n]+?)\*\*[ \t]*:")
# Champs que tient le pilote (rapport-executant.md) : pas de case à cocher pour l'exécutant.
CHAMPS_DU_PILOTE = {"dépend de", "relecture", "taille", "blocs touchés"}
# Case du rapport : ``- [x] <champ>`` puis, si prouvée, `` — preuve : <preuve>``.
CASE = re.compile(r"^[ \t]*[-*][ \t]+\[(?P<coche>[ xX])\][ \t]+(?P<reste>.*?)[ \t]*$")
SEPARATEUR_PREUVE = re.compile(r"[ \t]+—[ \t]*preuve[ \t]*:[ \t]*", re.IGNORECASE)


def _normaliser(champ: str) -> str:
    """Casse, gras et espaces ignorés : « **Test attendu** » et « test  attendu » se valent."""
    return re.sub(r"\s+", " ", champ.replace("*", "")).strip().casefold()


def champs_du_brief(texte: str) -> list[str]:
    """Les champs de l'étape à prouver, dans leur ordre d'apparition, sans doublon."""
    vus: dict[str, str] = {}
    for ligne in texte.splitlines():
        m = CHAMP_DU_BRIEF.match(ligne)
        if not m:
            continue
        nom = _normaliser(m.group("champ"))
        if nom and nom not in CHAMPS_DU_PILOTE:
            vus.setdefault(nom, m.group("champ").strip())
    return list(vus.values())


def cases_du_rapport(texte: str) -> dict[str, list[tuple[bool, str | None]]]:
    """Par champ, les cases du rapport : (cochée ?, preuve ou None si absente)."""
    cases: dict[str, list[tuple[bool, str | None]]] = {}
    for ligne in texte.splitlines():
        m = CASE.match(ligne)
        if not m:
            continue
        reste = m.group("reste")
        coche = m.group("coche").lower() == "x"
        morceaux = SEPARATEUR_PREUVE.split(reste, maxsplit=1)
        champ = morceaux[0]
        preuve = morceaux[1].strip() if len(morceaux) == 2 else None
        cases.setdefault(_normaliser(champ), []).append((coche, preuve))
    return cases


def _preuve_valide(preuve: str | None) -> bool:
    """Une preuve existe si elle contient autre chose que de la ponctuation."""
    return preuve is not None and bool(re.search(r"\w", preuve))


def verifier(texte_brief: str, texte_rapport: str) -> list[str]:
    """Les défauts, un par case : vide si le rapport est complet."""
    cases = cases_du_rapport(texte_rapport)
    defauts = []
    for champ in champs_du_brief(texte_brief):
        entrees = cases.get(_normaliser(champ), [])
        if any(coche and _preuve_valide(preuve) for coche, preuve in entrees):
            continue
        if not entrees:
            defauts.append(f"case manquante : {champ}")
        elif any(coche for coche, _ in entrees):
            defauts.append(f"case sans preuve : {champ}")
        else:
            defauts.append(f"case non cochée : {champ}")
    return defauts


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(
        description="Vérifie qu'un rapport d'exécutant coche une case prouvée par champ d'étape.")
    parseur.add_argument("--brief", required=True, metavar="FICHIER",
                         help="le brief de l'étape (puces « - **Champ** : valeur »)")
    parseur.add_argument("--rapport", required=True, metavar="FICHIER",
                         help="le rapport de l'exécutant (cases « - [x] <champ> — preuve : … »)")
    args = parseur.parse_args(argv)

    try:
        texte_brief = Path(args.brief).read_text(encoding="utf-8")
        texte_rapport = Path(args.rapport).read_text(encoding="utf-8")
    except OSError as erreur:
        print(f"fichier illisible : {erreur}", file=sys.stderr)
        return USAGE

    if not champs_du_brief(texte_brief):
        print(f"aucun champ d'étape dans le brief : {args.brief}", file=sys.stderr)
        return USAGE

    defauts = verifier(texte_brief, texte_rapport)
    if defauts:
        print("\n".join(defauts))
        return INCOMPLET
    print("Toutes les cases de l'étape sont cochées avec une preuve.", file=sys.stderr)
    return OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
