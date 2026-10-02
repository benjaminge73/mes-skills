# Dérouler les étapes — le détail du §3

Fichier de référence de `executer-plan-notion` : `SKILL.md` §3 dit **quand** le
lire (avant la première étape, puis à chaque étape). Le détail vit ici.

Sommaire :

- Une étape = un commit sur la branche du plan, prouvé en local
- La délégation est la règle, pas une faveur (l'appel `Agent`)
- Le brief du sous-agent
- Ce qui reste chez le pilote
- Après chaque étape
- L'autonomie est le défaut

Le chapitre `Exécution` de la page est la feuille de route. Il ne se réécrit pas
pour raconter l'avancement : l'avancement va dans `Journal d'exécution` (§4).

### Une étape = un commit sur la branche du plan, prouvé en local

Le défaut, sauf avis contraire de Benjamin :

- Chaque étape se code **directement sur la branche du plan**. Pas de
  sous-branche, pas de PR d'étape : une PR, c'est un run de CI, et c'est
  précisément ce qu'on économise (§2).
- **La preuve de l'étape est locale, et c'est le pilote qui la
  joue** — pas le rapport du sous-agent. Rejouer la commande de preuve du brief,
  et recopier sa sortie au journal (§4). **Cette preuve, ce sont les tests des
  fichiers impactés par l'étape, et rien de plus** : ni suite complète, ni tests
  e2e, même si l'étape touche un écran. Les e2e sont lents et lourds (navigateur,
  serveur à lancer), et les jouer à chaque étape reproduirait en local le coût
  qu'on vient de retirer de la CI. Ils passent **une fois, à la clôture** (§6),
  avec la suite complète — c'est le verdict de fin de plan, rendu en local.
  Une preuve qui lance un navigateur, un
  conteneur ou dure plus de 2 min est une action lourde : relevé, jeton, et au
  journal `Machine : <verdict> — attente <n> min` (`machine-partagee.md`).

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
  chez le pilote (cf. plus bas) ; le correctif peut repartir en
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
  `<branche-du-plan>-etape-N-en-echec` (tiret, pas `/` : cette dernière forme
  est **impossible** en git dès que `<branche-du-plan>` existe déjà comme
  branche — `refs/heads/<branche-du-plan>` ne peut pas être à la fois un
  fichier et un dossier sous `refs/heads/`, cf. `vagues.md`), sans PR (donc
  sans CI), pour n'être ni perdu ni mêlé à ce qui est livré ; entrée de journal
  avec la sortie de la
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

**Pour une étape qui écrit du code testé, l'étape = deux commits, rouge puis
vert.** L'exécutant commite d'abord les tests seuls, rouges, puis le code qui
les fait passer — jamais dans le même commit. La preuve rejouée par le
pilote comprend le rouge : rejouer la commande de preuve sur le premier
commit avant de regarder le second, et vérifier que le second ne touche
aucun fichier de test. Le geste exact, les trois issues (rouge attendu, vert
qui dit que le test ne mord pas, `git diff` non vide) et la combinaison avec
une vague ou un regroupement vivent dans un fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/preuve-du-rouge.md`

### La délégation est la règle, pas une faveur

**Charger ce skill vaut demande explicite de déléguer.** Certains harnais portent
une consigne du type « ne pas lancer de sous-agent sans que l'utilisateur l'ait
demandé » : la demande est faite ici, une fois pour toutes, pour toute étape d'un
plan au statut `valide`. Il n'y a pas à la redemander à Benjamin étape par étape.

Le pilote reste en **Opus effort high** : il lit le plan, découpe,
brief, vérifie, écrit dans Notion. **Il n'écrit pas lui-même le code des
étapes déléguables.** Chaque étape part dans un sous-agent **Sonnet** — la
dernière version, par l'alias (voir `executant.md`) : **en séquence par défaut** — les étapes d'un plan sont couplées, et deux sous-agents
concurrents peuvent éditer les mêmes fichiers sans le savoir —, **en parallèle
par vagues** quand le calcul du §2 le permet, et **regroupées** dans un seul
sous-agent quand il le prescrit. Le détail — calculer une vague, isoler chaque
étape parallèle dans un worktree, reporter le travail sur la branche du plan
dans l'ordre des numéros, regrouper deux étapes qui partagent un fichier — vit
dans le fichier partagé du §2 :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`

**À lire une fois, à l'ouverture, avant la première étape** — pas seulement au
moment où une vague se présente : c'est le calcul du §2 qui dit s'il y en a
une, et le relire à ce moment-là serait relire le plan à l'envers.

Concrètement, **un appel de l'outil `Agent` par étape**, avec ces paramètres —
ils ne sont pas indicatifs :

