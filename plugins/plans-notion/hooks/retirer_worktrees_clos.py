#!/usr/bin/env python3
"""Hook SessionStart : retire le worktree d'un plan fini, et rien d'autre.

Pour chaque fiche locale (``plan-en-cours.py``) à l'état ``a merger`` qui porte
une PR et un worktree, le worktree n'est retiré que si les quatre preuves
tiennent, dans cet ordre :

1. le worktree existe, la branche locale a un SHA, et la session qui démarre
   ne se trouve pas dans ce worktree ;
2. l'arbre du worktree est propre (``git status --porcelain`` vide) ;
3. ``gh pr view`` rend la PR ``MERGED`` ;
4. son ``headRefOid`` égale le SHA de la branche locale : aucun commit n'a été
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


def traiter(module, fiche: dict, cwd_session: Path, dossier: Path, cle: str) -> str:
    """Retire le worktree si les preuves tiennent et clôt la fiche ; sinon rend la raison, en une ligne."""
    titre = " ".join(str(fiche.get("titre") or "sans titre").split())
    numero = fiche["pr"]
    etiquette = f"plan « {titre} » (PR {numero})"

    def conserve(raison: str) -> str:
        return f"{etiquette} : worktree conservé, {raison}."

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
            ligne = traiter(module, fiche, cwd_session, dossier, chemin.stem)
        except Exception:
            # Une erreur peut venir après le retrait : on ne prétend pas que rien n'a bougé.
            ligne = f"plan « {fiche.get('titre', 'sans titre')} » : erreur pendant le contrôle, à vérifier à la main."
        print(ligne)
    return 0


if __name__ == "__main__":
    sys.exit(main())
