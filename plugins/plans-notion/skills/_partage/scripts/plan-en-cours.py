#!/usr/bin/env python3
"""Fiche locale du plan en cours : ce que la garde de fin de tour lit sans réseau.

Usage :
    plan-en-cours.py ouvrir --page <id> --titre <t> --depot <owner/repo> \
        --branche <b> --worktree <chemin> [--sonnette <trigger_id>] [--session <id>]
    plan-en-cours.py pr --numero <n> [--session <id>]
    plan-en-cours.py attente --raison <texte> [--session <id>]
    plan-en-cours.py reprendre [--session <id>]
    plan-en-cours.py etape --faite <n> --restantes <k> [--session <id>]
    plan-en-cours.py clore [--session <id>]
    plan-en-cours.py lire [--session <id>]

Le script ne parle jamais à Notion. Il tient une copie locale, un fichier JSON
par session, dans ``${XDG_STATE_HOME:-~/.local/state}/plans-notion/plans-en-cours/
<cle>.json`` (dossier en mode 700). Les valeurs des propriétés Session, Sonnette
et Machine de la base « Plans Claude » sont dans cette fiche (``session_id``,
``sonnette``, ``origine`` : Machine) ; c'est la session qui les écrit dans Notion.

Identifiant de session. Ordre de recherche :

1. ``--session <id>`` ;
2. la clé ``bridgeSessionId`` du fichier ``~/.claude/sessions/<pid>.json``, le
   pid venant de la variable ``CLAUDE_PID`` ;
3. sinon aucun identifiant claude.ai : ``session_id`` reste vide, la sonnette
   aussi (« pas de sonnette possible »).

Le script n'invente jamais d'identifiant. La clé du fichier de fiche est
``session_id`` quand il existe ; sinon l'identifiant local de la session
Claude Code (``CLAUDE_CODE_SESSION_ID``), qui est réel et stable. Sans aucune
des deux, il sort en 2.

Le ``sessionId`` local du fichier de session n'est jamais l'identifiant
claude.ai : il ne sert ni de ``session_id`` ni de sonnette.

Cycle de la fiche : ``en cours`` (à l'ouverture), ``attente`` (``attente``, puis
``reprendre`` compte une relance), ``a merger`` (à ``pr``), ``clos`` (à ``clore``).
``etape`` ne change pas l'état. Une fiche ``clos`` ne reçoit plus d'écriture
hormis ``clore``.

Écriture : chaque modification se fait sous ``flock`` sur le dossier (pas de mise
à jour perdue), dans un fichier temporaire du même dossier, puis ``os.replace``
(un lecteur voit l'ancienne fiche ou la nouvelle, jamais un JSON tronqué).

Codes de sortie : 0 fait ou lu ; 1 refus métier (fiche absente, fiche déjà
ouverte, transition interdite) ; 2 usage ou identifiant absent ou de forme
invalide.

Python 3, bibliothèque standard seulement.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SORTIE_OK = 0
SORTIE_REFUS = 1
SORTIE_USAGE = 2

FORME_IDENTIFIANT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")

ETAT_EN_COURS = "en cours"
ETAT_ATTENTE = "attente"
ETAT_A_MERGER = "a merger"
ETAT_CLOS = "clos"


class Refus(Exception):
    """Arrêt propre : un message pour stderr, un code de sortie."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Identite:
    session_id: str | None      # identifiant claude.ai, ou None
    cle: str                    # nom du fichier de fiche, sans « .json »
    origine: str


# --- identifiant de session --------------------------------------------------

def _forme_valide(valeur) -> bool:
    return isinstance(valeur, str) and bool(FORME_IDENTIFIANT.match(valeur))