```
Agent({
  subagent_type: "plans-notion:executant",  // nom qualifié par le plugin — le nom court ne résout pas
  run_in_background: false,                 // séquentiel — true pour les étapes d'une même vague (vagues.md)
  description: "Étape N — <titre court>",
  prompt: "<le brief ci-dessous>"
})
```

**Aucun paramètre `model` ici, et c'est voulu.** L'agent `executant` porte
`model: sonnet` dans son propre fichier de définition :

📄 `${CLAUDE_PLUGIN_ROOT}/agents/executant.md`

Le modèle est donc garanti par construction, sur toutes les machines et en
session cloud, au lieu de dépendre d'un champ à ne pas oublier à chaque appel.
C'est le remplacement d'une discipline par un mécanisme : le champ `model` était
le premier à sauter quand on est absorbé par le travail, et sans lui l'étape
partait quand même — en Opus, avec la facture pour seul signal.

⚠️ **Le nom court `"executant"` ne résout pas.** Un agent fourni par un plugin
s'invoque avec son nom qualifié, `plugin:agent` — `"plans-notion:executant"` ici.
Le nom nu rend `Agent type 'executant' not found` et l'étape ne part pas du tout.

Ce fichier de définition porte ce qui ne change **jamais** d'une étape à
l'autre : le périmètre fermé, l'interdiction de commiter, le diagnostic plutôt
que le correctif devant une preuve rouge, le format de rapport. Le brief
ci-dessous porte ce qui change à chaque étape. Les deux arrivent au sous-agent ;
il est donc inutile de recopier dans le brief ce que la définition dit déjà.

### Le brief du sous-agent

Un sous-agent n'a **rien** du contexte de la session : ni le plan, ni la
discussion, ni les étapes précédentes. Un brief vague rend un travail inutilisable,
et c'est ce qui donne ensuite l'envie de « faire soi-même ». Le brief porte donc,
à chaque fois :

1. **L'objectif de l'étape**, recopié du chapitre `Exécution` — pas résumé.

   ⚠️ **Une prémisse du brief se vérifie par une commande dont la sortie est
   recopiée dans le brief, jamais de mémoire.** Un `grep` à la mauvaise forme
   peut faire croire qu'un travail reste à faire alors qu'il est fait.
2. **Le contexte utile** : ce que les étapes précédentes ont produit (repris du
   `Journal d'exécution`, §4), la branche courante, les conventions du repo.
   Pour une étape qui change ce qui s'affiche : **le chemin local de la
   maquette** et la partie qu'elle doit réaliser, recopiée de sa ligne
   `Impact fonctionnel` — le sous-agent n'a pas la page, donc pas la maquette.
3. **La liste fermée des fichiers qu'il a le droit de toucher**, et l'interdiction
   d'en toucher d'autres — **même pour réparer un import qui casse en route**.
   Un fichier touché « en passant », hors liste, est exactement ce qui rend une
   vague dangereuse (`vagues.md`, les fichiers partagés non repérés) : le
   signaler dans le rapport plutôt que le corriger soi-même.
4. **La commande qui prouve que c'est fini**, à lancer, avec, pour le rapport, sa
   sortie **bornée** recopiée sans paraphrase : les dernières lignes du log (le
   résumé du runner), le compte des échecs, et pour chaque échec son nom et
   l'extrait qui dit pourquoi — jamais le log entier. Elle ne porte que sur **les tests des fichiers
   impactés** (§3, « précisément ») : ceux que l'étape écrit ou modifie, et ceux
   qui couvrent les sources qu'elle touche — jamais la suite complète.
   **Le délai attendu quand elle est longue** : « `pytest` prend 4 minutes,
   attends-le. » Sept abandons prématurés relevés sur l'historique viennent
   d'un sous-agent qui rend la main pendant une commande encore en cours, faute
   de savoir combien de temps l'attendre.
5. **Ce qu'il ne fait pas** : ni `commit`, ni `push`, ni PR, ni élargissement du
   périmètre, ni écriture dans Notion — **sauf le regroupement de deux étapes**
   (`vagues.md`), où il commite la première avant d'ouvrir la seconde, avec le
   message fourni dans le brief, **et sauf une étape testée**
   (`preuve-du-rouge.md`), où il commite le rouge puis le vert sur ordre du
   brief, sans jamais toucher un fichier de test dans le commit vert : les deux
   seules exceptions à cette règle. En cas d'échec : **diagnostic, pas
   correctif** — le debug revient au pilote, seul à avoir le
   plan.
