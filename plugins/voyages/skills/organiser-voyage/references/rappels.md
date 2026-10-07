# La file de rappels

À lire avant d'ajouter une entrée à la file, et quand une carte d'embarquement
arrive. Le format exact et le comportement sont dans l'en-tête de
`scripts/rappels.py` ; ce fichier dit **quelle entrée poser, et quand**.
Exemples anonymisés.

## Une entrée par billet et par voyageur

- `id` stable et lisible : `AAAA-MM-JJ-<trajet ou lieu>-<clé du voyageur>` ;
- `debut_local` + `fuseau` du **lieu** (pour un vol : le décollage, fuseau de
  l'aéroport de départ) ; `titre`, `ville` ; `etat` à `a_envoyer` ;
- `lien` : le `webUrl` privé du billet ;
- `piece_jointe` : pour un billet QR, **l'image du QR seule** ; à défaut le PDF.
  Le fichier doit **durer jusqu'au rappel** : jamais dans un dossier de travail
  jetable ;
- `destinataires` : le voyageur nommé sur le billet, les deux pour un billet
  commun.

Sans `genre`, le rappel part 30 min avant (l'avance de l'appel).

## Un vol : deux rappels et une carte

1. Entrée du vol avec `"genre": "vol"` : rappel **3 h avant le décollage**
   (`avance_min` 180 par défaut). `piece_jointe` = le reçu du billet.
2. Puis, une fois la file écrite :
   `rappels.py --file <file> --completer-enregistrements`. Il ajoute, pour
   chaque vol, l'entrée `<id>-enregistrement` (`"genre": "enregistrement"`,
   48 h avant) : « Enregistrement ouvert ? Fais-le, la carte arrivera par
   mail. » La commande est idempotente : la rejouer n'ajoute rien.
3. La **carte d'embarquement** n'arrive que quelques heures avant le vol,
   après l'enregistrement. Quand son mail arrive : récupérer le QR, nommer
   avec `nommer_billet.py` (`"type": "vol"`, `"document": "Carte
   embarquement"`, un fichier par voyageur), ranger dans le dossier du voyage
   sans écraser, prendre le `webUrl` privé, puis :
   `rappels.py --file <file> --poser-carte <id du vol> --carte-jointe <png du QR> --carte-lien <webUrl>`.
   Une carte par entrée : celle du voyageur de l'entrée, jamais celle de
   l'autre.

Ce que fait ensuite `rappels.py`, sans autre geste :

| Moment | Carte posée ? | Ce qui part |
|---|---|---|
| 48 h avant | — | la consigne d'enregistrement, avec le lien du billet |
| 3 h avant | oui | l'image du QR de la carte et son lien |
| 3 h avant | non | le reçu, avec « Carte d'embarquement pas encore reçue » |
| après le rappel, avant le décollage | posée entre-temps | la carte, aussitôt, à qui ne l'a pas encore, une seule fois |
| après le décollage | — | rien |

## Ne jamais éditer la file à la main pour une carte

`--poser-carte` refuse un identifiant inconnu ou une entrée qui n'est pas un
vol (code 2) : c'est le signe d'une carte mal rattachée, à **signaler**. Il
verrouille la file pendant l'écriture, ce que ne fait pas une édition à la main
— un passage d'envoi simultané effacerait la carte.
