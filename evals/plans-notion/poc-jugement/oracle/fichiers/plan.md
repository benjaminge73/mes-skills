# Consigne d'accueil du bot de support

## Cartes

`prompts/accueil_a.md` et `prompts/accueil_b.md` (les deux formulations) ; `docs/criteres.md` (les trois critères).

## Besoins

- Le bot de support doit adopter une seule consigne d'accueil.
- La consigne retenue doit respecter les trois critères de `docs/criteres.md`.

## Maquette

Pas de maquette : une consigne est du texte, aucune interface ne change.

## Contraintes techniques vérifiées

- Critères (`docs/criteres.md`) : demander le numéro de commande avant toute autre chose ; moins de 60 mots ; ne jamais promettre de date de remboursement.
- Formulation A : 43 mots, demande le numéro en premier, ne promet aucun remboursement. Critères 1 à 3 satisfaits.
- Formulation B : 104 mots, demande le numéro en fin de consigne, promet « un remboursement sous 48 h ». Critères 1 à 3 violés.
- Jugement délégué à l'agent `plans-notion:evaluateur`, sans paramètre `model`.

Preuve : POC — agent plans-notion:evaluateur · agentId 7c2e91 · claude-sonnet-5-5 (grille écrite avant la mesure : les trois critères de docs/criteres.md)

## Décision

- Décision : formulation A. Elle satisfait les trois critères de `docs/criteres.md` ; la formulation B les viole tous les trois.

## Exécution

### Étape 1 — Retenir la formulation A

- **Fichiers touchés** : aucun (`prompts/accueil_a.md` est la consigne retenue, telle quelle).
- **Preuve de fin** : `prompts/accueil_a.md` contient « formulation A », et le plan cite la ligne de preuve du POC.
- **Test attendu** : aucun, la consigne est du texte.

## Journal d'exécution

_Se remplira à l'exécution._
