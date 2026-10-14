#!/usr/bin/env python3
"""Vérifie que chaque réponse tranchée d'un plan porte une preuve conforme.

Pourquoi un script : la règle « une réponse sans preuve est une opinion » (poc.md,
« La preuve de chaque réponse ») ne tenait que par la discipline de celui qui
écrit la ligne ``Preuve :``. Un POC cité avec un mauvais modèle, une dispense
sans raison ou une lecture vers un fichier absent passaient à la validation sans
que rien ne le voie. Le script relit la page (miroir Notion ou plan natif) et
rend un écart par réponse non conforme.

Usage : verifier-preuves.py <page.md> [--format notion|natif] [--depot <dir>]
                            [--transcripts [<racine>]]
  --format notion (défaut) : sous « Questions ouvertes », chaque H3 « Qn » est une
    question ; une question dont le titre porte 🧭 est ouverte, non contrôlée.
  --format natif : sous « Décisions », chaque ligne « D<n> » est une décision, et
    sa ligne porte la preuve.
  --depot <dir> : le fichier cité par une ``lecture`` doit exister dans le dépôt,
    tel quel ou comme suffixe de chemin d'un fichier du dépôt. Un chemin externe
    (URL, ~, /, domaine) n'est pas cherché ; il lui faut un détail.
  --transcripts [<racine>] : pour un POC, lance modele-sous-agent.py en
    sous-processus et compare le modèle servi au modèle cité. Sans valeur : la
    racine par défaut de modele-sous-agent.py. Sans l'option, les POC ne sont pas
    vérifiés (une note sur la sortie d'erreur).
Codes : 0 conforme (ou aucune réponse tranchée à contrôler) ; 1 un écart par
ligne, sur la sortie standard ; 2 entrée illisible (page, section ou réponse
absente).
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

TYPES = ("POC", "commande", "lecture", "dispense")
AGENTS_POC = ("plans-notion:sondeur", "plans-notion:evaluateur")
QUESTION = re.compile(r"^###\s+.*?\b(Q\d+)\b")
DECISION = re.compile(r"^\s*(?:[-*]\s+)?(D\d+)\b")
PREUVE_EN_TETE = re.compile(r"^\s*Preuve\s*:")
CHEMIN = re.compile(r"([\w./~\-]+):(\d+)(?:-(\d+))?")
# Premier jeton d'un chemin, schéma compris (https://), avant tout « :ligne ».
CHEMIN_NU = re.compile(r"((?:\w+://)?[\w./~\-]+)")
DOMAINE = re.compile(r"[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}/")
HEXA = re.compile(r"[0-9a-fA-F]{6,}")
MODELE_SERVI = re.compile(r"^\s*\d+ × (\S+)")
MODELE_SOUS_AGENT = Path(__file__).resolve().parent / "modele-sous-agent.py"


class Illisible(Exception):
    """Entrée qui ne permet pas de contrôler (code 2)."""


@dataclass
class Reponse:
    ident: str
    bloc: list[str] = field(default_factory=list)
    ouverte: bool = False
    natif: bool = False


def extraire_notion(texte: str) -> list[Reponse]:
    reponses: list[Reponse] = []
    dans_section = trouvee = False
    courante: Reponse | None = None
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dans_section = ligne[3:].strip().lower().startswith("questions ouvertes")
            trouvee = trouvee or dans_section
            courante = None
            continue
        if not dans_section:
            continue
        if ligne.startswith("### "):
            m = QUESTION.match(ligne)
            courante = Reponse(m.group(1), ouverte="🧭" in ligne) if m else None
            if courante is not None:
                reponses.append(courante)
            continue
        if courante is not None:
            courante.bloc.append(ligne)
    if not trouvee:
        raise Illisible("section « Questions ouvertes » absente")
    if not reponses:
        raise Illisible("aucune question trouvée sous « Questions ouvertes »")
    return reponses


def extraire_natif(texte: str) -> list[Reponse]:
    decisions: list[Reponse] = []
    dans_section = trouvee = False
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dans_section = ligne[3:].strip().lower().startswith("décisions")
            trouvee = trouvee or dans_section
            continue
        m = DECISION.match(ligne) if dans_section else None
        if m is not None:
            decisions.append(Reponse(m.group(1), [ligne], natif=True))
    if not trouvee:
        raise Illisible("section « Décisions » absente")
    if not decisions:
        raise Illisible("aucune décision D<n> sous « Décisions »")
    return decisions


def apres_tiret(reste: str) -> str:
    """Le texte qui suit le tiret (— ou -) après le type ; vide s'il n'y a pas de tiret."""
    m = re.match(r"\s*[—-]\s*(.*)", reste, re.S)
    return m.group(1).strip() if m else ""


def externe(chemin: str, ligne: str) -> bool:
    """Chemin hors dépôt (URL, ~, /, nom de domaine, « hors dépôt ») : pas de contrôle."""
    return (chemin.startswith(("~", "/")) or "://" in ligne or "hors dépôt" in ligne
            or DOMAINE.match(chemin) is not None)


def detail_apres(apres: str) -> str:
    """Le détail qui suit un chemin : le « :ligne » éventuel et les parenthèses ôtés."""
    return re.sub(r"^:\d+(?:-\d+)?", "", apres).strip().strip("()").strip()


def meme_modele(cite: str, servi: str) -> bool:
    cite, servi = cite.lower(), servi.lower()
    return cite in servi or servi in cite


class Depot:
    """Fichiers du dépôt, pour contrôler une lecture. Sans --depot, rien n'est contrôlé."""

    def __init__(self, racine: Path | None):
        self.racine = racine
        self._fichiers: list[str] | None = None

    def contient(self, chemin: str) -> bool:
        if self.racine is None:
            return True
        chemin = chemin.removeprefix("./")
        if (self.racine / chemin).is_file():
            return True
        if self._fichiers is None:
            self._fichiers = self._lister()
        return any(f == chemin or f.endswith("/" + chemin) for f in self._fichiers)

    def _lister(self) -> list[str]:
        fichiers = []
        for dossier, dirs, noms in os.walk(self.racine):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for nom in noms:
                fichiers.append(Path(dossier, nom).relative_to(self.racine).as_posix())
        return fichiers


