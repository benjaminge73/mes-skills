#!/usr/bin/env python3
"""Récupération des billets d'un voyage : un seul script pour tous les types.

    recuperer_billet.py --sortie <dossier> (--pdf <fichier>... | --url <URL>... | --html <fichier.html>)

Trois cas, un seul par appel :

- ``--pdf``  : PDF joint au mail ;
- ``--url``  : lien de téléchargement suivi par ``urllib`` ; la réponse doit
  être un PDF (en-tête ``%PDF``), sinon signal ;
- ``--html`` : corps du mail rendu en PNG par Chromium headless, QR cherché
  dans la capture.

Les QR sont lus avec PyMuPDF (rendu 200 dpi) et zxing-cpp, format QR seul : un
Code 128 imprimé sur le billet est ignoré. Un billet = un QR distinct.

Sortie standard : un JSON
``{"cas": "pdf"|"lien"|"corps", "billets": [...], "signal": null|"<raison>"}``.
Chaque billet : ``qr_png`` (le QR découpé), ``pdf`` (PDF d'une page portant ce
QR, ``null`` pour le corps), ``page`` (rang ou ``null``), ``empreinte`` (sha256
court du contenu du QR). Le contenu décodé n'est jamais imprimé : c'est un code
de billet, l'empreinte suffit à dédoublonner.

Codes de sortie : 0 billets trouvés ; 3 signal (rien d'importable : aucun QR,
lien qui ne rend pas un PDF, capture vide) ; 4 erreur d'environnement
(Chromium absent) ; 2 usage.

Chromium : ``VOYAGES_CHROMIUM``, sinon ``/usr/bin/chromium-browser``, sinon
``chromium``, ``chromium-browser``, ``google-chrome`` du PATH. Le HTML et la
capture se font DANS ``--sortie`` : le Chromium snap est confiné par AppArmor
et ne lit ni n'écrit hors de ``$HOME/<dossier ne commençant ni par « . » ni
par « s »>`` ; ailleurs, la capture n'est pas produite, sans aucune erreur.
Les noms produits sont techniques (``billet-1.pdf``, ``qr-1.png``) : le nom
final vient de ``nommer_billet.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import pymupdf
import zxingcpp
from PIL import Image

SORTIE_OK, SORTIE_USAGE, SORTIE_SIGNAL, SORTIE_ENV = 0, 2, 3, 4
DPI = 200
MARGE_QR = 0.15  # part de la taille du QR gardée autour, zone de silence comprise
TAILLE_FENETRE = "800,1600"


class Signal(Exception):
    """Rien d'importable : remonte en JSON, jamais en import silencieux."""


class EnvironnementManquant(Exception):
    pass


def trouver_chromium() -> str:
    voulu = os.environ.get("VOYAGES_CHROMIUM")
    if voulu:
        if not Path(voulu).exists():
            raise EnvironnementManquant(f"VOYAGES_CHROMIUM pointe vers {voulu}, introuvable")
        return voulu
    if Path("/usr/bin/chromium-browser").exists():
        return "/usr/bin/chromium-browser"
    for nom in ("chromium", "chromium-browser", "google-chrome"):
        chemin = shutil.which(nom)
        if chemin:
            return chemin
    raise EnvironnementManquant(
        "Chromium introuvable : définir VOYAGES_CHROMIUM ou installer chromium / google-chrome")


def empreinte(texte: str) -> str:
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()[:12]


def qr_dans(image: Image.Image):
    return zxingcpp.read_barcodes(image.convert("L"), formats=zxingcpp.QRCode)


def decouper(image: Image.Image, code) -> Image.Image:
    pts = [code.position.top_left, code.position.top_right,
           code.position.bottom_right, code.position.bottom_left]
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    marge = int(max(max(xs) - min(xs), max(ys) - min(ys)) * MARGE_QR) + 4
    boite = (max(min(xs) - marge, 0), max(min(ys) - marge, 0),
             min(max(xs) + marge, image.width), min(max(ys) + marge, image.height))
    return image.crop(boite)


