---
name: executer-plan-notion
description: Implémente un plan de travail cadré dans Notion — vérification du statut avant de coder, découpe en étapes, sous-agents, journal d'exécution écrit sur la page, statut final. À charger AVANT d'écrire la moindre ligne de code dès que Benjamin donne le feu vert sur un travail déjà cadré, par exemple « go », « vas-y », « on y va », « attaque », « tu peux coder », « lance l'implémentation », « déroule le plan », « on passe à la réalisation », « c'est bon pour moi ». À charger aussi pour reprendre un chantier commencé — « reprends là où on s'est arrêté », « continue le refacto », « t'en étais à l'étape 2 », « on continue l'exécution ». À charger aussi quand Benjamin demande la PR ou la remontée sur `main` d'un travail déjà livré — « ouvre la PR », « merge sur main », « tu peux merger directement », « pousse ça sur main » — y compris dans une session où rien n'a été codé : la PR du plan ne s'ouvre que sur sa demande, et c'est ce skill qui fait passer la page de `a merger` à `execute`, sans quoi le merge a lieu mais la page ment. Vaut même si ni Notion ni le mot « plan » ne sont cités, même si seule une partie des étapes est demandée, et même si le plan n'est pas encore validé, car c'est ce skill qui dit quoi faire dans ce cas. Commence toujours par remettre le chapitre Exécution du plan à jour des dernières réponses et commentaires de Benjamin, y compris quand il a validé la page lui-même sans repasser par plan-notion. Ne couvre pas la conception du plan, qui relève du skill plan-notion, ni une tâche isolée sans plan derrière.
---

# Exécuter un plan Notion

## La porte d'entrée

**Aucune ligne de code avant d'avoir lu le `Statut` de la page du plan.**

- `valide` → on y va.
- `a merger` ou `execute` → **le travail est déjà fait**, sur sa branche pour le
  premier, sur `main` pour le second. S'arrêter et le dire : refaire une
  exécution terminée est le plus coûteux des malentendus.
  **Une exception, et une seule** : à `a merger`, Benjamin peut demander la
  **PR du plan, ou la remontée sur `main`**. Ce n'est pas une réexécution,
  c'est la dernière opération du plan — la faire (§6), et poser `execute` dans
  le même tour si le code part sur `main`.
- `brouillon`, `en revue` → s'arrêter et le dire. Un plan pas encore validé est
  une proposition, pas une commande : coder dessus, c'est produire un travail que
  Benjamin n'a jamais accepté.
- `en cours` → une exécution est déjà commencée. Lire le `Journal d'exécution`
  avant tout et reprendre où elle s'est arrêtée, plutôt que de repartir de zéro.
- Benjamin qui dit « go » ne remplace pas le statut. Il le dit de mémoire, la page
  dit ce qui a été tranché. **En cas de désaccord entre les deux, demander** — ça
  coûte un tour, refaire une implémentation en coûte dix.

⚠️ Les valeurs de `Statut` sont **sans accents** : `brouillon`, `en revue`,
`valide`, `en cours`, `a merger`, `execute`, `archive`. Écrire `exécuté` fait
échouer l'appel avec une `validation_error`.

Le connecteur **Notion** est indispensable. S'il manque, le dire immédiatement
plutôt que de contourner : exécuter sans pouvoir écrire le journal produit un
travail dont il ne reste aucune trace hors du fil de discussion, et le fil
disparaît au compactage du contexte.

## 1. Charger le plan

1. Retrouver la page : base **Plans Claude**, dans `IA / Claude`, reliée à la page
   projet dont la propriété `Repo` correspond au dépôt courant.
2. Lire la page **entière**, pas seulement le chapitre `Exécution`. Les décisions
   vivent aussi dans les cases cochées et dans le texte libre écrit après
   `Autre / complément →`, que `get-comments` ne montre pas.
3. Lire les fils de commentaires **non résolus** — il faut demander explicitement
   ceux ancrés dans le corps, sinon on ne voit que ceux de niveau page. Un fil non
   résolu qui contredit le chapitre `Exécution` bloque l'étape concernée : le
   signaler plutôt que de trancher seul.
4. **Relever, question par question, les cases cochées et les textes libres.** Ce
   relevé est le garde-fou de chaque écriture ultérieure (§5) ; sans lui, une
   refonte de section efface silencieusement les décisions de Benjamin.

## 2. Ouvrir l'exécution

### Remettre le chapitre `Exécution` à jour — toujours

