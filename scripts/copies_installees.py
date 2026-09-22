#!/usr/bin/env python3
"""Le diagnostic en une commande pour le piège des trois copies.

Trois copies du même plugin peuvent coexister sur ce poste, et ce n'est pas
forcément la bonne qui gouverne une session (voir CLAUDE.md, section « Le
piège propre à ce dépôt : trois copies du même skill ») :

1. **La copie installée** depuis la marketplace ``atelier``, déclarée dans
   ``~/.claude/plugins/installed_plugins.json``.
2. **Les instantanés ``@inline``**, des copies figées posées sous
   ``~/.claude/remote/plugins/<hash>/`` (parfois deux niveaux de hash) par le
   lanceur ``~/.claude/remote/ccd-cli/`` via des arguments ``--plugin-dir``.
   Un instantané qui porte le même nom qu'une copie installée la masque.
3. **Les ``--plugin-dir`` réellement passés** aux processus ``claude``
   vivants, quand ``/proc`` est lisible — la preuve la plus directe de ce
   qui a été chargé au démarrage d'une session donnée.

Aucun outil existant ne réunit ces trois vues d'un coup. Ce script les
réunit, en lecture seule : il ne modifie rien sur le disque.

Codes de sortie : ``1`` dès qu'au moins un instantané porte le nom d'un
plugin ``atelier`` installé avec une version différente de la sienne (c'est
le cas qui masque silencieusement une mise à jour) ; ``0`` sinon — y compris
quand rien n'a été trouvé du tout (``HOME`` vierge, sans
``~/.claude/remote/plugins/``).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

#: Résolu à l'exécution, jamais codé en dur : c'est ce qui rend le script
#: réfutable sur un `HOME` temporaire (voir la preuve de fin dans le plan).
HOME = Path(os.path.expanduser("~"))

INSTALLED_PLUGINS = HOME / ".claude" / "plugins" / "installed_plugins.json"
REMOTE_PLUGINS_DIR = HOME / ".claude" / "remote" / "plugins"
MANIFEST_GLOB = ".claude-plugin/plugin.json"

#: Suffixe des clés de `installed_plugins.json` pour la marketplace qui nous
#: intéresse ici. Les copies `synced` (sous `~/.claude/plugins/synced/`,
#: pilotées par un `manifest.json` différent) sont hors sujet et ne sont
#: jamais lues par ce script : il ne regarde que `installed_plugins.json`
#: et `~/.claude/remote/plugins/`.
MARKETPLACE_SUFFIX = "@atelier"


def _lire_json(chemin: Path) -> dict | None:
    """Lit un JSON et rend un dict, ou ``None`` — jamais une exception.

    Absent, illisible, mal formé ou racine qui n'est pas un objet : les
    quatre cas rendent ``None``, à charge de l'appelant de le signaler.
    """
    try:
        texte = chemin.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        contenu = json.loads(texte)
    except json.JSONDecodeError:
        return None
    return contenu if isinstance(contenu, dict) else None


def plugins_installes() -> dict[str, dict[str, str | None]]:
    """Les plugins de la marketplace ``atelier`` déclarés comme installés.

    Rend ``{nom: {"version": ..., "chemin": ...}}``. Vide — jamais une
    exception — si le fichier est absent, illisible, mal formé, ou ne
    déclare aucun plugin ``@atelier``.
    """
    manifeste = _lire_json(INSTALLED_PLUGINS)
    if manifeste is None:
        return {}
    plugins = manifeste.get("plugins")
    if not isinstance(plugins, dict):
        return {}

    resultat: dict[str, dict[str, str | None]] = {}
    for cle, entrees in plugins.items():
        if not isinstance(cle, str) or not cle.endswith(MARKETPLACE_SUFFIX):
            continue
        nom = cle[: -len(MARKETPLACE_SUFFIX)]
        if not isinstance(entrees, list) or not entrees or not isinstance(entrees[0], dict):
            continue
        premiere = entrees[0]
        resultat[nom] = {
            "version": premiere.get("version"),
            "chemin": premiere.get("installPath"),
        }
    return resultat


def instantanes_inline() -> list[dict[str, str | None]]:
    """Tous les instantanés ``@inline`` trouvés sous ``~/.claude/remote/plugins/``.

    Cherche ``.claude-plugin/plugin.json`` à n'importe quelle profondeur
    sous ``REMOTE_PLUGINS_DIR`` — mesuré sur ce poste : un niveau
    (``<hash>/.claude-plugin/...``) et deux niveaux
    (``<hash>/<hash>/.claude-plugin/...``) coexistent. Un manifeste illisible
    n'interrompt rien : il est rapporté avec son chemin, ``nom`` et
    ``version`` à ``None``.
    """
    if not REMOTE_PLUGINS_DIR.is_dir():
        return []

    try:
        manifestes = sorted(REMOTE_PLUGINS_DIR.glob(f"**/{MANIFEST_GLOB}"))
    except OSError:
        return []

    resultats: list[dict[str, str | None]] = []
    for manifeste_path in manifestes:
        dossier = manifeste_path.parent.parent
        manifeste = _lire_json(manifeste_path)
        if manifeste is None:
            resultats.append(
                {
                    "nom": None,
                    "version": None,
                    "chemin": str(dossier),
                    "erreur": "manifeste absent, illisible ou mal formé",
                }
            )
            continue
        nom = manifeste.get("name")
        version = manifeste.get("version")
        resultats.append(
            {
                "nom": nom if isinstance(nom, str) else None,
                "version": version if isinstance(version, str) else None,
                "chemin": str(dossier),
                "erreur": None,
            }
        )
    return resultats


def plugin_dirs_processus_vivants() -> tuple[list[str], str | None]:
    """Les valeurs ``--plugin-dir`` réellement passées aux processus vivants.

    Ne filtre pas par nom de binaire : le lanceur observé sur ce poste est
    ``~/.claude/remote/ccd-cli/<version>`` — son ``argv[0]`` ne s'appelle pas
    « claude » et un filtre par nom le raterait. Le signal fiable est la
    présence même de ``--plugin-dir`` dans la ligne de commande.

    Rend ``(chemins, message)``. ``message`` est ``None`` quand au moins un
    chemin a été collecté ; sinon il explique en une ligne pourquoi la liste
    est vide (``/proc`` illisible, aucun processus trouvé, ou aucun processus
    trouvé ne porte ``--plugin-dir``). Ne lève jamais : un processus qui
    disparaît pendant la lecture (course normale avec l'ordonnanceur) est
    simplement ignoré.
    """
    proc = Path("/proc")
    try:
        pids = [p for p in proc.iterdir() if p.name.isdigit()]
    except OSError as exc:
        return [], f"/proc n'est pas lisible : {exc}."

    if not pids:
        return [], "aucun processus trouvé sous /proc."

    chemins: list[str] = []
    for pid_dir in pids:
        try:
            brut = (pid_dir / "cmdline").read_bytes()
        except OSError:
            continue
        if not brut:
            continue
        arguments = [a for a in brut.decode("utf-8", errors="replace").split("\x00") if a]

        indice = 0
        while indice < len(arguments):
            argument = arguments[indice]
            if argument == "--plugin-dir" and indice + 1 < len(arguments):
                chemins.append(arguments[indice + 1])
                indice += 2
                continue
            if argument.startswith("--plugin-dir="):
                chemins.append(argument.split("=", 1)[1])
            indice += 1

    if not chemins:
        return [], "aucun processus vivant ne porte --plugin-dir."
    return chemins, None


def main() -> int:
    installes = plugins_installes()
    instantanes = instantanes_inline()
    chemins_proc, message_proc = plugin_dirs_processus_vivants()

    conflit = False

    print("1. Plugins installés depuis la marketplace atelier")
    if not installes:
        print(
            "  aucun trouvé "
            f"({INSTALLED_PLUGINS} absent, illisible, ou sans plugin @atelier)."
        )
    else:
        for nom, info in sorted(installes.items()):
            print(f"  {nom} {info['version']} — {info['chemin']}")

    print()
    print(f"2. Instantanés @inline sous {REMOTE_PLUGINS_DIR}")
    if not instantanes:
        print("  aucun trouvé.")
    else:
        for instantane in instantanes:
            if instantane["erreur"]:
                print(f"  ? {instantane['chemin']} — {instantane['erreur']}")
                continue

            nom, version, chemin = instantane["nom"], instantane["version"], instantane["chemin"]
            correspondance = installes.get(nom) if nom is not None else None

            if correspondance is not None and version is not None and version != correspondance["version"]:
                conflit = True
                print(
                    f"  ⚠ {nom} {version} — {chemin} "
                    f"(la copie installée est en {correspondance['version']} : "
                    "cet instantané la masque au démarrage)"
                )
            else:
                print(f"  {nom} {version} — {chemin}")

    print()
    print("3. --plugin-dir des processus claude vivants (/proc)")
    if message_proc is not None:
        print(f"  {message_proc}")
    else:
        for chemin in chemins_proc:
            print(f"  {chemin}")

    print()
    if conflit:
        print(
            "Résultat : au moins un instantané @inline masque une copie "
            "atelier installée à une version différente."
        )
        return 1

    print("Résultat : aucun instantané en conflit avec une copie atelier installée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
