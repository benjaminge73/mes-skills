#!/usr/bin/env bash
# Dépôt de départ du cas maquette-requise : une boutique web dont le panier a un
# bouton « Valider ». Le libellé vit dans web/i18n/fr.json, est cité par un test
# e2e (tests/e2e/panier.spec.js) et par un e-mail de confirmation.
# N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p web/templates/emails web/static web/i18n tests/e2e

cat > README.md <<'EOF'
# commande-web

Pages de la boutique : panier, paiement, confirmation.

Les libellés sont dans `web/i18n/fr.json` ; les gabarits les lisent par clé.

## Tests

```bash
npm test
```
EOF

cat > package.json <<'EOF'
{
  "name": "commande-web",
  "version": "1.4.0",
  "private": true,
  "scripts": {
    "test": "playwright test tests/e2e"
  }
}
EOF

cat > web/i18n/fr.json <<'EOF'
{
  "panier.titre": "Votre panier",
  "panier.code_promo": "Code promo",
  "panier.appliquer": "Appliquer",
  "panier.valider": "Valider",
  "panier.total": "Total"
}
EOF

cat > web/templates/panier.html <<'EOF'
<main class="panier">
  <h1>{{ t("panier.titre") }}</h1>

  <ul class="lignes">
    {% for ligne in lignes %}
    <li>{{ ligne.nom }} × {{ ligne.quantite }} — {{ ligne.prix|prix }}</li>
    {% endfor %}
  </ul>

  <form class="code-promo" action="/panier/code" method="post">
    <label for="code">{{ t("panier.code_promo") }}</label>
    <input id="code" name="code" type="text">
    <button type="submit" class="btn-secondaire">{{ t("panier.appliquer") }}</button>
  </form>

  <p class="total">{{ t("panier.total") }} : {{ total|prix }}</p>

  <form action="/commande" method="post">
    <button type="submit" class="btn-primaire" data-testid="panier-valider">{{ t("panier.valider") }}</button>
  </form>
</main>
EOF

cat > web/templates/emails/confirmation.txt <<'EOF'
Bonjour {{ prenom }},

Vous avez cliqué sur « Valider » : votre commande {{ numero }} est enregistrée.

À bientôt.
EOF

cat > web/static/app.css <<'EOF'
.btn-primaire { background: #1f6feb; color: #fff; padding: 0.6rem 1.2rem; border: 0; border-radius: 4px; }
.btn-secondaire { background: #eee; color: #222; padding: 0.4rem 0.8rem; border: 0; border-radius: 4px; }
.total { font-weight: bold; }
EOF

cat > tests/e2e/panier.spec.js <<'EOF'
const { test, expect } = require('@playwright/test');

test('un client valide son panier', async ({ page }) => {
  await page.goto('/panier');
  await page.getByRole('button', { name: 'Valider' }).click();
  await expect(page).toHaveURL(/\/commande/);
});
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "commande-web : panier, libellés, e-mail de confirmation"
