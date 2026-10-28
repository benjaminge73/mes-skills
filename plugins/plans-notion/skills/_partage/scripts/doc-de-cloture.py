#!/usr/bin/env python3
"""Porte de clôture de la doc vivante : le Récap d'une page de plan, et les PR sans entrée.

Pourquoi un script : la clôture doit poser une entrée au Changelog pour chaque PR mergée,
et « je l'ai fait » se dit sans se vérifier. Une PR oubliée ne se voit pas dans une liste
de cinquante entrées ; ça se compte. Même principe que ``controle-changelog.py``.

Usage :
  doc-de-cloture.py --porte <page.md> [--changelog <changelog.md>] [--hub-fichier <fichier>]
                    [--pr N] [--recap-fichier <fichier>] [--lot]
  doc-de-cloture.py --trous --changelog <changelog.md> --prs <prs.json>
                    (--depuis AAAA-MM-JJ | --projet <miroir-page-projet>) [--sauf N[,N…]]

Mode --porte, qui refuse le passage à « a merger » quand la doc manque :
  - la page a un H2 dont le titre commence par « Récap » (casse indifférente), et c'est son
    premier H2 : un Récap posé sous « Cartes » ou sous « Reprise du plan » ne se voit pas en
    ouvrant la page (relevé du 2026-10-28 : 11 pages de plan sur 30 sans Récap en tête,
    surtout des plans de suite). Ce qui précède le premier H2 (encadré, phrase) est toléré. Exception,
    le palier 3 : --recap-fichier existant qui porte un tel H2 (le Récap est dans un fichier
    confié à Hermes, la page ne le porte pas encore) ;
  - si --pr N est donné et que --lot n'est pas donné, une entrée du hub cite la PR N dans son
    en-tête. Les entrées lues sont celles du miroir --changelog et, au palier 3, celles de
    --hub-fichier (l'entrée du hub confiée à Hermes, même format), avec la même règle.
    --lot (plan enfant d'un lot : une entrée consolidée à la fermeture du lot) dispense de cette
    seconde exigence, pas de la première. --pr exige --changelog ou --hub-fichier ;
    --changelog ou --hub-fichier sans --pr sont des usages erronés.

Mode --trous, le rattrapage : liste chaque PR mergée à la date de départ ou après, qui n'est
pas une PR de dépendances (auteur ``dependabot…`` ou ``app/dependabot``, ou label
``dependencies``), dont le numéro n'est cité dans aucun en-tête du Changelog, et qui n'est
pas dans --sauf. ``<prs.json>`` est la sortie de
``gh pr list --state merged --limit 200 --json number,title,mergedAt,author,labels``.
La date de départ vient de ``--depuis`` ; sans lui, elle se lit dans ``--projet`` (miroir de la
page projet) : la ligne ``📘 Activée le AAAA-MM-JJ`` de l'encadré ``📘 Doc vivante : activée``. Si
``--depuis`` est donné, il l'emporte et ``--projet`` n'est pas lu.

Un en-tête d'entrée : une ligne H2 dont le titre commence par une date AAAA-MM-JJ ou par
« Récap », suivie de la ligne ``Plan :``, dans les cinq lignes qui suivent le H2 et avant le
prochain titre, toggle, <details> ou ligne en gras. Seuls le H2 et sa ligne Plan portent des numéros :
les puces, le bloc « Côté technique » et les phrases d'absence ne comptent pas.

Quels numéros comptent dans un en-tête :
  - dans le titre H2, seule la forme finale ``(PR #N)``, en fin de titre : le gabarit « Sans
    plan » la pose ainsi. Ni un ``#N`` nu (« Revert … (#282) »), ni un ``PR N`` ou un ``pull/N``
    ailleurs dans le titre (le titre recopie celui de la PR, qui peut citer d'autres PR), ni
    un numéro du titre de plan (« Thaïlande #4 ») ne comptent ;
  - sur la ligne Plan, seul le segment qui suit ``PR :`` compte : il va jusqu'à ``· Statut :``
    (exclu), ou jusqu'à la fin de la ligne. Il tient ainsi un groupe de liens séparés par ``·``
    (``PR : [x](pull/262) · [x](pull/263)``). Le lien du plan et son titre ne comptent jamais ;
  - dans ce segment : ``#N`` (frontière de mot, ``#25`` ne couvre pas ``#258``), ``pull/N``,
    et les plages (toutes les PR de A à B incluses) : ``#A à #B`` et ``#A à B`` (avec « à »
    seulement, la borne B peut être sans dièse), ``#A–#B``, ``#A-#B``, ``#A … #B`` (avec ces
    séparateurs, la borne B porte son dièse). Une plage inversée (A > B) ou de plus de 50
    numéros (B − A > 50) ne compte pas du tout. Un ``PR N`` en prose n'est pas lu.

Les blocs de code (``` ou ~~~) ne comptent ni pour le Récap, ni pour un en-tête.

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
H2 = re.compile(r"^##\s")
ENTREE = re.compile(r"^##\s+(?:\d{4}-\d{2}-\d{2}\b|récap)", re.IGNORECASE)
DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")
DATE_ARG = re.compile(r"\d{4}-\d{2}-\d{2}")
# La date d'activation, dans le miroir de la page projet (changelog-et-doc.md § 5).
ACTIVATION = re.compile(r"Activée le (\d{4}-\d{2}-\d{2})")
TITRE = re.compile(r"^#{1,6}\s")
ZONE_MAX = 5

# Une plage : « à » admet une borne B sans dièse (« #258 à 260 ») ; les autres séparateurs
# (–, -, …) exigent le dièse de B (« #258–#260 »). Une plage de plus de PLAGE_MAX numéros est
# suspecte : elle est ignorée.
PLAGE = re.compile(r"#(\d+)\s*(?:à\s*#?(\d+)|(?:–|-|…)\s*#(\d+))")
PLAGE_MAX = 50
TITRE_FINAL = re.compile(r"\(PR #(\d+)\)\s*$")
NUMERO = re.compile(r"#(\d+)")
PULL = re.compile(r"pull/(\d+)")
CLOTURE_CODE = re.compile(r"^\s*(```|~~~)")
# Le segment PR va de « PR : » jusqu'à « · Statut : » (exclu), ou jusqu'à la fin de la ligne.
# Il peut contenir plusieurs liens séparés par « · » (« PR : [x](pull/262) · [x](pull/263) »).
SEGMENT_PR = re.compile(r"(?:^|·)\s*PR\s*:(.*?)(?=\s*·\s*Statut\s*:|$)")


class ErreurEntree(Exception):
    """Entrée illisible ou usage erroné : le script rend 2."""


def lire(chemin, role):
    try:
        return Path(chemin).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ErreurEntree(f"{role} illisible : {chemin} ({e})") from None


def _zone(lignes, i):
    """Les lignes d'en-tête après le H2 d'indice i : jusqu'au titre, toggle, details ou gras suivant."""
    zone = []
    for ligne in lignes[i + 1:i + 1 + ZONE_MAX]:
        if TITRE.match(ligne) or ligne.startswith(("<toggle", "<details", "**")):
            break
        zone.append(ligne)
    return zone


