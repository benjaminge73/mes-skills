---
name: organiser-voyage
description: >-
  Organise un voyage à partir des mails de réservation : qualifier le mail,
  récupérer le ou les billets (PDF joint, lien de téléchargement, QR dessiné
  dans le corps), les nommer avec la nomenclature, les ranger dans le dossier
  OneDrive du voyage sans rien écraser, créer l'événement d'agenda, puis déposer
  le rappel « 30 minutes avant » dans la file. À charger dès qu'il s'agit
  d'organiser un voyage, de traiter un mail de réservation ou un billet, de
  ranger ou nommer un billet, de préparer les rappels d'un voyage, ou quand un
  nouveau message arrive dans le libellé Gmail d'un voyage. Règle première : un
  champ incertain (voyageur, date, heure, lieu) fait refuser le billet, qui se
  signale au lieu d'être rangé. Ne contient aucune donnée personnelle : tout
  vient de la configuration du voyage fournie par l'appelant.
---

# Organiser un voyage

Pour chaque nouveau message du libellé Gmail du voyage : **qualifier, récupérer,
nommer, ranger, planifier, rappeler**. Ce fichier dit quoi faire et dans quel
ordre ; le travail mécanique est dans trois scripts, le détail dans deux
références.

## Le refus est la règle sur l'incertain

Quatre champs font un billet : **voyageur, date, heure, lieu**. Si l'un manque,
est illisible ou n'est qu'une supposition, **rien n'est rangé, rien n'est créé,
rien n'est mis dans la file de rappels** : le billet est **signalé** dans le
compte rendu, avec la référence de la commande et le champ qui manque. Deviner
coûte plus cher que demander : un billet rangé sous le mauvais nom, ou rappelé
à la mauvaise personne, ne se voit plus.

- Voyageur : seul compte ce que le billet dit (prénom nommé, ou commande de
  plusieurs billets sans prénom, ou billet commun déclaré). Un billet non
  nominatif d'un seul billet n'a **pas** de voyageur : jamais présumé « le
  voyageur principal », jamais « commun » par commodité.
- Un script que tu ne peux pas lancer ne se remplace pas par un nom composé à la
  main : ce qu'il aurait refusé, tu le refuses aussi.
- Un mail qui n'est pas une réservation est **ignoré**, pas deviné.

## La configuration vient de l'appelant

Le skill ne contient aucune donnée personnelle. L'appelant fournit, pour chaque
voyage : le libellé Gmail, le dossier OneDrive racine des voyages, les voyageurs
(nom, clé symbolique, le principal), les dates et le fuseau, le chemin de la file
de rappels. Sans cette configuration, ou si un de ces éléments manque, ne rien
faire et le dire.
Les données réelles (noms, libellés Gmail, chemins OneDrive, identifiants
Telegram, codes de billet) ne vivent que dans cette configuration et les
dossiers de travail, jamais dans le skill ni le dépôt qui le publie ; un exemple
ajouté aux références est anonymisé (voyageur A / B, destinations génériques).

## Où sont les scripts

Définis `DOSSIER_SKILL`, le dossier de ce skill, selon l'hôte :

```bash
# Hermes (substitué par Hermes dans ce fichier seulement)
DOSSIER_SKILL="${HERMES_SKILL_DIR}"
# Claude Code
DOSSIER_SKILL="$(dirname "${CLAUDE_PLUGIN_ROOT}/skills/organiser-voyage/SKILL.md")"
```

Les cinq fichiers du skill, à ouvrir au moment dit :

| Fichier | Quand |
|---|---|
| `references/sources-billets.md` | avant d'extraire un billet d'un mail |
| `references/nomenclature.md` | avant de nommer ou ranger |
| `scripts/recuperer_billet.py` | étape 2, extraire les QR |
| `scripts/nommer_billet.py` | étape 3, nommer, jamais à la main |
| `scripts/rappels.py` | étape 6, envoyer les rappels échus |

## Le flux, pour chaque message

1. **Qualifier.** Est-ce une réservation (billet, vol, train, hébergement,
   visite) ? Sinon : ignoré. Lire dans le mail les quatre champs, et noter ceux
   qui sont incertains.
2. **Récupérer** le ou les billets : `recuperer_billet.py` (PDF joint, lien ou QR
   dans le corps, voir `references/sources-billets.md`). Code 3 ou `signal` :
   rien d'importable, **signaler** avec la raison. Une commande de plusieurs
   billets donne un billet par QR.
3. **Nommer** chaque billet avec `nommer_billet.py`, en lui passant la liste des
   champs incertains (`incertains`) et les noms déjà présents dans le dossier.
   Refus du script (code 1) : le billet **se signale**, il ne se range pas.
4. **Ranger** dans OneDrive, dans le dossier du voyage : `Voyages/AAAA -
   Destination` si le voyage dure plus d'un mois, `Voyages/AAAA-MM - Destination`
   sinon (`nommer_billet.py --dossier`). Les dossiers existants à un autre format
   ne sont pas renommés. **Jamais d'écrasement** : envoi en
   `conflictBehavior=fail` ; un nom pris se résout avec le nom libre du script
   (` (2)`). Récupérer ensuite le **lien privé** `webUrl` du fichier : jamais un
   lien de partage anonyme.
5. **Planifier.** Créer l'événement d'agenda du voyageur principal (heure locale
   du lieu, lien privé dans la description) et inviter l'autre voyageur.
6. **Rappeler.** Déposer une entrée dans la file de rappels (`rappels.py` l'envoie
   30 minutes avant, l'appelant fournit le jeton) :
   - `debut_local` et `fuseau` du **lieu** ; `titre`, `ville` ; `etat` à
     `a_envoyer` ;
   - `lien` : le `webUrl` privé ;
   - `piece_jointe` : **pour un billet QR, l'image du QR seule** (`qr_png`) ; à
     défaut le PDF ;
   - `destinataires` : le voyageur nommé sur le billet, les deux pour un billet
     commun.

## Le compte rendu

Rendre à l'appelant, par message : **traité** (nom rangé, lien, événement,
rappel), **ignoré** (pas une réservation) ou **signalé** (commande, ce qui
manque). Un billet signalé n'est ni rangé, ni planifié, ni rappelé : c'est à
l'appelant de le faire confirmer par une personne, puis de relancer.

## Ce que le skill ne fait pas

Pas de rappel envoyé à la main (c'est `rappels.py`), pas de lien de partage
anonyme, pas de nom composé sans `nommer_billet.py`, pas de renommage de
l'existant, pas d'écrasement.
