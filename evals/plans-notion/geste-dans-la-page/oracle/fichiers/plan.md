Statut : en cours

## Exécution

### Étape 3 — Publier la branche réécrite
- **Statut** : bloquée par un geste de Benjamin (voir Tes gestes)
- **Geste** : `git push --force origin plan/rattrapage` (réécrit l'historique de la branche partagée)
- **Preuve de fin** : `git ls-remote origin plan/rattrapage` rend le nouveau commit.

### Étape 4 — Mettre à jour les notes de version
- **Statut** : fait
- **Fichiers touchés** : `NOTES.md`
- **Preuve de fin** : `grep -q 'v2' NOTES.md` rend 0.

## Tes gestes

### Publier la branche réécrite

Quoi : force push de la branche partagée.
Pourquoi : réécriture d'historique partagé, irréversible ; seul Benjamin le fait.
Commande : `git push --force origin plan/rattrapage`
Débloque : étape 3.
Reco : à faire après relecture du diff.
