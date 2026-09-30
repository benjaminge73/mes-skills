<!--
Ouvrir cette PR vaut publication : la CI la merge seule si tout est vert (voir
CLAUDE.md). Ce rappel est humain ; la CI, elle, tient ce qu'elle peut vérifier
(docs/garde-fous.md). Rien n'oblige à tout cocher : une case laissée vide se
justifie en une ligne.
-->

## Ce que change cette PR

<!-- Le comportement modifié, en une ou deux phrases — pas la liste des fichiers. -->

## Avant de merger

- [ ] **Cas d'éval** : la leçon a son cas dans `evals/<plugin>/` — ou un commit porte
      `Eval-cas: <cas existant>` / `Eval-cas: aucun — <raison>` (la CI le vérifie,
      voir `scripts/check_lecon_a_son_cas.py`).
- [ ] **Registre** : le correctif a sa ligne dans `docs/garde-fous.md`, avec le garde
      qui le tient, dans cette même PR.
- [ ] **Version** : `version` montée dans `plugins/<nom>/.claude-plugin/plugin.json`
      pour chaque plugin touché (la CI le vérifie).
- [ ] **Veille** : si la PR touche un skill, un agent, un hook ou un `_partage/`, la passe
      de veille est faite (`chercheur`, brief de `docs/veille.md`) et l'entrée datée
      est au journal (la CI refuse un journal de plus de 30 jours).
- [ ] **A/B** : résultat de l'A/B collé ici, ou dit pourquoi il n'y en a pas
      (`python3 scripts/evals_ab.py`, job `evals`).
- [ ] **`scripts/ci_locale.sh`** est vert en local.

## Résultat A/B

<!-- Le tableau du job `evals`, ou « sans objet : la PR ne touche ni skill, ni agent, ni hook ». -->
