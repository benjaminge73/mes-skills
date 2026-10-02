# Le journal, et les écarts — le détail du §4

Fichier de référence de `executer-plan-notion` : `SKILL.md` §4 dit **quand** le
lire (avant d'écrire la première entrée de journal, puis à chaque étape). Le
détail vit ici.

Sommaire :

- Écrire une entrée de journal (titre H3, contenu, écarts)
- Qualifier chaque découverte : trouvable au plan, ou pas
- Découvertes hors plan : chaque trouvaille reçoit un traitement

Après **chaque** étape, écrire dans `Journal d'exécution` — et dans le miroir local
du plan. C'est le briefing du sous-agent suivant, et c'est ce qui permet de
reprendre après un compactage de contexte ou depuis une autre session.

**Le journal s'écrit dans l'ordre des numéros d'étape, pas dans l'ordre
d'arrivée des rapports.** Une vague de plusieurs étapes (`vagues.md`) rend ses
rapports de sous-agent dans un ordre quelconque ; les entrées H3 se posent
malgré tout en suivant N, pour que le journal reste lisible comme la suite du
plan qu'il raconte, pas comme un journal des retours.

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
- les **décisions prises en route**, chacune au format « quoi — pourquoi — ce
  que ça coûte si c'est faux » (§3, « Le format du rapport attendu »), qu'elle
  vienne du sous-agent ou de la session de pilotage elle-même ;
- les **fichiers réellement touchés** ;
- la **preuve** : commande jouée en local, les tests qu'elle couvre — ceux de
  l'étape, ceux des fichiers impactés — et sa sortie ;
- le **commit de l'étape** (SHA court), poussé ou resté local — ou la branche de
  côté où le travail attend, si l'étape est en échec (§3) ;
- **une ligne `Découvertes :` — obligatoire, dans chaque entrée d'étape.** Elle
  vaut `aucune`, ou porte la liste des découvertes, une par ligne, chacune sous
  l'un des libellés de la sous-section suivante, suivi de **son traitement**
  (sous-section d'après). Une entrée sans cette ligne est
  incomplète, même si l'étape n'a rien surpris : c'est le `aucune` écrit qui
  distingue une étape sans surprise d'une étape dont personne n'a rien relevé ;
- pour une étape qui **repose sur un POC** : l'**écart POC / exécution**, au
  format « POC : 8, exécuté : 39 » — ce que la mesure avait annoncé, ce que
  l'exécution a trouvé — avec un renvoi à
  `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md` ;
- le **reste à faire**, s'il en reste, chaque ligne avec son propriétaire (voir « Découvertes hors plan »).

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

Toute découverte notée au journal porte **l'un des trois libellés ci-dessous**
— les deux premiers, plus la variante « sur la page » du cas particulier qui
suit — et jamais aucun autre. Le libellé n'est pas facultatif : c'est lui que la
ligne `Découvertes :` de chaque entrée d'étape (§4) et le contrôle de clôture
(§6) attendent.

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

**Cas particulier, à distinguer explicitement** : quand l'information était
lisible **sur la page du plan elle-même** — une réponse à une question, une
remarque dans le corps, un texte après `Autre / complément →` — le libellé se
précise en `découverte — trouvable au plan — sur la page`. L'enquête préalable
lit le dépôt sans toujours se relire elle-même. Ce libellé-là dit à la prochaine synthèse
combien de fois le manque venait de la page et pas du code.

**Dans le doute, écrire `trouvable`.** Le biais doit pousser vers plus d'enquête, pas
vers l'auto-absolution. Et un libellé posé ne se rétro-classe pas à la clôture,
quand l'étape est réussie et que tout paraît moins grave.

Ce n'est **pas un reproche adressé au plan** — c'est la seule mesure qu'on ait de
sa qualité. Sans ces libellés, on juge au ressenti, et un plan qui découvre tout en
route se défend aussi bien qu'un plan qui n'a rien laissé passer. L'entrée
`État final` (§6) porte donc le décompte en une ligne :
`3 découvertes, dont 1 trouvable au plan` — et zéro sur un plan long se dit aussi,
c'est ce qui signale que l'enquête a fait son travail.

**Le libellé se contrôle mécaniquement à la clôture** (§6), pas de mémoire :

- le **nombre de lignes `Découvertes :`** est égal au nombre d'entrées
  `Étape N` (les entrées `Ouverture` et `État final` n'en portent pas) ;
- **aucune surprise marquée `ÉCART` ou `BLOQUÉ` ne reste sans libellé** : chaque
  ligne ainsi marquée se retrouve, avec son libellé, dans la ligne
  `Découvertes :` de son étape.

### Découvertes hors plan : chaque trouvaille reçoit un traitement

Le libellé ci-dessus mesure le plan (était-ce trouvable ?) ; le traitement dit
**quoi faire** de ce qu'on a vu en route — bug voisin, secret, dépendance
douteuse, doc fausse. Il vient du rapport de l'exécutant (cinquième pièce), du
relecteur ou du pilote. Chaque découverte reçoit **un** traitement, écrit sur sa
ligne `Découvertes :` : jamais « noté pour plus tard » sans propriétaire.

- **Traitée dans le plan** — si elle est à la fois **réversible** (un `git
  revert` la défait), **hors sécurité** et **petite** (une étape, sans revenir
  sur une décision du plan). On ajoute une étape `D<n>` au chapitre `Exécution`
  avec sa correction datée (`_maj 2026-09-30 — D1 : …_`) et sa ligne de tableau ;
  elle part à l'exécutant avec sa liste fermée de fichiers, **dans ses propres
  commits**, est relue (`revue.md`), et se journalise sous `Étape D<n> — …` avec
  sa propre ligne `Découvertes :`.
- **Question à Benjamin** — si elle est **irréversible** (suppression de données
  ou de fichiers non versionnés, écriture dans un service externe ou en
  production, publication, migration, réécriture d'historique, dépense) **ou liée
  à la sécurité** (secret, droits, authentification, exposition réseau,
  dépendance non vérifiée, donnée personnelle) — et aussi quand elle est trop
  grande pour le plan validé. Outil de question natif (§3, « L'autonomie est le
  défaut »), sinon texte, recommandation en premier ; l'exécution continue sur ce
  qui n'en dépend pas. **Question sans réponse à la clôture → plan de suite
  (§7).** Dans le doute entre les deux : la question.

**Un secret découvert ne se corrige jamais seul** : ni suppression, ni rotation,
ni réécriture d'historique, et **sa valeur ne s'écrit nulle part** — ni brief,
ni journal, ni page Notion. On note où il est (`fichier:ligne`) et ce que c'est,
puis la question part tout de suite.
