# Questions

**Q1 — Quel job envoie le rapport de veille dans `#veille` chaque matin ?**

- Option 1 (recommandée) — réutiliser le job existant `rapport-veille-quotidien` (id `f3a9c1`, `0 7 * * *`, déjà actif sur `slack:#veille`, fait de C4) : rien à créer, seulement à vérifier que le rapport produit convient.
- Option 2 — créer un second job `rapport-veille-slack` : deux envois par jour dans le même canal, sauf à désactiver l'ancien ; une seconde source de vérité à tenir.

**Q2 — Le rapport produit par le job existant doit-il changer de contenu ?**

- Option 1 (recommandée) — non : le plan ne touche pas `scripts/rapport_veille.py`.
- Option 2 — oui : à chiffrer dans un plan séparé, puisque le contenu n'a pas été relu (non vérifié, fiche).
