#!/usr/bin/env python3
"""Boucle d'amélioration de la liste de relecture (étape 7 du plan « Refonte des plugins par la checklist »).

Relève les lignes candidates (une remarque retenue que la chaîne a manquée, vue dans deux étapes de la même
catégorie), mesure chacune sur le jeu de validation (43 cas), et ne l'ajoute que si le rappel monte sans que le bruit
dépasse celui de l'A/A (deux relectures identiques, mesurées une fois et notées dans le journal).

Usage : boucle_liste.py --section NOM [--plafond-mois 5] [--dry-run] [--cron]
Codes : 0 rien à ajouter ; 10 une ligne ajoutée (PR ouverte) ; 1 erreur réelle (ou quota, hors cron) ;
        3 plafond de dépense du mois atteint ; 5 bilan de Q2 pas encore passé.
--cron : sort toujours en 0, avec [SILENT] ou une ligne de message. Un code non nul ferait compter chaque passage
        comme un échec du superviseur (contrat des crons de dérive).

Quota du fournisseur (HTTP 402, « out of extra usage », plafond de dépense) : le texte du service passe tel quel dans
la sortie, une seule fois (état « signalé » dans le journal) ; ensuite [SILENT] jusqu'au premier succès. Rien n'est
compté contre le plafond.

Journal (`journal-checklist.md`) : une section `## NOM` par liste ou par plan, des entrées `### AAAA-MM-JJ — titre`
dont les puces ont une clé fixe (`- Coût : N dollars`, `- Quota : signalé|levé`, `- Ligne candidate : …`, etc.). Ce
format est l'interface que P3 réutilise (`--section Enquête`) : ne pas le changer sans lui.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import banc

PLAFOND_MOIS = 5.0
CODE_OK, CODE_PR, CODE_ERREUR, CODE_PLAFOND, CODE_BILAN = 0, 10, 1, 3, 5
SILENCE = "[SILENT]"
ICI = Path(__file__).resolve().parent
DEPOT = ICI.parents[1]
JOURNAL = ICI / "journal-checklist.md"
LISTE_REL = "plugins/plans-notion/skills/_partage/listes/relecture-code.md"
CAS_VALIDATION = "cas-ref-validation.json"
REF_VALIDATION = "ref-validation.json"
LETTRES = "ABCDEFGH"
POIDS = {"oui": 1.0, "partiel": 0.5, "non": 0.0}
RE_QUOTA = re.compile(r"402|out of extra usage|plafond de dépense|spending (?:cap|limit)|usage limit", re.I)

RE_BILAN = re.compile(r"^Bilan de Q2 : (\d{4}-\d{2}-\d{2})\s*$", re.M)
RE_ENTREE = re.compile(r"^### (\d{4}-\d{2}-\d{2})\b")
RE_COUT = re.compile(r"^- Coût : ([\d.]+) dollars\s*$")
RE_BASE = re.compile(r"^- Mesure de base : rappel ([\d.]+) ; bruit ([\d.]+) ; liste ([0-9a-f]{64})\s*$")
RE_AA = re.compile(r"^- Bruit A/A : ([\d.]+)\s*$")
RE_QUOTA_J = re.compile(r"^- Quota : (signalé|levé)\s*$")
RE_CANDIDAT = re.compile(r"^- Ligne candidate : (.+?)\s*$")


@dataclass(frozen=True)
class Mesure:
    rappel: float
    bruit: float
    cout: float


@dataclass(frozen=True)
class Candidat:
    categorie: str
    ligne: str


@dataclass(frozen=True)
class Resultat:
    code: int
    lignes: list
    silencieux: bool = False


class QuotaAtteint(Exception):
    pass


class Souci(RuntimeError):
    pass


# --- Journal : lecture et écriture, sans état caché -----------------------------------------------------------------

def bilan_q2(texte: str) -> str | None:
    m = RE_BILAN.search(texte)
    return m.group(1) if m else None


def lignes_section(texte: str, section: str) -> list[str] | None:
    """Les lignes de `## <section>` jusqu'à la section suivante, ou None si elle n'existe pas."""
    lignes = texte.split("\n")
    debut = next((i + 1 for i, l in enumerate(lignes) if l.startswith("## ") and l[3:].strip() == section), None)
    if debut is None:
        return None
    fin = next((j for j in range(debut, len(lignes)) if lignes[j].startswith("## ")), len(lignes))
    return lignes[debut:fin]


def dernier(lignes: list[str], regex: re.Pattern) -> tuple | None:
    """Les groupes de la dernière ligne qui correspond : la plus récente l'emporte."""
    trouve = None
    for l in lignes:
        m = regex.match(l)
        if m:
            trouve = m.groups()
    return trouve


