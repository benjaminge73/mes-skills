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
2. **Passer le plan au filtre de l'enquête.** Quinze vérifications, et elles se
   font page ouverte, pas de mémoire :
   1. plus aucune question ouverte dont la réponse était vérifiable et n'a pas
      été vérifiée ;
   2. plus aucune option qui reporte une mesure faisable aujourd'hui ;
   3. chaque chemin de « Fichiers touchés » qui existe vraiment, ou qui est
      annoncé comme une création ;
   4. le chapitre `Maquette` tient : aucune étape dont l'`Impact fonctionnel`
      dit autre chose que « Rien » sans maquette qui la montre **dans la
      version courante des étapes**, légende avec son `file_upload_id` — ou
      une dispense dont la raison est l'une des deux recevables (§3) ;
   5. une relecture de **cohérence interne** : les renvois entre sections
      pointent juste, l'ordre des étapes est le bon, et aucune prémisse ne
      contredit une réponse tranchée plus loin dans la page ;
   6. chaque « Preuve de fin » a été **jouée**, ou est **réfutable**, avant de
      passer `valide` — une preuve qu'on ne peut ni jouer ni contredire ne
      prouve rien à l'exécution ;
   7. aucun chiffre n'est repris d'un plan `#N-1` **sans remesure** ;
   8. toute question chiffrée porte, à côté de sa réponse, la commande jouée
      et son résultat — sinon rien ne permet de la remesurer au point 7
      ci-dessus ;
   9. la répétition à blanc a été **jouée et reportée** dans `Contraintes
      techniques vérifiées`, sous « État de départ » (« La répétition à blanc et
      le POC de décision ») ;
   10. une ligne « Existant cherché : … / trouvé : … / fait maison parce que … »
      **par artefact** non propre au projet que les étapes fabriquent, présente
      dans `Contraintes techniques vérifiées` (gisement 6, « L'extérieur »).
   11. une **carte de voisinage** présente dans `Contraintes techniques
       vérifiées` (geste du pilote, `enquete.md`), ou une dispense écrite
       `Pas de carte — <raison>` dont la raison est l'une des trois recevables :
       dépôt de contenu sans code touché, serveur MCP absent, dépôt non indexé.
   12. le miroir de la page (fetch) rend 0 à
       `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-preuves.py" <miroir> --depot <dépôt> --transcripts` :
       chaque écart se corrige, ou se justifie par une dispense motivée, avant
       `valide` ; le format de la preuve est dans `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`.
   13. chaque cron créé ou modifié (job Hermes, unité systemd, workflow `schedule:`, autre planificateur), hook ou workflow sur événement, a son
       étape `C<n>`, ou la page dit « Aucun cron touché » : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md`.
   14. chaque étape qui touche un fichier cité par la doc du dépôt porte sa ligne
       « Docs relues » (`chapitres-questions-execution.md`, « Fichiers touchés » compris).
   15. chaque ligne `ouvert` des dépôts du plan est citée dans `Restes repris` : reprise si elle
       est du sujet, « laissée ouverte » avec sa raison sinon. Contrôle bloquant (Q8) :
       `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/restes-repris.py" <miroir> --lignes <export>`
       rend 0 (`_partage/restes.md`, règle 7).

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
