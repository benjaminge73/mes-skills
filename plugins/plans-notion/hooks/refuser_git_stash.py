#!/usr/bin/env python3
"""Hook PreToolUse (Bash) : refuse toute commande ``git stash``, sous aucune forme.

La pile de stash est partagée entre toutes les sessions et tous les worktrees
du poste : un ``pop`` malheureux récupère le travail d'une autre session. Le
hook refuse donc ``git stash`` (``push``, ``pop``, ``apply``, ``list``…), y
compris derrière ``git -C <chemin>``, après un ``&&``, sur une ligne suivante,
et derrière un mot de tête qui ne change pas la commande : chemin absolu
(``/usr/bin/git``), affectation (``GIT_DIR=x``), ``command``, ``env``, ``sudo``,
``time``, ``nohup``, ``exec``, ``xargs``, ``then``, ``do``, ``else``, ``{``, ``!``.

Le hook lit sur stdin le JSON de Claude Code (``tool_name``, ``tool_input``).
Refus : code 2 et motif sur stderr. Permis : code 0, sans sortie.

Le découpage reprend celui de ``refuser_no_verify.py`` (commande découpée avec
``shlex``, segments séparés par les opérateurs), avec deux différences. Un saut
de ligne sépare aussi deux commandes, ce que ``shlex`` seul ne fait pas. Et le
corps d'un heredoc (``<<MOT`` … ligne ``MOT``, ``<<-MOT`` admis avec tabulations
de tête) n'est pas lu comme une commande : c'est du texte, un fichier ou un message.

Limites, écrites ici parce que c'est un garde-fou, pas un pare-feu :
- non vu : un contournement par ``bash -c "git stash"``, ``eval``, un alias,
  une fonction du shell, ou une option qui prend une valeur après un préfixe
  (``sudo -u root git stash``) ;
- un heredoc jamais terminé avale le reste du texte : rien n'est refusé après lui ;
- au moindre doute (JSON ou commande illisible), le hook laisse passer plutôt que
  de bloquer une session.
"""
from __future__ import annotations

import json
import posixpath
import re
import shlex
import sys

SEPARATEURS = {"&&", "||", ";", "|", "&", "\n", "(", ")"}
# Options de git qui prennent une valeur dans le mot suivant (git -C dir stash).
OPTIONS_GIT_AVEC_VALEUR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
# Mots de tête qui précèdent la vraie commande sans la changer : on les saute.
PREFIXES = {"command", "env", "sudo", "time", "nohup", "exec", "xargs",
            "then", "do", "else", "{", "!"}
AFFECTATION = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
# « <<MOT », « <<-MOT », « <<'MOT' », « <<"MOT" » : le mot est le terminateur du corps.
DEBUT_HEREDOC = re.compile(r"<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")

MOTIF = ("Refusé : `git stash` est interdit sous toutes ses formes. La pile de stash est "
         "partagée entre tous les worktrees et toutes les sessions du poste : un autre "
         "exécutant peut la dépiler et emporter ton travail, ou récupérer le sien à ta place. "
         "Pour mettre du travail de côté, fais un commit WIP (`git commit -m \"WIP: …\"`) ; "
         "pour voir un état antérieur sans toucher au tien, `git worktree add --detach "
         "<tmp> <sha>`.")


def _heredocs_ouverts(ligne: str, etat: dict) -> list[tuple[str, bool]]:
    """Heredocs ouverts par la ligne, hors guillemets et hors commentaire.

    Rend ``(terminateur, tirets)`` dans l'ordre. ``etat`` porte l'état des
    guillemets d'une ligne à l'autre, car un message peut couvrir plusieurs lignes.
    """
    ouverts = []
    j = 0
    while j < len(ligne):
        c = ligne[j]
        if etat["simple"]:
            etat["simple"] = c != "'"
            j += 1
        elif c == "\\":
            j += 2
        elif etat["double"]:
            etat["double"] = c != '"'
            j += 1
        elif c == "#" and (j == 0 or ligne[j - 1] in " \t;&|("):
            break  # commentaire : le reste de la ligne n'ouvre rien
        elif c == "'":
            etat["simple"] = True
            j += 1
        elif c == '"':
            etat["double"] = True
            j += 1
        elif ligne.startswith("<<<", j):  # here-string, pas un heredoc
            j += 3
        elif ligne.startswith("<<", j):
            m = DEBUT_HEREDOC.match(ligne, j)
            if m:
                ouverts.append((m.group(3), m.group(1) == "-"))
                j = m.end()
            else:
                j += 2
        else:
            j += 1
    return ouverts


def _sans_corps_de_heredoc(commande: str) -> str:
    """Commande sans les lignes de corps de heredoc (la ligne d'ouverture reste)."""
    lignes = commande.split("\n")
    gardees = []
    etat = {"simple": False, "double": False}
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        gardees.append(ligne)
        i += 1
        for terminateur, tirets in _heredocs_ouverts(ligne, etat):
            while i < len(lignes):
                corps = lignes[i]
                i += 1
                if (corps.lstrip("\t") if tirets else corps) == terminateur:
                    break
    return "\n".join(gardees)


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


def _index_de_la_commande(mots: list[str]) -> int:
    """Index du premier mot qui n'est ni un préfixe, ni une affectation, ni une option."""
    i = 0
    while i < len(mots) and (mots[i] in PREFIXES or mots[i].startswith("-")
                             or AFFECTATION.match(mots[i])):
        i += 1
    return i


def _est_un_git_stash(mots: list[str]) -> bool:
    i = _index_de_la_commande(mots)
    # Le nom de base compte : « /usr/bin/git » est git.
    if i >= len(mots) or posixpath.basename(mots[i]) != "git":
        return False
    i += 1
    while i < len(mots) and mots[i].startswith("-"):
        i += 2 if mots[i] in OPTIONS_GIT_AVEC_VALEUR else 1
    return i < len(mots) and mots[i] == "stash"


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if donnees.get("tool_name") != "Bash":
            return 0
        commande = donnees["tool_input"]["command"]
        refus = any(_est_un_git_stash(s) for s in _segments(_sans_corps_de_heredoc(commande)))
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
