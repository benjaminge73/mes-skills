#!/usr/bin/env python3
"""Coût réel d'un plan Notion : les sessions qui le citent, leurs tokens, leurs dollars.

Usage : cout-plan.py --page <identifiant Notion> [--projets <dossier>] [--grille <json>]

1. Les sessions du plan : les journaux ``<projets>/**/*.jsonl`` dont un appel
   d'outil (``tool_use``) cite l'identifiant de la page, tirets facultatifs. Un
   journal de sous-agent (``<session>/subagents/*.jsonl``) compte pour sa session.
   Une mention dans un résultat d'outil (une recherche qui liste la page) ne compte pas.
2. Les tokens : ``ccusage session --json``, sous-agents compris, filtré sur ces
   sessions. Le ``cost`` de ccusage n'est pas repris : les dollars se recalculent.
3. Les dollars : les tokens de chaque modèle multipliés par ``grille-tarifs.json``.
   Les écritures de cache se chiffrent à la part 1 h mesurée par modèle dans les
   journaux des sessions retenues (``ventilation_des_ecritures``). Un modèle sans
   ventilation dans les journaux reste au tarif 5 min, et sa ligne le dit.
   Un modèle absent de la grille est listé à part, « non chiffré », et exclu du
   total : jamais un zéro silencieux.

Codes de sortie : 0 rendu ; 1 aucune session ne cite la page, ou aucune n'a de
tokens chez ccusage ; 2 ccusage, la grille ou le dossier de journaux indisponible
(message sur stderr, pas de trace Python).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

CCUSAGE_VERSION = "20.0.30"
GRILLE_PAR_DEFAUT = Path(__file__).resolve().parent / "grille-tarifs.json"
PROJETS_PAR_DEFAUT = Path.home() / ".claude" / "projects"

# ccusage ne sépare pas l'écriture de cache 5 min de celle de 1 h (sortie de
# `ccusage session --json`, vérifiée le 2026-10-12). Les journaux, eux, la
# ventilent (champ `cache_creation` de chaque message assistant). Mesuré le
# 2026-10-12 sur les journaux des 30 derniers jours : les sessions pilotes
# écrivent 100 % en 1 h, les sous-agents 100 % en 5 min, quel que soit le
# modèle. D'où une part 1 h mesurée par modèle sur les sessions retenues, et
# appliquée aux écritures de ccusage (les tokens restent ceux de ccusage).
TARIF_5_MIN = "ecriture_cache_5m"
TARIF_1_H = "ecriture_cache_1h"

# (champ de modelBreakdowns dans ccusage, champ de prix dans la grille, libellé d'affichage)
# Les écritures de cache ont un champ de tokens, mais pas de prix propre : leur
# prix se mélange selon la part 1 h (voir prix_ecriture).
COLONNES = [
    ("inputTokens", "entree", "entrée"),
    ("outputTokens", "sortie", "sortie"),
    ("cacheReadTokens", "lecture_cache", "lecture cache"),
    ("cacheCreationTokens", "ecriture_cache", "écriture cache"),
]
CHAMPS_PRIX = ["entree", "sortie", "lecture_cache", TARIF_5_MIN, TARIF_1_H]

ID_NOTION = re.compile(r"^[0-9a-f]{32}$")


def erreur(message: str, code: int) -> None:
    print(message, file=sys.stderr)
    sys.exit(code)


def identifiant(valeur: str) -> str:
    nu = valeur.replace("-", "").lower()
    if not ID_NOTION.match(nu):
        raise argparse.ArgumentTypeError(
            f"« {valeur} » n'est pas un identifiant Notion (32 caractères hexadécimaux, "
            "tirets facultatifs)")
    return nu


def motif_de_la_page(page_nu: str) -> re.Pattern:
    """Le motif qui trouve l'identifiant avec ou sans tirets, quelle que soit la casse."""
    morceaux = [page_nu[0:8], page_nu[8:12], page_nu[12:16], page_nu[16:20], page_nu[20:32]]
    return re.compile("-?".join(morceaux), re.IGNORECASE)


def session_du_journal(chemin: Path) -> str:
    if chemin.parent.name == "subagents":
        return chemin.parent.parent.name
    return chemin.stem


def cite_dans_un_appel(ligne: str, motif: re.Pattern) -> bool:
    try:
        objet = json.loads(ligne)
    except ValueError:
        return False
    if not isinstance(objet, dict):
        return False
    contenu = (objet.get("message") or {}).get("content")
    if not isinstance(contenu, list):
        return False
    for morceau in contenu:
        if isinstance(morceau, dict) and morceau.get("type") == "tool_use":
            if motif.search(json.dumps(morceau.get("input", {}), ensure_ascii=False)):
                return True
    return False


