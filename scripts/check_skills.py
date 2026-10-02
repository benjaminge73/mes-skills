#!/usr/bin/env python3
"""Les règles de forme des skills et des agents, jouées pour tous les plugins.

Chaque règle ci-dessous est un correctif du 2026-09-30 qui a reçu un garde : un
défaut qu'on avait corrigé une fois ne doit pas pouvoir revenir sans que la CI
le voie. Le registre ``docs/garde-fous.md`` dit d'où vient chaque règle ; ce
script est le garde de celles qui portent sur les fichiers de plugin — et,
aussi, le garde **du registre lui-même** (voir « Le registre », plus bas).

Les règles, et le fait de doc qui fonde chacune (voir ``docs/veille.md``) :

(a) ``description`` + ``when_to_use`` ≤ 1 536 caractères, par skill et par
    agent : au-delà, Claude Code tronque la fin de la description dans la
    liste des skills — les phrases de déclenchement qu'on y avait mises en
    dernier disparaissent sans un mot.
(b) Taille des ``SKILL.md`` **à cliquet** : un plafond par fichier dans
    ``scripts/limites.json``, qui ne peut que baisser. La CI compare avec le
    ``limites.json`` de la base (``git show <base>:scripts/limites.json``) et
    refuse une hausse ; absent de la base, il est accepté. Le plafond de départ
    est la taille du jour (lignes et octets) : on ne juge pas le passé, on
    interdit d'aggraver.
(c) Un bloc d'invariants dans les 60 premières lignes et sous 5 000 jetons
    estimés (octets / 4), exigé seulement des skills que ``limites.json``
    marque (``invariants_en_tete``) : à la compaction, Claude Code ne garde que
    les 5 000 premiers jetons d'un skill invoqué.
(d) Chaque agent de ``agents/`` est cité dans la ``description`` de
    ``plugin.json`` : c'est ce qu'un lecteur du manifeste voit du plugin.
(e) Chaque fichier de ``skills/_partage/`` est cité par au moins un skill ou un
    agent, et la liste « Ses compagnons sont les fichiers partagés … » d'un
    skill contient **tous** les fichiers ``_partage/`` que ce skill cite : une
    liste incomplète dit à un lecteur qu'il n'a pas besoin d'un fichier dont
    le skill dépend.
(f) Pas de ``hooks``, ``mcpServers`` ni ``permissionMode`` dans un agent de
    plugin : Claude Code ignore ces champs pour un agent de plugin, ils
    tromperaient le lecteur sur ce qui est réellement appliqué.
(g) Un agent qui s'interdit Write ou Edit n'a pas de ``memory`` : activer la
    mémoire active Read, Write et Edit d'office, et défait l'interdit.
(h) Aucun dossier ``.claude/agent-memory*`` dans le dépôt : la mémoire d'un
    agent est de l'état personnel, pas du code à versionner.
(i) Pour chaque plugin qui a un banc ``evals/<plugin>/`` : chaque cas (un dossier
    avec ``prompt.md`` ou ``case.yaml``) est dans au moins une catégorie de
    ``evals/categories.json``, chaque cas cité existe, chaque catégorie a au
    moins un cas, et chaque chemin qu'une catégorie « exerce » existe sous
    ``plugins/<plugin>/``. Sans cela, un cas qu'aucune catégorie ne nomme ne
    serait jamais joué par une PR qui choisit ses catégories, et une catégorie
    qui pointe dans le vide ferait croire qu'un skill est couvert. Sens inverse
    (étape D5) : chaque fichier sous ``skills/`` (``_partage/`` compris) et
    ``agents/`` d'un plugin qui a un banc doit être couvert par au moins un
    préfixe ``exerce`` ; sinon le fichier est refusé, nommé, avec la consigne de
    le déclarer dans ``evals/categories.json``. Un nouveau fichier oblige donc à
    dire, dans sa PR, quel cas le teste.

Exceptions datées
-----------------
Un défaut connu qu'on ne corrige pas dans la PR courante se déclare dans
``scripts/limites.json`` (``exceptions``) avec ``regle``, ``cible``, ``date``,
``raison`` et ``levee_par`` (l'étape qui la lève). Une exception ne bloque pas,
mais elle est **affichée à chaque passage** : possible, jamais silencieuse. Une
exception qui ne correspond plus à aucun défaut est refusée (elle est
périmée : on la retire). ``--sans-exceptions`` les ignore toutes, pour voir
l'état réel.

Le registre
-----------
``docs/garde-fous.md`` liste chaque règle avec le garde qui la tient. Ce
script contrôle que chaque garde qu'il cite comme **en place** existe : un
fichier de script, un job de ``ci.yml`` (``ci.yml#<job>``) ou un cas d'éval
(``evals/<plugin>/<cas>``). Un garde « prévu — étape X » ou « manquant » n'est
pas vérifié, mais doit dire son statut.

Codes de sortie : ``0`` tout est cohérent, ``1`` au moins une règle violée,
``2`` panne (base illisible, ``limites.json`` illisible).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]

PLAFOND_DESCRIPTION = 1536
LIGNES_INVARIANTS = 60
JETONS_INVARIANTS = 5000
OCTETS_PAR_JETON = 4
CHAMPS_IGNORES_POUR_UN_AGENT_DE_PLUGIN = ("hooks", "mcpServers", "permissionMode")
CHAMPS_D_UNE_EXCEPTION = ("regle", "cible", "date", "raison", "levee_par")


class BaseIndisponible(RuntimeError):
    """La base de comparaison n'a pas pu être lue : ni vert ni rouge, une panne."""


