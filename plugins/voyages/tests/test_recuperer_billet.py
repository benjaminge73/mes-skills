"""Tests de la récupération des billets (PDF joint, lien, QR dans le corps).

Tout est hors ligne : les PDF et les QR sont engendrés ici avec un contenu
fictif, le « lien » est servi par un serveur HTTP local. Les attendus
(empreintes, nombre de billets) sont écrits à partir du contenu fictif, pas du
code. Les dossiers temporaires sont créés sous tests/ et jamais sous /tmp :
le Chromium snap du poste ne lit ni n'écrit hors de $HOME, et il le fait
sans le moindre message d'erreur.
"""
from __future__ import annotations

import base64
import hashlib
import http.server
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

import pymupdf
import zxingcpp
from PIL import Image

TESTS = Path(__file__).resolve().parent
SCRIPT = (TESTS.parent / "skills" / "organiser-voyage" / "scripts" / "recuperer_billet.py")
FIXTURES = TESTS / "fixtures"

SIGNAL = 3  # code de sortie dédié : « rien d'importable »


def empreinte(contenu: str) -> str:
    return hashlib.sha256(contenu.encode("utf-8")).hexdigest()[:12]


def image_code(contenu: str, format_, scale: int = 6) -> Image.Image:
    code = zxingcpp.create_barcode(contenu, format_)
    bitmap = zxingcpp.write_barcode_to_image(code, scale=scale)
    h, w = bitmap.shape
    return Image.frombytes("L", (w, h), bytes(bitmap))


def png(image: Image.Image) -> bytes:
    tampon = io.BytesIO()
    image.save(tampon, format="PNG")
    return tampon.getvalue()


def fabriquer_pdf(chemin: Path, pages: list[dict]) -> None:
    """Une page par élément : {"qr": [contenus], "code128": contenu | None}."""
    doc = pymupdf.open()
    for page in pages:
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 60), "Billet fictif", fontsize=18)
        for i, contenu in enumerate(page.get("qr", [])):
            rect = pymupdf.Rect(50 + i * 250, 100, 200 + i * 250, 250)
            p.insert_image(rect, stream=png(image_code(contenu, zxingcpp.QRCode)))
        if page.get("code128"):
            p.insert_image(pymupdf.Rect(50, 400, 350, 470),
                           stream=png(image_code(page["code128"], zxingcpp.Code128, 3)))
    doc.save(chemin)
    doc.close()


def lancer(sortie: Path, *args: str, env_extra: dict | None = None):
    env = dict(os.environ, NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, str(SCRIPT), "--sortie", str(sortie), *args],
                       capture_output=True, text=True, timeout=180, env=env)
    return r


def lire(r) -> dict:
    return json.loads(r.stdout)


def decoder(chemin: str) -> list[str]:
    with Image.open(chemin) as im:
        return [b.text for b in zxingcpp.read_barcodes(im.convert("L"), formats=zxingcpp.QRCode)]


class Dossier(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=TESTS)
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.sortie = self.dir / "sortie"
        self.sortie.mkdir()


class CorpsDeMail(Dossier):
    def test_un_qr_en_image_distante_donne_un_signal_et_aucun_billet(self):
        # Panne : un mail dont le QR est une image distante rendait une capture
        # blanche, importée comme si c'était le billet. Sans réseau (port
        # fermé), le script doit signaler, ne rien produire, sortir non nul.
        r = lancer(self.sortie, "--html", str(FIXTURES / "mail-qr-distant.html"))
        self.assertEqual(r.returncode, SIGNAL, r.stdout + r.stderr)
        res = lire(r)
        self.assertEqual(res["billets"], [])
        self.assertTrue(res["signal"])
        self.assertEqual(list(self.sortie.glob("qr-*.png")), [])

    def test_un_qr_en_data_uri_dans_le_corps_donne_un_png_de_qr(self):
        # Panne : le rendu Chromium pouvait ne rien produire sans erreur (snap
        # confiné) ; ce cas prouve que, QR présent dans le corps, le PNG du QR
        # seul sort, lisible, sans le contenu du QR dans la sortie standard.
        contenu = "BILLET-TEST-CORPS"
        uri = "data:image/png;base64," + base64.b64encode(
            png(image_code(contenu, zxingcpp.QRCode, 8))).decode()
        html = self.dir / "mail.html"
        html.write_text(f'<!doctype html><meta charset="utf-8"><body style="background:#fff">'
                        f'<p>Voyageur A</p><img src="{uri}"></body>', encoding="utf-8")
        r = lancer(self.sortie, "--html", str(html))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = lire(r)
        self.assertEqual(res["cas"], "corps")
        self.assertIsNone(res["signal"])
        self.assertEqual(len(res["billets"]), 1)
        b = res["billets"][0]
        self.assertEqual(b["empreinte"], empreinte(contenu))
        self.assertIsNone(b["pdf"])
        self.assertEqual(decoder(b["qr_png"]), [contenu])
        self.assertNotIn(contenu, r.stdout + r.stderr)


