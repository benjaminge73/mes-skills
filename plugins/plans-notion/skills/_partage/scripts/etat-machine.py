#!/usr/bin/env python3
"""État de la machine : peut-elle recevoir une action lourde maintenant ?

Usage :
    etat-machine.py releve [--json] [--hors-pid PID ...] [--proc RACINE]

``releve`` lit ``/proc`` (charge moyenne, mémoire, pression CPU et mémoire,
processus) et rend un verdict parmi trois :

* ``libre``    : rien ne s'oppose à une action lourde ;
* ``chargée``  : la machine travaille déjà (pression CPU forte, ou une famille
  lourde active en dehors du détenteur du jeton) — on peut y aller, mais en
  sachant que la mesure sera faussée et en prévenant les autres ;
* ``saturée``  : la mémoire est au bord — on n'y lance rien.

Sortie par défaut : le verdict seul sur la première ligne (``head -1`` suffit
à un script shell), puis une cause par ligne. ``--json`` rend le même relevé
structuré : ``verdict``, ``causes`` (``code``, ``decisive``, ``detail``),
``familles``, ``mesures``.

La charge moyenne figure toujours dans les causes mais ne décide jamais : le
POC du 2026-10-01 a montré qu'une seule e2e la pousse à 15 sur 6 cœurs et
qu'elle met une à deux minutes à retomber, si bien que la juger rendrait la
machine « chargée » dès qu'une action tourne, et encore juste après qu'elle
a fini.

``--hors-pid PID`` (répétable) exclut ce processus et tous ses descendants du
décompte des familles lourdes : ce que le détenteur du jeton fait tourner ne
rend pas la machine « chargée » pour lui-même.

``--proc`` change la racine de ``/proc`` : c'est ce qui permet aux tests de lire
des fixtures au lieu de la vraie machine.

Python 3, bibliothèque standard seulement. Lit du Linux générique : en session
cloud, sans VPS, le script répond simplement sur la machine où il tourne. Une
mesure illisible (pas de ``/proc/pressure``, par exemple) est ignorée, jamais
une erreur : on répond sur ce qu'on lit.

Codes de sortie : 0 relevé rendu, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# --- Seuils : chacun avec sa provenance --------------------------------------

# Pression mémoire « full » moyennée sur 60 s, à partir de laquelle la machine
# est « saturée ». Provenance : chien de garde du VPS,
# hermes-custom/scripts/claude_remote_saturation_watchdog.py:159
# (MEM_FULL_AVG60 = 40.0), calibré sur l'incident du 2026-09-25 (pression
# « full » à ~75 %, charge 30 sur 6 cœurs).
SEUIL_MEM_FULL_AVG60 = 40.0

# Mémoire disponible sous laquelle la machine est « saturée », en ko (1,5 Go).
# Provenance : Q9 du plan « Évals sobres et machine partagée », 2026-10-01
# (VPS de 11 Go ; le POC n'est jamais descendu sous 3,7 Go disponibles).
SEUIL_MEM_DISPONIBLE_KO = int(1.5 * 1024 * 1024)

# Pression CPU « some » moyennée sur 10 s, à partir de laquelle la machine est
# « chargée ». Provenance : POC de Q9, 2026-10-01 — contrairement à la charge
# moyenne, elle retombe en quelques secondes ; une e2e seule la pousse jusqu'à
# 70 %, une suite seule jusqu'à 51 %, au repos elle reste à quelques pour cent.
SEUIL_CPU_SOME_AVG10 = 50.0

# --- Familles lourdes ---------------------------------------------------------

SUITE_DE_TESTS = "suite-de-tests"
NAVIGATEUR_SANS_TETE = "navigateur-sans-tete"
CLAUDE_PLUGIN_EVAL = "claude-plugin-eval"
CONTENEUR_DE_RUNNER = "conteneur-de-runner"
SESSION_CLAUDE_REJEU = "session-claude-rejeu"

VERDICT_LIBRE = "libre"
VERDICT_CHARGEE = "chargée"
VERDICT_SATUREE = "saturée"

# Programmes qui lancent un autre programme : seuls leurs arguments proches
# nomment ce qui tourne vraiment (``python -m pytest``, ``npx vitest``). Tout
# autre programme (``grep``, ``vim``…) qui cite « pytest » n'est pas une suite.
_LANCEURS = ("python", "node", "nodejs", "npx", "uv", "uvx", "pnpm", "yarn", "npm", "bun")
_PROGRAMMES_DE_TESTS = {"pytest", "py.test", "vitest", "jest", "playwright"}
_NAVIGATEURS = {"chrome", "chromium", "chromium-browser", "google-chrome", "headless_shell",
                "chrome-headless-shell"}


def _nom(argument: str) -> str:
    """Nom d'un exécutable ou d'un script : basename, sans extension de script."""
    base = os.path.basename(argument)
    for suffixe in (".py", ".mjs", ".cjs", ".js"):
        if base.endswith(suffixe):
            return base[: -len(suffixe)]
    return base


def _est_lanceur(nom: str) -> bool:
    return any(nom == p or (p == "python" and nom.startswith("python")) for p in _LANCEURS)


def familles_de(argv: list[str]) -> list[str]:
    """Familles lourdes auxquelles appartient un processus, d'après sa ligne de commande."""
    if not argv:
        return []
    prog = _nom(argv[0])
    trouvees: list[str] = []

    # Suite de tests : le programme lui-même, ou un lanceur dont l'un des deux
    # arguments suivants (``-m pytest``, ``run vitest``, ``vitest.mjs``) la nomme.
    if prog in _PROGRAMMES_DE_TESTS or (
            _est_lanceur(prog) and any(_nom(a) in _PROGRAMMES_DE_TESTS for a in argv[1:4])):
        trouvees.append(SUITE_DE_TESTS)

    # Navigateur sans tête : un binaire de navigateur lancé avec --headless, ou
    # le binaire « headless shell » de Playwright, sans tête par construction.
    if prog in ("headless_shell", "chrome-headless-shell") or (
            prog in _NAVIGATEURS and any(a.startswith("--headless") for a in argv[1:])):
        trouvees.append(NAVIGATEUR_SANS_TETE)

    # ``claude plugin eval`` : le banc d'évals joue de vraies sessions.
    if prog == "claude" and any(a == "plugin" and b == "eval" for a, b in zip(argv, argv[1:])):
        trouvees.append(CLAUDE_PLUGIN_EVAL)

    # Conteneur de runner : ``Runner.Worker`` est le processus d'un job en cours
    # (``Runner.Listener``, lui, attend et ne pèse rien). Un ``docker run`` nu
    # n'en est pas : sur ce poste, des serveurs MCP vivent des heures dans un
    # conteneur sans rien peser.
    if prog == "Runner.Worker":
        trouvees.append(CONTENEUR_DE_RUNNER)

    # Session Claude enfant d'un rejeu : ``claude`` non interactif (-p/--print).
    if prog == "claude" and any(a in ("-p", "--print") for a in argv[1:]):
        trouvees.append(SESSION_CLAUDE_REJEU)

    return trouvees


