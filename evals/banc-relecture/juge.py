#!/usr/bin/env python3
"""Juge automatique : compare les rapports d'un ou plusieurs bras aux remarques de la relecture de référence (Opus).

Usage : juge.py <sortie.json> <bras1> [bras2 ...] [--cas id1,id2] [--par 8] [--modele claude-sonnet-5-5]
Plusieurs bras = leur union (comité, tirages, passes) : les rapports d'un même cas sont jugés ensemble.

La référence est $BANC_DONNEES/ref-opus.json : {id: [{n, gravite, resume, extrait}]}. Elle a été établie par l'agent
`evaluateur` sur 24 cas ; ce juge, validé contre lui (README, « Le juge »), garde le même classement des bras à 2-9 points.
Ligne rendue : rappel des remarques, rappel des bugs, remarques en plus réelles / bruit, erreurs, coût du juge.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json

import banc

CONSIGNE = """Tu es juge de relectures de code. On te donne les remarques d'une relecture de RÉFÉRENCE (Opus) et un ou plusieurs rapports CANDIDATS sur le même changement.
1. Pour chaque remarque de référence : le candidat signale-t-il LE MÊME défaut (même cause, même endroit — pas seulement le même fichier) ? « oui », « partiel » (même défaut vu en partie, ou conséquence vue sans la cause) ou « non ». Un défaut que le candidat voit mais déclare explicitement « pas une remarque » compte « non ».
2. Liste chaque remarque du candidat ABSENTE de la référence (dédoublonne entre rapports candidats : même cause, même endroit = une seule), avec verdict « réelle » (argumentée par fichier:ligne ou scénario concret, plausible) ou « bruit » (vague, non argumentée, contredite par le brief ou par la référence).
Réponds UNIQUEMENT par un JSON : {"ref": [{"n": <int>, "match": "oui|partiel|non"}], "extras": [{"resume": "<≤200 car.>", "verdict": "réelle|bruit"}]}"""
POIDS = {"oui": 1, "partiel": 0.5, "non": 0}

ap = argparse.ArgumentParser()
ap.add_argument("sortie"); ap.add_argument("bras", nargs="+")
ap.add_argument("--cas"); ap.add_argument("--par", type=int, default=8); ap.add_argument("--modele", default="claude-sonnet-5-5")
a = ap.parse_args()
ref = banc.charger("ref-opus.json")
ids = a.cas.split(",") if a.cas else sorted(ref, key=int)


def un(k: str):
    rapports = []
    for b in a.bras:
        f = banc.DONNEES / "sorties" / b / f"{k}.json"
        if f.exists():
            rapports.append((b, json.loads(f.read_text()).get("result") or ""))
    texte = (CONSIGNE + "\n\nRÉFÉRENCE :\n" + json.dumps(ref[k], ensure_ascii=False) + "\n\n"
             + "\n\n".join(f"CANDIDAT {b} :\n{r[:12000]}" for b, r in rapports))
    d = banc.claude(texte, modele=a.modele, outils="", tours=1, delai=600)
    j = banc.json_dans(d.get("result") or "")
    return k, (j if j else {"erreur": d.get("erreur") or "JSON illisible"}), d.get("total_cost_usd") or 0


res, cout = {}, 0.0
with cf.ThreadPoolExecutor(a.par) as ex:
    for k, j, c in ex.map(un, ids):
        res[k] = j; cout += c
(banc.DONNEES / "jugements").mkdir(parents=True, exist_ok=True)
(banc.DONNEES / "jugements" / a.sortie).write_text(json.dumps(res, ensure_ascii=False, indent=1))

n = tot = nb = totb = ext_r = ext_b = err = 0
for k, j in res.items():
    if "erreur" in j:
        err += 1; continue
    m = {x["n"]: x["match"] for x in j.get("ref", [])}
    for o in ref[k]:
        s = POIDS.get(m.get(o["n"], "non"), 0); n += s; tot += 1
        if o["gravite"].startswith("bug"):
            nb += s; totb += 1
    for e in j.get("extras", []):
        ext_r += e["verdict"] == "réelle"; ext_b += e["verdict"] != "réelle"
print(f"rappel {n / max(tot, 1):.1%} ({n}/{tot}) | bugs {nb / max(totb, 1):.1%} | extras réelles/bruit {ext_r}/{ext_b}"
      f" | erreurs {err} | coût juge {cout:.2f}")
