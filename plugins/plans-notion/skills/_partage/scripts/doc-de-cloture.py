#!/usr/bin/env python3
"""Porte de clôture de la doc vivante : le Récap d'une page de plan, et les PR sans entrée.

Pourquoi un script : la clôture doit poser une entrée au Changelog pour chaque PR mergée,
et « je l'ai fait » se dit sans se vérifier. Une PR oubliée ne se voit pas dans une liste
de cinquante entrées ; ça se compte. Même principe que ``controle-changelog.py``.

Usage :
  doc-de-cloture.py --porte <page.md> [--changelog <changelog.md> --pr N]
                    [--recap-fichier <fichier>] [--lot]
  doc-de-cloture.py --trous --changelog <changelog.md> --prs <prs.json>
                    --depuis AAAA-MM-JJ [--sauf N[,N…]]

Mode --porte, qui refuse le passage à « a merger » quand la doc manque :
  - la page a un H2 dont le titre commence par « Récap » (casse indifférente). Exception,
    le palier 3 : --recap-fichier existant qui porte un tel H2 (le Récap est dans un fichier
    confié à Hermes, la page ne le porte pas encore) ;
  - si --changelog et --pr N sont donnés et que --lot n'est pas donné, une entrée du
    Changelog cite la PR N dans son en-tête. --lot (plan enfant d'un lot : une entrée
    consolidée à la fermeture du lot) dispense de cette seconde exigence, pas de la première.
    --changelog sans --pr, ou --pr sans --changelog, est un usage erroné.

Mode --trous, le rattrapage : liste chaque PR mergée à la date --depuis ou après, qui n'est
pas une PR de dépendances (auteur ``dependabot…`` ou ``app/dependabot``, ou label
``dependencies``), dont le numéro n'est cité dans aucun en-tête du Changelog, et qui n'est
pas dans --sauf. ``<prs.json>`` est la sortie de
``gh pr list --state merged --limit 200 --json number,title,mergedAt,author,labels``.

Un en-tête d'entrée : une ligne H2 dont le titre commence par une date AAAA-MM-JJ ou par
« Récap », suivie de la ligne ``Plan :``, dans les cinq lignes qui suivent le H2 et avant le
prochain titre, toggle ou ligne en gras. Seuls le H2 et sa ligne Plan portent des numéros :
les puces, le bloc « Côté technique » et les phrases d'absence ne comptent pas. Formes
reconnues : ``#N`` (frontière de mot, ``#25`` ne couvre pas ``#258``), ``pull/N``, ``PR N``,
``PR #N``, et les plages ``#A à #B``, ``#A–#B``, ``#A-#B``, ``#A … #B`` (toutes les PR de A à B
incluses).

Sortie : en mode --porte, sans défaut, rien sur la sortie standard ; sinon un défaut par
ligne. En mode --trous, une ligne par PR en trou, ``#N <titre>``, triées par numéro.
Codes : 0 conforme, aucun trou ; 1 au moins un défaut ou un trou ; 2 entrée illisible
(fichier absent, JSON invalide) ou usage erroné, le motif part sur la sortie d'erreur.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RECAP = re.compile(r"^##\s+récap", re.IGNORECASE)
ENTREE = re.compile(r"^##\s+(?:\d{4}-\d{2}-\d{2}\b|récap)", re.IGNORECASE)
DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")
DATE_ARG = re.compile(r"\d{4}-\d{2}-\d{2}")
TITRE = re.compile(r"^#{1,6}\s")
ZONE_MAX = 5

PLAGE = re.compile(r"#(\d+)\s*(?:à|–|-|…)\s*#(\d+)")
NUMERO = re.compile(r"#(\d+)")
PULL = re.compile(r"pull/(\d+)")
PR_MOT = re.compile(r"\bPR\s+#?(\d+)")


class ErreurEntree(Exception):
    """Entrée illisible ou usage erroné : le script rend 2."""


def lire(chemin, role):
    try:
        return Path(chemin).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ErreurEntree(f"{role} illisible : {chemin} ({e})") from None


def _zone(lignes, i):
    """Les lignes d'en-tête après le H2 d'indice i : jusqu'au titre, toggle ou gras suivant."""
    zone = []
    for ligne in lignes[i + 1:i + 1 + ZONE_MAX]:
        if TITRE.match(ligne) or ligne.startswith(("<toggle", "**")):
            break
        zone.append(ligne)
    return zone


def numeros_cites(texte):
    """Les numéros isolés et les plages (a, b) cités dans un texte d'en-tête."""
    plages = [(min(int(a), int(b)), max(int(a), int(b))) for a, b in PLAGE.findall(texte)]
    isoles = {int(n) for n in NUMERO.findall(texte)}
    isoles |= {int(n) for n in PULL.findall(texte)}
    isoles |= {int(n) for n in PR_MOT.findall(texte)}
    return isoles, plages


def en_tetes(lignes):
    """Les PR documentées : numéros isolés et plages, lus dans les en-têtes d'entrée seulement."""
    isoles, plages = set(), []
    for i, ligne in enumerate(lignes):
        if not ENTREE.match(ligne):
            continue
        plan = [ligne_zone for ligne_zone in _zone(lignes, i) if ligne_zone.startswith("Plan :")]
        if not plan:
            continue
        for texte in [ligne, *plan]:
            n, p = numeros_cites(texte)
            isoles |= n
            plages += p
    return isoles, plages


def documentee(numero, isoles, plages):
    return numero in isoles or any(a <= numero <= b for a, b in plages)


