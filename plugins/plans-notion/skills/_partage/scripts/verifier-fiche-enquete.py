#!/usr/bin/env python3
"""La fiche de l'enquêteur recopie-t-elle chaque case de la liste d'enquête, avec sa preuve ou son marqueur ?

Pourquoi : l'enquêteur joue treize vérifications avant qu'un plan s'écrive. Sans contrôle, une case
peut se cocher sans rien montrer, ou disparaître de la fiche sans que personne le voie. Ici, le
nombre de cases et leurs identifiants viennent de la liste (jamais codés en dur), et le script ne
juge que la forme : il ne rejoue aucune preuve.

Usage : verifier-fiche-enquete.py --fiche <fichier> [--liste <fichier>]

  --fiche : la fiche de l'enquêteur, en texte, ou la sortie JSON de ``claude -p`` (champ ``result``).
            Une case par ligne : ``- [x] C<n> … — preuve : <preuve>`` si cochée, ou
            ``- [ ] C<n> … — sans objet : <raison>`` / ``— non vérifié : <raison>`` si non cochée.
  --liste : la liste d'enquête (défaut : ``listes/enquete.md`` à côté du dossier ``scripts/``).
            Ses cases sont les lignes ``- [ ] C<n> …``.

Codes :
  0 fiche complète : chaque case de la liste a une entrée valide dans la fiche
  1 au moins une case fautive : une ligne par case sur la sortie standard, nommant la case
    (« C3 cochée sans preuve… », « C7 absente de la fiche », « C2 non cochée sans … »)
  2 usage : option absente, fichier illisible, liste sans aucune case

Signalement sans refus : une case cochée dont la preuve dit « non vérifié » (insensible à la casse ;
« non verifie » sans accent compte aussi) est nommée sur la sortie standard, sur une ligne
« preuve partielle : C6 » (plusieurs cases : « preuve partielle : C6, C8 », dans l'ordre de la liste).
Cette ligne ne change pas le code de sortie : elle s'imprime en 0 comme en 1.

Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

OK, INCOMPLET, USAGE = 0, 1, 2

LISTE_PAR_DEFAUT = Path(__file__).resolve().parents[1] / "listes" / "enquete.md"

# Case de la liste : ``- [ ] C<n> …`` (l'état coché n'a pas de sens dans la liste, on le tolère).
CASE_DE_LISTE = re.compile(r"^[ \t]*[-*][ \t]+\[[ xX]\][ \t]+(?P<id>C\d+)\b")
# Case de la fiche : ``- [x] C<n> …`` ou ``- [ ] C<n> …``, avec le reste de la ligne.
CASE_DE_FICHE = re.compile(
    r"^[ \t]*[-*][ \t]+\[(?P<coche>[ xX])\][ \t]+(?P<id>C\d+)\b(?P<reste>.*)$")
# Preuve d'une case cochée : ``— preuve :`` suivi d'un contenu qui n'est pas que ponctuation.
PREUVE = re.compile(r"[ \t]+—[ \t]*preuve[ \t]*:[ \t]*(?P<preuve>.*)", re.IGNORECASE)
# Marqueur d'une case non cochée : ``sans objet :`` ou ``non vérifié :``, avec une raison.
MARQUEUR = re.compile(
    r"(?:sans objet|non v[ée]rifi[ée])[ \t]*:[ \t]*(?P<raison>.*)", re.IGNORECASE)
# Preuve qui avoue un trou : « non vérifié » n'importe où dans la preuve d'une case cochée.
PREUVE_PARTIELLE = re.compile(r"non[ \t]+v[ée]rifi[ée]", re.IGNORECASE)


def cases_de_la_liste(texte: str) -> list[str]:
    """Les identifiants de cases de la liste, dans leur ordre, sans doublon."""
    vus: dict[str, None] = {}
    for ligne in texte.splitlines():
        m = CASE_DE_LISTE.match(ligne)
        if m:
            vus.setdefault(m.group("id"), None)
    return list(vus)


def lire_fiche(texte: str) -> str:
    """Le texte de la fiche : le champ ``result`` si c'est une sortie JSON de ``claude -p``, sinon le texte."""
    try:
        donnee = json.loads(texte)
    except ValueError:
        return texte
    if isinstance(donnee, dict) and isinstance(donnee.get("result"), str):
        return donnee["result"]
    return texte


