# Clôture : les points un par un

Détail du § 6 (« Clore ») de `executer-plan-notion/SKILL.md`, lu à la demande (renvoi du SKILL.md). Texte déplacé tel quel, sans réécriture.

- `Statut` : **`a merger`** tant que le code n'est pas sur `main` — l'état de fin
  de clôture, sur tous les dépôts (PR ouverte, en brouillon seulement si
  Benjamin l'a demandé). **`execute`** se pose dès que le merge est
  vérifié sur `main`, dans le tour où on le constate ; `execute` ne se pose que
  sur du code **vérifié sur `main`**, et la symétrie est vraie aussi : jamais
  `a merger` sur du travail déjà parti sur `main`. `execute` est le seul statut de fin.
- `Branche` renseignée ; `PR` porte l'URL de la PR dès qu'elle existe, et reste
  **vide** tant que la PR n'a pas été ouverte.
- `Journal d'exécution` clos par une entrée `État final` (H3) : ce qui est
  livré, le verdict de la suite complète, les écarts, le reste à faire (chaque
  ligne avec son propriétaire, §7), plus : le décompte des découvertes **vérifié
  mécaniquement** (`grep -c`, jamais de tête), le contrôle des libellés, le
  registre des outils, **un verdict par étape (`verified` ou
  `unverifiable`, jamais un troisième mot)**, une rétrospective en six
  questions, les schémas relus
  (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/schemas.md`).
- Le compte rendu est le **récap** (`changelog-et-doc.md`, § 3) : les quatre rubriques,
  puis `PR` et `Statut`, puis « Côté technique » — étapes parties en sous-agent
  `executant` (Haiku) et pourquoi pour les autres, PR ouverte (son URL, prête, ou
  pourquoi retenue), palier qui a posé le Changelog.
- **Preuve doc, avant le push** : `qualite-doc.py lecteurs` puis `juger` (`cloture.md`, point 2 bis) ; passages douteux ou marqués d'office traités, sinon la clôture ne s'ouvre pas.
- **Porte des preuves, avant le push** : `preuves-des-etapes.py <page.md>
  --apres` — code 0, on poursuit ; code 1, des défauts de journal, on corrige
  la page et on rejoue ; code 3, une étape `unverifiable` est nommée, et sa
  question part à Benjamin avant la PR (`cloture.md`, point 3).
- **Livrer la PR prête, et la suivre jusqu'au merge** : la suite complète jouée
  en local, e2e compris, c'est le verdict de fin de plan — la PR ne s'ouvre pas
  sur une suite rouge ; puis le push de la branche, et la PR ouverte (`gh pr
  create`, sans `--draft`), label décidé en regardant ce dépôt-là. Un trou e2e
  non couvert par la CI du dépôt se pose à Benjamin **avant** cette ouverture.
  Juste après, et **avant toute attente de CI**, le contrôle bloquant
  (`git branch --list '<branche-du-plan>-etape-*'`, `git worktree list`). Dans le
  même tour : `Statut` = `a merger`, `PR`, `État final` et le compte rendu. Alors
  seulement, la CI : elle se suit en arrière-plan, **sans jamais merger
  soi-même**. Merge constaté sur `main` → `execute`, puis retrait du worktree,
  **pas la branche**. Rouge → correction dans le worktree encore présent. Retenue,
  ou session qui s'arrête avant le merge → le worktree se retire, `a merger`
  reste avec l'URL de la PR. Le détail des points et des trois issues : `cloture.md`.