def porte(args):
    defauts = []
    page = lire(args.porte, "page du plan")
    if not any(RECAP.match(ligne) for ligne in page.splitlines()):
        palier3 = False
        if args.recap_fichier and Path(args.recap_fichier).is_file():
            texte = lire(args.recap_fichier, "--recap-fichier")
            palier3 = any(RECAP.match(ligne) for ligne in texte.splitlines())
        if not palier3:
            defauts.append("récap absent : la page n'a aucun H2 « Récap » (ni --recap-fichier qui en porte un)")
    if args.changelog and not args.lot:
        isoles, plages = en_tetes(lire(args.changelog, "changelog").splitlines())
        if not documentee(args.pr, isoles, plages):
            defauts.append(f"PR #{args.pr} : aucune entrée du Changelog ne la cite dans son en-tête")
    return defauts


def est_dependance(pr):
    auteur = pr.get("author")
    login = (auteur.get("login") or "") if isinstance(auteur, dict) else ""
    if login.lower().startswith(("dependabot", "app/dependabot")):
        return True
    labels = pr.get("labels") or []
    return any(isinstance(label, dict) and label.get("name") == "dependencies" for label in labels)


def charger_prs(chemin):
    try:
        donnees = json.loads(lire(chemin, "--prs"))
    except json.JSONDecodeError as e:
        raise ErreurEntree(f"JSON invalide : {chemin} ({e.msg}, ligne {e.lineno})") from None
    if not isinstance(donnees, list):
        raise ErreurEntree(f"{chemin} : une liste de PR est attendue")
    for pr in donnees:
        if not isinstance(pr, dict) or not isinstance(pr.get("number"), int):
            raise ErreurEntree(f"{chemin} : une PR sans numéro entier")
        merge = pr.get("mergedAt")
        if merge is not None and not (isinstance(merge, str) and DATE_ISO.match(merge)):
            raise ErreurEntree(f"{chemin} : date de merge illisible pour #{pr['number']}")
    return donnees


def trous(args):
    isoles, plages = en_tetes(lire(args.changelog, "changelog").splitlines())
    restantes = []
    for pr in charger_prs(args.prs):
        merge = pr.get("mergedAt")
        if merge is None or merge[:10] < args.depuis:
            continue
        if est_dependance(pr) or pr["number"] in args.sauf:
            continue
        if documentee(pr["number"], isoles, plages):
            continue
        restantes.append(pr)
    return sorted(restantes, key=lambda pr: pr["number"])


def entier(texte, option):
    t = texte.lstrip("#")
    if not re.fullmatch(r"\d+", t):
        raise ErreurEntree(f"{option} : un numéro de PR attendu, reçu « {texte} »")
    return int(t)


def valider(args):
    if bool(args.porte) == args.trous:
        raise ErreurEntree("usage : --porte <page.md> OU --trous (pas les deux, pas aucun)")
    if args.porte:
        if args.prs or args.depuis or args.sauf:
            raise ErreurEntree("--prs, --depuis et --sauf ne vont qu'avec --trous")
        if args.changelog and args.pr is None:
            raise ErreurEntree("--changelog exige --pr N (le numéro de la PR à contrôler)")
        if args.pr is not None and not args.changelog:
            raise ErreurEntree("--pr N exige --changelog <miroir-changelog.md>")
        if args.pr is not None:
            args.pr = entier(args.pr, "--pr")
        return
    if args.pr is not None or args.recap_fichier or args.lot:
        raise ErreurEntree("--pr, --recap-fichier et --lot ne vont qu'avec --porte")
    if not (args.changelog and args.prs and args.depuis):
        raise ErreurEntree("--trous exige --changelog, --prs et --depuis AAAA-MM-JJ")
    if not DATE_ARG.fullmatch(args.depuis):
        raise ErreurEntree(f"--depuis : une date AAAA-MM-JJ attendue, reçu « {args.depuis} »")
    args.sauf = {
        entier(morceau, "--sauf")
        for valeur in (args.sauf or [])
        for morceau in re.split(r"[,\s]+", valeur) if morceau
    }


def parseur():
    p = argparse.ArgumentParser(description="Porte de clôture de la doc vivante (voir l'en-tête du script).")
    p.add_argument("--porte", metavar="PAGE", help="page du plan à contrôler (miroir Notion)")
    p.add_argument("--trous", action="store_true", help="lister les PR mergées sans entrée au Changelog")
    p.add_argument("--changelog", metavar="MIROIR", help="miroir du Changelog du projet")
    p.add_argument("--pr", metavar="N", help="numéro de la PR à contrôler (avec --porte)")
    p.add_argument("--recap-fichier", metavar="FICHIER", help="fichier qui porte le Récap (palier 3)")
    p.add_argument("--lot", action="store_true", help="plan enfant d'un lot : pas d'entrée individuelle")
    p.add_argument("--prs", metavar="JSON", help="sortie de gh pr list --json (avec --trous)")
    p.add_argument("--depuis", metavar="AAAA-MM-JJ", help="date de merge de départ (avec --trous)")
    p.add_argument("--sauf", action="append", metavar="N[,N…]", help="PR à exclure (avec --trous)")
    return p


def main(argv=None):
    args = parseur().parse_args(argv)
    try:
        valider(args)
        if args.trous:
            restantes = trous(args)
            for pr in restantes:
                print(f"#{pr['number']} {pr.get('title') or ''}".rstrip())
            return 1 if restantes else 0
        defauts = porte(args)
        for defaut in defauts:
            print(defaut)
        return 1 if defauts else 0
    except ErreurEntree as e:
        print(f"doc-de-cloture : {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
