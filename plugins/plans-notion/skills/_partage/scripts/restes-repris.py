#!/usr/bin/env python3
"""Garde des restes repris : chaque ligne ouverte des dépôts du plan est citée sur la page.

Pourquoi un script : à l'ouverture d'un plan, les lignes ouvertes de la base « Restes » de
ses dépôts doivent être relevées et tranchées (`_partage/restes.md`, règle 7). Une ligne
oubliée dort, et « laissée ouverte » sans raison ressemble à une décision. Le passage à
`en revue` est bloqué tant que le chapitre `Restes repris` ne cite pas chaque ligne. Un
plan ne reprend que les lignes de son sujet (Q9) : les autres sont citées « laissée
ouverte » avec leur raison. Le script ne juge pas le sujet, il vérifie que chaque ligne a
été jugée.

Usage : restes-repris.py <page.md> --lignes <export> [--depots owner/repo,...]

<page.md> : miroir local de la page du plan (sortie de ``notion-fetch``, en forme markdown
  ou en forme du connecteur de l'app, comme ``restes-sans-ligne.py``).
  Dépôts du plan : ``--depots`` s'il est donné ; sinon les valeurs de la propriété ``Repo``
  du miroir (ligne ``**Repo** : owner/repo``, ou ligne de tableau ``| Repo | … |``), séparées
  par des virgules. Aucun dépôt lisible : code 2.
  Chapitre : le H2 « Restes repris » et ses H3 (un par dépôt, si le plan en touche
  plusieurs). Chaque puce de premier niveau est un bloc avec ses lignes de suite. Une
  ligne ouverte est citée par un bloc qui porte son identifiant Notion (dans le lien vers
  sa page) ou son titre exact (texte visible). Une citation hors du chapitre ne compte pas.
  Un bloc qui dit « laissée ouverte » ne reprend pas la ligne : il doit donner la raison
  après la mention (« — laissée ouverte : hors sujet, Benjamin tranche »). Sans raison,
  la ligne est oubliée.

<export> : sortie de ``restes_lignes.py lire`` : une ligne JSON par reste (JSON-lines), ou un
  tableau JSON. Clés lues, toutes en texte : ``Reste`` (titre), ``Repo`` (``owner/repo``),
  ``État``, ``id`` (identifiant de la page, tirets ou non). Seules les lignes ``État`` =
  ``ouvert`` dont ``Repo`` est un dépôt du plan sont contrôlées. Un fichier vide est
  illisible : une base sans ligne ouverte s'écrit ``[]``, pour distinguer un export vide
  d'une sortie de commande cassée.

Codes : 0 chaque ligne ouverte des dépôts du plan est reprise, ou laissée ouverte avec une
raison ; 1 au moins une ligne oubliée, une ligne par oubli sur la sortie standard, avec le
titre, le dépôt et l'identifiant ; 2 illisible (page ou export absent ou cassé, dépôts non
déterminés) : un message sur la sortie d'erreur.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

# Le connecteur de l'app rend le gras en <b>, le code en <code>, et un lien de page en
# <mention-page>. On ramène tout aux formes markdown avant toute lecture.
GRAS_HTML = re.compile(r"<(b|strong)>(.*?)</\1>", re.S)
CODE_HTML = re.compile(r"<code>(.*?)</code>", re.S)
MENTION_HTML = re.compile(r'<mention-page\s+url="([^"]*)"\s*>(.*?)</mention-page>', re.S)

LIEN = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
URL = re.compile(r"https?://[^\s)\"<>]+")
# 32 hexadécimaux qui ne sont pas suivis d'un autre : le dernier bloc d'une URL « titre-<id> ».
ID_NOTION = re.compile(r"[0-9a-f]{32}(?![0-9a-f])")
# « ## Restes repris », éventuellement sous un <span> de couleur (règle du bleu des retouches).
TITRE_CHAPITRE = re.compile(r"^##[ \t]+(?:<span[^>]*>[ \t]*)*restes repris\b", re.IGNORECASE)
FIN_CHAPITRE = re.compile(r"^#{1,2}[ \t]")
TITRE_SOUS_CHAPITRE = re.compile(r"^#{3,6}[ \t]")
PUCE = re.compile(r"^(?P<indent>[ \t]*)[-*][ \t]+")
# La propriété Repo, en puce, en clé gras ou en ligne de tableau.
REPO_LIGNE = re.compile(r"^[ \t]*(?:[-*|][ \t]*)?\**Repo\**[ \t]*[:|][ \t]*(?P<valeur>.*)$")
DEPOT = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
LAISSEE = re.compile(r"laiss[eé]e\s+ouverte", re.IGNORECASE)
CHAMPS_LIGNE = ("Reste", "Repo", "État", "id")


class Illisible(Exception):
    """Entrée qui ne permet pas de contrôler (code 2)."""


def normaliser(texte: str) -> str:
    """Miroir du connecteur → formes markdown : gras, code, lien de page."""
    texte = GRAS_HTML.sub(lambda m: f"**{m.group(2)}**", texte)
    texte = CODE_HTML.sub(lambda m: f"`{html.unescape(m.group(1))}`", texte)
    return MENTION_HTML.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", texte)


def visible(texte: str) -> str:
    """Texte lu par Benjamin : sans liens (le texte reste), sans URL nue, sans balisage."""
    texte = LIEN.sub(lambda m: m.group(1), texte)
    texte = URL.sub("", texte)
    texte = re.sub(r"\*\*|`", "", texte)
    texte = re.sub(r"^[ \t]*[-*][ \t]+", "", texte, flags=re.M)
    return " ".join(texte.split())


def _cle(texte: str) -> str:
    """Forme de comparaison : visible, sans casse, sans ponctuation de bord."""
    return visible(texte).casefold().strip(" .;:—–-")


def _identifiant(url: str) -> str | None:
    """Identifiant Notion d'une URL : son dernier bloc de 32 hexadécimaux, tirets ôtés."""
    trouves = ID_NOTION.findall(url.split("?")[0].replace("-", "").lower())
    return trouves[-1] if trouves else None


