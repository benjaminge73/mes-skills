# Liste de relecture d'un plan

Qui la joue : la session, sur la page du plan, avant `en revue` et avant `valide` ; sur un plan natif, avant `ExitPlanMode` (`avant-le-plan.md`). Le fichier se garde non coché. La session recopie la liste, case par case, et écrit sa copie : une case tenue se coche avec `— preuve : …` (la commande jouée et sa sortie, ou la lecture qui la tranche) ; une case non tenue ou non jouée se laisse décochée avec `— non cochée : <raison>`. Une case non applicable se coche `— sans objet — <raison>`.

Les cases 16 à 19 sont celles de Hal (`relecture-par-hal.md` § 9) : la copie jointe à `relire` les laisse décochées, la session les coche d'après l'avis rendu.

Plan natif : pas de page, pas de miroir, pas de Hal. Les cases 4, 9, 15 et 16 à 19 se cochent `sans objet — plan natif` ; la 12 se joue avec `--format natif`.

## Les quinze vérifications

- [ ] 1. Aucune question ouverte dont la réponse était vérifiable n'est restée non vérifiée. — preuve : la commande ou la lecture qui la tranche, ou `non vérifiable — <raison>`.
- [ ] 2. Aucune option ne reporte une mesure faisable aujourd'hui. — preuve : la mesure jouée (commande, résultat), ou l'option retirée.
- [ ] 3. Chaque chemin de « Fichiers touchés » existe, ou est annoncé comme création. — preuve : `ls` du chemin, ou la mention « création » dans l'étape.
- [ ] 4. Le chapitre `Maquette` tient : chaque « Impact fonctionnel » autre que « Rien » est montré par une maquette de la version courante des étapes, ou dispensé par `Pas de maquette — <raison>` recevable (`chapitres-cadrage.md`). — preuve : l'identifiant de la maquette et la date des étapes, ou la dispense.
- [ ] 5. Cohérence interne : renvois entre sections justes, ordre des étapes bon, aucune prémisse contredite par une réponse tranchée plus loin. — preuve : les renvois relus, avec la section d'où part chacun.
- [ ] 6. Chaque « Preuve de fin » a été jouée, ou est réfutable. — preuve : la commande et sa sortie, ou la contre-épreuve qui la réfuterait.
- [ ] 7. Aucun chiffre n'est repris d'un plan `#N-1` sans remesure. — preuve : la commande de remesure et son résultat, ou `aucun chiffre repris`.
- [ ] 8. Toute question chiffrée porte, à côté de sa réponse, la commande jouée et son résultat. — preuve : la commande et sa sortie, sous la réponse.
- [ ] 9. La répétition à blanc est jouée et reportée dans `Contraintes techniques vérifiées`, sous « État de départ ». — preuve : l'intertitre « La répétition à blanc et le POC de décision » et sa date.
- [ ] 10. Une ligne « Existant cherché : … / trouvé : … / fait maison parce que … » existe par artefact non propre au projet. — preuve : une ligne par artefact, ou `aucun artefact non propre`.
- [ ] 11. Une carte de voisinage figure dans `Contraintes techniques vérifiées`, ou `Pas de carte — <raison>` recevable (dépôt de contenu, serveur MCP absent, dépôt non indexé). — preuve : la carte datée, ou la dispense.
- [ ] 12. `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/verifier-preuves.py" <miroir> --depot <dépôt> --transcripts` rend 0. — preuve : la commande et son code de sortie 0 (format de la preuve : `poc.md`), ou chaque écart corrigé ou dispensé.
- [ ] 13. Chaque cron, hook ou workflow sur événement touché a son étape `C<n>`, ou la page dit `Aucun cron touché` (`cron-a-la-main.md`). — preuve : l'étape `C<n>`, ou la phrase.
- [ ] 14. Chaque étape qui touche un fichier cité par la doc du dépôt porte sa ligne « Docs relues », « Fichiers touchés » compris. — preuve : la ligne, avec le fichier de doc lu (`chapitres-questions-execution.md`).
- [ ] 15. Chaque ligne `ouvert` des dépôts du plan est citée dans `Restes repris` : reprise, ou « laissée ouverte » avec sa raison (`restes.md`, règle 7). — contrôle bloquant (Q8) — preuve : `python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/restes-repris.py" <miroir> --lignes <export>` rend 0.

## Les quatre points de Hal

- [ ] 16. Les préférences et décisions de Benjamin (`fact_store`) ne contredisent pas le plan. — preuve : la réserve de Hal qui cite son fait, ou la ligne « Ce que j'ai vérifié » qui le couvre.
- [ ] 17. Aucun autre plan ouvert du même dépôt ne touche les mêmes fichiers. — preuve : le bloc « Plans ouverts des mêmes dépôts » croisé avec « Fichiers touchés », ou `aucun conflit`.
- [ ] 18. Les faits du plan sur le VPS (cron, unité, fichier) sont vérifiés en lecture seule. — preuve : la commande et sa sortie, ou le fait listé dans « À vérifier par la session ».
- [ ] 19. Le plan ne refait pas un piège déjà payé (fait ou plan antérieur). — preuve : le fait ou le plan cité, et la ligne du plan qui l'évite.

## Les deux points d'Anthropic

- [ ] 20. Chaque étape a un contrôle qui rend réussi ou échoué. — preuve : sa « Preuve de fin », qui rend 0 ou non 0.
- [ ] 21. Une seule chose par étape. — preuve : le titre de l'étape nomme une seule action ; deux actions reliées par « et » : l'étape se découpe.
