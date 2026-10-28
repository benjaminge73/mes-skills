#!/usr/bin/env python3
"""Garde CI de la ligne `Doc :` dans la description d'une PR.

Pourquoi : la règle de doc vivante (une entrée de Changelog par PR, ou une raison dite)
n'était tenue que par la session qui ouvre la PR. Relevé du 2026-10-28 : 21 PR de ce dépôt
sans ligne `Doc :` depuis le 2026-10-20, et des « sans objet » dont la raison est fausse
(« la page projet n'a pas été consultée », « pas de job doc dans la CI »). Une règle que
seule la session vérifie se saute sans que personne le voie ; celle-ci, la CI la lit.

Deux formes acceptées, sur une ligne qui commence par `Doc :` (gras Markdown toléré) :
  Doc : https://app.notion.com/p/...      lien vers l'entrée du Changelog (Notion)
  Doc : sans objet — <raison>             tiret long, demi-cadratin ou tiret simple

Refusés : une ligne absente ou vide ; un lien qui ne va pas vers Notion (le lien de la PR
elle-même n'est pas une entrée) ; « sans objet » sans raison ; une raison de la liste
RAISONS_REFUSEES, qui répète un contresens déjà relevé. C'est l'encadré de la page projet qui
dit si la doc vivante s'applique, jamais la présence de ce job ; et ne pas avoir lu la page
n'est pas une raison. Plusieurs lignes `Doc :` : la première valide suffit.

L'auteur Dependabot passe sans que le corps soit lu (`dependabot[bot]`, `app/dependabot`).

Le corps arrive par la variable d'environnement PR_BODY (relu par l'API dans ci.yml, jamais
interpolé dans le YAML), l'auteur par PR_AUTHOR. Codes : 0 accepté, 1 refusé, 2 panne
(PR_BODY absent), 4 aucune valeur écrite après `Doc :` (le job attend, puis refuse). Bibliothèque standard uniquement.
"""
from __future__ import annotations

import os
import re
import sys

LIGNE_DOC = re.compile(r"^\**\s*Doc\s*\**\s*:\s*\**\s*(.*)$")
LIEN_NOTION = re.compile(r"^<?https://(?:app\.|www\.)?notion\.(?:so|com|site)/\S+$")
LIEN = re.compile(r"^<?https?://\S+")
SANS_OBJET = re.compile(r"^sans objet\s*[—–-]\s*(\S.*)$", re.IGNORECASE)
RAISON_MIN = 15
ATTENTE = 4

# Chaque motif vient d'une PR réelle relevée le 2026-10-28 ; la raison dit le contresens.
RAISONS_REFUSEES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"pas (été |encore )?(consult|lu|regard)", re.IGNORECASE),
     "ne pas avoir lu la page projet n'est pas une raison : la lire, puis décider"),
    (re.compile(r"(pas|aucun|sans)( de)? job `?doc", re.IGNORECASE),
     "la doc vivante dépend de l'encadré de la page projet, jamais de la présence de ce job"),
    (re.compile(r"(pas de|aucun|sans) changelog", re.IGNORECASE),
     "un projet à doc vivante activée a un Changelog : l'entrée y va"),
    (re.compile(r"(entrée|doc) à venir|plus tard|à faire|en attente", re.IGNORECASE),
     "« à venir » est une fausse déclaration : écrire l'entrée, puis mettre son lien"),
    (re.compile(r"document[ée]e? dans (le |la |les )?(readme|docs?/|\.env)", re.IGNORECASE),
     "la doc du dépôt ne remplace pas l'entrée du Changelog, qui dit ce qui change pour l'utilisateur"),
]

AIDE = ("Écris une ligne « Doc : <lien Notion de l'entrée du Changelog> », ou "
        "« Doc : sans objet — <raison> » si la PR n'a aucun effet visible pour la personne "
        "qui se sert du projet. Puis édite la description et relance le job doc.")


def est_dependabot(auteur: str | None) -> bool:
    return (auteur or "").lower() in {"dependabot[bot]", "app/dependabot"}


def verifier_doc(corps: str | None, auteur: str | None = None) -> tuple[bool, str]:
    """Rend (accepté, raison) pour la description `corps` d'une PR de `auteur`."""
    if est_dependabot(auteur):
        return True, "auteur Dependabot : description non lue."
    valeurs = []
    for brute in (corps or "").splitlines():
        m = LIGNE_DOC.match(brute.strip())
        if m:
            valeurs.append(m.group(1).strip().strip("*").strip())
    if not valeurs:
        return False, f"aucune ligne « Doc : » dans la description. {AIDE}"
    defauts = []
    for valeur in valeurs:
        if LIEN_NOTION.match(valeur):
            return True, f"lien vers le Changelog : {valeur}"
        if LIEN.match(valeur):
            defauts.append(f"« {valeur} » n'est pas un lien Notion vers l'entrée du Changelog")
            continue
        sans_objet = SANS_OBJET.match(valeur)
        if not sans_objet:
            defauts.append("ligne vide" if not valeur else f"forme inconnue : « {valeur} »")
            continue
        raison = sans_objet.group(1).strip()
        refus = next((pourquoi for motif, pourquoi in RAISONS_REFUSEES if motif.search(raison)), None)
        if refus:
            defauts.append(f"raison refusée (« {raison} ») : {refus}")
        elif len(raison) < RAISON_MIN:
            defauts.append(f"raison trop courte (« {raison} ») : dire pourquoi rien ne change pour l'utilisateur")
        else:
            return True, f"sans objet — {raison}"
    return False, "; ".join(defauts) + f". {AIDE}"


def doc_pas_encore_ecrite(corps: str | None, auteur: str | None = None) -> bool:
    """Vrai si la description n'a encore aucune valeur après `Doc :` (ligne absente ou vide).

    C'est l'état de toute PR qui vient de s'ouvrir : l'entrée du Changelog cite le numéro de
    la PR, donc ne peut s'écrire qu'après elle. Une ligne mal formée ou à raison refusée n'est
    pas « pas encore écrite » : elle est fausse, et reste refusée tout de suite."""
    if est_dependabot(auteur):
        return False
    for brute in (corps or "").splitlines():
        m = LIGNE_DOC.match(brute.strip())
        if m and m.group(1).strip().strip("*").strip():
            return False
    return True


def main() -> int:
    auteur = os.environ.get("PR_AUTHOR")
    if "PR_BODY" not in os.environ and not est_dependabot(auteur):
        print("garde_doc_pr : PR_BODY absent (panne de lecture, pas un refus)", file=sys.stderr)
        return 2
    ok, raison = verifier_doc(os.environ.get("PR_BODY"), auteur)
    if ok:
        print(f"Doc : {raison}")
        return 0
    print(f"::error title=Ligne Doc::{raison}")
    # Code 4 : rien n'est encore écrit après `Doc :`. Le job `doc` de ci.yml attend alors que
    # la description se remplisse au lieu de rougir (voir `attendre-la-ligne-doc`).
    return ATTENTE if doc_pas_encore_ecrite(os.environ.get("PR_BODY"), auteur) else 1


if __name__ == "__main__":
    sys.exit(main())
