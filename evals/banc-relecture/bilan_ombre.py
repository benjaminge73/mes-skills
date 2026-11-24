#!/usr/bin/env python3
"""Bilan de l'ombre : applique la règle de Q2 (« chaîne à la place d'Opus ») aux ombres triées par le pilote.

Pour chaque étape, deux fichiers dans `$BANC_DONNEES/ombres/` :
  - `ombre-<id>.json`, écrit par `ombre.py` (rapport de la chaîne, coûts, `liste_sha256`, date `fait_le`) ;
  - `retenues-<id>.json`, écrit par le pilote après tri : `{"id": ..., "remarques": [...]}`, où chaque remarque porte
    `origine` (`opus` : remarque d'Opus retenue seule ; `commune` : Opus et l'ombre la disent, retenue ; `ombre` :
    remarque de l'ombre seule, triée) et `verdict` (`retenue` pour opus et commune ; `réelle` ou `bruit` pour ombre).
    `gravite` (« bug… » ou « autre ») et `resume` sont requis, `extrait` est facultatif.

Vérité = remarques retenues (opus, commune) plus remarques de l'ombre seule jugées réelles (union). La chaîne est
mesurée par `juge.py` (Sonnet, texte seul) contre cette vérité : rappel pondéré (oui 1, partiel 0,5, non 0).

Règle de Q2 (écrite avant de regarder les données) :
  - moins de `--min-etapes` étapes triées : « pas assez d'étapes », code 3, aucun appel au juge ;
  - sinon, si un des trois plafonds est dépassé (bugs de correction manqués au total > 1, remarques de l'ombre seule
    bruit en moyenne > 1 par relecture, coût Haiku + chaîne en moyenne > 0,5 dollar par relecture) : « statu quo » ;
  - rappel >= 70 % : « bascule » ; rappel entre 50 et 70 % : « hybride » ; sinon « statu quo ».
La sortie est une recommandation : la décision reste celle de Benjamin.

Usage : bilan_ombre.py [--depuis AAAA-MM-JJ] [--min-etapes 20]
Codes : 0 décision rendue ; 1 erreur de données ou du juge ; 3 pas assez d'étapes ; 4 versions de liste mêlées.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import banc

SEUIL_BASCULE = Fraction(70, 100)
SEUIL_HYBRIDE = Fraction(50, 100)
PLAFOND_BUGS = 1            # bugs de correction retenus manqués par la chaîne, au total
PLAFOND_NON_FONDEES = 1     # remarques de l'ombre seule jugées bruit, en moyenne par relecture
PLAFOND_COUT = 0.5          # dollars par relecture, Haiku + chaîne (le bras Sonnet est compté à part)
POIDS = {"oui": Fraction(1), "partiel": Fraction(1, 2), "non": Fraction(0)}
ORIGINES = {"opus": {"retenue"}, "commune": {"retenue", "écartée"}, "ombre": {"réelle", "bruit"}}
VERITE = {"retenue", "réelle"}
PAS_ASSEZ = "pas assez d'étapes"


def valider_retenues(donnees) -> list[dict]:
    """La liste des remarques du fichier de tri du pilote. Lève ValueError si la forme n'est pas celle de l'en-tête."""
    remarques = donnees.get("remarques") if isinstance(donnees, dict) else None
    if not isinstance(remarques, list):
        raise ValueError("« remarques » doit être une liste")
    for i, r in enumerate(remarques, 1):
        origine, verdict = r.get("origine"), r.get("verdict")
        if origine not in ORIGINES:
            raise ValueError(f"remarque {i} : origine {origine!r} inconnue (opus, commune ou ombre)")
        if verdict not in ORIGINES[origine]:
            raise ValueError(f"remarque {i} : verdict {verdict!r} interdit pour l'origine {origine}")
        if not str(r.get("resume", "")).strip():
            raise ValueError(f"remarque {i} : « resume » vide")
    return remarques


def verite(remarques: list[dict]) -> list[dict]:
    return [r for r in remarques if r["verdict"] in VERITE]


def reference(remarques: list[dict]) -> list[dict]:
    """La vérité d'une étape au format de référence de juge.py : {n, gravite, resume, extrait}."""
    return [{"n": i, "gravite": r.get("gravite", "autre"), "resume": r["resume"], "extrait": r.get("extrait", "")}
            for i, r in enumerate(verite(remarques), 1)]


