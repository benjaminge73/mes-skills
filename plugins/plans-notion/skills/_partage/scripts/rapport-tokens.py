#!/usr/bin/env python3
"""Rapport de tokens et de dollars : par projet, skill, sous-agent et modèle, plus ruptures de cache et tours.

Usage : rapport-tokens.py [--since <Nd|Nh|AAAA-MM-JJ>] [--projets <dossier>] [--grille <json>]
                          [--seuil-cache <tokens>] [--top <N>]

Lecture seule, sans dépendance : le script lit lui-même les journaux
``<projets>/**/*.jsonl`` de Claude Code (sans ccusage) et chiffre les tokens sur
``grille-tarifs.json`` (à côté du script par défaut).

1. La fenêtre. Un message dont le ``timestamp`` précède ``--since`` n'est jamais
   compté. Un fichier modifié avant la fenêtre n'est pas lu : il ne peut pas
   contenir de message récent.
2. Les appels. Un message assistant qui porte ``usage``, dédoublonné par
   ``requestId`` (à défaut ``message.id``) entre fichiers : pour une même requête,
   on garde la ligne au ``output_tokens`` le plus grand (à égalité, la première).
   Un message dont les quatre compteurs sont nuls n'est pas un appel.
3. Les dollars. Chaque appel est chiffré sur la grille de son modèle. Les
   écritures de cache suivent la ventilation 1 h de son message
   (``cache_creation.ephemeral_1h_input_tokens``) ; le reste part au tarif 5 min,
   donc sans ce détail tout part au 5 min. Un modèle absent de la grille est
   « non chiffré » : il sort du total en dollars, jamais à zéro.
4. Le projet. Le nom du dépôt tiré du premier ``cwd`` de la session qui donne un
   nom (un ``cwd`` sans nom, comme ``/``, est ignoré) : le dernier segment, le
   segment qui suit ``worktrees/``, ou, pour un worktree
   ``<dépôt>/.claude/worktrees/<nom>``, le segment qui précède ``.claude``.
   À défaut, le nom du dossier de projet.
5. Le sous-agent. Un ``agent-*.jsonl`` sous ``<session>/subagents/`` (y compris
   ``workflows/wf_*/``), ou posé à la racine d'un dossier ``ssh-*``. Son type
   vient d'``agentType`` dans le ``<agent>.meta.json`` voisin ; sinon du
   ``subagent_type`` de l'appel ``Agent`` du journal parent, retrouvé par le
   ``toolUseId`` du meta.json ou, sans meta,
   par ``toolUseResult.agentId`` (le nom du fichier). Sinon, « type non résolu ».
6. Le déclencheur d'un appel : le dernier message ``user`` qui le précède dans
   son journal. Un message humain réel (``origin.kind == "human"``, ou texte sans
   marqueur et sans ``promptSource: "sdk"``) est « humain ». Une notification de
   session liée (marqueur de notification, ou ``origin`` de notification) est
   « notification de session liée ». Un résultat d'outil, un message isMeta, un
   message de sous-agent, un prompt écrit par un script (``promptSource: "sdk"``
   sans origine) ou un message système injecté est « autre message système ».
7. Les tours. Un message humain ouvre un tour, jusqu'au suivant. Les messages
   isMeta et les notifications ne coupent pas un tour.

Codes de sortie : 0 rendu ; 1 aucun message dans la fenêtre ; 2 grille ou
dossier de journaux illisible (message sur stderr, pas de trace Python).

Les idées de rattachement d'un sous-agent (meta.json, puis appel Agent du
journal parent) et de dédoublonnage par requestId viennent de session-report
(Apache-2.0, anthropics/claude-plugins-official). Réécrites ici, aucune ligne copiée.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Iterator

GRILLE_PAR_DEFAUT = Path(__file__).resolve().parent / "grille-tarifs.json"
PROJETS_PAR_DEFAUT = Path.home() / ".claude" / "projects"
FENETRE_PAR_DEFAUT = "7d"
SEUIL_PAR_DEFAUT = 100_000
TOP_PAR_DEFAUT = 10

TARIF_5_MIN = "ecriture_cache_5m"
TARIF_1_H = "ecriture_cache_1h"
CHAMPS_PRIX = ["entree", "sortie", "lecture_cache", TARIF_5_MIN, TARIF_1_H]

CAS_HUMAIN = "humain"
CAS_NOTIFICATION = "notification de session liée"
CAS_SYSTEME = "autre message système"

ORIGINES_NOTIFICATION = ("task-notification", "coordinator", "peer")
MARQUEURS_NOTIFICATION = (
    "Linked sessions now", "<side-sessions-event>", "<ci-monitor-event>", "<task-notification>",
    "<agent-message", "Another Claude session sent", "The coordinator sent a message",
    "[SYSTEM NOTIFICATION", "finished a turn", "Background (from the session that started this one)",
)
DEBUTS_SYSTEME = (
    "<system-reminder>", "<command-", "<local-command-", "[Request interrupted",
    "This session is being continued", "[Image", "[Workflow harness", "(Re-invocation",
    "[handback-", "Base directory for this skill",
)

RAPPEL_SYSTEME = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)

ETIQUETTE_TOUR = 60
AUCUN_SKILL = "aucun skill"
TYPE_NON_RESOLU = "type non résolu"
NON_CHIFFRE = "non chiffré"
MODELE_INCONNU = "modèle inconnu"
TIRET = "—"


@dataclass
class Appel:
    ts: datetime
    session: str
    fichier: Path  # journal d'où vient la ligne retenue
    projet: str
    modele: str
    skill: str | None
    sous_agent: str | None  # type du sous-agent ; None pour la session principale
    entree: int
    sortie: int
    lecture: int
    ecr_5m: int
    ecr_1h: int
    cout: float | None  # None : modèle absent de la grille
    declencheur: str

    @property
    def ecriture(self) -> int:
        return self.ecr_5m + self.ecr_1h

    def origine(self) -> str:
        return "session" if self.sous_agent is None else f"sous-agent {self.sous_agent}"


@dataclass
class Somme:
    entree: int = 0
    sortie: int = 0
    lecture: int = 0
    ecriture: int = 0
    cout: float = 0.0
    chiffres: int = 0
    non_chiffres: int = 0

    def ajouter(self, a: Appel) -> None:
        self.entree += a.entree
        self.sortie += a.sortie
        self.lecture += a.lecture
        self.ecriture += a.ecriture
        if a.cout is None:
            self.non_chiffres += 1
        else:
            self.cout += a.cout
            self.chiffres += 1


@dataclass
class Tour:
    debut: datetime
    projet: str
    libelle: str
    cout: float
    chiffres: int
    non_chiffres: int


@dataclass
class Fichier:
    chemin: Path
    session: str
    sous_agent: bool
    dossier: Path  # dossier de projet, ou dossier ssh-* qui porte le journal
    principal: Path  # journal principal de la session (peut ne pas exister)


@dataclass
class Bilan:
    debut: datetime
    seuil: int
    appels: list[Appel] = field(default_factory=list)
    humains: dict[str, set[tuple[datetime, str]]] = field(default_factory=dict)
    projets: dict[str, str] = field(default_factory=dict)  # session -> projet
    vus: dict[str, int] = field(default_factory=dict)  # requestId -> rang de sa ligne dans appels
    messages: int = 0


def erreur(message: str, code: int) -> None:
    print(message, file=sys.stderr)
    sys.exit(code)


def fenetre(valeur: str) -> str:
    if re.fullmatch(r"\d+[dh]", valeur):
        return valeur
    try:
        datetime.strptime(valeur, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"« {valeur} » : attendu Nd, Nh ou AAAA-MM-JJ")
    return valeur


def debut_de_fenetre(valeur: str, maintenant: datetime) -> datetime:
    m = re.fullmatch(r"(\d+)([dh])", valeur)
    if m:
        n = int(m.group(1))
        return maintenant - (timedelta(days=n) if m.group(2) == "d" else timedelta(hours=n))
    return datetime.strptime(valeur, "%Y-%m-%d").astimezone()


def horodatage(valeur: object) -> datetime | None:
    if not isinstance(valeur, str):
        return None
    try:
        dt = datetime.fromisoformat(valeur.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.astimezone()


def entier(valeur: object) -> int:
    return valeur if isinstance(valeur, int) and not isinstance(valeur, bool) else 0


def blocs_de(obj: dict) -> list[dict]:
    message = obj.get("message")
    contenu = message.get("content") if isinstance(message, dict) else None
    if not isinstance(contenu, list):
        return []
    return [b for b in contenu if isinstance(b, dict)]


def textes_de(contenu: object) -> str:
    if isinstance(contenu, str):
        return contenu
    if isinstance(contenu, list):
        return "\n".join(b["text"] for b in contenu
                         if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str))
    return ""


def resume(texte: str) -> str:
    """Le libellé d'un tour : une ligne, sans « | » (séparateur du tableau), 60 caractères au plus."""
    return " ".join(texte.replace("|", "/").split())[:ETIQUETTE_TOUR]


