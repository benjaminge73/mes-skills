#!/usr/bin/env python3
"""Hook SessionStart : retire le worktree d'un plan fini, et rien d'autre.

Pour chaque fiche locale (``plan-en-cours.py``) à l'état ``a merger`` qui porte
une PR et un worktree, le worktree n'est retiré que si les preuves tiennent,
dans cet ordre :

0. la session de la fiche n'est plus vivante : aucun fichier
   ``<pid>.json`` du dossier de sessions ne porte son ``sessionId`` avec un pid
   qui existe encore. Dans le doute (fichier illisible, pid absent), elle est
   vivante ;
1. le worktree existe, la branche locale a un SHA, et la session qui démarre
   ne se trouve pas dans ce worktree ;
2. ``HEAD`` du worktree est la branche (``git symbolic-ref HEAD``) et pointe
   sur le SHA de la branche locale : un worktree détaché ou en avance n'est
   jamais retiré ;
3. l'arbre du worktree est propre (``git status --porcelain`` vide) ;
4. ``gh pr view`` rend la PR ``MERGED`` ;
5. son ``headRefOid`` égale le SHA de la branche locale : aucun commit n'a été
   ajouté après le merge (c'est la règle du hook de démarrage du VPS).

Retrait : ``git worktree remove`` sans ``--force``, puis fiche à ``clos``. La
branche n'est jamais supprimée : le balayeur du VPS s'en charge une fois le
worktree parti. Tout autre cas ne touche à rien et le dit en une ligne.

Contrat : code 0 toujours. La sortie entre dans le contexte de la session : une
ligne par plan concerné, aucune ligne sinon. Le hook est synchrone, et ``gh``
est appelé avec un délai borné ; une erreur laisse le worktree en place.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DELAI_GH = 15
DELAI_GIT = 15
ETAT_A_MERGER = "a merger"
DEPOT = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def _charger_fiches():
    """``plan-en-cours.py``, chargé depuis le plugin : même dossier, même verrou, même écriture."""
    chemin = Path(__file__).resolve().parents[1] / "skills" / "_partage" / "scripts" / "plan-en-cours.py"
    spec = importlib.util.spec_from_file_location("plan_en_cours", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["plan_en_cours"] = module  # requis par dataclasses, qui relit le module par son nom
    spec.loader.exec_module(module)
    return module


def repertoire_sessions(env, home: Path) -> Path:
    """``~/.claude/sessions``, comme ``plan-en-cours.py`` ; ``PLANS_NOTION_SESSIONS_DIR`` le surcharge pour les tests."""
    return Path(env.get("PLANS_NOTION_SESSIONS_DIR") or home / ".claude" / "sessions")


def _pid_vivant(pid) -> bool:
    """Vrai si le processus existe. Un pid absent ou invalide compte pour vivant : dans le doute."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid < 1:
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (OSError, OverflowError):
        # Le processus existe mais n'est pas à nous (PermissionError), ou l'appel échoue : vivant.
        return True
    return True


def session_vivante(cle: str, sessions: Path) -> bool:
    """Vrai si une session locale porte l'identifiant ``cle`` et que son processus tourne encore.

    Lit les ``<pid>.json`` du dossier de sessions de Claude Code (champs ``sessionId``
    et ``pid``). Dans le doute, vrai : un dossier illisible est vivant ; un fichier
    illisible est vivant si le pid de son nom tourne encore, ou si son nom n'est pas
    un pid ; un fichier dont le ``sessionId`` est la clé, sans ``pid`` lisible, est
    vivant.
    """
    if not sessions.exists():
        return False
    if not sessions.is_dir():
        return True
    try:
        fichiers = sorted(sessions.glob("*.json"))
    except OSError:
        return True
    for fichier in fichiers:
        try:
            donnees = json.loads(fichier.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            donnees = None
        if not isinstance(donnees, dict):
            # Illisible : on ne sait pas à quelle session il appartient. Son pid, dans le nom, fait foi.
            pid_du_nom = int(fichier.stem) if fichier.stem.isdigit() else None
            if _pid_vivant(pid_du_nom):
                return True
            continue
        if donnees.get("sessionId") == cle and _pid_vivant(donnees.get("pid")):
            return True
    return False


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=DELAI_GIT)
    except (OSError, subprocess.SubprocessError):
        return None