class Anomalie(NamedTuple):
    regle: str
    cible: str
    message: str


@dataclass
class Resultat:
    refus: list[Anomalie] = field(default_factory=list)
    excusees: list[tuple[Anomalie, dict]] = field(default_factory=list)
    plugins: int = 0
    skills: int = 0
    agents: int = 0

    @property
    def ok(self) -> bool:
        return not self.refus


# --------------------------------------------------------------------------
# Lecture du frontmatter — sans PyYAML, pour les formes que ce dépôt emploie
# --------------------------------------------------------------------------

_CLE = re.compile(r"^([A-Za-z_][\w-]*):(?:[ \t]+(.*))?$")


def _sans_guillemets(valeur: str) -> str:
    valeur = valeur.strip()
    if len(valeur) >= 2 and valeur[0] == valeur[-1] == '"':
        return valeur[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(valeur) >= 2 and valeur[0] == valeur[-1] == "'":
        return valeur[1:-1].replace("''", "'")
    return valeur


def _bloc(lignes: list[str], style: str) -> str:
    """Corps d'un scalaire de bloc (``>``, ``>-``, ``|``, ``|-``) déjà découpé."""
    non_vides = [ligne for ligne in lignes if ligne.strip()]
    if not non_vides:
        return ""
    indent = min(len(ligne) - len(ligne.lstrip(" ")) for ligne in non_vides)
    contenu = [ligne[indent:] if ligne.strip() else "" for ligne in lignes]
    while contenu and contenu[-1] == "":
        contenu.pop()
    if style.startswith("|"):
        texte = "\n".join(contenu)
    else:
        morceaux: list[str] = []
        for ligne in contenu:
            if ligne == "":
                morceaux.append("\n")
            elif morceaux and morceaux[-1] != "\n":
                morceaux.append(" " + ligne)
            else:
                morceaux.append(ligne)
        texte = "".join(morceaux)
    return texte if style.endswith("-") else texte + "\n"


def lire_frontmatter(texte: str) -> dict:
    """Les champs de premier niveau du frontmatter : ``str`` ou ``list[str]``.

    Couvre les formes du dépôt : scalaire nu ou entre guillemets, bloc replié
    ou littéral, liste en tirets, liste en ligne ``[a, b]``. Un fichier sans
    frontmatter rend ``{}``.
    """
    lignes = texte.splitlines()
    if not lignes or lignes[0].strip() != "---":
        return {}
    fin = next((i for i in range(1, len(lignes)) if lignes[i].strip() == "---"), None)
    if fin is None:
        return {}
    corps = lignes[1:fin]

    champs: dict = {}
    i = 0
    while i < len(corps):
        m = _CLE.match(corps[i])
        if not m:
            i += 1
            continue
        cle, valeur = m.group(1), (m.group(2) or "").strip()
        i += 1
        suite: list[str] = []
        while i < len(corps) and (not corps[i].strip() or corps[i][0] in " \t-"):
            if _CLE.match(corps[i]):
                break
            suite.append(corps[i])
            i += 1
        if valeur[:1] in (">", "|"):
            champs[cle] = _bloc(suite, valeur)
        elif valeur.startswith("["):
            champs[cle] = [_sans_guillemets(x) for x in valeur.strip("[]").split(",") if x.strip()]
        elif valeur:
            champs[cle] = _sans_guillemets(valeur)
        else:
            items = [ligne.strip()[1:].strip() for ligne in suite if ligne.strip().startswith("-")]
            if items:
                champs[cle] = [_sans_guillemets(x) for x in items]
            else:
                champs[cle] = " ".join(ligne.strip() for ligne in suite if ligne.strip())
    return champs


def _texte(champs: dict, cle: str) -> str:
    valeur = champs.get(cle, "")
    return valeur if isinstance(valeur, str) else " ".join(valeur)


def _liste(champs: dict, cle: str) -> list[str] | None:
    valeur = champs.get(cle)
    if valeur is None:
        return None
    return [valeur] if isinstance(valeur, str) else list(valeur)


# --------------------------------------------------------------------------
# Les règles
# --------------------------------------------------------------------------

def _rel(racine: Path, chemin: Path) -> str:
    return chemin.relative_to(racine).as_posix()


def _milliers(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _regle_a(cible: str, champs: dict) -> list[Anomalie]:
    longueur = len(_texte(champs, "description").rstrip("\n")) + len(
        _texte(champs, "when_to_use").rstrip("\n"))
    if longueur <= PLAFOND_DESCRIPTION:
        return []
    return [Anomalie("a", cible, (
        f"`description` + `when_to_use` font {longueur} caractères, au-dessus de "
        f"{_milliers(PLAFOND_DESCRIPTION)} : Claude Code tronque la fin dans "
        "la liste des skills. Raccourcir (de "
        f"{longueur - PLAFOND_DESCRIPTION} caractères au moins) en mettant les phrases "
        "de déclenchement d'abord et le détail dans le corps du fichier."))]


def _taille(chemin: Path) -> tuple[int, int]:
    brut = chemin.read_bytes()
    return len(brut.decode("utf-8", errors="replace").splitlines()), len(brut)


def _regle_b(cible: str, chemin: Path, limites: dict) -> list[Anomalie]:
    plafonds = limites.get("taille_skill_md", {}).get(cible)
    if not isinstance(plafonds, dict):
        return [Anomalie("b", cible, (
            "aucun plafond de taille dans scripts/limites.json (`taille_skill_md`). "
            "Ajouter une entrée avec la taille actuelle : "
            f"{{\"lignes\": {_taille(chemin)[0]}, \"octets\": {_taille(chemin)[1]}}}."))]
    lignes, octets = _taille(chemin)
    anomalies = []
    for unite, valeur in (("lignes", lignes), ("octets", octets)):
        plafond = plafonds.get(unite)
        if plafond is not None and valeur > plafond:
            anomalies.append(Anomalie("b", cible, (
                f"{valeur} {unite}, au-dessus du plafond de {plafond} posé dans "
                "scripts/limites.json. Réduire le fichier (déplacer du détail dans "
                "`_partage/`) : le plafond ne peut que baisser, jamais monter.")))
    return anomalies


_TITRE_INVARIANTS = re.compile(r"^(#{1,6})\s+.*\binvariants?\b", re.IGNORECASE)


def _regle_c(cible: str, texte: str) -> list[Anomalie]:
    lignes = texte.splitlines()
    debut = next((i for i, ligne in enumerate(lignes[:LIGNES_INVARIANTS])
                  if _TITRE_INVARIANTS.match(ligne)), None)
    if debut is None:
        return [Anomalie("c", cible, (
            f"ce skill est marqué dans limites.json (`invariants_en_tete`) mais n'a pas de "
            f"bloc « Invariants » (un titre) dans ses {LIGNES_INVARIANTS} premières lignes. "
            "Ajouter le bloc en tête : à la compaction, seuls les "
            f"{_milliers(JETONS_INVARIANTS)} premiers jetons du skill survivent."))]
    niveau = len(_TITRE_INVARIANTS.match(lignes[debut]).group(1))
    fin = len(lignes)
    for j in range(debut + 1, len(lignes)):
        m = re.match(r"^(#{1,6})\s", lignes[j])
        if m and len(m.group(1)) <= niveau:
            fin = j
            break
    octets = len("\n".join(lignes[:fin]).encode("utf-8"))
    jetons = math.ceil(octets / OCTETS_PAR_JETON)
    if jetons > JETONS_INVARIANTS:
        return [Anomalie("c", cible, (
            f"le bloc « Invariants » se termine vers {jetons} jetons estimés, au-delà des "
            f"{_milliers(JETONS_INVARIANTS)} premiers jetons que la compaction conserve. "
            "Raccourcir le bloc ou le remonter."))]
    return []


def _regle_d(racine: Path, plugin: Path) -> list[Anomalie]:
    agents = sorted(p.stem for p in (plugin / "agents").glob("*.md"))
    if not agents:
        return []
    manifeste = plugin / ".claude-plugin" / "plugin.json"
    try:
        description = str(json.loads(manifeste.read_text(encoding="utf-8")).get("description", ""))
    except (OSError, json.JSONDecodeError):
        description = ""
    absents = [a for a in agents
               if not re.search(rf"(?<![\w-]){re.escape(a)}(?![\w-])", description)]
    if not absents:
        return []
    return [Anomalie("d", _rel(racine, manifeste), (
        "la `description` de plugin.json ne cite pas ces agents de `agents/` : "
        + ", ".join(absents) + ". Les ajouter à la description (c'est ce que "
        "voit un lecteur du manifeste) — attention : toucher plugin.json exige de "
        "monter la version du plugin."))]


_RENVOI_PARTAGE = re.compile(r"_partage/([\w-]+(?:\.[\w-]+)*)")


def _compagnons(texte: str) -> set[str] | None:
    """Fichiers ``_partage/`` de la liste « Ses compagnons sont … » (jusqu'à la ligne vide)."""
    lignes = texte.splitlines()
    for i, ligne in enumerate(lignes):
        if re.search(r"compagnons sont", ligne, re.IGNORECASE):
            paragraphe = []
            for suite in lignes[i:]:
                if not suite.strip():
                    break
                paragraphe.append(suite)
            return set(_RENVOI_PARTAGE.findall("\n".join(paragraphe)))
    return None


def _regles_e(racine: Path, plugin: Path) -> list[Anomalie]:
    partage = plugin / "skills" / "_partage"
    fichiers = sorted(p.name for p in partage.glob("*") if p.is_file()) if partage.is_dir() else []
    skills = sorted(plugin.glob("skills/*/SKILL.md"))
    agents = sorted(plugin.glob("agents/*.md"))
    anomalies: list[Anomalie] = []

    cites: set[str] = set()
    par_skill: dict[Path, set[str]] = {}
    for source in skills + agents:
        trouves = set(_RENVOI_PARTAGE.findall(source.read_text(encoding="utf-8"))) & set(fichiers)
        cites |= trouves
        par_skill[source] = trouves

    for nom in fichiers:
        if nom not in cites:
            anomalies.append(Anomalie("e", _rel(racine, partage / nom), (
                f"`_partage/{nom}` n'est cité par aucun skill ni agent : il est livré "
                "avec le plugin sans que personne ne le lise. Le citer là où il sert, "
                "ou le supprimer.")))

    for skill in skills:
        cites_ici = par_skill[skill]
        if not cites_ici:
            continue
        liste = _compagnons(skill.read_text(encoding="utf-8"))
        cible = _rel(racine, skill)
        if liste is None:
            anomalies.append(Anomalie("e", cible, (
                "ce skill cite des fichiers de `_partage/` mais n'a pas de liste « Ses "
                "compagnons sont les fichiers partagés … » : en ajouter une, complète.")))
            continue
        manquants = sorted(cites_ici - liste)
        if manquants:
            anomalies.append(Anomalie("e", cible, (
                "la liste des compagnons du skill oublie des fichiers `_partage/` qu'il cite : "
                + ", ".join(manquants) + ". Les ajouter à la liste « Ses compagnons sont … » "
                "(toucher un skill exige de monter la version du plugin).")))
    return anomalies


def _regles_agent(cible: str, champs: dict) -> list[Anomalie]:
    anomalies = []
    for champ in CHAMPS_IGNORES_POUR_UN_AGENT_DE_PLUGIN:
        if champ in champs:
            anomalies.append(Anomalie("f", cible, (
                f"le champ `{champ}` est ignoré pour un agent de plugin : il tromperait "
                "le lecteur sur ce qui est appliqué. Le retirer (ou copier l'agent dans "
                ".claude/agents/ s'il en faut vraiment un).")))
    if "memory" in champs:
        interdit = _liste(champs, "disallowedTools") or []
        autorise = _liste(champs, "tools")
        lecture_seule = bool({"Write", "Edit"} & set(interdit)) or (
            autorise is not None and not ({"Write", "Edit"} & set(autorise)))
        if lecture_seule:
            anomalies.append(Anomalie("g", cible, (
                "cet agent s'interdit Write/Edit mais déclare `memory` : la mémoire active "
                "Read, Write et Edit d'office et défait l'interdit. Retirer `memory`.")))
    return anomalies


def _regle_h(racine: Path) -> list[Anomalie]:
    trouves = []
    for chemin in sorted(racine.rglob("agent-memory*")):
        if chemin.parent.name == ".claude" and ".git" not in chemin.relative_to(racine).parts:
            trouves.append(chemin)
    return [Anomalie("h", _rel(racine, c), (
        "dossier de mémoire d'agent dans le dépôt : c'est de l'état personnel, pas du code. "
        "Le supprimer et ne jamais le versionner.")) for c in trouves]


def _dossiers_de_cas(evals_plugin: Path) -> list[str]:
    return sorted(d.name for d in evals_plugin.iterdir()
                  if d.is_dir() and ((d / "prompt.md").is_file() or (d / "case.yaml").is_file()))


def _fichiers_a_exercer(plugin: Path) -> list[str]:
    """Chemins (relatifs au plugin) des fichiers sous ``skills/`` et ``agents/``.

    Énumérés sur le disque, comme les règles d et e : les tests posent un dépôt
    jetable qui n'est pas un dépôt git. Les caches de Python sont ignorés.
    """
    trouves = []
    for dossier in ("skills", "agents"):
        for chemin in sorted((plugin / dossier).rglob("*")):
            if chemin.is_file() and "__pycache__" not in chemin.parts and chemin.suffix != ".pyc":
                trouves.append(chemin.relative_to(plugin).as_posix())
    return trouves


def _regle_i(racine: Path, plugin: Path) -> list[Anomalie]:
    evals_plugin = racine / "evals" / plugin.name
    if not evals_plugin.is_dir():
        return []
    fichier = racine / "evals" / "categories.json"
    cible = _rel(racine, fichier)
    qui = f"le plugin `{plugin.name}` a un banc `evals/{plugin.name}/`"
    if not fichier.is_file():
        return [Anomalie("i", cible, (
            f"{qui} mais `evals/categories.json` n'existe pas : le créer, avec une entrée "
            f"`\"{plugin.name}\"` qui classe chaque cas dans au moins une catégorie."))]
    try:
        brut = json.loads(fichier.read_text(encoding="utf-8"))
        categories = brut[plugin.name]
        if not isinstance(categories, dict) or not all(
                isinstance(c, dict) and isinstance(c.get("cas"), list)
                and isinstance(c.get("exerce"), list) for c in categories.values()):
            raise TypeError("catégories mal formées")
    except (OSError, json.JSONDecodeError):
        return [Anomalie("i", cible, "`evals/categories.json` n'est pas du JSON lisible : le corriger.")]
    except (KeyError, TypeError):
        return [Anomalie("i", cible, (
            f"{qui} mais `evals/categories.json` n'a pas d'entrée exploitable `\"{plugin.name}\"` : "
            "un objet {catégorie: {\"exerce\": [chemins], \"cas\": [noms]}}."))]

    anomalies: list[Anomalie] = []
    cas_du_banc = _dossiers_de_cas(evals_plugin)
    classes = {c for cat in categories.values() for c in cat["cas"]}
    for cas in cas_du_banc:
        if cas not in classes:
            anomalies.append(Anomalie("i", cible, (
                f"le cas `{cas}` (evals/{plugin.name}/{cas}) n'est dans aucune catégorie : "
                "l'ajouter au `cas` d'une catégorie de `evals/categories.json`, faute de quoi "
                "une PR qui choisit ses catégories ne le jouera jamais.")))
    for nom, cat in sorted(categories.items()):
        if not cat["cas"]:
            anomalies.append(Anomalie("i", cible, (
                f"la catégorie `{nom}` n'a aucun cas : lui en donner un, ou la supprimer de "
                "`evals/categories.json`.")))
        for cas in cat["cas"]:
            if cas not in cas_du_banc:
                anomalies.append(Anomalie("i", cible, (
                    f"la catégorie `{nom}` cite le cas `{cas}`, qui n'existe pas dans "
                    f"`evals/{plugin.name}/` : corriger le nom ou créer le cas.")))
        for chemin in cat["exerce"]:
            if not (plugin / str(chemin)).exists():
                anomalies.append(Anomalie("i", cible, (
                    f"la catégorie `{nom}` dit exercer `{chemin}`, qui n'existe pas sous "
                    f"`plugins/{plugin.name}/` : corriger le chemin (relatif au plugin), "
                    "ou retirer la ligne.")))

    # Sens inverse : chaque fichier de skills/ et agents/ est exercé par une catégorie.
    prefixes = [str(c) for cat in categories.values() for c in cat["exerce"]]
    for relatif in _fichiers_a_exercer(plugin):
        if not any(relatif.startswith(p) for p in prefixes):
            anomalies.append(Anomalie("i", cible, (
                f"le fichier `plugins/{plugin.name}/{relatif}` n'est exercé par aucune catégorie : "
                "le déclarer dans la liste `exerce` d'une catégorie de `evals/categories.json` "
                "(chemin relatif au plugin) — celle dont un cas le teste. Sans cela, une PR qui le "
                "touche ne sait pas quoi jouer.")))
    return anomalies


# --------------------------------------------------------------------------
# Contrôle d'ensemble, exceptions, cliquet, registre
# --------------------------------------------------------------------------

def controler(racine: Path, limites: dict, sans_exceptions: bool = False) -> Resultat:
    resultat = Resultat()
    anomalies: list[Anomalie] = []
    marques = set(limites.get("invariants_en_tete", []))

    plugins_dir = racine / "plugins"
    plugins = [p for p in sorted(plugins_dir.iterdir())
               if p.is_dir() and not p.name.startswith(".")] if plugins_dir.is_dir() else []
    resultat.plugins = len(plugins)

    for plugin in plugins:
        for skill in sorted(plugin.glob("skills/*/SKILL.md")):
            resultat.skills += 1
            cible = _rel(racine, skill)
            texte = skill.read_text(encoding="utf-8")
            anomalies += _regle_a(cible, lire_frontmatter(texte))
            anomalies += _regle_b(cible, skill, limites)
            if cible in marques:
                anomalies += _regle_c(cible, texte)
        for agent in sorted(plugin.glob("agents/*.md")):
            resultat.agents += 1
            cible = _rel(racine, agent)
            champs = lire_frontmatter(agent.read_text(encoding="utf-8"))
            anomalies += _regle_a(cible, champs)
            anomalies += _regles_agent(cible, champs)
        anomalies += _regle_d(racine, plugin)
        anomalies += _regles_e(racine, plugin)
        anomalies += _regle_i(racine, plugin)
    anomalies += _regle_h(racine)

    exceptions = [] if sans_exceptions else list(limites.get("exceptions", []))
    utilisees: set[int] = set()
    for anomalie in anomalies:
        excuse = next(
            (k for k, exc in enumerate(exceptions)
             if exc.get("regle") == anomalie.regle and exc.get("cible") == anomalie.cible
             and all(exc.get(c) for c in CHAMPS_D_UNE_EXCEPTION)), None)
        if excuse is None:
            resultat.refus.append(anomalie)
        else:
            utilisees.add(excuse)
            resultat.excusees.append((anomalie, exceptions[excuse]))

    for k, exc in enumerate(exceptions):
        manquants = [c for c in CHAMPS_D_UNE_EXCEPTION if not exc.get(c)]
        cible = str(exc.get("cible", "?"))
        if manquants:
            resultat.refus.append(Anomalie("exception", cible, (
                "exception incomplète dans limites.json, il manque : " + ", ".join(manquants)
                + ". Une exception dit sa date, sa raison et l'étape qui la lève.")))
        elif k not in utilisees:
            resultat.refus.append(Anomalie("exception", cible, (
                f"exception ({exc['regle']}) périmée : plus aucun défaut ne lui correspond. "
                "La retirer de scripts/limites.json.")))
    return resultat


def verifier_cliquet(limites: dict, limites_base: dict | None) -> list[Anomalie]:
    """Les plafonds de ``limites.json`` ne peuvent que baisser par rapport à la base."""
    if limites_base is None:
        return []
    anomalies: list[Anomalie] = []
    for fichier, ancien in limites_base.get("taille_skill_md", {}).items():
        nouveau = limites.get("taille_skill_md", {}).get(fichier)
        if nouveau is None:
            anomalies.append(Anomalie("b", fichier, (
                "le plafond de ce fichier a disparu de limites.json : retirer un plafond "
                "revient à le relever à l'infini. Le remettre.")))
            continue
        for unite in ("lignes", "octets"):
            if nouveau.get(unite, math.inf) > ancien.get(unite, math.inf):
                anomalies.append(Anomalie("b", fichier, (
                    f"plafond de {unite} relevé de {ancien.get(unite)} à {nouveau.get(unite)} "
                    "dans limites.json : un plafond ne peut que baisser. Réduire le fichier "
                    "au lieu de relever le plafond.")))
    ancien = limites_base.get("veille_jours_max")
    nouveau = limites.get("veille_jours_max")
    if ancien is not None and (nouveau is None or nouveau > ancien):
        anomalies.append(Anomalie("veille", "scripts/limites.json", (
            f"le seuil `veille_jours_max` passe de {ancien} à {nouveau} : il ne peut que baisser.")))
    return anomalies


def lire_limites_base(racine: Path, base: str) -> dict | None:
    """``scripts/limites.json`` tel que la base l'a ; ``None`` s'il n'y existait pas."""
    connu = subprocess.run(["git", "cat-file", "-e", f"{base}^{{commit}}"], cwd=racine,
                           capture_output=True, text=True)
    if connu.returncode != 0:
        raise BaseIndisponible(f"la base `{base}` est introuvable dans ce clone "
                               "(faire `git fetch origin main`, ou passer --base / BASE_REF)")
    lu = subprocess.run(["git", "show", f"{base}:scripts/limites.json"], cwd=racine,
                        capture_output=True, text=True)
    if lu.returncode != 0:
        return None
    try:
        return json.loads(lu.stdout)
    except json.JSONDecodeError as erreur:
        raise BaseIndisponible(f"limites.json de `{base}` est illisible ({erreur})") from erreur


_STATUTS = ("en place", "réglage", "prévu", "manquant")


def _jeton_verifiable(jeton: str) -> bool:
    return "#" in jeton or "/" in jeton or jeton.endswith((".py", ".sh", ".yml", ".yaml", ".json", ".md"))


def _garde_existe(racine: Path, jeton: str) -> tuple[bool, str]:
    if "#" in jeton:
        fichier, job = jeton.split("#", 1)
        chemin = racine / (fichier if "/" in fichier else f".github/workflows/{fichier}")
        if not chemin.is_file():
            return False, f"`{jeton}` : le workflow {chemin.relative_to(racine).as_posix()} n'existe pas"
        if not re.search(rf"^  {re.escape(job)}:\s*$", chemin.read_text(encoding="utf-8"), re.MULTILINE):
            return False, f"`{jeton}` : aucun job `{job}` dans {chemin.name}"
        return True, ""
    if "/" in jeton:
        chemin = racine / jeton
    elif jeton.endswith((".py", ".sh")):
        chemin = racine / "scripts" / jeton
    elif jeton.endswith((".yml", ".yaml")):
        chemin = racine / ".github" / "workflows" / jeton
    else:
        chemin = racine / jeton
    if not chemin.exists():
        return False, f"`{jeton}` n'existe pas"
    return True, ""


def verifier_registre(racine: Path) -> list[Anomalie]:
    """Chaque garde que le registre dit « en place » existe ; les autres disent leur statut."""
    registre = racine / "docs" / "garde-fous.md"
    cible = "docs/garde-fous.md"
    if not registre.is_file():
        return [Anomalie("registre", cible, "le registre des garde-fous est absent : le créer.")]

    anomalies: list[Anomalie] = []
    lignes = 0
    for numero, ligne in enumerate(registre.read_text(encoding="utf-8").splitlines(), start=1):
        if not ligne.lstrip().startswith("|"):
            continue
        cellules = [c.strip() for c in ligne.strip().strip("|").split("|")]
        if set("".join(cellules)) <= set("-: ") or cellules[0].lower().startswith("règle"):
            continue
        lignes += 1
        if len(cellules) != 6:
            anomalies.append(Anomalie("registre", f"{cible}:{numero}", (
                f"{len(cellules)} colonnes au lieu de 6 (Règle, Ce qu'elle protège, Origine, "
                "Garde, Où il tourne, Statut).")))
            continue
        nom, garde, statut = cellules[0], cellules[3], cellules[5].lower()
        lieu = f"{cible}:{numero}"
        if not statut.startswith(_STATUTS):
            anomalies.append(Anomalie("registre", lieu, (
                f"« {nom} » : statut « {cellules[5]} » inconnu. Attendu : "
                + ", ".join(_STATUTS) + " (« prévu — étape X »).")))
        elif statut.startswith("prévu") and "étape" not in statut:
            anomalies.append(Anomalie("registre", lieu, (
                f"« {nom} » : un garde prévu dit son étape (« prévu — étape B5 »).")))
        elif statut.startswith("en place"):
            jetons = [j for j in re.findall(r"`([^`]+)`", garde) if _jeton_verifiable(j)]
            if not jetons:
                anomalies.append(Anomalie("registre", lieu, (
                    f"« {nom} » est « en place » mais cite aucun garde vérifiable (script, "
                    "`ci.yml#job`, cas d'éval) : citer le garde en code, ou changer le statut.")))
            for jeton in jetons:
                existe, raison = _garde_existe(racine, jeton)
                if not existe:
                    anomalies.append(Anomalie("registre", lieu, f"« {nom} » cite un garde inexistant : {raison}."))
    if lignes == 0:
        anomalies.append(Anomalie("registre", cible, "aucune ligne de règle dans le registre : un registre vide ne protège rien."))
    return anomalies


# --------------------------------------------------------------------------
# Programme
# --------------------------------------------------------------------------

def _afficher_exceptions(resultat: Resultat) -> None:
    for anomalie, exc in resultat.excusees:
        print(f"EXCEPTION ({anomalie.regle}) {anomalie.cible} — depuis {exc['date']} — "
              f"{exc['raison']} — levée par : {exc['levee_par']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--racine", type=Path, default=REPO_ROOT)
    parser.add_argument("--limites", type=Path, default=None,
                        help="fichier de plafonds et d'exceptions (défaut : "
                             "<racine>/scripts/limites.json)")
    parser.add_argument("--base", default=os.environ.get("BASE_REF", "origin/main"),
                        help="référence git dont on lit limites.json pour le cliquet "
                             "(défaut : $BASE_REF, sinon origin/main)")
    parser.add_argument("--sans-base", action="store_true",
                        help="sauter le cliquet (aucune base disponible)")
    parser.add_argument("--sans-exceptions", action="store_true",
                        help="ignorer les exceptions datées : montre l'état réel")
    args = parser.parse_args(argv)

    chemin_limites = args.limites or args.racine / "scripts" / "limites.json"
    try:
        limites = json.loads(chemin_limites.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erreur:
        print(f"check_skills : {chemin_limites} illisible ({erreur}).", file=sys.stderr)
        return 2

    resultat = controler(args.racine, limites, sans_exceptions=args.sans_exceptions)
    resultat.refus += verifier_registre(args.racine)
    if not args.sans_base:
        try:
            resultat.refus += verifier_cliquet(limites, lire_limites_base(args.racine, args.base))
        except BaseIndisponible as panne:
            print(f"check_skills : cliquet impossible — {panne}.", file=sys.stderr)
            return 2

    _afficher_exceptions(resultat)
    if resultat.refus:
        for a in resultat.refus:
            print(f"({a.regle}) {a.cible} — {a.message}", file=sys.stderr)
        print(f"check_skills : {len(resultat.refus)} règle(s) violée(s).", file=sys.stderr)
        return 1
    print(f"check_skills : {resultat.plugins} plugin(s), {resultat.skills} skill(s), "
          f"{resultat.agents} agent(s) contrôlés ; {len(resultat.excusees)} exception(s) datée(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