**Le chapitre `Exécution` est presque toujours en retard d'un tour.** Benjamin
répond aux questions dans la page, coche des cases, écrit après
`Autre / complément →`, laisse un commentaire, passe `Statut` à `valide` et
enchaîne directement sur ce skill — **sans repasser par `plan-notion`**. Rien n'a
donc répercuté ses dernières réponses dans les étapes. Coder sur ce chapitre-là,
c'est exécuter le plan d'avant ses réponses, et le découvrir trois étapes plus
loin.

Donc, **avant la première étape, sans exception** — même si le plan a l'air à
jour, même s'il a été écrit dans la même session :

1. Reprendre le relevé du §1 : chaque case cochée, chaque texte libre, chaque fil
   non résolu, chaque commentaire de la dernière passe.
2. **Confronter chaque réponse au chapitre `Exécution`, étape par étape.** Une
   réponse peut supprimer une étape, en fusionner deux, changer la liste des
   fichiers, retourner un choix d'architecture — ou ne rien changer du tout.
3. **Écrire ce qui change**, en édition ciblée (§5), et **dater** chaque
   correction : `_maj 2026-08-21 — Q3 tranchée : l'étape 4 tombe, le cache est
   fait côté serveur._` Renuméroter les H3 si des étapes disparaissent, pour que
   le sommaire reste une suite sans trou.
