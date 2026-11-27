# Dérouler les étapes — le détail du §3

Fichier de référence de `executer-plan-notion` : `SKILL.md` §3 dit **quand** le
lire (avant la première étape, puis à chaque étape). Le détail vit ici, sauf le
brief du sous-agent et la suite d'étape (« Après chaque étape »), sortis dans deux
fichiers à part : chaque section sortie garde ici une ligne de renvoi.

Sommaire :

- Une étape = un commit sur la branche du plan, prouvé en local
- La délégation est la règle, pas une faveur (l'appel `Agent`)
- L'escalade bornée
- Le brief du sous-agent → `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/brief-du-sous-agent.md`
- Ce qui reste chez le pilote
- Après chaque étape → `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/apres-chaque-etape.md`
- L'autonomie est le défaut

Le chapitre `Exécution` de la page est la feuille de route. Il ne se réécrit pas
pour raconter l'avancement : l'avancement va dans `Journal d'exécution` (§4).

### Une étape = un commit sur la branche du plan, prouvé en local

Le défaut, sauf avis contraire de Benjamin :

- Chaque étape `lot` se code **directement sur la branche du plan**. Une étape
  `étape` (relue seule) se joue sur sa branche d'étape, dans son worktree, et se
  rapatrie sur la branche du plan (`vagues.md`, « Une étape relue seule »). Pour une
  étape `lot`, pas de sous-branche, pas de PR d'étape : une PR, c'est un run de CI,
  et c'est précisément ce qu'on économise (§2).
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
  commit de l'étape précédente, pas la liste du brief — et elle a trois sources :
  1. **les tests écrits ou modifiés pendant l'étape** : en TDD ce sont eux qui
     définissent l'étape, ils tournent forcément ;
  2. **les tests existants qui couvrent les sources touchées**. Le plus sûr est
     le mode « related » du runner quand il existe — `npx vitest related
     <sources>` (vitest remonte les imports), `npx jest --findRelatedTests
     <sources>`. Sans ce mode (pytest, autres) : la convention de nommage du
     dépôt (`foo.py` → `test_foo.py`, `foo.ts` → `foo.test.ts`) **plus** un
     `grep -l` du nom du module dans les dossiers de tests, pour attraper ceux
     qui l'importent sous un autre nom ;
  3. **les gardes qui lisent les dossiers touchés** : un test qui n'importe pas le
     fichier touché, mais le *lit* (il parcourt un dossier de skills, compte les
     `SKILL.md`), n'est trouvé ni par le nom ni par l'import. On le cherche par le
     chemin : `git grep -l '<dossier ou fichier touché>' -- scripts/ 'plugins/*/tests/*'`,
     et on garde les `test_*.py` ainsi que les `check_*.py` que `scripts/ci_locale.sh`
     joue. Sans cette source, une garde qui lit un dossier modifié ne tombe qu'à la
     clôture (deux défauts du plan précédent y sont passés).

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
  complète de la clôture, ou dans le run de CI de la PR de clôture.
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
  cette suite que sur la PR de clôture — c'est la seconde ceinture,
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

**Une étape testée peut se faire à deux exécutants, enchaînés ; le pilote le décide dans le brief.** Le premier n'écrit que le test et le joue rouge ; le pilote commite ce rouge, puis lance le second avec le SHA de ce commit et la liste des fichiers de test, en lecture seule. Le second exécutant écrit le code qui les fait passer et ne modifie jamais un de ces fichiers ; le pilote vérifie, avant tout commit, que `git diff <sha-rouge> -- <fichiers-de-test>` et `git status --porcelain -- <dossier des tests>` sont vides, puis commite le vert. Raison : celui qui écrit le test et le code peut le faire taire sans le voir ; le second n'a pas écrit le test, et le `git diff` rend toute retouche visible sans avoir à croire personne. Écarté : un agent « testeur » neuf, qui doublerait la définition d'`executant` pour le même geste. Détail du brief dans `preuve-du-rouge.md`, section « Deux exécutants ».

### La délégation est la règle, pas une faveur

**Charger ce skill vaut demande explicite de déléguer.** Certains harnais portent
une consigne du type « ne pas lancer de sous-agent sans que l'utilisateur l'ait
demandé » : la demande est faite ici, une fois pour toutes, pour toute étape d'un
plan au statut `valide`. Il n'y a pas à la redemander à Benjamin étape par étape.

**Une étape d'exécution part toujours à `plans-notion:executant`, jamais à un
`general-purpose`, et un POC non plus.** Un POC part au `plans-notion:sondeur`
(mécanique) ou à `plans-notion:evaluateur` (jugement), jamais à un
`general-purpose`, et sans paramètre `model` à l'appel (sauf une montée de l'escalade
bornée, plus bas) : la définition de l'agent le porte, et un `model` passé à l'appel l'emporte sur elle (« Qui joue le POC »
dans `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`). Raison mesurée : 443
`general-purpose` en Sonnet sur 14 jours, 12,1 % du coût, souvent pour des
étapes. Un `general-purpose` sans `model` hérite du modèle de la session, et
c'est ce coût-là qu'on retire.

