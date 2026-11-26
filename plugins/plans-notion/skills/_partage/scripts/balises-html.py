#!/usr/bin/env python3
"""Balises HTML écrites en texte dans une page Notion : contrôle et conversion.

Cause : le connecteur claude.ai Notion lit et écrit le gras en ``<b>…</b>`` et le code
en ``<code>…</code>`` ; la commande ``composio`` (API markdown publique de Notion) ne les
interprète pas et les enregistre en texte littéral. Ce script :

- ``controler <fichier>`` : code 0 si aucune balise ``<b>``, ``<strong>``, ``<i>``,
  ``<em>``, ``<code>`` (brute, ou échappée ``\\<b\\>``) ne traîne hors code ; code 1 sinon,
  une ligne ``fichier:numéro: balise`` par occurrence ; code 2 si le fichier est illisible.
- ``nettoyer <fichier>`` : écrit sur stdout le texte converti en markdown (gras ``**``,
  italique ``*``, code en backticks). Idempotent. Ne touche ni au contenu entre backticks,
  ni aux blocs de code, ni aux cases ``- [ ]`` / ``- [x]``.

Limites écrites : une balise coupée sur deux lignes n'est pas vue (le contrôle se fait
ligne à ligne) ; un ``<code>`` non refermé est converti en backtick seul.

Le hook ``hooks/refuser_balises_composio.py`` importe ``balises_hors_code`` et
``nettoyer_texte`` depuis ce fichier : une seule définition de ce qu'est une balise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Brute ou échappée (« \<b\> »), balise ouvrante ou fermante, insensible à la casse.
BALISE = re.compile(r"\\?<\\?(/?)(b|strong|i|em|code)\\?>", re.IGNORECASE)
CANONIQUE = {"strong": "b", "em": "i"}
SPAN_CODE = re.compile(r"`[^`\n]*`")
CLOTURE_DE_BLOC = re.compile(r"^\s*```")
# Deux gras (ou italiques) séparés seulement par des balises de code ou des blancs : un seul.
FUSION = re.compile(r"</(b|i)>((?:\s|</?code>)*)<\1>")
CODE_HTML = re.compile(r"<code>(.*?)</code>")
LIEN_AUTOMATIQUE = re.compile(r"\[([^\]\n]+)\]\((?:https?://)?\1\)")


def _masquer_code_en_ligne(ligne: str) -> str:
    """Le contrôle ne lit pas ce qui est entre backticks : on l'efface, longueur gardée."""
    return SPAN_CODE.sub(lambda m: " " * len(m.group(0)), ligne)


def balises_hors_code(texte: str) -> list[tuple[int, str]]:
    """Les occurrences de balise hors code, sous forme ``(numéro de ligne, balise brute)``."""
    occurrences = []
    dans_bloc = False
    for numero, ligne in enumerate(texte.splitlines(), start=1):
        if CLOTURE_DE_BLOC.match(ligne):
            dans_bloc = not dans_bloc
            continue
        if dans_bloc:
            continue
        for m in BALISE.finditer(_masquer_code_en_ligne(ligne)):
            occurrences.append((numero, m.group(0)))
    return occurrences


def _nom_canonique(m: re.Match) -> str:
    nom = m.group(2).lower()
    return f"<{m.group(1)}{CANONIQUE.get(nom, nom)}>"


def _code(m: re.Match) -> str:
    contenu = re.sub(r"</?(?:b|i)>", "", m.group(1))
    contenu = LIEN_AUTOMATIQUE.sub(r"\1", contenu)
    coeur = contenu.strip()
    if not coeur:
        return contenu
    debut = contenu[: len(contenu) - len(contenu.lstrip())]
    fin = contenu[len(contenu.rstrip()):]
    return f"{debut}`{coeur}`{fin}"


def _enrober(texte: str, balise: str, marque: str) -> str:
    """``<balise>x</balise>`` devient ``marque x marque``, les blancs de bord restant dehors."""
    def remplacer(m: re.Match) -> str:
        contenu = m.group(1)
        coeur = contenu.strip()
        if not coeur:
            return contenu
        debut = contenu[: len(contenu) - len(contenu.lstrip())]
        fin = contenu[len(contenu.rstrip()):]
        return f"{debut}{marque}{coeur}{marque}{fin}"

    return re.sub(rf"<{balise}>(.*?)</{balise}>", remplacer, texte)


def _convertir_ligne(ligne: str) -> str:
    # Les spans en backticks déjà présents sont mis de côté : leur contenu ne bouge pas.
    gardes: list[str] = []

    def mettre_de_cote(m: re.Match) -> str:
        gardes.append(m.group(0))
        return f"\x00{len(gardes) - 1}\x00"

    texte = SPAN_CODE.sub(mettre_de_cote, ligne)
    texte = BALISE.sub(_nom_canonique, texte)
    while True:
        fusionne = FUSION.sub(r"\2", texte)
        if fusionne == texte:
            break
        texte = fusionne
    texte = CODE_HTML.sub(_code, texte)
    texte = _enrober(texte, "i", "*")
    texte = _enrober(texte, "b", "**")
    # Balises restées sans paire : converties une à une, pour qu'aucune ne traîne.
    for brute, neuve in (("<b>", "**"), ("</b>", "**"), ("<i>", "*"), ("</i>", "*"),
                         ("<code>", "`"), ("</code>", "`")):
        texte = texte.replace(brute, neuve)
    return re.sub(r"\x00(\d+)\x00", lambda m: gardes[int(m.group(1))], texte)


def nettoyer_texte(texte: str) -> str:
    """Le texte avec ses balises converties en markdown ; blocs de code et cases intacts."""
    sortie = []
    dans_bloc = False
    for ligne in texte.split("\n"):
        if CLOTURE_DE_BLOC.match(ligne):
            dans_bloc = not dans_bloc
            sortie.append(ligne)
            continue
        if dans_bloc:
            sortie.append(ligne)
            continue
        sortie.append(_convertir_ligne(ligne))
    return "\n".join(sortie)


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("controler", "nettoyer"):
        print("usage : balises-html.py controler|nettoyer <fichier>", file=sys.stderr)
        return 2
    try:
        texte = Path(argv[2]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as erreur:
        print(f"balises-html : fichier illisible ({erreur})", file=sys.stderr)
        return 2
    if argv[1] == "nettoyer":
        sys.stdout.write(nettoyer_texte(texte))
        return 0
    occurrences = balises_hors_code(texte)
    for numero, balise in occurrences:
        print(f"{argv[2]}:{numero}: {balise}")
    return 1 if occurrences else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
