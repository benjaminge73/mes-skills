#!/usr/bin/env python3
"""Vérifie qu'un commit vert n'a pas retouché les tests du commit rouge.

Pourquoi : `preuve-du-rouge.md` pose que le commit vert ne touche aucun fichier de test. Jusqu'ici,
c'était une affirmation du sous-agent ; ici, c'est un `git diff` que le pilote rejoue avant de
commiter le vert. Un test désactivé (`skip`, `xfail`), une assertion retirée ou remplacée par
`assert True` / `pass` font passer la barre sans rien prouver : c'est le geste que la preuve
existe pour empêcher.

Règle : entre le rouge et le vert, tout fichier de test ajouté, modifié ou supprimé fait code 1.
Un fichier de test est, dans cet ordre : tout fichier du commit rouge (le rouge ne porte que des
tests, par construction) ; ceux que désigne `--tests` ; sans `--tests`, ceux qui sont dans un
dossier `tests/`, `test/` ou `__tests__/`, ou dont le nom suit `test_*`, `*_test.*`, `*.test.*`
ou `*.spec.*`. Un vert qui ajoute, modifie ou supprime la configuration du lanceur de tests
(`conftest.py`, `pytest.ini`, `jest.config.*`, `vitest.config.*`) fait aussi code 1 : sans toucher
à un test, il ferait sauter les tests. `pyproject.toml`, `tox.ini` et `setup.cfg` ne comptent que
si le changement tombe dans une section de test (`[tool.pytest…]`, `[pytest]`, `[tool:pytest]`,
`[testenv…]`, ou une ligne qui porte `addopts`, `testpaths`, `norecursedirs`, `markers`) : une
dépendance ajoutée à `pyproject.toml` ne fait sauter aucun test, elle ne fait pas code 1.
Le détail dit pourquoi (désactivation, assertion retirée, fichier supprimé, configuration
retouchée) pour que le pilote voie la triche, mais la sortie ne dépend pas de ce détail.

Limite : le script ne lit que les deux commits. Un skip posé hors de ces fichiers, p.ex. une
variable d'environnement qui fait sauter un test, lui échappe.

Usage :
  verifier-rouge-vert.py <sha-rouge> <sha-vert> [--tests <chemin> ...]

  --tests : fichiers ou dossiers de test, relatifs à la racine du dépôt (`./tests` et `tests`
            sont équivalents). Il remplace la détection par nom, il ne s'y ajoute pas.

Codes :
  0 aucun fichier de test ni de configuration du lanceur n'a bougé entre les deux commits
  1 au moins un fichier de test ou de configuration du lanceur a bougé ; la liste est sur la
    sortie standard
  2 panne : un SHA est inconnu, ce dossier n'est pas un dépôt git, ou usage incorrect

Lance `git` dans le dossier courant, et rien d'autre : il ne lit ni ne modifie l'arbre de travail.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import fnmatch
import posixpath
import re
import subprocess
import sys

OK, TRICHE, PANNE = 0, 1, 2

DOSSIERS_DE_TEST = {"tests", "test", "__tests__"}
MOTIF_NOM_DE_TEST = re.compile(r"^(test_.*|.*_test\..*|.*\.test\..*|.*\.spec\..*)$")

# La configuration qui fait tourner les tests : la retoucher fait sauter des tests sans en toucher un.
CONFIG_LANCEUR = {"conftest.py", "pytest.ini"}
MOTIFS_CONFIG_LANCEUR = ("jest.config.*", "vitest.config.*")
# Configuration partagée avec autre chose que les tests (`pyproject.toml` porte aussi les
# dépendances) : elle ne compte que si un changement tombe dans une section de test.
CONFIG_PAR_SECTION = {"pyproject.toml", "tox.ini", "setup.cfg"}
# Ce qui, dans une section, dit qu'elle est celle du lanceur de tests.
MARQUEURS_SECTION_DE_TEST = ("[tool.pytest", "[pytest]", "[tool:pytest]", "[testenv",
                             "addopts", "testpaths", "norecursedirs", "markers")
EN_TETE_DE_SECTION = re.compile(r"^\s*\[[^\]]*\]\s*$")
ENTETE_DE_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

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


def _normaliser(chemin: str) -> str:
    """`./tests/` devient `tests` : sans cela, `--tests ./tests` ne reconnaît aucun fichier."""
    return posixpath.normpath(chemin.strip())


def _fichiers_du_rouge(rouge: str) -> set[str]:
    """Chemins touchés par le commit rouge. Un rouge racine n'a pas de parent : on lit alors le
    commit lui-même avec `diff-tree --root`, et non `git show`, qui rend une liste vide pour le
    commit racine quand `log.showRoot=false` (le fichier du rouge disparaîtrait sans bruit)."""
    if _git(["rev-parse", "--verify", "--quiet", f"{rouge}^"]).returncode == 0:
        sortie = _git(["diff", "--name-only", "--no-renames", "-z", f"{rouge}^", rouge])
    else:
        sortie = _git(["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", rouge])
    if sortie.returncode != 0:
        raise RuntimeError(sortie.stderr.strip() or "lecture du commit rouge impossible")
    return {m for m in sortie.stdout.split("\0") if m}


def _est_un_test(chemin: str, tests: list[str] | None, fichiers_du_rouge: set[str]) -> bool:
    if chemin in fichiers_du_rouge:
        return True
    if tests is not None:
        return any(t == "." or chemin == t or chemin.startswith(t + "/") for t in tests)
    parties = chemin.split("/")
    return (any(p in DOSSIERS_DE_TEST for p in parties[:-1])
            or bool(MOTIF_NOM_DE_TEST.match(parties[-1])))


def _est_config_du_lanceur(chemin: str) -> bool:
    nom = chemin.rsplit("/", 1)[-1]
    return nom in CONFIG_LANCEUR or any(fnmatch.fnmatchcase(nom, m) for m in MOTIFS_CONFIG_LANCEUR)


def _est_config_par_section(chemin: str) -> bool:
    return chemin.rsplit("/", 1)[-1] in CONFIG_PAR_SECTION


def _contenu(sha: str, chemin: str) -> list[str]:
    """Lignes du fichier à ce commit ; vide si le fichier n'y existe pas (ajout, suppression)."""
    sortie = _git(["show", f"{sha}:{chemin}"])
    return sortie.stdout.splitlines() if sortie.returncode == 0 else []


