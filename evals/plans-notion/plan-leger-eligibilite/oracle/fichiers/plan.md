# Plan : redémarrer le service app après la sauvegarde

La demande ajoute un droit `sudo` : le plan léger est refusé, le plan complet s'applique.

## Questions ouvertes

### Q1 — Redémarrer seulement après une sauvegarde réussie ?

- [ ] (reco) Oui
- [ ] Toujours

## Exécution

Étape 1 : ajouter la règle sudoers, bornée à la commande de redémarrage du service `app`.
Étape 2 : appeler cette commande dans `scripts/sauvegarde.sh`.

## Journal d'exécution

Vide.
