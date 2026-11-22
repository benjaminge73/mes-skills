#!/usr/bin/env python3
"""Rejoue un bras de relecture sur le jeu de cas : la consigne `relecteur.md` du dépôt, le brief d'origine, un worktree
détaché au commit relu, et un modèle / effort / ajout de consigne au choix.

Usage :
  rejouer.py <bras> <modele> <effort|-> <plafond_dollars> [--cas echantillon.json] [--ajout checklist.txt]
             [--angle secu|archi|senior|tests] [--notes notes.json] [--par 6]

Sorties : $BANC_DONNEES/sorties/<bras>/<id>.json (sortie JSON de `claude -p`, dont `result` et `total_cost_usd`).
Un cas déjà rejoué est sauté : on relance un bras interrompu sans rien repayer.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import threading

import banc

ap = argparse.ArgumentParser()
ap.add_argument("bras"); ap.add_argument("modele"); ap.add_argument("effort"); ap.add_argument("plafond", type=float)
ap.add_argument("--cas", default="echantillon.json", help="fichier de cas, dans $BANC_DONNEES")
ap.add_argument("--ajout", help="texte ajouté au brief (ex. checklist.txt, à côté de ce script)")
ap.add_argument("--angle", help="clé de angles.json ajoutée au brief (comité)")
ap.add_argument("--notes", help="JSON {id: texte} ajouté au brief cas par cas (2e passe), dans $BANC_DONNEES")
ap.add_argument("--par", type=int, default=6, help="relectures en parallèle (le Mac n'a pas de limite de places)")
a = ap.parse_args()

ajout = (banc.ICI / a.ajout).read_text() if a.ajout else ""
if a.angle:
    ajout += "\n\n" + json.loads((banc.ICI / "angles.json").read_text())[a.angle]
notes = banc.charger(a.notes) if a.notes else {}
agent = {"description": "relecteur rejoué (banc)", "prompt": banc.corps_relecteur(), "model": a.modele,
         "disallowedTools": ["Edit", "Write", "NotebookEdit"]}
if a.effort != "-":
    agent["effort"] = a.effort
sortie = banc.DONNEES / "sorties" / a.bras
sortie.mkdir(parents=True, exist_ok=True)
verrou, depense = threading.Lock(), [0.0]


def un(cas: dict):
    k = str(cas["id"]); f = sortie / f"{k}.json"
    if f.exists():
        return k, "déjà"
    with verrou:
        if depense[0] >= a.plafond:
            return k, "plafond"
    with banc.Worktree(cas, f"{a.bras}-{k}") as wt:
        prompt = cas["prompt"].replace(cas["rep"], str(wt)) + (("\n\n" + ajout) if ajout else "")
        if notes.get(k):
            prompt += "\n\n" + notes[k]
        d = banc.claude(prompt, cwd=wt, agent=agent, tours=60)
    d["id"] = cas["id"]
    f.write_text(json.dumps(d, ensure_ascii=False))
    with verrou:
        depense[0] += d.get("total_cost_usd") or 0
    return k, round(d.get("total_cost_usd") or 0, 3)


with cf.ThreadPoolExecutor(a.par) as ex:
    for res in ex.map(un, banc.charger(a.cas)):
        print(res, "cumul", round(depense[0], 2), flush=True)
print("FIN", a.bras, round(depense[0], 2))
