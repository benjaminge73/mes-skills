#!/usr/bin/env python3
"""Mesure le socle de contexte d'une session Claude Code, à partir de ses journaux.

Usage : socle-contexte.py [--depuis AAAA-MM-JJ] [--sessions <fichier tsv>] [--json]
                          [--projets <dossier>]

Lecture seule, bibliothèque standard seule. Le script lit les ``<projets>/*/*.jsonl``
(par défaut ``~/.claude/projects``) et rend, par session puis en médiane :

- ``premier_appel`` : le contexte du premier appel au modèle ;
- ``socle`` : le contexte du premier appel qui suit la dernière pièce de démarrage
  (``deferred_tools_delta`` ou ``mcp_instructions_delta``), c'est-à-dire le contexte
  une fois le démarrage posé ;
- ``pieces`` : la taille de chaque pièce injectée avant le socle, par type.

Le contexte d'un appel est la somme de ``input_tokens``, ``cache_creation_input_tokens``
et ``cache_read_input_tokens``. Un appel est compté une fois, dédoublonné sur
``message.id`` (un vrai journal écrit plusieurs lignes par appel).

Règles :

1. Les lignes ``isSidechain`` vraies (sous-agents) sont ignorées, de même que les
   messages synthétiques (``model == "<synthetic>"``, p.ex. erreur 403 ou 429) et
   toute ligne dont les trois compteurs valent zéro : ce ne sont pas des appels.
2. Une pièce de démarrage est un delta qui arrive avant le 10e appel distinct.
3. Après une compaction (``system`` de sous-type ``compact_boundary``), des deltas
   reviennent : ils ne sont pas des pièces de démarrage, et aucune pièce suivante
   n'est comptée.
4. La taille d'une pièce est son nombre de caractères. ``hook_success`` se mesure
   sur ``content`` (ce qui est injecté ; ``stdout`` reste la sortie brute du hook).
5. Pour ``deferred_tools_delta``, un nom ``mcp__<serveur>__<outil>`` est compté
   sous ``<serveur>`` ; les autres noms sont ``natifs``.

Codes de sortie : 0 rendu ; 2 aucun journal lisible (message sur stderr, pas de
trace Python). Un identifiant de ``--sessions`` introuvable est ignoré et signalé
sur stderr.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

PROJETS_PAR_DEFAUT = Path.home() / ".claude" / "projects"
APPELS_DE_DEMARRAGE = 10

PIECES_TYPES = (
    "instructions",
    "skill_listing",
    "agent_listing_delta",
    "deferred_tools_delta",
    "mcp_instructions_delta",
    "hook_success",
)
DELTAS_DE_DEMARRAGE = ("deferred_tools_delta", "mcp_instructions_delta")
CHAMPS_CONTEXTE = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
MODELE_SYNTHETIQUE = "<synthetic>"


def taille_piece(at: str, a: dict) -> int:
    """Nombre de caractères d'une pièce, selon son type."""
    if at == "instructions":
        fichiers = a.get("files") or []
        return sum(len(f.get("content") or "") for f in fichiers if isinstance(f, dict))
    if at == "skill_listing":
        return len(a.get("content") or "")
    if at in ("agent_listing_delta", "deferred_tools_delta"):
        return sum(len(x) for x in a.get("addedLines") or [] if isinstance(x, str))
    if at == "mcp_instructions_delta":
        return sum(len(x) for x in a.get("addedBlocks") or [] if isinstance(x, str))
    if at == "hook_success":
        return len(a.get("content") or "")
    return 0


def ventiler_deferred(noms: list, pieces_deferred: dict) -> None:
    """Compte les noms d'un deferred_tools_delta par serveur MCP, les natifs à part."""
    for nom in noms:
        if not isinstance(nom, str):
            continue
        pieces_deferred["noms"] += 1
        if nom.startswith("mcp__"):
            serveur = nom[len("mcp__"):].split("__", 1)[0]
            par = pieces_deferred["par_serveur"]
            par[serveur] = par.get(serveur, 0) + 1
        else:
            pieces_deferred["natifs"] += 1


