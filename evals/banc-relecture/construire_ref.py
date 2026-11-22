#!/usr/bin/env python3
"""Construit une référence (`ref-*.json`) depuis les rapports Opus d'origine d'un fichier de cas : la liste des remarques
de chaque rapport, avec leur gravité, au même format que `ref-opus.json` (établie, elle, par l'agent `evaluateur`).

Usage : construire_ref.py <cas.json> <ref-sortie.json> [--exclure echantillon.json] [--par 8]
`--exclure` retire les cas d'un autre fichier : c'est ainsi qu'on obtient un jeu de VALIDATION, jamais vu par une
checklist mise au point sur l'échantillon.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json

import banc

CONSIGNE = """Voici le rapport final d'une relecture de code. Liste chaque remarque (défaut signalé) qu'il compte, sans en inventer ni en fusionner. Pour chacune : sa gravité parmi « bug de correction », « écart au plan », « test qui ne teste rien », « découverte hors plan », « autre » (doc périmée, nit), un résumé ≤ 200 caractères, et un extrait exact du rapport. Un point que le rapport déclare explicitement « pas une remarque » ou « hors comptage » n'en est pas une. Rapport « RIEN À SIGNALER » : liste vide.
Réponds UNIQUEMENT par un JSON : {"remarques": [{"n": 1, "gravite": "...", "resume": "...", "extrait": "..."}]}

RAPPORT :
"""

ap = argparse.ArgumentParser()
ap.add_argument("cas"); ap.add_argument("sortie"); ap.add_argument("--exclure"); ap.add_argument("--par", type=int, default=8)
a = ap.parse_args()
exclus = {str(x["id"]) for x in banc.charger(a.exclure)} if a.exclure else set()
cas = [x for x in banc.charger(a.cas) if str(x["id"]) not in exclus]


def un(x: dict):
    d = banc.claude(CONSIGNE + (x.get("resultat") or "")[:15000], modele="claude-sonnet-5-5", outils="", tours=1, delai=600)
    j = banc.json_dans(d.get("result") or "")
    return str(x["id"]), (j or {}).get("remarques"), d.get("total_cost_usd") or 0


ref, cout, erreurs = {}, 0.0, []
with cf.ThreadPoolExecutor(a.par) as ex:
    for k, r, c in ex.map(un, cas):
        cout += c
        if r is None:
            erreurs.append(k)
        else:
            ref[k] = r
(banc.DONNEES / a.sortie).write_text(json.dumps(ref, ensure_ascii=False, indent=1))
(banc.DONNEES / ("cas-" + a.sortie)).write_text(json.dumps([x for x in cas if str(x["id"]) in ref], ensure_ascii=False))
print(f"cas {len(ref)} | remarques {sum(len(v) for v in ref.values())} | bugs {sum(o['gravite'].startswith('bug') for v in ref.values() for o in v)}"
      f" | erreurs {erreurs} | coût {cout:.2f}")
