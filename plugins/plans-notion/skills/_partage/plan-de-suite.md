# Le plan de suite, quand tout n'est pas passé

Fichier référencé par `executer-plan-notion` (§7), à lire au moment de la
clôture dès qu'il reste quelque chose que l'exécution autonome a mis de côté.

Une exécution autonome se termine parfois avec des étapes en échec, des étapes
sautées faute de dépendance, ou une décision qui attend Benjamin. **Dans ce cas —
et dans ce cas seulement — créer un plan de suite.** C'est ce qui remplace les
questions qu'on ne lui a pas posées en cours de route : l'autonomie ne se paie
qu'à condition que ce qui a été mis de côté atterrisse quelque part de visible.

- **Même titre que le plan courant, suffixé du numéro suivant** :
  `[Plan] Projet - Titre thématique #2`, puis `#3`. Le plan sans suffixe compte
  pour `#1`. Jamais de date dans le titre.
- Page créée dans la base **Plans Claude**, mêmes propriétés que l'originale
  (`Projet`, `Repo`, `Date`), `Statut` = `brouillon` : c'est un plan comme un
  autre, il repasse par la validation de Benjamin avant qu'on code dessus.
- **`Branche` se tranche, jamais ne se laisse vide** — règle des trois cas dans
  `plan-notion` §2 : recopiée si la branche du `#N` vit encore, neuve et écrite si
  elle est déjà partie sur `main`, remplacée et justifiée si elle a été
  abandonnée. C'est ce qui garantit que la suite du travail atterrit au même
  endroit que son début.
- Structure habituelle d'un plan (`plan-notion` §3), avec **en tête un chapitre
  `Reprise du plan #N-1`** qui porte :
  - ce qui a été **fait** dans le plan précédent, une ligne par étape ;
  - ce qui a été **laissé de côté**, et pourquoi — CI rouge dont le correctif
    était structurant, dépendance non satisfaite, arbitrage en attente ;
  - les **arbitrages demandés à Benjamin**, sous la forme habituelle des questions
    ouvertes : H3 `🧭 Q1 — …`, encadré orange, cases **non cochées**, une reco.
- Les étapes non traitées sont **reprises dans le chapitre `Exécution`** du
  nouveau plan, renumérotées à partir de 1 et corrigées de ce que l'exécution a
  appris. Les recopier telles quelles alors qu'on en sait plus long serait
  repartir avec le plan d'hier.
- **Lier les deux pages** : le plan précédent pointe le suivant dans son
  `État final`, le suivant pointe le précédent dans sa reprise.
- Le plan précédent **garde son statut de fin** — `a merger`, ou `execute` si sa
  branche est partie sur `main`. Il a été exécuté jusqu'où il pouvait l'être : ce
  n'est pas un échec à cacher, c'est un périmètre qui a bougé.

Ne pas créer de plan de suite quand tout est passé. Une page vide de contenu utile
encombre la base et fait douter du statut de celle qui la précède.
