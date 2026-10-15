#!/usr/bin/env python3
"""Porte du statut ``pret`` : la préparation d'un plan est faite, on peut passer à ``en cours``.

Pourquoi un script : « avant la première étape, sans exception » (relecture du
plan, questions au vert, preuves, maquette, relevé de la CI, vagues, branche)
tenait à la mémoire du pilote, et un pilote pressé de coder en sautait un geste
sans que rien ne le voie. ``Statut`` = ``pret`` ne se pose qu'une fois ce
script à 0 sur le miroir de la page ; ``en cours`` ne se pose qu'après ``pret``.

Usage : preparation-prete.py <page.md>
Le miroir est la sortie de ``notion-fetch``. Le script contrôle quatre choses :
  1. aucune question du chapitre « Questions ouvertes » n'est restée ouverte
     (titre H3 portant 🧭, même marque que ``verifier-preuves.py``) ;
  2. chaque étape du chapitre « Exécution » porte sa « Preuve de fin »
     (``preuves-des-etapes.py --avant``, joué à côté de ce script) ;
  3. le « Journal d'exécution » porte une entrée H3 « Ouverture » (la dernière,
     si la préparation a été refaite) ;
  4. cette entrée porte neuf puces à clé en gras — **Relecture**, **Questions**,
     **Preuves**, **Répétition**, **Maquette**, **CI**, **Vagues**, **Pilote**,
     **Branche** —, chacune non vide et sans coquille (« — », « - », « aucune »,
     « à définir », « à voir »). ``sans objet — <raison>`` est une valeur
     recevable, la raison est obligatoire.
Il ne juge pas le contenu : il vérifie que chaque geste a laissé sa trace écrite.
Codes : 0 prêt ; 1 au moins un défaut, un par ligne sur la sortie standard ;
2 entrée illisible (page absente, chapitre « Questions ouvertes », « Exécution »
ou « Journal d'exécution » absent).
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

CLES = ("Relecture", "Questions", "Preuves", "Répétition", "Maquette", "CI", "Vagues",
        "Pilote", "Branche")
PUCE = re.compile(r"^[ \t]*[-*][ \t]+\*\*([^*]+?)\*\*[ \t]*(?:\([^)]*\)[ \t]*)?:[ \t]*(.*)$")
OUVERTURE = re.compile(r"^###[ \t]+ouverture\b", re.IGNORECASE)
QUESTION_OUVERTE = re.compile(r"^###[ \t]+.*🧭.*\bQ\d+\b")
COQUILLES = {"", "—", "-", "aucune", "à définir", "à voir"}
SANS_OBJET = re.compile(r"^sans objet\b[ \t]*(.*)$", re.IGNORECASE)
PREUVES = Path(__file__).with_name("preuves-des-etapes.py")


class Illisible(Exception):
    """Entrée qui ne permet pas de contrôler (code 2)."""


def _titre(ligne: str) -> str:
    return ligne[3:].strip().replace("’", "'").lower()


def section(texte: str, titre: str, nom: str) -> list[str]:
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


def questions_ouvertes(texte: str) -> list[str]:
    return [l.strip() for l in section(texte, "questions ouvertes", "Questions ouvertes")
            if QUESTION_OUVERTE.match(l)]


def derniere_ouverture(texte: str) -> list[str] | None:
    """Lignes de la dernière entrée H3 « Ouverture » du journal, ou None."""
    entree: list[str] | None = None
    en_cours = False
    for ligne in section(texte, "journal d'exécution", "Journal d'exécution"):
        if ligne.startswith("### "):
            en_cours = bool(OUVERTURE.match(ligne))
            if en_cours:
                entree = []
        elif en_cours and entree is not None:
            entree.append(ligne)
    return entree


def _valeur_vide(valeur: str) -> bool:
    return valeur.strip().strip("`*").strip().rstrip(".").strip().lower() in COQUILLES


def defauts_ouverture(entree: list[str]) -> list[str]:
    valeurs: dict[str, str] = {}
    for ligne in entree:
        m = PUCE.match(ligne)
        if m:
            valeurs.setdefault(m.group(1).strip(), m.group(2))
    defauts = []
    for cle in CLES:
        if cle not in valeurs:
            defauts.append(f"Ouverture : puce **{cle}** absente")
            continue
        valeur = valeurs[cle]
        if _valeur_vide(valeur):
            defauts.append(f"Ouverture : **{cle}** vide ou réduite à une coquille")
            continue
        so = SANS_OBJET.match(valeur.strip().strip("`*").strip())
        if so and _valeur_vide(so.group(1).lstrip("—–-: \t")):
            defauts.append(f"Ouverture : **{cle}** « sans objet » sans raison")
    return defauts


def preuves_avant(page: str) -> list[str]:
    """Défauts de ``preuves-des-etapes.py --avant`` ; une ligne si le script lui-même échoue."""
    r = subprocess.run([sys.executable, str(PREUVES), page, "--avant"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return []
    if r.returncode == 1:
        return [f"preuves : {l}" for l in r.stdout.splitlines() if l.strip()]
    return [f"preuves : preuves-des-etapes.py --avant illisible (code {r.returncode}) "
            f"{r.stderr.strip()}".rstrip()]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage : preparation-prete.py <page.md>", file=sys.stderr)
        return 2
    try:
        texte = Path(args[0]).read_text(encoding="utf-8")
        section(texte, "exécution", "Exécution")
        defauts = [f"question ouverte : {t}" for t in questions_ouvertes(texte)]
        defauts += preuves_avant(args[0])
        entree = derniere_ouverture(texte)
    except (Illisible, OSError) as erreur:
        print(f"illisible : {erreur}", file=sys.stderr)
        return 2
    if entree is None:
        defauts.append("Journal d'exécution : entrée « Ouverture » absente")
    else:
        defauts += defauts_ouverture(entree)
    if defauts:
        print("\n".join(defauts))
        return 1
    print("prêt : questions vertes, preuves de fin écrites, entrée Ouverture complète")
    return 0


if __name__ == "__main__":
    sys.exit(main())
