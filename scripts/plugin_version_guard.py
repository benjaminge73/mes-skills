#!/usr/bin/env python3
"""Refuser une PR qui change un plugin sans bouger sa version.

Pourquoi ce garde-fou existe
----------------------------
Le 2026-09-01, quatre PR mergées et déployées — #345, #346, #348, #350 — se
sont révélées **invisibles de toutes les sessions**. Aucune n'avait échoué :
la CI était verte, le déploiement réussi, et ``claude plugin update``
répondait « already at the latest version (0.2.0) » sans rien faire.

La cause tient en une phrase : **ce que Claude Code compare pour décider
qu'un plugin a changé, c'est la chaîne ``version`` de son manifeste, jamais
le contenu des fichiers.** Le manifeste n'avait pas bougé depuis #311, donc
rien n'a bougé pendant six jours — et le `gitCommitSha` épinglé dans
``~/.claude/plugins/installed_plugins.json`` est resté celui de #311.

Ce mode de défaillance est **muet des deux côtés** : rien ne se plaint au
merge, et la commande de mise à jour annonce un succès. Il n'existe aucun
moment où quelqu'un aurait pu s'en apercevoir sans aller lire le cache à la
main. C'est exactement le genre de panne qu'un garde-fou doit attraper, parce
qu'aucune vigilance humaine ne le fera.

L'auto-update natif ne remplace pas ce garde-fou : il compare la même chaîne.
Sans bump, il rejouerait la panne à chaque session, automatiquement.

La règle
--------
**Toute PR qui touche un fichier sous ``plugins/<nom>/`` doit rendre la
``version`` de ``plugins/<nom>/.claude-plugin/plugin.json`` différente de
celle de la branche de base.**

Pas « doit toucher le manifeste » : toucher le manifeste sans changer la
version — corriger une description, par exemple — ne propage rien non plus.
C'est la valeur qui est le signal, donc c'est la valeur qu'on compare.

Trois cas ne demandent aucun bump, et ce sont les seuls :

- **Un plugin qui naît.** Aucune version de base à comparer : rien à faire
  bouger, la première installation prendra ce qu'elle trouve.
- **Un plugin qui disparaît.** Son manifeste part avec lui ; exiger un bump
  sur un fichier supprimé n'aurait pas de sens.
- **La racine.** ``.claude-plugin/marketplace.json`` à la racine du dépôt
  décrit le marketplace, pas un plugin : le rafraîchissement du marketplace
  le relit sans passer par une version de plugin.

Pas d'échappatoire
------------------
Aucun mot-clé ne désarme ce garde-fou, pour la même raison que la règle des
deux PR : une porte de sortie serait empruntée au premier obstacle, et il n'y
aurait plus de règle. Le geste correct quand il se déclenche tient en une
ligne — incrémenter la version dans le manifeste — et c'est précisément le
geste qui manquait.

Usage
-----
    python scripts/plugin_version_guard.py --changed-files fichier.tsv \\
        --base-ref <sha>

où chaque ligne est ``statut<TAB>chemin`` (le format de l'API GitHub :
``added``, ``modified``, ``removed``, ``renamed``…). Sans ``--changed-files``,
le script lit l'entrée standard.

Codes de sortie : ``0`` respectée, ``1`` refusée, ``2`` entrée illisible
(voir ``EMPTY_INPUT_MESSAGE``).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Callable

#: Ce dépôt n'est jamais copié ailleurs — contrairement à `hermes-custom`,
#: d'où ce garde-fou vient — donc remonter d'un cran depuis `scripts/`
#: désigne bien la racine du checkout.
REPO_ROOT = Path(__file__).resolve().parents[1]

PLUGINS_DIR = "plugins"
MANIFEST_SUFFIX = ".claude-plugin/plugin.json"

#: Même code que ``two_pr_guard`` : « je n'ai rien pu lire » se distingue du
#: refus (1). Les deux font échouer la CI, mais le lecteur du log doit
#: pouvoir dire lequel des deux s'est produit sans relire le message.
EMPTY_INPUT_EXIT = 2

EMPTY_INPUT_MESSAGE = (
    "Garde de version des plugins — impossible de lire la liste des fichiers "
    "de la PR : aucune ligne « statut<TAB>chemin » en entrée. Une PR ne "
    "touche jamais 0 fichier, donc rien n'a été vérifié (typiquement `gh api` "
    "en échec : 403, réseau, quota). Refus, plutôt qu'un vert sur zéro "
    "vérification."
)


class BaseIndisponible(RuntimeError):
    """L'état de la branche de base n'a pas pu être lu.

    Sans avant/après, le garde-fou n'a aucun bump à constater. Il refuse
    alors — un vert obtenu sans comparaison serait exactement la panne qu'il
    est censé empêcher. Le refus reste étroit : il ne se produit que sur une
    PR qui touche effectivement à ``plugins/``.
    """


def plugin_touched_by(path: str) -> str | None:
    """Le plugin auquel ce chemin appartient, ou ``None``.

    ``plugins/plans-notion/skills/x.md`` → ``plans-notion``. Un chemin hors
    de ``plugins/``, ou ``plugins/`` tout court, ne concerne aucun plugin.
    """
    parts = PurePosixPath(path.replace("\\", "/")).parts
    if len(parts) < 3 or parts[0] != PLUGINS_DIR:
        return None
    return parts[1]


def manifest_of(plugin: str) -> str:
    """Le chemin du manifeste d'un plugin, relatif à la racine du dépôt."""
    return f"{PLUGINS_DIR}/{plugin}/{MANIFEST_SUFFIX}"


