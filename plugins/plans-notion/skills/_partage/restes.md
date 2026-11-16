# La base « Restes » : ce que la clôture laisse dormir

Fichier partagé, cité par `plan-notion` et `executer-plan-notion`. Il décrit la base
Notion (un outil de pages et de bases de données) où atterrit ce que le tri de fin de
plan ne peut pas régler tout de suite. Les noms ci-dessous sont exacts, accents et
apostrophes droites compris : le garde de clôture et le plan Hermes les lisent tels quels.

Sigles : **PR** (demande de fusion d'une branche dans `main`), **CI** (tests et
déploiement automatiques sur GitHub), **Hal** (l'agent Hermes qui reprend les restes
datés), **Hermes** (la couche d'agents du poste, sur le VPS, serveur privé virtuel).

## À quoi elle sert

Un reste à faire écrit dans la page d'un plan terminé ne revient à personne : il dort
(voir `plan-de-suite.md`). La base le recueille. **Un reste = une ligne.** Elle ne
remplace pas le tri : elle se branche dessus et recueille ce qu'il laisse dormir (Q7).

- Un geste, une vérification ou un suivi (événement attendu) devient une ligne.
- Une décision se pose d'abord dans la session, par le tri. Seule celle qui reste sans
  réponse devient une ligne typée `décision` (Q2, Q7).

## Où elle est

- Page « Restes », sous la page « Claude », à côté de « Plans Claude ».
- URL : https://app.notion.com/p/41ab8cc8aa1d8107aeeec751df2d8a73
- Source de données (l'identifiant qu'un appel API demande) :
  `collection://41ab8cc8-aa1d-81cf-b83c-000b76701db9`
- Chaque page projet porte une vue liée, filtrée sur `Repo` = `benjaminge73/<repo>` (Q9).

## Schéma

| Propriété | Type | Rôle |
|---|---|---|
| `Reste` | titre | Ce qui reste à faire, en une phrase. |
| `Repo` | texte | Forme `benjaminge73/<repo>`. Clé de tri par dépôt. |
| `Type` | select | `geste`, `vérification`, `décision`, `suivi`. |
| `Pour` | select | `Hal`, `Benjamin`. Qui doit agir. |
| `Plan d'origine` | relation vers « Plans Claude » | Le plan qui a laissé le reste. |
| `Repris par` | relation vers « Plans Claude » | Le plan qui l'a repris. Pas de relation inverse. |
| `Échéance` | date | Date butoir, si elle existe. |
| `État` | select | `ouvert`, `repris`, `fait`, `caduc`, `écarté`. Une ligne neuve s'écrit à `ouvert`. |
| `Condition` | texte | La date ou le critère qui déclenche le reste. |
| `Contexte` | texte | Ce qu'il faut savoir pour le reprendre. |
| `Journal` | texte | Historique de la ligne, en texte libre. |

Valeurs d'`État` : `ouvert` = à traiter ; `repris` = pris par un plan ; `fait` = terminé ;
`caduc` = plus d'objet ; `écarté` = retiré par Benjamin.

## Vues

- « Ouverts » : `État` = `ouvert`, groupée par `Repo`.
- « Pour Hal » : `Pour` = `Hal` et `État` = `ouvert`.
- « Pour Benjamin » : `Pour` = `Benjamin` et `État` = `ouvert`.
- « Tous » : sans filtre.

## Règles

1. **Une ligne par reste.** La page du plan ne recopie pas son texte : elle cite la ligne
   par son lien (Q11).
2. **Le tri d'abord.** Chaque reste passe par le tri de `plan-de-suite.md`. La ligne
   arrive après, pas à sa place (Q7).
3. **Décision sans réponse** : ligne `Type` = `décision`. Le plan de suite ne sert que si
   du travail reste aussi (Q10).
4. **Événement attendu** : la ligne fait foi. `La suite` et le Récap la citent (Q11).
5. **Confrontation avant versement.** Chaque reste est comparé à l'état réel avant d'être
   écrit. Un reste caduc n'est pas versé : il est listé à Benjamin dans la session (Q13).
6. **Rattrapage.** Les restes des 10 derniers plans clos sont versés (Q6).
7. **Ouverture d'un plan.** Il reprend toutes les lignes `ouvert` de son dépôt. Une
   décision devient une question ouverte ; le reste va dans un chapitre en tête de la page.
   Benjamin retire ce qu'il ne veut pas reprendre (Q3).
8. **Qui agit.** À la clôture, le pilote propose `Pour`. Hal confirme, ou renvoie la ligne
   à Benjamin (Q5). Hal peut agir lui-même, déployer compris ; à la fin d'un plan, il
   ouvre une PR que la CI merge si elle est verte (décision de Benjamin, 2026-11-16).
9. **Champ obligatoire.** `Condition` est le seul champ obligatoire d'une ligne `Pour` =
   `Hal`. Si le pilote ne la connaît pas, elle devient une question à Benjamin avant le
   passage du plan à `a merger` (Q8).
10. **Rappel.** Aucun rappel côté mes-skills. Un reste daté se rappelle par Hal, dans le
    plan Hermes. D'ici là, rien ne rappelle un reste daté (Q4).
11. **Garde.** Un script compare le miroir local de la page et l'export des lignes du
    plan. Code 1 : le passage à `a merger` est refusé (Q12).
12. **Schéma figé.** Le plan Hermes s'appuie sur ce schéma, tel qu'écrit ici, une fois ce
    plan passé à `valide` (Q14).
