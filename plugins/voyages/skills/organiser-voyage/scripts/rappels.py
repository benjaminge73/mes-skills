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
- ``genre`` (facultatif) : ``vol`` (rappel 3 h avant le décollage, avec la
  carte d'embarquement si elle est là) ou ``enregistrement`` (48 h avant le
  vol : « fais l'enregistrement ») ;
- ``avance_min`` : minutes d'avance propres à l'entrée (facultatif), sinon
  celle du genre (vol 180, enregistrement 2880), sinon celle de l'appel ;
- ``carte_piece_jointe``, ``carte_lien`` (vol) : image du QR de la carte
  d'embarquement et son lien privé, posés par ``--poser-carte`` ;
- ``destinataires`` : clés symboliques (``["voyageur_a"]``, ou les deux) ;
- ``etat`` : ``a_envoyer``, ``envoye``, ``echec`` ou ``manque``.

Le script écrit en plus : ``envoyes_a`` (clés déjà servies : on ne renvoie
jamais à qui a déjà reçu), ``texte_envoye_a`` (le message est parti, la pièce
jointe non : on ne renvoie que la pièce), ``tentatives``, ``derniere_erreur``
(sans jeton), ``envoye_le`` (UTC), et pour un vol ``carte_envoyee_a`` /
``carte_texte_envoye_a`` (même logique, pour la carte).

Vol sans carte au moment du rappel : le reçu part, avec « carte
d'embarquement pas encore reçue ». Si la carte est posée ensuite, avant le
décollage, elle part au passage suivant à qui ne l'a pas encore, une fois.

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

Sortie : un résumé JSON ``envoyes`` / ``cartes`` (cartes tardives) /
``en_echec`` / ``manques`` / ``a_venir`` (listes d'identifiants, sans
secret). Code 0 si aucun échec, 1 sinon, 2 si l'appel est mal formé.

Édition de la file, sans jeton ni entrée standard (l'agent de veille)::

    rappels.py --file rappels.json --completer-enregistrements
    rappels.py --file rappels.json --poser-carte <id> --carte-jointe <png> [--carte-lien <url>]

La file est verrouillée (``<file>.lock``) pendant chaque passage et chaque
édition : une carte posée pendant un envoi n'est pas écrasée.
"""
from __future__ import annotations

import argparse
import fcntl
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
AVANCE_PAR_GENRE = {"vol": 180, "enregistrement": 2880}
GENRES = {None, *AVANCE_PAR_GENRE}
CONSIGNE_ENREGISTREMENT = "Enregistrement ouvert ? Fais-le, la carte arrivera par mail."
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
    """Avance propre à l'entrée (``avance_min``, entier > 0), sinon celle de son
    genre, sinon celle de l'appel."""
    propre = entree.get("avance_min")
    if propre is None:
        return AVANCE_PAR_GENRE.get(entree.get("genre"), avance)
    if isinstance(propre, bool) or not isinstance(propre, int) or propre <= 0:
        raise ValueError("avance_min doit être un entier positif")
    return propre


def a_une_carte(entree: dict) -> bool:
    return entree.get("genre") == "vol" and bool(entree.get("carte_piece_jointe"))


def _entete(entree: dict, maintenant: datetime, premiere: str) -> list[str]:
    local = datetime.fromisoformat(entree["debut_local"])
    aujourdhui = maintenant.astimezone(ZoneInfo(entree["fuseau"])).date()
    ville = entree.get("ville")
    lieu = f"{ville} - {entree['titre']}" if ville else entree["titre"]
    return [premiere, lieu,
            f"{_jour(local.date(), aujourdhui)} {local.hour} h {local.minute:02d} (heure locale)"]


def _lien_carte(entree: dict) -> list[str]:
    lien = entree.get("carte_lien") or entree.get("lien")
    return ["", f"Carte d'embarquement OneDrive : {lien}"] if lien else []


def composer_message(entree: dict, maintenant: datetime, avance: int) -> str:
    lignes = _entete(entree, maintenant, f"Rappel - dans {_delai(avance)}")
    if a_une_carte(entree):
        return "\n".join(lignes + _lien_carte(entree))
    if entree.get("genre") == "vol":
        lignes += ["", "Carte d'embarquement pas encore reçue."]
    elif entree.get("genre") == "enregistrement":
        lignes += ["", CONSIGNE_ENREGISTREMENT]
    if entree.get("lien"):
        lignes += ["", f"Billet OneDrive : {entree['lien']}"]
    return "\n".join(lignes)


def message_carte_tardive(entree: dict, maintenant: datetime) -> str:
    return "\n".join(_entete(entree, maintenant, "Carte d'embarquement reçue")
                     + _lien_carte(entree))


def piece_de(entree: dict) -> str | None:
    """La carte (image du QR) d'un vol quand elle est là, sinon la pièce du billet."""
    return entree["carte_piece_jointe"] if a_une_carte(entree) else entree.get("piece_jointe")


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


class _Verrou:
    """Verrou exclusif sur ``<file>.lock`` : un passage d'envoi et une édition
    (carte posée par la veille) ne réécrivent jamais la file en même temps."""

    def __init__(self, chemin: Path):
        self.chemin = chemin.with_name(chemin.name + ".lock")

    def __enter__(self):
        self.fd = os.open(self.chemin, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        os.close(self.fd)


def completer_enregistrements(chemin_file) -> list[str]:
    """Ajoute, pour chaque vol encore à rappeler, son rappel d'enregistrement
    (``<id>-enregistrement``) s'il manque. Rend les identifiants ajoutés."""
    chemin = Path(chemin_file)
    with _Verrou(chemin):
        racine, entrees = _lire(chemin)
        presents = {str(e.get("id")) for e in entrees}
        ajoutes = []
        for entree in list(entrees):
            if entree.get("genre") != "vol" or entree.get("etat", "a_envoyer") not in ("a_envoyer", "echec"):
                continue
            ident = f"{entree['id']}-enregistrement"
            if ident in presents:
                continue
            nouvelle = {cle: entree[cle] for cle in ("titre", "ville", "debut_local", "fuseau", "lien")
                        if cle in entree}
            nouvelle.update(id=ident, genre="enregistrement",
                            avance_min=AVANCE_PAR_GENRE["enregistrement"],
                            destinataires=list(entree["destinataires"]), etat="a_envoyer")
            entrees.append(nouvelle)
            presents.add(ident)
            ajoutes.append(ident)
        if ajoutes:
            _ecrire(chemin, racine)
    return ajoutes


def poser_carte(chemin_file, ident: str, piece_jointe: str, lien: str | None) -> None:
    """Pose la carte d'embarquement (image du QR, lien privé) sur le rappel du vol
    ``ident``. ``ValueError`` si l'identifiant est inconnu ou n'est pas un vol."""
    if not piece_jointe:
        raise ValueError("carte sans pièce jointe")
    chemin = Path(chemin_file)
    with _Verrou(chemin):
        racine, entrees = _lire(chemin)
        cibles = [e for e in entrees if str(e.get("id")) == ident]
        if len(cibles) != 1:
            raise ValueError(f"rappel {ident!r} introuvable (ou en double)")
        if cibles[0].get("genre") != "vol":
            raise ValueError(f"rappel {ident!r} n'est pas un vol")
        cibles[0]["carte_piece_jointe"] = piece_jointe
        if lien:
            cibles[0]["carte_lien"] = lien
        _ecrire(chemin, racine)


def _envoyer_carte_tardive(entree: dict, maintenant: datetime, destinataires: dict[str, str],
                           envoyeur, jeton: str | None, ecrire) -> tuple[int, list[str]]:
    """Vol déjà rappelé sans carte, carte posée depuis : elle part à chaque
    destinataire servi qui ne l'a pas encore. Rend (cartes parties, erreurs)."""
    servis = entree.get("envoyes_a", [])
    cartes = list(entree.get("carte_envoyee_a", []))
    texte_parti = list(entree.get("carte_texte_envoye_a", []))
    message = message_carte_tardive(entree, maintenant)
    erreurs, parties = [], 0
    for cle in entree["destinataires"]:
        if cle not in servis or cle in cartes:
            continue
        chat_id = destinataires.get(cle)
        if chat_id is None:
            erreurs.append(f"{cle} : destinataire inconnu")
            continue
        try:
            envoyeur(chat_id, None if cle in texte_parti else message, entree["carte_piece_jointe"])
        except Exception as e:  # un envoyeur peut lever n'importe quoi
            if getattr(e, "texte_parti", False) and cle not in texte_parti:
                texte_parti.append(cle)
            erreurs.append(nettoyer(f"{cle} : carte : {type(e).__name__}: {e}", jeton))
        else:
            cartes.append(cle)
            parties += 1
        entree["carte_envoyee_a"] = cartes
        entree["carte_texte_envoye_a"] = texte_parti
        ecrire()
    return parties, erreurs


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

    with _Verrou(chemin):
        return _traiter(chemin, jeton, destinataires, maintenant, envoyeur, avance)


def _traiter(chemin: Path, jeton: str, destinataires: dict[str, str], maintenant: datetime,
             envoyeur, avance: int) -> dict[str, list[str]]:
    racine, entrees = _lire(chemin)
    resume: dict[str, list[str]] = {"envoyes": [], "cartes": [], "en_echec": [], "manques": [],
                                    "a_venir": []}

    for rang, entree in enumerate(entrees):
        ident = str(entree.get("id", f"#{rang}"))
        etat = entree.get("etat", "a_envoyer")
        if etat == "manque":
            continue
        if etat == "envoye":
            try:
                avant_le_debut = maintenant < debut_utc(entree)
            except (KeyError, ValueError, TypeError):
                avant_le_debut = False  # déjà envoyé : rien à reprendre sur une entrée abîmée
            if a_une_carte(entree) and avant_le_debut:
                parties, erreurs = _envoyer_carte_tardive(
                    entree, maintenant, destinataires, envoyeur, jeton,
                    lambda: _ecrire(chemin, racine))
                if parties:
                    resume["cartes"].append(ident)
                if erreurs:
                    entree["derniere_erreur"] = " ; ".join(erreurs)
                    _ecrire(chemin, racine)
                    resume["en_echec"].append(ident)
            continue

        try:
            if etat not in ("a_envoyer", "echec"):
                raise ValueError(f"etat inconnu {etat!r}")
            if entree.get("genre") not in GENRES:
                raise ValueError(f"genre inconnu {entree.get('genre')!r}")
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
        piece = piece_de(entree)
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
                envoyeur(chat_id, None if cle in texte_parti else message, piece)
            except Exception as e:  # un envoyeur peut lever n'importe quoi
                if getattr(e, "texte_parti", False) and cle not in texte_parti:
                    texte_parti.append(cle)
                erreurs.append(nettoyer(f"{cle} : {type(e).__name__}: {e}", jeton))
            else:
                servis.append(cle)
                if a_une_carte(entree):
                    entree["carte_envoyee_a"] = [*entree.get("carte_envoyee_a", []), cle]
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
    edition = analyseur.add_mutually_exclusive_group()
    edition.add_argument("--completer-enregistrements", action="store_true",
                         help="ajoute le rappel d'enregistrement (48 h) de chaque vol, sans envoi")
    edition.add_argument("--poser-carte", metavar="ID",
                         help="pose la carte d'embarquement sur le rappel du vol ID, sans envoi")
    analyseur.add_argument("--carte-jointe", help="avec --poser-carte : image du QR de la carte")
    analyseur.add_argument("--carte-lien", help="avec --poser-carte : lien privé de la carte")
    args = analyseur.parse_args(argv)

    if args.completer_enregistrements or args.poser_carte:
        try:
            if args.poser_carte:
                poser_carte(args.file, args.poser_carte, args.carte_jointe, args.carte_lien)
                print(json.dumps({"carte_posee": args.poser_carte}, ensure_ascii=False))
            else:
                print(json.dumps({"ajoutes": completer_enregistrements(args.file)},
                                 ensure_ascii=False))
        except (OSError, ValueError, KeyError) as e:
            print(f"édition refusée : {type(e).__name__} {e}", file=sys.stderr)
            return 2
        return 0

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