def analyser(lignes: list) -> dict | None:
    """Rend le résumé d'une session, ou None s'il n'y a aucun appel lisible."""
    version = None
    debut = None
    appels: list[tuple[int, int]] = []  # (position de la ligne, contexte)
    vus: set[str] = set()
    compactee = False
    dernier_delta = None  # position de la dernière pièce de démarrage
    pieces_brutes: list[tuple[int, str, dict]] = []

    for position, d in enumerate(lignes):
        if d.get("isSidechain") is True:
            continue
        if version is None and isinstance(d.get("version"), str):
            version = d["version"]
        if debut is None and isinstance(d.get("timestamp"), str):
            debut = d["timestamp"]
        t = d.get("type")
        if t == "system" and d.get("subtype") == "compact_boundary":
            compactee = True
            continue
        if t == "assistant":
            msg = d.get("message") or {}
            mid = msg.get("id")
            usage = msg.get("usage")
            if not mid or not isinstance(usage, dict) or mid in vus:
                continue
            if msg.get("model") == MODELE_SYNTHETIQUE:
                continue
            contexte = sum(int(usage.get(c) or 0) for c in CHAMPS_CONTEXTE)
            if contexte == 0:
                continue
            vus.add(mid)
            appels.append((position, contexte))
            continue
        if t == "attachment":
            a = d.get("attachment") or {}
            at = a.get("type")
            if compactee or at not in PIECES_TYPES:
                continue
            if at in DELTAS_DE_DEMARRAGE and len(vus) < APPELS_DE_DEMARRAGE:
                dernier_delta = position
            pieces_brutes.append((position, at, a))

    if not appels:
        return None

    premier_appel = appels[0][1]
    if dernier_delta is None:
        position_socle, socle = appels[0]
    else:
        suivants = [(p, c) for p, c in appels if p > dernier_delta]
        position_socle, socle = suivants[0] if suivants else (None, None)

    pieces = {t: {"nombre": 0, "caracteres": 0} for t in PIECES_TYPES}
    pieces["deferred_tools_delta"].update({"noms": 0, "par_serveur": {}, "natifs": 0})
    for position, at, a in pieces_brutes:
        if position_socle is not None and position >= position_socle:
            continue
        pieces[at]["nombre"] += 1
        pieces[at]["caracteres"] += taille_piece(at, a)
        if at == "deferred_tools_delta":
            ventiler_deferred(a.get("addedNames") or [], pieces["deferred_tools_delta"])

    return {
        "version": version,
        "debut": debut,
        "premier_appel": premier_appel,
        "socle": socle,
        "pieces": pieces,
    }


def lire_journal(chemin: Path) -> list | None:
    """Lignes JSON d'un journal ; None si le fichier ne se lit pas."""
    lignes = []
    try:
        with chemin.open(encoding="utf-8") as f:
            for brut in f:
                brut = brut.strip()
                if not brut:
                    continue
                try:
                    objet = json.loads(brut)
                except json.JSONDecodeError:
                    continue
                if isinstance(objet, dict):
                    lignes.append(objet)
    except (OSError, UnicodeDecodeError):
        return None
    return lignes


def lire_identifiants(fichier: Path) -> list[str]:
    """Colonne ``session`` d'un tsv à en-tête ; lève ValueError si l'en-tête ne la porte pas."""
    with fichier.open(encoding="utf-8", newline="") as f:
        lignes = list(csv.reader(f, delimiter="\t"))
    if not lignes or not lignes[0] or lignes[0][0].strip() != "session":
        raise ValueError(f"en-tête « session » absent en première colonne de {fichier}")
    return [ligne[0].strip() for ligne in lignes[1:] if ligne and ligne[0].strip()]


def journaux_a_lire(projets: Path, identifiants: list[str] | None, depuis_ts: float | None = None) -> list[Path]:
    """Journaux à analyser. Un fichier modifié avant ``depuis_ts`` n'est pas lu :
    il ne peut contenir aucun message de la fenêtre (le filtre fin reste sur le début de session)."""
    if identifiants is None:
        chemins = sorted(Path(p) for p in glob.glob(str(projets / "*" / "*.jsonl")))
    else:
        chemins = []
        for identifiant in identifiants:
            correspondants = sorted(projets.glob(f"*/{identifiant}.jsonl")) if "/" not in identifiant else []
            if correspondants:
                chemins.append(correspondants[0])
            else:
                print(f"identifiant introuvable, ignoré : {identifiant}", file=sys.stderr)
    if depuis_ts is None:
        return chemins
    return [c for c in chemins if c.stat().st_mtime >= depuis_ts]


def mediane(valeurs: list) -> int | float | None:
    valeurs = [v for v in valeurs if v is not None]
    if not valeurs:
        return None
    m = statistics.median(valeurs)
    return int(m) if float(m).is_integer() else m


def comptes_serveurs(deferred: dict) -> dict:
    """Noms d'un deferred_tools_delta par serveur MCP, ``natifs`` compris si non nul."""
    compte = dict(deferred["par_serveur"])
    if deferred["natifs"]:
        compte["natifs"] = deferred["natifs"]
    return compte


def ordonner(compte: dict) -> list[tuple[str, int]]:
    """Serveurs par nombre décroissant, à égalité par nom."""
    return sorted(compte.items(), key=lambda kv: (-kv[1], kv[0]))


