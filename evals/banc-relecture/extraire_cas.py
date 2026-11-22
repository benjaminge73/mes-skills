#!/usr/bin/env python3
"""Construit le jeu de cas depuis les journaux de Claude Code de la machine qui a relu (le VPS) : chaque sous-agent
`relecteur` passé donne un cas (brief, rapport final, verdict, coût), et chaque cas dont la plage de commits existe encore
dans un clone local devient rejouable. Lecture seule sur les journaux et les dépôts.

Usage (sur la machine des journaux) :
  extraire_cas.py <dossier_sortie> --depuis 2026-11-01 --clones ~/repos/github/<compte> [--projets ~/.claude/projects]

Produit dans <dossier_sortie> : cas-opus.json (tous les cas), cas-rejouables.json, jev-entrees.json (objectif, stat, diff
de chaque cas rejouable) et bundles/<dépôt>.bundle (les commits des cas, à cloner côté poste de banc :
`git clone --bare <bundle> <dépôt>.git` puis `git fetch <bundle> 'refs/poc/*:refs/poc/*'`).
Des refs temporaires `refs/poc/*` sont posées pour créer les bundles, puis retirées des dépôts.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("sortie"); ap.add_argument("--depuis", required=True); ap.add_argument("--clones", required=True)
ap.add_argument("--projets", default="~/.claude/projects")
a = ap.parse_args()
out = Path(a.sortie); (out / "bundles").mkdir(parents=True, exist_ok=True)
VERDICT = re.compile(r"RIEN [ÀA] SIGNALER|REMARQUES\s*\((\d+)\)", re.I)


def lire_sous_agent(meta: str):
    """Un sous-agent `relecteur` : son brief (1er message), son rapport final (remise SubagentHandback, à défaut dernier
    texte), son modèle et son usage dédoublonné par requête."""
    f = meta.replace(".meta.json", ".jsonl")
    prompt = dernier = ts = modele = None; usage = collections.Counter(); vus = set()
    for ligne in open(f, errors="ignore"):
        try:
            d = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        ts = ts or d.get("timestamp"); msg = d.get("message") or {}
        if d.get("type") == "user" and prompt is None and isinstance(msg.get("content"), str):
            prompt = msg["content"]
        if d.get("type") == "assistant":
            modele = msg.get("model") or modele
            rid = d.get("requestId") or msg.get("id")
            if rid not in vus:
                vus.add(rid)
                for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
                    usage[k] += (msg.get("usage") or {}).get(k, 0) or 0
            for b in msg.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip():
                    dernier = b["text"]
                if isinstance(b, dict) and b.get("type") == "tool_use" and "andback" in b.get("name", ""):
                    dernier = json.dumps(b.get("input"), ensure_ascii=False)
    return prompt, dernier, ts, modele, usage


cas = []
for meta in glob.glob(os.path.expanduser(a.projets) + "/*/*/subagents/*.meta.json"):
    try:
        if "relecteur" not in json.loads(Path(meta).read_text()).get("agentType", ""):
            continue
    except (OSError, json.JSONDecodeError):
        continue
    prompt, rapport, ts, modele, usage = lire_sous_agent(meta)
    if not ts or ts[:10] < a.depuis or not prompt:
        continue
    v = VERDICT.search(rapport or "")
    cas.append({"ts": ts, "model": modele, "prompt": prompt, "resultat": rapport, "verdict": v.group(0) if v else None,
                "usage": usage, "mode": "plan entier" if "plan entier" in prompt.lower() else "étape",
                "rem": bool(v and v.group(0).upper().startswith("REM"))})
for i, x in enumerate(cas):
    x["id"] = i
(out / "cas-opus.json").write_text(json.dumps(cas, ensure_ascii=False))


def git(*args, check=False):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


rejouables = []
for x in cas:
    plage = re.search(r"([0-9a-f]{7,40})\.\.\.?([0-9a-f]{7,40})\b", x["prompt"])
    rep = re.search(r"Répertoire\s*:\s*(\S+?)\.?\s", x["prompt"])
    if not plage or not rep:
        continue
    chemin = rep.group(1).rstrip(".")
    # Un worktree de plan vit sous .../worktrees/<dépôt>/<branche> ; sinon le dossier est le dépôt lui-même.
    nom = chemin.split("/worktrees/", 1)[1].split("/")[0] if "/worktrees/" in chemin else Path(chemin).name
    base = Path(a.clones).expanduser() / nom
    debut, fin = plage.group(1), plage.group(2)
    if not (base / ".git").exists() or any(git("-C", str(base), "cat-file", "-e", h + "^{commit}").returncode for h in (debut, fin)):
        continue
    x.update(base=str(base), rep=chemin, debut=debut, fin=fin, plage=plage.group(0))
    rejouables.append(x)

entrees = {}
par_depot = collections.defaultdict(list)
for x in rejouables:
    par_depot[x["base"]].append(x)
    m = re.search(r"OBJECTIF[^:]*:\s*(.{0,1500})", x["prompt"], re.S)
    entrees[str(x["id"])] = {"objectif": m.group(1) if m else x["prompt"][:1500],
                             "stat": git("-C", x["base"], "diff", "--stat", x["debut"], x["fin"]).stdout[-3000:],
                             "diff": git("-C", x["base"], "diff", "-U2", x["debut"], x["fin"]).stdout[:12000]}
for base, xs in par_depot.items():
    for x in xs:
        git("-C", base, "update-ref", f"refs/poc/{x['id']}f", x["fin"], check=True)
        git("-C", base, "update-ref", f"refs/poc/{x['id']}d", x["debut"], check=True)
    git("-C", base, "bundle", "create", str((out / "bundles" / f"{Path(base).name}.bundle").resolve()), "--glob=refs/poc/*", check=True)
    for ref in git("-C", base, "for-each-ref", "--format=%(refname)", "refs/poc/").stdout.split():
        git("-C", base, "update-ref", "-d", ref)
    print(Path(base).name, len(xs), "cas")
(out / "cas-rejouables.json").write_text(json.dumps(rejouables, ensure_ascii=False))
(out / "jev-entrees.json").write_text(json.dumps(entrees, ensure_ascii=False))
print("cas", len(cas), "| rejouables", len(rejouables), collections.Counter((x["mode"], x["rem"]) for x in rejouables))
