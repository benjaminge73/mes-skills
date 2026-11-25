#!/usr/bin/env python3
"""Hook PreToolUse (Bash) : prend le jeton des actions lourdes avant une suite lourde.

Une commande lourde (suite de tests complète, Playwright, ``claude plugin eval``,
``docker run``, ``npm test``…) est réécrite par ``updatedInput`` : elle ne part
plus telle quelle, elle passe par l'enveloppeur ``skills/_partage/scripts/sous-jeton.sh``,
qui prend le jeton de la machine (``etat-machine.py``) puis joue la commande.
Aucune décision de permission n'est posée : la réécriture ne contourne rien.

Une preuve ciblée (un fichier de test, ``-k``, ``::``, ``--version``…), une
commande qui ne lance pas de suite, et une commande qui cite déjà le jeton
(``etat-machine.py``, ``sous-jeton.sh``, ``lancer.sh``) passent sans sortie.

Pour la commande intérieure, ``rtk rewrite`` est appliqué lui-même (délai 2 s) :
Claude Code lance les hooks d'un même événement en parallèle et ne dit pas quel
``updatedInput`` gagne, donc la compression rtk est gardée ici (plan, D7).

Le délai de l'outil Bash : 600000 ms en avant-plan, avec un plafond d'attente de
300 s ; en arrière-plan, le délai de l'appelant reste intact et le plafond est de
1800 s. Le hook ne force pas l'arrière-plan.

Fail-open : toute exception, toute entrée illisible ou tout outil autre que Bash
sort en code 0 sans sortie, et la commande passe telle quelle.
"""
from __future__ import annotations

import importlib.util
import json
import posixpath
import re
import shlex
import subprocess
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
PLUGIN = HOOKS.parent
SOUS_JETON = PLUGIN / "skills" / "_partage" / "scripts" / "sous-jeton.sh"
ETAT_MACHINE = PLUGIN / "skills" / "_partage" / "scripts" / "etat-machine.py"

DELAI_AVANT_PLAN_MS = 600000
ATTENTE_AVANT_PLAN_S = 300
ATTENTE_ARRIERE_PLAN_S = 1800

# Mots de tête qui précèdent le programme sans le changer : on les saute.
TETES = {"command", "env", "time", "nohup", "exec", "sudo", "rtk", "npx", "xvfb-run",
         "nice", "then", "do", "else", "{", "!"}
# Options de tête qui prennent une valeur dans le mot suivant (nice -n 5, timeout -s KILL).
OPTIONS_TETE_AVEC_VALEUR = {"-n", "-s", "-k", "--signal", "--kill-after"}
AFFECTATION = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
DUREE = re.compile(r"\d+(\.\d+)?[smhd]?$")

# Options de pytest et de jest dont le mot suivant est une valeur, pas une cible.
OPTIONS_AVEC_VALEUR = {"-c", "--config", "--ignore", "--deselect", "--rootdir",
                       "-n", "-p", "-m", "-o", "-r", "-W", "--tb", "--maxfail",
                       "--junitxml", "--durations", "--basetemp",
                       "--reporter", "--project"}  # vitest
# Caractères d'un opérateur de redirection (« 2>&1 » est lexé « 2 », « >& », « 1 »).
CARACTERES_REDIRECTION = set("<>&")
# Sous-commande de vitest (« vitest run fichier ») : ce n'est pas une cible.
SOUS_COMMANDES = {"run"}
# Options d'information : rien ne tourne, la commande est libre.
OPTIONS_INFORMATION = {"--version", "--help", "-h", "--collect-only", "--co"}
# Options de filtrage par nom de test : une preuve ciblée, donc libre.
OPTIONS_FILTRE = {"-k", "-t", "--testNamePattern"}
EXTENSIONS_FICHIER_TEST = (".py", ".ts", ".tsx", ".js", ".mjs")
# Une commande qui cite l'un de ces noms est déjà sous jeton, ou la prend elle-même.
DEJA_SOUS_JETON = ("etat-machine.py", "sous-jeton.sh", "lancer.sh")


def _charger(nom: str, chemin: Path):
    """Module chargé depuis son fichier ; le nom du module ne sert qu'à l'import."""
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _programme(mots: list[str]) -> list[str]:
    """Les mots à partir du programme lui-même, après les têtes qui ne le changent pas."""
    i = 0
    while i < len(mots):
        m = mots[i]
        if m == "timeout":
            i += 1
            while i < len(mots) and mots[i].startswith("-"):
                i += 2 if mots[i] in OPTIONS_TETE_AVEC_VALEUR else 1
            if i < len(mots) and DUREE.match(mots[i]):
                i += 1
        elif m == "uv" and i + 1 < len(mots) and mots[i + 1] == "run":
            i += 2
        elif m == "pnpm" and i + 1 < len(mots) and mots[i + 1] == "exec":
            # Seul « pnpm exec » est sauté : « pnpm run test » nomme le script lancé.
            i += 2
        elif m.startswith("-") and m != "-":
            i += 2 if m in OPTIONS_TETE_AVEC_VALEUR else 1
        elif AFFECTATION.match(m) or m in TETES:
            i += 1
        else:
            break
    return mots[i:]