def classer_user(obj: dict) -> tuple[str, str]:
    """Le cas d'un message ``user`` (humain, notification, autre système) et son texte.

    Le harnais peut mettre un ``<system-reminder>`` dans le même message que le texte tapé.
    On classe sur le texte restant, rappels retirés ; s'il ne reste rien, sur le rappel seul.
    Un humain garde pour libellé ce texte restant.
    """
    message = obj.get("message")
    contenu = message.get("content") if isinstance(message, dict) else None
    if isinstance(contenu, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in contenu):
        return CAS_SYSTEME, ""
    texte = textes_de(contenu)
    reste = RAPPEL_SYSTEME.sub("", texte).strip()
    cible = reste or texte
    origine = obj.get("origin")
    genre = origine.get("kind") if isinstance(origine, dict) else None
    if genre in ORIGINES_NOTIFICATION or any(m in cible for m in MARQUEURS_NOTIFICATION):
        return CAS_NOTIFICATION, texte
    if obj.get("isSidechain") is True or obj.get("isMeta") is True:
        return CAS_SYSTEME, texte
    if genre not in (None, "human"):
        return CAS_SYSTEME, texte
    if cible.lstrip().startswith(DEBUTS_SYSTEME):
        return CAS_SYSTEME, texte
    if genre is None and obj.get("promptSource") == "sdk":
        # Prompt écrit par un script ou une session (claude -p, SDK), sans origine humaine.
        return CAS_SYSTEME, texte
    return CAS_HUMAIN, reste


