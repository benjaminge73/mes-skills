#!/usr/bin/env python3
"""La chaîne retenue par le POC du 2026-11-22 : N rapports Haiku (checklist) → extraction et dédoublonnage des remarques
(Haiku, texte seul) → vérification de chaque remarque dans le code (Haiku, citation exigée, sinon REFUTED)
→ un rapport synthétique des remarques non réfutées, jugeable par juge.py.

Usage : chaine.py <bras_sortie> <bras1> [bras2 ...] [--cas echantillon.json] [--jev .env:VARIABLE --seuil-jev 0.5]

`--jev` : second avis de Jev (noul, diff fourni) sur les remarques que Haiku réfute ; une remarque réfutée est repêchée
si Jev lui donne au moins `--seuil-jev`. La clé est lue dans le fichier donné, par ce seul processus, jamais affichée.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re

import banc
import jev

EXTRACTION = ("Voici {n} rapports de relecture du MÊME changement. Extrais la liste DÉDOUBLONNÉE de toutes les remarques "
              "(défauts signalés), en fusionnant celles qui ont même cause et même endroit. Ignore les « rien » et les points "
              "déclarés non bloquants sans défaut. Réponds UNIQUEMENT par un JSON : "
              "{{\"remarques\": [\"<remarque autonome, ≤ 400 car., avec fichier:ligne et scénario s'ils sont donnés>\"]}}\n\n{rapports}")
VERIFICATION = ("Tu vérifies UNE remarque de relecture sur ce dépôt (le worktree courant est au commit relu ; la plage relue est "
                "{plage}). Objectif de l'étape : {obj}\n\nREMARQUE À VÉRIFIER :\n{txt}\n\nVa lire le code (Read, Grep, git "
                "show/diff/log). Le défaut est-il réel dans ce code ? Cite la ou les lignes qui le prouvent (fichier:ligne + "
                "extrait exact). Si tu ne peux pas citer de ligne qui prouve le défaut, ou si le code le contredit, il est "
                "réfuté. Dernière ligne, seule : VERDICT: CONFIRMED ou VERDICT: REFUTED")

ap = argparse.ArgumentParser()
ap.add_argument("sortie"); ap.add_argument("bras", nargs="+")
ap.add_argument("--cas", default="echantillon.json")
ap.add_argument("--jev", help="<fichier .env>:<VARIABLE> pour le second avis de Jev")
ap.add_argument("--seuil-jev", type=float, default=0.5)
a = ap.parse_args()
cle = jev.cle(*a.jev.split(":", 1)) if a.jev else None
diffs = banc.charger("jev-entrees.json") if cle else {}
dossier = banc.DONNEES / "sorties" / a.sortie
dossier.mkdir(parents=True, exist_ok=True)


def cas(c: dict):
    k = str(c["id"]); cout = 0.0
    rapports = [json.loads(f.read_text()).get("result") or ""
                for f in (banc.DONNEES / "sorties" / b / f"{k}.json" for b in a.bras) if f.exists()]
    d = banc.claude(EXTRACTION.format(n=len(rapports), rapports="\n\n".join(
        f"RAPPORT {i + 1} :\n{r[:10000]}" for i, r in enumerate(rapports))), tours=3)
    cout += d.get("total_cost_usd") or 0
    remarques = (banc.json_dans(d.get("result") or "") or {}).get("remarques", [])
    with banc.Worktree(c, f"{a.sortie}-{k}") as wt:
        def verifier(r: str):
            v = banc.claude(VERIFICATION.format(plage=c["plage"], obj=banc.objectif(c, 1200), txt=r), cwd=wt,
                            outils="Read,Grep,Glob,Bash", tours=15, delai=900)
            t = v.get("result") or ""
            verdict = "CONFIRMED" if re.search(r"VERDICT:\s*CONFIRMED", t) else "REFUTED" if re.search(r"VERDICT:\s*REFUTED", t) else "?"
            if verdict == "REFUTED" and cle:
                e = diffs.get(k, {})
                p = jev.noul(cle, "OBJECTIF :\n" + e.get("objectif", "")[:1200] + "\n\nDIFF :\n" + e.get("diff", "")[:9000]
                             + "\n\nREMARQUE DE RELECTURE :\n" + r,
                             "Le changement ci-dessus contient-il réellement le défaut décrit par la remarque de relecture ?")
                if p is not None and p >= a.seuil_jev:
                    verdict = "REPECHEE"
            return r, verdict, v.get("total_cost_usd") or 0
        with cf.ThreadPoolExecutor(4) as ex:
            verdicts = list(ex.map(verifier, remarques))
    cout += sum(c_ for _, _, c_ in verdicts)
    gardees = [r for r, v, _ in verdicts if v != "REFUTED"]
    rapport = ("REMARQUES (%d)\n" % len(gardees) + "\n".join(f"{i + 1}. {r}" for i, r in enumerate(gardees))) if gardees else "RIEN À SIGNALER"
    (dossier / f"{k}.json").write_text(json.dumps({"id": c["id"], "result": rapport, "total_cost_usd": cout,
                                                   "verdicts": [v for _, v, _ in verdicts]}, ensure_ascii=False))
    return k, len(remarques), len(gardees), cout


total = 0.0
with cf.ThreadPoolExecutor(3) as ex:
    for k, n, g, c in ex.map(cas, banc.charger(a.cas)):
        total += c; print(k, n, "->", g, flush=True)
print("FIN", a.sortie, "coût", round(total, 2))
