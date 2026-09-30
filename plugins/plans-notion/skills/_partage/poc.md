# Le POC et la répétition à blanc

Fichier **partagé**, lu par `plan-notion` à la conception (avant de passer un
plan à `valide`) et par `executer-plan-notion` à l'exécution, pour noter au
journal l'écart entre ce que le POC avait mesuré et ce que l'exécution a
trouvé. Comme `vagues.md` et `preuve-du-rouge.md`, il vit à un seul endroit
pour que les skills gardent leur taille : la règle ne se duplique pas, elle se
référence. Écarté : écrire ce gabarit dans `plan-notion/SKILL.md`, qui pèse déjà
près de 800 lignes.

Il ne dit pas *comment* découper un plan en étapes ni *quand* les paralléliser
(`${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`), ni *comment* prouver qu'un
test a mordu (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/preuve-du-rouge.md`).
Il dit *quoi* vérifier **avant** de valider un plan, pour que la première
surprise n'arrive pas en pleine exécution : une répétition à blanc de ce qui
est déjà écrit, et, quand une option du plan repose sur une incertitude
mesurable, un POC (preuve de concept : une mesure jetable, faite avant de
choisir) qui la lève.

## Pourquoi ce fichier

Le relevé des 43 plans exécutés du 2026-09-08 au 2026-09-28, en cinq lignes :

- **632 surprises relevées** dans ces 43 plans : un fait que le plan ne
  connaissait pas et que l'exécution a découvert.
- **Le ratio « trouvable » n'a pas bougé** : 74,6 % (235 surprises sur 315
  libellées) contre 78,6 % au rétex précédent. Environ les trois quarts de
  ce qui surprend auraient pu être vus avant, et cette part ne recule pas.
- **La moitié des surprises n'a pas de libellé** (317 sur 632) : personne n'a
  écrit ce qui avait manqué, donc personne ne peut le prévenir la fois
  suivante.
- **Le remède le moins cher** : lire le code, 43 % des cas ; le POC, 20 % ;
  compter sur les données réelles, 13 %.
- **Un POC l'aurait aussi attrapée** dans 48 % des cas (58 % en comptant les
  cas où il l'aurait attrapée en partie), et il est **seul efficace** sur
  quatre angles : l'outil (ce qu'il fait vraiment), l'environnement, les
  données, le quota. Lire le code ne dit rien de ces quatre-là.

Le POC ne remplace donc pas l'enquête : il prend le relais là où lire ne
suffit plus.

## La répétition à blanc

**Systématique, avant de passer un plan à `valide`.** Elle se joue dans un
worktree **détaché** sur `origin/main`, jamais sur une branche de travail ni
dans le checkout principal, et retiré dans la même passe :

```bash
git worktree add --detach <chemin> origin/main
# ... les quatre gestes ci-dessous ...
git worktree remove --force <chemin>
```

Les quatre gestes, dans cet ordre :

1. **Jouer chaque commande de preuve écrite au plan**, telle quelle, à
   l'endroit où l'exécution la jouera. Une commande qu'on n'a jamais lancée est
   une hypothèse : elle peut sortir en code 2 faute d'entrée, ou porter un
   `--check` qui exige un zéro impossible à son rang dans le plan.
2. **Jouer la suite complète du dépôt**, pour connaître l'état de départ. Une
   suite déjà rouge sur `main` se découvre ici, en une minute, et non à la
   troisième étape en cherchant ce que l'étape a cassé.
3. **Faire un appel d'essai par outil externe** que le plan utilise, dans la
   limite du registre des quotas (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`) : un seul
   appel, pour voir la forme de la réponse, le coût réel et les droits du
   compte, jamais un lot.
4. **Refaire les comptages avec le chargeur réel du dépôt**, sur tout le
   corpus concerné, jamais avec un parseur écrit pour l'occasion : un parseur
   de circonstance lit le corpus comme son auteur l'imagine, le chargeur du
   dépôt le lit comme l'exécution le lira.

Un plan `Bounded` (périmètre fermé, sans outil externe) ne joue que les gestes
1 et 2 : il n'y a rien à essayer chez un tiers, et le corpus, s'il y en a un,
est celui que la suite complète charge déjà.

