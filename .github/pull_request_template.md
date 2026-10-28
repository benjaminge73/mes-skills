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
Sans label et sans cette ligne, rien ne se joue (hors fumée, qui ne part que sur le label
`fumee`) : cette ligne documente le choix, elle ne rend plus la CI rouge à elle seule (voir
`Eval-cas:` plus bas, qui lui, bloque). La fumée se demande par le label `fumee` : ouvrir la
PR en brouillon avec ce label, puis la passer prête (docs/tester-un-skill.md). -->
Evals: 

<!-- Doc vivante (Mes Skills l'a activée) : le job `doc` de la CI refuse la PR sans cette
ligne. Soit le lien Notion de l'entrée du Changelog (ouvrir la PR, écrire l'entrée en citant
son numéro, puis éditer cette ligne : le job `doc` attend jusqu'à 10 minutes qu'elle se remplisse, au-delà il faut relancer le job), soit « sans objet — <raison> »
quand rien ne change pour la personne qui se sert des plugins (CI interne, test, veille). -->
Doc : 

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
      pas. La fumée ne tourne que si la PR porte le label `fumee` (job `fumee`) ; son
      verdict se lit dans « Verdict des évals ».
- [ ] **`scripts/ci_locale.sh`** est vert en local.

## Résultat A/B

<!-- Seulement si le label `evals` est posé : le tableau du job `evals`. Sinon « sans objet :
évals non demandées (voir la ligne `Evals:`) » : le résumé de la fumée n'a pas à être
collé ici. -->