def juger_par_juge(reference_par_etape: dict, chaines: dict[str, str]) -> dict:
    """Lance juge.py sur les rapports de la chaîne contre la vérité ; rend son JSON, {étape: {ref, extras}}."""
    bras = "bilan-" + time.strftime("%Y%m%d-%H%M%S")
    donnees = banc.DONNEES
    donnees.mkdir(parents=True, exist_ok=True)
    (donnees / f"ref-{bras}.json").write_text(json.dumps(reference_par_etape, ensure_ascii=False))
    for etape, texte in chaines.items():
        f = donnees / "sorties" / bras / f"{etape}.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"result": texte}, ensure_ascii=False))
    r = subprocess.run([sys.executable, str(banc.ICI / "juge.py"), f"{bras}.json", bras,
                        "--cas", ",".join(chaines), "--ref", f"ref-{bras}.json"],
                       cwd=banc.ICI, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"juge.py en échec : {(r.stderr or r.stdout).strip()[-300:]}")
    return json.loads((donnees / "jugements" / f"{bras}.json").read_text())


def charger(ombres: Path, depuis: str | None) -> tuple[list[dict], list[str]]:
    """Les étapes triées (ombre et retenues présentes, datées à partir de `depuis`), et les ids laissés de côté."""
    etapes, laissees = [], []
    for f in sorted(ombres.glob("ombre-*.json"), key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p.name)]):
        id_ = f.stem[len("ombre-"):]
        ombre = json.loads(f.read_text())
        if not (ombres / f"retenues-{id_}.json").exists():
            laissees.append(f"{id_} (sans tri du pilote)")
            continue
        if not ombre.get("chaine"):
            laissees.append(f"{id_} (sans rapport de la chaîne)")
            continue
        date = ombre.get("fait_le") or datetime.date.fromtimestamp(f.stat().st_mtime).isoformat()
        if depuis and date < depuis:
            continue
        try:
            remarques = valider_retenues(json.loads((ombres / f"retenues-{id_}.json").read_text()))
        except (ValueError, json.JSONDecodeError) as e:
            raise SystemExit(f"bilan_ombre : retenues-{id_}.json invalide : {e}")
        etapes.append({"id": id_, "liste_sha256": ombre.get("liste_sha256"), "remarques": remarques,
                       "chaine": ombre["chaine"]["result"], "cout": float(ombre["chaine"].get("cout_avec_haiku") or 0),
                       "cout_sonnet": float((ombre.get("sonnet") or {}).get("cout") or 0)})
    return etapes, laissees


def decider(n: int, rappel: Fraction, bugs: int, non_fondees: Fraction, cout: float) -> str:
    if bugs > PLAFOND_BUGS or non_fondees > PLAFOND_NON_FONDEES or cout > PLAFOND_COUT:
        return "statu quo"
    if rappel >= SEUIL_BASCULE:
        return "bascule"
    if rappel >= SEUIL_HYBRIDE:
        return "hybride"
    return "statu quo"


def calculer(etapes: list[dict], jugement: dict) -> tuple[list[list[str]], dict]:
    """Le tableau par étape et les totaux, à partir du juge. Le juge ne reçoit que la vérité et les rapports."""
    lignes, tot = [], {"den": 0, "pond": Fraction(0), "bugs": 0, "bruit": 0, "cout": 0.0}
    for e in etapes:
        rem = e["remarques"]
        j = jugement.get(e["id"], {})
        if "erreur" in j or "ref" not in j:
            raise RuntimeError(f"juge sans jugement pour l'étape {e['id']} : {j.get('erreur', 'absent')}")
        matchs = {x["n"]: x["match"] for x in j["ref"]}
        verites = verite(rem)
        pond = sum((POIDS[matchs.get(i, "non")] for i in range(1, len(verites) + 1)), Fraction(0))
        tot["den"] += len(verites)
        tot["pond"] += pond
        tot["bugs"] += sum(1 for i, r in enumerate(verites, 1)
                           if r.get("gravite", "autre").startswith("bug") and matchs.get(i, "non") == "non")
        bruit = sum(1 for r in rem if r["verdict"] in ("bruit", "écartée"))
        tot["bruit"] += bruit
        tot["cout"] += e["cout"]
        n_op = sum(1 for r in rem if r["origine"] == "opus")
        n_co = sum(1 for r in rem if r["origine"] == "commune" and r["verdict"] == "retenue")
        n_om = sum(1 for r in rem if r["origine"] == "ombre" and r["verdict"] == "réelle")
        rappel_etape = f"{float(pond / len(verites)) * 100:.0f} %" if verites else "—"
        lignes.append([e["id"], str(n_op + n_co), str(n_co + n_om + bruit), str(n_co), str(n_om), str(bruit),
                       str(n_op), rappel_etape, f"{e['cout']:.3f}", f"{e['cout_sonnet']:.3f}"])
    return lignes, tot


