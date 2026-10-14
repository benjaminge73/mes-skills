# Compte rendu d'un plan natif

Fichier partagé, lu par `plans-notion:deleguer-a-haiku` : au compte rendu final, et à
l'invariant « Diagnostic, pas correctif ». Une session lancée par Hermes lit ce texte
tel quel : les rubriques ci-dessous restent dans le texte, avec leur nom exact.

La dernière réponse de la session, courte : pour chaque étape, son état, sa commande de
preuve et le résultat rejoué ; le verdict du relecteur s'il a été appelé ; les écarts et
les questions ouvertes. Une consigne d'Hermes lit ce texte tel quel. Rien n'est écrit
dans Notion ni ailleurs.

Le texte contient trois rubriques, présentes même vides (« aucune » s'écrit aussi) :

- **Ajouts sans question** : les découvertes intégrées au plan sans demander, une par
  ligne (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md`, § 2).
- **Recos appliquées par défaut** : les recos appliquées sans réponse de Benjamin. La
  dépense (argent, quota externe) se signale en tête de cette rubrique.
- **Questions pour Benjamin** : les questions restées sans réponse, et tout ce qui touche
  la sécurité ou l'irréversible.

**Tri sans humain.** Une session lancée par Hermes n'a personne pour répondre. Le tri suit
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/decouvertes.md`, § 3 : la sécurité et l'irréversible
ne s'appliquent pas par défaut. Leurs étapes dépendantes sont gelées (les autres continuent)
et la question part dans « Questions pour Benjamin ». La dépense s'applique par défaut et se
signale en tête de « Recos appliquées par défaut ».

**Diagnostic, pas correctif.** Une preuve rouge ne se corrige jamais dans la session, pas
même par le pilote (la session qui conduit le plan). Il lit la sortie, dit ce qu'il
comprend, puis relance une étape `D<n>` (découverte, numérotée à part des étapes du plan)
déléguée à `plans-notion:executant`, avec un brief précis et sa liste fermée de fichiers.
L'appel ne porte pas de paramètre `model`, sauf pour la correction d'un cron qui échoue :
voir `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md`.