def masquer_code(lignes):
    """Les lignes, un bloc de code (``` ou ~~~) vidé : ce qu'il contient n'est pas lu."""
    sortie, ouvert = [], None
    for ligne in lignes:
        cloture = CLOTURE_CODE.match(ligne)
        if ouvert is None and cloture:
            ouvert = cloture.group(1)
            sortie.append("")
        elif ouvert is not None:
            if cloture and cloture.group(1) == ouvert:
                ouvert = None
            sortie.append("")
        else:
            sortie.append(ligne)
    return sortie


def numeros_cites(texte):
    """Les numéros isolés (``#N``, ``pull/N``) et les plages (a, b) cités dans un texte.

    « PR N » en prose n'est pas lu : « (voir PR 190) » ne documente pas la PR 190.
    """
    plages = []
    for m in PLAGE.finditer(texte):
        a, b = int(m.group(1)), int(m.group(2) or m.group(3))
        if a <= b and b - a <= PLAGE_MAX:
            plages.append((a, b))
    # Une plage matchée, valide ou non, est retirée du texte : ses bornes ne se lisent pas une
    # seconde fois comme numéros isolés.
    reste = PLAGE.sub(" ", texte)
    isoles = {int(n) for n in NUMERO.findall(reste)}
    isoles |= {int(n) for n in PULL.findall(reste)}
    return isoles, plages


def numeros_titre(ligne_h2):
    """Dans un titre H2, seule la forme finale « (PR #N) », en fin de titre, compte.

    Le gabarit « Sans plan » la pose en fin de titre. Un « PR N » ou un « pull/N » ailleurs
    dans le titre ne compte pas : le titre recopie celui de la PR, qui peut citer d'autres PR.
    """
    m = TITRE_FINAL.search(ligne_h2)
    return ({int(m.group(1))} if m else set()), []


def numeros_pr(ligne_plan):
    """Sur une ligne Plan, seul le segment qui suit « PR : » compte, jusqu'à « · Statut : »."""
    m = SEGMENT_PR.search(ligne_plan)
    if not m:
        return set(), []
    return numeros_cites(m.group(1))


