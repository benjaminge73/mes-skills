# Rétex — 44 plans Notion (2026-09-08 → 2026-09-28) : chercher, prouver, paralléliser

Date : 2026-09-29

Ce document fait suite à `docs/retex-plans-2026-09.md` (le rétex du
2026-09-08, 77 plans). Il rassemble, pour qu'elle vive dans le dépôt et pas
seulement dans une page Notion, la synthèse d'un second dépouillement, fait
avec une question différente : pas seulement « qu'est-ce qui a surpris à
l'exécution », mais **« quel remède le moins cher l'aurait attrapé avant que
le plan soit validé, et un essai grandeur nature (un POC) l'aurait-il aussi
attrapé ? »**. Il est pensé pour être lu seul.

Un mot de vocabulaire, parce que tout le document tourne autour. Un **POC**
(*proof of concept*, preuve de faisabilité) est un petit essai jetable, joué
avant de s'engager, qui répond à une seule question mesurable — « cette API
accepte-t-elle vraiment cette option ? », « ces 8 URL répondent-elles ? ».
Il coûte quelques minutes et se distingue d'une lecture de code : il **exécute
quelque chose contre le réel**.

**Choix de publication** : ce document ne donne que des **agrégats**. Les
exemples cités sont anonymisés (aucun nom de lieu, de client, de projet
privé ou de compte) ; les journaux bruts restent dans la base de plans.

## Méthode

Le relevé du 2026-09-29 couvre les **44 plans** de la base de plans exécutés
entre le 2026-09-08 (date du rétex précédent) et le 2026-09-28. Leurs journaux
d'exécution ont été lus **en entier** par 5 sous-agents en parallèle, qui
suivaient une même consigne et un même gabarit de colonnes.

- **43 plans sur 44** portent au moins une surprise.
- **632 surprises** relevées au total. Les décomptes d'`État final` (la ligne
  « N découvertes, dont M trouvables » qui clôt un plan) sont **exclus** : on
  compte les surprises elles-mêmes, pas ce que le plan dit d'elles, pour ne
  pas rejouer les décomptes faux du rétex précédent.
- Pour chaque surprise, deux colonnes de **jugement** : le **remède le moins
  cher** qui l'aurait attrapée avant `valide`, et **si un POC l'aurait aussi
  attrapée** (oui, partiel, non).

⚠️ **Ces deux colonnes sont un jugement des sous-agents, pas une mesure.**
Ce que le rétex établit solidement, ce sont les décomptes (632, 315, 317…).
Ce qu'il estime, c'est la répartition par remède. Elle donne un ordre de
grandeur fiable, pas une précision au point de pourcentage.

⚠️ **Les 632 ne se comparent pas aux 215 du rétex précédent.** Là, on
comptait les *découvertes libellées* des seuls journaux qui portaient la
convention ; ici, on compte **toute** surprise, libellée ou non. Seul le
**ratio** « trouvable » parmi les surprises libellées est comparable d'un
relevé à l'autre.

## Chiffres clés

### Le ratio « trouvable » n'a pas bougé

**235 découvertes libellées « trouvable » sur 315 libellées : 74,6 %**,
contre **78,6 %** (169 sur 215) au rétex du 2026-09-08
(`docs/retex-plans-2026-09.md:31-32`). Quatre points d'écart : trop peu pour
dire que quelque chose a changé, d'autant que le libellé est lui-même un
jugement. Trois semaines de plans après le premier rétex, et environ **trois
surprises libellées sur quatre restent trouvables avant l'exécution** —
donc trouvées trop tard.

### La moitié des surprises n'a aucun libellé

**317 surprises sur 632 n'ont aucun libellé** (« trouvable » / « pas
trouvable »), soit la moitié. **13 plans sur 43** n'en portent pas un seul.
Le ratio ci-dessus se calcule donc **sur la moitié du réel** : les 315
surprises libellées. Si les 317 autres se répartissaient autrement, le vrai
ratio serait autre, et rien dans les journaux ne permet de le savoir. C'est
le constat qui motive le levier C plus bas : une mesure qu'on ne peut faire
que sur une moitié n'est pas une mesure de suivi.