def fichier_de(chemin: Path, racine: Path) -> Fichier:
    parent = chemin.parent
    # Un sous-agent de workflow est plus bas : <session>/subagents/workflows/wf_*/agent-*.jsonl.
    # On cherche le dossier subagents parmi les ancêtres, sans sortir de la racine des journaux.
    sous = next((racine / p for p in chemin.relative_to(racine).parents if p.name == "subagents"), None)
    if sous is not None and (parent.name == "subagents" or chemin.name.startswith("agent-")):
        session_dir = sous.parent
        return Fichier(chemin, session_dir.name, True, session_dir.parent,
                       session_dir.parent / f"{session_dir.name}.jsonl")
    if chemin.name.startswith("agent-") and parent.name.startswith("ssh-"):
        cle = parent.name[len("ssh-"):]
        return Fichier(chemin, cle, True, parent, parent / f"{cle}.jsonl")
    return Fichier(chemin, chemin.stem, False, parent, chemin)


def cwds_de(chemin: Path, max_lignes: int = 300) -> Iterator[str]:
    """Les ``cwd`` du journal, dans l'ordre, sur ses premières lignes."""
    try:
        with chemin.open(encoding="utf-8", errors="replace") as h:
            for i, ligne in enumerate(h):
                if i >= max_lignes:
                    break
                if '"cwd"' not in ligne:
                    continue
                try:
                    obj = json.loads(ligne)
                except ValueError:
                    continue
                cwd = obj.get("cwd") if isinstance(obj, dict) else None
                if isinstance(cwd, str) and cwd:
                    yield cwd
    except OSError:
        return


def nom_du_depot(cwd: str) -> str | None:
    segments = [s for s in cwd.split("/") if s]
    if "worktrees" in segments:
        i = segments.index("worktrees")
        if i >= 1 and segments[i - 1] == ".claude":
            # Worktree <dépôt>/.claude/worktrees/<nom> : le dépôt est avant .claude.
            return segments[i - 2] if i >= 2 else None
        if i + 1 < len(segments):
            return segments[i + 1]
    return segments[-1] if segments else None