def en_tetes(lignes):
    """Les PR documentées : numéros isolés et plages, lus dans les en-têtes d'entrée seulement."""
    lignes = masquer_code(lignes)
    isoles, plages = set(), []
    for i, ligne in enumerate(lignes):
        if not ENTREE.match(ligne):
            continue
        plan = [ligne_zone for ligne_zone in _zone(lignes, i) if ligne_zone.startswith("Plan :")]
        if not plan:
            continue
        n, p = numeros_titre(ligne)
        isoles |= n
        plages += p
        for ligne_plan in plan:
            n, p = numeros_pr(ligne_plan)
            isoles |= n
            plages += p
    return isoles, plages


def documentee(numero, isoles, plages):
    return numero in isoles or any(a <= numero <= b for a, b in plages)


def porte(args):
    defauts = []
    page = masquer_code(lire(args.porte, "page du plan").splitlines())
    if not any(RECAP.match(ligne) for ligne in page):
        palier3 = False
        if args.recap_fichier and Path(args.recap_fichier).is_file():
            texte = masquer_code(lire(args.recap_fichier, "--recap-fichier").splitlines())
            palier3 = any(RECAP.match(ligne) for ligne in texte)
        if not palier3:
            defauts.append("récap absent : la page n'a aucun H2 « Récap » (ni --recap-fichier qui en porte un)")
    else:
        premier = next((ligne for ligne in page if H2.match(ligne)), "")
        if not RECAP.match(premier):
            defauts.append(f"récap pas en tête : le premier H2 de la page est « {premier.strip()} » ; "
                           "le Récap se pose au-dessus de tout autre H2 (Cartes, Reprise du plan…)")
    if args.pr is not None and not args.lot:
        sources = []
        if args.changelog:
            sources.append(lire(args.changelog, "changelog"))
        if args.hub_fichier and Path(args.hub_fichier).is_file():
            sources.append(lire(args.hub_fichier, "--hub-fichier"))
        isoles, plages = set(), []
        for texte in sources:
            n, p = en_tetes(texte.splitlines())
            isoles |= n
            plages += p
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


def date_activation(chemin):
    """La date d'activation : la première ligne « Activée le AAAA-MM-JJ » du miroir projet.

    Sans elle, la date n'est pas devinée : code 2, et le message nomme la ligne attendue.
    """
    m = ACTIVATION.search(lire(chemin, "--projet"))
    if not m:
        raise ErreurEntree(
            f"--projet : {chemin} ne porte pas la ligne « Activée le AAAA-MM-JJ » de l'encadré "
            "« 📘 Doc vivante : activée » ; sans date, --trous exige --depuis AAAA-MM-JJ")
    return m.group(1)


def entier(texte, option):
    t = texte.lstrip("#")
    if not re.fullmatch(r"\d+", t):
        raise ErreurEntree(f"{option} : un numéro de PR attendu, reçu « {texte} »")
    return int(t)


def valider(args):
    if bool(args.porte) == args.trous:
        raise ErreurEntree("usage : --porte <page.md> OU --trous (pas les deux, pas aucun)")
    if args.porte:
        if args.prs or args.depuis or args.sauf or args.projet:
            raise ErreurEntree("--prs, --depuis, --sauf et --projet ne vont qu'avec --trous")
        if args.changelog and args.pr is None:
            raise ErreurEntree("--changelog exige --pr N (le numéro de la PR à contrôler)")
        if args.hub_fichier and args.pr is None:
            raise ErreurEntree("--hub-fichier exige --pr N (le numéro de la PR à contrôler)")
        if args.pr is not None and not (args.changelog or args.hub_fichier):
            raise ErreurEntree("--pr N exige --changelog <miroir-changelog.md> ou --hub-fichier <fichier>")
        if args.pr is not None:
            args.pr = entier(args.pr, "--pr")
        return
    if args.pr is not None or args.recap_fichier or args.lot or args.hub_fichier:
        raise ErreurEntree("--pr, --recap-fichier, --hub-fichier et --lot ne vont qu'avec --porte")
    if not (args.changelog and args.prs):
        raise ErreurEntree("--trous exige --changelog et --prs")
    if not args.depuis:
        # --depuis, s'il est donné, l'emporte : --projet n'est pas lu.
        if not args.projet:
            raise ErreurEntree("--trous exige --depuis AAAA-MM-JJ ou --projet <miroir>")
        args.depuis = date_activation(args.projet)
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
    p.add_argument("--hub-fichier", metavar="FICHIER",
                   help="entrée du hub confiée à Hermes (palier 3), lue comme un Changelog (avec --pr)")
    p.add_argument("--lot", action="store_true", help="plan enfant d'un lot : pas d'entrée individuelle")
    p.add_argument("--prs", metavar="JSON", help="sortie de gh pr list --json (avec --trous)")
    p.add_argument("--depuis", metavar="AAAA-MM-JJ", help="date de merge de départ (avec --trous)")
    p.add_argument("--projet", metavar="MIROIR",
                   help="miroir de la page projet, dont la ligne « Activée le AAAA-MM-JJ » donne la date "
                        "de départ (avec --trous, sans --depuis)")
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