def medianes_par_serveur(sessions: list[dict]) -> dict:
    """Médiane du nombre de noms par serveur ; un serveur absent d'une session compte 0."""
    serveurs = set()
    for s in sessions:
        serveurs |= set(comptes_serveurs(s["pieces"]["deferred_tools_delta"]))
    medianes_brutes = {
        serveur: mediane([comptes_serveurs(s["pieces"]["deferred_tools_delta"]).get(serveur, 0) for s in sessions])
        for serveur in serveurs
    }
    return dict(sorted(medianes_brutes.items(), key=lambda kv: (-kv[1], kv[0])))


def medianes(sessions: list[dict]) -> dict:
    return {
        "premier_appel": mediane([s["premier_appel"] for s in sessions]),
        "socle": mediane([s["socle"] for s in sessions]),
        "pieces": {t: mediane([s["pieces"][t]["caracteres"] for s in sessions]) for t in PIECES_TYPES},
        "deferred_tools_noms": mediane([s["pieces"]["deferred_tools_delta"]["noms"] for s in sessions]),
        "deferred_par_serveur": medianes_par_serveur(sessions),
    }


def texte_deferred(p: dict) -> str:
    detail = ", ".join(f"{k}={v}" for k, v in ordonner(comptes_serveurs(p)))
    return f"deferred_tools_delta={p['caracteres']}({p['noms']} noms" + (f": {detail}" if detail else "") + ")"


def texte_pieces(pieces: dict) -> str:
    morceaux = []
    for t in PIECES_TYPES:
        p = pieces[t]
        if t == "deferred_tools_delta":
            morceaux.append(texte_deferred(p))
        else:
            morceaux.append(f"{t}={p['caracteres']}")
    return "  ".join(morceaux)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mesure le socle de contexte des sessions Claude Code.")
    parser.add_argument("--depuis", metavar="AAAA-MM-JJ", help="ignorer les sessions commencées avant cette date")
    parser.add_argument("--sessions", metavar="FICHIER_TSV", help="tsv à en-tête ; colonne 1 = identifiants de session")
    parser.add_argument("--json", action="store_true", help="rendre du JSON au lieu du texte")
    parser.add_argument("--projets", metavar="DOSSIER", type=Path, default=PROJETS_PAR_DEFAUT,
                        help="dossier des journaux (défaut : ~/.claude/projects)")
    args = parser.parse_args(argv)

    depuis_ts = None
    if args.depuis is not None:
        try:
            depuis_ts = datetime.strptime(args.depuis, "%Y-%m-%d").timestamp()
        except ValueError:
            parser.error("--depuis attend une date AAAA-MM-JJ")

    identifiants = None
    if args.sessions is not None:
        try:
            identifiants = lire_identifiants(Path(args.sessions))
        except (OSError, ValueError) as e:
            print(f"socle-contexte : {e}", file=sys.stderr)
            return 2

    sessions = []
    for chemin in journaux_a_lire(args.projets, identifiants, depuis_ts):
        lignes = lire_journal(chemin)
        resume = analyser(lignes) if lignes is not None else None
        if resume is None:
            print(f"journal non lisible ou sans appel, ignoré : {chemin}", file=sys.stderr)
            continue
        if args.depuis and resume["debut"] and resume["debut"][:10] < args.depuis:
            continue
        resume["session"] = chemin.stem
        sessions.append(resume)

    if not sessions:
        print(f"aucun journal lisible dans {args.projets}", file=sys.stderr)
        return 2

    sessions.sort(key=lambda s: (s["debut"] or "", s["session"]))
    mediane_globale = medianes(sessions)

    if args.json:
        sortie = {
            "sessions": [
                {k: s[k] for k in ("session", "version", "premier_appel", "socle", "pieces")}
                for s in sessions
            ],
            "medianes": mediane_globale,
        }
        print(json.dumps(sortie, ensure_ascii=False, indent=2))
        return 0

    for s in sessions:
        socle = "-" if s["socle"] is None else s["socle"]
        print(f"{s['session']}  v{s['version'] or '?'}  premier_appel={s['premier_appel']}  "
              f"socle={socle}  {texte_pieces(s['pieces'])}")
    m = mediane_globale
    socle = "-" if m["socle"] is None else m["socle"]
    par_serveur = ", ".join(f"{k}={v}" for k, v in m["deferred_par_serveur"].items())
    print(f"médiane ({len(sessions)} sessions)  premier_appel={m['premier_appel']}  socle={socle}  "
          + "  ".join(f"{t}={v}" for t, v in m["pieces"].items())
          + f"  deferred_tools_noms={m['deferred_tools_noms']}"
          + f"  deferred_par_serveur=[{par_serveur}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
