<!--
Ouvrir cette PR vaut publication : la CI la merge seule si tout est vert (voir
CLAUDE.md). Ce rappel est humain ; la CI, elle, tient ce qu'elle peut vérifier
(docs/garde-fous.md). Rien n'oblige à tout cocher : une case laissée vide se
justifie en une ligne.
-->

## Ce que change cette PR

<!-- Le comportement modifié, en une ou deux phrases — pas la liste des fichiers. -->

<!-- Les évals se jouent à la demande (le banc complet coûte ~55 $). Deux formes, une seule
à garder :
  1. Jouer les évals : poser le label `evals` sur la PR, puis écrire ici les catégories de
     `evals/categories.json` séparées par des virgules, puis « — raison » ; ou `tout`.
     Label posé sans cette ligne remplie, la CI joue tout le banc.
        Evals: existant, bruit — la PR ne touche que la recherche de l'existant
  2. Ne pas les jouer : écrire « aucun » et la raison (obligatoire), sans label.
        Evals: aucun — doc seule, aucun comportement ne change
Une PR qui touche un skill, un agent, un hook ou un `_partage/` sans label `evals` et sans
la ligne `Evals: aucun — <raison>` rend la CI rouge. -->
Evals: 

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
- [ ] **Évals** : l'A/B se joue à la demande (label `evals` posé, résultat collé plus
      bas), ou la ligne `Evals: aucun — <raison>` plus haut dit pourquoi il n'y en a
      pas. Sans label, la fumée tourne seule (job `fumee`) ; son verdict se lit
      dans « Verdict des évals ».
- [ ] **`scripts/ci_locale.sh`** est vert en local.

## Résultat A/B

<!-- Seulement si le label `evals` est posé : le tableau du job `evals`. Sinon « sans objet :
évals non demandées (voir la ligne `Evals:`) » : le résumé de la fumée n'a pas à être
collé ici. -->