def tableau(lignes: list[list[str]]) -> str:
    entetes = ["étape", "Opus (retenues)", "ombre (total)", "communes", "ombre seule réelle", "ombre seule bruit",
               "Opus seul", "rappel", "coût ombre (dollars)", "coût Sonnet, à part (dollars)"]
    cols = [[h, *(l[i] for l in lignes)] for i, h in enumerate(entetes)]
    larg = [max(len(c) for c in col) for col in cols]
    rendu = [" | ".join(entetes[i].ljust(larg[i]) for i in range(len(entetes)))]
    rendu += [" | ".join(l[i].ljust(larg[i]) for i in range(len(entetes))) for l in lignes]
    return "\n".join(rendu)


def main(argv=None, *, donnees: Path | None = None, juger=None) -> int:
    ap = argparse.ArgumentParser(description="Bilan de l'ombre : règle de Q2 sur les étapes triées.")
    ap.add_argument("--depuis", help="ne compte que les ombres faites à partir de cette date (AAAA-MM-JJ)")
    ap.add_argument("--min-etapes", type=int, default=20, help="étapes triées minimum avant toute décision (défaut 20)")
    ap.add_argument("--source-json", help="lignes d'un journal exporté (même colonnes) : option réservée, non branchée")
    a = ap.parse_args(argv)
    if a.source_json:
        print("bilan_ombre : --source-json n'est pas encore branché (étape ultérieure)", file=sys.stderr)
        return 2

    dossier = (donnees or banc.DONNEES) / "ombres"
    etapes, laissees = charger(dossier, a.depuis) if dossier.is_dir() else ([], [])
    for l in laissees:
        print(f"laissée de côté : {l}")

    shas = {e["liste_sha256"] for e in etapes}
    if len(shas) > 1:
        print("bilan_ombre : versions mêlées, les étapes portent des liste_sha256 différents : "
              + ", ".join(str(s) for s in sorted(shas, key=str)) + " ; aucun bilan", file=sys.stderr)
        return 4

    n = len(etapes)
    if n < a.min_etapes:
        lignes, _ = calculer(etapes, {e["id"]: {"ref": [], "extras": []} for e in etapes}) if etapes else ([], None)
        lignes = [l[:7] + ["—"] + l[8:] for l in lignes]
        if lignes:
            print(tableau(lignes))
        print(f"étapes triées : {n} sur {a.min_etapes} demandées ; rappel non calculé, juge non appelé")
        print(f"DÉCISION : {PAS_ASSEZ}")
        return 3

    jugement = (juger or juger_par_juge)({e["id"]: reference(e["remarques"]) for e in etapes},
                                         {e["id"]: e["chaine"] for e in etapes})
    lignes, tot = calculer(etapes, jugement)
    rappel = tot["pond"] / tot["den"] if tot["den"] else Fraction(0)
    non_fondees = Fraction(tot["bruit"], n)
    cout = tot["cout"] / n
    decision = decider(n, rappel, tot["bugs"], non_fondees, cout)

    print(tableau(lignes))
    print(f"étapes comptées : {n} ; remarques retenues (dénominateur) : {tot['den']}")
    print(f"rappel de la chaîne : {float(rappel) * 100:.1f} % ({float(tot['pond']):g} captées)")
    print(f"bugs de correction manqués : {tot['bugs']} (plafond {PLAFOND_BUGS})")
    print(f"remarques de l'ombre seule jugées bruit par relecture : {float(non_fondees):.2f} (plafond {PLAFOND_NON_FONDEES})")
    print(f"coût moyen par relecture (Haiku + chaîne) : {cout:.3f} dollars (plafond {PLAFOND_COUT})")
    print(f"DÉCISION : {decision}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