def entrees_de_la_fiche(texte: str) -> dict[str, tuple[bool, str]]:
    """Par identifiant, la première case de la fiche : (cochée ?, reste de la ligne)."""
    entrees: dict[str, tuple[bool, str]] = {}
    for ligne in texte.splitlines():
        m = CASE_DE_FICHE.match(ligne)
        if m:
            entrees.setdefault(m.group("id"), (m.group("coche").lower() == "x", m.group("reste")))
    return entrees


def _preuve_valide(reste: str) -> bool:
    """La case cochée porte « — preuve : » suivi d'un contenu, pas seulement de ponctuation."""
    m = PREUVE.search(reste)
    return m is not None and bool(re.search(r"\w", m.group("preuve")))


def _marqueur_valide(reste: str) -> bool:
    """La case non cochée porte « sans objet : » ou « non vérifié : » suivi d'une raison."""
    m = MARQUEUR.search(reste)
    return m is not None and bool(re.search(r"\w", m.group("raison")))


def verifier(texte_liste: str, texte_fiche: str) -> list[str]:
    """Les défauts, un par case de la liste : vide si la fiche est complète."""
    entrees = entrees_de_la_fiche(texte_fiche)
    defauts = []
    for identifiant in cases_de_la_liste(texte_liste):
        if identifiant not in entrees:
            defauts.append(f"{identifiant} absente de la fiche")
            continue
        coche, reste = entrees[identifiant]
        if coche and not _preuve_valide(reste):
            defauts.append(f"{identifiant} cochée sans preuve (« — preuve : » absent ou vide)")
        elif not coche and not _marqueur_valide(reste):
            defauts.append(f"{identifiant} non cochée sans « sans objet : » ni « non vérifié : »")
    return defauts


def preuves_partielles(texte_liste: str, texte_fiche: str) -> list[str]:
    """Les identifiants des cases cochées dont la preuve dit « non vérifié », dans l'ordre de la liste."""
    entrees = entrees_de_la_fiche(texte_fiche)
    partielles = []
    for identifiant in cases_de_la_liste(texte_liste):
        if identifiant not in entrees:
            continue
        coche, reste = entrees[identifiant]
        m = PREUVE.search(reste) if coche else None
        if m is not None and PREUVE_PARTIELLE.search(m.group("preuve")):
            partielles.append(identifiant)
    return partielles


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(
        description="Vérifie que la fiche de l'enquêteur recopie chaque case de la liste d'enquête.")
    parseur.add_argument("--fiche", required=True, metavar="FICHIER",
                         help="la fiche de l'enquêteur (texte, ou sortie JSON de claude -p)")
    parseur.add_argument("--liste", default=str(LISTE_PAR_DEFAUT), metavar="FICHIER",
                         help="la liste d'enquête (défaut : listes/enquete.md)")
    args = parseur.parse_args(argv)

    try:
        texte_liste = Path(args.liste).read_text(encoding="utf-8")
        texte_fiche = lire_fiche(Path(args.fiche).read_text(encoding="utf-8"))
    except OSError as erreur:
        print(f"fichier illisible : {erreur}", file=sys.stderr)
        return USAGE

    if not cases_de_la_liste(texte_liste):
        print(f"aucune case dans la liste : {args.liste}", file=sys.stderr)
        return USAGE

    defauts = verifier(texte_liste, texte_fiche)
    partielles = preuves_partielles(texte_liste, texte_fiche)
    ligne_partielle = [f"preuve partielle : {', '.join(partielles)}"] if partielles else []
    if defauts:
        print("\n".join(defauts + ligne_partielle))
        return INCOMPLET
    for ligne in ligne_partielle:
        print(ligne)
    print(f"Fiche complète : {len(cases_de_la_liste(texte_liste))} cases de la liste.", file=sys.stderr)
    return OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