### Le remède le moins cher

Pour les 632 surprises, ce qui les aurait attrapées avant `valide` au
moindre coût (jugement des sous-agents) :

| Remède le moins cher | Surprises | Part |
|---|---|---|
| Lire le code (fonction entière, appelants, modules voisins) | 269 | 43 % |
| Un POC (essai réel, jeté après) | 126 | 20 % |
| Compter sur les données réelles (corpus complet, chargeur réel) | 85 | 13 % |
| Aucun (surprise réellement imprévisible) | 57 | 9 % |
| Relire la page du plan elle-même | 47 | 7 % |
| Lire la documentation de l'outil | 26 | 4 % |
| Consulter un registre (outils, quotas, limites connues) | 22 | 3,5 % |
| **Total** | **632** | **100 %** |

Deux lectures. **Lire le code reste le premier remède** à lui seul (43 %) :
c'est ce que l'agent `enqueteur` renforcé au rétex précédent est censé
faire. Et **presque une surprise sur dix (9 %) n'avait aucun remède
disponible** : c'est le plancher incompressible, à ne pas chercher à
descendre.

### Un POC l'aurait aussi attrapée ?

**301 oui (48 %), 65 partiel, 266 non**. Avec les partiels : 366 sur 632,
soit **58 %**. Le POC couvre donc près d'une surprise sur deux (48 %), et
58 % en comptant les partiels, ce qui est plus que les 20 % où il est le
*remède le moins cher* : dans beaucoup de cas, le POC aurait attrapé ce
qu'une lecture attrapait aussi — mais **plus cher**.

## Angle × remède : où le POC est seul, où il ne sert pas

Chaque surprise porte aussi un **angle**, la famille de la cause
(`voisin` : ce qu'il y a juste à côté du code touché ; `donnees` : ce que
contiennent réellement les données ; `outil` : le comportement d'un outil ou
d'une API tiers ; `env` : droits, chemins, environnement d'exécution ;
`page` : ce que le plan dit déjà ; `quota` : limites et paliers de
facturation ; `existant` : ce qui existait déjà). Le croisement avec le
remède donne :

| Angle | Surprises | Remède dominant | Le POC est-il utile ? |
|---|---|---|---|
| `voisin` | 226 | **193 lectures de code** | Non : il ne sert pas, lire suffit |
| `donnees` | 113 | comptage (65), puis POC (30) | Oui, en complément d'un comptage complet |
| `outil` | 87 | **39 POC + 21 lectures de doc** | **Oui : le POC est seul à attraper** ce que la doc tait |
| `env` | 59 | 19 POC | Oui, pour ce qui dépend de la machine réelle |
| `page` | 52 | **36 relectures** du plan | Non : relire suffit |
| `quota` | non détaillé | non détaillé | **Oui, le POC est seul** |
| `existant` | **3** | — | Sans objet : voir ci-dessous |

Les six premiers angles listés avec un effectif totalisent 540 surprises ;
**au moins 92 relèvent donc d'autres angles** (dont `quota`), non détaillés
dans ce document.

Ce qu'il faut en retenir, en une phrase par ligne :

- **`voisin` et `page` : ne pas faire de POC.** 193 surprises sur 226 et 36
  sur 52 se règlent par une lecture. Un POC y serait un détour plus cher.
- **`outil`, `env`, `donnees`, `quota` : le POC est le bon remède, parce que
  la réponse n'est écrite nulle part avant qu'on essaie.** Aucune lecture du
  code du dépôt ne dit ce qu'un fournisseur tiers fait d'une requête.