def cout_du_mois(texte: str, mois: str) -> float:
    """Le coût cumulé du mois (AAAA-MM), toutes sections confondues : somme des puces `- Coût` des entrées du mois."""
    total, date = 0.0, None
    for l in texte.split("\n"):
        if l.startswith("## "):
            date = None
        m = RE_ENTREE.match(l)
        if m:
            date = m.group(1)
        m = RE_COUT.match(l)
        if m and date and date.startswith(mois):
            total += float(m.group(1))
    return total


def candidats_journalises(texte: str) -> set[str]:
    trouves = set()
    for l in texte.split("\n"):
        m = RE_CANDIDAT.match(l)
        if m:
            trouves.add(m.group(1))
    return trouves - {"aucune"}


def ajouter_entree(texte: str, section: str, date: str, titre: str, puces: list[str]) -> str:
    """Ajoute une entrée à la fin de sa section, avant la section suivante."""
    lignes = texte.split("\n")
    debut = next((i for i, l in enumerate(lignes) if l.startswith("## ") and l[3:].strip() == section), None)
    if debut is None:
        raise Souci(f"section « {section} » absente du journal")
    fin = next((j for j in range(debut + 1, len(lignes)) if lignes[j].startswith("## ")), len(lignes))
    k = fin
    while k > debut + 1 and not lignes[k - 1].strip():
        k -= 1
    lignes[k:k] = ["", f"### {date} — {titre}", *puces]
    return "\n".join(lignes)


def inserer_ligne(liste: str, categorie: str, ligne: str) -> str:
    """Ajoute une ligne numérotée à la fin de la catégorie (lettre A à H) de la liste de relecture."""
    lignes = liste.split("\n")
    debut = next((i for i, l in enumerate(lignes) if l.startswith(f"{categorie}. ")), None)
    if debut is None:
        raise Souci(f"catégorie {categorie} absente de la liste de relecture")
    fin = len(lignes)
    for j in range(debut + 1, len(lignes)):
        if re.match(r"[A-Z]\. ", lignes[j]) or lignes[j].startswith("Rends le verdict"):
            fin = j
            break
    k = fin
    while k > debut + 1 and not lignes[k - 1].strip():
        k -= 1
    n = sum(1 for l in lignes[debut:k] if re.match(r"\s+\d+\. ", l)) + 1
    lignes[k:k] = [f"   {n}. {ligne}"]
    return "\n".join(lignes)


def mesure_depuis_jugement(jugement: dict, ref: dict, cout: float) -> Mesure:
    """Rappel pondéré (oui 1, partiel 0,5, non 0) et bruit moyen par relecture, à partir du jugement de juge.py."""
    num = den = 0.0
    bruit = 0
    for cas, items in ref.items():
        j = jugement.get(cas)
        if j is None or "erreur" in j or "ref" not in j:
            raise Souci(f"juge sans jugement pour le cas {cas}")
        matchs = {x["n"]: x["match"] for x in j["ref"]}
        den += len(items)
        num += sum(POIDS.get(matchs.get(o["n"], "non"), 0.0) for o in items)
        bruit += sum(1 for e in j.get("extras", []) if e.get("verdict") != "réelle")
    n = len(ref)
    return Mesure(rappel=num / den if den else 0.0, bruit=bruit / n if n else 0.0, cout=round(cout, 4))


# --- Dépendances réelles (non jouées par les tests) -----------------------------------------------------------------