def sessions_qui_citent(projets: Path, motif: re.Pattern) -> set[str]:
    trouvees: set[str] = set()
    for chemin in sorted(projets.rglob("*.jsonl")):
        with chemin.open(encoding="utf-8", errors="replace") as h:
            for ligne in h:
                if motif.search(ligne) and cite_dans_un_appel(ligne, motif):
                    trouvees.add(session_du_journal(chemin))
                    break
    return trouvees


def ventilation_des_ecritures(projets: Path, sessions: set[str]) -> dict[str, dict[str, int]]:
    """Par modèle, les écritures de cache 5 min (« 5m ») et 1 h (« 1h ») des journaux des ``sessions``.

    Un message écrit plusieurs fois dans un journal (une ligne par bloc de
    contenu) compte une fois, par ``message.id`` : même règle que le barème.
    Un modèle n'apparaît que si un de ses messages porte un des deux champs.
    """
    vus: set[tuple[str, str]] = set()
    sommes: dict[str, dict[str, int]] = {}
    for chemin in sorted(projets.rglob("*.jsonl")):
        session = session_du_journal(chemin)
        if session not in sessions:
            continue
        with chemin.open(encoding="utf-8", errors="replace") as h:
            for ligne in h:
                if "cache_creation" not in ligne:
                    continue
                try:
                    objet = json.loads(ligne)
                except ValueError:
                    continue
                message = objet.get("message") if isinstance(objet, dict) else None
                if not isinstance(message, dict):
                    continue
                usage = message.get("usage")
                cache = usage.get("cache_creation") if isinstance(usage, dict) else None
                modele = message.get("model")
                if not isinstance(cache, dict) or not isinstance(modele, str):
                    continue
                cinq = cache.get("ephemeral_5m_input_tokens")
                heure = cache.get("ephemeral_1h_input_tokens")
                if cinq is None and heure is None:
                    continue
                ident = message.get("id")
                if ident is not None:
                    if (session, ident) in vus:
                        continue
                    vus.add((session, ident))
                t = sommes.setdefault(modele, {"5m": 0, "1h": 0})
                t["5m"] += int(cinq or 0)
                t["1h"] += int(heure or 0)
    return sommes


def part_une_heure(ventilation: dict[str, int] | None) -> float | None:
    """La part 1 h des écritures d'un modèle, ou None si les journaux ne la donnent pas."""
    if not ventilation:
        return None
    total = ventilation["5m"] + ventilation["1h"]
    if total <= 0:
        return None
    return ventilation["1h"] / total


def prix_ecriture(tarifs_modele: dict[str, float], part: float | None) -> float:
    """Le prix du million d'écritures de cache : le mélange des deux tarifs selon la part 1 h."""
    p5 = tarifs_modele[TARIF_5_MIN]
    if part is None:
        return p5
    return part * tarifs_modele[TARIF_1_H] + (1 - part) * p5


def commande_ccusage() -> list[str]:
    exe = shutil.which("ccusage")
    if exe:
        return [exe]
    if shutil.which("npx"):
        return ["npx", "-y", f"ccusage@{CCUSAGE_VERSION}"]
    erreur("cout-plan : ccusage est absent du PATH. L'installer avec "
           f"« npm i -g ccusage@{CCUSAGE_VERSION} ».", 2)
    raise SystemExit(2)  # inatteignable : erreur() sort ; garde pour le lecteur


