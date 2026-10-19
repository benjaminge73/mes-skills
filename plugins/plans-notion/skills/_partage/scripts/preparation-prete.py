#!/usr/bin/env python3
"""Porte du statut ``pret`` : la préparation d'un plan est faite, on peut passer à ``en cours``.

Pourquoi un script : « avant la première étape, sans exception » (relecture du
plan, questions au vert, preuves, maquette, relevé de la CI, vagues, branche)
tenait à la mémoire du pilote, et un pilote pressé de coder en sautait un geste
sans que rien ne le voie. ``Statut`` = ``pret`` ne se pose qu'une fois ce
script à 0 sur le miroir de la page ; ``en cours`` ne se pose qu'après ``pret``.
Un plan ``pret`` a toutes ses étapes prouvées et rejouées à blanc, ses vagues
calculées, et, s'il appartient à un plan maître, l'orchestration entre les plans
écrite sur la page maître.

Usage : preparation-prete.py <page.md> --depot <dépôt> [--maitre <maitre.md>]
Les miroirs sont la sortie de ``notion-fetch``. Le script contrôle :
  1. aucune question du chapitre « Questions ouvertes » n'est restée ouverte
     (titre H3 portant 🧭, même marque que ``verifier-preuves.py``) ;
  2. chaque étape du chapitre « Exécution » porte sa « Preuve de fin »
     (``preuves-des-etapes.py --avant``) ;
  3. chaque réponse tranchée porte une preuve conforme
     (``verifier-preuves.py --depot <dépôt>``) ;
  4. les vagues : la colonne « Vague » du tableau de chevauchement égale le calcul
     (``vagues.py --comparer``) ;
  5. le « Journal d'exécution » porte une entrée H3 « Ouverture » (la dernière, si
     la préparation a été refaite) avec dix puces à clé en gras — **Relecture**,
     **Questions**, **Preuves**, **Répétition**, **Maquette**, **CI**, **Vagues**,
     **Pilote**, **Branche**, **Orchestration** — et, pour chaque étape du chapitre,
     une puce **Preuve de l'étape N** (la commande de preuve rejouée à blanc et ce
     qu'elle a rendu), chacune non vide et sans coquille (« — », « - », « aucune »,
     « à définir », « à voir ») ; ``sans objet — <raison>`` est recevable, la raison
     est obligatoire ; la puce **Pilote** nomme Sonnet et ``medium``, ou porte la
     dérogation de Benjamin citée (``dérogation de Benjamin, <date> : « … »``) ;
  6. **Orchestration** : ``sans objet — <raison>`` (aucun plan maître), ou la page maître
     est fournie par ``--maitre`` et porte, non vides, les sections « Plans »,
     « Croisement », « Ordre de merge » et « File des actions lourdes ».
Il ne juge pas le contenu : il vérifie que chaque geste a laissé sa trace.
Codes : 0 prêt ; 1 au moins un défaut, un par ligne sur la sortie standard ;
2 entrée illisible ou usage faux (page, chapitre « Questions ouvertes »,
« Exécution » ou « Journal d'exécution » absent, ``--depot`` manquant).
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CLES = ("Relecture", "Questions", "Preuves", "Répétition", "Maquette", "CI", "Vagues",
        "Pilote", "Branche", "Orchestration")
SECTIONS_MAITRE = (("plans", "Plans"), ("croisement", "Croisement"), ("ordre de merge", "Ordre de merge"),
                   ("file des actions lourdes", "File des actions lourdes"))
ETAPE = re.compile(r"^###[ \t]+étape[ \t]+(D?\d+)", re.IGNORECASE)
PUCE = re.compile(r"^[ \t]*[-*][ \t]+\*\*([^*]+?)\*\*[ \t]*(?:\([^)]*\)[ \t]*)?:[ \t]*(.*)$")
OUVERTURE = re.compile(r"^###[ \t]+ouverture\b", re.IGNORECASE)
QUESTION_OUVERTE = re.compile(r"^###[ \t]+.*🧭.*\bQ\d+\b")
COQUILLES = {"", "—", "-", "aucune", "à définir", "à voir"}
SANS_OBJET = re.compile(r"^sans objet\b[ \t]*(.*)$", re.IGNORECASE)
PILOTE_SONNET = re.compile(r"\bsonnet\b", re.IGNORECASE)
PILOTE_MEDIUM = re.compile(r"\bmedium\b", re.IGNORECASE)
PILOTE_DEROGATION = re.compile(r"dérogation de Benjamin[^«]*«[^»]+»", re.IGNORECASE)
SCRIPTS = Path(__file__).parent


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


def etapes(texte: str) -> list[str]:
    """Numéros (``1``, ``D1``) des étapes du chapitre « Exécution », dans l'ordre, sans doublon."""
    vus: list[str] = []
    for ligne in section(texte, "exécution", "Exécution"):
        m = ETAPE.match(ligne)
        if m and m.group(1).upper() not in vus:
            vus.append(m.group(1).upper())
    return vus


