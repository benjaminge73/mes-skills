# Renommer le bouton « Valider » du panier en « Confirmer la commande »

## Cartes

`web/i18n/fr.json` (clé `panier.valider`) → `web/templates/panier.html` (bouton) ; cité aussi par `tests/e2e/panier.spec.js` et `web/templates/emails/confirmation.txt`.

## Besoins

- Le bouton du bas de page du panier ne se confond plus avec la validation du code promo : il s'appelle « Confirmer la commande ».

## Maquette

Le bouton change de libellé ; même petit, ce changement se montre. État cible de la page du panier :

```html
<!-- Maquette — passe 1 · 2026-09-30 · état cible -->
<main class="panier">
  <h1>Votre panier</h1>
  <form class="code-promo">
    <label for="code">Code promo</label>
    <input id="code" type="text">
    <button type="button" class="btn-secondaire">Appliquer</button>
  </form>
  <p class="total">Total : 24,90 €</p>
  <button type="button" class="btn-primaire">Confirmer la commande</button>
</main>
```

## Contraintes techniques vérifiées

- Le libellé vit dans `web/i18n/fr.json:5` (`"panier.valider": "Valider"`) ; `web/templates/panier.html:19` lit la clé, il n'a pas de texte en dur (`grep -rn "Valider" .`).
- **Le test e2e dépend du libellé** : `tests/e2e/panier.spec.js:5` sélectionne le bouton par `{ name: 'Valider' }`. Sans mise à jour, `npm test` casse.
- **L'e-mail de confirmation cite le libellé** : `web/templates/emails/confirmation.txt:3` dit « Vous avez cliqué sur « Valider » ». Le bouton ne s'appellerait plus ainsi.
- La clé `panier.valider` n'a pas d'autre usage (`grep -rn "panier.valider" .`).
- Existant cherché : sans objet — libellé propre au projet. / trouvé : — / fait maison parce que le besoin est interne.

## Questions ouvertes

### 🧭 Q1 — Renomme-t-on aussi la clé `panier.valider` ?

- [ ] (reco) Non, seule la valeur change : la clé reste stable
- [ ] Oui, en `panier.confirmer`
- [ ] Autre / complément →

## La suite

Rien.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Libellé | `web/i18n/fr.json` | — | 1 |
| 2 — Test et e-mail | `tests/e2e/panier.spec.js`, `web/templates/emails/confirmation.txt` | — | 1 |

### Étape 1 — Changer le libellé

- **Choix d'architecture** : seule la valeur de `panier.valider` change dans `web/i18n/fr.json`. Écarté : texte en dur dans le gabarit.
- **Fichiers touchés** : `web/i18n/fr.json` (modifié).
- **Dépend de** : Q1.
- **Taille** : 1 fichier.
- **Impact fonctionnel** : le bouton principal du panier affiche « Confirmer la commande » — c'est la partie « bouton primaire » de la maquette.
- **Impact technique** : aucun.
- **Preuve de fin** : `grep -n "panier.valider" web/i18n/fr.json` montre « Confirmer la commande ».
- **Test attendu** : —

### Étape 2 — Aligner le test et l'e-mail

- **Choix d'architecture** : le test sélectionne le bouton par `data-testid="panier-valider"` plutôt que par son nom, pour ne plus dépendre du libellé. Écarté : réécrire le nom dans le test, qui casserait au prochain renommage.
- **Fichiers touchés** : `tests/e2e/panier.spec.js` (modifié), `web/templates/emails/confirmation.txt` (modifié).
- **Dépend de** : —
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : l'e-mail dit « Vous avez cliqué sur « Confirmer la commande » ».
- **Impact technique** : le test e2e ne dépend plus du libellé.
- **Preuve de fin** : `npm test` vert.
- **Test attendu** : le test e2e clique sur le bouton du panier et atteint `/commande`, quel que soit le libellé.

## Journal d'exécution

_Se remplira à l'exécution._