def sessions_ccusage() -> list[dict]:
    cmd = [*commande_ccusage(), "session", "--json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        erreur("cout-plan : ccusage n'a pas répondu en 10 minutes.", 2)
    except OSError as e:
        erreur(f"cout-plan : impossible de lancer ccusage ({e}).", 2)
    if r.returncode != 0:
        derniere = (r.stderr.strip().splitlines() or ["(pas de message)"])[-1]
        erreur(f"cout-plan : ccusage a échoué (code {r.returncode}) : {derniere}", 2)
    try:
        return json.loads(r.stdout)["session"]
    except (ValueError, KeyError, TypeError):
        erreur("cout-plan : la sortie de ccusage n'est pas le JSON attendu (clé « session » absente).", 2)
    raise SystemExit(2)


def charger_grille(chemin: Path) -> tuple[dict, str]:
    try:
        grille = json.loads(chemin.read_text(encoding="utf-8"))
        tarifs = {}
        for nom, prix in grille["modeles"].items():
            tarifs[nom] = {champ: float(prix[champ]["prix"]) for champ in CHAMPS_PRIX}
        return tarifs, str(grille.get("releve", "date inconnue"))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        erreur(f"cout-plan : grille illisible ({chemin}) : {e}", 2)
    raise SystemExit(2)


def fmt_tokens(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def fmt_usd(x: float) -> str:
    return f"{x:,.4f}".replace(",", " ").replace(".", ",") + " $"


def fmt_pourcent(x: float) -> str:
    return f"{x * 100:.1f}".replace(".", ",") + " %"


def ligne_de_tokens(nom: str, t: dict) -> str:
    return f"  {nom} | " + " | ".join(
        f"{libelle} {fmt_tokens(t[champ])}" for _, champ, libelle in COLONNES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coût réel d'un plan Notion (sessions, tokens, dollars).")
    parser.add_argument("--page", type=identifiant, required=True,
                        help="identifiant Notion de la page du plan (tirets facultatifs)")
    parser.add_argument("--projets", type=Path, default=PROJETS_PAR_DEFAUT,
                        help="dossier des journaux (défaut : ~/.claude/projects)")
    parser.add_argument("--grille", type=Path, default=GRILLE_PAR_DEFAUT,
                        help="grille de tarifs (défaut : grille-tarifs.json à côté du script)")
    args = parser.parse_args(argv)

    tarifs, releve = charger_grille(args.grille)
    if not args.projets.is_dir():
        erreur(f"cout-plan : dossier de journaux absent ({args.projets}).", 2)

    citantes = sessions_qui_citent(args.projets, motif_de_la_page(args.page))
    if not citantes:
        erreur(f"cout-plan : aucune session ne cite la page {args.page} dans {args.projets}.", 1)

    retenues = [s for s in sessions_ccusage() if s.get("period") in citantes]
    avec_tokens = {s["period"] for s in retenues}
    if not avec_tokens:
        erreur(f"cout-plan : {len(citantes)} session(s) citent la page, aucune n'a de tokens chez ccusage.", 1)

    totaux: dict[str, dict[str, int]] = {}
    lignes_sessions = []
    for s in sorted(retenues, key=lambda s: str(s.get("period"))):
        modeles = set()
        for b in s.get("modelBreakdowns") or []:
            nom = str(b.get("modelName", "?"))
            modeles.add(nom)
            t = totaux.setdefault(nom, {champ: 0 for _, champ, _ in COLONNES})
            for cle_ccusage, champ, _ in COLONNES:
                t[champ] += int(b.get(cle_ccusage) or 0)
        activite = str((s.get("metadata") or {}).get("lastActivity", ""))[:10] or "date inconnue"
        lignes_sessions.append(
            f"  {s['period']} | dernière activité {activite} | modèles : {', '.join(sorted(modeles)) or 'aucun'}")
    sans_donnees = sorted(citantes - avec_tokens)

    chiffres = {nom: t for nom, t in totaux.items() if nom in tarifs}
    hors_grille = {nom: t for nom, t in totaux.items() if nom not in tarifs}
    ventilations = ventilation_des_ecritures(args.projets, avec_tokens)
    total = 0.0
    lignes_modeles = []
    for nom in sorted(chiffres):
        t = chiffres[nom]
        part = part_une_heure(ventilations.get(nom))
        cout = (sum(t[champ] * tarifs[nom][champ] for champ in ("entree", "sortie", "lecture_cache"))
                + t["ecriture_cache"] * prix_ecriture(tarifs[nom], part)) / 1_000_000
        total += cout
        if part is None:
            statut = "écriture cache au tarif 5 min, ventilation absente"
        else:
            statut = f"part 1 h {fmt_pourcent(part)}"
        lignes_modeles.append(ligne_de_tokens(nom, t) + f" | {statut} | {fmt_usd(cout)}")

    sortie = [
        f"Plan {args.page} : {len(citantes)} session(s) citent la page, {len(avec_tokens)} avec des tokens chez ccusage.",
        "Sessions retenues (sous-agents compris) :",
        *lignes_sessions,
    ]
    for sid in sans_donnees:
        sortie.append(f"  {sid} | sans donnée ccusage (non comptée)")
    sortie.append(f"Par modèle (grille du {releve}, dollars par million de tokens) :")
    sortie.extend(lignes_modeles or ["  (aucun modèle chiffrable)"])
    if hors_grille:
        sortie.append("Modèles hors grille (non chiffrés, exclus du total) :")
        for nom in sorted(hors_grille):
            sortie.append(ligne_de_tokens(nom, hors_grille[nom]) + " | non chiffré")
    sortie.append(f"Total chiffré | {fmt_usd(total)}")
    print("\n".join(sortie))
    return 0


if __name__ == "__main__":
    sys.exit(main())