def _sans_redirections(mots: list[str]) -> list[str]:
    """Les mots sans les redirections : l'opérateur, sa cible, et le numéro de fd qui le précède."""
    gardes = []
    i = 0
    while i < len(mots):
        m = mots[i]
        if m and set(m) <= CARACTERES_REDIRECTION:
            i += 2  # l'opérateur (« > », « 2>&1 » lexé « >& ») et le mot qui le suit
            continue
        if m.isdigit() and i + 1 < len(mots) and mots[i + 1] \
                and set(mots[i + 1]) <= CARACTERES_REDIRECTION:
            i += 1  # le fd (« 2 ») : l'opérateur qui suit est traité au tour suivant
            continue
        gardes.append(m)
        i += 1
    return gardes


def _cibles(args: list[str]) -> list[str]:
    """Les mots qui désignent ce que la suite lance : ni options, ni valeurs d'option, ni sous-commande."""
    positionnels = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in OPTIONS_AVEC_VALEUR:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        positionnels.append(a)
        i += 1
    if positionnels and positionnels[0] in SOUS_COMMANDES:
        positionnels = positionnels[1:]
    return positionnels


def _preuve_ciblee(args: list[str]) -> bool:
    """Vrai si la suite n'est lancée que sur des fichiers, ou une option d'information.

    Une cible qui n'est ni un fichier de test (extension, ou ``::``) ni une option est
    un dossier : la suite entière part, même avec un fichier à côté.
    """
    if any(a in OPTIONS_INFORMATION or a in OPTIONS_FILTRE or a.startswith("--testNamePattern=")
           for a in args):
        return True
    cibles = _cibles(args)
    return bool(cibles) and all("::" in c or c.endswith(EXTENSIONS_FICHIER_TEST) for c in cibles)


def _commande_lourde(argv: list[str], etat) -> bool:
    """Une commande jugée sur son programme et ses arguments, sans gestionnaire de paquets."""
    famille = etat.familles_de(argv)
    if etat.CLAUDE_PLUGIN_EVAL in famille:
        return True
    if etat.SUITE_DE_TESTS in famille:
        return not _preuve_ciblee(argv[1:])
    return False


def _segment_lourd(mots: list[str], etat) -> bool:
    argv = _programme(_sans_redirections(mots))
    if not argv:
        return False
    prog = posixpath.basename(argv[0])
    args = argv[1:]
    if prog == "docker":
        return args[:1] == ["run"]
    if prog in ("npm", "pnpm", "yarn", "bun"):
        # « test », ou le raccourci sans « run » (« pnpm test:unit », « yarn e2e »).
        if args[:1] == ["test"] or (args and args[0].startswith(("test:", "e2e"))):
            return True
        if args[:1] == ["run"]:
            # « run <script> » : lourd si le script est une suite, sinon (build…) libre.
            return len(args) > 1 and args[1].startswith(("test", "e2e"))
        # Sinon les arguments sont la commande lancée (« pnpm vitest run… ») ; install, add : libres.
        return _commande_lourde(args, etat)
    if prog == "playwright":
        # Playwright est lourd dès qu'on lance ses tests, même sur un seul fichier.
        return args[:1] == ["test"]
    return _commande_lourde(argv, etat)


def _lourde(commande: str, garde, etat) -> bool:
    if any(nom in commande for nom in DEJA_SOUS_JETON):
        return False
    segments = garde._segments(garde._sans_corps_de_heredoc(commande))
    return any(_segment_lourd(s, etat) for s in segments)


def _commande_interieure(commande: str) -> str:
    """La commande jouée sous jeton : sa réécriture rtk si rtk en rend une, sinon l'original."""
    try:
        r = subprocess.run(["rtk", "rewrite", commande], capture_output=True, text=True,
                           timeout=2)
    except (OSError, subprocess.SubprocessError):
        return commande
    sortie = r.stdout.rstrip("\n")
    if sortie.strip() and r.returncode in (0, 3):
        return sortie
    return commande


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if donnees.get("tool_name") != "Bash":
            return 0
        entree = donnees["tool_input"]
        commande = entree["command"]
        if not isinstance(commande, str):
            return 0
        garde = _charger("refuser_git_stash", HOOKS / "refuser_git_stash.py")
        etat = _charger("etat_machine", ETAT_MACHINE)
        if not _lourde(commande, garde, etat):
            return 0
        interieur = _commande_interieure(commande)
        maj = dict(entree)
        if bool(entree.get("run_in_background")):
            attente = ATTENTE_ARRIERE_PLAN_S  # le délai de l'appelant reste intact
        else:
            attente = ATTENTE_AVANT_PLAN_S
            maj["timeout"] = DELAI_AVANT_PLAN_MS
        maj["command"] = (f"PLANS_NOTION_ATTENTE_MAX={attente} bash "
                          f"{shlex.quote(str(SOUS_JETON))} {shlex.quote(interieur)}")
        sortie = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": maj}}
        print(json.dumps(sortie, ensure_ascii=False))
        return 0
    except Exception as erreur:  # garde-fou cassé : on ne bloque rien
        print(f"jeton_lourd : entrée ignorée ({type(erreur).__name__}: {erreur})",
              file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
