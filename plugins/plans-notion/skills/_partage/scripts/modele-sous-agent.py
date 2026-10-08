#!/usr/bin/env python3
"""Dit sur quel modèle un sous-agent a réellement tourné, et si c'est celui de sa définition.

Pourquoi un script : le 2026-10-08, une session a mis à jour `plans-notion` en
0.20.0 (executant passé à `model: haiku`) sans recharger ses plugins ; ses
executants ont continué en Sonnet, sur la définition 0.19.1 gardée en mémoire,
sans que rien ne le signale. Le frontmatter garantit le modèle par construction
— à condition que la session ait chargé le bon frontmatter. Seule la
transcription du sous-agent dit ce qui a tourné.

La transcription vit sous
``<racine>/projects/<projet>/<session>/subagents/agent-<id>.jsonl`` ; ``<id>``
est l'``agentId`` que rend l'outil Agent. On y relève le ``message.model`` de
chaque réponse du modèle.

Usage : modele-sous-agent.py <agentId> [--agent <plugin>:<agent> | --definition <agent.md>]
                             [--racine <dir>]
  sans --agent ni --definition : imprime les modèles vus (« n × modèle ») ; code 0.
  --agent plans-notion:executant : la définition est lue dans la version
  **installée** du plugin (``installPath`` de ``plugins/installed_plugins.json``),
  pas dans la copie que la session a chargée — c'est précisément celle-là qui
  peut être périmée, et elle se donnerait raison à elle-même.
  --definition <agent.md> : un fichier de définition donné tel quel.
  Le ``model:`` du frontmatter (alias ``haiku``, ``sonnet``, ``opus``, ou
  identifiant complet) est comparé ; code 0 si tout appel a tourné sur ce
  modèle, 1 sinon (une ligne qui dit l'écart).
Code 2 : transcription introuvable, aucun modèle relevé, plugin non installé,
ou définition sans ``model:`` (rien à comparer). ``--racine`` vaut ``$CLAUDE_CONFIG_DIR`` ou
``~/.claude`` par défaut. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ALIAS = ("haiku", "sonnet", "opus")


def transcription(racine: Path, agent_id: str) -> Path | None:
    nom = agent_id if agent_id.startswith("agent-") else f"agent-{agent_id}"
    trouves = sorted(racine.glob(f"projects/*/*/subagents/{nom}.jsonl"))
    return trouves[-1] if trouves else None


def modeles(chemin: Path) -> Counter:
    vus: Counter = Counter()
    for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        m = d.get("message") if isinstance(d, dict) else None
        if isinstance(m, dict) and m.get("role") == "assistant":
            modele = m.get("model")
            if isinstance(modele, str) and modele and not modele.startswith("<"):
                vus[modele] += 1
    return vus


def modele_declare(definition: Path) -> str | None:
    texte = definition.read_text(encoding="utf-8")
    bloc = re.match(r"^---\n(.*?)\n---", texte, re.S)
    if not bloc:
        return None
    m = re.search(r"^model:\s*([^\s#]+)", bloc.group(1), re.M)
    return m.group(1).strip("\"'") if m else None


def definition_installee(racine: Path, agent: str) -> Path | None:
    plugin, _, nom = agent.partition(":")
    try:
        installes = json.loads((racine / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for cle, entrees in sorted((installes.get("plugins") or {}).items()):
        if cle.split("@")[0] == plugin and entrees:
            return Path(entrees[0]["installPath"]) / "agents" / f"{nom}.md"
    return None


def conforme(vu: str, declare: str) -> bool:
    if declare in ALIAS:
        return f"claude-{declare}-" in vu
    return vu == declare or declare in vu


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("agent_id")
    choix = ap.add_mutually_exclusive_group()
    choix.add_argument("--agent", help="<plugin>:<agent>, lu dans la version installée")
    choix.add_argument("--definition", type=Path)
    ap.add_argument("--racine", type=Path,
                    default=Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"))
    a = ap.parse_args(argv)

    chemin = transcription(a.racine, a.agent_id)
    if chemin is None:
        print(f"transcription introuvable : agent-{a.agent_id.removeprefix('agent-')}.jsonl "
              f"sous {a.racine}/projects/*/*/subagents/", file=sys.stderr)
        return 2
    vus = modeles(chemin)
    if not vus:
        print(f"aucun modèle relevé dans {chemin}", file=sys.stderr)
        return 2
    for modele, n in vus.most_common():
        print(f"{n} × {modele}")
    if a.agent:
        a.definition = definition_installee(a.racine, a.agent)
        if a.definition is None or not a.definition.is_file():
            print(f"{a.agent} : plugin non installé ou agent absent "
                  f"({a.racine}/plugins/installed_plugins.json)", file=sys.stderr)
            return 2
    if a.definition is None:
        return 0

    declare = modele_declare(a.definition)
    if declare is None:
        print(f"{a.definition} ne déclare pas de model: — rien à comparer", file=sys.stderr)
        return 2
    ecarts = [m for m in vus if not conforme(m, declare)]
    if ecarts:
        print(f"ÉCART : la définition déclare « {declare} », le sous-agent a tourné sur "
              f"{', '.join(sorted(ecarts))}. Définition périmée en mémoire de la session "
              f"(plugin mis à jour sans rechargement) : ouvrir une session neuve.")
        return 1
    print(f"conforme : « {declare} »")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
