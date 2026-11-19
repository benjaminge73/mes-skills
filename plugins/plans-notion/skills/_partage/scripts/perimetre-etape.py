#!/usr/bin/env python3
"""Une étape n'a-t-elle touché que les fichiers de sa liste fermée ?

Pourquoi : le brief d'une étape nomme les fichiers qu'elle a le droit de toucher. L'exécutant
peut pourtant retoucher un fichier de plus (un import, une doc voisine), et le rapport peut
ne pas le dire. Ici, c'est git qui répond : le pilote compare ce qui a changé entre le SHA
d'avant l'étape et ``HEAD`` à la liste du brief, au retour de l'exécutant.

Usage :
  perimetre-etape.py --base <sha> --fichiers <liste>

  --base     : commit d'avant l'étape ; le contrôle porte sur ``<base>..HEAD``.
  --fichiers : fichiers autorisés, relatifs à la racine du dépôt, séparés par des virgules.
               L'option peut se répéter (``--fichiers a --fichiers b``).

Codes :
  0 tout fichier touché entre ``<base>`` et ``HEAD`` est dans la liste (rien sur la sortie)
  1 au moins un fichier touché est hors de la liste : un par ligne, sur la sortie standard
  2 panne : base inconnue, dossier hors dépôt git, git en échec, liste vide, usage incorrect

Limites : le script lit les commits, pas l'arbre de travail. Une modification non commitée
n'est pas vue. Les renommages sont lus comme une suppression plus un ajout (``--no-renames``),
pour que l'ancien chemin d'un fichier déplacé compte aussi.

Lance ``git`` dans le dossier courant, et rien d'autre. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import posixpath
import subprocess
import sys

OK, HORS_LISTE, PANNE = 0, 1, 2


def _git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _sha_connu(sha: str) -> bool:
    return _git(["rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"]).returncode == 0


def _normaliser(chemin: str) -> str:
    """`./src/a.py` devient `src/a.py` : sans cela, la liste du brief ne reconnaît rien."""
    return posixpath.normpath(chemin.strip())


def _liste(valeurs: list[str]) -> list[str]:
    """Les fichiers de la liste, à partir des options répétées et des virgules."""
    morceaux = (m for v in valeurs for m in v.split(",") if m.strip())
    return sorted({_normaliser(m) for m in morceaux})


def _fichiers_touches(base: str) -> list[str]:
    """Chemins touchés entre ``base`` et ``HEAD``. Sans ``--no-renames``, git ne rendrait que
    le nouveau nom d'un fichier renommé : l'ancien, hors liste, passerait inaperçu."""
    sortie = _git(["diff", "--name-only", "--no-renames", "-z", f"{base}..HEAD"])
    if sortie.returncode != 0:
        raise RuntimeError(sortie.stderr.strip() or "git diff a échoué")
    return [m for m in sortie.stdout.split("\0") if m]


def verifier(base: str, autorises: list[str]) -> tuple[int, list[str]]:
    """Rend le code de sortie et les fichiers hors liste (vide si tout est dans la liste)."""
    if not _sha_connu(base):
        return PANNE, [f"base inconnue dans ce dépôt (ou dossier hors dépôt git) : {base}"]
    try:
        touches = _fichiers_touches(base)
    except RuntimeError as erreur:
        return PANNE, [str(erreur)]
    permis = set(autorises)
    hors = [chemin for chemin in touches if chemin not in permis]
    return (HORS_LISTE if hors else OK), hors


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(
        description="Vérifie qu'une étape n'a touché que les fichiers de sa liste fermée.")
    parseur.add_argument("--base", required=True, metavar="SHA",
                         help="commit d'avant l'étape ; le contrôle porte sur base..HEAD")
    parseur.add_argument("--fichiers", required=True, action="append", metavar="LISTE",
                         help="fichiers autorisés, relatifs à la racine du dépôt, séparés par "
                              "des virgules ; l'option peut se répéter")
    args = parseur.parse_args(argv)

    autorises = _liste(args.fichiers)
    if not autorises:
        print("liste vide : --fichiers doit nommer au moins un fichier", file=sys.stderr)
        return PANNE

    code, lignes = verifier(args.base, autorises)
    if code == PANNE:
        print("\n".join(lignes), file=sys.stderr)
        return PANNE
    if code == HORS_LISTE:
        print("\n".join(lignes))
    else:
        print("Tous les fichiers touchés sont dans la liste de l'étape.", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
