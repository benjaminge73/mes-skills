#!/usr/bin/env python3
"""Rappels « 30 minutes avant » : un script pur, bibliothèque standard seule.

Il lit une file de rappels (fichier JSON), envoie par l'API Bot Telegram ceux
dont l'échéance tombe dans la fenêtre, et marque chaque entrée. Aucun agent ne
décide de l'heure d'envoi. Python >= 3.11 (``zoneinfo``), aucun paquet tiers.

File : une liste JSON, ou ``{"rappels": [...]}`` (la forme lue est la forme
réécrite, les autres clés de l'objet sont conservées). Une entrée :

- ``id``, ``titre``, ``ville`` (facultatif) ;
- ``debut_local`` : ``AAAA-MM-JJTHH:MM``, heure locale du lieu, sans fuseau ;
- ``fuseau`` : nom IANA (``Europe/Rome``) ;
- ``lien`` : lien privé OneDrive (``webUrl``), facultatif ;
- ``piece_jointe`` : chemin du billet (image du QR, ou PDF), facultatif ;
- ``avance_min`` : minutes d'avance propres à l'entrée (facultatif ; un vol
  porte 180, soit 3 h avant le décollage), sinon l'avance de l'appel ;
- ``destinataires`` : clés symboliques (``["voyageur_a"]``, ou les deux) ;
- ``etat`` : ``a_envoyer``, ``envoye``, ``echec`` ou ``manque``.

Le script écrit en plus : ``envoyes_a`` (clés déjà servies : on ne renvoie
jamais à qui a déjà reçu), ``texte_envoye_a`` (le message est parti, la pièce
jointe non : on ne renvoie que la pièce), ``tentatives``, ``derniere_erreur``
(sans jeton), ``envoye_le`` (UTC).

Heures : ``debut_local`` + ``fuseau`` sont convertis en UTC **une seule fois**
(``zoneinfo``, heure d'été comprise) ; l'horloge du serveur ne sert jamais à
lire une heure locale. Un rappel part si ``début - avance <= maintenant <
début`` (UTC) et s'il n'est pas déjà envoyé. Passé le début sans envoi complet,
il est marqué ``manque`` : jamais envoyé en retard, jamais perdu en silence
(il est compté dans le résumé). Un envoi en échec est marqué ``echec`` et
repris au passage suivant, tant que la fenêtre dure.

Jeton et identifiants de discussion sont passés par l'appelant (aucune
lecture d'environnement ici). En ligne de commande, ils arrivent sur l'entrée
standard, jamais en argument (visible dans ``ps``)::

    echo '{"jeton": "...", "destinataires": {"voyageur_a": "<chat_id>"}}' \\
        | rappels.py --file rappels.json [--avance 30] [--maintenant 2027-04-12T12:00:00Z]

Sortie : un résumé JSON ``envoyes`` / ``en_echec`` / ``manques`` / ``a_venir``
(listes d'identifiants, sans secret). Code 0 si aucun échec, 1 sinon, 2 si
l'appel est mal formé.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

API = "https://api.telegram.org"
AVANCE_PAR_DEFAUT = 30
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
IMAGES = {".png", ".jpg", ".jpeg"}
_FORME_DE_JETON = re.compile(r"bot\d+:[A-Za-z0-9_-]+")


class ErreurEnvoi(Exception):
    """Envoi refusé ou impossible. ``texte_parti`` : le message est déjà arrivé,
    seule la pièce jointe a échoué (la reprise ne le renverra pas)."""

    def __init__(self, message: str, texte_parti: bool = False):
        super().__init__(message)
        self.texte_parti = texte_parti


def nettoyer(texte: str, jeton: str | None) -> str:
    """Retire le jeton d'un texte d'erreur (les exceptions urllib portent l'URL)."""
    if jeton:
        texte = texte.replace(jeton, "[jeton]")
    texte = _FORME_DE_JETON.sub("bot[jeton]", texte)
    return texte[:300]


# --- Envoi Telegram -------------------------------------------------------

def _multipart(champs: dict[str, str], champ_fichier: str, nom: str,
               contenu: bytes, type_mime: str) -> tuple[bytes, str]:
    frontiere = uuid.uuid4().hex
    corps = b""
    for cle, valeur in champs.items():
        corps += (f'--{frontiere}\r\nContent-Disposition: form-data; name="{cle}"'
                  f"\r\n\r\n{valeur}\r\n").encode("utf-8")
    nom = re.sub(r'["\r\n]', "_", nom)
    corps += (f'--{frontiere}\r\nContent-Disposition: form-data; name="{champ_fichier}"; '
              f'filename="{nom}"\r\nContent-Type: {type_mime}\r\n\r\n').encode("utf-8")
    corps += contenu + f"\r\n--{frontiere}--\r\n".encode("ascii")
    return corps, f"multipart/form-data; boundary={frontiere}"


def envoyeur_telegram(jeton: str, base: str = API, delai: float = 30.0):
    """Rend l'envoyeur par défaut : ``envoyer(chat_id, texte, piece_jointe)``.

    ``texte`` (sendMessage, texte brut sans parse_mode : Telegram rend l'URL
    cliquable seul) puis ``piece_jointe`` si elle est donnée : photo pour une
    image, document sinon. Lève ``ErreurEnvoi``, jamais avec le jeton.
    """

    def appeler(methode: str, donnees: bytes, type_contenu: str) -> None:
        requete = urllib.request.Request(
            f"{base}/bot{jeton}/{methode}", data=donnees,
            headers={"Content-Type": type_contenu}, method="POST")
        try:
            with urllib.request.urlopen(requete, timeout=delai) as reponse:
                corps = reponse.read()
        except urllib.error.HTTPError as e:
            try:
                description = json.loads(e.read()).get("description", "")
            except Exception:  # corps vide ou non JSON : le code HTTP suffit
                description = ""
            finally:
                e.close()
            raise ErreurEnvoi(nettoyer(f"{methode} : HTTP {e.code} {description}".strip(), jeton)) from None
        except urllib.error.URLError as e:
            raise ErreurEnvoi(nettoyer(f"{methode} : réseau ({type(e.reason).__name__}: {e.reason})", jeton)) from None
        except OSError as e:  # délai dépassé, connexion coupée
            raise ErreurEnvoi(nettoyer(f"{methode} : réseau ({type(e).__name__})", jeton)) from None
        try:
            ok = json.loads(corps).get("ok", False)
        except ValueError:
            ok = False
        if not ok:
            raise ErreurEnvoi(f"{methode} : réponse de l'API sans ok")

    def envoyer(chat_id: str, texte: str | None, piece_jointe: str | None) -> None:
        if texte is not None:
            donnees = urllib.parse.urlencode({"chat_id": chat_id, "text": texte}).encode("utf-8")
            appeler("sendMessage", donnees, "application/x-www-form-urlencoded")
        if piece_jointe:
            chemin = Path(piece_jointe)
            try:
                contenu = chemin.read_bytes()
                image = chemin.suffix.lower() in IMAGES
                champ, methode = ("photo", "sendPhoto") if image else ("document", "sendDocument")
                type_mime = mimetypes.guess_type(chemin.name)[0] or "application/octet-stream"
                corps, type_contenu = _multipart({"chat_id": chat_id}, champ, chemin.name,
                                                 contenu, type_mime)
                appeler(methode, corps, type_contenu)
            except OSError as e:
                raise ErreurEnvoi(f"pièce jointe illisible ({type(e).__name__})",
                                  texte_parti=texte is not None) from None
            except ErreurEnvoi as e:
                e.texte_parti = texte is not None
                raise

    return envoyer


# --- Heures et message ----------------------------------------------------

def debut_utc(entree: dict) -> datetime:
    """Début de l'événement en UTC : l'unique conversion heure locale -> UTC."""
    local = datetime.fromisoformat(entree["debut_local"])
    if local.tzinfo is not None:
        raise ValueError("debut_local ne porte pas de fuseau")
    return local.replace(tzinfo=ZoneInfo(entree["fuseau"])).astimezone(timezone.utc)


def _jour(jour: date, aujourdhui: date) -> str:
    if jour == aujourdhui:
        return "Aujourd'hui"
    if jour - aujourdhui == timedelta(days=1):
        return "Demain"
    texte = f"{jour.day} {MOIS[jour.month - 1]}"
    return texte if jour.year == aujourdhui.year else f"{texte} {jour.year}"


def _delai(avance: int) -> str:
    if avance >= 60 and avance % 60 == 0:
        return f"{avance // 60} h"
    if avance > 60:
        return f"{avance // 60} h {avance % 60:02d}"
    return f"{avance} min"


def avance_de(entree: dict, avance: int) -> int:
    """Avance propre à l'entrée (``avance_min``, entier > 0), sinon celle de l'appel."""
    propre = entree.get("avance_min")
    if propre is None:
        return avance
    if isinstance(propre, bool) or not isinstance(propre, int) or propre <= 0:
        raise ValueError("avance_min doit être un entier positif")
    return propre


def composer_message(entree: dict, maintenant: datetime, avance: int) -> str:
    local = datetime.fromisoformat(entree["debut_local"])
    aujourdhui = maintenant.astimezone(ZoneInfo(entree["fuseau"])).date()
    ville = entree.get("ville")
    lieu = f"{ville} - {entree['titre']}" if ville else entree["titre"]
    lignes = [
        f"Rappel - dans {_delai(avance)}",
        lieu,
        f"{_jour(local.date(), aujourdhui)} {local.hour} h {local.minute:02d} (heure locale)",
    ]
    if entree.get("lien"):
        lignes += ["", f"Billet OneDrive : {entree['lien']}"]
    return "\n".join(lignes)


# --- File -----------------------------------------------------------------

def _ecrire(chemin: Path, donnees) -> None:
    """Écriture atomique : fichier temporaire du même dossier, puis os.replace."""
    fd, temporaire = tempfile.mkstemp(dir=chemin.parent, prefix=chemin.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        try:
            shutil.copymode(chemin, temporaire)
        except OSError:
            pass
        os.replace(temporaire, chemin)
    except BaseException:
        try:
            os.unlink(temporaire)
        except OSError:
            pass
        raise


def _lire(chemin: Path) -> tuple[object, list]:
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    if isinstance(donnees, list):
        return donnees, donnees
    if isinstance(donnees, dict) and isinstance(donnees.get("rappels"), list):
        return donnees, donnees["rappels"]
    raise ValueError("la file doit être une liste, ou un objet {\"rappels\": [...]}")


def traiter(chemin_file, jeton: str, destinataires: dict[str, str],
            maintenant: datetime | None = None, envoyeur=None,
            avance: int = AVANCE_PAR_DEFAUT) -> dict[str, list[str]]:
    """Passe sur la file : envoie ce qui est dans la fenêtre, marque chaque entrée.

    ``destinataires`` : clé symbolique -> chat_id. ``envoyeur(chat_id, texte,
    piece_jointe)`` est injectable (``texte`` vaut None quand seul le
    document reste à envoyer) ; il lève une exception en cas d'échec.
    """
    chemin = Path(chemin_file)
    if maintenant is None:
        maintenant = datetime.now(timezone.utc)
    if maintenant.tzinfo is None:
        raise ValueError("maintenant doit porter un fuseau (UTC)")
    maintenant = maintenant.astimezone(timezone.utc)
    if envoyeur is None:
        if not jeton:
            raise ValueError("jeton absent")
        envoyeur = envoyeur_telegram(jeton)

    racine, entrees = _lire(chemin)
    resume: dict[str, list[str]] = {"envoyes": [], "en_echec": [], "manques": [], "a_venir": []}

    for rang, entree in enumerate(entrees):
        ident = str(entree.get("id", f"#{rang}"))
        etat = entree.get("etat", "a_envoyer")
        if etat in ("envoye", "manque"):
            continue

        try:
            if etat not in ("a_envoyer", "echec"):
                raise ValueError(f"etat inconnu {etat!r}")
            cles = entree["destinataires"]
            if not cles or not all(isinstance(c, str) for c in cles):
                raise ValueError("destinataires vide ou mal formé")
            debut = debut_utc(entree)
            avance_entree = avance_de(entree, avance)
            entree["titre"]  # noqa: B018 - exigé par le message
        except (KeyError, ValueError, TypeError) as e:
            erreur = nettoyer(f"entrée invalide : {type(e).__name__} {e}", jeton)
            if entree.get("derniere_erreur") != erreur:
                entree["derniere_erreur"] = erreur
                _ecrire(chemin, racine)
            resume["en_echec"].append(ident)
            continue

        if maintenant >= debut:
            entree["etat"] = "manque"
            _ecrire(chemin, racine)
            resume["manques"].append(ident)
            continue
        if maintenant < debut - timedelta(minutes=avance_entree):
            resume["a_venir"].append(ident)
            continue

        message = composer_message(entree, maintenant, avance_entree)
        servis = list(entree.get("envoyes_a", []))
        texte_parti = list(entree.get("texte_envoye_a", []))
        erreurs = []
        for cle in cles:
            if cle in servis:
                continue
            chat_id = destinataires.get(cle)
            if chat_id is None:
                erreurs.append(f"{cle} : destinataire inconnu")
                continue
            try:
                envoyeur(chat_id, None if cle in texte_parti else message,
                         entree.get("piece_jointe"))
            except Exception as e:  # un envoyeur peut lever n'importe quoi
                if getattr(e, "texte_parti", False) and cle not in texte_parti:
                    texte_parti.append(cle)
                erreurs.append(nettoyer(f"{cle} : {type(e).__name__}: {e}", jeton))
            else:
                servis.append(cle)
            entree["envoyes_a"] = servis
            entree["texte_envoye_a"] = texte_parti
            _ecrire(chemin, racine)

        if erreurs:
            entree["etat"] = "echec"
            entree["tentatives"] = int(entree.get("tentatives", 0)) + 1
            entree["derniere_erreur"] = " ; ".join(erreurs)
            resume["en_echec"].append(ident)
        else:
            entree["etat"] = "envoye"
            entree["derniere_erreur"] = None
            entree["envoye_le"] = maintenant.strftime("%Y-%m-%dT%H:%M:%SZ")
            resume["envoyes"].append(ident)
        _ecrire(chemin, racine)

    return resume


# --- Ligne de commande ----------------------------------------------------

def _instant(texte: str) -> datetime:
    instant = datetime.fromisoformat(texte)
    return instant.replace(tzinfo=timezone.utc) if instant.tzinfo is None else instant


def main(argv=None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Envoie les rappels dont l'échéance est dans la fenêtre. "
                    'Jeton et destinataires : JSON {"jeton", "destinataires"} sur l\'entrée standard.')
    analyseur.add_argument("--file", required=True, help="file de rappels (JSON)")
    analyseur.add_argument("--avance", type=int, default=AVANCE_PAR_DEFAUT,
                           help="minutes d'avance (défaut : 30)")
    analyseur.add_argument("--maintenant", type=_instant, default=None,
                           help="instant ISO en UTC (défaut : l'heure du système, en UTC)")
    args = analyseur.parse_args(argv)

    try:
        entree = json.load(sys.stdin)
        jeton, destinataires = entree["jeton"], entree["destinataires"]
        if not isinstance(jeton, str) or not jeton or not isinstance(destinataires, dict):
            raise ValueError("jeton ou destinataires invalide")
    except (ValueError, KeyError, TypeError):
        print("entrée standard attendue : {\"jeton\": \"...\", \"destinataires\": {...}}",
              file=sys.stderr)
        return 2
    try:
        resume = traiter(args.file, jeton, destinataires, maintenant=args.maintenant,
                         avance=args.avance)
    except (OSError, ValueError) as e:
        print(nettoyer(f"file illisible : {type(e).__name__} {e}", jeton), file=sys.stderr)
        return 2
    print(json.dumps(resume, ensure_ascii=False))
    return 1 if resume["en_echec"] else 0


if __name__ == "__main__":
    sys.exit(main())