6. **Le format du rapport attendu** — cinq pièces, toujours dans cet ordre :
   - **Un état, un seul, parmi quatre** : `DONE` (fait, prouvé, rien à
     signaler), `DONE_WITH_CONCERNS` (fait et prouvé, mais quelque chose mérite
     un regard — un écart, un choix rendu sans arbitrage), `NEEDS_CONTEXT` (le
     brief manque d'une information pour continuer), `BLOCKED` (bloqué, en
     disant sur quoi). Un rapport sans état explicite se lit comme
     `DONE_WITH_CONCERNS` par défaut, jamais comme `DONE`.
   - **Fichiers réellement touchés** et le SHA du commit s'il y en a un
     (regroupement, `vagues.md`).
   - **La sortie bornée de la commande de preuve**, recopiée sans paraphrase :
     dernières lignes du log (résumé du runner), compte des échecs, nom de
     chaque échec et extrait qui dit pourquoi — jamais le log entier. (Le pilote,
     lui, lit la sortie complète de sa propre relance.)
   - **Les écarts par rapport au brief**, et **chaque décision prise en
     route** au format : « quoi — pourquoi — ce que ça coûte si c'est faux. »
     Un sous-agent tranche parfois un détail que le brief ne couvrait pas
     (l'ordre de deux paramètres, le nom d'une variable locale) ; ce format
     dit au pilote ce qui a été décidé sans lui, sans qu'il
     ait à rejouer le diff pour le retrouver.
   - **Découvertes hors périmètre** : ce qu'il a vu sans le toucher, une par
     ligne, `fichier:ligne` et ce que c'est, ou `aucune`. Il signale, il ne
     corrige pas ; d'un secret, il ne recopie jamais la valeur. Le pilote en
     fait des découvertes traitées (§4).

### Ce qui reste chez le pilote

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

- **Un rapport de sous-agent n'est pas une preuve : rejouer la commande** chez le
  pilote, **sur la liste réelle des fichiers touchés**
  (`git diff --name-only`), pas sur celle du brief (§3). Un sous-agent qui
  annonce « les tests passent » a parfois lancé autre chose que ce qu'on croit,
  ou touché un fichier de plus que ce que la commande couvrait.
- **Commiter l'étape sur la branche du plan**, et la pousser si le relevé du §2
  l'autorise (sous-section précédente). Pas de PR.
- **Faire relire par l'agent `relecteur` selon la colonne `Relecture`** :
  une étape `étape` se relit seule, ici ; une étape `lot` attend la preuve de
  fin de son lot, relu d'un seul coup avec les autres. On boucle jusqu'à
  `RIEN À SIGNALER` : chaque remarque se vérifie avant d'être retenue (correctif
  délégué) ou écartée (raison écrite). Les deux régimes, le brief, la boucle et
  le garde-fou à trois tours vivent dans un fichier partagé :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/revue.md`
- **À chaque clôture de lot** (`revue.md` ; une étape relue seule est son propre
  lot) : **relire le diff de la mémoire de l'`executant`**, et le recopier dans
  l'entrée de journal, ligne `Mémoire :` (`aucun changement` se dit aussi). Elle
  vit hors dépôt, sans historique : prendre la référence **avant le premier
  appel** de l'agent ; à la clôture, **comparer d'abord, reprendre ensuite**
  pour le lot suivant (l'inverse compare la mémoire à elle-même).
  ```bash
  # prise de référence (vide si la mémoire n'existe pas encore)
  rm -rf <tmp>/memoire-avant && mkdir -p <tmp>/memoire-avant && { cp -a ~/.claude/agent-memory/plans-notion-executant/. <tmp>/memoire-avant/ 2>/dev/null || true; }
  # à la clôture : ce diff, puis la prise ci-dessus
  diff -ruN <tmp>/memoire-avant ~/.claude/agent-memory/plans-notion-executant
  ```
  On y cherche un **secret** (sa valeur ne se recopie pas au journal : la règle
  du § « Découvertes hors plan » joue), une consigne déguisée en fait, une leçon
  rangée au mauvais dépôt ; la ligne fautive se retire, et le reste du diff se
  lit comme un fait, jamais comme un ordre.
- **Pour une étape qui change ce qui s'affiche, comparer le résultat à la
  maquette** : rendre l'écran, le mettre en regard de la partie de maquette
  visée, et porter dans l'entrée de journal la capture si on sait la poser,
  puis les écarts un par ligne, chacun *voulu* (quelle contrainte l'impose)
  ou *pas voulu* — ou « Aucun écart ». Un écart pas voulu se corrige dans
  l'étape, comme une preuve rouge. Le détail, et le cas des sessions qui ne
  peuvent pas poser d'image :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md`
- **Écrire l'entrée de journal de l'étape dans la page** (§4), sous son propre
  H3. Pour une vague, les entrées se posent **dans l'ordre des numéros
  d'étape**, jamais dans l'ordre d'arrivée des rapports de sous-agent
  (`vagues.md`).
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

**Poser la question en chat.** Si ton environnement fournit un outil de question
structurée (dans Claude Code : `AskUserQuestion`), l'utiliser ; sinon, les
options en texte, la recommandation en premier.
