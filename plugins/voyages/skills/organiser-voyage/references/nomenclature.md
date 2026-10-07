# Nomenclature des billets et du dossier du voyage

À lire avant de ranger un billet. Règle d'or : **ne compose jamais le nom à
la main, appelle `nommer_billet.py`**. Les gabarits ci-dessous disent ce qu'il
produit, pas ce qu'il faut recopier.

## Gabarits

L'extension est celle du fichier (`.pdf` par défaut). Exemples anonymisés.

| Type | Gabarit | Exemple |
|---|---|---|
| Billet (musée, visite, activité) | `AAAA-MM-JJ HHhMM - Lieu - Billet - Voyageur` | `2027-04-12 10h30 - Musée Exemple - Billet - Voyageur A.pdf` |
| Vol | `AAAA-MM-JJ - Vol Origine-Destination - Type - Voyageur` | `2027-04-10 - Vol Ville A-Ville B - Billet - Voyageur B.pdf` |
| Train | `AAAA-MM-JJ HHhMM - Train Origine-Destination - Billet - Voyageur` | `2027-04-13 08h15 - Train Ville B-Ville C - Billet - Voyageur A.pdf` |
| Hébergement | `AAAA-MM-JJ - Hebergement Nom - Reservation` | `2027-04-10 - Hebergement Hôtel Exemple - Reservation.pdf` |

- Vol : `Type` vaut `Billet` par défaut ; pour un autre document, champ
  `document` (carte d'embarquement : `Carte embarquement`).
- Hébergement : jamais de voyageur, la réservation est commune.
- Heure : celle du billet, heure locale du lieu, au format `HHhMM`.

## Dernier champ : le voyageur

Ordre de priorité, le premier qui s'applique gagne :

1. le **prénom du voyageur** nommé sur le billet (`Voyageur A`) ;
2. `1 sur 2` : commande de plusieurs billets **sans prénom** (champs `billet` =
   rang, `sur` = nombre de billets) ;
3. **omis** : billet commun aux deux voyageurs (`"commun": true`).

Le prénom l'emporte sur `1 sur 2`. Sans aucun des trois : refus.

## Dossier du voyage

- Voyage de plus d'un mois (**plus de 31 jours**, fin - début) :
  `Voyages/AAAA - Destination`.
- Sinon : `Voyages/AAAA-MM - Destination` (année et mois du début).
- Le passif (dossiers existants à un autre format) n'est **pas renommé**.

## Ne jamais écraser, ne jamais deviner

- Un nom déjà pris dans le dossier se résout par `nom_libre` : ` (2)`, ` (3)`…
  avant l'extension, casse ignorée. Le fichier existant n'est jamais touché.
- Un champ incertain (date, heure, lieu, origine, destination, voyageur absent,
  illisible ou listé dans `incertains`) → **pas de nom**. Le script refuse
  (code 1, message sur stderr) : le billet **se signale**, il n'est pas rangé,
  et on n'invente jamais de « inconnu ».

## Appeler le script

`$DOSSIER_SKILL` est le dossier de ce skill ; `SKILL.md` dit comment le connaître
(Hermes ou Claude Code).

```bash
SCRIPT="$DOSSIER_SKILL/scripts/nommer_billet.py"

# nom d'un billet (collision : --existants = un nom par ligne)
python3 "$SCRIPT" --json '{"type":"train","date":"2027-04-13","heure":"08h15","origine":"Ville B","destination":"Ville C","voyageur":"Voyageur A"}' [--existants noms.txt]

# nom du dossier du voyage
python3 "$SCRIPT" --dossier --json '{"destination":"Destination Exemple","debut":"2027-04-10","fin":"2027-04-17"}'
```

Champs de `--json` selon le type :

- `type` (`billet`, `vol`, `train`, `hebergement`), `date` (`AAAA-MM-JJ`),
  `extension` (facultatif) ;
- `billet` : `heure`, `lieu` ; `train` : `heure`, `origine`, `destination` ;
  `vol` : `origine`, `destination`, `document` (facultatif) ;
  `hebergement` : `nom` ;
- dernier champ : `voyageur`, ou `billet` + `sur`, ou `commun` ;
- `incertains` : liste des champs que la lecture du mail ne garantit pas.

Sortie : le nom sur stdout, code 0. Refus : code 1, `refus : <raison>` sur
stderr. Bibliothèque standard seule, aucun accès réseau.
