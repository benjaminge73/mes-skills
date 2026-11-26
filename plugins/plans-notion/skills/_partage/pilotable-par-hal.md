# Une case cochée est une décision, et la session reste pilotable par Hal

Fichier **partagé**, lu par `executer-plan-notion` (`SKILL.md`, « La porte d'entrée » ;
`ouverture.md`) à partir du statut `valide` et pour tous les statuts suivants (`pret`,
`en cours`, `a merger`). Né d'un incident de Benjamin (2026-11-18) : sur un plan `valide`, il avait
coché une case qui n'était pas la reco ; la session chargée de l'exécution lui a reposé la
question (`AskUserQuestion`), et Hal n'aurait pas pu la débloquer en répondant.

## 1. Une case cochée vaut décision

Une case cochée par Benjamin dans une question du plan **est** sa réponse, **même si ce n'est pas
la recommandation**. La session :

- l'applique (remise à jour du chapitre `Exécution`, `remise-a-jour-execution.md`) et l'écrit, datée :
  `_maj <date> — Qn tranchée par Benjamin : <réponse>, contre la reco._` ;
- **ne redemande pas** de confirmation, ni dans la session ni ailleurs ;
- ne s'arrête que sur ce que `SKILL.md` prévoit déjà (sécurité majeure, financier ou irréversible
  **non validé** : le choix coché que Benjamin a fait en connaissance de cause l'est, validé) ou sur une
  **contradiction** réelle entre deux réponses cochées, qu'elle dit en une ligne.

Une réponse écrite après `Autre / complément →` vaut de même. Seule une question **restée sans
réponse** reçoit la reco par défaut (`remise-a-jour-execution.md`, « questions restées orange »).

## 2. Pas de question qui bloque la session

À partir de `valide`, une question à Benjamin **ne passe plus par `AskUserQuestion`** : cet outil
bloque l'écran de la session et rien d'extérieur (Hal, un message programmé) ne peut y répondre.
La session :

1. **pose la question en texte**, recommandation en premier, avec ce que la réponse change et le
   défaut qui s'appliquera à défaut de réponse ;
2. **la recopie dans la page du plan**, section `## Questions en attente`, pour que Hal et Benjamin la
   voient sans ouvrir la session ;
3. note l'attente (`plan-en-cours.py attendre --raison "<la décision attendue>"`), **finit son tour**
   et continue d'ici là sur tout ce qui n'en dépend pas ;
4. à la réponse (message dans la session, ou ligne dans la page, ou `## Courrier de Hal`), `reprendre`
   et applique, en barrant la question dans la page.

Le texte vaut pour toutes les questions des fichiers du skill qui nomment `AskUserQuestion`
(découvertes, trou e2e de la clôture, restes à faire, trois tours rouges) : à partir de `valide`,
lire « question en texte » à la place.

## 3. Ce que Hal peut surveiller et faire

Hal doit pouvoir **trouver** la session et **lui répondre** dès `valide`, pas seulement à `en cours` :

- la session pose `Session` et `Machine` sur la page **au début de la préparation** (`ouverture.md`,
  « La fiche du plan »), pas seulement à `en cours` ;
- Hal lit l'état dans la page (`Statut`, journal, `## Questions en attente`) et la fiche locale, et
  répond **dans la page**, section `## Courrier de Hal`, ou par un message à la session (identifiant de
  la propriété `Session`) ; la sonnette réveille la session, qui lit le courrier avant de reprendre
  (`ouverture.md`).
- Hal répond ce que `demander-a-hal.md` §4 lui permet : un geste réversible, une réponse que la
  mémoire de Benjamin tranche. Une décision que Benjamin n'a pas prise reste à Benjamin : Hal
  la lui remonte, il ne la devine pas.
- Une étape **déjà validée** dans le plan (case cochée, plafond écrit) et confiée à Hal ne se met pas
  en attente d'un « go » : elle se transmet avec `--valide` et `--plafond` (`demander-a-hal.md` § 2 bis),
  et Hal vérifie la validation dans la page. Un dépassement reste à Benjamin.