def _section_de_test(lignes: list[str], i: int) -> bool:
    """Vrai si la ligne i porte un marqueur de test, ou si l'en-tête de section au-dessus porte un."""
    if not 0 <= i < len(lignes):
        return False
    if any(m in lignes[i] for m in MARQUEURS_SECTION_DE_TEST):
        return True
    for j in range(i, -1, -1):
        if EN_TETE_DE_SECTION.match(lignes[j]):
            return any(m in lignes[j] for m in MARQUEURS_SECTION_DE_TEST)
    return False


def _touche_une_section_de_test(rouge: str, vert: str, chemin: str) -> bool:
    """Vrai si un changement du fichier tombe dans une section de test.

    Le diff sans contexte (`--unified=0`) donne les lignes changées, avec leur position dans
    l'ancien fichier (`-a,b`) et le nouveau (`+c,d`). Chacune est jugée sur sa propre ligne et sur
    l'en-tête de la section qui la contient, lu dans le fichier du commit où la ligne existe. Le
    contexte de diff n'est pas lu : une section de test peut commencer loin au-dessus du changement.
    """
    avant, apres = _contenu(rouge, chemin), _contenu(vert, chemin)
    diff = _git(["diff", "--unified=0", "--no-renames", rouge, vert, "--", chemin]).stdout
    for ligne in diff.splitlines():
        m = ENTETE_DE_HUNK.match(ligne)
        if not m:
            continue
        ancien_debut, ancien_nombre = int(m.group(1)), int(m.group(2) or 1)
        nouveau_debut, nouveau_nombre = int(m.group(3)), int(m.group(4) or 1)
        changees = [(avant, ancien_debut - 1 + k) for k in range(ancien_nombre)]
        changees += [(apres, nouveau_debut - 1 + k) for k in range(nouveau_nombre)]
        if any(_section_de_test(lignes, i) for lignes, i in changees):
            return True
    return False


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
    if tests is not None:
        tests = [_normaliser(t) for t in tests]
    try:
        fichiers_du_rouge = _fichiers_du_rouge(rouge)
        modifies = _fichiers_modifies(rouge, vert)
    except RuntimeError as panne:
        return PANNE, [str(panne)]

    lignes = []
    for statut, chemin in modifies:
        if _est_un_test(chemin, tests, fichiers_du_rouge):
            if statut == "D":
                raisons = ["fichier de test supprimé"]
            elif statut == "A":
                raisons = ["fichier de test ajouté au vert"]
            else:
                raisons = _raisons_de_modification(rouge, vert, chemin)
        elif _est_config_du_lanceur(chemin):
            raisons = ["configuration du lanceur de tests retouchée (aucun fichier de test)"]
        elif _est_config_par_section(chemin) and _touche_une_section_de_test(rouge, vert, chemin):
            raisons = ["configuration du lanceur de tests retouchée dans une section de test"]
        else:
            continue
        lignes.append(f"  {statut} {chemin} — {'; '.join(raisons)}")
    return (TRICHE if lignes else OK), lignes


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(
        description="Vérifie qu'un commit vert ne retouche aucun fichier de test du commit rouge.")
    parseur.add_argument("rouge", help="SHA du commit rouge (tests seuls)")
    parseur.add_argument("vert", help="SHA du commit vert (code)")
    parseur.add_argument("--tests", nargs="+", metavar="CHEMIN",
                         help="fichiers ou dossiers de test, relatifs à la racine du dépôt "
                              "(`./` accepté)")
    args = parseur.parse_args(argv)

    code, lignes = verifier(args.rouge, args.vert, args.tests)
    if code == PANNE:
        print("\n".join(lignes), file=sys.stderr)
        return PANNE
    if code == TRICHE:
        print(f"Fichiers de test ou configuration du lanceur modifiés entre {args.rouge[:12]} "
              f"(rouge) et {args.vert[:12]} (vert) : le vert ne doit en toucher aucun.")
        print("\n".join(lignes))
    else:
        print("Aucun fichier de test ni configuration du lanceur modifié entre le rouge et le vert.")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
