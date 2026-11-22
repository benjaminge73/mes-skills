#!/usr/bin/env python3
"""Jev (TypeSafe System One) : classifieur quasi gratuit, qui rend un choix ou une probabilité, jamais du texte.

Usage en script :
  jev.py aiguillage <.env> <VARIABLE> <sortie.json>   — par cas, quels angles du comité lancer (4 questions oui/non)
  jev.py second-avis <.env> <VARIABLE> <sortie.json>  — chaque remarque du comité, notée « le diff contient-il ce défaut ? »

Mesures du 2026-11-22 (README) : triage des cas AUC 0,65 ; filtre des remarques sans le diff AUC 0,64 ; avec le diff et une
question `noul`, AUC 0,75. La clé se lit dans le fichier .env donné, dans ce seul processus ; elle n'est jamais affichée.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

URL = "https://api.typesafe.ai/v1/systemone"


def cle(env: str, variable: str) -> str:
    for ligne in Path(env).expanduser().read_text().splitlines():
        if ligne.startswith(variable + "="):
            valeur = ligne.split("=", 1)[1].strip().strip('"')
            if valeur:
                return valeur
    sys.exit(f"jev : {variable} absente ou vide dans {env}")


def demander(cle_: str, etat: str, questions: dict, modele: str = "jev-latest") -> dict | None:
    """Les réponses brutes (`answers`) de Jev, ou None si l'appel échoue."""
    req = urllib.request.Request(URL, data=json.dumps({"model": modele, "state": etat, "questions": questions}).encode(),
                                 headers={"Authorization": "Bearer " + cle_, "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=90).read())["answers"]
    except Exception:
        return None


def noul(cle_: str, etat: str, question: str) -> float | None:
    """Probabilité (0 à 1) que la réponse à `question` soit oui. La réponse porte `{"type": "noul", "noul": p}`."""
    r = demander(cle_, etat, {"q": {"type": "noul", "instructions": question}})
    return (r or {}).get("q", {}).get("noul")


PLAUSIBILITE = {"défaut réel": "La remarque décrit un défaut que le diff introduit vraiment, à l'endroit cité.",
                "bruit": "La remarque est vague, hors sujet, contredite par le code ou l'objectif, ou ne relève que du style."}


def plausibilite(cle_: str, objectif: str, diff: str, remarque: str) -> float | None:
    """Probabilité « défaut réel » d'une remarque de relecture. Format retenu le 2026-11-22 sur 145 remarques étiquetées
    (AUC 0,81) : `state` en chaîne avec le diff complet, `choice` à options DÉCRITES. Moins bons : `noul` (0,74), `state`
    en objet à champs nommés (0,74), `score` (0,69), diff réduit aux fichiers cités (0,57). Version figée, pas l'alias."""
    etat = "OBJECTIF :\n" + objectif[:1200] + "\n\nDIFF :\n" + diff[:9000] + "\n\nREMARQUE DE RELECTURE :\n" + remarque
    r = demander(cle_, etat, {"q": {"type": "choice", "instructions": "Que vaut cette remarque de relecture pour ce changement ?",
                                    "criteria": PLAUSIBILITE}}, modele="jev-1.14.0")
    return ((r or {}).get("q", {}).get("probabilities") or {}).get("défaut réel")


ANGLES = {
    "secu": "Ce changement touche-t-il un point de sécurité qui mérite une relecture dédiée : entrée externe, commande shell, chemin, réseau, secret, droits, taille ou mémoire ?",
    "archi": "Ce changement risque-t-il un écart à son objectif, un contrat ou une interface cassée, des appelants ou des docs devenus faux ?",
    "senior": "Ce changement contient-il de la logique où un bug de correction est plausible : cas limites, erreurs, conditions, concurrence, codes de sortie ?",
    "tests": "Ce changement ajoute-t-il ou modifie-t-il des tests ou une preuve dont la pertinence mérite d'être vérifiée ?",
}

if __name__ == "__main__":
    import banc
    mode, env, var, sortie = sys.argv[1:5]
    k_ = cle(env, var)
    entrees = banc.charger("jev-entrees.json")  # {id: {objectif, stat, diff}}
    res = {}
    if mode == "aiguillage":
        for k, v in entrees.items():
            etat = "OBJECTIF :\n" + v["objectif"] + "\n\nFICHIERS :\n" + v["stat"] + "\n\nDIFF (tronqué) :\n" + v["diff"]
            r = demander(k_, etat, {a: {"type": "choice", "instructions": t, "criteria": {"oui": None, "non": None}} for a, t in ANGLES.items()}) or {}
            res[k] = {a: {"choix": r.get(a, {}).get("choice"), "confiance": r.get(a, {}).get("confidence")} for a in ANGLES}
    elif mode == "second-avis":
        for a in ANGLES:
            for r in json.loads((banc.DONNEES / "jugements" / "evaluateur" / f"jugement-comite-{a}.json").read_text())["remarques"]:
                e = entrees[str(r["id_cas"])]
                p = noul(k_, "OBJECTIF :\n" + e["objectif"][:1200] + "\n\nDIFF :\n" + e["diff"][:9000] + "\n\nREMARQUE DE RELECTURE :\n" + r["texte"],
                         "Le changement ci-dessus contient-il réellement le défaut décrit par la remarque de relecture ?")
                res[f"{a}:{r['id_cas']}:{r['n_remarque']}"] = {"label": r["verdict"], "opus": bool(r.get("apparie_opus")), "jev": p}
    else:
        sys.exit("mode : aiguillage | second-avis")
    (banc.DONNEES / sortie).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(mode, len(res), "->", banc.DONNEES / sortie)
