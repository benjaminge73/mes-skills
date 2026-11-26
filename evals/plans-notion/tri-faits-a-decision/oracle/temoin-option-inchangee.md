# Questions

**Q1 — Quel job envoie le rapport de veille dans `#veille` chaque matin ?**

- Option 1 (recommandée) — créer un nouveau job `rapport-veille-slack`, planifié à 7 h, qui poste dans `#veille`.
- Option 2 — réutiliser l'existant : le job `rapport-veille-quotidien` déjà actif.

**Q2 — Le rapport produit doit-il changer de contenu ?**

- Option 1 (recommandée) — non : le plan ne touche pas `scripts/rapport_veille.py`.
- Option 2 — oui : à chiffrer dans un plan séparé.
