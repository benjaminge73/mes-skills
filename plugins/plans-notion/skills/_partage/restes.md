# La base « Restes » : ce que la clôture laisse dormir

Fichier partagé, cité par `plan-notion` et `executer-plan-notion`. Il décrit la base
Notion (un outil de pages et de bases de données) où atterrit ce que le tri de fin de
plan ne peut pas régler tout de suite. Les noms ci-dessous sont exacts, accents et
apostrophes droites compris : le garde de clôture et le plan Hermes les lisent tels quels.

Sommaire : à quoi elle sert · où elle est · schéma · vues · règles.

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
- Elle se retrouve par la recherche Notion (« Restes ») ou par sa source de données ci-dessous.
- Source de données (l'identifiant qu'un appel API demande) :
  `collection://41ab8cc8-aa1d-81cf-b83c-000b76701db9`
- Pour la commande `composio` (`NOTION_QUERY_DATABASE`), l'identifiant à passer est le `database_id`
  `41ab8cc8-aa1d-8107-aeee-c751df2d8a73` : le `collection://` ci-dessus y rend « object_not_found »
  (relevé du 2026-11-16).
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
| `État` | select | `ouvert`, `repris`, `fait`, `caduc`, `écarté`, `en cours` (sens non documenté). Une ligne neuve s'écrit à `ouvert`. |
| `Condition` | texte | La date ou le critère qui déclenche le reste. |
| `Contexte` | texte | Ce qu'il faut savoir pour le reprendre. |
| `Journal` | texte | Historique de la ligne, en texte libre. |

Valeurs d'`État` : `ouvert` = à traiter ; `repris` = pris par un plan ; `fait` = terminé ;
`caduc` = plus d'objet ; `écarté` = retiré par Benjamin. `en cours` est présente dans la base,
sens non documenté : aucun script ne l'écrit.

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
7. **Ouverture d'un plan.** Le chapitre `Restes repris`, en tête de page, cite chaque ligne
   `ouvert` des dépôts du plan (propriété `Repo` ; un plan à plusieurs dépôts les liste tous).
   Un plan reprend **par défaut** chaque ligne. Une ligne reprise devient une étape (geste ou
   vérification), une question ouverte si c'est une décision, ou une puce de `La suite`
   avec son déclencheur (suivi). Les décisions d'un même thème partagent une question (une
   option par ligne, chaque ligne en lien) ; la clôture passe la ligne `fait` avec la réponse
   à son `Journal` (sans réponse, la reco appliquée par défaut, dite telle), ou la remet
   `ouvert` si Benjamin a contesté la reco sans trancher.
   Une ligne n'est laissée ouverte que pour une des raisons suivantes,
   citée à côté de la ligne par sa lettre, sous la forme `laissée ouverte (<lettre>) : <raison>` :
   - **(a)** condition ou échéance pas encore atteinte. Confrontée à l'état réel (règle 5), elle
     doit être réellement non atteinte : une `Condition` renseignée ne suffit pas ;
   - **(b)** geste qui exige les comptes ou la main de Benjamin (connexion, paiement, appareil) ;
   - **(c)** plus gros qu'une étape moyenne, ou travail dans un autre dépôt ;
   - **(d)** contredit le sujet du plan : le faire défairait ce que le plan construit ;
   - **(e)** déjà portée par un autre plan ouvert, nommé et lié.

   Exemple : `- [titre en lien] — laissée ouverte (a) : échéance <date> non atteinte.`

   Un plan reprend **au plus 10 lignes**, dont **au plus 5 questions** venues des restes, les
   plus anciennes d'abord. Le surplus se laisse en **(p)** « au-delà du plafond » et reste
   ouvert pour un plan suivant du même dépôt. Sous 10 reprises, `(p)` ne vaut que pour une
   ligne `décision` (la sixième question). Benjamin retire une reprise : la ligne passe
   alors « laissée ouverte » (Q3), avec la lettre de son motif ; à défaut
   `(a) : retirée par Benjamin, attend sa demande`.
8. **Qui agit.** À la clôture, le pilote propose `Pour`. Hal confirme, ou renvoie la ligne
   à Benjamin (Q5). Hal peut agir lui-même, déployer compris ; à la fin d'un plan, il
   ouvre une PR que la CI merge si elle est verte (décision de Benjamin, 2026-11-16).
9. **Champ obligatoire.** `Condition` est le seul champ obligatoire d'une ligne `Pour` =
   `Hal`. Si le pilote ne la connaît pas, elle devient une question à Benjamin avant le
   passage du plan à `a merger` (Q8).
10. **Rappel.** Aucun rappel côté mes-skills. Un reste daté se rappelle par Hal, dans le
    plan Hermes. D'ici là, rien ne rappelle un reste daté (Q4).
11. **Garde.** Deux scripts, code 1 pour chacun. `restes-sans-ligne.py` compare le miroir
    local de la page et l'export des lignes du plan : code 1 refuse le passage à `a merger`
    (Q12). `restes-repris.py` vérifie le chapitre `Restes repris` contre les lignes `ouvert`
    des dépôts du plan : chaque ligne doit être reprise, ou laissée ouverte avec une lettre de
    la règle 7 et une raison non vide ; il rend aussi 1 au-delà de 10 reprises, et pour un (p)
    posé sous ce plafond sur une ligne qui n'est pas une `décision` ; les reprises se comptent
    sur les puces du chapitre. Il ne compte pas les
    questions (une question regroupe plusieurs lignes) : le plafond de 5 se relit. Code 1 bloque le passage à `en revue` (Q8). Les deux sont dans
    `_partage/scripts/`.
12. **Schéma figé.** Le plan Hermes s'appuie sur ce schéma, tel qu'écrit ici, une fois ce
    plan passé à `valide` (Q14).
