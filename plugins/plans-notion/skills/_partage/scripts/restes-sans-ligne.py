#!/usr/bin/env python3
"""Garde de clôture de la base « Restes » : chaque reste en attente a sa ligne.

Pourquoi un script : un reste qui attend un événement ou un geste d'un propriétaire
doit atterrir dans la base « Restes » (restes.md), sinon il dort dans la page d'un plan
clos. Le passage à `a merger` ne le voyait pas. Le script compare la rubrique « Reste à
faire » de l'« État final » du plan avec l'export des lignes de la base, et rend un
défaut par reste sans ligne.

Usage : restes-sans-ligne.py <page.md> --lignes <lignes.json>

<page.md> : miroir local de la page du plan (markdown rendu par le connecteur Notion).
  Deux formes sont lues : celle de ``composio execute NOTION_GET_PAGE_MARKDOWN``
  (``**gras**``, accents graves, ``[texte](url)``) et celle du connecteur de l'app
  (``<b>gras</b>``, ``<code>…</code>``, ``<mention-page url="…">texte</mention-page>``).
  La rubrique lue : la puce « **Reste à faire** » dans le H3 « État final » du H2
  « Journal d'exécution ». Chaque puce de premier niveau de la rubrique, avec ses lignes
  de suite et ses sous-puces, est un reste en attente. La rubrique se ferme sur une
  puce à clé en gras de même niveau (« **Découvertes** : … »), sur un paragraphe après
  une ligne vide, ou à la fin du H3.
  Un reste n'a pas à être versé dans les cas suivants :
  - la rubrique dit « rien », « aucun » ou « aucune » (ou un tiret) : rien en attente ;
  - il est porté par un plan de suite : un lien dont le texte contient « Reprise du plan » ;
  - il est satisfait par une ligne de la base : il cite l'URL d'une ligne (même
    identifiant Notion de 32 caractères hexadécimaux), ou son texte contient le champ
    ``Reste`` d'une ligne (comparaison sans casse ni balisage, champ vide ignoré).

<lignes.json> : export des lignes de la base « Restes » du plan (schéma dans restes.md).
  Liste d'objets, chacun avec les clés ``Reste``, ``Pour``, ``État``, ``Plan d'origine``
  et ``url`` (``url`` = URL de la page de la ligne). Les valeurs sont du texte, à
  l'exception de ``Reste`` et ``url``, qui doivent l'être. Une clé absente ou une valeur
  de mauvais type rend le fichier illisible.
  L'``État`` d'une ligne n'entre pas dans le contrôle : une ligne présente satisfait la
  puce, quel que soit son état. Exemple, les valeurs entre chevrons étant à remplacer :
  ``[{"Reste": "<texte de la ligne>", "Pour": "Hal", "État": "ouvert",
  "Plan d'origine": "<titre ou URL du plan>", "url": "<URL de la page de la ligne>"}]``

Codes : 0 chaque reste en attente a sa ligne (ou aucun reste) ; 1 au moins un reste sans
ligne, une ligne par reste sur la sortie standard, « Reste sans ligne dans la base : … » ;
2 illisible : page ou export absent ou cassé, H2 « Journal d'exécution » absent, H3
« État final » absent, ou rubrique « Reste à faire » absente.
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
# <mention-page>. On ramène tout aux formes markdown avant toute lecture, pour que les
# expressions ci-dessous n'aient qu'un format à connaître.
GRAS_HTML = re.compile(r"<(b|strong)>(.*?)</\1>", re.S)
CODE_HTML = re.compile(r"<code>(.*?)</code>", re.S)
MENTION_HTML = re.compile(r'<mention-page\s+url="([^"]*)"\s*>(.*?)</mention-page>', re.S)

# « ### État final », éventuellement sous un <span> de couleur (règle du bleu des retouches).
ETAT_FINAL = re.compile(r"^###[ \t]+(?:<span[^>]*>[ \t]*)*état final\b", re.IGNORECASE)
# La clé « **Reste à faire** : » ; les deux graphies (le deux-points hors ou dans le gras).
CLE_RESTE = re.compile(
    r"^(?P<indent>[ \t]*)[-*][ \t]+\*\*Reste à faire(?:[ \t]*:)?\*\*[ \t]*:?(?P<reste>.*)$",
    re.IGNORECASE)
# Une clé de rubrique voisine : puce dont le texte commence par du gras.
CLE_GRAS = re.compile(r"^[ \t]*[-*][ \t]+\*\*[^*]+\*\*")
PUCE = re.compile(r"^(?P<indent>[ \t]*)[-*][ \t]+")
LIEN = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
URL = re.compile(r"https?://[^\s)\"<>]+")
ID_NOTION = re.compile(r"[0-9a-f]{32}")
# Une puce dont la valeur ne prouve rien : rubrique vide, sans reste.
VALEURS_VIDES = {"", "rien", "aucun", "aucune"}
CHAMPS_LIGNE = ("Reste", "Pour", "État", "Plan d'origine", "url")


class Illisible(Exception):
    """Entrée qui ne permet pas de contrôler (code 2)."""


def normaliser(texte: str) -> str:
    """Miroir du connecteur → formes markdown : gras, code, lien de page."""
    texte = GRAS_HTML.sub(lambda m: f"**{m.group(2)}**", texte)
    texte = CODE_HTML.sub(lambda m: f"`{html.unescape(m.group(1))}`", texte)
    return MENTION_HTML.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", texte)


def visible(texte: str) -> str:
    """Texte lu par Benjamin : sans liens (l'ancre reste), sans URL nue, sans balisage."""
    texte = LIEN.sub(lambda m: m.group(1), texte)
    texte = URL.sub("", texte)
    texte = re.sub(r"\*\*|`", "", texte)
    texte = re.sub(r"^[ \t]*[-*][ \t]+", "", texte, flags=re.M)
    return " ".join(texte.split())


def _cle(texte: str) -> str:
    """Forme de comparaison : visible, sans casse, sans ponctuation de bord."""
    return visible(texte).casefold().strip(" .;:—–-")


def _titre(ligne: str) -> str:
    return ligne[3:].strip().replace("’", "'").lower()


def _journal(texte: str) -> list[str]:
    """Lignes du H2 « Journal d'exécution », jusqu'au H2 suivant."""
    lignes: list[str] = []
    trouve = dedans = False
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dedans = _titre(ligne).startswith("journal d'exécution")
            trouve = trouve or dedans
            continue
        if dedans:
            lignes.append(ligne)
    if not trouve:
        raise Illisible("H2 « Journal d'exécution » absent")
    return lignes


def _etat_final(journal: list[str]) -> list[str]:
    """Lignes du H3 « État final », jusqu'au H3 suivant."""
    for i, ligne in enumerate(journal):
        if ETAT_FINAL.match(ligne):
            suite = []
            for suivante in journal[i + 1:]:
                if suivante.startswith("#"):
                    break
                suite.append(suivante)
            return suite
    raise Illisible("H3 « État final » absent du « Journal d'exécution »")


def _largeur(indentation: str) -> int:
    return len(indentation.expandtabs(4))


def _restes(etat: list[str]) -> list[str]:
    """Texte brut de chaque puce de premier niveau de la rubrique « Reste à faire »."""
    i = next((k for k, ligne in enumerate(etat) if CLE_RESTE.match(ligne)), None)
    if i is None:
        raise Illisible("rubrique « Reste à faire » absente de « État final »")
    cle = CLE_RESTE.match(etat[i])
    niveau_cle = _largeur(cle.group("indent"))
    corps = [cle.group("reste")] if cle.group("reste").strip() else []
    vide_avant = False
    for ligne in etat[i + 1:]:
        if not ligne.strip():
            vide_avant = True
            continue
        p = PUCE.match(ligne)
        indentation = _largeur(p.group("indent") if p else ligne[: len(ligne) - len(ligne.lstrip())])
        if p and CLE_GRAS.match(ligne) and indentation <= niveau_cle:
            break
        if not p and vide_avant and indentation <= niveau_cle:
            break
        corps.append(ligne)
        vide_avant = False
    niveaux = [_largeur(PUCE.match(l).group("indent")) for l in corps if PUCE.match(l)]
    niveau = min(niveaux, default=None)
    restes: list[list[str]] = []
    for ligne in corps:
        p = PUCE.match(ligne)
        if (p and _largeur(p.group("indent")) == niveau) or not restes:
            restes.append([ligne])
        else:
            restes[-1].append(ligne)
    return ["\n".join(bloc) for bloc in restes]


def _identifiant(url: str) -> str | None:
    """Identifiant Notion d'une URL : son dernier bloc de 32 hexadécimaux, tirets ôtés."""
    trouves = ID_NOTION.findall(url.split("?")[0].replace("-", "").lower())
    return trouves[-1] if trouves else None


def _porte_par_plan_de_suite(brut: str) -> bool:
    return any("reprise du plan" in ancre.casefold() for ancre, _ in LIEN.findall(brut))


def _satisfait(brut: str, ids_base: set[str], textes_base: list[str]) -> bool:
    if _porte_par_plan_de_suite(brut):
        return True
    ids_cites = {_identifiant(u) for u in URL.findall(brut)} - {None}
    if ids_cites & ids_base:
        return True
    vise = _cle(brut)
    return any(texte in vise for texte in textes_base)


def lire_lignes(chemin: str) -> list[dict]:
    try:
        donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Illisible(f"export « {chemin} » : {e}") from e
    if not isinstance(donnees, list):
        raise Illisible("l'export n'est pas une liste de lignes")
    for n, ligne in enumerate(donnees, 1):
        if not isinstance(ligne, dict):
            raise Illisible(f"ligne {n} : pas un objet")
        absents = [c for c in CHAMPS_LIGNE if c not in ligne]
        if absents:
            raise Illisible(f"ligne {n} : champ(s) absent(s) : {', '.join(absents)}")
        for champ in ("Reste", "url"):
            if not isinstance(ligne[champ], str):
                raise Illisible(f"ligne {n} : « {champ} » n'est pas un texte")
    return donnees


def controler(texte_page: str, lignes: list[dict]) -> tuple[list[str], int]:
    """(défauts, nombre de restes en attente) ; un défaut par reste sans ligne."""
    etat = _etat_final(_journal(normaliser(texte_page)))
    restes = [r for r in _restes(etat) if _cle(r) not in VALEURS_VIDES]
    ids_base = {_identifiant(ligne["url"]) for ligne in lignes} - {None}
    textes_base = [_cle(ligne["Reste"]) for ligne in lignes if _cle(ligne["Reste"])]
    defauts = [f"Reste sans ligne dans la base : {visible(r)}"
               for r in restes if not _satisfait(r, ids_base, textes_base)]
    return defauts, len(restes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    ap.add_argument("--lignes", required=True, help="export JSON des lignes de la base")
    a = ap.parse_args(argv)
    try:
        texte = Path(a.page).read_text(encoding="utf-8")
        lignes = lire_lignes(a.lignes)
        defauts, n = controler(texte, lignes)
    except (OSError, ValueError, Illisible) as e:
        print(f"illisible : {e}", file=sys.stderr)
        return 2
    for defaut in defauts:
        print(defaut)
    if defauts:
        return 1
    if n:
        print(f"restes : {n} reste(s) en attente, tous ont leur ligne")
    else:
        print("restes : aucun reste en attente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
