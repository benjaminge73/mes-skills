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
ordre ; le travail mécanique est dans trois scripts, le détail dans les références.

## Le refus est la règle sur l'incertain

Quatre champs font un billet : **voyageur, date, heure, lieu** (hébergement et
location : voir la branche plus bas). Si l'un manque, est illisible ou n'est
qu'une supposition, **rien n'est rangé, créé ni mis dans la file de rappels** :
le billet est **signalé** dans le compte rendu, avec la référence de la commande
et le champ qui manque. Deviner coûte plus cher que demander : un billet rangé
sous le mauvais nom, ou rappelé à la mauvaise personne, ne se voit plus.

- Voyageur : seul compte ce que le billet dit (prénom nommé, commande de plusieurs
  billets sans prénom, ou billet commun déclaré). Un billet non nominatif d'un seul
  billet n'a **pas** de voyageur : jamais présumé « le voyageur principal », ni « commun ».
- Un script que tu ne peux pas lancer ne se remplace pas par un nom composé à la
  main : ce qu'il aurait refusé, tu le refuses aussi.
- Un mail qui n'est pas une réservation est **ignoré**, pas deviné.

## La configuration vient de l'appelant

Le skill ne contient aucune donnée personnelle. L'appelant fournit, pour chaque
voyage : le libellé Gmail, le dossier OneDrive racine des voyages, les voyageurs
(nom, clé symbolique, le principal), les dates et le fuseau, le chemin de la file
de rappels. Sans cette configuration, ou si un de ces éléments manque, ne rien
faire et le dire. Les données réelles ne vivent que dans cette configuration et
les dossiers de travail ; les exemples des références sont anonymisés.

## Où sont les scripts

Définis `DOSSIER_SKILL`, le dossier de ce skill, selon l'hôte :

```bash
# Hermes (substitué par Hermes dans ce fichier seulement)
DOSSIER_SKILL="${HERMES_SKILL_DIR}"
# Claude Code
DOSSIER_SKILL="$(dirname "${CLAUDE_PLUGIN_ROOT}/skills/organiser-voyage/SKILL.md")"
```

Les fichiers du skill, à ouvrir au moment dit :

| Fichier | Quand |
|---|---|
| `references/sources-billets.md` | avant d'extraire un billet d'un mail |
| `references/nomenclature.md` | avant de nommer ou ranger |
| `references/hebergements-locations.md` | hébergement ou location |
| `references/rappels.md` | étape 6, carte d'embarquement |
| `scripts/recuperer_billet.py` | étape 2, extraire les QR |
| `scripts/nommer_billet.py` | étape 3, jamais à la main |
| `scripts/rappels.py` | étape 6, envoyer les rappels échus |

## Le flux, pour chaque message

1. **Qualifier.** Réservation (billet, vol, train, hébergement, location, visite) ?
   Sinon : ignoré. Lire les quatre champs, et noter ceux qui sont incertains.
2. **Récupérer** : `recuperer_billet.py` (PDF joint, lien ou QR dans le corps, voir
   `references/sources-billets.md`). Code 3 ou `signal` : **signaler** avec la
   raison. Une commande de plusieurs billets donne un billet par QR.
   Hébergement ou location sans PDF : ni script, ni signal.
3. **Nommer** chaque billet avec `nommer_billet.py`, en lui passant les champs
   `incertains` et les noms déjà présents. Refus (code 1) : **signaler**, ne pas ranger.
4. **Ranger** dans `Voyages/AAAA - Destination` (voyage de plus d'un mois) ou
   `Voyages/AAAA-MM - Destination` (`nommer_billet.py --dossier`). Dossiers existants
   non renommés. **Jamais d'écrasement** : `conflictBehavior=fail`, nom pris → ` (2)`.
   Lien **privé** `webUrl`, jamais un lien de partage anonyme.
5. **Planifier.** Événement d'agenda du voyageur principal (heure locale du lieu,
   lien privé en description), autre voyageur invité. Séjour et location :
   `hebergements-locations.md`.
6. **Rappeler.** Une entrée par billet et par voyageur (`references/rappels.md`) :
   30 min avant ; un **vol** 3 h avant, plus son rappel d'enregistrement 48 h avant
   (`--completer-enregistrements`). Une **carte d'embarquement** se range comme un
   billet, puis se pose sur le rappel du vol (`--poser-carte`). Hébergement et
   location : aucun rappel.

**Branche « réservation sans billet »** (hébergement, location) : tout est dans
`references/hebergements-locations.md`. Un PDF joint est rangé tel quel, sans
`recuperer_billet.py`.

## Le compte rendu

Rendre à l'appelant, par message : **traité** (nom rangé, lien, événement, rappel),
**ignoré** (pas une réservation), **signalé** (commande, ce qui manque). Pour un
hébergement ou une location, l'issue s'écrit `traité | ignoré | en_attente(raison)`.
Un billet signalé n'est ni rangé, ni planifié, ni rappelé : l'appelant le fait
confirmer par une personne, puis relance.

## Ce que le skill ne fait pas

Pas de rappel à la main (`rappels.py`), pas de lien anonyme, pas de nom composé
sans `nommer_billet.py`, pas de renommage, pas d'écrasement.