def projet_de_session(fichiers: list[Fichier]) -> str:
    ordre = sorted(fichiers, key=lambda f: (f.sous_agent, str(f.chemin)))
    for f in ordre:
        for cwd in cwds_de(f.chemin):
            nom = nom_du_depot(cwd)
            if nom:
                return nom
    return ordre[0].dossier.name


def lire_meta(chemin: Path) -> dict:
    meta = chemin.with_name(chemin.stem + ".meta.json")
    try:
        obj = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}


def index_du_parent(principal: Path, cache: dict[Path, dict]) -> dict:
    """Pour un journal parent : type par ``tool_use.id`` d'appel Agent, et id d'appel par agentId."""
    if principal in cache:
        return cache[principal]
    index: dict = {"types": {}, "tuid_par_agent": {}}
    cache[principal] = index
    if not principal.is_file():
        return index
    try:
        with principal.open(encoding="utf-8", errors="replace") as h:
            for ligne in h:
                if "Agent" not in ligne and "agentId" not in ligne:
                    continue
                try:
                    obj = json.loads(ligne)
                except ValueError:
                    continue
                if not isinstance(obj, dict):
                    continue
                resultat = obj.get("toolUseResult")
                if isinstance(resultat, dict) and isinstance(resultat.get("agentId"), str):
                    for b in blocs_de(obj):
                        if b.get("type") == "tool_result" and isinstance(b.get("tool_use_id"), str):
                            index["tuid_par_agent"][resultat["agentId"]] = b["tool_use_id"]
                for b in blocs_de(obj):
                    appel_agent = b.get("input")
                    sous = appel_agent.get("subagent_type") if isinstance(appel_agent, dict) else None
                    if b.get("type") == "tool_use" and b.get("name") == "Agent" \
                            and isinstance(b.get("id"), str) and isinstance(sous, str) and sous:
                        index["types"][b["id"]] = sous
    except OSError:
        pass
    return index


def type_du_sous_agent(f: Fichier, cache: dict[Path, dict]) -> str:
    meta = lire_meta(f.chemin)
    nom = meta.get("agentType")
    if isinstance(nom, str) and nom.strip():
        return nom.strip()
    index = index_du_parent(f.principal, cache)
    meta_tuid = meta.get("toolUseId")
    tuid = meta_tuid if isinstance(meta_tuid, str) and meta_tuid else None
    if tuid is None:
        id_agent = f.chemin.stem[len("agent-"):] if f.chemin.stem.startswith("agent-") else f.chemin.stem
        tuid = index["tuid_par_agent"].get(id_agent)
    if tuid is None:
        return TYPE_NON_RESOLU
    return index["types"].get(tuid, TYPE_NON_RESOLU)


def cout_de(tarifs: dict[str, float] | None, entree: int, sortie: int, lecture: int,
            cinq: int, une_heure: int) -> float | None:
    if tarifs is None:
        return None
    return (entree * tarifs["entree"] + sortie * tarifs["sortie"] + lecture * tarifs["lecture_cache"]
            + cinq * tarifs[TARIF_5_MIN] + une_heure * tarifs[TARIF_1_H]) / 1_000_000


