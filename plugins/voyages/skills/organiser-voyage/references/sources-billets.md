# Lire un mail de réservation : où est le billet

À lire avant d'extraire un billet d'un mail. Un seul script,
`recuperer_billet.py`, couvre les trois cas ; le nom final du fichier vient
ensuite de `nommer_billet.py` (voir `nomenclature.md`).

## Reconnaître le cas

| Cas | Comment le reconnaître | Option |
|---|---|---|
| `pdf` | un PDF est **joint** au mail | `--pdf <fichier>` (répétable) |
| `lien` | le corps contient un lien de téléchargement : un émetteur de billetterie en ligne de type Vivaticket, bouton « Download tickets » qui rend un PDF | `--url <URL>` (répétable) |
| `corps` | le QR est **dessiné dans le corps** du mail, pas de PDF | `--html <fichier.html>` (corps du mail, rendu par Chromium) |

Un seul cas par appel. Le lien est suivi tel quel ; s'il ne rend pas un PDF,
c'est un signal.

## Plusieurs billets par commande

Une commande peut porter plusieurs billets (1 PDF de 2 pages = 2 QR) : le
script rend **un billet par QR distinct**, donc un fichier par QR. Les Code 128
imprimés sur le billet sont ignorés (QR seul). Un même QR vu deux fois n'est
gardé qu'une fois (`empreinte`).

## Appeler le script

`$DOSSIER_SKILL` est le dossier de ce skill ; `SKILL.md` dit comment le connaître
(Hermes ou Claude Code).

```bash
PY=<interpréteur avec PyMuPDF, zxing-cpp et Pillow>
S="$DOSSIER_SKILL/scripts/recuperer_billet.py"
SORTIE="$HOME/brouillons/voyages/<commande>"

"$PY" "$S" --sortie "$SORTIE" --pdf billet.pdf
"$PY" "$S" --sortie "$SORTIE" --url "https://…/telechargement"
"$PY" "$S" --sortie "$SORTIE" --html corps.html
```

## Lire le résultat

Stdout : `{"cas": "pdf"|"lien"|"corps", "billets": [...], "signal": null|"<raison>"}`.
Chaque billet : `qr_png` (le QR découpé), `pdf` (PDF d'une page portant ce QR,
`null` pour le cas `corps`), `page`, `empreinte`. Le contenu du QR n'est jamais
imprimé : c'est un code de billet.

| Code | Sens | Conduite |
|---|---|---|
| 0 | billets trouvés | ranger chaque billet (nom via `nommer_billet.py`) |
| 3 | `signal` : rien d'importable (aucun QR, lien qui ne rend pas un PDF, capture vide) | **ne rien ranger, signaler** avec la raison |
| 4 | Chromium absent (stderr) | signaler l'environnement ; définir `VOYAGES_CHROMIUM` |
| 2 | appel mal formé | corriger l'appel |

Sur un `signal` ou un code 3 : ni rangement, ni rappel, ni nom deviné. Le
mail se signale à la personne.

## Ce qui part au rappel

- La pièce jointe du rappel est **l'image du QR seule** (`qr_png`) ; à défaut,
  le **PDF** (`pdf`).
- Le lien est le lien **privé** OneDrive (`webUrl`), **jamais un lien de
  partage anonyme**.
- La veille dépose dans la file de rappels : `debut_local` + `fuseau`, `lien`,
  `piece_jointe`, `destinataires` (voir `rappels.py`).

## Envoi vers OneDrive

Il passe par l'outil d'envoi binaire du connecteur (slug Composio
`ONE_DRIVE_ONEDRIVE_UPLOAD_FILE`), en **refusant l'écrasement**
(`conflictBehavior=fail`). Un échec pour nom déjà pris se résout avec
`nom_libre`, jamais en écrasant.

## Dépendances d'exécution

- `recuperer_billet.py` : un interpréteur avec **PyMuPDF**, **zxing-cpp** et
  **Pillow**. `nommer_billet.py` et `rappels.py` : bibliothèque standard seule
  (`rappels.py` : Python 3.11 ou plus).
- Chromium : `VOYAGES_CHROMIUM` pointe vers le binaire ; à défaut le script
  cherche `/usr/bin/chromium-browser`, puis `chromium`, `chromium-browser`,
  `google-chrome`. Sur un runner sans bac à sable, `VOYAGES_CHROMIUM_SANS_BAC_A_SABLE=1`
  ajoute `--no-sandbox`.
- Chromium installé en **snap** : il ne lit ni n'écrit hors de `$HOME/<dossier
  ne commençant ni par « . » ni par « s »>`. Le dossier `--sortie` se met donc
  sous le répertoire personnel (`~/brouillons/…`), **pas `/tmp`, pas un dossier
  caché** : ailleurs, la capture n'est pas produite, sans erreur.
