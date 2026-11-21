# Ce que le skill ne fait pas : le détail

Détail du § 8 (« Ce que ce skill ne fait pas ») de `executer-plan-notion/SKILL.md`, lu à la demande (renvoi du SKILL.md). Texte déplacé tel quel, sans réécriture.

- Il ne **conçoit** pas le plan — c'est `plan-notion`. Il **tient à jour** le
  chapitre `Exécution` : à l'entrée pour y répercuter les dernières réponses de
  Benjamin (§2), et en cours de route pour les écarts datés (§4). Mettre à jour
  n'est pas concevoir ; si l'approche est en cause, la main repasse à
  `plan-notion`.
- Il ne crée de sa propre initiative que deux sortes de page : le **plan de suite
  `#N+1`** en clôture (§7), qui repart ensuite en `plan-notion` comme n'importe
  quel brouillon, et, quand une session porte plusieurs plans, le **plan maître**
  du lancement, s'il n'existe pas déjà (« Plusieurs plans »).
- Il ne code pas si le statut n'est pas `valide`.
- Il n'écrit pas lui-même le code des étapes déléguables : ça part en sous-agent
  `plans-notion:executant`, **Haiku par définition** (son frontmatter,
  sans numéro de version) — un par étape en séquence par défaut, mais
  pas absolument : en parallèle par vagues, ou regroupées, quand `vagues.md`
  le permet ou le prescrit (§3). Piloter, ce n'est pas coder.
- Il ne relit pas lui-même le diff d'une étape à la place de l'agent
  `plans-notion:relecteur` : un regard qui a piloté l'étape partage ses angles
  morts avec celui qui l'a écrite. Il **fait relire** (§3, `revue.md`), et
  vérifie chaque remarque avant d'agir dessus.
- Il ne code jamais dans le checkout principal du dépôt : la branche du plan
  vit dans un worktree dédié dès sa création (§2), retiré à la clôture (§6) —
  jamais avant, et jamais à la place de la branche elle-même, que le hook
  `SessionStart` nettoie après le merge.
- Il n'ouvre **la** PR du plan qu'à la clôture (§6) — une seule, de la branche
  vers `main`, **prête** (brouillon seulement sur demande de Benjamin), avec ou
  sans `review-required` selon ce que ce dépôt-là en fait. Pas de PR d'étape.
  Chaque PR est un run de CI, et le quota GitHub Actions est la contrainte qui a
  fixé la règle « une branche par plan » (§2).
- Il ne **merge jamais** lui-même, même sur demande : c'est la CI qui merge la
  PR (§6). Il suit la CI, **vérifie** le merge sur pièce, puis pose `execute`.
- Il ne pose jamais `execute` sur un travail qui n'est pas sur `main` — ni ne
  laisse `a merger` sur un travail qui y est déjà (§6).
- Il ne s'arrête pas entre deux étapes pour demander l'autorisation de continuer
  (§3).
- Il ne résout pas les fils de commentaires.
- Ses fichiers de référence, à côté de ce `SKILL.md`, se lisent à l'endroit où
  le déroulé les cite : `ouverture.md` (§2), `etapes.md` (§3), `journal.md`
  (§4), `cloture.md` (§6) ; le plan maître se lit dans
  `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`.
