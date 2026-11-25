#!/usr/bin/env python3
"""Le relevé du jour : ce qui a bougé sur le VPS, rendu en fiche courte, sans modèle.

Pourquoi : le pilote d'un plan a besoin de l'état réel du VPS avant d'écrire une étape (cœur Hermes modifié sans
commit, unités en échec, crons vivants qui divergent de leur miroir versionné, passerelle plus ancienne que le cœur)
et ne doit pas le redécouvrir à la main. Ce script lit cet état en lecture seule, sans `sudo`, sans modèle.

Usage : releve-du-jour.py [--json] [--comparer <fiche.md>] [--objets <chemins…>]

  --json             : la sortie en JSON (liste d'objets {det, texte}) au lieu de la fiche Markdown.
  --comparer <fiche> : ne rend que les constats qui ne figurent pas déjà dans cette fiche.
  --objets           : fichiers touchés par le plan, relatifs au répertoire courant (détecteur SECURITE).

Racines lues, surchargeables pour les tests :
  HERMES_HOME           : la racine Hermes (défaut ~/.hermes).
  RELEVE_HERMES_CUSTOM  : la copie de hermes-custom que le système utilise (défaut <racine>/patches).

Constats, préfixés par leur détecteur (« R6 · … ») :
  R6   fichiers non commités dans le cœur Hermes (hermes-agent)
  R8   unités systemd en échec (portées utilisateur et système) ; dans state/unites-degradees.json, les unités
       « en panne » ou « en redémarrage automatique » (approximation de diagnostiquer, voir diagnostic_unite)
  R9   crons vivants contre leur miroir versionné : le défaut, puis profil par profil ; un cron « completed »
       absent du miroir ne sort pas (job terminé)
  R10  passerelle démarrée avant le dernier commit du cœur
  R11  modules de test absents du venv Hermes
  SECURITE  un motif de la liste fermée (MOTIFS_SECURITE) dans un fichier touché (--objets) : « chemin:ligne · motif »,
            à sa première occurrence, sans la ligne ni la valeur. Une question d'office, pas une enquête.
La numérotation saute R1 à R5 et R7 : ce sont les détecteurs par objet du prototype, abandonnés (relevé par objet
jugé NO-GO) ; on garde les numéros du prototype pour que les renvois restent lisibles.

Une source qui ne se lit pas sort « illisible », jamais « rien ». Une source absente par nature (profil sans
jobs.json, profil sans miroir) ne sort rien. Hors VPS (pas de racine Hermes) : une seule ligne, « hors VPS, rien à
relever ».

Codes : 0 relevé rendu, vide ou non ; 2 usage (argument, fiche illisible).
Bibliothèque standard seule. git et systemctl sont appelés en lecture seule. Aucune valeur lue n'est rendue :
seulement des noms, des identifiants, des comptes et des dates.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

OK, USAGE = 0, 2
UTC = datetime.timezone.utc
MODULES_TEST = ("xdist", "pytest_timeout", "hypothesis")

# Liste fermée des motifs de sécurité, sans casse. Un motif trouvé dans un fichier touché donne une question d'office
# à Benjamin dans la page du plan : elle ne donne pas lieu à une enquête. Le nom affiché est celui de la première colonne.
MOTIFS_SECURITE = (
    ("sudo", r"sudo"),
    ("NOPASSWD", r"NOPASSWD"),
    ("ufw", r"\bufw\b"),
    ("chmod", r"chmod"),
    ("chown", r"chown"),
    ("setcap", r"setcap"),
    ("--system", r"--system"),
    ("0.0.0.0", r"0\.0\.0\.0"),
    ("api_key", r"api[_-]?key"),
    ("token", r"token"),
    ("secret", r"secret"),
    ("password", r"password"),
    ("identifiant Slack", r"\bU0[A-Z0-9]{7,}\b"),
)
MOTIFS_COMPILES = [(nom, re.compile(motif, re.IGNORECASE)) for nom, motif in MOTIFS_SECURITE]

# Un constat : (détecteur, texte). Le détecteur est vide pour une ligne hors détecteur (« hors VPS »).
Constat = tuple[str, str]


def lancer(commande: list[str], env: dict[str, str] | None = None) -> tuple[int, str] | None:
    """La sortie d'une commande en lecture seule, avec son code. None si la commande est absente ou ne rend pas."""
    try:
        r = subprocess.run(commande, capture_output=True, env=env, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def git_lecture(depot: Path, *args: str) -> str | None:
    """La sortie de git dans un dépôt, sans verrou optionnel. None si git manque ou refuse."""
    r = lancer(["git", "--no-optional-locks", "-C", str(depot), *args])
    return r[1] if r is not None and r[0] == 0 else None


def racine_hermes() -> Path:
    return Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")


def constats_coeur(racine: Path) -> list[Constat]:
    """R6 : les fichiers du cœur Hermes qui ne sont pas commités."""
    coeur = racine / "hermes-agent"
    if not coeur.is_dir():
        return [("R6", "illisible : cœur Hermes (hermes-agent) absent")]
    sortie = git_lecture(coeur, "status", "--porcelain")
    if sortie is None:
        return [("R6", "illisible : git status du cœur Hermes refusé, ou git absent")]
    n = sum(1 for ligne in sortie.splitlines() if ligne.strip())
    return [("R6", f"cœur Hermes (hermes-agent) : {n} fichier(s) non commité(s)")] if n else []


def diagnostic_unite(etat: object) -> tuple[str, str] | None:
    """(libellé, détail) d'une unité de state/unites-degradees.json, ou None si elle n'a rien à signaler.

    APPROXIMATION de `diagnostiquer` (~/.hermes/patches/scripts/unite_degradee_autorepair.py, 183-201) :
    - ActiveState failed : « en panne » ;
    - SubState auto-restart : « en redémarrage automatique », à part, jamais « en panne ». Une photo unique ne fait
      pas une boucle : la boucle se mesure d'un passage à l'autre, sur les compteurs, ce que ce relevé ne fait pas ;
    - ActiveState inactive et Result hors de (vide, success, exec-condition) : « en panne ». diagnostiquer ne retient
      ce Result que pour un oneshot ou un timer. Le fichier ne porte pas Type : ce relevé le retient pour toute unité
      inactive, donc il peut sortir à tort un service inactif dont le Result est en échec.
    Une unité active au Result en échec ne sort pas. Une unité LoadState=not-found (absente de ce poste) non plus.
    Les mots systemd sortent tels quels : ce sont des états, pas des valeurs."""
    if not isinstance(etat, dict):
        return ("illisible", "entrée non lisible")
    if etat.get("LoadState") == "not-found":
        return None
    actif, sous, resultat = (str(etat.get(cle, "")) for cle in ("ActiveState", "SubState", "Result"))
    detail = f"ActiveState={actif}, SubState={sous}, Result={resultat}"
    if actif == "failed":
        return ("en panne", detail)
    if sous == "auto-restart":
        return ("en redémarrage automatique", detail)
    if actif == "inactive" and resultat not in ("", "success", "exec-condition"):
        return ("en panne", detail)
    return None


def constats_unites(racine: Path) -> list[Constat]:
    """R8 : les unités systemd en échec, puis les unités que Hermes tient pour dégradées."""
    out: list[Constat] = []
    env = dict(os.environ)
    if not env.get("XDG_RUNTIME_DIR"):
        # Sans ce bus, `systemctl --user` échoue dans un shell non ouvert par la session (« Failed to connect »).
        env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
    portees = (
        ("utilisateur", ["systemctl", "--user", "--failed", "--no-legend", "--plain"]),
        ("système", ["systemctl", "--failed", "--no-legend", "--plain"]),
    )
    for portee, commande in portees:
        r = lancer(commande, env)
        if r is None or r[0] != 0:
            out.append(("R8", f"illisible : systemctl ({portee}) absent ou refusé"))
            continue
        for ligne in r[1].splitlines():
            mots = ligne.split()
            if mots and mots[0] in ("●", "*"):
                mots = mots[1:]
            # Un nom d'unité porte un suffixe (.service, .timer…) : l'en-tête et la légende n'en portent pas.
            if mots and "." in mots[0]:
                out.append(("R8", f"unité en échec ({portee}) : {mots[0]}"))
    etat = racine / "state" / "unites-degradees.json"
    if etat.is_file():
        try:
            donnees = json.loads(etat.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            out.append(("R8", "illisible : state/unites-degradees.json ne se lit pas"))
        else:
            if isinstance(donnees, dict):
                # Le fichier porte toutes les unités surveillées, saines comprises : seules sortent les unités en panne.
                for nom in sorted(donnees):
                    diag = diagnostic_unite(donnees[nom])
                    if diag:
                        libelle, detail = diag
                        out.append(("R8", f"unité {libelle} (state/unites-degradees.json) : {nom}, {detail}"))
            else:
                out.append(("R8", "illisible : state/unites-degradees.json n'est pas un objet"))
    return out


def jobs_de_crons(fichier: Path) -> dict[str, str] | None:
    """Les crons d'un jobs.json : {identifiant: state}, state vide s'il n'est pas noté. None s'il n'existe pas ;
    ValueError s'il ne se lit pas."""
    if not fichier.is_file():
        return None
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(str(e)) from e
    jobs = donnees.get("jobs") if isinstance(donnees, dict) else None
    if not isinstance(jobs, list) or not all(isinstance(j, dict) and "id" in j for j in jobs):
        raise ValueError("pas de liste « jobs » aux entrées identifiées")
    return {str(j["id"]): str(j.get("state", "")) for j in jobs}


def comparer_crons(libelle: str, vivant: Path, miroir: Path, obligatoire: bool) -> list[Constat]:
    """R9 : les crons vivants contre leur miroir, dans les deux sens.

    Pour le défaut (obligatoire), un jobs.json ou un miroir absent est une panne de lecture. Pour un profil, l'absence
    des deux vaut « rien » : c'est un profil sans cron, ou sans copie versionnée."""
    try:
        vivants = jobs_de_crons(vivant)
    except ValueError:
        return [("R9", f"illisible : {libelle}, cron/jobs.json vivant")]
    try:
        copie = jobs_de_crons(miroir)
    except ValueError:
        return [("R9", f"illisible : {libelle}, miroir versionné")]
    if obligatoire:
        if vivants is None:
            return [("R9", f"illisible : {libelle}, cron/jobs.json vivant absent")]
        if copie is None:
            return [("R9", f"illisible : {libelle}, miroir versionné absent")]
    elif vivants is None or copie is None:
        return []
    ids_copie = set(copie)
    # Un cron vivant « completed » est un job terminé, pas une dérive : il ne sort pas.
    out = [("R9", f"{libelle} : cron {i} vivant absent du miroir")
           for i in sorted(vivants) if i not in ids_copie and vivants[i] != "completed"]
    out += [("R9", f"{libelle} : cron {i} du miroir absent des crons vivants") for i in sorted(ids_copie - set(vivants))]
    return out


def constats_crons(racine: Path, miroir_racine: Path) -> list[Constat]:
    """R9 pour le défaut, puis pour chaque profil lu sur le disque (jamais « .deleted »)."""
    out = comparer_crons("profil par défaut", racine / "cron" / "jobs.json",
                         miroir_racine / "config" / "cron" / "jobs.json", obligatoire=True)
    profils = racine / "profiles"
    if profils.is_dir():
        for profil in sorted(profils.iterdir()):
            if profil.name.startswith(".") or not profil.is_dir():
                continue
            out += comparer_crons(f"profil {profil.name}", profil / "cron" / "jobs.json",
                                  miroir_racine / "config" / "profiles" / profil.name / "cron" / "jobs.json",
                                  obligatoire=False)
    return out


def constats_passerelle(racine: Path) -> list[Constat]:
    """R10 : la passerelle a-t-elle démarré avant le dernier commit du cœur installé ?"""
    etat = racine / "state" / "gateway.lifecycle.json"
    try:
        debut = datetime.datetime.fromisoformat(json.loads(etat.read_text(encoding="utf-8"))["started_at"])
    except (OSError, ValueError, KeyError, TypeError):
        return [("R10", "illisible : state/gateway.lifecycle.json (started_at)")]
    if debut.tzinfo is None:
        debut = debut.replace(tzinfo=UTC)
    sortie = git_lecture(racine / "hermes-agent", "log", "-1", "--format=%ct")
    if sortie is None or not sortie.strip().isdigit():
        return [("R10", "illisible : date du dernier commit du cœur")]
    commit = datetime.datetime.fromtimestamp(int(sortie.strip()), tz=UTC)
    if debut < commit:
        return [("R10", f"passerelle démarrée le {debut:%Y-%m-%d %H:%M} UTC, avant le dernier commit du cœur "
                         f"({commit:%Y-%m-%d %H:%M} UTC) : à redémarrer")]
    return []


def constats_modules(racine: Path) -> list[Constat]:
    """R11 : les modules de test que la suite Hermes attend dans son venv."""
    python = racine / "hermes-agent" / "venv" / "bin" / "python"
    if not python.exists():
        return [("R11", "illisible : venv Hermes absent, modules de test non vérifiés")]
    out: list[Constat] = []
    for module in MODULES_TEST:
        r = lancer([str(python), "-I", "-c", f"import {module}"])
        if r is None:
            return out + [("R11", "illisible : venv Hermes ne répond pas")]
        if r[0] != 0:
            out.append(("R11", f"module de test {module} absent du venv Hermes"))
    return out


def constats_vps(racine: Path) -> list[Constat]:
    if not racine.is_dir():
        return [("", "hors VPS, rien à relever")]
    miroir_racine = Path(os.environ["RELEVE_HERMES_CUSTOM"]) if os.environ.get("RELEVE_HERMES_CUSTOM") \
        else racine / "patches"
    return (constats_coeur(racine) + constats_unites(racine) + constats_crons(racine, miroir_racine)
            + constats_passerelle(racine) + constats_modules(racine))


def constats_securite(objets: list[str]) -> list[Constat]:
    """SECURITE : pour chaque fichier touché, un constat par motif de la liste, à sa première occurrence.

    Seul le contenu est lu. Sortent le chemin, le numéro de ligne et le nom du motif : jamais la ligne ni la valeur
    trouvée. Un fichier absent, un dossier ou un binaire ne sort rien ; un fichier présent qui ne se lit pas sort
    « illisible »."""
    out: list[Constat] = []
    for chemin in objets:
        fichier = Path(chemin)
        if not fichier.is_file():
            continue
        try:
            octets = fichier.read_bytes()
        except OSError:
            out.append(("", f"illisible : {chemin} (lecture refusée)"))
            continue
        if b"\x00" in octets[:8192]:
            continue
        vus: set[str] = set()
        for numero, ligne in enumerate(octets.decode("utf-8", errors="replace").splitlines(), 1):
            for nom, motif in MOTIFS_COMPILES:
                if nom not in vus and motif.search(ligne):
                    vus.add(nom)
                    out.append(("SECURITE", f"{chemin}:{numero} · {nom}"))
    return out


def rendre(constat: Constat) -> str:
    detecteur, texte = constat
    return f"{detecteur} · {texte}" if detecteur else texte


def normaliser(ligne: str) -> str:
    return ligne.strip().lstrip("-*• ").strip()


def lignes_de_fiche(chemin: str) -> set[str] | None:
    try:
        texte = Path(chemin).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    return {normaliser(ligne) for ligne in texte.splitlines() if ligne.strip()}


def construire_parseur() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Le relevé du jour du VPS, en fiche courte, sans modèle (lecture seule).")
    ap.add_argument("--json", action="store_true", help="la sortie en JSON au lieu de la fiche Markdown")
    ap.add_argument("--comparer", metavar="FICHE", help="ne rend que les constats absents de cette fiche")
    ap.add_argument("--objets", nargs="+", default=[], metavar="CHEMIN",
                    help="fichiers touchés, relatifs au répertoire courant")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = construire_parseur().parse_args(argv)
    constats = constats_vps(racine_hermes()) + constats_securite(a.objets)
    if a.comparer:
        connues = lignes_de_fiche(a.comparer)
        if connues is None:
            print(f"refus : fiche {a.comparer} illisible.", file=sys.stderr)
            return USAGE
        constats = [c for c in constats if normaliser(rendre(c)) not in connues]
    if a.json:
        print(json.dumps([{"det": d, "texte": t} for d, t in constats], ensure_ascii=False, indent=2))
        return OK
    if not a.comparer:
        print(f"## Relevé du jour, {datetime.date.today():%Y-%m-%d}")
        if not constats:
            print("aucun constat.")
    for constat in constats:
        print(rendre(constat))
    return OK


if __name__ == "__main__":
    sys.exit(main())