def version_in(blob: str | None) -> str | None:
    """La ``version`` déclarée par un manifeste, ou ``None``.

    Rend ``None`` aussi bien pour un manifeste absent que pour un manifeste
    illisible ou sans champ ``version`` : dans les trois cas, il n'y a pas de
    signal de propagation à comparer.
    """
    if blob is None:
        return None
    try:
        manifest = json.loads(blob)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(manifest, dict):
        return None
    version = manifest.get("version")
    return version if isinstance(version, str) else None


def violations(
    changed: list[tuple[str, str]],
    read_head: Callable[[str], str | None],
    read_base: Callable[[str], str | None],
) -> list[str]:
    """Les plugins touchés dont la version n'a pas bougé. Vide si tout va bien.

    ``read_head`` lit un fichier tel que la PR le laisse, ``read_base`` tel
    que la branche de base l'avait. Les deux rendent ``None`` quand le
    fichier n'existe pas de ce côté — c'est ainsi qu'on reconnaît un plugin
    qui naît (pas de base) ou qui disparaît (pas de tête).
    """
    touched = sorted({
        plugin
        for _status, path in changed
        if (plugin := plugin_touched_by(path)) is not None
    })

    refused = []
    for plugin in touched:
        manifest = manifest_of(plugin)
        head = read_head(manifest)
        if head is None:
            # Le plugin disparaît avec son manifeste : rien à faire bouger.
            continue

        base = read_base(manifest)
        if base is None:
            # Le plugin naît : aucune version de base à dépasser.
            continue

        avant, apres = version_in(base), version_in(head)
        if apres is None:
            refused.append(
                f"{manifest} ne déclare pas de `version` lisible. C'est cette "
                "chaîne, et elle seule, qui dit aux sessions qu'il y a "
                "quelque chose à récupérer : sans elle, rien ne se propage."
            )
            continue

        if avant == apres:
            refused.append(
                f"{plugin} change mais reste en {apres}. Claude Code compare "
                f"la `version` de {manifest}, jamais le contenu des fichiers : "
                "tant qu'elle ne bouge pas, `plugin update` répond « already "
                "at the latest version » et aucune session ne voit ce travail. "
                f"Incrémenter la version dans {manifest}."
            )

    return refused


def _read_changed(handle) -> list[tuple[str, str]]:
    changed = []
    for line in handle:
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 2 and parts[1]:
            changed.append((parts[0].strip(), parts[1].strip()))
    return changed


def _head_reader(repo_root: Path) -> Callable[[str], str | None]:
    """Lit le fichier dans le checkout — c'est déjà l'état de la PR."""

    def read(path: str) -> str | None:
        fichier = repo_root / path
        if not fichier.is_file():
            return None
        return fichier.read_text(encoding="utf-8")

    return read


def _base_reader(repo_root: Path, base_ref: str | None) -> Callable[[str], str | None]:
    """Lit le fichier tel que la branche de base l'avait, via ``git show``.

    ``actions/checkout`` clone à profondeur 1 : le commit de base n'est pas
    dans le clone, et le step CI va le chercher seul, à profondeur 1. Quand
    il manque quand même, on lève plutôt que de rendre ``None`` — sinon tout
    plugin passerait pour naissant, et le garde-fou serait vert sur rien.
    """

    def read(path: str) -> str | None:
        if not base_ref:
            raise BaseIndisponible(
                "aucune branche de base fournie (--base-ref)"
            )
        rendu = subprocess.run(
            ["git", "show", f"{base_ref}:{path}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if rendu.returncode == 0:
            return rendu.stdout
        # `git show` échoue aussi bien pour « le chemin n'existait pas » que
        # pour « le commit est absent du clone ». Seul le second cas est une
        # panne : on le distingue en demandant si le commit est là.
        connu = subprocess.run(
            ["git", "cat-file", "-e", f"{base_ref}^{{commit}}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if connu.returncode != 0:
            raise BaseIndisponible(
                f"le commit de base {base_ref} est absent du clone"
            )
        return None

    return read


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--changed-files",
        help="fichier TSV « statut<TAB>chemin » ; défaut : entrée standard",
    )
    parser.add_argument(
        "--base-ref",
        help="commit de la branche de base, pour lire la version d'avant",
    )
    args = parser.parse_args(argv)

    if args.changed_files:
        with open(args.changed_files, encoding="utf-8") as handle:
            changed = _read_changed(handle)
    else:
        changed = _read_changed(sys.stdin)

    if not changed:
        print(EMPTY_INPUT_MESSAGE, file=sys.stderr)
        return EMPTY_INPUT_EXIT

    try:
        refused = violations(
            changed,
            _head_reader(REPO_ROOT),
            _base_reader(REPO_ROOT, args.base_ref),
        )
    except BaseIndisponible as panne:
        print(
            "Garde de version des plugins — cette PR touche à `plugins/` mais "
            f"l'état d'avant n'a pas pu être lu ({panne}). Sans avant/après, "
            "aucun bump ne peut être constaté : refus, plutôt qu'un vert sur "
            "zéro comparaison.",
            file=sys.stderr,
        )
        return 1

    if refused:
        print(
            "Garde de version des plugins — cette PR ne peut pas être "
            "fusionnée :\n  " + "\n  ".join(refused),
            file=sys.stderr,
        )
        return 1

    print(
        f"Garde de version des plugins : respectée "
        f"({len(changed)} fichier(s) examiné(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