**Le résultat va dans `Contraintes techniques vérifiées`**, sous un intertitre
« État de départ » : les commandes jouées, leurs sorties, le décompte de la
suite, les comptages. Un plan `valide` sans cette section n'a pas eu sa
répétition.

Ce que la répétition a déjà attrapé, anonymisé :

- une commande de preuve qui sortait en code 2 quand on la lançait sans
  entrée ;
- un `--check` censé rendre 0 alors que l'étape qui le fait passer venait plus
  tard dans le plan ;
- une suite déjà rouge sur `main`, découverte en route, alors qu'on la
  croyait verte ;
- un hook de dépôt (un garde-fou qui refuse certains gestes au commit)
  redécouvert, à chaque fois en cours d'exécution, dans trois plans distincts.

## Le POC de décision : le gabarit en douze points

Quand une option du plan **dépend d'une incertitude mesurable** — le taux de
réussite d'un outil, le volume réel d'une population, le coût d'un appel — le
plan ne tranche pas sur une impression : il fait un POC, avant `valide`. Le
gabarit tient en douze points, tous à remplir, même par « sans objet, parce
que… » :

1. **Question et décision pilotée.** La question s'écrit en une phrase et
   nomme la décision qu'elle commande : « si la mesure dit X, l'option A ; si
   elle dit Y, l'option B ». Un POC sans décision au bout est de la curiosité.
2. **Population réelle recomptée.** Le nombre d'éléments sur lesquels la
   décision portera, recompté par commande, pas repris d'un plan précédent ni
   d'une estimation. Un volume repris de mémoire s'est trouvé faux de 80 %.
3. **Jeux nommés, lus séparément, taille minimale justifiée.** Au moins un jeu
   tiré au hasard (le taux moyen), un jeu de vérité humaine (ce qu'une
   personne a déjà tranché), un jeu de cas durs (le pire cas). Chacun se lit
   à part, jamais fondu dans une moyenne, et sa taille se justifie : pourquoi
   ce nombre suffit à distinguer les deux options.
4. **Seuil de décision et seuil d'arrêt, écrits avant la mesure.** Le seuil
   dit à partir de quand l'option est retenue ; l'arrêt dit à partir de quand
   on cesse de mesurer et on écarte. Les deux s'écrivent avant de voir un
   seul chiffre.
5. **Rejeu de stabilité.** Rejouer le même jeu une seconde fois : un résultat
   qui change d'un passage à l'autre ne tranche rien, et il vaut mieux le
   savoir avant de bâtir dessus.
6. **Anti-biais.** Jugement à l'aveugle quand un humain ou un modèle note ;
   rien du banc d'essai dans la consigne de l'outil mesuré ; **jamais de
   rejeu sur les cas qui ont servi à corriger** l'outil, sans quoi on mesure
   ce qu'on a appris et non ce qu'il sait faire.
