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
	Preuve : lecture — docs/limites.md:3 (le SMS coûte 0,07 € par message et plafonne à 500 par mois, l'e-mail est gratuit)
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