def _pr(depot: str, numero: int) -> dict | None:
    """État de la PR selon ``gh``, ou ``None`` si ``gh`` ne répond pas proprement."""
    try:
        r = subprocess.run(["gh", "pr", "view", str(numero), "--repo", depot, "--json", "state,headRefOid"],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=DELAI_GH)
        if r.returncode != 0:
            return None
        donnees = json.loads(r.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return donnees if isinstance(donnees, dict) else None


def _clore(fiche: dict) -> dict:
    fiche["etat"] = "clos"
    fiche["raison_attente"] = None
    return fiche


def traiter(module, fiche: dict, cwd_session: Path, dossier: Path, cle: str, sessions: Path) -> str:
    """Retire le worktree si les preuves tiennent et clôt la fiche ; sinon rend la raison, en une ligne."""
    titre = " ".join(str(fiche.get("titre") or "sans titre").split())
    numero = fiche["pr"]
    etiquette = f"plan « {titre} » (PR {numero})"

    def conserve(raison: str) -> str:
        return f"{etiquette} : worktree conservé, {raison}."

    if session_vivante(cle, sessions):
        # Une autre session démarre, mais celle de la fiche tourne encore : son worktree est à elle.
        return conserve("session de la fiche encore vivante")
    worktree = Path(fiche["worktree"]).resolve()
    if not worktree.is_dir():
        return conserve("worktree absent du disque")
    if worktree in (cwd_session, *cwd_session.parents):
        return conserve("worktree de la session courante")
    branche = fiche.get("branche")
    if not isinstance(branche, str) or not branche or branche.startswith("-"):
        return conserve("branche illisible")
    local = _git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branche}"], worktree)
    if local is None or local.returncode != 0 or not local.stdout.strip():
        return conserve("branche locale introuvable")
    sha_local = local.stdout.strip()
    # Le SHA de la branche ne suffit pas : un `git checkout --detach` suivi d'un commit
    # laisse la branche au SHA du merge, l'arbre propre, et le commit serait perdu au retrait.
    tete_sur_branche = _git(["symbolic-ref", "--quiet", "HEAD"], worktree)
    if tete_sur_branche is None or tete_sur_branche.returncode != 0 \
            or tete_sur_branche.stdout.strip() != f"refs/heads/{branche}":
        return conserve("HEAD détaché ou sur une autre branche")
    tete = _git(["rev-parse", "--verify", "--quiet", "HEAD"], worktree)
    if tete is None or tete.returncode != 0 or tete.stdout.strip() != sha_local:
        return conserve("HEAD du worktree illisible ou différent de la branche")
    propre = _git(["status", "--porcelain"], worktree)
    if propre is None or propre.returncode != 0:
        return conserve("arbre illisible")
    if propre.stdout.strip():
        return conserve("arbre non propre")
    depot = fiche.get("depot")
    if not isinstance(depot, str) or not DEPOT.match(depot):
        return conserve("dépôt illisible")
    pr = _pr(depot, numero)
    if pr is None:
        return conserve("gh n'a pas rendu l'état de la PR")
    if pr.get("state") != "MERGED":
        return conserve(f"PR non mergée (état {pr.get('state')})")
    if pr.get("headRefOid") != sha_local:
        return conserve("commit local ajouté après le merge")
    commun = _git(["rev-parse", "--path-format=absolute", "--git-common-dir"], worktree)
    if commun is None or commun.returncode != 0 or not commun.stdout.strip():
        return conserve("dépôt principal introuvable")
    retrait = _git(["worktree", "remove", str(worktree)], Path(commun.stdout.strip()))
    if retrait is None or retrait.returncode != 0:
        return conserve("git worktree remove a refusé")
    module._modifier(dossier, cle, _clore)
    return f"{etiquette} : worktree retiré, fiche close."


def main() -> int:
    try:
        entree = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        entree = {}
    if not isinstance(entree, dict):
        entree = {}
    try:
        module = _charger_fiches()
        dossier = module.dossier_fiches(os.environ)
        if not dossier.is_dir():
            return 0
        cwd_session = Path(entree.get("cwd") or os.getcwd()).resolve()
        sessions = repertoire_sessions(os.environ, Path(os.path.expanduser("~")))
    except Exception:
        return 0
    for chemin in sorted(dossier.glob("*.json")):
        try:
            fiche = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(fiche, dict) or fiche.get("etat") != ETAT_A_MERGER:
            continue
        if not isinstance(fiche.get("pr"), int) or not isinstance(fiche.get("worktree"), str):
            continue
        try:
            ligne = traiter(module, fiche, cwd_session, dossier, chemin.stem, sessions)
        except Exception:
            # Une erreur peut venir après le retrait : on ne prétend pas que rien n'a bougé.
            ligne = f"plan « {fiche.get('titre', 'sans titre')} » : erreur pendant le contrôle, à vérifier à la main."
        print(ligne)
    return 0


if __name__ == "__main__":
    sys.exit(main())
