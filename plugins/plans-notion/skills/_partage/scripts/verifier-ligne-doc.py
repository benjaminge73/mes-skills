#!/usr/bin/env python3
"""Joue en local, avant `gh pr ready`, la garde que le job CI `doc` jouera sur la PR.

Pourquoi : relevé du 2026-11-03, 34 échecs du job `doc` en 19 jours sur les six dépôts à doc
vivante, masqués parce que `doc-relance.yml` relance le job une fois la ligne corrigée (le run
finit vert, l'échec ne se voit plus dans la liste des runs). Deux causes : une PR passée prête
avec `Doc :` vide ou « à venir », et un repli écrit sous une forme que la garde du dépôt
refusait. Chaque échec coûte un run de CI ; la même garde, jouée ici, coûte une seconde.

Ce script ne réécrit aucune règle : il trouve la garde du dépôt et la joue telle quelle, avec
le même contrat que `ci.yml` (le corps dans PR_BODY, l'auteur dans PR_AUTHOR). Une garde qui
change dans un dépôt change donc aussi ici, sans copie à tenir à jour.

Usage :
  verifier-ligne-doc.py <numéro de PR> [--depot <dossier>]   lit la description par `gh pr view`
  verifier-ligne-doc.py --corps <fichier> [--depot <dossier>]   lit une description pas encore postée

Gardes cherchées dans le dépôt (le dossier courant par défaut), dans cet ordre :
  scripts/garde_doc_pr.py   (python3)   hermes-custom, job-agent, mavod-perso, mes-skills, micro-trading
  scripts/garde-doc-pr.mjs  (node)      vahiny

Codes : ceux de la garde (0 accepté, 1 refusé, 4 rien d'écrit après `Doc :`), plus
  2 panne (lecture de la PR impossible, fichier absent, interpréteur absent) ;
  3 le dépôt n'a pas de garde : la CI ne lira pas la ligne. Ce n'est pas un feu vert sur la
    doc : c'est l'encadré « Doc vivante » de la page projet qui dit si une entrée est due.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

GARDES = (("scripts/garde_doc_pr.py", "python3"), ("scripts/garde-doc-pr.mjs", "node"))
PANNE, SANS_GARDE = 2, 3


def trouver_garde(depot: Path) -> tuple[Path, str] | None:
    for chemin, interpreteur in GARDES:
        if (depot / chemin).is_file():
            return depot / chemin, interpreteur
    return None


def lire_pr(numero: str, depot: Path) -> tuple[str, str]:
    """Rend (corps, login de l'auteur) de la PR, lus comme le job `doc` les lit."""
    sortie = subprocess.run(
        ["gh", "pr", "view", numero, "--json", "body,author"],
        cwd=depot, capture_output=True, text=True, check=True).stdout
    donnees = json.loads(sortie)
    return donnees.get("body") or "", (donnees.get("author") or {}).get("login", "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("numero", nargs="?", help="numéro de la PR")
    source.add_argument("--corps", type=Path, help="fichier de la description, avant de la poster")
    parser.add_argument("--depot", type=Path, default=Path.cwd(), help="dossier du dépôt (défaut : courant)")
    parser.add_argument("--auteur", default="benjaminge73",
                        help="auteur de la PR avec --corps (défaut : benjaminge73)")
    args = parser.parse_args(argv)

    garde = trouver_garde(args.depot)
    if garde is None:
        print(f"verifier-ligne-doc : aucune garde doc dans {args.depot} "
              f"({' ni '.join(c for c, _ in GARDES)}) : la CI ne lira pas la ligne.")
        return SANS_GARDE
    chemin, interpreteur = garde
    if shutil.which(interpreteur) is None:
        print(f"verifier-ligne-doc : {interpreteur} introuvable pour jouer {chemin}", file=sys.stderr)
        return PANNE

    try:
        if args.corps is not None:
            corps, auteur = args.corps.read_text(encoding="utf-8"), args.auteur
        else:
            corps, auteur = lire_pr(args.numero, args.depot)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as erreur:
        print(f"verifier-ligne-doc : lecture de la description impossible ({erreur})", file=sys.stderr)
        return PANNE

    env = {**os.environ, "PR_BODY": corps, "PR_AUTHOR": auteur}
    jeu = subprocess.run([interpreteur, str(chemin)], cwd=args.depot, env=env)
    verdict = {0: "acceptée", 1: "refusée", 4: "pas encore écrite"}.get(jeu.returncode, "panne")
    print(f"verifier-ligne-doc : ligne Doc {verdict} par {chemin.relative_to(args.depot)} "
          f"(code {jeu.returncode}){'' if jeu.returncode == 0 else ' : ne pas passer la PR prête'}")
    return jeu.returncode


if __name__ == "__main__":
    sys.exit(main())