def lire_journal(f: Fichier, projet: str, type_sous: str | None,
                 tarifs: dict[str, dict[str, float]], bilan: Bilan) -> None:
    cas, texte_dernier = CAS_SYSTEME, ""
    with f.chemin.open(encoding="utf-8", errors="replace") as h:
        for ligne in h:
            if '"user"' not in ligne and '"assistant"' not in ligne:
                continue
            try:
                obj = json.loads(ligne)
            except ValueError:
                continue
            if not isinstance(obj, dict):
                continue
            ts = horodatage(obj.get("timestamp"))
            genre = obj.get("type")
            if genre == "user":
                cas, texte_dernier = classer_user(obj)
                if ts is None:
                    continue
                if ts >= bilan.debut:
                    bilan.messages += 1
                if cas == CAS_HUMAIN:
                    # Les humains hors fenêtre comptent comme bornes de tour, sans être comptés.
                    bilan.humains.setdefault(f.session, set()).add((ts, resume(texte_dernier)))
                continue
            if genre != "assistant" or ts is None or ts < bilan.debut:
                continue
            message = obj.get("message")
            usage = message.get("usage") if isinstance(message, dict) else None
            if not isinstance(usage, dict):
                continue
            bilan.messages += 1
            entree = entier(usage.get("input_tokens"))
            sortie = entier(usage.get("output_tokens"))
            lecture = entier(usage.get("cache_read_input_tokens"))
            ecriture = entier(usage.get("cache_creation_input_tokens"))
            if not (entree or sortie or lecture or ecriture):
                continue
            cle = obj.get("requestId") or message.get("id")
            cache = usage.get("cache_creation")
            une_heure = min(entier(cache.get("ephemeral_1h_input_tokens")) if isinstance(cache, dict) else 0,
                            ecriture)
            cinq = ecriture - une_heure
            modele = message.get("model")
            if not isinstance(modele, str) or not modele:
                modele = MODELE_INCONNU
            skill = obj.get("attributionSkill")
            appel = Appel(
                ts=ts, session=f.session, fichier=f.chemin, projet=projet, modele=modele,
                skill=skill if isinstance(skill, str) and skill else None,
                sous_agent=type_sous, entree=entree, sortie=sortie, lecture=lecture,
                ecr_5m=cinq, ecr_1h=une_heure,
                cout=cout_de(tarifs.get(modele), entree, sortie, lecture, cinq, une_heure),
                declencheur=cas)
            if cle is not None and cle in bilan.vus:
                # Claude Code écrit parfois une même requête sur deux lignes, la première avec
                # un output_tokens partiel : on garde la ligne qui en a le plus (à égalité, la première).
                rang = bilan.vus[cle]
                if sortie <= bilan.appels[rang].sortie:
                    continue
                bilan.appels[rang] = appel
            else:
                if cle is not None:
                    bilan.vus[cle] = len(bilan.appels)
                bilan.appels.append(appel)


def analyser(projets: Path, debut: datetime, tarifs: dict[str, dict[str, float]], seuil: int) -> Bilan:
    bilan = Bilan(debut=debut, seuil=seuil)
    tous = [fichier_de(c, projets) for c in sorted(projets.rglob("*.jsonl"))]
    par_session: dict[str, list[Fichier]] = {}
    for f in tous:
        par_session.setdefault(f.session, []).append(f)
    lus: list[Fichier] = []
    for f in tous:
        try:
            if f.chemin.stat().st_mtime >= debut.timestamp():
                lus.append(f)
        except OSError:
            continue
    bilan.projets = {f.session: projet_de_session(par_session[f.session]) for f in lus}
    caches: dict[Path, dict] = {}
    for f in lus:
        type_sous = type_du_sous_agent(f, caches) if f.sous_agent else None
        lire_journal(f, bilan.projets[f.session], type_sous, tarifs, bilan)
    return bilan


def tours_du_bilan(bilan: Bilan) -> list[Tour]:
    par_session: dict[str, list[Appel]] = {}
    for a in bilan.appels:
        par_session.setdefault(a.session, []).append(a)
    for liste in par_session.values():
        liste.sort(key=lambda a: a.ts)
    tours: list[Tour] = []
    for session, humains in bilan.humains.items():
        ordre = sorted(humains)
        appels = par_session.get(session, [])
        temps = [a.ts for a in appels]
        for i, (ts0, libelle) in enumerate(ordre):
            if ts0 < bilan.debut:
                continue
            i0 = bisect.bisect_left(temps, ts0)
            i1 = bisect.bisect_left(temps, ordre[i + 1][0]) if i + 1 < len(ordre) else len(appels)
            morceau = appels[i0:i1]
            chiffres = [a.cout for a in morceau if a.cout is not None]
            tours.append(Tour(debut=ts0, projet=bilan.projets.get(session, "?"), libelle=libelle,
                              cout=sum(chiffres), chiffres=len(chiffres),
                              non_chiffres=len(morceau) - len(chiffres)))
    return tours