- **`existant` ne se mesure pas avec cette méthode.** L'angle ne compte que
  **3 lignes**, et ce n'est pas une bonne nouvelle : on ne découvre pas à
  l'exécution une solution qu'on n'a jamais cherchée. Un banc d'évaluation
  de modèles construit à la main alors que des benchmarks publics existaient
  n'apparaît dans **aucun journal** : personne ne s'en est aperçu, donc rien
  n'a été noté. Ce que les journaux ne peuvent pas mesurer, seule une
  recherche **avant** le plan peut le trouver.

### Exemples de surprises que seul un POC attrapait (anonymisés)

- une option d'API qui bascule silencieusement au palier de facturation
  supérieur ;
- un préflight CORS (la requête d'autorisation préalable d'un navigateur)
  refusé par un fournisseur de tuiles cartographiques ;
- 8 URL de photos sur 8 qui répondent 403 ;
- un connecteur tiers qui tronque une réponse ;
- des quotas distincts selon le chemin d'accès au même service ;
- le `PATH` des unités systemd sans le gestionnaire de versions de node ;
- un hook de dépôt redécouvert dans 3 plans successifs ;
- des preuves de fin injouables : un script qui sort en code 2 sans
  entrée, un `--check` censé valoir 0 alors que c'est impossible à son rang ;
- une suite de tests déjà rouge sur la branche principale, découverte en
  route.

Le point commun : **la réponse existait, elle coûtait quelques minutes à
obtenir, et personne ne l'avait demandée à la réalité avant de valider.**

## Ce que les POC déjà faits ont appris (12 plans relus)

Douze plans avaient fait un POC. Leur relecture donne deux listes, et la
seconde est plus instructive que la première.

**Ce qui a marché :**

- un **seuil écrit avant la mesure**, avec un « arrêt si » : on sait avant de
  voir le résultat ce qui vaudra oui ou non ;
- des **jeux nommés et séparés** (73 corrections humaines, 360 cas au hasard,
  80 cas sans sous-catégorie) : chacun répond à une question distincte ;
- la **stabilité rejouée** (498 résultats identiques sur 503 en rejouant) ;
- la **relecture manuelle** des signalements plutôt que la confiance dans le
  score ;
- des **leviers comparés sur un jeu fixe** ;
- un **plafond d'appels écrit avant** (1 500 prévus, 430 réels) ;
- le **détail par croisement** plutôt que le taux global ;
- le **banc figé en test**, pour qu'il serve encore après le POC ;
- l'**abandon prévu d'avance** : si tel résultat, on s'arrête.

**Ce qui a manqué :**

- **la mesure renvoyée à l'exécution** sur 4 fiches : le POC existait sur le
  papier, il n'a pas eu lieu avant `valide` ;
- un **jeu biaisé** : 19 cas durs mesurent le pire cas, pas le taux moyen ;
- un **POC hors population réelle** ;
- un **témoin vide, comptable dès la conception** : un groupe de contrôle
  qui ne pouvait rien montrer ;
- des **chiffres fondateurs faux** : un coût de vision mesuré à 27,5 $ par
  guide contre 1,04 $ estimé ; une résolution de rendu fausse d'un
  facteur 2 ;
- un **masque de champs par défaut** qui cachait ce qu'on cherchait ;
- un **volume faux de 80 %** ;
- un **POC sans critère d'arrêt** : 115 requêtes pour 2 trouvailles.

Le tri : ce qui a marché, c'est presque toujours **une décision écrite avant
le résultat**. Ce qui a manqué, c'est presque toujours **une hypothèse non
mesurée, ou un POC qui ne ressemblait pas au réel**. Un POC mal cadré rend
un chiffre faux avec l'air d'une preuve — c'est pire que pas de POC.

## Ce qui en découle

Les leviers retenus (décision D8 du plan qui a suivi ce relevé) :

**A — Répétition à blanc systématique avant `valide`.** Avant de valider un
plan, on joue à blanc ce qui peut l'être : les commandes de preuve, les
privilèges, les chemins. Ce levier cible ce que le POC de décision ne
couvre pas : les preuves injouables et les suites déjà rouges, qui se
trouvent en lançant la commande et non en la relisant.