def ajouter(billets, vus, sortie: Path, image, code, pdf_source, page):
    """Enregistre un billet s'il est nouveau (dédoublonné par empreinte)."""
    emp = empreinte(code.text)
    if emp in vus:
        return
    vus.add(emp)
    n = len(billets) + 1
    qr_png = sortie / f"qr-{n}.png"
    decouper(image, code).convert("RGB").save(qr_png)
    chemin_pdf = None
    if pdf_source is not None:
        chemin_pdf = sortie / f"billet-{n}.pdf"
        with pymupdf.open(pdf_source) as src, pymupdf.open() as une_page:
            une_page.insert_pdf(src, from_page=page - 1, to_page=page - 1)
            une_page.save(chemin_pdf)
    billets.append({"qr_png": str(qr_png),
                    "pdf": str(chemin_pdf) if chemin_pdf else None,
                    "page": page if pdf_source is not None else None,
                    "empreinte": emp})


def billets_d_un_pdf(chemin: Path, sortie: Path, billets, vus) -> None:
    with pymupdf.open(chemin) as doc:
        for numero, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=DPI, alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            for code in qr_dans(image):
                ajouter(billets, vus, sortie, image, code, chemin, numero)


def telecharger(url: str, destination: Path) -> Path:
    with urllib.request.urlopen(url, timeout=60) as reponse:  # noqa: S310 - lien du mail
        contenu = reponse.read()
    if not contenu.startswith(b"%PDF"):
        raise Signal(f"le lien ne rend pas un PDF : {url.split('?')[0]}")
    destination.write_bytes(contenu)
    return destination


def capturer(html: Path, sortie: Path) -> Path:
    chromium = trouver_chromium()
    page = sortie / "corps.html"
    capture = sortie / "corps.png"
    shutil.copyfile(html, page)
    capture.unlink(missing_ok=True)
    cmd = [chromium, "--headless", "--disable-gpu", f"--window-size={TAILLE_FENETRE}",
           "--hide-scrollbars", "--virtual-time-budget=8000", f"--screenshot={capture}",
           page.resolve().as_uri()]
    if os.environ.get("VOYAGES_CHROMIUM_SANS_BAC_A_SABLE"):
        cmd.insert(2, "--no-sandbox")
    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise Signal("Chromium n'a pas rendu le corps dans le délai (120 s)")
    if not capture.exists() or capture.stat().st_size == 0:
        raise Signal("capture du corps absente ou vide : Chromium confiné (snap) ? "
                     "le dossier --sortie doit être sous $HOME, hors dossier caché ou en « s »")
    return capture


def traiter(args) -> tuple[str, list]:
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    billets: list = []
    vus: set = set()
    if args.pdf:
        cas = "pdf"
        for fichier in args.pdf:
            billets_d_un_pdf(Path(fichier), sortie, billets, vus)
        if not billets:
            raise Signal("aucun QR lisible dans le PDF")
    elif args.url:
        cas = "lien"
        erreurs = []
        for i, url in enumerate(args.url, start=1):
            try:
                pdf = telecharger(url, sortie / f"telechargement-{i}.pdf")
            except Signal as e:
                erreurs.append(str(e))
                continue
            billets_d_un_pdf(pdf, sortie, billets, vus)
        if not billets:
            raise Signal("; ".join(erreurs) or "aucun QR lisible dans le PDF téléchargé")
    else:
        cas = "corps"
        capture = capturer(Path(args.html), sortie)
        with Image.open(capture) as image:
            image = image.convert("RGB")
            for code in qr_dans(image):
                ajouter(billets, vus, sortie, image, code, None, None)
        if not billets:
            raise Signal("aucun QR lisible dans le corps rendu (image distante non chargée ?)")
    return cas, billets


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--sortie", required=True, help="dossier de sortie (HTML et capture compris)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--pdf", action="append", help="PDF joint (répétable)")
    g.add_argument("--url", action="append", help="lien de téléchargement (répétable)")
    g.add_argument("--html", help="corps du mail en HTML")
    args = p.parse_args(argv)
    cas = "pdf" if args.pdf else "lien" if args.url else "corps"
    try:
        cas, billets = traiter(args)
        res, code = {"cas": cas, "billets": billets, "signal": None}, SORTIE_OK
    except Signal as e:
        res, code = {"cas": cas, "billets": [], "signal": str(e)}, SORTIE_SIGNAL
    except EnvironnementManquant as e:
        print(f"erreur : {e}", file=sys.stderr)
        return SORTIE_ENV
    print(json.dumps(res, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
