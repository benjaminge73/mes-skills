> Détail de la section « 8. Passer la main à l'exécution » de `SKILL.md` (skill plan-notion), sorti du skill pour le ramener sous son budget de taille. Lire ce fichier quand Benjamin valide le plan. Dans le texte qui suit, « ce fichier » désigne `SKILL.md`.

Concevoir et réaliser sont deux postures opposées — l'une n'écrit rien, l'autre
n'écrit que du code — et elles vivent dans deux skills séparés. Ce fichier
s'arrête au moment où le plan devient exécutable.

Quand Benjamin valide le plan :

1. **D'abord répercuter ses dernières réponses dans le chapitre `Exécution`** —
   cases cochées, textes libres après `Autre / complément →`, commentaires de la
   passe — corrections datées (§3). Un plan passe à `valide` avec un chapitre
   `Exécution` juste, ou il n'y passe pas : c'est ce chapitre-là, et pas les
   réponses éparpillées dans la page, qui part dans les briefs des sous-agents
   d'exécution.
2. **Passer le plan à la liste de relecture commune.** Quinze vérifications de
   l'enquête, quatre points de Hal et deux points d'Anthropic, en vingt et une
   cases, chacune avec sa preuve, page ouverte, pas de mémoire :
   `${CLAUDE_PLUGIN_ROOT}/skills/_partage/listes/relecture-plan.md`. Sa copie
   cochée est celle que la relecture de Hal a reçue avant `en revue`
   (`relecture-par-hal.md` § 3) : ici, on la reprend sur la page fraîche et on
   recoche ce qui tient encore. Une case non tenue se corrige avant `valide`.

   Ce filtre vient de l'enquête sur les plans passés ; il coûte quelques minutes ici et évite
   la découverte en pleine exécution, qui coûte une étape. Mesures : `docs/retex/plan-notion.md`.
3. Passer `Statut` à `valide`.
4. Le dire en une ligne, et **invoquer `executer-plan-notion`** si l'implémentation
   enchaîne dans la foulée. Un skill n'en charge pas un autre tout seul : sans
   invocation explicite, ses règles ne s'appliquent pas.
5. Ne pas commencer à coder ici « en attendant ». La règle 2 tient jusqu'au bout.

Le plus souvent, ce n'est pas moi qui valide : **Benjamin répond dans la page,
passe `Statut` à `valide` lui-même et invoque `executer-plan-notion` directement**,
sans repasser par ici, et ce skill n'a jamais vu ses réponses. C'est pourquoi
`executer-plan-notion` refait cette mise à jour à son entrée (§2 de ce skill-là) : les deux
passages font le même travail, exprès. On ne sait pas d'avance lequel sera sauté, et un
chapitre `Exécution` en retard d'un tour produit un travail qui répond à la version d'avant.

Ce que `executer-plan-notion` prend en charge, donc inutile de le détailler ici : la découpe
en sous-agents, le `Journal d'exécution`, la branche du plan (sa PR unique s'ouvre à la clôture),
le déroulé en autonomie, le statut de fin (`a merger`, puis `execute` une fois sur `main`), et le
plan de suite `#N+1` s'il reste des arbitrages. Reste au plan le **contenu** du chapitre
`Exécution` : le quoi, pas le comment de la séance de code.
