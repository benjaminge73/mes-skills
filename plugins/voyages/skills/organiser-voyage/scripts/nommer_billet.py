#!/usr/bin/env python3
"""Nommage des billets d'un voyage : module pur, bibliothèque standard seule.

Entrées : les champs extraits d'un billet (dict) et, pour la collision, les
noms déjà présents dans le dossier cible. Sortie : un nom de fichier. Aucun
accès réseau ni OneDrive : tout se teste hors ligne.

Nomenclature (extension = celle du fichier, ``.pdf`` par défaut) :

- billet (musée, visite, activité) :
  ``AAAA-MM-JJ HHhMM - Lieu - Billet - Voyageur A.pdf``
- vol : ``AAAA-MM-JJ - Vol Origine-Destination - Type - Voyageur A.pdf``
  (Type = ``document``, par défaut « Billet » ; ex. « Carte d'embarquement »)
- train : ``AAAA-MM-JJ HHhMM - Train Origine-Destination - Billet - Voyageur A.pdf``
- hébergement : ``AAAA-MM-JJ - Hebergement Nom - Reservation.pdf`` (jamais de
  voyageur : la réservation est commune)

Dernier champ des billets nominatifs : le voyageur si le billet le porte ;
sinon, pour une commande à N billets (``billet`` = rang, ``sur`` = N),
``1 sur 2`` ; sinon, si ``commun`` est vrai (billet valable pour les deux
voyageurs), le champ est omis. Le prénom l'emporte sur « 1 sur 2 ».

Refus : une date, une heure (billet ou train), un lieu, une origine, une
destination ou un voyageur absent, vide, invalide ou listé dans ``incertains``
lève ``ChampIncertain``. Jamais de nom bricolé avec « inconnu ».

Collision : ``nom_libre`` ajoute `` (2)``, `` (3)``… avant l'extension ; la
comparaison ignore la casse (OneDrive aussi).

Dossier du voyage : ``nom_dossier_voyage`` rend ``AAAA - Destination`` si le
voyage dure plus d'un mois, c'est-à-dire plus de 31 jours (fin - début), sinon
``AAAA-MM - Destination`` (année et mois du début).

CLI : ``nommer_billet.py --json '<champs>' [--existants fichier]`` imprime le
nom ; ``--dossier`` lit ``{destination, debut, fin}`` et imprime le nom du
dossier. Refus : code 1 et message sur stderr.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

JOUR_MAX_MOIS = 31  # « plus d'un mois » = strictement plus de 31 jours
INTERDITS = re.compile(r'["*:<>?/\\|]')


class ChampIncertain(ValueError):
    """Un champ nécessaire au nom est absent, invalide ou incertain."""


def _nettoyer(texte: str) -> str:
    texte = INTERDITS.sub("", texte)
    texte = re.sub(r"\s+", " ", texte)
    return texte.strip(" .")


def _texte(champs: dict, cle: str) -> str:
    if cle in (champs.get("incertains") or []):
        raise ChampIncertain(f"champ « {cle} » signalé incertain")
    valeur = champs.get(cle)
    if not isinstance(valeur, str) or not _nettoyer(valeur):
        raise ChampIncertain(f"champ « {cle} » absent ou vide")
    return _nettoyer(valeur)


def _date(champs: dict, cle: str = "date") -> date:
    brut = _texte(champs, cle)
    try:
        return date.fromisoformat(brut)
    except ValueError:
        raise ChampIncertain(f"champ « {cle} » n'est pas une date AAAA-MM-JJ valide : {brut!r}")


def _heure(champs: dict) -> str:
    if "heure" in (champs.get("incertains") or []):
        raise ChampIncertain("champ « heure » signalé incertain")
    brut = champs.get("heure")
    if not isinstance(brut, str):
        raise ChampIncertain("champ « heure » absent ou vide")
    brut = brut.strip()
    m = re.fullmatch(r"(\d{1,2})[h:](\d{2})", brut)
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise ChampIncertain(f"champ « heure » invalide : {brut!r}")
    return f"{int(m.group(1)):02d}h{m.group(2)}"


def _extension(champs: dict) -> str:
    ext = str(champs.get("extension") or "pdf").lstrip(".").lower()
    if not re.fullmatch(r"[a-z0-9]{1,5}", ext):
        raise ChampIncertain(f"extension invalide : {ext!r}")
    return "." + ext


def _dernier_champ(champs: dict) -> str | None:
    if champs.get("voyageur") not in (None, ""):
        return _texte(champs, "voyageur")
    if "voyageur" in (champs.get("incertains") or []):
        raise ChampIncertain("champ « voyageur » signalé incertain")
    rang, sur = champs.get("billet"), champs.get("sur")
    if isinstance(rang, int) and isinstance(sur, int) and 1 <= rang <= sur and sur >= 2:
        return f"{rang} sur {sur}"
    if champs.get("commun") is True:
        return None
    raise ChampIncertain("champ « voyageur » absent (ni prénom, ni « 1 sur N », ni billet commun)")


def construire_nom(champs: dict) -> str:
    """Le nom du fichier, ou ``ChampIncertain``. Ne regarde aucun dossier."""
    genre = champs.get("type")
    jour = _date(champs).isoformat()
    ext = _extension(champs)
    if genre == "hebergement":
        return f"{jour} - Hebergement {_texte(champs, 'nom')} - Reservation{ext}"
    if genre == "vol":
        trajet = f"Vol {_texte(champs, 'origine')}-{_texte(champs, 'destination')}"
        debut = jour
        doc = _nettoyer(str(champs.get("document") or "Billet")) or "Billet"
    elif genre == "train":
        trajet = f"Train {_texte(champs, 'origine')}-{_texte(champs, 'destination')}"
        debut = f"{jour} {_heure(champs)}"
        doc = "Billet"
    elif genre == "billet":
        trajet = _texte(champs, "lieu")
        debut = f"{jour} {_heure(champs)}"
        doc = "Billet"
    else:
        raise ChampIncertain(f"type inconnu ou absent : {genre!r}")
    parties = [debut + " - " + trajet, doc]
    dernier = _dernier_champ(champs)
    if dernier is not None:
        parties.append(_nettoyer(dernier))
    return " - ".join(parties) + ext


def nom_libre(nom: str, existants) -> str:
    """Un nom absent de ``existants`` (casse ignorée) : `` (2)``, `` (3)``… avant l'extension."""
    pris = {e.casefold() for e in existants}
    if nom.casefold() not in pris:
        return nom
    base, point, ext = nom.rpartition(".")
    if not point:
        base, ext = nom, ""
    else:
        ext = "." + ext
    n = 2
    while f"{base} ({n}){ext}".casefold() in pris:
        n += 1
    return f"{base} ({n}){ext}"