def _fichier_session(pid: str, home: Path) -> dict | None:
    if not pid.isdigit():
        return None
    try:
        donnees = json.loads((home / ".claude" / "sessions" / f"{pid}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return donnees if isinstance(donnees, dict) else None


def _origine(fichier: dict | None, env) -> str:
    entree = (fichier or {}).get("entrypoint") or env.get("CLAUDE_CODE_ENTRYPOINT") or ""
    if entree == "claude-desktop":
        return "app de bureau"
    if (fichier or {}).get("bridgeSessionId") or env.get("CLAUDE_CODE_ENVIRONMENT_KIND") == "bridge":
        return "serveur Remote Control"
    return "terminal du VPS"


def identite(session_arg: str | None, env, home: Path) -> Identite:
    fichier = _fichier_session(env.get("CLAUDE_PID", ""), home)
    if session_arg is not None:
        if not _forme_valide(session_arg):
            raise Refus(SORTIE_USAGE, "--session : forme d'identifiant refusée")
        session_id = session_arg
    else:
        bridge = (fichier or {}).get("bridgeSessionId")
        session_id = bridge if _forme_valide(bridge) else None

    cle = session_id
    if cle is None:
        local = env.get("CLAUDE_CODE_SESSION_ID", "")
        if local:
            if not _forme_valide(local):
                raise Refus(SORTIE_USAGE, "CLAUDE_CODE_SESSION_ID : forme refusée, fiche non ouverte")
            cle = local
    if cle is None:
        raise Refus(SORTIE_USAGE, "pas d'identifiant de session : ni --session, ni bridgeSessionId "
                                  "(CLAUDE_PID et ~/.claude/sessions/<pid>.json), ni CLAUDE_CODE_SESSION_ID")
    return Identite(session_id=session_id, cle=cle, origine=_origine(fichier, env))


# --- stockage ----------------------------------------------------------------

def dossier_fiches(env) -> Path:
    base = env.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return Path(base) / "plans-notion" / "plans-en-cours"


def _preparer(dossier: Path) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    os.chmod(dossier, 0o700)


@contextlib.contextmanager
def _verrou(dossier: Path):
    fd = os.open(dossier, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _lire_fiche(chemin: Path) -> dict | None:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except ValueError as e:
        raise Refus(SORTIE_REFUS, f"fiche illisible ({chemin.name}) : {e}")


def _ecrire_fiche(dossier: Path, chemin: Path, fiche: dict) -> None:
    donnees = json.dumps(fiche, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=dossier, prefix=f".{chemin.stem}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(donnees)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, chemin)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def _maintenant() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _modifier(dossier: Path, cle: str, transformer, *, creer: bool = False) -> dict:
    """Lit la fiche sous verrou, la transforme, l'écrit. Rien n'est créé sur un refus."""
    if not creer and not dossier.is_dir():
        raise Refus(SORTIE_REFUS, "pas de fiche pour cette session")
    if creer:
        _preparer(dossier)
    chemin = dossier / f"{cle}.json"
    with _verrou(dossier):
        fiche = _lire_fiche(chemin)
        if creer:
            if fiche is not None:
                raise Refus(SORTIE_REFUS, "une fiche existe déjà pour cette session : la clore, ou la lire")
        elif fiche is None:
            raise Refus(SORTIE_REFUS, "pas de fiche pour cette session")
        fiche = transformer(fiche)
        fiche["maj"] = _maintenant()
        _ecrire_fiche(dossier, chemin, fiche)
    return fiche


def _refuser_si_clos(fiche: dict) -> None:
    if fiche["etat"] == ETAT_CLOS:
        raise Refus(SORTIE_REFUS, "la fiche est close : plus d'écriture hormis la lecture")


# --- commandes ---------------------------------------------------------------

def cmd_ouvrir(args, ident: Identite, dossier: Path) -> str:
    sonnette_demandee = args.sonnette

    def neuve(_absent):
        return {
            "page_id": args.page,
            "titre": args.titre,
            "depot": args.depot,
            "branche": args.branche,
            "worktree": args.worktree,
            "pr": None,
            "session_id": ident.session_id,
            "etat": ETAT_EN_COURS,
            "raison_attente": None,
            "etapes_faites": None,
            "etapes_restantes": None,
            "relances": 0,
            "sonnette": sonnette_demandee if ident.session_id else None,
            "maj": None,
            "origine": ident.origine,
        }

    _modifier(dossier, ident.cle, neuve, creer=True)
    lignes = [f"fiche ouverte : {ident.cle}.json (origine : {ident.origine})"]
    if ident.session_id is None:
        lignes.append("pas de sonnette possible : session hors Remote Control, pas de bridgeSessionId")
    elif sonnette_demandee is None:
        lignes.append("sonnette : aucune (--sonnette non donné)")
    return "\n".join(lignes)


def cmd_pr(args, ident: Identite, dossier: Path) -> str:
    def f(fiche):
        _refuser_si_clos(fiche)
        fiche["pr"] = args.numero
        fiche["etat"] = ETAT_A_MERGER
        return fiche
    _modifier(dossier, ident.cle, f)
    return f"PR {args.numero} notée : etat=a merger"


def cmd_attente(args, ident: Identite, dossier: Path) -> str:
    def f(fiche):
        _refuser_si_clos(fiche)
        fiche["etat"] = ETAT_ATTENTE
        fiche["raison_attente"] = args.raison
        return fiche
    _modifier(dossier, ident.cle, f)
    return "fiche en attente"


def cmd_reprendre(args, ident: Identite, dossier: Path) -> str:
    def f(fiche):
        if fiche["etat"] != ETAT_ATTENTE:
            raise Refus(SORTIE_REFUS, f"la fiche n'est pas en attente (etat : {fiche['etat']})")
        fiche["etat"] = ETAT_EN_COURS
        fiche["raison_attente"] = None
        fiche["relances"] = int(fiche.get("relances") or 0) + 1
        return fiche
    fiche = _modifier(dossier, ident.cle, f)
    return f"fiche reprise : relances={fiche['relances']}"


def cmd_etape(args, ident: Identite, dossier: Path) -> str:
    def f(fiche):
        _refuser_si_clos(fiche)
        fiche["etapes_faites"] = args.faite
        fiche["etapes_restantes"] = args.restantes
        return fiche
    _modifier(dossier, ident.cle, f)
    return f"étapes : {args.faite} faites, {args.restantes} restantes"


def cmd_clore(args, ident: Identite, dossier: Path) -> str:
    def f(fiche):
        fiche["etat"] = ETAT_CLOS
        fiche["raison_attente"] = None
        return fiche
    _modifier(dossier, ident.cle, f)
    return "fiche close"


def cmd_lire(args, ident: Identite, dossier: Path) -> str:
    if not dossier.is_dir():
        raise Refus(SORTIE_REFUS, "pas de fiche pour cette session")
    fiche = _lire_fiche(dossier / f"{ident.cle}.json")
    if fiche is None:
        raise Refus(SORTIE_REFUS, "pas de fiche pour cette session")
    return json.dumps(fiche, ensure_ascii=False, indent=2, sort_keys=True)


COMMANDES = {
    "ouvrir": cmd_ouvrir,
    "pr": cmd_pr,
    "attente": cmd_attente,
    "reprendre": cmd_reprendre,
    "etape": cmd_etape,
    "clore": cmd_clore,
    "lire": cmd_lire,
}


# --- ligne de commande -------------------------------------------------------

def _entier_positif(texte: str) -> int:
    try:
        valeur = int(texte)
    except ValueError:
        raise argparse.ArgumentTypeError(f"entier attendu : {texte!r}")
    if valeur < 1:
        raise argparse.ArgumentTypeError(f"entier positif attendu : {texte!r}")
    return valeur


def _entier_positif_ou_nul(texte: str) -> int:
    try:
        valeur = int(texte)
    except ValueError:
        raise argparse.ArgumentTypeError(f"entier attendu : {texte!r}")
    if valeur < 0:
        raise argparse.ArgumentTypeError(f"entier positif ou nul attendu : {texte!r}")
    return valeur


def _parser() -> argparse.ArgumentParser:
    commun = argparse.ArgumentParser(add_help=False)
    commun.add_argument("--session", help="identifiant de session (sinon bridgeSessionId, sinon CLAUDE_CODE_SESSION_ID)")

    p = argparse.ArgumentParser(description="Fiche locale du plan en cours.")
    sous = p.add_subparsers(dest="commande", required=True)

    o = sous.add_parser("ouvrir", parents=[commun], help="ouvrir la fiche de la session")
    o.add_argument("--page", required=True)
    o.add_argument("--titre", required=True)
    o.add_argument("--depot", required=True)
    o.add_argument("--branche", required=True)
    o.add_argument("--worktree", required=True)
    o.add_argument("--sonnette", default=None, help="trigger_id de la sonnette (retenu seulement si la session est connue de claude.ai)")

    pr = sous.add_parser("pr", parents=[commun], help="noter la PR ouverte")
    pr.add_argument("--numero", type=_entier_positif, required=True)

    at = sous.add_parser("attente", parents=[commun], help="passer en attente")
    at.add_argument("--raison", required=True)

    sous.add_parser("reprendre", parents=[commun], help="repasser en cours après une attente")

    et = sous.add_parser("etape", parents=[commun], help="noter les étapes faites et restantes")
    et.add_argument("--faite", type=_entier_positif_ou_nul, required=True)
    et.add_argument("--restantes", type=_entier_positif_ou_nul, required=True)

    sous.add_parser("clore", parents=[commun], help="clore la fiche")
    sous.add_parser("lire", parents=[commun], help="rendre la fiche en JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    env = os.environ
    home = Path(os.path.expanduser("~"))
    dossier = dossier_fiches(env)
    try:
        ident = identite(args.session, env, home)
        sortie = COMMANDES[args.commande](args, ident, dossier)
    except Refus as e:
        print(f"plan-en-cours : {e.message}", file=sys.stderr)
        return e.code
    print(sortie)
    return SORTIE_OK


if __name__ == "__main__":
    sys.exit(main())
