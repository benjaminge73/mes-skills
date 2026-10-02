#!/usr/bin/env python3
"""Hook PreToolUse (Bash) : refuse un ``git commit`` lancé avec ``--no-verify`` ou ``-n``.

Le hook lit sur stdin le JSON de Claude Code (``tool_name``, ``tool_input``).
Refus : code 2 et motif sur stderr. Permis : code 0, sans sortie.

L'option n'est cherchée que parmi les arguments du ``git commit`` lui-même
(commande découpée avec ``shlex``) : ni le texte d'un message, ni ``git log -n``
ne comptent. C'est un garde-fou, pas un pare-feu : au moindre doute (JSON ou
commande illisible), le hook laisse passer plutôt que de bloquer une session.
"""
from __future__ import annotations

import json
import shlex
import sys

SEPARATEURS = {"&&", "||", ";", "|", "&", "\n", "(", ")"}
# Options de git qui prennent une valeur dans le mot suivant (git -C dir commit).
OPTIONS_GIT_AVEC_VALEUR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
# Options de commit qui prennent une valeur : « -nm "x" » ou « -m -n » (message « -n »).
# -S / --gpg-sign : valeur facultative, collée ou après « = », jamais dans le mot suivant.
COURTES_AVEC_VALEUR = set("mFCc")
LONGUES_AVEC_VALEUR = {"--message", "--file", "--author", "--date", "--reuse-message",
                       "--reedit-message", "--fixup", "--squash", "--template",
                       "--cleanup", "--trailer"}

MOTIF = ("Refusé : `git commit` avec `--no-verify` (ou `-n`) contourne les hooks de "
         "pré-commit. Relance le commit sans cette option ; si un hook échoue, corrige "
         "la cause plutôt que de le sauter.")


def _segments(commande: str) -> list[list[str]]:
    lexer = shlex.shlex(commande, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    segments, courant = [], []
    for mot in lexer:
        if mot in SEPARATEURS or (mot and set(mot) <= set("&|;()")):
            segments.append(courant)
            courant = []
        else:
            courant.append(mot)
    segments.append(courant)
    return [s for s in segments if s]


def _commit_sans_verification(mots: list[str]) -> bool:
    if not mots or mots[0] != "git":
        return False
    i = 1
    while i < len(mots) and mots[i].startswith("-"):
        i += 2 if mots[i] in OPTIONS_GIT_AVEC_VALEUR else 1
    if i >= len(mots) or mots[i] != "commit":
        return False
    args = mots[i + 1:]
    saute = False
    for mot in args:
        if saute:
            saute = False
            continue
        if mot == "--":
            break
        if mot == "--no-verify":
            return True
        if mot.startswith("--"):
            saute = mot in LONGUES_AVEC_VALEUR
        elif mot.startswith("-") and len(mot) > 1:
            for k, lettre in enumerate(mot[1:], start=1):
                if lettre == "n":
                    return True
                if lettre == "S":
                    break  # la suite du mot est le keyid ; le mot suivant n'est pas sa valeur
                if lettre in COURTES_AVEC_VALEUR:
                    saute = k == len(mot) - 1  # valeur dans le mot suivant
                    break
    return False


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if donnees.get("tool_name") != "Bash":
            return 0
        commande = donnees["tool_input"]["command"]
        refus = any(_commit_sans_verification(s) for s in _segments(commande))
    except Exception as erreur:  # garde-fou cassé : on ne bloque rien
        print(f"refuser_no_verify : entrée ignorée ({type(erreur).__name__}: {erreur})",
              file=sys.stderr)
        return 0
    if refus:
        print(MOTIF, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