def nom_dossier_voyage(destination: str, debut, fin) -> str:
    """``AAAA - Destination`` au-delà de 31 jours, sinon ``AAAA-MM - Destination``."""
    dest = _texte({"destination": destination}, "destination")
    d = _date({"debut": debut if isinstance(debut, str) else str(debut)}, "debut")
    f = _date({"fin": fin if isinstance(fin, str) else str(fin)}, "fin")
    if f < d:
        raise ChampIncertain("la fin du voyage précède son début")
    if (f - d).days > JOUR_MAX_MOIS:
        return f"{d.year:04d} - {dest}"
    return f"{d.year:04d}-{d.month:02d} - {dest}"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--json", required=True, help="les champs, en JSON")
    p.add_argument("--existants", help="fichier : un nom déjà présent par ligne")
    p.add_argument("--dossier", action="store_true",
                   help="nommer le dossier du voyage ({destination, debut, fin})")
    args = p.parse_args(argv)
    try:
        champs = json.loads(args.json)
        if not isinstance(champs, dict):
            raise ChampIncertain("--json doit être un objet")
        if args.dossier:
            print(nom_dossier_voyage(champs.get("destination"), champs.get("debut"), champs.get("fin")))
            return 0
        existants = []
        if args.existants:
            with open(args.existants, encoding="utf-8") as f:
                existants = [l.rstrip("\n") for l in f if l.strip()]
        print(nom_libre(construire_nom(champs), existants))
        return 0
    except (ChampIncertain, json.JSONDecodeError, OSError) as e:
        print(f"refus : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