**B — Agent `enqueteur` renforcé (geste 14).** Le geste ajouté : **les tests
des fichiers touchés et leurs consommateurs**. C'est la réponse à l'angle
`voisin`, premier de la liste (226 surprises, 193 réglées par une lecture).
Le renforcement précédent (gestes 7 à 12 dans
`plugins/plans-notion/agents/enqueteur.md`) n'a pas fait bouger le ratio ;
ce geste vise la part que la lecture du fichier ne suffisait pas à voir.

**C — Libellé obligatoire de chaque découverte, contrôlé à la clôture.**
Répond directement aux 317 surprises sans libellé : tant qu'un plan peut
se clore sans que chaque découverte soit marquée « trouvable » ou « pas
trouvable », le ratio se calcule sur la moitié du réel. Le contrôle est
mécanique, à la clôture, sur le modèle du décompte vérifié par `grep` du
rétex précédent (recommandation 19).

Trois autres décisions du même plan ferment ce que les leviers A à C ne
couvrent pas :

- **Un POC de décision obligatoire dès qu'une option dépend d'une
  incertitude mesurable** (décision D2). C'est le remède des angles `outil`,
  `env`, `donnees` et `quota`, les seuls où le POC est seul. Le cadrage suit
  la liste « ce qui a marché » ci-dessus : seuil et « arrêt si » écrits avant,
  plafond d'appels, jeu représentatif du réel.
- **La recherche de l'existant par un agent `chercheur`** (décision D6).
  C'est la réponse à l'angle `existant`, que ce relevé ne peut pas mesurer :
  chercher **avant** le plan ce qui existe déjà, plutôt que de compter après
  coup ce qu'on aurait pu ne pas construire.
- **Un registre des outils et quotas** (décision D5), qui vise les 22
  surprises (3,5 %) dont le remède était de consulter une limite déjà connue
  — et qui évite de refaire chaque fois le même POC sur le même quota.

Ce que ce retour **n'a pas décidé** : réduire la part du POC. Il en fait un
outil ciblé (quatre angles sur sept, où la réponse n'est écrite nulle
part), pas une étape systématique. Lire le code reste, et de loin, le remède
le moins cher pour près de la moitié des surprises.

## Limites de ce relevé

- **Le jugement des sous-agents fait la répartition par remède et par POC.**
  Cinq lecteurs, une même consigne, mais aucune contre-lecture : deux
  lecteurs auraient pu classer autrement une même surprise.
- **La moitié des surprises n'a pas de libellé** (317 sur 632) : le ratio
  « trouvable » ne porte que sur les 315 autres.
- **Un POC « qui l'aurait attrapée » est une hypothèse.** 12 POC réels ont été
  relus ; ils montrent aussi qu'un POC mal cadré peut rendre un chiffre faux.
  Le 58 % est un plafond, pas une promesse.
- **L'angle `existant` est aveugle par construction.** Le relevé ne voit que
  ce qui a surpris ; ce qu'on n'a pas cherché ne surprend personne.

## La suite : le seuil qui dira si ça a pris

Rejouer ce relevé **sur les plans exécutés après ce plan** (même consigne,
mêmes colonnes) **une fois une vingtaine de plans clos** — assez pour que le
ratio ne bouge pas au hasard d'un plan.

Le verdict est fixé d'avance, pour ne pas le discuter après coup :

- si le ratio « trouvable » **libellé ne descend pas sous 65 %**, ou
- si **plus de 20 %** des surprises restent **sans libellé**,

alors **les leviers A à C n'ont pas pris**, et le prochain plan le dit.

Pour repère : aujourd'hui le ratio vaut 74,6 % (il faudrait donc gagner près
de dix points) et la part sans libellé vaut 50,2 % (317 sur 632, à ramener
sous 20 %). Le second seuil se joue sur le levier C, qui est mécanique ; le
premier se joue sur les leviers A et B, qui dépendent de ce que les
sessions font vraiment — c'est lui le plus incertain.
