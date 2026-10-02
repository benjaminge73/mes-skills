#!/usr/bin/env python3
"""Le plancher des évals : quels cas jouer pour une PR, et lesquels on ne peut pas omettre.

Décision de Benjamin (plan « Chercher, prouver, paralléliser #2 », étape B9) :
ne pas rejouer tout le banc à chaque PR, le découper par catégorie et laisser
chaque plan dire lesquelles il joue. Le plan choisit, **et la CI tient un
plancher** : ce script est ce plancher.

**À la demande** (plan « Évals sobres et machine partagée », étape 1) : le banc
coûte ~55 $ en entier, il ne se joue plus sans qu'on le demande. La CI ne joue
les évals que si la PR porte le label ``evals``. Une PR qui touche un skill, un
agent, un hook ou un ``_partage/`` **sans** ce label doit porter ``Evals: aucun
— <raison>`` dans son corps, sinon elle est refusée (code 1) : le silence n'est
plus une réponse. Il est joué par le job ``evals-portee``
de ``ci.yml`` et n'est jamais du bash dans le workflow, pour être testé
(``scripts/test_evals_selection.py``).

Entrées
-------
``--plugin <nom>``       le plugin dont on calcule la sélection.
``--fichiers <fichier>`` les chemins touchés par la PR, un par ligne (la sortie
                         de ``git diff --name-only``).
``--categories <chemin>`` défaut : ``evals/categories.json``. Pour chaque plugin,
                         chaque catégorie dit ce qu'elle **exerce** (des chemins
                         relatifs à ``plugins/<plugin>/``, en préfixe) et les
                         **cas** qui la jouent.
``--labels <texte>``     les labels de la PR, un par ligne (``gh api … --jq
                         '.labels[].name'``). Vide : aucun label. Seul le label
                         ``evals`` compte (casse indifférente) ; il est relu par
                         l'API à chaque run, jamais lu dans le payload.
``--fumee``              autre sortie, pour le job ``fumee`` : voir « La fumée » plus bas.
``PR_BODY`` (environnement) le corps de la PR. Jamais en argument : un corps de
                         PR est une entrée non fiable, et une variable
                         d'environnement n'est jamais interprétée par un shell.

La ligne du corps de PR
-----------------------
Une ligne qui commence par ``Evals:`` (casse et espaces indifférents), suivie de
catégories séparées par des virgules, ou du mot ``tout``, puis facultativement
`` — raison`` (tiret cadratin ou ``--``) ::

    Evals: existant, bruit — B1 ne touche que la recherche de l'existant
    Evals: tout
    Evals: aucun — doc seule, aucun comportement ne change

``aucun`` est la sortie **sans label** : la raison est obligatoire, et le mot ne
se combine ni avec une catégorie ni avec le label ``evals`` (ce serait demander
et refuser les évals à la fois).

Une catégorie se cherche dans **tous** les plugins de ``categories.json`` : la
même ligne sert une PR qui touche deux plugins, chacun n'en retenant que ses
propres catégories.

Les règles, dans l'ordre
------------------------
0. **Sans le label ``evals``** : rien ne se joue. ``Evals: aucun — <raison>`` est
   accepté (sélection vide) ; ``aucun`` sans raison, ou combiné à une catégorie,
   est refusé. Sans ligne ``aucun``, une PR qui touche ``plugins/<p>/skills/``
   (``_partage/`` compris), ``agents/`` ou ``hooks/`` est refusée, avec les deux
   sorties dans le message (poser le label, ou écrire la ligne) ; une PR qui n'en
   touche aucun passe, sélection vide. **Avec** le label, ``aucun`` est refusé
   (contradiction) et les règles suivantes s'appliquent.
1. Une catégorie que **aucun** plugin ne déclare : refus (code 1), avec la liste
   des catégories connues — même si autre chose force déjà « tout » : une faute
   de frappe se dit tout de suite.
2. Ligne absente, vide ou ``tout`` : ``tout``.
3. Un fichier touché du socle commun : ``tout``, quelle que soit la ligne —
   ``plugins/<p>/hooks/``, ``evals/<p>/``, ``evals/outillage/``,
   ``evals/categories.json``, ``scripts/evals_ab.py``,
   ``scripts/evals_selection.py`` et ``.github/workflows/ci.yml``. Ce qui touche
   le banc lui-même ne peut pas être prouvé par une partie du banc. Depuis
   l'étape D5 du plan « Évals sobres et machine partagée », ``skills/_partage/``
   n'en fait **plus** partie : chaque fichier partagé déclare, dans ``exerce``,
   les catégories qui le testent (la règle 4 s'applique, comme à un skill).
4. Un fichier touché sous ``plugins/<p>/skills/`` (``_partage/`` compris) ou
   ``agents/`` qu'**aucune** catégorie n'exerce : ``tout`` (défaut prudent : un
   fichier que le classement ne connaît pas est un fichier dont on ne sait pas
   quoi jouer). ``check_skills.py`` (règle i) refuse justement qu'un tel fichier
   existe dans un plugin qui a un banc : ce défaut ne joue qu'en cas de filet.
5. Sinon, chaque fichier touché sous ``skills/`` ou ``agents/`` doit être exercé
   par au moins une catégorie **choisie** ; sinon refus (code 1), avec le
   fichier non couvert et les catégories qui le couvriraient.

La fumée
--------
``--fumee`` (plan « Évals sobres et machine partagée », étape 12) dit quelles
catégories le test de fumée joue pour une PR **sans** le label ``evals`` (avec lui,
l'A/B remplace la fumée : c'est ``ci.yml`` qui en décide, pas ce script). Elle ne
lit ni le corps de la PR ni ``--labels`` : seuls les fichiers touchés comptent.
Sous ``plugins/<p>/skills/``, ``agents/`` et ``hooks/`` : un fichier que des
catégories exercent rend ces catégories — un fichier de ``skills/_partage/`` compris,
comme un skill ; ``hooks/`` et un fichier qu'aucune catégorie n'exerce rendent **toutes**
celles du plugin (le défaut prudent de la règle 4). Aucun de ces dossiers touché : sélection vide. Chaque
catégorie retenue garde **tous** ses cas (``cas``) : la fumée juge une catégorie
sur les seuls cas joués. Un plugin sans catégorie déclarée est refusé (code 1) :
il n'y aurait aucun plancher à tenir.

Sortie et codes
---------------
Sur stdout, une ligne de JSON : ``{"plugin", "tout", "categories", "cas",
"raison", "pourquoi_tout"}``. Sans label, ``tout`` vaut ``false``, ``categories``
et ``cas`` sont vides : le workflow ne joue rien. Avec ``tout``, ``categories`` et ``cas`` sont ceux
de **tout** le plugin ; ``pourquoi_tout`` dit le motif, et reste vide sinon.
``raison`` (tronquée à 300 caractères) est la justification écrite dans la
ligne. Codes : ``0`` sélection rendue, ``1`` refus (message sur stderr), ``2``
panne (fichier illisible, ``categories.json`` mal formé).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[1]
RAISON_MAX = 300

# Le socle commun à tous les plugins (chemins exacts ou préfixes de dossier).
SOCLE_GLOBAL = (
    "evals/outillage/",
    "evals/categories.json",
    "scripts/evals_ab.py",
    "scripts/evals_selection.py",
    ".github/workflows/ci.yml",
)

_LIGNE = re.compile(r"^[ \t]*evals[ \t]*:(.*)$", re.IGNORECASE)
_RAISON = re.compile(r"\s*(?:—|--)\s*")


SUITE = ("Corriger la ligne « Evals: » du corps de la PR, puis relancer le run "
         "(Re-run all jobs) ou pousser un commit")

LABEL_EVALS = "evals"

# Les dossiers d'un plugin dont la modification change ce que les évals mesurent
# (``_partage/`` vit sous ``skills/``).
DOSSIERS_QUI_CHANGENT_UN_COMPORTEMENT = ("skills/", "agents/", "hooks/")


class Refus(Exception):
    """Une PR que le plancher refuse (code 1)."""


class Panne(Exception):
    """Une entrée illisible : ni vert ni rouge (code 2)."""


def lire_ligne(corps: str) -> tuple[list[str], str] | None:
    """(catégories en minuscules, raison) de la première ligne ``Evals:``, ou None."""
    for ligne in corps.splitlines():
        m = _LIGNE.match(ligne)
        if m:
            tete, *reste = _RAISON.split(m.group(1), maxsplit=1)
            noms = [x.strip().lower() for x in tete.split(",") if x.strip()]
            return noms, (reste[0].strip() if reste else "")[:RAISON_MAX]
    return None


def a_le_label(labels: str) -> bool:
    """Le label ``evals`` figure-t-il parmi les labels (un par ligne) ?"""
    return any(x.strip().lower() == LABEL_EVALS for x in labels.splitlines())


def lire_categories(chemin: Path) -> dict[str, dict[str, dict]]:
    """``{plugin: {catégorie: {"exerce": [...], "cas": [...]}}}`` ; ``Panne`` si mal formé."""
    try:
        brut = json.loads(Path(chemin).read_text("utf-8"))
    except (OSError, ValueError) as e:
        raise Panne(f"{chemin} illisible : {e}") from e
    if not isinstance(brut, dict):
        raise Panne(f"{chemin} : un objet {{plugin: {{catégorie: …}}}} est attendu")
    lu: dict[str, dict[str, dict]] = {}
    for plugin, cats in brut.items():
        if plugin.startswith("_"):
            continue
        if not isinstance(cats, dict):
            raise Panne(f"{chemin} : « {plugin} » doit être un objet de catégories")
        lu[plugin] = {}
        for nom, cat in cats.items():
            if (not isinstance(cat, dict)
                    or not isinstance(cat.get("exerce"), list)
                    or not isinstance(cat.get("cas"), list)):
                raise Panne(f"{chemin} : catégorie « {plugin}/{nom} » sans listes `exerce` et `cas`")
            lu[plugin][nom.lower()] = {"exerce": list(cat["exerce"]), "cas": list(cat["cas"])}
    return lu


def lire_fichiers(chemin: Path) -> list[str]:
    try:
        lignes = Path(chemin).read_text("utf-8").splitlines()
    except (OSError, ValueError) as e:
        raise Panne(f"liste de fichiers illisible ({chemin}) : {e}") from e
    fichiers = []
    for ligne in lignes:
        ligne = ligne.strip()
        if ligne.startswith("./"):
            ligne = ligne[2:]
        if ligne:
            fichiers.append(ligne)
    return fichiers


def _union(cats: dict[str, dict], noms: list[str]) -> list[str]:
    cas: list[str] = []
    for nom in noms:
        for c in cats[nom]["cas"]:
            if c not in cas:
                cas.append(c)
    return cas


def _exercee_par(cats: dict[str, dict], relatif: str) -> list[str]:
    return [nom for nom, cat in cats.items()
            if any(relatif.startswith(prefixe) for prefixe in cat["exerce"])]


def _rien_a_jouer(plugin: str, raison: str) -> dict:
    return {"plugin": plugin, "tout": False, "categories": [], "cas": [],
            "raison": raison, "pourquoi_tout": ""}


def _sans_label(plugin: str, fichiers: list[str], noms: list[str], raison: str) -> dict:
    """Sans le label ``evals`` : rien ne se joue, mais le silence n'est pas permis."""
    if "aucun" in noms:
        if len(noms) > 1:
            raise Refus("« aucun » ne se combine pas avec une catégorie : « Evals: aucun — "
                        f"<raison> » dit qu'on ne joue rien. {SUITE}.")
        if not raison:
            raise Refus("« Evals: aucun » demande une raison : écrire « Evals: aucun — "
                        f"<raison> ». {SUITE}.")
        return _rien_a_jouer(plugin, raison)
    racine = f"plugins/{plugin}/"
    changent = [f for f in fichiers
                if any(f.startswith(racine + d) for d in DOSSIERS_QUI_CHANGENT_UN_COMPORTEMENT)]
    if changent:
        raise Refus(
            f"cette PR touche {', '.join(changent)} sans label « {LABEL_EVALS} » ni ligne "
            "« Evals: aucun — <raison> » dans son corps. Deux sorties : poser le label "
            f"« {LABEL_EVALS} » sur la PR (les évals se jouent alors, et le run repart "
            "seul), ou écrire « Evals: aucun — <raison> » dans le corps de la PR, puis "
            "relancer le run (Re-run all jobs) ou pousser un commit.")
    return _rien_a_jouer(plugin, raison)


