# Réservation sans billet : hébergement et location

À lire quand le mail qualifié est un hébergement ou une location (étape 1 de
`SKILL.md`, branche « réservation sans billet »). Ce n'est pas un billet : pas de
voyageur, pas d'heure de début. La règle sur l'incertain reste la même : un champ
incertain ne se devine pas.

## Champs

| Type | Obligatoires | Facultatifs (défaut) |
|---|---|---|
| Hébergement | nom du logement, date d'arrivée, date de départ, lieu, code de confirmation | heure d'arrivée (15h00), heure de départ (11h00) |
| Location | loueur, prise (date, heure, lieu), restitution (date, heure, lieu), code de confirmation | aucun |

- Heure facultative **absente** du mail : le défaut s'applique, et le compte rendu
  le dit.
- Heure facultative **présente mais illisible** : champ incertain, comme un
  obligatoire.
- Un obligatoire manquant ou supposé : `en_attente(champ)`, rien n'est rangé.
- Code de confirmation absent ou illisible : `en_attente(code)`. Il sert au
  dédoublonnage ; les dates ne le remplacent jamais.
- Un hébergement n'a jamais de voyageur : la réservation est commune.

## Qualifier : seul le séjour confirmé compte

- **Compté** : le mail de confirmation d'un séjour (dates, logement, code de
  confirmation), ou d'une location (loueur, prise, restitution, code). Airbnb et
  tout émetteur du même type sont traités ainsi.
- **Ignoré** : reçu de paiement, message de l'hôte ou du loueur, rappel, même s'ils
  citent les dates du séjour ou de la location.
- **Modification** (dates ou heure changées) : elle met à jour l'événement existant
  (voir le renvoi plus bas) et le compte rendu la signale comme modification.

## La pièce : oui ou non

- **PDF joint au mail** : c'est la pièce. Elle est rangée telle quelle, sans
  découpe par QR : `recuperer_billet.py` n'est pas appelé pour ce flux.
- **Pas de PDF joint** : aucun fichier. Pas de PDF fabriqué depuis le corps du
  mail, pas de capture d'écran. La référence seule va à l'événement et à Notion :
  le **code de confirmation** et le **lien direct** vers la page de la réservation
  (Airbnb, ou le site de l'organisme de location).
- **Lien de téléchargement ou QR dans le corps** : non suivi pour ce flux. Sans PDF
  joint, c'est le cas ci-dessus.
- Notion n'est pas écrit par ce skill : la référence part à l'appelant, qui
  l'écrit.

## Nommer et ranger (seulement avec une pièce)

- **Hébergement** : `nommer_billet.py`, type `hebergement`, champs `nom` et `date`
  (date d'arrivée), `document` facultatif. Pas de voyageur.
- **Location** : `nommer_billet.py`, type `location`, champs `lieu` (lieu de prise en
  charge), `loueur`, `date` (date de prise), `document` facultatif. Gabarit :
  `AAAA-MM-JJ - Location voiture Lieu - Loueur - Document`. Pas de voyageur. Le
  script ne lit pas l'heure de prise : elle se lit dans le mail et se vérifie à
  part ; absente ou incertaine, `en_attente(heure)`.
- **`document`** (hébergement et location) : `Reservation` par défaut, sinon
  `Contrat` ou `Assurance`. Accent et casse ignorés (`Réservation` s'écrit
  `Reservation`). Un autre document se signale ; la liste s'élargit dans le script.
- **Rangement** : étape 4 de `SKILL.md`, dans le dossier du voyage, au sous-dossier
  de la configuration (plus bas). Sans pièce, rien n'est rangé.

Exemple anonymisé : hébergement « Appartement Exemple », arrivée 2027-04-10,
départ 2027-04-17, sans PDF joint. Aucun fichier. L'événement et Notion reçoivent
le code `CODE-EXEMPLE` et le lien direct de la réservation.

## Compte rendu : trois issues

- `traité` : tout ce que ce flux prévoit est fait (pièce rangée s'il y en a une,
  référence remise à l'appelant). Une modification traitée porte la mention
  « modification ».
- `ignoré` : pas une réservation (reçu, message de l'hôte, rappel).
- `en_attente(raison)` : réservation qualifiée mais non traitée : obligatoire
  manquant ou incertain, échec d'écriture (rangement, événement). Elle n'est **pas**
  marquée « vue » : elle est retentée au passage suivant. La raison dit quoi.

Le compte rendu des billets, dans `SKILL.md`, dit « signalé » : pour ce flux, c'est
`en_attente(raison)`.

## Événement, sous-dossier OneDrive et rappels

- **Un seul événement par séjour**, de l'arrivée au départ : début = date d'arrivée à
  l'heure de check-in, fin = date de départ à l'heure de check-out. Pour une
  location : un seul événement, de la prise à la restitution (début = prise, fin =
  restitution).
- **Fuseau et adresse** : `timeZone` IANA du **logement** (ou du lieu de prise),
  déduit de la ville ; `location` = l'adresse. Si la ville est ambiguë (p.ex. une
  ville frontalière dont le fuseau diffère de celui des vols), le compte rendu le
  signale.
- **Description** : le code de confirmation, le **lien direct** de la réservation
  (relevé dans le mail : page Airbnb ou de l'organisme), et le lien privé OneDrive
  (`webUrl`) **seulement si une pièce est rangée**.
- **Invités** : le voyageur B est invité, comme pour les vols. La liste vient de
  `agenda.invites` de la configuration du voyage ; le créateur, de `agenda.createur`.
- **Dédoublonnage avant toute création** : chercher dans l'agenda un événement qui
  porte déjà le **même code de confirmation**, et seulement lui. Des dates communes
  ne font pas « le même » événement : une location aux dates d'un séjour, ou la visite
  d'un jour de séjour, garde le sien. S'il existe, on ne crée rien : on le met à jour
  si le mail est une modification, sinon on le laisse.
- **Sous-dossier OneDrive** : `onedrive_sous_dossiers` de la configuration du voyage
  (`billets_avion`, `hebergement`, `location`), lu par l'agent. Clé absente :
  `en_attente(sous-dossier non configuré)`. Ne rien deviner, ne jamais écraser
  (`conflictBehavior=fail`). Le sous-dossier ne sert que s'il y a une **pièce** :
  sans pièce, rien n'est rangé.
- **Rappels** : aucun rappel Telegram pour un hébergement ou une location ; l'événement
  suffit.
- **Notion (consigne à l'appelant)** : ce skill n'écrit pas Notion. L'appelant
  complète la puce qui porte le **même code de confirmation** : lien direct de la
  réservation, et lien OneDrive en plus si une pièce est rangée. Il ne crée une puce
  que si aucune ne porte ce code. Une puce aux mêmes dates, sans ce code, n'est pas
  la même réservation : elle n'est jamais complétée.