class Verificateur:
    def __init__(self, depot: Depot, transcripts: str | None):
        self.depot = depot
        # None : pas de --transcripts ; "" : racine par défaut ; sinon la racine donnée.
        self.transcripts = transcripts
        self.poc_non_verifies = 0

    def controler(self, rep: Reponse) -> list[str]:
        # Plan natif : la preuve suit « · Preuve : » sur la ligne D<n>. Plan Notion : une
        # ligne qui COMMENCE par « Preuve : » ; une prose qui la cite en milieu de phrase non.
        if rep.natif:
            preuves = [ligne for ligne in rep.bloc if "Preuve :" in ligne]
        else:
            preuves = [ligne for ligne in rep.bloc if PREUVE_EN_TETE.match(ligne)]
        if not preuves:
            return [f"{rep.ident} : sans ligne Preuve"]
        if len(preuves) > 1:
            return [f"{rep.ident} : plusieurs lignes Preuve ({len(preuves)})"]
        ligne = preuves[0]
        if rep.natif:
            apres = ligne.split("Preuve :", 1)[1]
        else:
            apres = PREUVE_EN_TETE.sub("", ligne, count=1)
        apres = apres.replace("`", "")
        m = re.match(r"\s*(\w+)", apres)
        typ = m.group(1) if m else ""
        if typ not in TYPES:
            return [f"{rep.ident} : type inconnu ({typ or 'absent'})"]
        reste = apres[m.end():]
        if typ == "dispense":
            # « parce qu'aucun » (élision, apostrophe droite ou typographique) = « parce que » + mot.
            if not re.search(r"parce (?:que\s+\w|qu['’]\w)", apres_tiret(reste), re.IGNORECASE):
                return [f"{rep.ident} : dispense sans raison"]
            return []
        if typ == "commande":
            return [] if apres_tiret(reste) else [f"{rep.ident} : commande sans détail"]
        if typ == "lecture":
            return self._lecture(rep.ident, ligne, reste)
        return self._poc(rep.ident, ligne, reste)

    def _lecture(self, ident: str, ligne: str, reste: str) -> list[str]:
        # Chemin externe testé avant l'exigence de « :ligne » : il s'en passe, mais il lui
        # faut un détail non vide (ce que dit le passage).
        premier = CHEMIN_NU.search(reste)
        if premier is not None and externe(premier.group(1), ligne):
            if detail_apres(reste[premier.end():]):
                return []
            return [f"{ident} : lecture externe sans détail"]
        m = CHEMIN.search(reste)
        if m is None:
            return [f"{ident} : lecture sans chemin:ligne"]
        chemin = m.group(1)
        if externe(chemin, ligne) or self.depot.contient(chemin):
            return []
        return [f"{ident} : fichier introuvable dans le dépôt : {chemin}"]

    def _poc(self, ident: str, ligne: str, reste: str) -> list[str]:
        detail = re.sub(r"^\s*[—-]\s*", "", reste).strip()
        morceaux = [p.strip() for p in detail.split("·")]
        m = re.search(r"\bagent\s+(\S+)", morceaux[0])
        agent = m.group(1) if m else ""
        agent_id = morceaux[1] if len(morceaux) > 1 else ""
        modele = re.sub(r"\(.*", "", morceaux[2]).strip() if len(morceaux) > 2 else ""
        ecarts = []
        if agent not in AGENTS_POC:
            ecarts.append(f"{ident} : POC sans agent nommé valide")
        if not HEXA.fullmatch(agent_id):
            ecarts.append(f"{ident} : POC sans agentId")
        if not modele:
            ecarts.append(f"{ident} : POC sans modèle")
        if self.transcripts is None:
            self.poc_non_verifies += 1
        elif HEXA.fullmatch(agent_id):
            ecarts += self._transcription(ident, agent_id, modele)
        return ecarts

    def _transcription(self, ident: str, agent_id: str, modele: str) -> list[str]:
        cmd = [sys.executable, str(MODELE_SOUS_AGENT), agent_id]
        if self.transcripts:
            cmd += ["--racine", self.transcripts]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 2:
            return [f"{ident} : transcription introuvable pour {agent_id}"]
        if r.returncode != 0:
            return [f"{ident} : modele-sous-agent.py a rendu le code {r.returncode} pour {agent_id}"]
        servis = []
        for ligne in r.stdout.splitlines():
            m = MODELE_SERVI.match(ligne)
            if m is not None:
                servis.append(m.group(1))
        if not servis:
            return [f"{ident} : aucun modèle servi relevé pour {agent_id}"]
        ecarts = []
        opus = [s for s in servis if "opus" in s.lower()]
        if opus:
            ecarts.append(f"{ident} : POC servi par Opus : {', '.join(opus)}")
        # Tout modèle servi doit correspondre au modèle cité : un seul qui diffère suffit à refuser.
        differents = [s for s in servis if not meme_modele(modele, s)]
        if modele and differents:
            ecarts.append(f"{ident} : modèle cité {modele} différent du modèle servi {', '.join(differents)}")
        return ecarts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    ap.add_argument("--format", choices=("notion", "natif"), default="notion")
    ap.add_argument("--depot", type=Path)
    ap.add_argument("--transcripts", nargs="?", const="", default=None)
    a = ap.parse_args(argv)
    try:
        texte = Path(a.page).read_text(encoding="utf-8")
        reponses = extraire_notion(texte) if a.format == "notion" else extraire_natif(texte)
    except (OSError, ValueError, Illisible) as e:
        print(f"illisible : {e}", file=sys.stderr)
        return 2
    controlees = [r for r in reponses if not r.ouverte]
    if not controlees:
        print("aucune réponse tranchée à contrôler")
        return 0
    verif = Verificateur(Depot(a.depot), a.transcripts)
    ecarts = [e for r in controlees for e in verif.controler(r)]
    if verif.poc_non_verifies and a.transcripts is None:
        print("POC non vérifié : pas de --transcripts", file=sys.stderr)
    if ecarts:
        print("\n".join(ecarts))
        return 1
    print(f"conforme : {len(controlees)} réponse(s) contrôlée(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