def _largeur(indentation: str) -> int:
    return len(indentation.expandtabs(4))


def depots_du_plan(texte: str) -> list[str]:
    """Dépôts lus dans les lignes « Repo » du miroir, sans doublon, dans l'ordre."""
    depots: list[str] = []
    for ligne in texte.splitlines():
        m = REPO_LIGNE.match(ligne)
        if not m:
            continue
        for jeton in re.split(r"[\s,;|]+", m.group("valeur")):
            jeton = jeton.strip("`*")
            if DEPOT.fullmatch(jeton) and jeton.casefold() not in {d.casefold() for d in depots}:
                depots.append(jeton)
    return depots


def _depots(option: str | None, texte: str) -> list[str]:
    if option is not None:
        depots = [d.strip() for d in option.split(",") if d.strip()]
        if not depots or not all(DEPOT.fullmatch(d) for d in depots):
            raise Illisible(f"--depots « {option} » : attendu owner/repo, séparés par des virgules")
        return depots
    depots = depots_du_plan(texte)
    if not depots:
        raise Illisible("dépôts indéterminables : ni --depots, ni propriété Repo lisible "
                        "dans le miroir (owner/repo)")
    return depots


def chapitre_repris(texte: str) -> list[str]:
    """Blocs du H2 « Restes repris » : une puce de premier niveau et ses lignes de suite.

    Un H3 (un par dépôt) ferme le bloc en cours ; les puces qui suivent en ouvrent d'autres.
    Chapitre absent : aucun bloc.
    """
    lignes = texte.splitlines()
    debut = next((i for i, ligne in enumerate(lignes) if TITRE_CHAPITRE.match(ligne)), None)
    if debut is None:
        return []
    corps: list[str] = []
    for ligne in lignes[debut + 1:]:
        if FIN_CHAPITRE.match(ligne):
            break
        corps.append(ligne)
    puces = [_largeur(PUCE.match(l).group("indent")) for l in corps if PUCE.match(l)]
    if not puces:
        return []
    niveau = min(puces)
    blocs: list[list[str]] = []
    courant: list[str] | None = None
    for ligne in corps:
        if TITRE_SOUS_CHAPITRE.match(ligne):
            courant = None
            continue
        p = PUCE.match(ligne)
        if p and _largeur(p.group("indent")) == niveau:
            courant = [ligne]
            blocs.append(courant)
        elif courant is not None:
            courant.append(ligne)
    return ["\n".join(bloc) for bloc in blocs]


def _citee(bloc: str, identifiant: str, titre: str) -> bool:
    ids_cites = {_identifiant(u) for u in URL.findall(bloc)} - {None}
    if identifiant in ids_cites:
        return True
    return bool(titre) and titre in _cle(bloc)