Le pilote tourne en **Sonnet effort medium** : il lit le plan, découpe,
brief, vérifie, écrit dans Notion. **Il n'écrit pas lui-même le code des
étapes déléguables.** Chaque étape part dans un sous-agent **Haiku**, par
l'alias (voir `executant.md`) : **en séquence par défaut** — les étapes d'un plan sont couplées, et deux sous-agents
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
  prompt: "<le brief : voir brief-du-sous-agent.md>"
})
```

**Aucun paramètre `model` ni `effort` ici, et c'est voulu : seule la correction `D<n>` d'une boucle de cron passe `model: "sonnet"` (jamais `effort`, renvoi plus bas), et seule une montée de l'escalade bornée (plus bas) passe les deux.** L'agent
`executant` porte `model: haiku` et `effort: high` dans son propre fichier de
définition :

📄 `${CLAUDE_PLUGIN_ROOT}/agents/executant.md`

Le modèle et l'effort sont donc garantis par construction, sur toutes les machines et en
session cloud, au lieu de dépendre d'un champ à ne pas oublier à chaque appel.
C'est le remplacement d'une discipline par un mécanisme : le champ `model` était
le premier à sauter quand on est absorbé par le travail, et sans lui l'étape
partait quand même — en Sonnet, avec la facture pour seul signal. L'`effort`
suit la même logique : le frontmatter le fixe, l'appel ne le répète pas.

Une étape `C<n>` (lancer un cron à la main) se délègue de la même façon, sans `model`.
Elle ne se ferme que sur la sortie d'un lancement réel : « à vérifier à l'heure du
cron » la laisse ouverte (`cron-a-la-main.md`, « Jamais à la prochaine exécution »).
Seule sa correction `D<n>` porte un `model` (`"sonnet"`, diagnostic oblige) : c'est la
seule exception au principe ci-dessus, détaillée dans
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md`.

⚠️ **Le nom court `"executant"` ne résout pas.** Un agent fourni par un plugin
s'invoque avec son nom qualifié, `plugin:agent` — `"plans-notion:executant"` ici.
Le nom nu rend `Agent type 'executant' not found` et l'étape ne part pas du tout.

Ce fichier de définition porte ce qui ne change **jamais** d'une étape à
l'autre : le périmètre fermé, l'interdiction de commiter, le diagnostic plutôt
que le correctif devant une preuve rouge, le format de rapport. Le brief
(`${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/brief-du-sous-agent.md`) porte
ce qui change à chaque étape. Les deux arrivent au sous-agent ;
il est donc inutile de recopier dans le brief ce que la définition dit déjà.

### L'escalade bornée

Une étape qui échoue ne repart pas au hasard : on monte d'un palier, une fois, et si
ça ne suffit pas, Benjamin revoit. Le pilote ne reprend jamais le code lui-même.

1. **D'abord la cause.** Avant toute montée, chercher pourquoi le rapport est
   `NEEDS_CONTEXT`, `BLOCKED` ou une preuve rouge sans cause de code : brief incomplet
   (un fichier, une commande ou un critère manque), environnement (outil absent,
   service coupé), permission refusée. Corriger la cause, puis relancer **au même
   palier** : ce n'est pas une montée, et la relance ne compte pas dans la règle 4.
2. **Sinon, une montée par étape, vers le palier au-dessus.**
   - Un agent Haiku (`executant`, `sondeur`, `enqueteur`, `chercheur`, `lecteur`) : le
     même agent, appelé à nouveau avec `model: "sonnet"` et `effort: "medium"`.
   - Un agent Sonnet qui ne fait pas qu'exécuter (`evaluateur`) : le même agent, appelé
     à nouveau avec `model: "opus"` et `effort: "medium"`.
   - `relecteur` est déjà en Opus : il n'a pas de palier au-dessus, son échec va
     directement à la revue humaine.

   Dans les deux cas, le brief du nouvel appel reprend le rapport du palier précédent :
   ce qui a été tenté, la sortie de la preuve, l'écart constaté. Le frontmatter ne
   change pas ; l'appel le surcharge pour cette fois seulement.
3. **Si ça échoue encore : revue humaine.** L'étape passe à `A revoir` dans le journal,
   avec le dernier rapport et les paliers essayés. Les étapes indépendantes continuent ;
   une étape qui dépend de celle-là attend son retour. Pas de troisième version.
4. **Un essai par palier, jamais deux au même.** Pas de plafond de montées par plan :
   la règle d'arrêt est la revue humaine, pas un compte.
5. **Le contrôle de modèle suit la montée.** Après une montée, le modèle vu n'est plus
   celui du frontmatter : le contrôle « Au premier `executant` » de
   `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/apres-chaque-etape.md`, qui compare
   au frontmatter, ne s'applique pas tel quel. On lit alors les modèles vus, sans
   `--agent` ni `--definition` (`modele-sous-agent.py <agentId>` imprime « n × modèle »,
   code 0), et on vérifie que le modèle vu est celui demandé à l'appel.
