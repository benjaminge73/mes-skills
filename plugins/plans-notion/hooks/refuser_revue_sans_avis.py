#!/usr/bin/env python3
"""Hook PreToolUse : pas de ``Statut`` « en revue » sans avis de Hal enregistré.

Deux chemins, un seul contrat :
- l'outil MCP Notion (``notion-update-page``, ``notion-create-pages``) ;
- ``composio execute NOTION_UPDATE_PAGE`` lancé dans Bash (slug entier : le slug
  ``NOTION_UPDATE_PAGE_MARKDOWN`` ne pose pas de propriété et passe).

L'avis est au registre ``~/.hermes/state/relectures-hal/<id de page, 32 caractères>.json``
(dossier surchargeable par ``HERMES_RELECTURES_DIR``), écrit par ``demander_a_hal.py relire``.
Le registre laisse passer si le tour 1 rend ``OK``, si un tour 2 a été rendu (quel que
soit son verdict), ou si deux échecs sont notés, quel que soit leur numéro de tour.

Le hook ne s'active que si le script de Hal (``PLANS_NOTION_DEMANDER_A_HAL``, défaut
``~/.hermes/scripts/demander_a_hal.py``) existe et déclare ``RELECTURE_DISPONIBLE = True`` ;
sinon il se tait (poste sans Hermes).
Refus : code 2, motif sur stderr, qui cite la commande ``relire``. Permis : code 0, sans sortie.
Entrée illisible : code 0 (cas prévu) avec un mot sur stderr. Un plantage, un délai dépassé ou un
interpréteur introuvable bloquent l'appel, par ``onFailure: "block"`` dans hooks.json (Claude Code
2.1.295 ou plus) ; l'entrée Bash étant sur toute commande Bash, une panne du script bloquerait
toute commande Bash.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
import unicodedata
from pathlib import Path

CIBLE = "en revue"
SLUG_COMPOSIO = "NOTION_UPDATE_PAGE"
OUTILS_NOTION = ("notion-update-page", "notion-create-pages")
SEPARATEURS_SHELL = ("&&", "||", ";", "|")
MARQUEUR_HAL = re.compile(r"^RELECTURE_DISPONIBLE\s*=\s*True\b", re.MULTILINE)


def _sans_accent(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if not unicodedata.combining(c))


def _est_en_revue(valeur) -> bool:
    """Vrai si une valeur de propriété vaut « en revue », texte brut ou objet Notion imbriqué."""
    if isinstance(valeur, str):
        return _sans_accent(valeur).strip().lower() == CIBLE
    if isinstance(valeur, dict):
        return any(_est_en_revue(v) for v in valeur.values())
    if isinstance(valeur, list):
        return any(_est_en_revue(v) for v in valeur)
    return False


def _pose_en_revue(proprietes) -> bool:
    return isinstance(proprietes, dict) and "Statut" in proprietes and _est_en_revue(proprietes["Statut"])


def _cibles_notion(entree: dict) -> list:
    """Une entrée par page que la charge Notion pose en revue : son id, ou None si la page est nouvelle."""
    cibles = []
    if _pose_en_revue(entree.get("properties")):
        cibles.append(entree.get("page_id"))
    for page in entree.get("pages") or []:
        if isinstance(page, dict) and _pose_en_revue(page.get("properties")):
            cibles.append(None)
    return cibles


def _charge_composio(segment: list[str]):
    """La charge JSON de ``-d`` / ``--data`` (en ligne ou ``@fichier``), ou None si elle n'est pas lisible."""
    for position, mot in enumerate(segment):
        if mot in SEPARATEURS_SHELL:
            return None
        if mot in ("-d", "--data"):
            if position + 1 >= len(segment):
                return None
            valeur = segment[position + 1]
        elif mot.startswith("--data="):
            valeur = mot[len("--data="):]
        elif mot.startswith("-d@"):
            valeur = mot[len("-d"):]
        else:
            continue
        try:
            if valeur == "-":
                return None  # charge lue sur l'entrée standard : hors de la commande
            if valeur.startswith("@"):
                valeur = Path(os.path.expanduser(valeur[1:])).read_text(encoding="utf-8")
            return json.loads(valeur)
        except (OSError, ValueError):
            return None
    return None


