#!/usr/bin/env python3
"""Vérifier que les faits de doc dont dépendent nos règles sont toujours vrais.

``docs/veille.md`` (partie « Les faits porteurs ») liste chaque fait de la doc
Claude Code dont dépend une règle ou un contrôle, avec sa **citation mot pour
mot**, son URL et le contrôle qui en dépend. Une doc qui change sans qu'on le
sache fait protéger la mauvaise chose : ce script relit chaque page et vérifie
que la citation y figure toujours.

La comparaison est tolérante à la forme — espaces, retours à la ligne, casse,
balises HTML, guillemets typographiques — et pas au fond : ``1,536`` devenu
``2,048`` est un fait changé.

Modes
-----
- **Rapport seul (défaut).** Affiche un état par fait et ne crée rien. Code de
  sortie ``1`` si une citation est introuvable, ``2`` si une page est
  injoignable (sans preuve que la doc ait changé : aucune issue pour ça).
- **``--ouvrir-issues``**, que seul le workflow ``veille.yml`` passe : ouvre une
  issue « Doc Claude changée : <fait> » par citation introuvable, avec l'URL et
  le contrôle concerné, **sans doublon** (pas de nouvelle issue si une issue
  ouverte porte déjà ce titre). Il ne lui faut que ``GITHUB_TOKEN`` et
  ``GITHUB_REPOSITORY`` : aucun modèle, aucun autre secret.
- **``--pages <dossier>``**, pour les tests : lit ``<dossier>/<nom de la page>``
  au lieu du réseau.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
FAITS_PAR_DEFAUT = REPO_ROOT / "docs" / "veille.md"
PREFIXE_TITRE = "Doc Claude changée : "
COLONNES = 5  # Fait | Citation | URL | Vérifié le | Contrôle qui en dépend

_BALISE = re.compile(r"</?[A-Za-z][\w:-]*(?:\s[^<>]*)?/?>")
_URL = re.compile(r"https?://[^\s`<>)|]+")


@dataclass(frozen=True)
class Fait:
    fait: str
    citation: str
    url: str
    verifie: str
    controle: str


@dataclass(frozen=True)
class Resultat:
    fait: Fait
    statut: str  # « trouve », « absent » ou « injoignable »
    detail: str = ""


def lire_faits(texte: str) -> list[Fait]:
    """Les lignes du tableau de la partie « faits porteurs » (jusqu'à la partie suivante)."""
    dans_la_partie = False
    faits: list[Fait] = []
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dans_la_partie = "faits porteurs" in ligne.lower()
            continue
        if not dans_la_partie or not ligne.lstrip().startswith("|"):
            continue
        cellules = [c.strip() for c in ligne.strip().strip("|").split("|")]
        if len(cellules) != COLONNES or set("".join(cellules)) <= set("-: "):
            continue
        if cellules[0].lower().startswith("fait"):
            continue
        citation = cellules[1].strip()
        if citation.startswith("«") and citation.endswith("»"):
            citation = citation[1:-1].strip()
        trouve = _URL.search(cellules[2])
        faits.append(Fait(cellules[0], citation, trouve.group(0) if trouve else cellules[2],
                          cellules[3], cellules[4]))
    return faits


def normaliser(texte: str) -> str:
    """Forme comparable : sans balises, sans entités, espaces réduits, casse et guillemets lissés."""
    texte = html.unescape(_BALISE.sub(" ", texte))
    texte = (texte.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"'))
    return re.sub(r"\s+", " ", texte).strip().casefold()


def recuperer_reseau(url: str) -> str:
    requete = urllib.request.Request(url, headers={"User-Agent": "mes-skills-veille/1.0"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return reponse.read().decode("utf-8", errors="replace")


def lire_dossier(dossier: Path) -> Callable[[str], str]:
    """Un « réseau » de pages figées : ``<dossier>/<dernier segment de l'URL>``."""
    def recuperer(url: str) -> str:
        return (Path(dossier) / url.rstrip("/").rsplit("/", 1)[-1]).read_text(encoding="utf-8")
    return recuperer


def verifier(faits: list[Fait], recuperer: Callable[[str], str]) -> list[Resultat]:
    pages: dict[str, str | Exception] = {}
    resultats: list[Resultat] = []
    for fait in faits:
        if fait.url not in pages:
            try:
                pages[fait.url] = normaliser(recuperer(fait.url))
            except (OSError, ValueError) as erreur:
                pages[fait.url] = erreur
        page = pages[fait.url]
        if isinstance(page, Exception):
            resultats.append(Resultat(fait, "injoignable", str(page)))
        elif normaliser(fait.citation) in page:
            resultats.append(Resultat(fait, "trouve"))
        else:
            resultats.append(Resultat(fait, "absent"))
    return resultats


def a_signaler(resultats: list[Resultat]) -> list[Resultat]:
    return [r for r in resultats if r.statut == "absent"]


def titre_issue(fait: Fait) -> str:
    return PREFIXE_TITRE + fait.fait


def corps_issue(resultat: Resultat) -> str:
    f = resultat.fait
    return (
        f"La citation de ce fait porteur n'est plus sur la page.\n\n"
        f"- **Fait** : {f.fait}\n"
        f"- **Page** : {f.url}\n"
        f"- **Contrôle concerné** : {f.controle}\n"
        f"- **Dernière vérification** : {f.verifie}\n\n"
        f"Citation attendue :\n\n> {f.citation}\n\n"
        "À faire : relire la page, dire si la règle ou le contrôle qui en dépend tient "
        "toujours, mettre à jour la citation dans `docs/veille.md` (ou la règle), et "
        "ajouter une entrée au journal des passes.\n\n"
        "_Ouverte par `scripts/veille_faits.py` (workflow `veille.yml`)._"
    )


def ouvrir_issues(a_ouvrir: list[Resultat], titres_ouverts: Callable[[], set[str]],
                  creer: Callable[[str, str], None]) -> list[str]:
    """Crée une issue par fait, sauf si une issue ouverte porte déjà ce titre."""
    if not a_ouvrir:
        return []
    deja = set(titres_ouverts())
    creees: list[str] = []
    for resultat in a_ouvrir:
        titre = titre_issue(resultat.fait)
        if titre in deja:
            continue
        creer(titre, corps_issue(resultat))
        deja.add(titre)
        creees.append(titre)
    return creees


class GitHubAPI:
    """Le strict nécessaire de l'API REST : lister les issues ouvertes, en créer une."""

    def __init__(self, depot: str, jeton: str):
        self.depot = depot
        self.jeton = jeton

    def appel(self, methode: str, chemin: str, corps: dict | None = None):
        donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
        requete = urllib.request.Request(
            f"https://api.github.com{chemin}", data=donnees, method=methode,
            headers={"Authorization": f"Bearer {self.jeton}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28",
                     "User-Agent": "mes-skills-veille/1.0"})
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            return json.loads(reponse.read().decode("utf-8"))

    def titres_ouverts(self) -> set[str]:
        titres: set[str] = set()
        for page in range(1, 11):
            lot = self.appel("GET", f"/repos/{self.depot}/issues?state=open&per_page=100&page={page}")
            # L'API liste aussi les pull requests parmi les issues : on les écarte.
            titres |= {i["title"] for i in lot if "pull_request" not in i}
            if len(lot) < 100:
                break
        return titres

    def creer(self, titre: str, corps: str) -> None:
        self.appel("POST", f"/repos/{self.depot}/issues", {"title": titre, "body": corps})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--faits", type=Path, default=FAITS_PAR_DEFAUT,
                        help="fichier dont lire le tableau des faits (défaut : docs/veille.md)")
    parser.add_argument("--pages", type=Path, default=None,
                        help="lire les pages dans ce dossier au lieu du réseau (tests)")
    parser.add_argument("--ouvrir-issues", action="store_true",
                        help="ouvrir une issue par fait changé (le workflow seul le passe)")
    args = parser.parse_args(argv)

    api = None
    if args.ouvrir_issues:
        jeton, depot = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
        if not jeton or not depot:
            print("veille_faits : --ouvrir-issues demande GITHUB_TOKEN et GITHUB_REPOSITORY "
                  "(fournis par le workflow). En local, ne pas passer cette option.",
                  file=sys.stderr)
            return 2
        api = GitHubAPI(depot, jeton)

    try:
        faits = lire_faits(args.faits.read_text(encoding="utf-8"))
    except OSError as erreur:
        print(f"veille_faits : {args.faits} illisible ({erreur}).", file=sys.stderr)
        return 2
    if not faits:
        print(f"veille_faits : aucun fait dans {args.faits} (partie « Les faits porteurs »).",
              file=sys.stderr)
        return 2

    recuperer = lire_dossier(args.pages) if args.pages else recuperer_reseau
    resultats = verifier(faits, recuperer)

    libelles = {"trouve": "trouvé", "absent": "introuvable", "injoignable": "injoignable"}
    for r in resultats:
        detail = f" — {r.detail}" if r.detail else ""
        print(f"{libelles[r.statut]:<12} {r.fait.fait} ({r.fait.url}){detail}")
    signaler = a_signaler(resultats)
    injoignables = [r for r in resultats if r.statut == "injoignable"]
    print(f"\n{len(resultats)} fait(s) vérifié(s) : {len(signaler)} citation(s) à signaler, "
          f"{len(injoignables)} page(s) injoignable(s).")

    if api is not None and signaler:
        for titre in ouvrir_issues(signaler, api.titres_ouverts, api.creer):
            print(f"issue créée : {titre}")
    if injoignables:
        return 2
    if signaler and api is None:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
