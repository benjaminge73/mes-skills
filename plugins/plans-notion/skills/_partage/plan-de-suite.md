# Le reste à faire d'un plan terminé, et le plan de suite

Fichier référencé par `executer-plan-notion` (§6 et §7), à lire à la clôture de
**tout** plan, et dès qu'un reste à faire apparaît sur un plan déjà `a merger` ou
`execute`.

**Benjamin ne relit pas un plan terminé.** Un reste à faire écrit dans la page d'un
plan clos (journal, `État final`, `La suite`) n'est lu par personne : il dort là
jusqu'à ce qu'on le redécouvre. Chaque ligne de reste à faire atterrit donc là
où il la verra : **une question posée dans la session, ou un plan**. Jamais une
phrase seule dans la page du plan terminé ; seul ce qui attend un événement y dort,
et le Récap le répète.

## Le tri, avant le passage à `a merger`

Il se joue au début de la clôture (`cloture.md`, « Avant le point 1 »), avant la
suite complète finale, l'ouverture de la PR et l'écriture du Récap : le Récap
dit ensuite ce que le tri a décidé, il ne le décide pas. Il se rejoue aussi quand
un reste apparaît plus tard sur un plan `a merger` ou `execute` (à la remontée sur
`main`, ou en reprenant la page). Pour **chaque** ligne de reste à faire, la
première réponse qui s'applique décide :

1. **Elle demande une décision ou une réponse de Benjamin** → la question lui est
   posée **dans la session**, avec l'outil `AskUserQuestion` (recommandation en
   premier ; sans l'outil, en texte), avant de passer le plan à `a merger`.
   Plusieurs questions partent en un seul appel. La réponse s'applique dans le
   tour : si elle laisse du travail, ce travail reprend le tri au 2. La réponse
   et ce qu'elle a changé se notent à l'`État final`.
   - **Pas de réponse** — session sans humain (`decouvertes.md` § 3), ou Benjamin
     qui répond « plus tard » ou ne répond pas : la question n'est pas laissée dans
     le plan terminé, elle part en question ouverte (🧭, cases non cochées, une
     reco) dans un plan de suite. Les restes dont la réponse gèle le travail
     (sécurité, irréversible, `decouvertes.md` § 3) y vont aussi.
2. **C'est du travail qui reste** (une étape en échec ou sautée, un chantier mis de
   côté, une correction repérée trop tard) → le seuil est **plus d'une étape au
   total**, tout ce qui reste étant compté ensemble :
   - **une étape au plus**, réversible et hors sécurité → étape `D<n>`
     (`decouvertes.md` § 2), faite avant la clôture : le plan reste `en cours`
     jusque-là, et la suite complète finale la couvre ;
   - **plus d'une étape**, ou un élément qui ne tient pas dans une étape (il
     revient sur une décision tranchée, coûte, touche la sécurité, est
     irréversible : mesure de `decouvertes.md` § 1) → **un plan de suite**
     (ci-dessous) qui porte **tout** le travail restant. On ne coupe pas le reste en
     « le petit ici, le gros là-bas » : ce serait deux endroits à relire.
   Le seuil est un total, pas une mesure par élément comme pour les découvertes en
   route (`decouvertes.md` § 2, sans plafond) : à la clôture, empiler des `D<n>`
   ferait ne jamais clore.
3. **Il attend un événement** (une mesure à N jours, un merge, une version
   publiée) → il reste dans `La suite` du plan, avec son déclencheur et son
   propriétaire, **et** il est repris dans la rubrique ⏭️ du Récap (que Benjamin
   lit, lui). C'est le seul reste qui dort dans la page terminée.

Chaque ligne de reste à faire de l'`État final` nomme son propriétaire : la
question posée (avec la réponse), le plan de suite (avec son lien), l'étape `D<n>`
faite, ou l'événement attendu. Une ligne sans propriétaire se règle avant `a merger`.

## Le plan de suite

Une exécution se termine parfois avec du travail restant : des étapes en échec, des
étapes sautées faute de dépendance, un chantier mis de côté, une question sans
réponse. **Quand le tri ci-dessus y mène — et seulement alors — créer un plan de
suite.** L'autonomie ne se paie qu'à condition que ce qui a été mis de côté
atterrisse quelque part de visible.

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
  - les **arbitrages restés sans réponse** (ceux que Benjamin a tranchés dans la
    session n'y sont pas), sous la forme habituelle des questions
    ouvertes : H3 `🧭 Q1 — …`, encadré orange, cases **non cochées**, une reco.
- Les étapes non traitées sont **reprises dans le chapitre `Exécution`** du
  nouveau plan, renumérotées à partir de 1 et corrigées de ce que l'exécution a
  appris. Les recopier telles quelles alors qu'on en sait plus long serait
  repartir avec le plan d'hier.
- **Lier les deux pages** : le plan précédent pointe le suivant dans son
  `État final`, le suivant pointe le précédent dans sa reprise.
- Le plan précédent **garde son statut de fin** — `a merger` tant que son code
  n'est pas sur `main`, `execute` une fois qu'il y est. Sa PR de clôture a été
  ouverte par la clôture elle-même (`remontee-sur-main.md`) : le plan de suite
  la cite telle quelle, il ne la rouvre pas. Il a été exécuté jusqu'où il
  pouvait l'être : ce n'est pas un échec à cacher, c'est un périmètre qui a
  bougé.
- **Plan couvert par un plan maître** : le plan de suite le rejoint et le statut du
  maître est recalculé (`plan-notion/plan-maitre.md`) ; la ligne du plan terminé
  dans « Reste à faire » du `Récap du lot` cite le plan de suite avec son lien.
- Le lien du plan de suite va aussi dans la rubrique ⏭️ du Récap et dans le compte
  rendu : c'est là que Benjamin le trouve.

Ne pas créer de plan de suite quand rien ne reste, ou que le reste tient dans une
étape `D<n>`, une question posée, ou un événement attendu. Une page vide de contenu
utile encombre la base et fait douter du statut de celle qui la précède.
