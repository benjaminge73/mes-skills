#!/usr/bin/env python3
"""Un renvoi entre fichiers de skill qui pointe dans le vide est silencieux.

Un skill se renvoie à un compagnon avec une ligne du type
``📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md` `` : rien ne
casse au chargement, le skill se lance, la panne n'apparaît qu'au moment où la
session essaie de lire ce compagnon — trop tard pour la corriger avant qu'elle
n'échoue en plein travail. Ce mode de défaillance est exactement celui du
garde de version (``plugin_version_guard.py``) : muet des deux côtés, jusqu'à
ce que quelqu'un tombe dessus en session.

Ce script n'attrape pas tout ce qui peut rendre un renvoi trompeur — le
2026-09-08, deux skills annonçaient encore « les trois pièges » d'un fichier
qui en portait cinq, et ça, aucun script ne le voit sans lire le contenu des
deux côtés. Il attrape le cran d'avant, strictement mécanique : le fichier
cité n'existe plus, ou n'a jamais existé.

Un fichier à phases (des titres ``### Phase N``) a le même défaut : un renvoi
« Phase 4.5 » vers une section qui n'existe pas ne casse rien, et le lecteur le
découvre au mauvais moment. Ce script refuse donc, dans un tel fichier, toute
mention « Phase N » qui ne désigne aucun de ses titres.

Il vérifie aussi, dans la foulée et pour la même raison de coût nul, une
deuxième invariant que ``claude plugin validate`` ne couvre pas dans le détail
qui nous intéresse ici : chaque ``SKILL.md`` et chaque agent commence par un
frontmatter exploitable (``name:`` et ``description:`` présents), et le
``name`` d'un skill correspond au nom de son dossier — sans quoi Claude Code
ne le retrouve pas sous le nom qu'on croit lui donner.

Aucune dépendance externe (pas de PyYAML) : le frontmatter est lu ligne à
ligne, pas parsé comme du YAML complet.

Codes de sortie : ``0`` si tout est cohérent, ``1`` sinon.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"

# Un guillemet, simple ou double, ne fait jamais partie d'un chemin : sans
# lui dans la classe exclue, `cat "${CLAUDE_PLUGIN_ROOT}/x.json"` capturait
# `x.json"` et signalait un fichier introuvable qui existait (2026-09-08).
REFERENCE_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^`\s)\"']+)")

# Titre d'une phase (« ### Phase 4: … ») et renvoi à une phase (« Phase 4.5 »).
# Le numéro peut porter une décimale : sans elle, « Phase 4.5 » se lirait
# « Phase 4 » et passerait dès que la phase 4 existe.
PHASE_TITRE_RE = re.compile(r"^#+ Phase (\d+(?:\.\d+)?)\b")
PHASE_RENVOI_RE = re.compile(r"\bPhase (\d+(?:\.\d+)?)\b")


def _relatif(chemin: Path) -> str:
    return chemin.relative_to(REPO_ROOT).as_posix()


def verifier_renvois() -> tuple[list[str], int]:
    """Chaque `${CLAUDE_PLUGIN_ROOT}/...` doit désigner un fichier du plugin."""
    problemes: list[str] = []
    verifies = 0

    if not PLUGINS_DIR.is_dir():
        return problemes, verifies

    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir() or plugin_dir.name.startswith("."):
            continue

        for md_file in sorted(plugin_dir.rglob("*.md")):
            rel = _relatif(md_file)
            try:
                lignes = md_file.read_text(encoding="utf-8").splitlines()
            except OSError as erreur:
                problemes.append(f"{rel}:1 — illisible ({erreur})")
                continue

            for numero, ligne in enumerate(lignes, start=1):
                for correspondance in REFERENCE_RE.finditer(ligne):
                    chemin = correspondance.group(1)
                    verifies += 1
                    cible = plugin_dir / chemin
                    if not cible.is_file():
                        problemes.append(
                            f"{rel}:{numero} — renvoi introuvable : "
                            f"${{CLAUDE_PLUGIN_ROOT}}/{chemin}"
                        )

    return problemes, verifies


def _frontmatter(lignes: list[str]) -> tuple[list[str], str | None]:
    """Rend les lignes du frontmatter, ou None si le fichier n'en a pas.

    Ne parse pas le YAML : se contente de délimiter le bloc entre les deux
    lignes ``---`` et de rendre son contenu brut, ligne à ligne.
    """
    if not lignes or lignes[0].strip() != "---":
        return [], "le fichier ne commence pas par `---`"

    for index in range(1, len(lignes)):
        if lignes[index].strip() == "---":
            return lignes[1:index], None

    return [], "frontmatter jamais refermé (pas de second `---`)"


def _valeur_champ(bloc: list[str], champ: str) -> str | None:
    prefixe = f"{champ}:"
    for ligne in bloc:
        nettoyee = ligne.strip()
        if nettoyee.startswith(prefixe):
            valeur = nettoyee[len(prefixe):].strip()
            return valeur.strip("\"'")
    return None


# Une valeur YAML « nue » (sans guillemets) ne peut ni commencer par un
# indicateur réservé, ni contenir `: ` (lu comme une nouvelle clé), ni ` #`
# (lu comme un commentaire). Le 2026-09-23, « son existence : écart au plan »
# dans la description de l'agent relecteur a cassé tout le frontmatter : Claude
# Code chargeait alors l'agent sans aucune métadonnée — ni `model`, ni `effort`,
# ni `disallowedTools` — et la CLI locale ne le signalait pas.
_INDICATEURS_DE_DEBUT = tuple("`@%!&*")
_DEBUTS_NON_NUS = ("\"", "'", "|", ">", "[", "{")


def erreurs_yaml_scalaires(bloc: list[str]) -> list[str]:
    """Signale les valeurs nues de premier niveau qu'un parseur YAML refuserait.

    Sans PyYAML : ne regarde que les lignes `clé: valeur` non indentées, et
    laisse passer tout ce qui est cité, en bloc (`|`, `>`) ou en flux (`[`, `{`).
    """
    erreurs: list[str] = []
    for ligne in bloc:
        if not ligne or ligne[0] in " \t-#" or ":" not in ligne:
            continue
        cle, _, valeur = ligne.partition(":")
        valeur = valeur.strip()
        if not valeur or valeur.startswith(_DEBUTS_NON_NUS):
            continue
        if valeur.startswith(_INDICATEURS_DE_DEBUT):
            erreurs.append(
                f"`{cle}` commence par `{valeur[0]}`, réservé en YAML : "
                "mettre la valeur entre guillemets"
            )
        elif ": " in valeur or valeur.endswith(":"):
            erreurs.append(
                f"`{cle}` contient « : » hors guillemets, que YAML lit comme "
                "une nouvelle clé : remplacer par « — » ou citer la valeur"
            )
        elif " #" in valeur:
            erreurs.append(
                f"`{cle}` contient « #» précédé d'une espace, que YAML lit "
                "comme un commentaire : citer la valeur"
            )
    return erreurs


def verifier_frontmatters() -> tuple[list[str], int]:
    """SKILL.md et agents/*.md : frontmatter exploitable, `name` cohérent."""
    problemes: list[str] = []
    verifies = 0

    fichiers = sorted(PLUGINS_DIR.glob("*/skills/*/SKILL.md")) + sorted(
        PLUGINS_DIR.glob("*/agents/*.md")
    )

    for fichier in fichiers:
        rel = _relatif(fichier)
        verifies += 1
        try:
            lignes = fichier.read_text(encoding="utf-8").splitlines()
        except OSError as erreur:
            problemes.append(f"{rel}:1 — illisible ({erreur})")
            continue

        bloc, erreur_bloc = _frontmatter(lignes)
        if erreur_bloc is not None:
            problemes.append(f"{rel}:1 — {erreur_bloc}")
            continue

        for erreur_yaml in erreurs_yaml_scalaires(bloc):
            problemes.append(f"{rel}:1 — frontmatter YAML invalide : {erreur_yaml}")

        nom = _valeur_champ(bloc, "name")
        if nom is None:
            problemes.append(f"{rel}:1 — frontmatter sans ligne `name:`")

        if _valeur_champ(bloc, "description") is None:
            problemes.append(f"{rel}:1 — frontmatter sans ligne `description:`")

        # Le nom du dossier ne fait foi que pour un skill (skills/<nom>/SKILL.md) :
        # un agent n'a pas de dossier qui porte son nom de la même façon.
        est_skill = fichier.parent.parent.name == "skills"
        if est_skill and nom is not None and nom != fichier.parent.name:
            problemes.append(
                f"{rel}:1 — `name: {nom}` ne correspond pas au dossier "
                f"`{fichier.parent.name}`"
            )

    return problemes, verifies


def _titres_phase(lignes: list[str]) -> set[str]:
    """Les numéros des titres « Phase N » du fichier."""
    titres: set[str] = set()
    for ligne in lignes:
        correspondance = PHASE_TITRE_RE.match(ligne)
        if correspondance:
            titres.add(correspondance.group(1))
    return titres


def renvois_phase(lignes: list[str]) -> list[tuple[int, str]]:
    """Rend (ligne, numéro) de chaque mention « Phase N » hors titre.

    Un fichier sans aucun titre « Phase N » n'est pas un fichier à phases : la
    mention y est une formule libre, rien n'est rendu.
    """
    if not _titres_phase(lignes):
        return []

    renvois: list[tuple[int, str]] = []
    for numero, ligne in enumerate(lignes, start=1):
        if PHASE_TITRE_RE.match(ligne):
            continue
        for correspondance in PHASE_RENVOI_RE.finditer(ligne):
            renvois.append((numero, correspondance.group(1)))
    return renvois


def phases_absentes(lignes: list[str]) -> list[tuple[int, str]]:
    """Rend (ligne, numéro) des renvois « Phase N » sans titre correspondant.

    Un renvoi peut précéder le titre qu'il désigne (c'est le cas dans un skill
    qui cite « Phase 1 » dans son introduction) : on lit les titres d'abord.
    """
    titres = _titres_phase(lignes)
    return [
        (numero, phase)
        for numero, phase in renvois_phase(lignes)
        if phase not in titres
    ]


def verifier_phases() -> tuple[list[str], int]:
    """Dans un fichier à phases, chaque renvoi « Phase N » désigne un titre."""
    problemes: list[str] = []
    verifies = 0

    if not PLUGINS_DIR.is_dir():
        return problemes, verifies

    for md_file in sorted(PLUGINS_DIR.rglob("*.md")):
        rel = _relatif(md_file)
        try:
            lignes = md_file.read_text(encoding="utf-8").splitlines()
        except OSError as erreur:
            problemes.append(f"{rel}:1 — illisible ({erreur})")
            continue

        verifies += len(renvois_phase(lignes))
        for numero, phase in phases_absentes(lignes):
            problemes.append(
                f"{rel}:{numero} — renvoi à une phase absente : Phase {phase}"
            )

    return problemes, verifies


def main() -> int:
    problemes_renvois, nb_renvois = verifier_renvois()
    problemes_frontmatters, nb_frontmatters = verifier_frontmatters()
    problemes_phases, nb_phases = verifier_phases()
    problemes = problemes_renvois + problemes_frontmatters + problemes_phases

    if problemes:
        for probleme in problemes:
            print(probleme)
        return 1

    print(
        f"Renvois : {nb_renvois} vérifiés, frontmatters : {nb_frontmatters} "
        f"vérifiés, phases : {nb_phases} vérifiées"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
