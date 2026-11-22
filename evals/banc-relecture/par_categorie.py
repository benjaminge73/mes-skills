#!/usr/bin/env python3
"""Rappel par catégorie de défaut, depuis un ou plusieurs jugements de `juge.py`.

Usage : par_categorie.py <jugement1.json> [jugement2.json ...] [--ref ref-opus.json]
Chaque jugement est une ligne ; les colonnes sont les gravités de la référence (bug de correction, écart au plan, test qui
ne teste rien, découverte hors plan, autre). C'est ce tableau qui dit si une checklist corrige les angles morts qu'on lui
a donnés à corriger — et, sur le jeu de validation, si elle le fait sans sur-apprentissage.
"""
from __future__ import annotations

import argparse
import collections
import json

import banc

ap = argparse.ArgumentParser()
ap.add_argument("jugements", nargs="+"); ap.add_argument("--ref", default="ref-opus.json")
a = ap.parse_args()
ref = banc.charger(a.ref)
POIDS = {"oui": 1, "partiel": 0.5}
CATS = ["bug de correction", "écart au plan", "test qui ne teste rien", "découverte hors plan", "autre"]


def cat(g: str) -> str:
    return next((c for c in CATS if g.startswith(c.split()[0])), "autre")


totaux = collections.Counter(cat(o["gravite"]) for v in ref.values() for o in v)
print(f"{'jugement':34} " + " ".join(f"{c[:14]:>15}" for c in CATS) + f" {'extras r/b':>11}")
print(f"{'(référence : nombre)':34} " + " ".join(f"{totaux[c]:>15}" for c in CATS))
for f in a.jugements:
    j = json.loads((banc.DONNEES / "jugements" / f).read_text())
    trouve = collections.Counter(); ext = collections.Counter()
    for k, v in j.items():
        if "erreur" in v or k not in ref:
            continue
        m = {x["n"]: x["match"] for x in v.get("ref", [])}
        for o in ref[k]:
            trouve[cat(o["gravite"])] += POIDS.get(m.get(o["n"], "non"), 0)
        for e in v.get("extras", []):
            ext[e["verdict"] == "réelle"] += 1
    print(f"{f[:34]:34} " + " ".join(f"{(trouve[c] / totaux[c] if totaux[c] else 0):>14.0%} " for c in CATS) + f" {ext[True]:>5}/{ext[False]:<5}")
