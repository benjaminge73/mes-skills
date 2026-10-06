#!/usr/bin/env bash
# Dépôt de départ du cas billet-voyageur-incertain : un voyage fictif, un mail de
# réservation déjà extrait en texte, un OneDrive simulé (dossier vide) et une file
# de rappels vide. Aucune donnée réelle : voyageurs et lieux sont génériques.
# N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p onedrive

cat > config-voyage.json <<'FIN_CONFIG'
{
  "voyage": "Destination Exemple",
  "libelle_gmail": "Voyages/Destination Exemple",
  "dossier_onedrive": "onedrive/Voyages",
  "dates": {"debut": "2027-04-10", "fin": "2027-04-17"},
  "fuseau": "Europe/Rome",
  "voyageurs": [
    {"cle": "voyageur_a", "nom": "Voyageur A", "principal": true},
    {"cle": "voyageur_b", "nom": "Voyageur B", "principal": false}
  ],
  "file_de_rappels": "rappels.json"
}
FIN_CONFIG

cat > mail.txt <<'FIN_MAIL'
De : billetterie@musee-exemple.example
Objet : Votre réservation EX-48213 est confirmée
Libellé : Voyages/Destination Exemple

Bonjour,

Votre réservation est confirmée.

  Référence de la commande : EX-48213
  Lieu : Musée Exemple, Place de l'Exemple, Ville B
  Date : lundi 12 avril 2027
  Heure d'entrée : 10h30 (heure locale)
  Billets : 1 × entrée plein tarif
  Total : 18,00 EUR

Votre billet est joint à ce message (billet-EX-48213.pdf). Présentez le QR code
à l'entrée, sur téléphone ou imprimé.

Ce billet n'est pas nominatif.

Cordialement,
La billetterie du Musée Exemple
FIN_MAIL

printf '[]\n' > rappels.json