class Dependances:
    """Le journal est un vrai fichier ; la liste, les mesures et les PR passent par le banc et git."""

    def __init__(self, journal: Path = JOURNAL):
        self.journal = journal
        self._liste = None

    def lire_journal(self) -> str:
        return self.journal.read_text()

    def ecrire_journal(self, texte: str) -> None:
        self.journal.write_text(texte)

    def jeu_present(self) -> bool:
        return (banc.DONNEES / REF_VALIDATION).is_file() and (banc.DONNEES / CAS_VALIDATION).is_file()

    def liste_texte(self) -> str:
        """La liste telle qu'elle est sur origin/main : c'est elle que la boucle mesure et amende."""
        if self._liste is None:
            f = subprocess.run(["git", "-C", str(DEPOT), "fetch", "--quiet", "origin", "main"],
                               capture_output=True, text=True)
            if f.returncode != 0:
                raise Souci(f"fetch de origin/main en échec : {f.stderr.strip()[-200:]}")
            r = subprocess.run(["git", "-C", str(DEPOT), "show", f"origin/main:{LISTE_REL}"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise Souci(f"liste de relecture illisible sur origin/main : {r.stderr.strip()[-200:]}")
            self._liste = r.stdout
        return self._liste

    def liste_sha(self) -> str:
        return hashlib.sha256(self.liste_texte().encode()).hexdigest()

    def liste_avec(self, candidat: Candidat) -> str:
        return inserer_ligne(self.liste_texte(), candidat.categorie, candidat.ligne)

    def mesurer(self, liste: str, bras: str) -> Mesure:
        """Une relecture Haiku high sur les 43 cas, puis le juge. Coûte de l'argent : le cron seul l'appelle."""
        dossier = banc.DONNEES / "listes-boucle"
        dossier.mkdir(parents=True, exist_ok=True)
        fichier = dossier / f"{bras}.md"
        fichier.write_text(liste)
        r = subprocess.run([sys.executable, str(banc.ICI / "rejouer.py"), bras, "claude-haiku-5-5", "high",
                            str(PLAFOND_MOIS), "--cas", CAS_VALIDATION, "--liste", str(fichier)],
                           cwd=banc.ICI, capture_output=True, text=True)
        sorties = {f.stem: json.loads(f.read_text()) for f in (banc.DONNEES / "sorties" / bras).glob("*.json")}
        for d in sorties.values():
            erreur = d.get("erreur") or (d.get("result") if d.get("is_error") else None)
            if erreur and RE_QUOTA.search(str(erreur)):
                raise QuotaAtteint(str(erreur)[:300])
        if r.returncode != 0 or not sorties:
            raise Souci(f"rejouer.py en échec pour {bras} : {(r.stderr or r.stdout).strip()[-300:]}")
        cout = sum(float(d.get("total_cost_usd") or 0) for d in sorties.values())
        j = subprocess.run([sys.executable, str(banc.ICI / "juge.py"), f"{bras}.json", bras, "--ref", REF_VALIDATION],
                           cwd=banc.ICI, capture_output=True, text=True)
        if j.returncode != 0:
            raise Souci(f"juge.py en échec pour {bras} : {(j.stderr or j.stdout).strip()[-300:]}")
        m = re.search(r"coût juge ([\d.]+)", j.stdout)
        cout += float(m.group(1)) if m else 0.0
        return mesure_depuis_jugement(banc.charger(f"jugements/{bras}.json"), banc.charger(REF_VALIDATION), cout)

    def candidats(self) -> list[Candidat]:
        """Remarques retenues par Opus seul (la chaîne les a manquées), de même catégorie, dans deux étapes au moins."""
        vues: dict[tuple[str, str], tuple[str, set]] = {}
        for f in sorted((banc.DONNEES / "ombres").glob("retenues-*.json")):
            d = json.loads(f.read_text())
            for r in d.get("remarques", []):
                cat = r.get("categorie")
                resume = " ".join(str(r.get("resume", "")).split())
                if r.get("origine") != "opus" or cat not in list(LETTRES) or not resume:
                    continue
                cle = (cat, resume.casefold())
                vues.setdefault(cle, (resume, set()))[1].add(d.get("id", f.name))
        return [Candidat(categorie=cat, ligne=resume[:200])
                for (cat, _), (resume, ids) in vues.items() if len(ids) >= 2]

    def ouvrir_pr(self, candidat: Candidat, iso: str) -> str:
        # Non écrit à cette étape : la PR (branche, garde, bump de plans-notion, corps) reste à éprouver avant le cron.
        raise Souci("ouverture de PR non branchée : à écrire et éprouver avant le cron")


# --- Décision -------------------------------------------------------------------------------------------------------

def _plafond_atteint(cout: float, plafond: float) -> Resultat:
    return Resultat(CODE_PLAFOND, [f"plafond atteint : {cout:.2f} dollars ce mois-ci (plafond {plafond:g}) ; "
                                   "arrêt avant la mesure suivante"])


def _a_mesurer(texte: str, deps) -> list[Candidat]:
    deja = candidats_journalises(texte)
    return [c for c in deps.candidats() if c.ligne not in deja]


def executer(section, deps, aujourdhui, plafond=PLAFOND_MOIS, dry_run=False) -> Resultat:
    texte = deps.lire_journal()
    bilan = bilan_q2(texte)
    if bilan is None or bilan > aujourdhui.isoformat():
        return Resultat(CODE_BILAN, ["bilan de Q2 pas encore passé : la ligne « Bilan de Q2 : AAAA-MM-JJ » "
                                     "manque au journal"], silencieux=True)
    if lignes_section(texte, section) is None:
        return Resultat(CODE_ERREUR, [f"section « {section} » absente du journal"])
    if not deps.jeu_present():
        return Resultat(CODE_ERREUR, ["jeu de validation absent (ref-validation.json ou "
                                      "cas-ref-validation.json dans BANC_DONNEES)"])
    cout = cout_du_mois(texte, aujourdhui.strftime("%Y-%m"))
    if cout >= plafond:
        return _plafond_atteint(cout, plafond)
    if dry_run:
        return Resultat(CODE_OK, [f"dry-run : aucune mesure, aucune PR ; candidats à mesurer : "
                                  f"{len(_a_mesurer(texte, deps))}"])
    try:
        return _boucle(section, deps, aujourdhui, plafond)
    except QuotaAtteint as q:
        return _quota(section, deps, aujourdhui, str(q))
    except Souci as s:
        return Resultat(CODE_ERREUR, [f"souci : {s}"])


def _quota(section, deps, aujourdhui, texte_service: str) -> Resultat:
    texte = deps.lire_journal()
    etat = dernier(lignes_section(texte, section), RE_QUOTA_J)
    if etat and etat[0] == "signalé":
        return Resultat(CODE_ERREUR, ["quota du fournisseur toujours atteint : rien mesuré, rien compté"],
                        silencieux=True)
    deps.ecrire_journal(ajouter_entree(texte, section, aujourdhui.isoformat(), "quota du fournisseur atteint",
                                       ["- Quota : signalé"]))
    return Resultat(CODE_ERREUR, [f"{' '.join(texte_service.split())} — quota du fournisseur atteint : "
                                  "rien mesuré, rien compté contre le plafond"])


def _boucle(section, deps, aujourdhui, plafond) -> Resultat:
    iso, mois = aujourdhui.isoformat(), aujourdhui.strftime("%Y-%m")
    texte = deps.lire_journal()
    sec = lignes_section(texte, section)
    sha, liste = deps.liste_sha(), deps.liste_texte()
    en_attente = ["- Quota : levé"] if dernier(sec, RE_QUOTA_J) == ("signalé",) else []

    def noter(titre, puces):
        nonlocal en_attente
        deps.ecrire_journal(ajouter_entree(deps.lire_journal(), section, iso, titre, en_attente + puces))
        en_attente = []

    def arret():
        c = cout_du_mois(deps.lire_journal(), mois)
        return _plafond_atteint(c, plafond) if c >= plafond else None

    def puces_base(m):
        return [f"- Mesure de base : rappel {m.rappel:.3f} ; bruit {m.bruit:.3f} ; liste {sha}",
                f"- Coût : {m.cout:.3f} dollars"]

    bruit_aa = dernier(sec, RE_AA)
    base = None
    for groupes in (dernier([l], RE_BASE) for l in sec):
        if groupes and groupes[2] == sha:
            base = (float(groupes[0]), float(groupes[1]))
    if bruit_aa is None:
        if (r := arret()) is not None:
            return r
        m1 = deps.mesurer(liste, "base-1")
        noter("mesure de base, bras 1", puces_base(m1))
        if (r := arret()) is not None:
            return r
        m2 = deps.mesurer(liste, "base-2")
        aa = abs(m1.bruit - m2.bruit)
        noter("mesure de base, bras 2 et bruit A/A", puces_base(m2) + [f"- Bruit A/A : {aa:.3f}"])
        bruit_aa, base = aa, (m2.rappel, m2.bruit)
    else:
        bruit_aa = float(bruit_aa[0])
        if base is None:
            if (r := arret()) is not None:
                return r
            m = deps.mesurer(liste, "base-1")
            noter("mesure de base", puces_base(m))
            base = (m.rappel, m.bruit)

    for c in _a_mesurer(texte, deps):
        if (r := arret()) is not None:
            return r
        bras = f"cand-{hashlib.sha1(c.ligne.encode()).hexdigest()[:8]}"
        m = deps.mesurer(deps.liste_avec(c), bras)
        gain, hausse = m.rappel - base[0], m.bruit - base[1]
        retenue = gain > 0 and hausse <= bruit_aa
        noter(f"candidat « {c.ligne[:60]} »", [
            f"- Ligne candidate : {c.ligne}", f"- Catégorie : {c.categorie}",
            f"- Mesure : rappel {m.rappel:.3f} ; bruit {m.bruit:.3f} ; gain {gain:+.3f} ; hausse de bruit {hausse:+.3f}",
            f"- Décision : {'retenue' if retenue else 'refusée'}", f"- Coût : {m.cout:.3f} dollars"])
        if retenue:
            try:
                url = deps.ouvrir_pr(c, iso)
            except Souci as s:
                noter("PR non ouverte", [f"- PR : échec — {s}"])
                raise
            noter("PR ouverte", [f"- PR : {url}"])
            return Resultat(CODE_PR, [f"ligne ajoutée à la catégorie {c.categorie} : {c.ligne} — PR {url}"])
    return Resultat(CODE_OK, [], silencieux=True)


def main(argv=None, *, deps=None, aujourdhui=None) -> int:
    ap = argparse.ArgumentParser(description="Boucle d'amélioration de la liste de relecture : une ligne mesurée, "
                                             "ajoutée par PR seulement si elle passe.")
    ap.add_argument("--section", required=True, help="section du journal (« Code » pour la liste de relecture)")
    ap.add_argument("--plafond-mois", type=float, default=PLAFOND_MOIS,
                    help="dépense maximale par mois, toutes sections confondues (défaut 5)")
    ap.add_argument("--dry-run", action="store_true",
                    help="vérifie bilan, jeu, plafond et quota, sans rien mesurer ni ouvrir de PR")
    ap.add_argument("--cron", action="store_true", help="sort toujours en 0 : [SILENT] ou une ligne de message")
    a = ap.parse_args(argv)
    deps = deps if deps is not None else Dependances()
    aujourdhui = aujourdhui or datetime.date.today()
    try:
        r = executer(a.section, deps, aujourdhui, a.plafond_mois, a.dry_run)
    except OSError as e:
        r = Resultat(CODE_ERREUR, [f"journal illisible : {e}"])
    if a.cron:
        if r.silencieux or not r.lignes:
            print(SILENCE)
        else:
            for l in r.lignes:
                print(l)
        return 0
    for l in r.lignes:
        print(l)
    return r.code


if __name__ == "__main__":
    sys.exit(main())
