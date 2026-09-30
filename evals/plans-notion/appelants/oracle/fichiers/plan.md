# Paramètre obligatoire `locale` pour `format_prix`

## Cartes

`core/prix.py` (`format_prix`) ← `billing/facture.py`, `reports/mensuel.py` (alias `fp`), `web/filtres.py` (par nom en chaîne), `tests/test_prix.py`.

## Besoins

- `format_prix(montant, devise, locale)` écrit la virgule décimale en français et le point en anglais.

## Maquette

L'étape 2 change ce que voit le client (séparateur décimal des prix). État cible, en français puis en anglais :

```html
<!-- Maquette — passe 1 · 2026-09-30 -->
<section lang="fr"><p>stylo : 2,00 €</p><p>Chiffre d'affaires du mois : 1250,00 €</p></section>
<section lang="en"><p>stylo : 2.00 €</p><p>Chiffre d'affaires du mois : 1250.00 €</p></section>
```

## Contraintes techniques vérifiées

- Définition : `core/prix.py:1`. Appelants trouvés par `grep -rn format_prix .` **et** `grep -rn "fp(" .` :
  - `billing/facture.py:5` — appel direct ;
  - `reports/mensuel.py:1,5` — importé sous l'alias `fp` : une recherche de `format_prix(` ne voit pas l'appel ;
  - `web/filtres.py:4,8` — la fonction est désignée par son nom en chaîne (`FILTRES = {"prix": "format_prix"}`) puis appelée par `getattr` : aucune recherche d'appel ne la voit, et une erreur n'apparaîtrait qu'à l'exécution (`TypeError`) ;
  - `tests/test_prix.py:8` — le test de la fonction elle-même.
- `tests/test_facture.py` passe par `ligne_facture` : il casse par ricochet si `billing/facture.py` n'est pas adapté.
- Existant cherché : sans objet — paramètre ajouté à une fonction du projet. / trouvé : — / fait maison parce que le besoin est interne.

## Questions ouvertes

### 🧭 Q1 — Que fait `web/filtres.py` pour la locale ?

- [ ] (reco) La locale du site est lue une fois dans `web/filtres.py` et passée à `appliquer("prix", montant, devise, locale)`
- [ ] Le gabarit passe la locale à chaque appel
- [ ] Autre / complément →

## La suite

Rien.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Nouvelle signature | `core/prix.py`, `tests/test_prix.py` | — | 1 |
| 2 — Appelants | `billing/facture.py`, `reports/mensuel.py`, `web/filtres.py`, `tests/test_facture.py` | 1, Q1 | 2 |

### Étape 1 — Nouvelle signature

- **Choix d'architecture** : `format_prix(montant, devise, locale)`, paramètre obligatoire sans valeur par défaut, pour que tout appelant oublié échoue au lieu d'afficher un prix faux. Écarté : valeur par défaut « fr », qui masquerait un appelant oublié.
- **Fichiers touchés** : `core/prix.py` (modifié), `tests/test_prix.py` (modifié).
- **Dépend de** : —
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien tant que les appelants n'ont pas changé de locale.
- **Impact technique** : casse les quatre appelants jusqu'à l'étape 2.
- **Preuve de fin** : `python3 -m unittest tests.test_prix` vert.
- **Test attendu** : `format_prix(12.5, "EUR", "fr")` rend `12,50 €` et `"en"` rend `12.50 €`.

### Étape 2 — Adapter les appelants

- **Choix d'architecture** : chaque appelant passe la locale explicitement, y compris `web/filtres.py` où l'appel est en `*args`.
- **Fichiers touchés** : `billing/facture.py`, `reports/mensuel.py`, `web/filtres.py`, `tests/test_facture.py` (tous modifiés).
- **Dépend de** : étape 1, Q1.
- **Taille** : 4 fichiers.
- **Impact fonctionnel** : les prix des factures et du rapport mensuel s'écrivent avec la locale choisie.
- **Impact technique** : signature de `ligne_facture` et de `resume` étendue si la locale vient de l'appelant.
- **Preuve de fin** : `python3 -m unittest discover -s tests` vert et `grep -rn "format_prix\|fp(" .` ne montre aucun appel à deux arguments.
- **Test attendu** : `web.filtres.appliquer("prix", 3, "EUR", "fr")` rend `3,00 €` — c'est ce test qui attrape l'appel par nom en chaîne.

## Journal d'exécution

_Se remplira à l'exécution._
