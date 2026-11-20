#!/usr/bin/env python3
"""Fraîcheur de la copie locale : le dépôt de travail est-il à jour de sa branche principale ?

Pourquoi un script : une copie locale en retard fait écrire un plan, ouvrir un worktree ou
une PR sur du code périmé, et le conflit n'apparaît qu'à la CI. Le script fait les gestes
de ``fraicheur-du-depot.md`` : détecter la branche principale distante (``main``, ``master``…),
la relever (``git fetch``), compter le retard, et, avec ``--appliquer``, remettre la copie à
jour (``merge --ff-only`` sur la branche principale, ``rebase`` sur une branche de travail).

Usage : fraicheur-depot.py [--depot <dossier>] [--remote origin] [--appliquer]

Sans ``--appliquer`` le script ne change rien (il relève seulement : ``git fetch`` met à jour
la référence distante, jamais l'arbre de travail). Il ne stashe jamais, ne pousse jamais, et
rend l'arbre comme il l'a trouvé quand un rebase échoue (``rebase --abort``).

Codes : 0 à jour (ou remis à jour par ``--appliquer``) ; 1 en retard et rien appliqué ;
2 illisible (pas un dépôt git, remote ou branche principale introuvables) ; 3 arrêt qui
demande un humain : modifications non commitées qui empêchent la remise à jour, ou conflit
de rebase (rebase abandonné, fichiers cités) ; 4 réseau : le ``git fetch`` a échoué, la
fraîcheur n'est PAS vérifiée (le script compare quand même à la dernière référence connue,
dite périmée). La sortie dit toujours en une ligne l'état, et, si la branche était déjà
poussée et vient d'être rebasée, la commande ``git push --force-with-lease`` à jouer (le
script ne la joue pas).
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def git(depot, *args, delai=60):
    return subprocess.run(
        ["git", "-C", depot, *args], capture_output=True, text=True, timeout=delai
    )


def principale(depot, remote):
    """Nom court de la branche principale du remote, ou None."""
    r = git(depot, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip().split("/", 1)[1]
    r = git(depot, "remote", "show", remote, delai=30)  # réseau : dernier recours
    for ligne in r.stdout.splitlines():
        if "HEAD branch" in ligne:
            nom = ligne.split(":", 1)[1].strip()
            if nom and nom != "(unknown)":
                return nom
    for nom in ("main", "master"):
        if git(depot, "rev-parse", "--verify", "--quiet", f"refs/remotes/{remote}/{nom}").returncode == 0:
            return nom
    return None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--depot", default=".")
    p.add_argument("--remote", default="origin")
    p.add_argument("--appliquer", action="store_true")
    a = p.parse_args(argv)
    depot, remote = a.depot, a.remote

    if git(depot, "rev-parse", "--git-dir").returncode != 0:
        print(f"Illisible : « {depot} » n'est pas un dépôt git.")
        return 2
    if git(depot, "remote", "get-url", remote).returncode != 0:
        print(f"Illisible : pas de remote « {remote} ».")
        return 2
    base = principale(depot, remote)
    if base is None:
        print(f"Illisible : branche principale de « {remote} » introuvable (ni HEAD distant, ni main, ni master).")
        return 2
    ref = f"{remote}/{base}"

    reseau = True
    try:
        reseau = git(depot, "fetch", "--quiet", remote, base, delai=90).returncode == 0
    except subprocess.TimeoutExpired:
        reseau = False
    if git(depot, "rev-parse", "--verify", "--quiet", f"refs/remotes/{ref}").returncode != 0:
        print(f"Illisible : « {ref} » n'existe pas dans ce clone et le fetch a échoué.")
        return 2

    branche = git(depot, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    en_retard = int(git(depot, "rev-list", "--count", f"HEAD..{ref}").stdout.strip() or 0)
    propres = int(git(depot, "rev-list", "--count", f"{ref}..HEAD").stdout.strip() or 0)
    sale = bool(git(depot, "status", "--porcelain", "--untracked-files=no").stdout.strip())
    perime = "" if reseau else " ⚠ réseau indisponible : fetch échoué, comparaison à la dernière référence connue (périmée), fraîcheur NON vérifiée."

    if en_retard == 0:
        print(f"À jour : « {branche} » contient déjà {ref}.{perime}")
        return 0 if reseau else 4
    etat = f"En retard : « {branche} » a {en_retard} commit(s) de moins que {ref} ({propres} à elle)."
    if not reseau:
        print(etat + perime)
        return 4
    if not a.appliquer:
        print(etat + " Rien appliqué (relancer avec --appliquer).")
        return 1
    if sale:
        fichiers = git(depot, "status", "--porcelain", "--untracked-files=no").stdout.rstrip()
        print(etat + "\nArrêt : modifications non commitées, remise à jour impossible sans les perdre ni les stasher.\n" + fichiers)
        print("Les commiter (ou les écarter sur ordre de Benjamin), puis relancer.")
        return 3

    # Déjà poussée : la branche a un amont et celui-ci porte tout ce qu'elle porte (rebaser le réécrit).
    pousse = (
        git(depot, "rev-parse", "--verify", "--quiet", "@{upstream}").returncode == 0
        and git(depot, "rev-list", "--count", "@{upstream}..HEAD").stdout.strip() == "0"
        and propres > 0
    )

    if branche == base:
        r = git(depot, "merge", "--ff-only", ref)
        if r.returncode != 0:
            print(etat + "\nArrêt : la branche principale locale a divergé de " + ref + " (fast-forward impossible).\n" + r.stderr.strip())
            return 3
        print(f"Remise à jour : « {branche} » avancée sur {ref} (fast-forward, {en_retard} commit(s)).")
        return 0

    r = git(depot, "rebase", ref, delai=300)
    if r.returncode != 0:
        conflits = git(depot, "diff", "--name-only", "--diff-filter=U").stdout.split()
        git(depot, "rebase", "--abort")
        print(etat + "\nArrêt : conflit de rebase sur " + ", ".join(conflits or ["(fichiers non lus)"]) +
              ". Rebase abandonné, la branche est revenue comme avant. À résoudre à la main ou à poser à Benjamin.")
        return 3
    msg = f"Remise à jour : « {branche} » rebasée sur {ref} ({en_retard} commit(s) repris)."
    if pousse:
        msg += f"\nLa branche était déjà poussée : l'historique a changé, à pousser avec `git push --force-with-lease {remote} {branche}` (jamais --force)."
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
