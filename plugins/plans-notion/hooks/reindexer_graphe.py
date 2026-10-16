#!/usr/bin/env python3
"""Hook SessionStart : réindexe le graphe codebase-memory quand le dépôt a avancé.

Si le dépôt courant est suivi par codebase-memory-mcp (un fichier
``<cache>/<projet>.db`` existe) et que son HEAD git diffère du commit noté dans
``<cache>/<projet>.head``, le hook relance ``index_repository``. ``hooks.json``
le déclare asynchrone : la session n'attend pas l'indexation (13 à 22 s).

Le ``.head`` n'est réécrit qu'après une indexation réussie : un échec ou un délai
dépassé garde l'ancien SHA, donc la session suivante réessaie.

Contrat : sortie standard toujours vide (la sortie d'un hook SessionStart entre
dans le contexte de la session), code de sortie toujours 0. Les problèmes vont
sur stderr en une ligne, ou nulle part. Un verrou ``<projet>.lock`` évite deux
indexations simultanées quand deux sessions s'ouvrent ensemble. Un SIGTERM ou un
SIGHUP pendant l'indexation tue l'indexeur, retire le verrou, puis sort 0.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

NODE = "/opt/homebrew/opt/node@24/bin/node"
DELAI_GIT = 10
DELAI_INDEXATION = 180
AGE_VERROU_PERIME = 10 * 60
SIGNAUX_D_ARRET = (signal.SIGTERM, signal.SIGHUP)

# État lu par le gestionnaire de signal : groupe du processus en attente, verrou posé ici.
_GROUPE: int | None = None
_VERROU: Path | None = None


def executer(cmd: list[str], timeout: float) -> tuple[int, str]:
    """Lance une commande dans son propre groupe ; renvoie (code, stdout).

    Code -1 si introuvable ou délai dépassé. Au délai, tout le groupe est tué : bin.js
    lance l'indexeur natif en enfant, et un simple kill du pid de tête le laisserait vivre.
    """
    global _GROUPE
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, encoding="utf-8", errors="replace",
                                start_new_session=True)
    except OSError:
        return -1, ""
    _GROUPE = proc.pid
    try:
        sortie, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _tuer_le_groupe(proc)
        return -1, ""
    finally:
        _GROUPE = None
    return proc.returncode, sortie.strip()


def _sur_signal(signum: int, cadre) -> None:
    """SIGTERM ou SIGHUP pendant l'attente : tue le groupe, retire le verrou, sort 0."""
    if _GROUPE is not None:
        with contextlib.suppress(OSError):  # le groupe a pu disparaître entre-temps
            os.killpg(_GROUPE, signal.SIGKILL)
    if _VERROU is not None:
        with contextlib.suppress(OSError):
            _VERROU.unlink(missing_ok=True)
    sys.exit(0)


def _tuer_le_groupe(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)  # pgid = pid grâce à start_new_session
    except OSError:
        pass  # le groupe a déjà disparu
    proc.wait()
    if proc.stdout:
        proc.stdout.close()


def dossier_cache() -> Path:
    defini = os.environ.get("CBM_CACHE_DIR")
    return Path(defini) if defini else Path.home() / ".cache" / "codebase-memory-mcp"


def bin_js() -> Path:
    defini = os.environ.get("CBM_BIN_JS")
    return Path(defini) if defini else Path.home() / ".npm-global/lib/node_modules/codebase-memory-mcp/bin.js"


def nom_du_projet(racine: str) -> str:
    """Chemin absolu : « / » et espaces en « - », tirets consécutifs réduits, « - » initial retiré.

    Mesuré sur le serveur : « /a/-b/c » donne « a-b-c », pas « a--b-c » ;
    l'espace se remplace comme le « / ».
    """
    return re.sub(r"-+", "-", re.sub(r"[/ ]", "-", racine)).removeprefix("-")


def lire_head(chemin: Path) -> str | None:
    try:
        return chemin.read_text(encoding="utf-8").strip()
    except (OSError, ValueError):
        return None


def prendre_verrou(chemin: Path) -> bool:
    """Crée le verrou en exclusivité. Un verrou périmé est retiré d'abord. False si tenu."""
    if chemin.exists():
        if time.time() - chemin.stat().st_mtime < AGE_VERROU_PERIME:
            return False
        # Ce retrait n'est pas atomique : deux sessions qui tombent ensemble sur un
        # verrou périmé peuvent indexer deux fois. Coût au pire : une indexation en trop.
        chemin.unlink(missing_ok=True)
    try:
        os.close(os.open(chemin, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False
    return True


def indexer(racine: str, script: Path) -> bool:
    cmd = [NODE, str(script), "cli", "index_repository", "--repo-path", racine, "--mode", "full"]
    code, _ = executer(cmd, DELAI_INDEXATION)
    return code == 0


def main() -> int:
    anciens = {signal_: signal.signal(signal_, _sur_signal) for signal_ in SIGNAUX_D_ARRET}
    try:
        return _reindexer_la_session()
    finally:
        for signal_, ancien in anciens.items():
            if ancien is not None:
                signal.signal(signal_, ancien)


def _reindexer_la_session() -> int:
    global _VERROU
    try:
        donnees = json.load(sys.stdin)
        cwd = donnees.get("cwd") if isinstance(donnees, dict) else None
        if not isinstance(cwd, str) or not cwd:
            return 0
        code, racine = executer(["git", "-C", cwd, "rev-parse", "--show-toplevel"], DELAI_GIT)
        if code != 0 or not racine:
            return 0
        cache, projet = dossier_cache(), nom_du_projet(racine)
        if not (cache / f"{projet}.db").is_file():
            return 0  # dépôt non suivi par codebase-memory : on ne crée rien
        code, head = executer(["git", "-C", racine, "rev-parse", "HEAD"], DELAI_GIT)
        if code != 0 or not head:
            return 0
        if lire_head(cache / f"{projet}.head") == head:
            return 0
        script = bin_js()
        if not (Path(NODE).is_file() and script.is_file()):
            return 0  # autre machine (VPS, sans node ou sans le paquet) : silence
        verrou = cache / f"{projet}.lock"
        if not prendre_verrou(verrou):
            return 0  # une autre session indexe déjà
        _VERROU = verrou
        try:
            reussi = indexer(racine, script)
        finally:
            verrou.unlink(missing_ok=True)
            _VERROU = None
        if reussi:
            (cache / f"{projet}.head").write_text(head + "\n", encoding="utf-8")
        else:
            print(f"reindexer_graphe : indexation de {projet} en échec, la prochaine session réessaie",
                  file=sys.stderr)
    except Exception as erreur:  # un hook cassé ne bloque ni n'enrichit aucune session
        print(f"reindexer_graphe : ignoré ({type(erreur).__name__}: {erreur})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