def _laissee(bloc: str) -> tuple[bool, str]:
    """(le bloc dit « laissée ouverte », la raison qui suit la mention)."""
    m = LAISSEE.search(bloc)
    if not m:
        return False, ""
    return True, visible(bloc[m.end():]).strip(" :—–-.;,")


def _defaut(blocs: list[str], identifiant: str, titre: str) -> str | None:
    """None si la ligne est reprise, ou laissée ouverte avec une raison ; sinon le motif :
    ``non_cite`` (aucun bloc du chapitre ne la cite) ou ``sans_raison``."""
    cites = [b for b in blocs if _citee(b, identifiant, titre)]
    if not cites:
        return "non_cite"
    for bloc in cites:
        marquee, raison = _laissee(bloc)
        if not marquee or raison:
            return None
    return "sans_raison"


def lire_lignes(chemin: str) -> list[dict]:
    try:
        texte = Path(chemin).read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        raise Illisible(f"export « {chemin} » : {e}") from e
    if not texte.strip():
        raise Illisible(f"export « {chemin} » vide : une base sans ligne ouverte s'écrit « [] »")
    if texte.lstrip().startswith("["):
        try:
            donnees = json.loads(texte)
        except ValueError as e:
            raise Illisible(f"export « {chemin} » : JSON cassé ({e})") from e
        if not isinstance(donnees, list):
            raise Illisible("l'export n'est pas une liste de lignes")
    else:
        donnees = []
        for n, ligne in enumerate(texte.splitlines(), 1):
            if not ligne.strip():
                continue
            try:
                donnees.append(json.loads(ligne))
            except ValueError as e:
                raise Illisible(f"export « {chemin} », ligne {n} : JSON cassé ({e})") from e
    for n, ligne in enumerate(donnees, 1):
        if not isinstance(ligne, dict):
            raise Illisible(f"ligne {n} : pas un objet")
        absents = [c for c in CHAMPS_LIGNE if c not in ligne]
        if absents:
            raise Illisible(f"ligne {n} : champ(s) absent(s) : {', '.join(absents)}")
        for champ in CHAMPS_LIGNE:
            if not isinstance(ligne[champ], str):
                raise Illisible(f"ligne {n} : « {champ} » n'est pas un texte")
    return donnees


def controler(texte: str, lignes: list[dict], depots: list[str]) -> tuple[list[str], int]:
    """(défauts, nombre de lignes ouvertes contrôlées) ; un défaut par ligne oubliée."""
    voulus = {d.casefold() for d in depots}
    blocs = chapitre_repris(texte)
    ouvertes = [l for l in lignes if l["État"] == "ouvert" and l["Repo"].casefold() in voulus]
    defauts = []
    for ligne in ouvertes:
        titre = _cle(ligne["Reste"])
        identifiant = ligne["id"].replace("-", "").lower()
        motif = _defaut(blocs, identifiant, titre)
        if motif is None:
            continue
        nom = " ".join(ligne["Reste"].split())
        ou = f"({ligne['Repo']}, id {ligne['id']})"
        if motif == "non_cite":
            defauts.append(f"Reste ouvert non cité dans « Restes repris » : « {nom} » {ou}")
        else:
            defauts.append(f"« laissée ouverte » sans raison : « {nom} » {ou}")
    return defauts, len(ouvertes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    ap.add_argument("--lignes", required=True, help="export JSON-lines des lignes de la base")
    ap.add_argument("--depots", help="dépôts du plan, owner/repo séparés par des virgules "
                                     "(défaut : la propriété Repo du miroir)")
    a = ap.parse_args(argv)
    try:
        texte = normaliser(Path(a.page).read_text(encoding="utf-8"))
        lignes = lire_lignes(a.lignes)
        depots = _depots(a.depots, texte)
        defauts, n = controler(texte, lignes, depots)
    except (OSError, ValueError, Illisible) as e:
        print(f"illisible : {e}", file=sys.stderr)
        return 2
    for defaut in defauts:
        print(defaut)
    if defauts:
        return 1
    if n:
        print(f"restes repris : {n} ligne(s) ouverte(s) sur {len(depots)} dépôt(s), toutes citées")
    else:
        print(f"restes repris : aucune ligne ouverte sur {len(depots)} dépôt(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
