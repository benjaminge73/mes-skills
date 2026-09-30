# Résultats des évaluations

Une ligne par comparaison jouée par `scripts/evals_ab.py --journal`. Le bruit
(±) est mesuré en A/A quand un fichier de bruit a été fourni, estimé sinon.

**Notes** (au-dessus du tableau : `--journal` ajoute ses lignes en fin de
fichier, une note posée dessous couperait le tableau).

- **A/A local du 2026-09-30** : joué sur les 9 cas `lecture` seulement, Bash
  étant bloqué par le noyau du VPS. Le bruit y est **mesuré** : rms des écarts
  par cas 0,0385, soit ± 3 pts sur la moyenne et ± 8 pts par cas à 95 %. La
  cellule « ± 27 (estimé) » de la ligne est marquée « estimé » : elle n'utilise
  pas cette mesure. Les juges `plan-sans-question-ouverte` (`bruit-doc-seule`) et
  `decouverte-annoncee` (`existant-jeu-de-donnees`) ont été corrigés à la lecture
  des transcriptions **après** cette mesure : les scores de ces deux cas
  (79 % et 71 %) portent les anciens juges.
- **POC du 2026-09-30** (avant ce banc) : un cas simulé, une suite déjà rouge
  plus un hook `commit-msg`, 0.15.1 contre 0.16.0, 3 passages chacun. Seuil écrit
  avant : écart d'au moins 0,33 en faveur de 0.16.0 ; non atteint (0,67 contre
  0,50). Bash étant bloqué par le bac à sable du VPS, le banc est passé sur le
  runner GitHub.

| date | plugin | mode | base | tête | cas × passages | moyenne base → tête | écart ± bruit | par cas (base → tête) | coût | commande |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-30 | plans-notion | aa | HEAD (v0.16.1, 2975a28) | HEAD (v0.16.1, 2975a28) | 9 × 3 | 90 % → 90 % | +0 pts ± 27 (estimé) | appelants 100→100; bruit-bounded 88→90; bruit-doc-seule 77→79; existant-jeu-de-donnees 81→71; existant-jeu-de-questions 78→78; garde-fou-cache 100→100; hook-claude 95→100; maquette-requise 97→100; report-sans-seuil 94→94 | $53.14 | `python3 scripts/evals_ab.py --plugin plans-notion --mode aa --tete HEAD --sortie-bruit <fichier> -- --runs 3 --concurrency 3` |
| 2026-09-30 | plans-notion | ab | 0.15.1 | 0.16.0 | 1 × 3 | 67 % → 50 % | -17 pts ± non mesuré | cas simulé (suite déjà rouge + hook commit-msg) 67→50 | $4.46 | `POC, script jetable` |
