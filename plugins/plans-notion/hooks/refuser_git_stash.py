#!/usr/bin/env python3
"""Hook PreToolUse (Bash) : refuse toute commande ``git stash``, sous aucune forme.

La pile de stash est partagée entre toutes les sessions et tous les worktrees
du poste : un ``pop`` malheureux récupère le travail d'une autre session. Le
hook refuse donc ``git stash`` (``push``, ``pop``, ``apply``, ``list``…), y
compris derrière ``git -C <chemin>``, après un ``&&`` ou sur une ligne suivante.

Le hook lit sur stdin le JSON de Claude Code (``tool_name``, ``tool_input``).
Refus : code 2 et motif sur stderr. Permis : code 0, sans sortie.

Le découpage reprend celui de ``refuser_no_verify.py`` (commande découpée avec
``shlex``, segments séparés par les opérateurs), avec une différence : un saut de
ligne sépare aussi deux commandes, ce que ``shlex`` seul ne fait pas. Au moindre
doute (JSON ou commande illisible), le hook laisse passer plutôt que de bloquer
une session : c'est un garde-fou, pas un pare-feu.
"""
from __future__ import annotations

import json
import shlex
import sys

SEPARATEURS = {"&&", "||", ";", "|", "&", "\n", "(", ")"}
# Options de git qui prennent une valeur dans le mot suivant (git -C dir stash).
OPTIONS_GIT_AVEC_VALEUR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

MOTIF = ("Refusé : `git stash` est interdit sous toutes ses formes. La pile de stash est "
         "partagée entre tous les worktrees et toutes les sessions du poste : un autre "
         "exécutant peut la dépiler et emporter ton travail, ou récupérer le sien à ta place. "
         "Pour mettre du travail de côté, fais un commit WIP (`git commit -m \"WIP: …\"`) ; "
         "pour voir un état antérieur sans toucher au tien, `git worktree add --detach "
         "<tmp> <sha>`.")


def _segments(commande: str) -> list[list[str]]:
    # Le saut de ligne est un séparateur de commandes : il est donc lexé comme
    # ponctuation, et non comme un blanc ignoré par shlex.
    lexer = shlex.shlex(commande, posix=True, punctuation_chars="();&|\n")
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    segments, courant = [], []
    for mot in lexer:
        if mot in SEPARATEURS or (mot and set(mot) <= set("&|;()\n")):
            segments.append(courant)
            courant = []
        else:
            courant.append(mot)
    segments.append(courant)
    return [s for s in segments if s]


def _est_un_git_stash(mots: list[str]) -> bool:
    if not mots or mots[0] != "git":
        return False
    i = 1
    while i < len(mots) and mots[i].startswith("-"):
        i += 2 if mots[i] in OPTIONS_GIT_AVEC_VALEUR else 1
    return i < len(mots) and mots[i] == "stash"


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if donnees.get("tool_name") != "Bash":
            return 0
        commande = donnees["tool_input"]["command"]
        refus = any(_est_un_git_stash(s) for s in _segments(commande))
    except Exception as erreur:  # garde-fou cassé : on ne bloque rien
        print(f"refuser_git_stash : entrée ignorée ({type(erreur).__name__}: {erreur})",
              file=sys.stderr)
        return 0
    if refus:
        print(MOTIF, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