def valeurs_puces(entree: list[str]) -> dict[str, str]:
    valeurs: dict[str, str] = {}
    for ligne in entree:
        m = PUCE.match(ligne)
        if m:
            valeurs.setdefault(m.group(1).strip().replace("’", "'"), m.group(2))
    return valeurs


def defaut_valeur(cle: str, valeur: str | None) -> str | None:
    if valeur is None:
        return f"Ouverture : puce **{cle}** absente"
    if _valeur_vide(valeur):
        return f"Ouverture : **{cle}** vide ou réduite à une coquille"
    so = SANS_OBJET.match(valeur.strip().strip("`*").strip())
    if so and _valeur_vide(so.group(1).lstrip("—–-: \t")):
        return f"Ouverture : **{cle}** « sans objet » sans raison"
    return None


def defaut_pilote(valeur: str | None) -> str | None:
    """Le pilote tourne en Sonnet ``medium``, sauf dérogation citée de Benjamin."""
    if valeur is None or _valeur_vide(valeur):
        return None  # déjà signalé par defaut_valeur
    if PILOTE_DEROGATION.search(valeur):
        return None
    if PILOTE_SONNET.search(valeur) and PILOTE_MEDIUM.search(valeur):
        return None
    return ("Ouverture : **Pilote** n'est pas Sonnet `medium` et ne cite aucune dérogation de "
            "Benjamin : lancer l'exécution dans une sous-session `--model claude-sonnet-5-5 "
            "--effort medium` (ouverture.md, « Le réglage du pilote »)")


def defauts_ouverture(entree: list[str], numeros: list[str]) -> list[str]:
    valeurs = valeurs_puces(entree)
    cles = list(CLES) + [f"Preuve de l'étape {n}" for n in numeros]
    defauts = [d for d in (defaut_valeur(c, valeurs.get(c)) for c in cles) if d]
    pilote = defaut_pilote(valeurs.get("Pilote"))
    return defauts + [pilote] if pilote else defauts


def orchestration_sans_objet(entree: list[str]) -> bool:
    valeur = valeurs_puces(entree).get("Orchestration", "")
    return bool(SANS_OBJET.match(valeur.strip().strip("`*").strip()))


def defauts_maitre(texte: str) -> list[str]:
    """Sections de la page maître requises pour l'orchestration, chacune non vide."""
    defauts = []
    for debut, nom in SECTIONS_MAITRE:
        try:
            lignes = section(texte, debut, nom)
        except Illisible:
            defauts.append(f"plan maître : section « {nom} » absente")
            continue
        if not any(not _valeur_vide(l) and not l.lstrip().startswith("#") for l in lignes):
            defauts.append(f"plan maître : section « {nom} » vide")
    return defauts


def sous_script(nom: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / nom), *args], capture_output=True, text=True)


def defauts_script(etiquette: str, r: subprocess.CompletedProcess, nom: str) -> list[str]:
    """Défauts d'un sous-script de contrôle : code 0 conforme, 1 une ligne par écart, autre = illisible."""
    if r.returncode == 0:
        return []
    if r.returncode == 1:
        return [f"{etiquette} : {l}" for l in r.stdout.splitlines() if l.strip()]
    return [f"{etiquette} : {nom} illisible (code {r.returncode}) {r.stderr.strip()}".rstrip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    ap.add_argument("--depot", required=True)
    ap.add_argument("--maitre")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        texte = Path(a.page).read_text(encoding="utf-8")
        numeros = etapes(texte)
        defauts = [f"question ouverte : {t}" for t in questions_ouvertes(texte)]
        defauts += defauts_script("preuves", sous_script("preuves-des-etapes.py", a.page, "--avant"),
                                  "preuves-des-etapes.py --avant")
        defauts += defauts_script("réponses", sous_script("verifier-preuves.py", a.page, "--depot", a.depot),
                                  "verifier-preuves.py")
        defauts += defauts_script("vagues", sous_script("vagues.py", a.page, "--comparer"),
                                  "vagues.py --comparer")
        entree = derniere_ouverture(texte)
        maitre = Path(a.maitre).read_text(encoding="utf-8") if a.maitre else None
    except (Illisible, OSError) as erreur:
        print(f"illisible : {erreur}", file=sys.stderr)
        return 2
    if entree is None:
        defauts.append("Journal d'exécution : entrée « Ouverture » absente")
    else:
        defauts += defauts_ouverture(entree, numeros)
        if not orchestration_sans_objet(entree):
            if maitre is None:
                defauts.append("Orchestration : un plan maître est cité, `--maitre <miroir>` manque")
            else:
                defauts += defauts_maitre(maitre)
    if defauts:
        print("\n".join(defauts))
        return 1
    print("prêt : questions vertes, étapes prouvées et rejouées, vagues calculées, "
          "entrée Ouverture complète, orchestration écrite ou sans objet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
