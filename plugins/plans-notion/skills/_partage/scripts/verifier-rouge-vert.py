#!/usr/bin/env python3
"""Vérifie qu'un commit vert n'a pas retouché les tests du commit rouge.

Pourquoi : `preuve-du-rouge.md` pose que le commit vert ne touche aucun fichier de test. Jusqu'ici,
c'était une affirmation du sous-agent ; ici, c'est un `git diff` que le pilote rejoue avant de
commiter le vert. Un test désactivé (`skip`, `xfail`), une assertion retirée ou remplacée par
`assert True` / `pass` font passer la barre sans rien prouver : c'est le geste que la preuve
existe pour empêcher.

Règle : entre le rouge et le vert, tout fichier de test ajouté, modifié ou supprimé fait code 1.
Le détail dit pourquoi (désactivation, assertion retirée, fichier supprimé) pour que le pilote
voie la triche, mais la sortie ne dépend pas de ce détail : un fichier de test bougé suffit.

Usage :
  verifier-rouge-vert.py <sha-rouge> <sha-vert> [--tests <chemin> ...]

  --tests : fichiers ou dossiers de test, relatifs à la racine du dépôt. Sans cette option, un
            fichier est tenu pour un test s'il est dans un dossier `tests/`, `test/` ou
            `__tests__/`, ou si son nom suit `test_*`, `*_test.*`, `*.test.*` ou `*.spec.*`.

Codes :
  0 aucun fichier de test n'a bougé entre les deux commits (le vert ne touche que le code)
  1 au moins un fichier de test a bougé ; la liste est sur la sortie standard
  2 panne : un SHA est inconnu, ce dossier n'est pas un dépôt git, ou usage incorrect

Lance `git` dans le dossier courant, et rien d'autre : il ne lit ni ne modifie l'arbre de travail.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

OK, TRICHE, PANNE = 0, 1, 2

DOSSIERS_DE_TEST = {"tests", "test", "__tests__"}
MOTIF_NOM_DE_TEST = re.compile(r"^(test_.*|.*_test\..*|.*\.test\..*|.*\.spec\..*)$")

# Une désactivation : `.skip`, `@unittest.skip`, `skipTest`, `xfail`.
DESACTIVATION = re.compile(r"\bskip|\bxfail\b")
# Une assertion : `assert`, `self.assertEqual`, `expect(` (jest).
ASSERTION = re.compile(r"\bassert|\bexpect\(")
# Une assertion remplacée par rien qui teste : `assert True`, `pass`.
ASSERTION_VIDE = re.compile(r"^\s*(assert\s+True|pass)\s*$")


def _git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _sha_connu(sha: str) -> bool:
    return _git(["rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"]).returncode == 0


def _est_un_test(chemin: str, tests: list[str] | None) -> bool:
    if tests is not None:
        return any(chemin == t or chemin.startswith(t.rstrip("/") + "/") for t in tests)
    parties = chemin.split("/")
    return (any(p in DOSSIERS_DE_TEST for p in parties[:-1])
            or bool(MOTIF_NOM_DE_TEST.match(parties[-1])))


def _fichiers_modifies(rouge: str, vert: str) -> list[tuple[str, str]]:
    """Paires (statut, chemin) entre le rouge et le vert. Renommage vu comme suppression + ajout."""
    sortie = _git(["diff", "--name-status", "--no-renames", "-z", rouge, vert])
    if sortie.returncode != 0:
        raise RuntimeError(sortie.stderr.strip() or "git diff a échoué")
    morceaux = [m for m in sortie.stdout.split("\0") if m]
    return [(morceaux[i][0], morceaux[i + 1]) for i in range(0, len(morceaux) - 1, 2)]


def _raisons_de_modification(rouge: str, vert: str, chemin: str) -> list[str]:
    """Ce que le vert fait au fichier de test, en clair. Ne change pas le code de sortie."""
    diff = _git(["diff", "--unified=0", "--no-renames", rouge, vert, "--", chemin]).stdout
    ajoutees, retirees, dans_un_bloc = [], [], False
    for ligne in diff.splitlines():
        if ligne.startswith("@@"):
            dans_un_bloc = True
        elif dans_un_bloc and ligne.startswith("+"):
            ajoutees.append(ligne[1:])
        elif dans_un_bloc and ligne.startswith("-"):
            retirees.append(ligne[1:])

    raisons = []
    desactivations = [l.strip() for l in ajoutees if DESACTIVATION.search(l)]
    if desactivations:
        raisons.append(f"test désactivé ({desactivations[0]})")
    if any(ASSERTION.search(l) for l in retirees):
        raisons.append("assertion retirée ou remplacée")
    if any(ASSERTION_VIDE.match(l) for l in ajoutees):
        raisons.append("assertion remplacée par `assert True` ou `pass`")
    return raisons or ["fichier de test modifié"]


def verifier(rouge: str, vert: str, tests: list[str] | None) -> tuple[int, list[str]]:
    """Rend le code de sortie et les lignes de la liste (vide si le vert ne touche aucun test)."""
    for sha in (rouge, vert):
        if not _sha_connu(sha):
            return PANNE, [f"SHA inconnu dans ce dépôt : {sha}"]
    try:
        modifies = _fichiers_modifies(rouge, vert)
    except RuntimeError as panne:
        return PANNE, [str(panne)]

    lignes = []
    for statut, chemin in modifies:
        if not _est_un_test(chemin, tests):
            continue
        if statut == "D":
            raisons = ["fichier de test supprimé"]
        elif statut == "A":
            raisons = ["fichier de test ajouté au vert"]
        else:
            raisons = _raisons_de_modification(rouge, vert, chemin)
        lignes.append(f"  {statut} {chemin} — {'; '.join(raisons)}")
    return (TRICHE if lignes else OK), lignes


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(
        description="Vérifie qu'un commit vert ne retouche aucun fichier de test du commit rouge.")
    parseur.add_argument("rouge", help="SHA du commit rouge (tests seuls)")
    parseur.add_argument("vert", help="SHA du commit vert (code)")
    parseur.add_argument("--tests", nargs="+", metavar="CHEMIN",
                         help="fichiers ou dossiers de test, relatifs à la racine du dépôt")
    args = parseur.parse_args(argv)

    code, lignes = verifier(args.rouge, args.vert, args.tests)
    if code == PANNE:
        print("\n".join(lignes), file=sys.stderr)
        return PANNE
    if code == TRICHE:
        print(f"Fichiers de test modifiés entre {args.rouge[:12]} (rouge) et "
              f"{args.vert[:12]} (vert) : le vert ne doit en toucher aucun.")
        print("\n".join(lignes))
    else:
        print("Aucun fichier de test modifié entre le rouge et le vert.")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
