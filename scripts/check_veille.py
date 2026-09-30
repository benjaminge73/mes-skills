#!/usr/bin/env python3
"""Pas de mise à jour de skill sur une veille périmée.

Un fait de doc peut changer d'une version de Claude Code à l'autre : une règle
ou un contrôle fondé sur un fait périmé protège la mauvaise chose (voir
``docs/veille.md``, partie « Les faits porteurs »). La règle : avant toute PR
qui touche un skill, un agent, un hook ou un ``_partage/``, une passe de veille
— l'agent ``chercheur``, avec le brief de ``docs/veille.md``, lit les sources
depuis la dernière passe, et l'entrée datée s'ajoute au journal.

Ce script en est le garde : une PR qui touche ``plugins/<p>/skills/``,
``agents/`` ou ``hooks/`` est refusée si la dernière entrée du journal de
``docs/veille.md`` a **plus de 30 jours** (le seuil est ``veille_jours_max`` dans
``scripts/limites.json`` ; il ne peut que baisser). Une PR qui ne touche que
``docs/``, ``scripts/`` ou le README n'exige rien.

La date de référence est injectable — ``--aujourdhui AAAA-MM-JJ`` ou la
variable ``VEILLE_AUJOURDHUI`` — pour que les tests ne dépendent pas du jour.

Codes de sortie : ``0`` respectée, ``1`` refusée, ``2`` panne (base illisible,
date invalide).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_lecon_a_son_cas import DECLENCHEUR  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SEUIL_PAR_DEFAUT = 30

_TITRE_JOURNAL = re.compile(r"^##\s+.*journal", re.IGNORECASE)
_ENTREE = re.compile(r"^###\s+(\d{4})-(\d{2})-(\d{2})\b")


class BaseIllisible(RuntimeError):
    """La base de comparaison n'existe pas dans ce clone."""


@dataclass
class Verdict:
    refus: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    derniere_passe: date | None = None


def dates_du_journal(texte: str) -> list[date]:
    """Les dates des entrées ``### AAAA-MM-JJ …`` de la partie « Journal des passes »."""
    dans_le_journal = False
    dates: list[date] = []
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dans_le_journal = bool(_TITRE_JOURNAL.match(ligne))
            continue
        m = _ENTREE.match(ligne)
        if dans_le_journal and m:
            try:
                dates.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            except ValueError:
                continue
    return dates


def _plugins_touches(racine: Path, base: str, tete: str) -> list[str]:
    for ref in (base, tete):
        connu = subprocess.run(["git", "cat-file", "-e", f"{ref}^{{commit}}"], cwd=racine,
                               capture_output=True, text=True)
        if connu.returncode != 0:
            raise BaseIllisible(f"la référence `{ref}` est introuvable dans ce clone")
    diff = subprocess.run(["git", "diff", "--no-renames", "--name-only", f"{base}...{tete}"],
                          cwd=racine, capture_output=True, text=True)
    if diff.returncode != 0:
        raise BaseIllisible(diff.stderr.strip())
    plugins = {m.group(1) for f in diff.stdout.splitlines() if (m := DECLENCHEUR.match(f))}
    return sorted(plugins)


def analyser(racine: Path, base: str, tete: str, aujourdhui: date,
             seuil: int = SEUIL_PAR_DEFAUT) -> Verdict:
    verdict = Verdict(plugins=_plugins_touches(racine, base, tete))
    if not verdict.plugins:
        return verdict

    journal = racine / "docs" / "veille.md"
    dates = dates_du_journal(journal.read_text(encoding="utf-8")) if journal.is_file() else []
    touches = ", ".join(f"plugins/{p}/" for p in verdict.plugins)
    consigne = ("Faire la passe de veille : l'agent `chercheur`, avec le brief de docs/veille.md, "
                "lit les sources depuis la dernière passe ; ce qui s'applique entre dans la PR "
                "(ou dans un plan si c'est plus gros) ; puis ajouter l'entrée datée au journal "
                "de docs/veille.md.")
    if not dates:
        verdict.refus.append(
            f"la PR touche {touches} mais docs/veille.md n'a aucune entrée datée dans son "
            f"journal des passes (ou n'existe pas). {consigne}")
        return verdict

    verdict.derniere_passe = max(dates)
    age = (aujourdhui - verdict.derniere_passe).days
    if age > seuil:
        verdict.refus.append(
            f"la PR touche {touches} et la dernière passe de veille date du "
            f"{verdict.derniere_passe.isoformat()}, il y a {age} jours : au-delà des {seuil} jours "
            f"admis. {consigne}")
    return verdict


def _seuil(racine: Path) -> int:
    try:
        limites = json.loads((racine / "scripts" / "limites.json").read_text(encoding="utf-8"))
        return int(limites.get("veille_jours_max", SEUIL_PAR_DEFAUT))
    except (OSError, ValueError):
        return SEUIL_PAR_DEFAUT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--racine", type=Path, default=REPO_ROOT)
    parser.add_argument("--base", default=os.environ.get("BASE_REF", "origin/main"),
                        help="base de la PR (défaut : $BASE_REF, sinon origin/main)")
    parser.add_argument("--tete", default="HEAD")
    parser.add_argument("--aujourdhui", default=os.environ.get("VEILLE_AUJOURDHUI"),
                        help="date de référence AAAA-MM-JJ (défaut : aujourd'hui ; "
                             "ou $VEILLE_AUJOURDHUI)")
    parser.add_argument("--seuil", type=int, default=None,
                        help="jours admis (défaut : veille_jours_max de scripts/limites.json)")
    args = parser.parse_args(argv)

    try:
        aujourdhui = date.fromisoformat(args.aujourdhui) if args.aujourdhui else date.today()
    except ValueError:
        print(f"Veille — date de référence invalide : {args.aujourdhui!r} (attendu AAAA-MM-JJ).",
              file=sys.stderr)
        return 2
    seuil = args.seuil if args.seuil is not None else _seuil(args.racine)

    try:
        verdict = analyser(args.racine, args.base, args.tete, aujourdhui, seuil)
    except BaseIllisible as panne:
        print(f"Veille — comparaison impossible ({panne}). Sans base, rien n'a été vérifié : "
              "faire `git fetch origin main`, ou passer --base / BASE_REF.", file=sys.stderr)
        return 2

    if verdict.refus:
        print("Veille — cette PR ne peut pas être fusionnée :\n  " + "\n  ".join(verdict.refus),
              file=sys.stderr)
        return 1
    if verdict.plugins:
        print(f"Veille : respectée (dernière passe le {verdict.derniere_passe}, seuil {seuil} jours)")
    else:
        print("Veille : rien d'exigé (la PR ne touche ni skills, ni agents, ni hooks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
