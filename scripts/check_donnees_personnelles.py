#!/usr/bin/env python3
"""Aucune donnée personnelle dans le dépôt public.

Ce dépôt est public, et le plugin ``voyages`` manipule des billets, des mails de
réservation et des noms de voyageurs : la configuration de chaque voyage vit chez
l'appelant, jamais ici. Ce garde parcourt les fichiers de ``plugins/voyages/``
et ``evals/voyages/`` (constante ``RACINES_A_PARCOURIR``, à étendre quand un autre
plugin manipule des données de personnes) et refuse ce qui ressemble à une donnée
personnelle.

Motifs génériques (aucun nom dans ce fichier) :

- **adresse e-mail**, sauf domaines réservés aux exemples (``example.com``,
  ``example.org``, ``example.net``, ``*.example``, ``*.invalid``, ``*.test``,
  ``*.localhost``) ; un domaine sans point (``x@localhost``) n'est pas lu ;
- **numéro de téléphone** : français (``0X XX XX XX XX``, séparateurs espace,
  point ou tiret facultatifs, ou ``+33…``) et international (``+`` suivi d'au
  moins 9 chiffres) ;
- **identifiant numérique long** : une suite de 9 à 16 chiffres isolée, c'est-à-dire
  ni collée à une lettre, un chiffre, ``_``, ``.`` ou ``-`` qui la précède, ni suivie
  d'une lettre, d'un chiffre ou ``_``, ni d'une partie décimale (``.5``). Typiquement
  un identifiant Telegram (9 à 10 chiffres, ou ``-100…`` pour un groupe). Faux positifs
  écartés **par construction** : un hash hexadécimal (les chiffres y touchent des
  lettres), un UUID (segments reliés par ``-``), un horodatage ISO (tirets et
  ``T``), un numéro de version (points), une suite de plus de 16 chiffres (ce n'est
  plus un identifiant) et un horodatage compact ``AAAAMMJJ[hhmm[ss]]``. **Faux
  positif connu** : un horodatage Unix de 10 ou 13 chiffres a la forme d'un
  identifiant ; ils se marquent par l'échappatoire ci-dessous ;
- **chemin de profil Hermes** (``.hermes/profiles/``) et **chemin absolu d'un
  répertoire personnel** (``/home/<nom>/``, ``/Users/<nom>/``,
  ``C:\\Users\\<nom>\\``), sauf un nom de substitution (``user``, ``username``,
  ``utilisateur``, ``example``, ``exemple``).

Plus une **liste de motifs connus**, lue hors du dépôt, un motif par ligne (``#``
ouvre un commentaire, les lignes vides sont ignorées, comparaison insensible à la
casse, en sous-chaîne). Chemin : ``~/.config/mes-skills/motifs-personnels.txt``,
ou celui de la variable d'environnement ``MOTIFS_PERSONNELS``. La liste par défaut
est facultative (absente : seuls les motifs génériques jouent, et le garde le dit) ;
un chemin donné par la variable et introuvable est une erreur d'usage, pour qu'une
faute de frappe ne désactive pas le garde en silence. En CI, la liste est absente.

**Échappatoire d'un faux positif assumé** : la mention ``donnees-personnelles: ok``
(casse libre) sur la même ligne. Elle ne couvre que cette ligne.

Sortie : une ligne ``fichier:ligne : <type de motif>`` par trouvaille, **sans jamais
recopier la valeur trouvée** — ce log est public. Code de sortie : ``0`` propre,
``1`` au moins une trouvaille, ``2`` usage (racine absente, liste introuvable).

Le **chemin relatif** de chaque fichier parcouru (binaires compris : un billet PDF
nommé d'après son voyageur) passe par les mêmes motifs ; une trouvaille sort en
``fichier:0 : <type> (dans le chemin)``. Le **contenu** d'un fichier binaire (un octet
nul dans les 8 premiers Ko) n'est pas lu ; ``__pycache__`` et ``.git`` sont ignorés
en entier.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Les dossiers parcourus, relatifs à la racine du dépôt. À étendre quand un autre
# plugin manipule des données de personnes.
RACINES_A_PARCOURIR = ("plugins/voyages", "evals/voyages")

DOSSIERS_IGNORES = {"__pycache__", ".git"}
LISTE_PAR_DEFAUT = Path("~/.config/mes-skills/motifs-personnels.txt")
VARIABLE_LISTE = "MOTIFS_PERSONNELS"
ECHAPPATOIRE = re.compile(r"donnees-personnelles:\s*ok", re.IGNORECASE)

DOMAINES_EXEMPLES = ("example.com", "example.org", "example.net")
SUFFIXES_EXEMPLES = (".example", ".invalid", ".test", ".localhost")
NOMS_DE_SUBSTITUTION = {"user", "username", "utilisateur", "example", "exemple"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
TEL_FR = re.compile(r"(?<![\w+.])(?:\+33[ .-]?|0)[1-9](?:[ .-]?\d{2}){4}(?!\d)")
TEL_INTERNATIONAL = re.compile(r"(?<![\w+])\+\d(?:[ .-]?\d){8,}")
IDENTIFIANT_LONG = re.compile(r"(?<![\w.-])-?\d{9,16}(?![\w]|\.\d)")
HORODATAGE_COMPACT = re.compile(
    r"(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:\d{4}|\d{6})?")
DATE_ISO_AVEC_PLUS = re.compile(r"\+\d{4}-\d{2}-\d{2}")
PROFIL_HERMES = re.compile(r"\.hermes/profiles/")
REPERTOIRE_PERSONNEL = re.compile(
    r"(?:/home/|/Users/|[A-Za-z]:\\Users\\)([A-Za-z0-9._-]+)[/\\]")


def _domaine_reserve(domaine: str) -> bool:
    d = domaine.lower()
    return d in DOMAINES_EXEMPLES or d.endswith(SUFFIXES_EXEMPLES)


def types_de_motifs(ligne: str, connus: list[str]) -> list[str]:
    """Les types de motifs personnels trouvés sur une ligne (sans les valeurs)."""
    if ECHAPPATOIRE.search(ligne):
        return []
    types: list[str] = []
    if any(not _domaine_reserve(m.group(1)) for m in EMAIL.finditer(ligne)):
        types.append("adresse e-mail")
    telephone = bool(TEL_FR.search(ligne))
    for m in TEL_INTERNATIONAL.finditer(ligne):
        if not DATE_ISO_AVEC_PLUS.match(m.group(0)):
            telephone = True
    if telephone:
        types.append("numéro de téléphone")
    for m in IDENTIFIANT_LONG.finditer(ligne):
        if not HORODATAGE_COMPACT.fullmatch(m.group(0).lstrip("-")):
            types.append("identifiant numérique long")
            break
    if PROFIL_HERMES.search(ligne):
        types.append("chemin de profil Hermes")
    if any(m.group(1).lower() not in NOMS_DE_SUBSTITUTION
           for m in REPERTOIRE_PERSONNEL.finditer(ligne)):
        types.append("chemin de répertoire personnel")
    bas = ligne.lower()
    if any(motif in bas for motif in connus):
        types.append("motif connu")
    return types


def lire_motifs_connus() -> tuple[list[str], str]:
    """(motifs, message). Lève ``FileNotFoundError`` si la variable désigne un fichier absent."""
    explicite = os.environ.get(VARIABLE_LISTE)
    chemin = Path(explicite).expanduser() if explicite else LISTE_PAR_DEFAUT.expanduser()
    if not chemin.is_file():
        if explicite:
            raise FileNotFoundError(f"{VARIABLE_LISTE} désigne un fichier introuvable")
        return [], ("liste de motifs connus absente : seuls les motifs génériques sont joués")
    motifs = []
    for brut in chemin.read_text(encoding="utf-8").splitlines():
        ligne = brut.strip()
        if ligne and not ligne.startswith("#"):
            motifs.append(ligne.lower())
    return motifs, f"liste de motifs connus lue ({len(motifs)} motif(s))"


def fichiers(dossier: Path):
    """``(chemin, est_texte)`` pour chaque fichier parcouru, binaires compris :
    le chemin de tous est contrôlé, le contenu des seuls fichiers texte est lu."""
    for chemin in sorted(dossier.rglob("*")):
        if not chemin.is_file():
            continue
        if DOSSIERS_IGNORES.intersection(chemin.relative_to(dossier).parts):
            continue
        try:
            with chemin.open("rb") as f:
                debut = f.read(8192)
        except OSError:
            continue
        yield chemin, b"\x00" not in debut


def analyser(racine: Path, dossiers, connus: list[str]) -> list[tuple[str, int, str]]:
    trouvailles = []
    for dossier in dossiers:
        for chemin, est_texte in fichiers(racine / dossier):
            nom = chemin.relative_to(racine).as_posix()
            # Le chemin dit déjà « billet-<nom>.pdf » : numéro de ligne 0.
            for type_ in types_de_motifs(nom, connus):
                trouvailles.append((nom, 0, f"{type_} (dans le chemin)"))
            if not est_texte:
                continue
            texte = chemin.read_text(encoding="utf-8", errors="replace")
            for numero, ligne in enumerate(texte.splitlines(), 1):
                for type_ in types_de_motifs(ligne, connus):
                    trouvailles.append((nom, numero, type_))
    return trouvailles


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--racine", type=Path, default=REPO_ROOT,
                        help="racine du dépôt (défaut : celui de ce script)")
    parser.add_argument("dossiers", nargs="*", default=list(RACINES_A_PARCOURIR),
                        help="dossiers à parcourir, relatifs à la racine "
                             f"(défaut : {', '.join(RACINES_A_PARCOURIR)})")
    args = parser.parse_args(argv)

    for dossier in args.dossiers:
        if not (args.racine / dossier).is_dir():
            print(f"dossier à parcourir introuvable : {dossier} "
                  "(un garde qui ne lit rien ne prouve rien)", file=sys.stderr)
            return 2
    try:
        connus, message = lire_motifs_connus()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    print(f"({message})")

    trouvailles = analyser(args.racine, args.dossiers, connus)
    for nom, numero, type_ in trouvailles:
        print(f"{nom}:{numero} : {type_}")
    if trouvailles:
        print(f"ROUGE — {len(trouvailles)} trouvaille(s) : une donnée personnelle ne se "
              "publie pas dans ce dépôt. La valeur n'est pas recopiée ici ; marquer un faux "
              "positif par « donnees-personnelles: ok » sur la ligne.")
        return 1
    print("Aucune donnée personnelle trouvée dans " + ", ".join(args.dossiers) + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