def fmt_tokens(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def fmt_usd(x: float) -> str:
    return f"{x:,.4f}".replace(",", " ").replace(".", ",") + " $"


def fmt_pourcent(x: float) -> str:
    return f"{x * 100:.1f}".replace(".", ",") + " %"


def part_de(cout: float, total: float) -> str:
    return fmt_pourcent(cout / total) if total > 0 else fmt_pourcent(0.0)


def tableau(entetes: list[str], lignes: list[list[str]]) -> list[str]:
    largeurs = [max(len(c) for c in colonne) for colonne in zip(entetes, *lignes)]

    def rendre(cellules: list[str]) -> str:
        return "  " + " | ".join(
            c.ljust(w) if i == 0 else c.rjust(w) for i, (c, w) in enumerate(zip(cellules, largeurs)))

    return [rendre(entetes), *[rendre(l) for l in lignes]]


def sommer(appels: list[Appel], cle: Callable[[Appel], str]) -> dict[str, Somme]:
    groupes: dict[str, Somme] = {}
    for a in appels:
        groupes.setdefault(cle(a), Somme()).ajouter(a)
    return groupes


def bloc_groupes(titre: str, premiere_colonne: str, groupes: dict[str, Somme], total: float, vide: str) -> list[str]:
    if not groupes:
        return [titre, f"  {vide}"]
    lignes = []
    for libelle, s in sorted(groupes.items(), key=lambda kv: (-kv[1].cout, kv[0])):
        if s.chiffres == 0:
            dollars, part = NON_CHIFFRE, TIRET
        else:
            dollars, part = fmt_usd(s.cout), part_de(s.cout, total)
            if s.non_chiffres:
                libelle += " [dont non chiffré]"
        lignes.append([libelle, fmt_tokens(s.entree), fmt_tokens(s.sortie), fmt_tokens(s.lecture),
                       fmt_tokens(s.ecriture), dollars, part])
    return [titre, *tableau([premiere_colonne, "entrée", "sortie", "lecture cache", "écriture cache",
                             "dollars", "part"], lignes)]


def bloc_ruptures(bilan: Bilan, top: int, total: float) -> list[str]:
    titre = "5. Ruptures de cache"
    rupt = [a for a in bilan.appels if a.entree + a.ecriture > bilan.seuil]
    if not rupt:
        return [titre, f"  aucune rupture au-delà de {fmt_tokens(bilan.seuil)} tokens (entrée + écriture cache)."]
    chiffres = [a.cout for a in rupt if a.cout is not None]
    resume_ligne = (f"  {len(rupt)} rupture(s) au-delà de {fmt_tokens(bilan.seuil)} tokens "
                    f"(entrée + écriture cache), coût chiffré total : {fmt_usd(sum(chiffres))}")
    if len(chiffres) < len(rupt):
        resume_ligne += f" ; {len(rupt) - len(chiffres)} non chiffrée(s)"
    ordre = sorted(rupt, key=lambda a: (a.cout is None, -(a.cout or 0.0), a.ts))[:top]
    lignes = [[a.ts.astimezone().strftime("%Y-%m-%d %H:%M"), a.projet, a.origine(), a.modele,
               fmt_tokens(a.entree + a.ecriture), a.declencheur,
               NON_CHIFFRE if a.cout is None else fmt_usd(a.cout)] for a in ordre]
    return [titre, resume_ligne, *tableau(["horodatage", "projet", "origine", "modèle",
                                           "entrée + écriture", "déclencheur", "dollars"], lignes)]


def bloc_tours(tours: list[Tour], top: int, total: float) -> list[str]:
    titre = "6. Top des tours"
    if not tours:
        return [titre, "  aucun tour dans la fenêtre"]
    lignes = []
    for t in sorted(tours, key=lambda t: (-t.cout, t.debut))[:top]:
        libelle = t.libelle or "(message vide)"
        if t.non_chiffres:
            libelle += " [dont non chiffré]"
        hors_grille_seul = t.chiffres == 0 and t.non_chiffres > 0
        dollars = NON_CHIFFRE if hors_grille_seul else fmt_usd(t.cout)
        lignes.append([dollars, TIRET if hors_grille_seul else part_de(t.cout, total),
                       t.debut.astimezone().strftime("%Y-%m-%d %H:%M"), t.projet, libelle])
    return [titre, *tableau(["dollars", "part", "début", "projet", "message humain"], lignes)]


def rendre(bilan: Bilan, since: str, top: int, releve: str) -> str:
    total = sum(a.cout for a in bilan.appels if a.cout is not None)
    non = [a for a in bilan.appels if a.cout is None]
    sous = [a for a in bilan.appels if a.sous_agent is not None]
    tours = tours_du_bilan(bilan)
    sortie = [
        f"Rapport de tokens — fenêtre depuis {bilan.debut:%Y-%m-%d %H:%M} (--since {since}) — "
        f"total chiffré : {fmt_usd(total)}",
        f"{len({a.session for a in bilan.appels if a.sous_agent is None})} session(s), "
        f"{len({a.fichier for a in sous})} sous-agent(s), "
        f"{len(bilan.appels)} appel(s) comptés (requestId dédoublonnés). Grille du {releve}.",
        "",
        *bloc_groupes("1. Par projet", "projet", sommer(bilan.appels, lambda a: a.projet), total,
                      "aucun appel dans la fenêtre"),
        "",
        *bloc_groupes("2. Par skill", "skill", sommer(bilan.appels, lambda a: a.skill or AUCUN_SKILL), total,
                      "aucun appel dans la fenêtre"),
        "",
        *bloc_groupes("3. Par sous-agent", "sous-agent", sommer(sous, lambda a: a.sous_agent or TYPE_NON_RESOLU),
                      total, "aucun sous-agent dans la fenêtre"),
        "",
        *bloc_groupes("4. Par modèle", "modèle", sommer(bilan.appels, lambda a: a.modele), total,
                      "aucun appel dans la fenêtre"),
        "",
        *bloc_ruptures(bilan, top, total),
        "",
        *bloc_tours(tours, top, total),
        "",
    ]
    fin = f"Total chiffré : {fmt_usd(total)}"
    if non:
        tokens = sum(a.entree + a.sortie + a.lecture + a.ecriture for a in non)
        fin += f"  (hors {len(non)} appel(s) non chiffré(s), {fmt_tokens(tokens)} tokens : voir section 4)"
    sortie.append(fin)
    return "\n".join(sortie)


def charger_grille(chemin: Path) -> tuple[dict[str, dict[str, float]], str]:
    try:
        grille = json.loads(chemin.read_text(encoding="utf-8"))
        tarifs = {nom: {champ: float(prix[champ]["prix"]) for champ in CHAMPS_PRIX}
                  for nom, prix in grille["modeles"].items()}
        return tarifs, str(grille.get("releve", "date inconnue"))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        erreur(f"rapport-tokens : grille illisible ({chemin}) : {e}", 2)
    raise SystemExit(2)  # inatteignable : erreur() sort ; garde pour le lecteur


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rapport de tokens et de dollars des journaux Claude Code.")
    parser.add_argument("--since", type=fenetre, default=FENETRE_PAR_DEFAUT,
                        help="fenêtre : Nd, Nh ou AAAA-MM-JJ (défaut : 7d)")
    parser.add_argument("--projets", type=Path, default=PROJETS_PAR_DEFAUT,
                        help="dossier des journaux (défaut : ~/.claude/projects)")
    parser.add_argument("--grille", type=Path, default=GRILLE_PAR_DEFAUT,
                        help="grille de tarifs (défaut : grille-tarifs.json à côté du script)")
    parser.add_argument("--seuil-cache", type=int, default=SEUIL_PAR_DEFAUT,
                        help="rupture de cache au-delà de ce nombre de tokens (défaut : 100000)")
    parser.add_argument("--top", type=int, default=TOP_PAR_DEFAUT,
                        help="nombre de lignes des ruptures et des tours (défaut : 10)")
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error("--top doit être au moins 1")

    tarifs, releve = charger_grille(args.grille)
    if not args.projets.is_dir():
        erreur(f"rapport-tokens : dossier de journaux absent ({args.projets}).", 2)

    debut = debut_de_fenetre(args.since, datetime.now().astimezone())
    try:
        bilan = analyser(args.projets, debut, tarifs, args.seuil_cache)
    except OSError as e:
        erreur(f"rapport-tokens : lecture des journaux impossible ({e}).", 2)
    if bilan.messages == 0:
        erreur(f"rapport-tokens : aucun message dans la fenêtre (depuis {debut:%Y-%m-%d %H:%M}) "
               f"dans {args.projets}.", 1)

    print(rendre(bilan, args.since, args.top, releve))
    return 0


if __name__ == "__main__":
    sys.exit(main())
