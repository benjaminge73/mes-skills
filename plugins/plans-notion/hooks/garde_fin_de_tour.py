#!/usr/bin/env python3
"""Hook Stop : retient la fin de tour d'une session qui porte un plan en cours.

Le hook reçoit sur stdin le JSON de Claude Code : ``session_id`` (identifiant
local, celui qui nomme la fiche), ``stop_hook_active``, ``background_tasks`` et
``session_crons``. Il lit la fiche locale de la session, écrite par
``plan-en-cours.py``, et décide sans réseau ni modèle :

- ``en cours``, sans tâche de fond ni réveil programmé, et ``relances`` sous le
  seuil : retenue, et ``relances`` +1 dans la fiche (Q3 : trois relances sans
  étape nouvelle, puis le hook se tait pour que Hal regarde) ;
- ``a merger``, sans réveil programmé ni sonnette : retenue, avec la consigne
  d'armer un réveil toutes les 15 minutes (Q12, « lis ta boîte ») ;
- tout le reste, dont une fiche absente, illisible ou close : laissé passer.

Une retenue n'a lieu qu'à ``stop_hook_active`` faux. Une session relancée par
une retenue passe la fin de tour suivante, sinon la boucle ne s'arrête jamais.

Contrat : sortie vide et code 0 = laisser passer ; sortie
``{"decision": "block", "reason": ...}`` et code 0 = retenir. Une erreur, à
n'importe quelle étape, laisse passer : un garde cassé ne bloque aucune session.
La relance est écrite avant la retenue : si l'écriture échoue, on ne retient pas.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

SEUIL_RELANCES = 3
ETAT_EN_COURS = "en cours"
ETAT_A_MERGER = "a merger"

CONSIGNE_CONTINUER = "Le plan n'est pas fini : continue l'étape suivante du plan."
CONSIGNE_ARMER = ("Le plan attend son merge et aucun réveil n'est armé : arme un réveil "
                  "toutes les 15 minutes (« lis ta boîte ») pour être prévenu du merge.")


def _charger_fiches():
    """``plan-en-cours.py``, chargé depuis le plugin : même dossier, même verrou, même écriture."""
    chemin = Path(__file__).resolve().parents[1] / "skills" / "_partage" / "scripts" / "plan-en-cours.py"
    spec = importlib.util.spec_from_file_location("plan_en_cours", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["plan_en_cours"] = module  # requis par dataclasses, qui relit le module par son nom
    spec.loader.exec_module(module)
    return module


def decider(fiche: dict, entree: dict) -> str | None:
    """``"continuer"``, ``"armer"`` ou ``None`` (laisser passer). Ne lit ni n'écrit rien."""
    reveil = bool(entree.get("session_crons"))
    etat = fiche.get("etat")
    if etat == ETAT_EN_COURS:
        if entree.get("background_tasks") or reveil:
            return None
        if int(fiche.get("relances") or 0) >= SEUIL_RELANCES:
            return None
        return "continuer"
    if etat == ETAT_A_MERGER:
        if reveil or fiche.get("sonnette"):
            return None
        return "armer"
    return None


def _compter_relance(fiche: dict) -> dict:
    fiche["relances"] = int(fiche.get("relances") or 0) + 1
    return fiche


def main() -> int:
    try:
        entree = json.loads(sys.stdin.read())
        if not isinstance(entree, dict) or entree.get("stop_hook_active"):
            return 0
        session = entree.get("session_id")
        module = _charger_fiches()
        if not isinstance(session, str) or not module.FORME_IDENTIFIANT.match(session):
            return 0
        dossier = module.dossier_fiches(os.environ)
        if not (dossier / f"{session}.json").is_file():
            return 0
        fiche = module._lire_fiche(dossier / f"{session}.json")
        if not isinstance(fiche, dict):
            return 0
        decision = decider(fiche, entree)
        if decision is None:
            return 0
        if decision == "continuer":
            module._modifier(dossier, session, _compter_relance)
            consigne = CONSIGNE_CONTINUER
        else:
            consigne = CONSIGNE_ARMER
        sys.stdout.write(json.dumps({"decision": "block", "reason": consigne}, ensure_ascii=False))
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