7. **Coût et quota lus au registre.** Le coût d'un appel et le quota se lisent
   dans `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`, jamais de mémoire. Un appel d'essai
   précède tout lot, et le lot porte un plafond écrit (`--max-appels` ou
   l'équivalent) qui coupe la mesure au lieu de la laisser courir.
8. **Chiffres fondateurs vérifiés par commande.** Chaque chiffre sur lequel
   repose la question (volume, coût unitaire, taux de départ) est recalculé
   par une commande dont la sortie est recopiée. Un chiffre non vérifié ne
   fonde rien.
9. **Ce que le POC ne mesure pas.** Une ligne honnête sur ses angles morts :
   la population qu'il n'a pas couverte, le cas qu'il n'a pas pu simuler.
   Elle empêche d'étendre la conclusion au-delà de ce qui a été vu.
10. **Critère coût / bénéfice.** Ce que la mesure coûte (appels, temps de
    pilotage, quota) comparé à ce que l'erreur de décision coûterait. Un POC
    qui coûte plus cher que l'erreur qu'il évite ne se fait pas : on tranche
    avec le doute écrit.
11. **Écart POC / exécution, noté au journal.** À la fin de l'exécution,
    `executer-plan-notion` compare ce que le POC avait annoncé à ce que
    l'exécution a mesuré, et l'écrit au journal. C'est ce qui permet de savoir,
    plan après plan, si les POC sont fiables.
12. **Coût de pilotage chiffré, à côté de chaque option.** Chaque option du
    plan porte, à côté de sa description, ce que sa mise en œuvre coûte à
    piloter (nombre d'étapes, de sous-agents, d'appels, de relectures). Une
    option moins chère à construire et plus chère à surveiller ne se voit
    qu'avec ce chiffre.

Exemples réels, anonymisés, de ce qui a marché :

- **Un seuil écrit avant la mesure, avec son « arrêt si ».** « Si l'agent dit
  oui à confiance ≥ 0,80 à plus de 2 de ces 19 propositions, la publication
  automatique reste fermée. » La raison, donnée dans le plan : « écrire la
  règle avant de voir les chiffres empêche de choisir un gagnant puis de lui
  trouver des raisons. »
- **Des jeux nommés et séparés** : 73 corrections humaines (la vérité), 360
  cas tirés au hasard (le taux moyen), 80 cas sans sous-catégorie (le cas
  dur). Chaque jeu s'est lu à part, sans être fondu dans une moyenne.
- **Une stabilité rejouée** : 498 résultats identiques sur 503 au second
  passage.
- **Un plafond d'appels écrit avant** : 1 500 prévus, 430 réels.
- **Un abandon prévu d'avance** : le plan disait à quel chiffre l'option serait
  écartée.

Exemples réels, anonymisés, de ce qui a manqué :

- **Une mesure renvoyée à l'exécution** : la question a été posée au plan, mais
  sa mesure a été remise à une étape, donc après le choix de l'option.
- **Un jeu biaisé** : 19 cas durs présentés comme un taux, alors qu'ils
  donnaient le pire cas, pas la moyenne.
- **Un POC hors population réelle** : mesuré sur des exemples choisis à la
  main, pas sur ce que le traitement recevrait.
- **Des chiffres fondateurs faux** : un coût de vision mesuré à 27,5 $ par
  guide contre 1,04 $ estimé.
- **Un masque de champs d'API laissé par défaut** : l'outil rendait moins
  que ce que le plan supposait, et personne ne l'avait regardé.
- **Un volume faux de 80 %**, repris d'un plan précédent sans recomptage.
- **Un POC sans critère d'arrêt** : 115 requêtes lancées pour deux trouvailles,
  faute d'avoir écrit à partir de quand s'arrêter.

## La frontière : ce qui est un POC, ce qui est une étape

Un POC **tranche une option** ; il se joue **avant `valide`**, et son résultat
va dans le plan. Un banc d'essai qui **est le livrable** — l'outil de mesure
que Benjamin veut garder, rejouer, faire évoluer — n'est pas un POC : c'est
une étape d'exécution, avec sa liste de fichiers, ses tests et sa preuve.

Le test pour trancher : « si je supprime ce code après avoir lu son résultat,
le plan y perd-il quelque chose ? » Non : c'est un POC. Oui : c'est une étape.

## Le code jetable

Le code d'un POC est **jetable**, et il se traite comme tel :

- **Dans le scratchpad seulement**, jamais dans le dépôt : pas de commit, pas
  de branche, pas de fichier « temporaire » qui traîne dans l'arbre.
- **Supprimé dès que son résultat est sur la page** du plan : le chiffre y est,
  le script n'a plus de raison d'exister.
- **Un `du -sh` du scratchpad en fin de passe**, pour vérifier que rien n'y
  reste. Décision de Benjamin : « il faut systématiquement le nettoyer pour ne
  pas perdre de place sur le VPS ». Le scratchpad d'une seule session a pesé
  336 Mo, avec un disque déjà à 83 %.
- **Un script qui mérite de survivre devient une étape d'exécution**, réécrit
  avec ses tests (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/bons-tests.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/preuve-du-rouge.md`) : on ne garde pas
  un brouillon de mesure au motif qu'il a servi.
