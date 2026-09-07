#!/usr/bin/env python3
"""Le manifeste de la marketplace et le contenu du dépôt disent la même chose.

Deux moitiés, et il faut les deux : un plugin décrit dans
``.claude-plugin/marketplace.json`` mais absent du disque casse l'installation
pour tout le monde ; un plugin présent sous ``plugins/`` mais absent du
manifeste ne s'installe **nulle part** et personne ne s'en aperçoit — c'est
un dossier de fichiers qui a l'air d'un plugin et qui n'en est pas un.

Ce script ne remplace pas ``claude plugin validate`` (qui, lui, connaît le
schéma complet) : il tient l'invariant que le schéma ne voit pas, à savoir la
correspondance entre les deux surfaces. Il ne dépend de rien d'autre que de
la bibliothèque standard, pour tourner en CI sans installation préalable.

Codes de sortie : ``0`` cohérent, ``1`` incohérent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO_ROOT / "plugins"
MANIFEST_SUFFIX = Path(".claude-plugin") / "plugin.json"


def _lire_json(chemin: Path) -> dict | None:
    try:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return contenu if isinstance(contenu, dict) else None


def anomalies() -> list[str]:
    """Tout ce qui empêche ce dépôt de distribuer ce qu'il prétend."""
    manifeste = _lire_json(MARKETPLACE)
    if manifeste is None:
        return [f"{MARKETPLACE.name} est absent ou illisible."]

    declares: dict[str, dict] = {}
    trouvees: list[str] = []

    entrees = manifeste.get("plugins")
    if not isinstance(entrees, list):
        return [f"{MARKETPLACE.name} ne déclare pas de liste `plugins`."]

    for entree in entrees:
        if not isinstance(entree, dict):
            trouvees.append("Une entrée de `plugins` n'est pas un objet.")
            continue
        nom = entree.get("name")
        if not isinstance(nom, str) or not nom:
            trouvees.append("Une entrée de `plugins` n'a pas de `name`.")
            continue
        declares[nom] = entree

    for nom, entree in sorted(declares.items()):
        source = entree.get("source")
        if not isinstance(source, str) or not source.startswith("./plugins/"):
            trouvees.append(
                f"{nom} : `source` doit être un chemin relatif « ./plugins/<nom> », "
                f"pas {source!r}."
            )
            continue

        racine = REPO_ROOT / source[2:]
        if not racine.is_dir():
            trouvees.append(f"{nom} : {source} n'existe pas dans le dépôt.")
            continue

        plugin = _lire_json(racine / MANIFEST_SUFFIX)
        if plugin is None:
            trouvees.append(
                f"{nom} : {source}/{MANIFEST_SUFFIX.as_posix()} est absent ou illisible."
            )
            continue

        if plugin.get("name") != nom:
            trouvees.append(
                f"{nom} : son manifeste s'appelle {plugin.get('name')!r}. "
                "Claude Code installe sous le nom du manifeste, pas celui du "
                "marketplace — les deux doivent coïncider."
            )

        if not isinstance(plugin.get("version"), str) or not plugin["version"]:
            trouvees.append(
                f"{nom} : son manifeste ne déclare pas de `version` lisible. "
                "C'est cette chaîne, et elle seule, qui dit aux sessions "
                "installées qu'il y a quelque chose à récupérer."
            )

    if PLUGINS_DIR.is_dir():
        for dossier in sorted(PLUGINS_DIR.iterdir()):
            if not dossier.is_dir() or dossier.name.startswith("."):
                continue
            if dossier.name not in declares:
                trouvees.append(
                    f"plugins/{dossier.name}/ existe mais n'est pas déclaré dans "
                    f"{MARKETPLACE.name} : il ne s'installera nulle part."
                )

    return trouvees


def main() -> int:
    trouvees = anomalies()
    if trouvees:
        print(
            "Cohérence de la marketplace — ce dépôt ne distribue pas ce qu'il "
            "annonce :\n  " + "\n  ".join(trouvees),
            file=sys.stderr,
        )
        return 1

    print(
        "Cohérence de la marketplace : respectée "
        f"({len(_lire_json(MARKETPLACE)['plugins'])} plugin(s) déclaré(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
