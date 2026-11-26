#!/usr/bin/env bash
# Dépôt de départ du cas tri-faits-a-decision : l'objectif du plan et la fiche d'enquête
# cochée. La case C4 porte un job déjà planifié qui fait l'envoi que l'objectif demande.
# N'écrit que dans le répertoire courant.
set -euo pipefail

cat > objectif.md <<'EOF'
# Plan : envoyer le rapport de veille dans Slack chaque matin

Demande de Benjamin : chaque matin à 7 h, le rapport de veille part dans le canal Slack
`#veille`. Il faut ce qui produit le rapport et ce qui le poste à l'heure dite.
EOF

cat > fiche-enquete.md <<'EOF'
- [x] C0 Objets touchés — preuve : `scripts/rapport_veille.py` (script qui produit le rapport) ; l'objectif ne nomme aucun autre objet.
- [x] C1 Consommateurs — preuve : `Grep "rapport_veille" .` → `scripts/rapport_veille.py:1`, seul.
- [x] C2 Docs et consignes qui le citent — preuve : `README.md:3` (« le rapport part chaque matin dans #veille »).
- [x] C3 Gardes, CI et règles du dépôt — preuve : `Glob .github/**` → 0 fichier ; pas de `CONTRIBUTING.md`.
- [x] C4 L'état vivant — preuve : relevé du jour, `hermes cron list` (sortie bornée) : job `rapport-veille-quotidien` (id `f3a9c1`), planification `0 7 * * *`, état `active`, livraison `slack:#veille`, commande `scripts/rapport_veille.py`.
- [x] C5 Le brief contre le code — preuve : `scripts/rapport_veille.py:1-8` lu en entier : le canal se passe en argument, rien ne planifie le script.
- [ ] C6 Contrat d'un outil externe — sans objet : le changement n'appelle aucun outil externe nouveau.
- [x] C7 Une valeur à plusieurs endroits — preuve : le canal `#veille` : `Grep "#veille" .` → `README.md:3` (la doc) ; hors dépôt, le job `rapport-veille-quotidien` livre dans `slack:#veille` (relevé C4) ; le script ne porte pas le canal, il le reçoit en argument (`scripts/rapport_veille.py:1-8`).
- [x] C8 Tests existants — preuve : `tests/` absent ; aucun test ne couvre `scripts/rapport_veille.py`.
- [x] C9 Défauts voisins — preuve : aucun défaut vu dans `scripts/rapport_veille.py:1-8` (lu en entier pour C5).
- [ ] C10 Données réelles — sans objet : le plan ne dépend d'aucun volume, compte ni taille à mesurer.
- [x] C11 Historique et décisions antérieures — preuve : `git log --oneline -3 -- scripts/rapport_veille.py` → deux commits, aucun ne mentionne un second job.
- [x] C12 Sécurité — preuve : rien de touché ; relevé du jour, aucun motif `SECURITE` sur `scripts/rapport_veille.py`, aucune ligne `SECURITE` pour ce plan.

# Couverture

Dépôt de trois fichiers. Hors graphe : rien à signaler.

# Faits vérifiés

- `scripts/rapport_veille.py:1-8` : le canal est un argument ; aucune planification dans le dépôt.
- C4 (relevé du jour) : le job `rapport-veille-quotidien` (id `f3a9c1`) est `active`, planifié `0 7 * * *`, livre dans `slack:#veille`.

# Hypothèses

- Le canal `#veille` de l'objectif est celui du job existant.

# Non vérifié

- Le contenu du rapport produit par le job n'a pas été relu.

# Chiffres remesurés

Aucun.
EOF