6. **Un arrêt par `maxTurns` n'est pas un échec.** Le sous-agent rend alors un résultat
   partiel, marqué comme tel. On le reprend sans repartir de zéro, au même palier :
   soit SendMessage à la même instance, soit un nouvel appel avec le résultat partiel
   dans le brief. Ce n'est pas une montée, et ça ne compte pas dans la règle 4.

### Le brief du sous-agent

Le brief qu'on écrit pour chaque appel `Agent` (ce que le sous-agent doit savoir, sa
liste fermée de fichiers, la commande qui prouve que c'est fini, le format de son
rapport) vit dans son fichier, lu au moment de le rédiger :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/brief-du-sous-agent.md`

### Ce qui reste chez le pilote

La liste est courte, et c'est voulu :

- **Les étapes de jugement** — nommage, formulation d'un message vu par un
  utilisateur, choix d'architecture. Les vérifier coûte le prix de les faire.
- **Le debug** après l'échec d'un sous-agent.
- **Toutes les écritures Notion** (§4, §5) et les opérations git.

La lecture d'un fichier de plus de 200 lignes, d'une sortie de commande ou d'une page
se confie à un agent, pas au pilote :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/lecture-deleguee.md`

Une étape dont on ne sait pas énoncer les trois lignes — le test qui doit passer,
les fichiers autorisés, la commande de preuve — **n'est pas une étape à garder
pour soi : c'est une étape mal spécifiée.** On la précise d'abord (au besoin en
corrigeant le chapitre `Exécution`, §4), puis on la délègue. Se rabattre sur « je
la fais moi-même » est le chemin par lequel un plan entier finit exécuté en Sonnet.

Contrôle de fin de parcours : **une exécution qui se termine sans aucun appel
`Agent` est un défaut**, pas une variante. Le signaler dans le compte rendu (§6)
en disant quelles étapes ont été faites en direct et pourquoi.

### Après chaque étape

Ce que le pilote fait au retour de chaque étape (rejeu de la preuve, périmètre,
verdict, modèle, commit, lecture du diff, fiche, relecture, journal, récap) vit dans
son fichier, lu à chaque retour d'étape :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/apres-chaque-etape.md`

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
  PR de clôture (elle s'ouvre à la clôture, §6) — dont le **correctif serait
  structurant** (il part alors sur une branche de côté, avec son arbitrage au
  plan de suite, §3 et §7), ou qu'on ne sait plus diagnostiquer (§3, plus
  haut) — tant que la correction tient dans l'étape, on corrige et on continue,
  sans rien demander ;
- une décision qui n'est ni dans le plan ni déductible de lui, et qui engage :
  schéma de données, contrat d'API public, suppression de données, dépense ;
- un fil de commentaire non résolu qui contredit l'étape à venir (§1).

Même là, s'arrêter ne veut pas dire attendre les bras ballants : faire **tout ce
qui ne dépend pas** du point bloquant, écrire ce qui bloque au journal, et clore
avec un plan de suite (§7).

**Un geste que seul Benjamin peut faire se consigne dans la page, il ne se poste pas.** Un geste
irréversible, secret, merge ou envoi à un tiers (`demander-a-hal.md`, § 4) ne part dans aucun message
Slack, ni vers Benjamin, ni vers Hal, ni vers `#arbitrage` : la session ajoute une entrée à la section
`## Tes gestes` de la page du plan (quoi, pourquoi, commande ou chemins exacts, étapes débloquées, reco),
en insertion seule, sans réécrire une ligne existante ni doubler un geste déjà consigné. Elle écrit
l'étape bloquée au journal, **continue tout ce qui n'en dépend pas**, et ne s'arrête pas pour attendre.
Quand il ne reste que des étapes bloquées par ces gestes, elle clôt le plan et crée le plan de suite
(`plan-de-suite.md`, « Un plan bloqué par les seuls gestes de Benjamin »). Benjamin traite ses gestes
en une fois, depuis la page.

**Avant de s'arrêter pour Benjamin, demander à Hal.** Une question qu'il a déjà
tranchée dans sa mémoire, ou un geste que la session ne peut pas tenir (commande
longue, interactive, dans tmux), se pose d'abord à Hal :
`${CLAUDE_PLUGIN_ROOT}/skills/_partage/demander-a-hal.md`. Un geste irréversible
reste à Benjamin, sauf la dépense **déjà validée** dans le plan (case cochée, plafond
écrit) : une étape déjà validée et confiée à Hal se transmet sans « go », par le § 2 bis du
même fichier, et un dépassement de ce plafond reste à Benjamin.

**Poser la question en chat.** Si ton environnement fournit un outil de question
structurée (dans Claude Code : `AskUserQuestion`), l'utiliser ; sinon, les
options en texte, la recommandation en premier.
