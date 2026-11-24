#!/usr/bin/env python3
"""Rejoue un bras de relecture sur le jeu de cas : la consigne `relecteur.md` du dépôt, le brief d'origine, un worktree
détaché au commit relu, et un modèle / effort / ajout de consigne au choix.

Usage :
  rejouer.py <bras> <modele> <effort|-> <plafond_dollars> [--cas echantillon.json]
             [--liste <chemin> | --ajout checklist.txt] [--angle secu|archi|senior|tests] [--notes notes.json] [--par 6]

--liste : la liste de relecture ajoutée au brief (ex. le fichier du plugin plans-notion, la checklist v2). Sans --liste ni --ajout,
         aucune consigne n'est ajoutée : c'est le bras témoin, qui doit rester reproductible.
--ajout : un autre texte ajouté au brief, à côté de ce script (ex. checklist.txt, la v1) ; exclusif de --liste.
<plafond_dollars> : la dépense maximale du bras. Un cas ne part que si le budget restant couvre le coût moyen d'un lot (voir Budget).

Sorties : $BANC_DONNEES/sorties/<bras>/<id>.json (sortie JSON de `claude -p`, dont `result` et `total_cost_usd`).
Un cas déjà rejoué est sauté : on relance un bras interrompu sans rien repayer.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import threading
from pathlib import Path

import banc

LISTE_PLUGIN = banc.ICI.parents[1] / "plugins/plans-notion/skills/_partage/listes/relecture-code.md"


class Budget:
    """Le plafond d'un rejeu. Un cas ne part que si le budget restant, une fois réservé le coût des cas en vol, couvre
    le coût moyen d'un lot (`par` cas). Tant qu'aucun cas n'est fini, le coût est inconnu : un seul cas part à la fois.
    Ainsi six cas en vol ne dépassent pas le plafond de six cas, et un cas qui ne part pas n'est pas rejoué plus tard
    dans cette passe : la reprise (les sorties déjà là sont sautées) le fera."""

    def __init__(self, plafond: float, par: int):
        self.plafond, self.par = plafond, max(1, par)
        self.depense, self.faits, self.en_vol = 0.0, 0, 0
        self._cond = threading.Condition()

    def demarrer(self, attendre: bool = False) -> bool:
        """Vrai si le cas peut partir. `attendre` (les threads du rejeu) : un cas qui se présente pendant que le premier
        coût est inconnu attend la fin de ce premier cas, au lieu d'être refusé ; le refus, lui, reste définitif."""
        with self._cond:
            if attendre:
                while self.faits == 0 and self.en_vol > 0:
                    self._cond.wait()
            if self.faits == 0:
                ok = self.en_vol == 0 and self.depense < self.plafond
            else:
                moyenne = self.depense / self.faits
                reste = self.plafond - self.depense - self.en_vol * moyenne
                ok = reste >= moyenne * self.par
            if ok:
                self.en_vol += 1
            return ok

    def terminer(self, cout: float, compte: bool) -> None:
        with self._cond:
            self.en_vol -= 1
            if compte:
                self.depense += cout
                self.faits += 1
            self._cond.notify_all()


def construire_parseur() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("bras"); ap.add_argument("modele"); ap.add_argument("effort"); ap.add_argument("plafond", type=float)
    ap.add_argument("--cas", default="echantillon.json", help="fichier de cas, dans $BANC_DONNEES")
    consigne = ap.add_mutually_exclusive_group()
    consigne.add_argument("--liste", nargs="?", const=str(LISTE_PLUGIN),
                          help="liste de relecture ajoutée au brief ; sans valeur : le fichier du plugin plans-notion ; absent : aucune consigne")
    consigne.add_argument("--ajout", help="texte ajouté au brief (ex. checklist.txt, à côté de ce script) ; remplace --liste")
    ap.add_argument("--angle", help="clé de angles.json ajoutée au brief (comité)")
    ap.add_argument("--notes", help="JSON {id: texte} ajouté au brief cas par cas (2e passe), dans $BANC_DONNEES")
    ap.add_argument("--par", type=int, default=6, help="relectures en parallèle (le Mac n'a pas de limite de places)")
    ap.add_argument("--bash-enferme", action="store_true", help="donne Bash au relecteur, dans le bac à sable (banc.BAC_A_SABLE)")
    return ap


def main(argv=None) -> int:
    a = construire_parseur().parse_args(argv)

    if a.ajout:
        ajout = (banc.ICI / a.ajout).read_text()
    elif a.liste:
        ajout = Path(a.liste).expanduser().read_text()
    else:
        ajout = ""
    if a.angle:
        ajout += "\n\n" + json.loads((banc.ICI / "angles.json").read_text())[a.angle]
    notes = banc.charger(a.notes) if a.notes else {}
    agent = {"description": "relecteur rejoué (banc)", "prompt": banc.corps_relecteur(), "model": a.modele,
             "tools": banc.LECTURE + (["Bash"] if a.bash_enferme else [])}
    note = banc.NOTE_BASH if a.bash_enferme else banc.NOTE_LECTURE
    if a.effort != "-":
        agent["effort"] = a.effort
    sortie = banc.DONNEES / "sorties" / a.bras
    sortie.mkdir(parents=True, exist_ok=True)
    budget = Budget(a.plafond, a.par)

    def un(cas: dict):
        k = str(cas["id"]); f = sortie / f"{k}.json"
        if f.exists():
            return k, "déjà"
        if not budget.demarrer(attendre=True):
            return k, "plafond"
        cout, compte = 0.0, False
        try:
            with banc.Worktree(cas, f"{a.bras}-{k}") as wt:
                prompt = cas["prompt"].replace(cas["rep"], str(wt)) + note + (("\n\n" + ajout) if ajout else "")
                if notes.get(k):
                    prompt += "\n\n" + notes[k]
                d = banc.claude(prompt, cwd=wt, agent=agent, tours=60, bash_enferme=a.bash_enferme)
            d["id"] = cas["id"]
            f.write_text(json.dumps(d, ensure_ascii=False))
            cout, compte = d.get("total_cost_usd") or 0, True
            return k, round(cout, 3)
        finally:
            budget.terminer(cout, compte)

    with cf.ThreadPoolExecutor(a.par) as ex:
        for res in ex.map(un, banc.charger(a.cas)):
            print(res, "cumul", round(budget.depense, 2), flush=True)
    print("FIN", a.bras, round(budget.depense, 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
