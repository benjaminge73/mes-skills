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

REFERENCE_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^`\s)]+)")


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


def main() -> int:
    problemes_renvois, nb_renvois = verifier_renvois()
    problemes_frontmatters, nb_frontmatters = verifier_frontmatters()
    problemes = problemes_renvois + problemes_frontmatters

    if problemes:
        for probleme in problemes:
            print(probleme)
        return 1

    print(f"Renvois : {nb_renvois} vérifiés, frontmatters : {nb_frontmatters} vérifiés")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