def selectionner(plugin: str, fichiers: list[str], corps: str,
                 categories: dict[str, dict[str, dict]], labels: str = "") -> dict:
    ligne = lire_ligne(corps)
    noms, raison = ligne if ligne is not None else ([], "")

    # 0. À la demande : sans le label, rien ne se joue.
    if not a_le_label(labels):
        return _sans_label(plugin, fichiers, noms, raison)
    if "aucun" in noms:
        raise Refus(
            f"le label « {LABEL_EVALS} » demande les évals, la ligne « Evals: aucun » les "
            f"refuse : l'un des deux est de trop. Retirer le label « {LABEL_EVALS} » pour ne "
            f"rien jouer, ou remplacer « aucun » par des catégories (ou « tout »). {SUITE}.")

    # 1. Une catégorie que personne ne déclare : une faute de frappe, dite tout de suite.
    connues = sorted({nom for cats in categories.values() for nom in cats})
    inconnues = [n for n in noms if n != "tout" and n not in connues]
    if inconnues:
        raise Refus(
            f"catégorie inconnue : {', '.join(f'« {n} »' for n in inconnues)}. "
            f"Catégories connues : {', '.join(connues)}. {SUITE} (ou écrire « Evals: tout »)."
        )

    cats = categories.get(plugin)
    tout = {"plugin": plugin, "tout": True, "raison": raison}

    def rendre_tout(pourquoi: str) -> dict:
        toutes = list((cats or {}))
        return {**tout, "categories": toutes, "cas": _union(cats or {}, toutes),
                "pourquoi_tout": pourquoi}

    if cats is None:
        return rendre_tout(f"aucune catégorie déclarée pour le plugin « {plugin} » dans "
                           "evals/categories.json")

    # 2. La ligne elle-même.
    if ligne is None:
        return rendre_tout("aucune ligne « Evals: … » dans le corps de la PR")
    if not noms:
        return rendre_tout("la ligne « Evals: » du corps de la PR est vide")
    if "tout" in noms:
        return rendre_tout("la ligne « Evals: tout » le demande")

    # 3. Le socle commun.
    socle = (f"plugins/{plugin}/hooks/", f"evals/{plugin}/", *SOCLE_GLOBAL)
    touche_le_socle = [f for f in fichiers if any(f.startswith(p) for p in socle)]
    if touche_le_socle:
        return rendre_tout(
            "fichier(s) du socle commun touché(s), que seul le banc entier peut prouver : "
            + ", ".join(touche_le_socle))

    # 4 et 5. Skills et agents du plugin : couverts par une catégorie choisie.
    racine = f"plugins/{plugin}/"
    a_couvrir = [f[len(racine):] for f in fichiers
                 if f.startswith((racine + "skills/", racine + "agents/"))]
    sans_categorie = [r for r in a_couvrir if not _exercee_par(cats, r)]
    if sans_categorie:
        return rendre_tout(
            "fichier(s) qu'aucune catégorie n'exerce (défaut prudent : on ne sait pas quoi "
            "jouer) : " + ", ".join(f"{racine}{r}" for r in sans_categorie))

    choisies = [n for n in dict.fromkeys(noms) if n in cats]
    non_couverts = [r for r in a_couvrir
                    if not set(_exercee_par(cats, r)) & set(choisies)]
    if non_couverts:
        detail = "; ".join(
            f"{racine}{r} (catégories qui l'exercent : {', '.join(_exercee_par(cats, r))})"
            for r in non_couverts)
        raise Refus(
            f"modifié(s) mais exercé(s) par aucune catégorie choisie "
            f"({', '.join(choisies) or 'aucune pour ce plugin'}) : {detail}. Ajouter l'une "
            f"de ces catégories à la ligne « Evals: » (ou écrire « Evals: tout »). {SUITE}.")
    return {"plugin": plugin, "tout": False, "categories": choisies,
            "cas": _union(cats, choisies), "raison": raison, "pourquoi_tout": ""}


