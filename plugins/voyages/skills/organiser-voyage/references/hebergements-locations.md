# Réservation sans billet : hébergement et location

À lire quand le mail qualifié est un hébergement ou une location (étape 1 de
`SKILL.md`, branche « réservation sans billet »). Ce n'est pas un billet : pas de
voyageur, pas d'heure de début. La règle sur l'incertain reste la même : un champ
incertain ne se devine pas.

## Champs

| Type | Obligatoires | Facultatifs (défaut) |
|---|---|---|
| Hébergement | nom du logement, date d'arrivée, date de départ, lieu | heure d'arrivée (15h00), heure de départ (11h00) |
| Location | loueur, prise (date, heure, lieu), restitution (date, heure, lieu) | aucun |

- Heure facultative **absente** du mail : le défaut s'applique, et le compte rendu
  le dit.
- Heure facultative **présente mais illisible** : champ incertain, comme un
  obligatoire.
- Un obligatoire manquant ou supposé : `en_attente(champ)`, rien n'est rangé.
- Un hébergement n'a jamais de voyageur : la réservation est commune.

## Qualifier : seul le séjour confirmé compte

- **Compté** : le mail de confirmation d'un séjour (dates, logement, code de
  confirmation). Airbnb et tout émetteur du même type sont traités ainsi.
- **Ignoré** : reçu de paiement, message de l'hôte, rappel, même s'ils citent les
  dates du séjour.
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
  (date d'arrivée). Le gabarit est dans `nomenclature.md`. Pas de voyageur.
- **Location** : ni `nomenclature.md` ni `nommer_billet.py` n'ont de gabarit ni de
  type pour une location. Tant qu'il n'y en a pas, la pièce est
  `en_attente(nommage location)` : ne pas réutiliser le gabarit d'hébergement.
- **Rangement** : étape 4 de `SKILL.md`, dans le dossier du voyage. Sans pièce,
  rien n'est rangé.

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

## Événement, sous-dossier OneDrive et rappels : à compléter à l'étape suivante du plan