4. **Une réponse qui ne change rien s'écrit quand même**, en une ligne sous
   l'étape concernée : `_Q2 confirme l'approche, étape inchangée._` Sans ça, on ne
   distingue plus une réponse prise en compte d'une réponse oubliée.
5. **Relire le chapitre entier** une fois les corrections posées. Il doit se tenir
   seul, sans avoir à remonter aux questions pour le comprendre : c'est lui, et
   lui seul, qui part dans les briefs des sous-agents (§3), et un sous-agent n'a
   pas la page.

Cette passe **met le plan à jour, elle ne le redessine pas**. Si une réponse remet
en cause l'approche elle-même — pas une étape, l'approche — ce n'est plus une mise
à jour mais une nouvelle passe de conception : le dire, repasser par
`plan-notion`, et ne rien coder en attendant.

Puis, dans le même tour, avant la première étape :

- **Les questions restées orange passent au vert**, réponse recopiée en gras dans
  le titre de l'encadré, avec la mention `(reco appliquée par défaut)`. C'est le
  moment précis où l'absence de réponse devient une décision. Si ça reste
  implicite, plus personne ne saura ensuite distinguer ce qui a été choisi par
  accord de ce qui a été choisi faute de réponse.
- `Statut` = `en cours`, propriété `Branche` renseignée.
- Créer **la** branche du plan : `type/thème-en-kebab` (`feat/`, `fix/`, `chore/`,
  `docs/`, `refactor/`), nommée d'après le sujet du plan et **dérivée de `main` à
  jour**. Jamais de travail sur `main`.
- **Relever ce qui déclenche la CI du dépôt**, une fois pour tout le plan :

  ```bash
  grep -n -A6 '^on:' .github/workflows/*.yml     # push ? pull_request ? sur quelles branches ?
  grep -ln 'pr merge' .github/workflows/*.yml     # un job merge-t-il seul les PR vertes ?
  grep -rli 'e2e\|playwright\|cypress' .github/workflows/ package.json pyproject.toml 2>/dev/null  # des e2e ?
  ```

  Trois réponses à noter dans l'entrée `Ouverture` du journal (§4), parce
  qu'elles commandent la suite : **un `push` sur une branche autre que `main`
  lance-t-il un run ?** (si oui, la branche ne se pousse qu'à la clôture, §6 ;
  sinon, elle se pousse après chaque étape, §3) ; **le dépôt a-t-il des tests
  e2e ?** (si oui, ils passent en local à la clôture, §6, et la PR du plan — le
  jour où Benjamin la demande — s'ouvre avec le label `review-required`, §6) ;
  **un job merge-t-il tout seul les PR vertes ?** (si oui, ouvrir la PR, c'est
  remonter sur `main` — sur `vahiny`, `review-required` commande la suite
  complète de tests puis, tout vert, le merge par la CI : sans lui, ce dépôt ne
  joue que les tests unitaires).

**Par défaut, un plan = une seule branche, et aucune PR tant que Benjamin ne la
demande pas** (§3, §6). Les étapes sont des **commits** sur la branche du plan,
pas des PR, et l'exécution **s'arrête à la branche** : travail complet, suite
complète jouée en local, page à `a merger`. La raison est comptable, et elle
s'est fixée en deux temps. Le 2026-09-03 : chaque PR déclenche un run GitHub
Actions complet — tests, build, e2e sur runner — et un plan de huit étapes en
coûtait huit, plus celui de la remontée ; le quota mensuel d'Actions s'y
consumait, `vahiny` en tête. Le 2026-09-04 : même la PR unique de clôture ne
s'ouvre plus d'elle-même — la remontée vers `main` est un geste vers
l'extérieur, et il n'a lieu que sur demande explicite de Benjamin (§6). La CI ne
tourne donc **au plus qu'une fois par plan**, sur la PR qu'il demande ; en
cours de route comme à la clôture, la preuve est **locale** (§3, §6). Ce qui ne
change pas : `main` ne bouge pas de toute l'exécution, et la branche du plan
porte à tout moment l'état complet de ce qui est livré. Une autre organisation —
une PR par étape, plusieurs branches — ne se fait que si Benjamin la demande.

## 3. Dérouler les étapes

Le chapitre `Exécution` de la page est la feuille de route. Il ne se réécrit pas
pour raconter l'avancement : l'avancement va dans `Journal d'exécution` (§4).

### Une étape = un commit sur la branche du plan, prouvé en local

Le défaut, sauf avis contraire de Benjamin :

- Chaque étape se code **directement sur la branche du plan**. Pas de
  sous-branche, pas de PR d'étape : une PR, c'est un run de CI, et c'est
  précisément ce qu'on économise (§2).
- **La preuve de l'étape est locale, et c'est la session principale qui la
  joue** — pas le rapport du sous-agent. Rejouer la commande de preuve du brief,
  et recopier sa sortie au journal (§4). **Cette preuve, ce sont les tests des
  fichiers impactés par l'étape, et rien de plus** : ni suite complète, ni tests
  e2e, même si l'étape touche un écran. Les e2e sont lents et lourds (navigateur,
  serveur à lancer), et les jouer à chaque étape reproduirait en local le coût
  qu'on vient de retirer de la CI. Ils passent **une fois, à la clôture** (§6),
  avec la suite complète — c'est le verdict de fin de plan, rendu en local.
  Décision de Benjamin du 2026-09-03.

  **« Les tests des fichiers impactés », précisément.** La liste se construit à
  partir des fichiers **réellement** touchés — `git diff --name-only` depuis le
  commit de l'étape précédente, pas la liste du brief — et elle a deux sources :
  1. **les tests écrits ou modifiés pendant l'étape** : en TDD ce sont eux qui
     définissent l'étape, ils tournent forcément ;
  2. **les tests existants qui couvrent les sources touchées**. Le plus sûr est
     le mode « related » du runner quand il existe — `npx vitest related
     <sources>` (vitest remonte les imports), `npx jest --findRelatedTests
     <sources>`. Sans ce mode (pytest, autres) : la convention de nommage du
     dépôt (`foo.py` → `test_foo.py`, `foo.ts` → `foo.test.ts`) **plus** un
     `grep -l` du nom du module dans les dossiers de tests, pour attraper ceux
     qui l'importent sous un autre nom.

  La commande de preuve du brief se dérive de cette liste ; au retour du
  sous-agent, elle se **rejoue sur la liste réelle** — un fichier touché en plus
  élargit la preuve, il ne la contourne pas. Une étape qui n'écrit aucun test et
  qu'aucun test existant ne couvre le dit au journal, en une ligne : soit elle
  n'a rien à tester (doc, config — la preuve est alors le lint ou le build des
  fichiers touchés), soit c'est un test qui manque, et mieux vaut le savoir à
  l'étape qu'à la clôture. Le reste de la suite attend la clôture (§6), et c'est
  voulu : c'est là qu'une régression éloignée se verra, une fois et pas huit.
- **Verte → un commit par étape**, sur la branche du plan. Message conforme aux
  conventions du dépôt, portant le numéro et le titre de l'étape — p.ex.
  `feat(api): étape 2 — endpoint de liste`. Corps repris de l'entrée de journal.
  L'étape suivante part de cette base.
- **Pousser la branche après le commit, seulement si le relevé du §2 dit qu'un
  `push` ne lance rien.** Sinon, les commits restent locaux jusqu'à la clôture,
  et l'entrée de journal le dit : c'est la page, pas GitHub, qui garde alors la
  trace de l'avancement.
- **Rouge → on corrige jusqu'au vert.** Une preuve rouge n'est pas une étape
  finie : lire la sortie, corriger, rejouer, et recommencer. Le diagnostic reste
  dans la session principale (cf. plus bas) ; le correctif peut repartir en
  sous-agent, avec le log d'échec recopié dans le brief. **Jamais de
  contournement** : ni `--no-verify`, ni check désactivé, ni test rendu tolérant
  pour faire passer la barre. Un test rouge dit quelque chose ; le faire taire ne
  le fait pas disparaître, ça le déplace dans l'étape suivante — ou dans la suite
  complète de la clôture, ou dans le run de CI de la PR que Benjamin demandera.
- **La seule sortie de cette boucle est l'arbitrage de Benjamin : quand le
  correctif est structurant.** C'est-à-dire quand réparer ne tient plus dans
  l'étape — il faut revenir sur une décision du plan, toucher un schéma de
  données, un contrat d'API, une dépendance, ou déborder sur des fichiers hors du
  périmètre de l'étape. Dans ce cas : **le travail de l'étape ne monte pas sur la
  branche du plan** — il part sur une branche de côté
  `<branche-du-plan>/etape-N-en-echec`, sans PR (donc sans CI), pour n'être ni
  perdu ni mêlé à ce qui est livré ; entrée de journal avec la sortie de la
  preuve, le nom de cette branche **et le correctif envisagé** ; l'exécution
  continue sur les étapes qui n'en dépendent pas ; et l'arbitrage part dans le
  plan de suite (§7). Ce n'est pas à moi de trancher un correctif structurant en
  douce : c'est exactement le genre de décision que le plan validé n'a pas
  couverte.
- Se traite **de la même façon** : un échec qu'on ne sait plus diagnostiquer.
  Deux ou trois passes sérieuses sans comprendre pourquoi le test tombe, c'est un
  blocage à faire remonter, pas une boucle à poursuivre.
- **Avec ou sans CI sur le dépôt, le verdict de fin de plan est local** : la
  suite complète jouée à la clôture (§6). La CI, s'il y en a une, ne rejoue
  cette suite que sur la PR que Benjamin demande — c'est la seconde ceinture,
  pas la première.

### La délégation est la règle, pas une faveur

**Charger ce skill vaut demande explicite de déléguer.** Certains harnais portent
une consigne du type « ne pas lancer de sous-agent sans que l'utilisateur l'ait
demandé » : la demande est faite ici, une fois pour toutes, pour toute étape d'un
plan au statut `valide`. Il n'y a pas à la redemander à Benjamin étape par étape.

La session de pilotage reste en **Opus effort high** : elle lit le plan, découpe,
brief, vérifie, écrit dans Notion. **Elle n'écrit pas elle-même le code des
étapes déléguables.** Chaque étape part dans un sous-agent **Sonnet 5**, un par
étape, **en séquence** — jamais en parallèle : les étapes d'un plan sont couplées,
et deux sous-agents concurrents éditent les mêmes fichiers sans le savoir.

Concrètement, **un appel de l'outil `Agent` par étape**, avec ces paramètres —
ils ne sont pas indicatifs :

```
Agent({
  subagent_type: "general-purpose",   // il doit pouvoir écrire ; Explore et Plan sont en lecture seule
  model: "sonnet",                    // = Sonnet 5. Omettre ce champ fait hériter Opus : le coût du plan explose
  run_in_background: false,           // séquentiel : on attend le rapport avant l'étape suivante
  description: "Étape N — <titre court>",
  prompt: "<le brief ci-dessous>"
})
```

`model: "sonnet"` est le point qui saute en premier quand on est absorbé par le
travail. Sans lui, l'étape part quand même — mais en Opus, et le seul écart
visible est la facture.

### Le brief du sous-agent

Un sous-agent n'a **rien** du contexte de la session : ni le plan, ni la
discussion, ni les étapes précédentes. Un brief vague rend un travail inutilisable,
et c'est ce qui donne ensuite l'envie de « faire soi-même ». Le brief porte donc,
à chaque fois :

1. **L'objectif de l'étape**, recopié du chapitre `Exécution` — pas résumé.
2. **Le contexte utile** : ce que les étapes précédentes ont produit (repris du
   `Journal d'exécution`, §4), la branche courante, les conventions du repo.
3. **La liste fermée des fichiers qu'il a le droit de toucher**, et l'interdiction
   d'en toucher d'autres.
4. **La commande qui prouve que c'est fini**, à lancer, avec sa sortie à recopier
   telle quelle dans le rapport. Elle ne porte que sur **les tests des fichiers
   impactés** (§3, « précisément ») : ceux que l'étape écrit ou modifie, et ceux
   qui couvrent les sources qu'elle touche — jamais la suite complète.
5. **Ce qu'il ne fait pas** : ni `commit`, ni `push`, ni PR, ni élargissement du
   périmètre, ni écriture dans Notion. En cas d'échec : **diagnostic, pas
   correctif** — le debug revient à la session principale, seule à avoir le plan.
6. **Le format du rapport attendu** : fichiers réellement touchés, sortie de la
   commande, écarts par rapport au brief, blocages.

### Ce qui reste dans la session principale

La liste est courte, et c'est voulu :

- **Les étapes de jugement** — nommage, formulation d'un message vu par un
  utilisateur, choix d'architecture. Les vérifier coûte le prix de les faire.
- **Le debug** après l'échec d'un sous-agent.
- **Toutes les écritures Notion** (§4, §5) et les opérations git.

Une étape dont on ne sait pas énoncer les trois lignes — le test qui doit passer,
les fichiers autorisés, la commande de preuve — **n'est pas une étape à garder
pour soi : c'est une étape mal spécifiée.** On la précise d'abord (au besoin en
corrigeant le chapitre `Exécution`, §4), puis on la délègue. Se rabattre sur « je
la fais moi-même » est le chemin par lequel un plan entier finit exécuté en Opus.

Contrôle de fin de parcours : **une exécution qui se termine sans aucun appel
`Agent` est un défaut**, pas une variante. Le signaler dans le compte rendu (§6)
en disant quelles étapes ont été faites en direct et pourquoi.

### Après chaque étape

- **Un rapport de sous-agent n'est pas une preuve : rejouer la commande** dans la
  session principale, **sur la liste réelle des fichiers touchés**
  (`git diff --name-only`), pas sur celle du brief (§3). Un sous-agent qui
  annonce « les tests passent » a parfois lancé autre chose que ce qu'on croit,
  ou touché un fichier de plus que ce que la commande couvrait.
- **Commiter l'étape sur la branche du plan**, et la pousser si le relevé du §2
  l'autorise (sous-section précédente). Pas de PR.
- **Écrire l'entrée de journal de l'étape dans la page** (§4), sous son propre H3.
- **Afficher un récap de l'étape dans la session** : ce qui a été fait, les
  fichiers touchés, le commit et le verdict de la preuve, les écarts, l'étape
  suivante.
  Quelques lignes — le détail va dans le journal, pas dans le fil.
- **Puis enchaîner sur l'étape suivante sans demander la main.**

### L'autonomie est le défaut

**Un plan se déroule de bout en bout.** Charger ce skill vaut feu vert pour toute
la suite : Benjamin a validé le plan, c'est là qu'il a arbitré. Redemander « je
continue ? » à chaque étape lui refait prendre une décision déjà prise, et coûte
un aller-retour par étape.

Le récap de fin d'étape n'est donc **pas** une demande d'autorisation : c'est un
point de passage visible, qui lui laisse la possibilité d'interrompre s'il le
veut, sans que le déroulé l'attende.

On ne s'arrête en cours de route que sur ce qui rendrait la suite fausse ou
irréversible :

- une preuve rouge — locale, en cours de route comme à la clôture ; CI, sur la
  PR si Benjamin la demande — dont le **correctif serait structurant**, ou qu'on
  ne sait plus diagnostiquer (§3, plus haut) — tant que la correction tient dans
  l'étape, on corrige et on continue, sans rien demander ;
- une décision qui n'est ni dans le plan ni déductible de lui, et qui engage :
  schéma de données, contrat d'API public, suppression de données, dépense ;
- un fil de commentaire non résolu qui contredit l'étape à venir (§1).

Même là, s'arrêter ne veut pas dire attendre les bras ballants : faire **tout ce
qui ne dépend pas** du point bloquant, écrire ce qui bloque au journal, et clore
avec un plan de suite (§7).

## 4. Le journal, et les écarts

Après **chaque** étape, écrire dans `Journal d'exécution` — et dans le miroir local
du plan. C'est le briefing du sous-agent suivant, et c'est ce qui permet de
reprendre après un compactage de contexte ou depuis une autre session.

**Une entrée = un titre H3**, repris mot pour mot du chapitre `Exécution` :
`Étape N — <titre court de l'étape>`. Sans ce titre, l'entrée n'apparaît pas dans
la table des matières de Notion — qui n'indexe que les *headings* — et le journal
d'un plan de dix étapes devient un mur qu'on fait défiler. Les entrées hors étape
prennent le même traitement : `Ouverture` au démarrage, `État final` à la clôture
(§6). **Un journal déjà commencé sans titres se chapitre d'abord**, en découpant
l'existant par étape et en posant les H3 au-dessus, **sans reformuler une ligne**
(§5), avant d'y ajouter quoi que ce soit.

Sous ce titre, l'entrée porte :

- **ce qui a été fait**, dans le détail — assez pour comprendre sans relire le diff ;
- les **décisions prises en route**, et ce qu'elles écartent ;
- les **fichiers réellement touchés** ;
- la **preuve** : commande jouée en local, les tests qu'elle couvre — ceux de
  l'étape, ceux des fichiers impactés — et sa sortie ;
- le **commit de l'étape** (SHA court), poussé ou resté local — ou la branche de
  côté où le travail attend, si l'étape est en échec (§3) ;
- le **reste à faire**, s'il en reste.

C'est la version longue du récap affiché dans la session (§3) : la session dit
l'essentiel, la page garde le détail.

Un écart entre ce qui était prévu et ce qui a été fait s'écrit **aux deux
endroits** :

- une ligne `écart` dans le journal, disant ce qui a changé et pourquoi ;
- une correction **datée** dans l'étape concernée du chapitre `Exécution` :
  `_maj 2026-08-17 — le hook existait déjà, étape 2 réduite à un test._`

Le chapitre reste ainsi une description juste de ce qui a été fait. Un plan qui
ment sur son exécution est pire qu'un plan absent, parce qu'on s'y fie.

Une découverte qui invalide une étape **à venir** se traite de la même façon, mais
**avant** de coder cette étape : corriger le chapitre, puis exécuter. Corriger
après coup revient à réécrire l'histoire, et on ne sait plus ce qui était prévu.

### Qualifier chaque découverte : trouvable au plan, ou pas

Toute découverte notée au journal porte **l'un de ces deux libellés**, et jamais
aucun autre :

- `découverte — trouvable au plan` : l'information **était déjà là** quand le plan
  s'écrivait. Dans le code (un appelant, un réglage, un test existant), dans
  l'historique git, dans le `Journal d'exécution` d'un plan antérieur, ou dans la
  session de conception elle-même. Le test est simple : *l'enquête préalable de
  `plan-notion` l'aurait-elle trouvée ?* Si oui, c'est trouvable.
- `découverte — pas trouvable` : seule l'exécution pouvait la produire. Un
  comportement réel sous charge, une API qui ment sur sa doc, un bug de dépendance,
  un état de données qu'aucune lecture n'annonçait.

Le libellé se complète par **l'endroit où c'était trouvable** — `fichier:ligne`, la
page du plan antérieur, la commande qui l'aurait dit. C'est ce qui transforme un
regret en consigne : la prochaine enquête sait où regarder.

**Dans le doute, écrire `trouvable`.** Le biais doit pousser vers plus d'enquête, pas
vers l'auto-absolution. Et un libellé posé ne se rétro-classe pas à la clôture,
quand l'étape est réussie et que tout paraît moins grave.

Ce n'est **pas un reproche adressé au plan** — c'est la seule mesure qu'on ait de
sa qualité. Sans ces libellés, on juge au ressenti, et un plan qui découvre tout en
route se défend aussi bien qu'un plan qui n'a rien laissé passer. L'entrée
`État final` (§6) porte donc le décompte en une ligne :
`3 découvertes, dont 1 trouvable au plan` — et zéro sur un plan long se dit aussi,
c'est ce qui signale que l'enquête a fait son travail.

## 5. Écrire dans la page sans rien casser

La page porte des décisions de Benjamin que le fil de discussion ne contient pas :
cases cochées, texte libre après `Autre / complément →`, remarques dans le corps.
Une écriture maladroite les efface sans rien signaler.

**Les règles vivent dans un fichier partagé avec `plan-notion` :**

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`

Le protocole en cinq temps — relever avant d'écrire, éditer de façon ciblée,
remettre les `- [x]` en cas de refonte, ne jamais reformuler Benjamin, vérifier
après coup — et les trois pièges de l'API : `update_content` qui ne décoche pas,
l'écriture qui échoue en silence, le commentaire qu'on ne résout jamais soi-même.

Il porte aussi **« Le bleu des retouches »**, et cette règle-là s'applique ici pour
une raison précise : **la remise à jour du chapitre `Exécution` en ouverture est une
retouche du plan comme une autre** (§2). Elle décolore donc le bleu de la passe
précédente avant d'écrire, et marque en bleu ce qu'elle change — sans quoi la page
garderait un bleu périmé qui désignerait les mauvaises lignes. Le `Journal
d'exécution`, lui, ne se colore pas : il s'écrit par ajout, chaque entrée y est neuve
par construction.

**Le lire avant la première écriture Notion de la session**, pas de mémoire. Cette
session-ci en fait beaucoup : la remise à jour du chapitre `Exécution` (§2), une
entrée de journal par étape (§4), la clôture (§6). Une seule de ces écritures
faite de travers coûte les décisions d'une passe entière.

Le relevé du §1 est la liste de contrôle de tout ça : sans lui, pas de refonte de
section.

**Ceinture — fichier introuvable.** Si la lecture échoue (plugin pas encore
installé, version périmée, fichier supprimé localement) : **le dire en une
ligne avec le chemin, et ne rien écrire dans la page**. Et comme la remise à
jour du chapitre `Exécution` (§2) précède la première étape, **ça bloque aussi
le code** — même raisonnement que pour le connecteur Notion manquant (en tête
de fichier) : exécuter sans pouvoir tenir la page produit un travail dont il ne
reste aucune trace hors du fil de discussion, et le fil disparaît au
compactage. Deux issues, dans cet ordre : **mettre à jour le plugin** —
`claude plugin update plans-notion` (redémarrage requis pour l'appliquer), ou
`claude plugin marketplace update` si la source a bougé — ou **demander à
Benjamin**. Coder en se promettant d'écrire la page plus tard est le scénario que
tout ce dispositif existe pour empêcher.

## 6. Clore

Dans le **même tour** que le compte rendu à Benjamin, jamais « plus tard » :

- `Statut` : **`a merger`**. C'est le statut normal de fin d'exécution, sur tous
  les dépôts : le travail est livré sur la branche du plan, prouvé en local, et
  il attend une décision de remontée qui n'appartient pas à ce skill. `execute`
  ne se pose que sur du code **vérifié sur `main`** (sous-section suivante).
  Une seule question, et sa réponse est factuelle — *où est le code à cette
  seconde ?* Poser `execute` sur du travail qui dort sur une branche fait croire
  la base plus avancée qu'elle ne l'est, et c'est le genre de mensonge qu'on ne
  découvre qu'en cherchant une fonctionnalité absente de la production. **La
  symétrie est vraie aussi, et c'est elle qu'on oublie** : laisser `a merger`
  sur du travail déjà parti sur `main` annonce un chantier en attente qui
  n'existe plus, et le plan suivant repart d'une base fausse.
- Ce skill ne pose jamais `archive` : ranger une page est une décision de
  Benjamin, pas un effet de bord d'un merge.
- `Branche` renseignée : la branche du plan. `PR` reste **vide** tant qu'aucune
  PR n'existe — une propriété remplie d'une PR qui n'a pas été ouverte ment
  autant qu'un statut faux.
- `Journal d'exécution` clos par une entrée `État final` (H3, comme les autres,
  §4) : ce qui est livré, le verdict de la suite complète (point 1 ci-dessous),
  les écarts, le reste à faire s'il y en a, et le lien vers le plan de suite s'il
  y en a un (§7).
- Le compte rendu dit **quelles étapes sont parties en sous-agent Sonnet** et,
  pour celles faites en direct, pourquoi (§3). Il dit aussi, en une ligne, que
  **la PR n'est pas ouverte et qu'elle le sera sur demande** — avec le label
  `review-required` si le dépôt a des tests e2e (relevé du §2).
- **Livrer la branche, et s'arrêter là.** Pas de PR : la remontée vers `main`
  est un geste vers l'extérieur, et il n'a lieu que sur demande explicite de
  Benjamin — décision du 2026-09-04, qui revient sur la PR de clôture
  automatique du 2026-09-03. La séquence de clôture est courte :
  1. **Jouer la suite complète en local** : tous les tests unitaires, lint,
     build, **et les tests e2e** — c'est ici, et seulement ici, qu'ils passent
     (§3). C'est **le verdict de fin de plan** : tant qu'il n'est pas vert, le
     plan n'est pas clos. Rouge → corriger jusqu'au vert, même boucle qu'en
     cours de route ; correctif structurant ou échec qu'on ne sait plus
     diagnostiquer → même arbitrage (§3) : journal, plan de suite (§7), et la
     page reste à `en cours`. Une suite qui n'est pas jouable sur le poste (e2e
     sans navigateur, par exemple) se dit au journal, tests nommés — ce n'est
     pas un vert, c'est un trou, et Benjamin doit le voir avant de demander la
     PR.
  2. **Pousser la branche du plan.** C'est le seul push de la clôture quand le
     relevé du §2 a retenu les commits en local ; sans lui, le travail ne vit
     que sur un disque. La sortie de la preuve va au journal (`État final`).
  3. **Ne pas ouvrir la PR.** Ni la merger, ni la préparer « pour gagner du
     temps ». Le compte rendu s'arrête sur la branche, prouvée et poussée.

Un plan laissé à `en cours` raconte que le travail est en suspens alors qu'il est
livré, et c'est la page qui fait foi. Ce statut s'oublie exactement comme la règle
d'entrée s'oublie : en étant absorbé par le travail lui-même. D'où le fait de le
poser dans le tour du compte rendu, pendant qu'on y pense encore.

### La PR, puis la remontée sur `main` — sur demande seulement

Benjamin demande la suite quand il le décide : « ouvre la PR », « merge sur
main », « tu peux merger directement », « pousse ça sur main ». Deux demandes
distinctes, et il faut entendre laquelle est faite :

- **« ouvre la PR »** → une seule PR, de la branche du plan vers `main`, **avec
  le label `review-required` dès la création si le dépôt a des tests e2e**
  (relevé du §2) — toujours, ceinture et bretelles : la suite complète a tourné
  en local à la clôture, le label la fait rejouer par la CI. Sur `vahiny`, ce
  label commande aussi le merge par la CI une fois tout vert : y demander la PR,
  c'est demander la remontée, et Benjamin le sait.
- **« merge sur main »** → la PR (ouverte à cette occasion si elle ne l'est
  pas), CI verte, merge, vérification sur pièce, `execute`.

La séquence complète — ouvrir, attendre la CI, vérifier que le merge a bien eu
lieu, poser `Statut` = `execute`, journaliser — et le piège qui la fait échouer
(le point qui saute le plus souvent : le statut, oublié une fois le merge fait)
vivent dans un fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/remontee-sur-main.md`

**À lire à chaque demande**, que ce soit avant l'exécution, en cours de route,
ou une session plus tard sur un plan déjà à `a merger` : c'est la seule
opération de ce skill qui peut arriver à trois moments différents, et qui a déjà
été bâclée en s'arrêtant au merge sans mettre `Statut` à jour. Une demande
explicite se fait **sans réclamer de confirmation supplémentaire** : refuser au
nom d'une règle qui n'existait que pour le protéger, c'est prendre la règle pour
une fin.

## 7. Le plan de suite, quand tout n'est pas passé

Une exécution autonome se termine parfois avec des étapes en échec, des étapes
sautées faute de dépendance, ou une décision qui attend Benjamin. **Dans ce cas
— et dans ce cas seulement — créer un plan de suite.** La forme de la page
(titre suffixé, propriétés, chapitre `Reprise du plan #N-1`, sort de la
`Branche`, lien entre les deux pages) vit dans un fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md`

**À lire au moment de la clôture**, dès qu'il reste quelque chose que
l'autonomie a mis de côté. Ne pas créer de plan de suite quand tout est passé :
une page vide de contenu utile encombre la base et fait douter du statut de
celle qui la précède.

## 8. Ce que ce skill ne fait pas

- Il ne **conçoit** pas le plan — c'est `plan-notion`. Il **tient à jour** le
  chapitre `Exécution` : à l'entrée pour y répercuter les dernières réponses de
  Benjamin (§2), et en cours de route pour les écarts datés (§4). Mettre à jour
  n'est pas concevoir ; si l'approche est en cause, la main repasse à
  `plan-notion`.
- Il crée une seule page de sa propre initiative : le **plan de suite `#N+1`** en
  clôture (§7), qui repart ensuite en `plan-notion` comme n'importe quel brouillon.
- Il ne code pas si le statut n'est pas `valide`.
- Il n'écrit pas lui-même le code des étapes déléguables : ça part en sous-agent
  `general-purpose` **Sonnet 5** (§3). Piloter, ce n'est pas coder.
- Il n'ouvre **aucune PR de sa propre initiative** — ni d'étape, ni de
  clôture (§6). L'exécution s'arrête à la branche du plan, prouvée en local et
  poussée. Chaque PR est un run de CI, et le quota GitHub Actions est la
  contrainte qui a fixé cette règle (§2) ; la remontée vers `main` est un geste
  vers l'extérieur, et c'est Benjamin qui en décide le moment.
- Il ouvre **la** PR du plan — une seule, de la branche vers `main` — **quand
  Benjamin la demande**, avec `review-required` si le dépôt a des tests e2e ;
  il merge sur `main` **quand Benjamin le demande** — et pose alors `execute`
  dans le même tour, une fois le merge vérifié (§6). Là où la CI du dépôt merge
  seule la PR (`vahiny` sur `review-required`), il **vérifie** le merge et pose
  `execute` ; il ne merge rien de sa propre initiative.
- Il ne pose jamais `execute` sur un travail qui n'est pas sur `main` — ni ne
  laisse `a merger` sur un travail qui y est déjà (§6).
- Il ne s'arrête pas entre deux étapes pour demander l'autorisation de continuer
  (§3).
- Il ne passe jamais un plan en `archive`.
- Il ne résout pas les fils de commentaires.
- Il ne dépend d'aucun `CLAUDE.md`, d'aucun hook, d'aucun fichier du dépôt de
  travail. Ses compagnons sont les fichiers partagés
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`,
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/remontee-sur-main.md` et
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/plan-de-suite.md`, livrés par le
  plugin `plans-notion` — pas par le dépôt de travail, quel qu'il soit.