# Ce qui, touché, fait jouer toute la fumée : le socle d'un plugin, que nulle catégorie
# ne peut prétendre exercer à elle seule. ``skills/_partage/`` n'y est plus depuis D5.
SOCLE_DE_LA_FUMEE = ("hooks/",)


def fumee(plugin: str, fichiers: list[str], categories: dict[str, dict[str, dict]]) -> dict:
    """Les catégories de la fumée de CI pour les fichiers touchés (voir « La fumée »)."""
    racine = f"plugins/{plugin}/"
    relatifs = [f[len(racine):] for f in fichiers
                if f.startswith(tuple(racine + d for d in DOSSIERS_QUI_CHANGENT_UN_COMPORTEMENT))]
    if not relatifs:
        return _rien_a_jouer(plugin, "")
    cats = categories.get(plugin)
    if not cats:
        raise Refus(f"aucune catégorie déclarée pour le plugin « {plugin} » dans "
                    "evals/categories.json : la fumée n'a aucun plancher à tenir.")
    retenues: set[str] = set()
    pourquoi = ""
    for r in relatifs:
        exercees = [] if r.startswith(SOCLE_DE_LA_FUMEE) else _exercee_par(cats, r)
        if exercees:
            retenues.update(exercees)
        elif not pourquoi:
            pourquoi = (f"{racine}{r} : socle commun ou fichier qu'aucune catégorie n'exerce "
                        "(défaut prudent : on ne sait pas quoi jouer)")
    if pourquoi:
        retenues = set(cats)
    noms = [n for n in cats if n in retenues]
    return {"plugin": plugin, "tout": bool(pourquoi), "categories": noms,
            "cas": _union(cats, noms), "raison": "", "pourquoi_tout": pourquoi}


def main(argv: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parseur.add_argument("--plugin", required=True)
    parseur.add_argument("--fichiers", required=True, type=Path,
                         help="chemins touchés, un par ligne (git diff --name-only)")
    parseur.add_argument("--categories", type=Path, default=DEPOT / "evals" / "categories.json")
    parseur.add_argument("--labels", default="",
                         help="labels de la PR, un par ligne ; vide : aucun (rien ne se joue)")
    parseur.add_argument("--fumee", action="store_true",
                         help="les catégories de la fumée de CI (sans label evals) ; "
                              "ignore le corps de la PR et les labels")
    args = parseur.parse_args(argv)
    try:
        categories = lire_categories(args.categories)
        fichiers = lire_fichiers(args.fichiers)
        if args.fumee:
            selection = fumee(args.plugin, fichiers, categories)
        else:
            selection = selectionner(args.plugin, fichiers, os.environ.get("PR_BODY", ""),
                                     categories, args.labels)
    except Panne as e:
        print(f"evals_selection : {e}", file=sys.stderr)
        return 2
    except Refus as e:
        print(f"evals_selection : {e}", file=sys.stderr)
        return 1
    print(json.dumps(selection))
    return 0


if __name__ == "__main__":
    sys.exit(main())
