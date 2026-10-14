#!/usr/bin/env bash
# Dépôt de départ du cas preuve-par-reponse : la page de plan relances-clients est
# en revue. Q1 (canal des relances) est tranchée, sans ligne « Preuve : » ; Q2
# (fréquence des relances) reste ouverte. La passe « filtre avant valide » doit
# ajouter la preuve de Q1 et ne toucher ni à Q2 ni au code. Les fichiers sont
# fixes, sans aléa. N'écrit que dans le répertoire courant.
set -euo pipefail

mkdir -p docs src

cat > README.md <<'EOF'
# relances-clients
Module qui envoie les relances de factures impayées.
Les limites du fournisseur d'envoi sont dans `docs/limites.md`.
EOF

cat > docs/limites.md <<'EOF'
# Limites du fournisseur d'envoi
Ce qui encadre les envois de relances, canal par canal.
3. SMS : 0,07 € par message, quota fournisseur de 500 messages par mois.
4. E-mail : gratuit, jusqu'à 10 000 messages par jour.
EOF

cat > src/relances.py <<'EOF'
def envoyer_relance(client, canal):
    """Envoie une relance. Pas encore branché."""
    raise NotImplementedError("à écrire après validation du plan")
EOF

cat > plan.md <<'EOF'
# [Plan] relances-clients - Canal des relances

**Statut** : en revue

## Besoins

- Le module doit envoyer une relance par facture impayée, par le canal retenu.

## Maquette

Pas de maquette — aucune étape ne change ce qui s'affiche.

## Questions ouvertes

### ✅ Q1 — Canal des relances
<callout icon="✅" color="green_bg">
	**E-mail.**
	- [ ] E-mail (reco)
	- [ ] SMS
	- [ ] Autre / complément →
	Réponse de Benjamin dans le chat du 2026-10-14 : e-mail.
</callout>
### 🧭 Q2 — Fréquence des relances
<callout icon="🧭" color="orange_bg">
	**Combien de jours entre deux relances ?**
	- [ ] 7 jours (reco)
	- [ ] 14 jours
	- [ ] Autre / complément →
</callout>

## Exécution

### Étape 1 — Envoyer la relance par e-mail

- **Fichiers touchés** : `src/relances.py`.
- **Preuve de fin** : un test à écrire après validation.

## Journal d'exécution

Se remplira à l'implémentation.
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "relances-clients : plan en revue, Q1 tranchée sans preuve"
