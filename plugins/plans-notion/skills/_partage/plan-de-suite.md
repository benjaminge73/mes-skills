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

**La suite se montre dans la session avant de s'écrire dans la page.** Une section
`La suite`, un reste de l'`État final` ou de la `Remontée sur main` n'est jamais
l'endroit où Benjamin découvre un reste : il l'a déjà vu dans la session, sous forme
de question ou de ligne du compte rendu, et la page ne garde que le résultat du tri.
Et la session ne l'attend pas : un reste connu en cours d'exécution (étape en échec ou
sautée, chantier mis de côté) est dit dans son message courant, pas gardé pour la
clôture. Une suite qui n'a atterri que dans la page d'un plan déjà exécuté est une
suite que personne n'a vue : elle se remonte dans la session, au tour où on la
constate (`AskUserQuestion`, ou le compte rendu), puis la page est corrigée.

## Le tri, avant le passage à `a merger`

Il se joue au début de la clôture (`cloture.md`, « Avant le point 1 »), avant la
suite complète finale, l'ouverture de la PR et l'écriture du Récap : le Récap
dit ensuite ce que le tri a décidé, il ne le décide pas. Il se rejoue aussi quand
un reste apparaît plus tard sur un plan `a merger` ou `execute` (à la remontée sur
`main`, ou en reprenant la page). Sur un plan déjà `a merger`, « le faire maintenant » ne vaut que
tant que sa PR est ouverte (les étapes `D<n>` partent sur sa branche) ; sur un plan
`execute`, il ne reste que le plan de suite ou l'abandon. Pour **chaque** ligne de reste à faire, la
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
     irréversible : mesure de `decouvertes.md` § 1) → **la suite proposée se montre
     dans la session et se décide là** : une question (`AskUserQuestion`, dans le
     même appel que les autres), qui nomme chaque reste et propose :
     - **créer le plan de suite** (ci-dessous), qui porte **tout** le travail
       restant — la reco, et la réponse par défaut ;
     - **le faire maintenant, dans cette session** : les restes deviennent des
       étapes `D<n>` (`decouvertes.md` § 2), jouées, relues et prouvées comme toute
       étape, et le plan reste `en cours` jusqu'à leur fin. Cette option n'est
       offerte que pour du travail **réversible et hors sécurité** ; un reste qui
       revient sur une décision tranchée, coûte, touche la sécurité ou est
       irréversible n'a que le plan de suite (il repasse par la validation de
       Benjamin) ou l'abandon ;
     - **l'écarter** : cité avec les mots de Benjamin à l'`État final`, jamais
       décidé à sa place.
     On ne coupe pas le reste en « le petit ici, le gros là-bas » : ce serait deux
     endroits à relire. Sans réponse (session sans humain, `decouvertes.md` § 3, ou
     « plus tard »), c'est le plan de suite : la question n'attend pas, le travail
     est porté quelque part de visible.
   Le seuil d'une étape est un total, pas une mesure par élément comme pour les
   découvertes en route (`decouvertes.md` § 2, sans plafond) : à la clôture, empiler
   des `D<n>` de sa propre initiative ferait ne jamais clore. Seul l'accord de
   Benjamin, donné dans la session, lève ce seuil.
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
réponse. **Quand le tri ci-dessus y mène — Benjamin a choisi de le créer, ou n'a
pas répondu — et seulement alors, créer un plan de suite.** L'autonomie ne se paie qu'à condition que ce qui a été mis de côté
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
étape `D<n>`, une question posée, un événement attendu, ou que Benjamin a choisi de
le faire dans la session ou de l'écarter. Une page vide de contenu
utile encombre la base et fait douter du statut de celle qui la précède.