class PdfJoint(Dossier):
    def test_un_pdf_de_deux_pages_a_deux_qr_rend_deux_billets_sans_le_code128(self):
        # Panne : une commande porte plusieurs billets (1 PDF de 2 pages = 2 QR)
        # et le Code 128 imprimé sur le billet n'est pas un QR : deux billets,
        # un PDF d'une page chacun, le code-barres linéaire ignoré.
        pdf = self.dir / "commande.pdf"
        fabriquer_pdf(pdf, [{"qr": ["BILLET-TEST-1"], "code128": "LINEAIRE-1"},
                            {"qr": ["BILLET-TEST-2"]}])
        r = lancer(self.sortie, "--pdf", str(pdf))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = lire(r)
        self.assertEqual(res["cas"], "pdf")
        self.assertEqual([b["empreinte"] for b in res["billets"]],
                         [empreinte("BILLET-TEST-1"), empreinte("BILLET-TEST-2")])
        self.assertEqual([b["page"] for b in res["billets"]], [1, 2])
        for b, attendu in zip(res["billets"], ["BILLET-TEST-1", "BILLET-TEST-2"]):
            self.assertEqual(decoder(b["qr_png"]), [attendu])
            with pymupdf.open(b["pdf"]) as d:
                self.assertEqual(d.page_count, 1)
        self.assertNotIn("BILLET-TEST", r.stdout + r.stderr)
        self.assertNotIn("LINEAIRE", r.stdout + r.stderr)

    def test_un_pdf_sans_qr_donne_un_signal_et_aucun_billet(self):
        # Panne : un PDF sans QR (seulement un Code 128) ne doit rien importer.
        pdf = self.dir / "sans-qr.pdf"
        fabriquer_pdf(pdf, [{"qr": [], "code128": "LINEAIRE-1"}])
        r = lancer(self.sortie, "--pdf", str(pdf))
        self.assertEqual(r.returncode, SIGNAL, r.stdout + r.stderr)
        res = lire(r)
        self.assertEqual(res["billets"], [])
        self.assertTrue(res["signal"])


class _Serveur(http.server.BaseHTTPRequestHandler):
    pdf = b""

    def do_GET(self):
        if self.path == "/billets.pdf":
            corps, type_ = self.pdf, "application/pdf"
        else:
            corps, type_ = b"<html><body>Connectez-vous</body></html>", "text/html"
        self.send_response(200)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *a):  # silence
        pass


class LienDeTelechargement(Dossier):
    def setUp(self):
        super().setUp()
        pdf = self.dir / "serveur.pdf"
        fabriquer_pdf(pdf, [{"qr": ["BILLET-TEST-LIEN"]}])
        _Serveur.pdf = pdf.read_bytes()
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Serveur)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def test_un_lien_qui_rend_un_pdf_donne_un_billet(self):
        # Panne : le billet n'est pas joint, il faut suivre le lien (type
        # « Download tickets ») et lire le PDF rendu.
        r = lancer(self.sortie, "--url", self.base + "/billets.pdf")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = lire(r)
        self.assertEqual(res["cas"], "lien")
        self.assertEqual([b["empreinte"] for b in res["billets"]], [empreinte("BILLET-TEST-LIEN")])

    def test_un_lien_qui_rend_du_html_donne_un_signal_et_aucun_billet(self):
        # Panne : un lien qui mène à une page de connexion (HTML) n'est pas un
        # billet : signaler, ne rien importer.
        r = lancer(self.sortie, "--url", self.base + "/connexion")
        self.assertEqual(r.returncode, SIGNAL, r.stdout + r.stderr)
        res = lire(r)
        self.assertEqual(res["billets"], [])
        self.assertTrue(res["signal"])


if __name__ == "__main__":
    unittest.main()