# --- Lecture de /proc ---------------------------------------------------------

def _lire(chemin: Path) -> str | None:
    try:
        return chemin.read_text()
    except (OSError, UnicodeDecodeError):
        return None


def lire_pression(proc: Path, ressource: str, ligne: str, champ: str) -> float | None:
    """``/proc/pressure/<ressource>`` : la valeur du ``champ`` (``avg10``…) de la ``ligne``."""
    texte = _lire(proc / "pressure" / ressource)
    if texte is None:
        return None
    for brut in texte.splitlines():
        morceaux = brut.split()
        if morceaux and morceaux[0] == ligne:
            for m in morceaux[1:]:
                nom, _, valeur = m.partition("=")
                if nom == champ:
                    try:
                        return float(valeur)
                    except ValueError:
                        return None
    return None


def lire_charge(proc: Path) -> float | None:
    texte = _lire(proc / "loadavg")
    try:
        return float(texte.split()[0]) if texte else None
    except (ValueError, IndexError):
        return None


def lire_cpus(proc: Path) -> int:
    texte = _lire(proc / "cpuinfo")
    if texte:
        n = sum(1 for ligne in texte.splitlines() if ligne.split(":")[0].strip() == "processor")
        if n:
            return n
    return os.cpu_count() or 1


def lire_mem_disponible_ko(proc: Path) -> int | None:
    texte = _lire(proc / "meminfo")
    for ligne in (texte or "").splitlines():
        if ligne.startswith("MemAvailable:"):
            try:
                return int(ligne.split()[1])
            except (ValueError, IndexError):
                return None
    return None


def lire_processus(proc: Path) -> dict[int, tuple[int, list[str]]]:
    """``{pid: (ppid, argv)}`` pour chaque processus lisible ; les threads du noyau sont ignorés."""
    resultat: dict[int, tuple[int, list[str]]] = {}
    try:
        entrees = list(proc.iterdir())
    except OSError:
        return resultat
    for entree in entrees:
        if not entree.name.isdigit():
            continue
        brut = None
        try:
            brut = (entree / "cmdline").read_bytes()
            stat = (entree / "stat").read_text()
        except OSError:
            continue
        argv = [a.decode(errors="replace") for a in brut.split(b"\0") if a]
        if not argv:
            continue
        # « pid (comm) état ppid … » : comm peut contenir espaces et parenthèses,
        # on repart donc de la dernière « ) ».
        try:
            ppid = int(stat[stat.rindex(")") + 1:].split()[1])
        except (ValueError, IndexError):
            ppid = 0
        resultat[int(entree.name)] = (ppid, argv)
    return resultat