def _cibles_composio(commande) -> list:
    """Une entrée par ``composio execute NOTION_UPDATE_PAGE`` qui pose « en revue » : son id, ou None."""
    if not isinstance(commande, str):
        return []
    try:
        mots = shlex.split(commande)
    except ValueError:
        return []
    cibles = []
    for i in range(len(mots) - 2):
        if (os.path.basename(mots[i]) == "composio" and mots[i + 1] == "execute"
                and mots[i + 2] == SLUG_COMPOSIO):
            charge = _charge_composio(mots[i + 3:])
            if isinstance(charge, dict) and _pose_en_revue(charge.get("properties")):
                cibles.append(charge.get("page_id"))
    return cibles


def _script_hal() -> Path:
    return Path(os.path.expanduser(os.environ.get("PLANS_NOTION_DEMANDER_A_HAL") or "~/.hermes/scripts/demander_a_hal.py"))


def _hal_disponible() -> bool:
    try:
        return bool(MARQUEUR_HAL.search(_script_hal().read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return False


def _registre() -> Path:
    return Path(os.path.expanduser(os.environ.get("HERMES_RELECTURES_DIR") or "~/.hermes/state/relectures-hal"))


def _identifiant(page) -> str | None:
    """Les 32 caractères hexadécimaux qui terminent l'adresse ou l'id Notion, ou None.

    Lit le chemin seulement (avant ``?`` et ``#``), son dernier segment, tirets retirés :
    l'id est à la fin de l'adresse, et un titre qui finit par un caractère hexadécimal
    (« revue ») ne doit pas décaler l'id.
    """
    if not isinstance(page, str):
        return None
    chemin = re.split(r"[?#]", page, maxsplit=1)[0].rstrip("/")
    dernier = chemin.rsplit("/", 1)[-1]
    trouve = re.search(r"[0-9a-f]{32}\Z", dernier.lower().replace("-", ""))
    return trouve.group(0) if trouve else None


def _motif_sans_avis(registre: Path, page) -> str | None:
    """None si Hal a rendu un avis suffisant pour cette page, sinon le motif du refus."""
    ident = _identifiant(page)
    if ident is None:
        return "page sans identifiant (création, ou charge sans page_id) : aucun avis ne peut lui être rattaché"
    fichier = registre / f"{ident}.json"
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return f"aucun avis de Hal enregistré pour la page {ident}"
    except (OSError, ValueError):
        return f"registre illisible ({fichier})"
    try:
        tours = donnees["tours"]
        rendus = {t["tour"]: t for t in tours if t.get("issue") == "ok"}
        echecs = [t for t in tours if t.get("issue") != "ok"]
    except (KeyError, TypeError, AttributeError):
        return f"registre illisible ({fichier})"
    if 1 in rendus and rendus[1].get("verdict") == "OK":
        return None
    if 2 in rendus:
        return None
    if len(echecs) >= 2:
        return None
    return f"l'avis de Hal ne permet pas encore la mise en revue (registre : {fichier})"


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if not isinstance(donnees, dict):
            raise ValueError("l'entrée n'est pas un objet")
        outil = donnees.get("tool_name")
        entree = donnees.get("tool_input") or {}
        if not isinstance(entree, dict):
            raise ValueError("tool_input n'est pas un objet")
        if outil == "Bash":
            cibles = _cibles_composio(entree.get("command"))
        elif isinstance(outil, str) and outil.endswith(OUTILS_NOTION):
            cibles = _cibles_notion(entree)
        else:
            return 0
    except Exception as erreur:
        print(f"refuser_revue_sans_avis : entrée ignorée ({type(erreur).__name__}: {erreur})",
              file=sys.stderr)
        return 0
    if not cibles or not _hal_disponible():
        return 0
    registre = _registre()
    for page in cibles:
        motif = _motif_sans_avis(registre, page)
        if motif is not None:
            print(f"Refusé : `Statut` ne passe pas à « en revue » sans avis de Hal ({motif}). "
                  "Lancer d'abord la relecture : `demander_a_hal.py relire`, puis poser « en revue ».",
                  file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
