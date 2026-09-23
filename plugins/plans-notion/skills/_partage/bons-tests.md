# Ce qui fait un bon test

Fichier **partagé**, lu par `executant` (section « Quand tu écris un
test ») et par `plan-notion` (chapitre `Exécution`,
puce **Test attendu**). Comme `preuve-du-rouge.md`, il vit à un seul endroit
pour que les deux skills gardent leur taille : la règle ne se duplique pas,
elle se référence.

Il ne dit pas *comment* prouver qu'un test a mordu avant de le faire passer
(`preuve-du-rouge.md`) — il dit ce qui fait qu'un test, une fois rouge, vaut
la peine d'exister. **Le rouge ne suffit pas** : un test à assertion miroir
(règle 4) est rouge avant que le code n'existe et vert dès qu'il existe, sans
avoir jamais rien vérifié entre les deux. C'est exactement ce que traque la
catégorie « test qui ne teste rien » du relecteur (`agents/relecteur.md`).

## Pourquoi ce fichier

Quatre règles, reprises de `writing-good-tests.md`
([obra/superpowers](https://github.com/obra/superpowers)) et resserrées à ce
qu'un exécutant peut vérifier lui-même avant de commiter le rouge.

## 1. Nommer la panne

Le nom du test dit **quel comportement cassé** il attrape, pas quelle
fonction il appelle. `test_calculateTotal()` ne dit rien ; en le lisant seul,
personne ne sait ce qui a été cassé le jour où il devient rouge.

```javascript
// ❌ nomme la fonction, pas la panne
it('calculateTotal', () => { ... });

// ✅ nomme le comportement cassé qu'il attrape
it('applique la remise seulement au-delà de 100€', () => { ... });
```

## 2. Attendu dérivé indépendamment du code

La valeur attendue vient de la spécification, d'un calcul à la main, ou d'un
exemple réel — jamais recopiée de la sortie du code qu'on teste. Un attendu
qui sort d'un `print()` ou d'un `console.log()` collé dans l'assertion prouve
que le code fait ce qu'il fait, pas ce qu'il doit faire.

```python
# ❌ l'attendu vient d'avoir fait tourner le code une fois et copié le résultat
assert format_price(19.9) == "19,90 €"  # collé depuis la sortie observée

# ✅ l'attendu vient de la règle métier ("deux décimales, virgule, espace, €")
assert format_price(19.9) == "19,90 €"  # dérivé de la spec, pas de la sortie
```

L'exemple ci-dessus a la même ligne des deux côtés : c'est volontaire — rien
dans le code ne distingue un attendu recopié d'un attendu dérivé à la main.
Seule la façon dont il a été obtenu fait la différence, et c'est pour ça que
cette règle ne se vérifie pas au diff : elle se vérifie à l'écriture.

## 3. Pas de « change detector »

Un test qui casse à chaque refactor sans changement de comportement observable
— un ordre d'appels internes, une structure de données interne, un texte
entier figé — ne protège rien : il coûte à chaque refactor légitime, et il
laisse passer un vrai bug si celui-ci respecte la structure figée.

```javascript
// ❌ change detector : casse si l'implémentation change l'ordre des clés,
// même si le comportement observable ne change pas
expect(JSON.stringify(result)).toBe('{"id":1,"name":"a","active":true}');

// ✅ teste le comportement, insensible à l'ordre ou aux détails internes
expect(result).toMatchObject({ id: 1, name: 'a', active: true });
```

## 4. Pas d'assertion miroir

Une assertion qui recalcule le résultat avec la **même logique** que le code
testé passe forcément, quelle que soit la logique en cause — bonne ou
mauvaise. Le test double la logique, il ne la vérifie pas.

```python
# ❌ assertion miroir : le même calcul des deux côtés, toujours vrai
def test_apply_discount():
    price, rate = 100, 0.2
    assert apply_discount(price, rate) == price - price * rate  # même formule

# ✅ attendu littéral, dérivé à la main
def test_apply_discount():
    assert apply_discount(100, 0.2) == 80
```

Le lien avec la preuve du rouge (`preuve-du-rouge.md`) : une assertion miroir
peut très bien être rouge avant que le code n'existe — `apply_discount` non
défini fait échouer n'importe quelle assertion. Le rouge initial ne distingue
pas un test qui mord d'un test qui ne fait que refléter le code à venir ;
seules ces quatre règles, lues à l'écriture, font cette différence.

---

*Adapté de [obra/superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent /
Prime Radiant). Récupéré le 2026-09-23. Modifications : quatre règles retenues sur les
deux principes de `writing-good-tests.md` (nommer la panne, attendu indépendant, pas de
change detector, pas d'assertion miroir — le principe « exercer le réel », sur les
mocks, n'est pas repris ici), exemples reformulés en JS/Python génériques, lien ajouté
vers `preuve-du-rouge.md`.*