def descendants(processus: dict[int, tuple[int, list[str]]], racines: set[int]) -> set[int]:
    """Les racines et tous leurs descendants, à n'importe quelle profondeur."""
    ensemble = set(racines)
    change = True
    while change:
        change = False
        for pid, (ppid, _argv) in processus.items():
            if ppid in ensemble and pid not in ensemble:
                ensemble.add(pid)
                change = True
    return ensemble


# --- Le relevé ----------------------------------------------------------------

def releve(proc: Path | str = "/proc", hors_pid: set[int] | None = None) -> dict:
    """Relevé complet : ``verdict``, ``causes``, ``familles``, ``mesures``."""
    proc = Path(proc)
    charge = lire_charge(proc)
    cpus = lire_cpus(proc)
    cpu_some = lire_pression(proc, "cpu", "some", "avg10")
    mem_full = lire_pression(proc, "memory", "full", "avg60")
    mem_dispo = lire_mem_disponible_ko(proc)

    processus = lire_processus(proc)
    exclus = descendants(processus, hors_pid or set())
    familles: list[str] = []
    for pid, (_ppid, argv) in sorted(processus.items()):
        if pid in exclus:
            continue
        for f in familles_de(argv):
            if f not in familles:
                familles.append(f)

    causes: list[dict] = []
    if mem_full is not None and mem_full >= SEUIL_MEM_FULL_AVG60:
        causes.append({"code": "pression-memoire", "decisive": True, "detail": (
            f"pression mémoire « full » sur 60 s à {mem_full:g} (seuil {SEUIL_MEM_FULL_AVG60:g})")})
    if mem_dispo is not None and mem_dispo < SEUIL_MEM_DISPONIBLE_KO:
        causes.append({"code": "memoire-disponible", "decisive": True, "detail": (
            f"{mem_dispo / 1024 / 1024:.1f} Go disponibles "
            f"(seuil {SEUIL_MEM_DISPONIBLE_KO / 1024 / 1024:.1f} Go)")})
    saturee = bool(causes)

    if cpu_some is not None and cpu_some >= SEUIL_CPU_SOME_AVG10:
        causes.append({"code": "pression-cpu", "decisive": True, "detail": (
            f"pression CPU « some » sur 10 s à {cpu_some:g} (seuil {SEUIL_CPU_SOME_AVG10:g})")})
    for f in familles:
        causes.append({"code": f"famille-{f}", "decisive": True,
                       "detail": f"famille lourde active hors du détenteur du jeton : {f}"})
    if charge is not None:
        causes.append({"code": "charge-moyenne", "decisive": False, "detail": (
            f"charge moyenne {charge:g} sur {cpus} cœurs (cité, ne décide pas)")})

    chargee = any(c["decisive"] for c in causes) and not saturee
    verdict = VERDICT_SATUREE if saturee else VERDICT_CHARGEE if chargee else VERDICT_LIBRE
    return {
        "verdict": verdict,
        "causes": causes,
        "familles": familles,
        "mesures": {
            "charge_moyenne_1m": charge, "cpus": cpus,
            "pression_cpu_some_avg10": cpu_some, "pression_memoire_full_avg60": mem_full,
            "memoire_disponible_ko": mem_dispo,
        },
    }


def formater(rel: dict) -> str:
    lignes = [rel["verdict"]]
    lignes += [f"- {c['detail']}" for c in rel["causes"]]
    return "\n".join(lignes)


# --- Ligne de commande --------------------------------------------------------

def _parser() -> argparse.ArgumentParser:
    commun = argparse.ArgumentParser(add_help=False)
    commun.add_argument("--proc", default="/proc", help="racine de /proc (pour les tests)")
    p = argparse.ArgumentParser(description="État de la machine et jeton des actions lourdes.")
    sous = p.add_subparsers(dest="commande", required=True)
    r = sous.add_parser("releve", parents=[commun], help="verdict libre / chargée / saturée")
    r.add_argument("--json", action="store_true", help="sortie structurée")
    r.add_argument("--hors-pid", type=int, action="append", default=[], metavar="PID",
                   help="exclut ce processus et ses descendants du décompte des familles")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.commande == "releve":
        rel = releve(args.proc, set(args.hors_pid))
        print(json.dumps(rel, ensure_ascii=False, indent=2) if args.json else formater(rel))
        return 0
    return 2  # inatteignable : argparse refuse toute autre commande


if __name__ == "__main__":
    sys.exit(main())
