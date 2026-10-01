#!/usr/bin/env python3
"""État de la machine : peut-elle recevoir une action lourde maintenant ?

Usage :
    etat-machine.py releve [--json] [--hors-pid PID ...] [--proc RACINE]
    etat-machine.py prendre <action> --plan <titre> [--attendre S] [--pid PID]
    etat-machine.py rendre [--pid PID]
    etat-machine.py qui [--json]

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
rend pas la machine « chargée » pour lui-même. Les détenteurs vivants du jeton
sont exclus d'office, sans qu'il faille les nommer.

Le jeton des actions lourdes
----------------------------
Une action lourde (suite complète, e2e, évals locales, rejeu, build…) ne part
qu'avec le jeton : ``PLACES_LOURDES`` places, une seule aujourd'hui.

* ``prendre <action> --plan <titre>`` pose le jeton et écrit dans
  ``${XDG_STATE_HOME:-~/.local/state}/plans-notion/lourd.lock`` le PID du
  détenteur, l'action, le plan et l'heure. Avec ``--attendre S``, une prise sur
  un jeton tenu réessaie (toutes les 0,2 s) pendant S secondes avant d'échouer.
  Une machine ``saturée`` refuse tout de suite : attendre ne l'arrange pas.
  ``chargée`` n'empêche rien : le relevé est rendu sur la 2e ligne pour que
  l'appelant prévienne les autres.
* ``rendre`` libère le jeton du PID donné ; sans effet pour un autre PID.
* ``qui`` dit qui le tient (``--json`` : ``{"detenteurs": [...]}``).

Le détenteur est un **PID** (``--pid``, par défaut le processus parent du
script : ``prendre`` est appelé par un script shell qui continue ensuite, et le
``flock`` d'un Python qui se termine se libère aussitôt). C'est donc le fichier
d'état qui fait foi, et ``flock`` ne protège que sa lecture-écriture. Un
détenteur dont le processus a disparu (ou dont le numéro a été réutilisé par un
autre processus : l'heure de démarrage est comparée) est libéré à la prise
suivante. Le PID doit exister au moment de la prise.

Le fichier d'état vit hors des dépôts et ne se commite jamais.

``--proc`` change la racine de ``/proc`` : c'est ce qui permet aux tests de lire
des fixtures au lieu de la vraie machine.

Python 3, bibliothèque standard seulement. Lit du Linux générique : en session
cloud, sans VPS, le script répond simplement sur la machine où il tourne. Une
mesure illisible (pas de ``/proc/pressure``, par exemple) est ignorée, jamais
une erreur : on répond sur ce qu'on lit.

Codes de sortie : 0 relevé rendu / jeton accordé / jeton rendu / réponse de
``qui`` ; 2 usage (dont un PID inexistant) ; 3 ``prendre`` refusé, jeton
occupé ; 4 ``prendre`` refusé, machine saturée.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import sys
import time
from datetime import datetime
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

# --- Le jeton -------------------------------------------------------------------

# Nombre d'actions lourdes simultanées. Provenance : POC de Q9, 2026-10-01 — à
# deux (e2e Playwright de vahiny + suite de hermes-custom), l'e2e est tombée sur
# un timeout de 30 s et la suite a pris 32 % de plus. Repasser à 2 un jour,
# c'est changer cette ligne et refaire la mesure.
PLACES_LOURDES = 1

SORTIE_OK = 0
SORTIE_USAGE = 2
SORTIE_OCCUPE = 3
SORTIE_SATUREE = 4

PAS_D_ATTENTE_S = 0.2

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


# --- Le jeton : fichier d'état et processus détenteurs ------------------------

def dossier_etat() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return Path(base) / "plans-notion"


def fichier_jeton() -> Path:
    return dossier_etat() / "lourd.lock"


def lire_demarrage(proc: Path, pid: int) -> int | None:
    """Heure de démarrage (champ 22 de ``stat``) d'un processus vivant, sinon ``None``.

    Un zombie est mort pour nous. Le couple (PID, heure de démarrage) identifie
    un processus : le noyau recycle les PID, jamais cette paire.
    """
    texte = _lire(proc / str(pid) / "stat")
    if not texte or ")" not in texte:
        return None
    champs = texte[texte.rindex(")") + 1:].split()
    try:
        if champs[0] == "Z":
            return None
        return int(champs[19])
    except (IndexError, ValueError):
        return None


def est_vivant(proc: Path, detenteur: dict) -> bool:
    try:
        return lire_demarrage(proc, int(detenteur["pid"])) == detenteur["demarrage"]
    except (KeyError, TypeError, ValueError):
        return False


@contextlib.contextmanager
def verrou(creer: bool, exclusif: bool):
    """Ouvre le fichier du jeton sous ``flock`` ; rend ``None`` s'il n'existe pas (et ``creer`` faux)."""
    chemin = fichier_jeton()
    if creer:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(chemin, os.O_RDWR | os.O_CREAT, 0o644)
    else:
        try:
            fd = os.open(chemin, os.O_RDONLY)
        except FileNotFoundError:
            yield None
            return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if exclusif else fcntl.LOCK_SH)
        yield fd
    finally:
        os.close(fd)  # ferme aussi le verrou


def lire_detenteurs(fd: int | None) -> list[dict]:
    """Détenteurs écrits dans le fichier ; un fichier absent, vide ou illisible vaut « personne »."""
    if fd is None:
        return []
    os.lseek(fd, 0, os.SEEK_SET)
    brut = b""
    while morceau := os.read(fd, 65536):
        brut += morceau
    try:
        detenteurs = json.loads(brut.decode())["detenteurs"]
        return [d for d in detenteurs if isinstance(d, dict)]
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return []


def ecrire_detenteurs(fd: int, detenteurs: list[dict]) -> None:
    donnees = json.dumps({"detenteurs": detenteurs}, ensure_ascii=False, indent=2).encode()
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, donnees)


def detenteurs_vivants(proc: Path) -> list[dict]:
    with verrou(creer=False, exclusif=False) as fd:
        return [d for d in lire_detenteurs(fd) if est_vivant(proc, d)]


def prendre(proc: Path, action: str, plan: str, pid: int, attendre: float) -> int:
    demarrage = lire_demarrage(proc, pid)
    if demarrage is None:
        print(f"prendre : le PID {pid} n'existe pas — le jeton se prend pour un processus vivant.",
              file=sys.stderr)
        return SORTIE_USAGE
    fin = time.monotonic() + max(attendre, 0.0)
    while True:
        with verrou(creer=True, exclusif=True) as fd:
            vivants = [d for d in lire_detenteurs(fd) if est_vivant(proc, d)]
            moi = next((d for d in vivants if d["pid"] == pid), None)
            if moi is not None:
                # Même processus qui redemande : pas de blocage sur soi-même.
                moi["action"], moi["plan"] = action, plan
                ecrire_detenteurs(fd, vivants)
                print(f"accordé\njeton déjà tenu par le PID {pid}")
                return SORTIE_OK
            if len(vivants) >= PLACES_LOURDES:
                tenu_par = vivants[0]
            else:
                rel = releve(proc, {d["pid"] for d in vivants})
                if rel["verdict"] == VERDICT_SATUREE:
                    print("refusé : machine saturée", file=sys.stderr)
                    print(formater(rel), file=sys.stderr)
                    return SORTIE_SATUREE
                vivants.append({"pid": pid, "demarrage": demarrage, "action": action,
                                "plan": plan, "depuis": datetime.now().astimezone().isoformat(
                                    timespec="seconds")})
                ecrire_detenteurs(fd, vivants)
                print(f"accordé\nrelevé : {rel['verdict']}")
                return SORTIE_OK
        reste = fin - time.monotonic()
        if reste <= 0:
            print(f"refusé : jeton tenu par le PID {tenu_par['pid']} — {tenu_par.get('action')} "
                  f"({tenu_par.get('plan')}) depuis {tenu_par.get('depuis')}", file=sys.stderr)
            return SORTIE_OCCUPE
        time.sleep(min(PAS_D_ATTENTE_S, reste))


def rendre(proc: Path, pid: int) -> int:
    with verrou(creer=True, exclusif=True) as fd:
        vivants = [d for d in lire_detenteurs(fd) if est_vivant(proc, d)]
        restants = [d for d in vivants if d["pid"] != pid]
        ecrire_detenteurs(fd, restants)
    print("rendu" if len(restants) < len(vivants) else f"rien à rendre : le PID {pid} ne tient pas le jeton")
    return SORTIE_OK


def qui(proc: Path, en_json: bool) -> int:
    vivants = detenteurs_vivants(proc)
    if en_json:
        print(json.dumps({"detenteurs": vivants}, ensure_ascii=False, indent=2))
    elif not vivants:
        print("libre")
    else:
        for d in vivants:
            print(f"{d.get('action')} — {d.get('plan')} (PID {d['pid']}, depuis {d.get('depuis')})")
    return SORTIE_OK


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
    t = sous.add_parser("prendre", parents=[commun], help="prend le jeton des actions lourdes")
    t.add_argument("action", help="ce qui va tourner (ex. « e2e vahiny »)")
    t.add_argument("--plan", required=True, help="titre du plan au nom duquel on prend le jeton")
    t.add_argument("--attendre", type=float, default=0.0, metavar="S",
                   help="secondes à réessayer si le jeton est tenu (défaut : 0, refus immédiat)")
    t.add_argument("--pid", type=int, default=None, help="PID du détenteur (défaut : processus parent)")
    d = sous.add_parser("rendre", parents=[commun], help="rend le jeton")
    d.add_argument("--pid", type=int, default=None, help="PID du détenteur (défaut : processus parent)")
    q = sous.add_parser("qui", parents=[commun], help="dit qui tient le jeton")
    q.add_argument("--json", action="store_true", help="sortie structurée")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    proc = Path(args.proc)
    if args.commande == "releve":
        # Ce que lance un détenteur du jeton ne compte pas contre lui-même.
        hors = set(args.hors_pid) | {d["pid"] for d in detenteurs_vivants(proc)}
        rel = releve(proc, hors)
        print(json.dumps(rel, ensure_ascii=False, indent=2) if args.json else formater(rel))
        return SORTIE_OK
    pid = getattr(args, "pid", None)
    pid = os.getppid() if pid is None else pid
    if args.commande == "prendre":
        return prendre(proc, args.action, args.plan, pid, args.attendre)
    if args.commande == "rendre":
        return rendre(proc, pid)
    if args.commande == "qui":
        return qui(proc, args.json)
    return SORTIE_USAGE  # inatteignable : argparse refuse toute autre commande


if __name__ == "__main__":
    sys.exit(main())
