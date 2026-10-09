# L'enquête avant les options — détail

Référence de `plan-notion`, lue **avant d'écrire une question, une option ou une étape**, et avant tout POC ou appel d'outil externe. `SKILL.md` en garde le principe ; ce fichier porte les six gisements et les gestes qui en découlent.

## Sommaire

- Les six gisements (session, plans antérieurs, code, historique, carte, extérieur)
- Vérifier un candidat *use*
- La répétition à blanc et le POC de décision
- Le registre des outils
- Une option qui reporte la décision n'est pas une option

## L'enquête avant les options

Un plan qui découvre à l'exécution ce que le code disait déjà n'a pas planifié : il
a deviné. **Avant d'écrire une question, une option ou une étape, aller chercher ce
qui est déjà su.** Six gisements, du moins cher au plus cher :

1. **La session en cours.** Une mesure faite il y a dix minutes reste vraie. C'est
   la source la plus souvent oubliée, parce qu'on rédige le plan dans la posture de
   celui qui ne sait pas encore — alors qu'on vient de regarder.
2. **Les plans antérieurs du même projet.** La base `Plans Claude` filtrée sur le
   projet, statuts `a merger` et `execute` : leur chapitre `Exécution` porte les
   arbitrages déjà rendus, leur `Journal d'exécution` les mesures déjà prises et les
   surprises déjà rencontrées. Une question qu'un plan précédent a tranchée ne se
   repose pas — on cite la page et on avance. Dans ces journaux, les lignes
   `découverte — trouvable au plan` sont à lire en premier : elles disent, noir sur
   blanc, ce que l'enquête d'un plan précédent a manqué sur ce projet-là.
3. **Le code.** Deux gestes, dans cet ordre : d'abord la **carte de voisinage**,
   dressée par le pilote lui-même (détail ci-dessous) ; puis invoquer l'agent
   **`enqueteur`** (outil `Agent`,
   `subagent_type: "plans-notion:enqueteur"` — le nom qualifié par le plugin,
   le nom court ne résout pas) plutôt que fouiller soi-même : il porte déjà
   les quatorze gestes qui évitent les angles morts de voisinage — couverture de
   l'index, `codebase-memory` en priorité sur la lecture de fichiers entiers,
   `grep` en défaut sur les zones que le graphe exclut, et surtout la
   recherche des **appelants** et pas seulement de la définition, là où se
   cachent la plupart des « découvertes » de l'exécution. Il rend une fiche
   courte et sourcée (`fichier:ligne`, ou la commande jouée et sa réponse),
   prête à recopier dans `Contraintes techniques vérifiées`.

   📄 `${CLAUDE_PLUGIN_ROOT}/agents/enqueteur.md`

   **La carte de voisinage (geste du pilote, avant l'enquêteur).** Quelques appels
   au graphe de code (`codebase-memory`, serveur MCP — « Model Context Protocol », le
   canal par lequel un outil extérieur se branche sur Claude) donnent à l'enquêteur un
   point de départ. Elle se dresse sur `main` : un plan s'écrit avant toute branche.
   - **Outils différés.** Les outils `codebase-memory` ne sont pas chargés au départ :
     un `ToolSearch` est nécessaire avant le premier appel.
   - **Nom de projet exact.** `list_projects`, puis copier le `name` rendu dans le
     paramètre `project` : ce n'est pas le nom court du dépôt, on ne le devine pas.
   - **Couverture.** `check_index_coverage` sur chaque dossier que le plan touche. En
     mode `moderate`, `scripts/` et `docs/` ne sont pas indexés : un dossier non couvert
     va en zone hors graphe, nommée dans la carte, et c'est le pilote qui le dit.
   - **Appels.** `search_graph` pour trouver les symboles ; `trace_path` en
     `direction: inbound` avec `include_tests` pour les appelants et les tests. Trois à
     six appels pour un plan court. Le nombre d'appels grandit avec le nombre
     d'étapes : P2 (2026-10-09) en a pris 57 pour un plan de 24 étapes. La carte se
     borne donc aux symboles des étapes **à risque**, pas à toutes les étapes.
   - **`detect_changes`** seulement si une branche de travail existe déjà.
   - **Dégradation sans bruit.** Serveur MCP absent (banc d'évals, session sans le
     serveur), dépôt non indexé ou worktree : le pilote le dit en une ligne, et le brief
     part **sans carte**.

   **Forme.** Une liste courte, par étape à risque : symbole touché → appelants
   (`fichier:ligne`) → tests qui l'exercent → zones hors graphe à faire vérifier. Une
   ligne que le graphe ne tranche pas (symbole vu, conséquence non vue) s'écrit comme
   **question** pour l'enquêteur, jamais comme fait.

   **Ce qu'on en fait.** La carte part dans le brief de l'enquêteur. Il la vérifie ligne
   à ligne, appelant par appelant (geste 5 de `agents/enqueteur.md`), et cherche ce que le
   graphe ne voit pas (« Ce que le graphe ne voit pas », sous le geste 6). Une fois
   vérifiée, elle entre dans `Contraintes techniques vérifiées`.
4. **L'historique.** `git log` sur les fichiers concernés, PR mergées, tests
   existants. Un comportement qui a déjà été changé l'a été pour une raison, et
   cette raison contraint le plan.
5. **La carte du dépôt.** Engendrée quand un générateur existe — chercher
   `docs/architecture.md`, un script `archi`, une commande `npm run archi` —
   sinon dessinée à la main pendant l'enquête, selon les règles du fichier
   partagé `_partage/schemas.md`. Une carte, même approximative, montre en un
   coup d'œil les blocs et leurs liens là où une liste de fichiers ne montre
   qu'un inventaire à plat.
6. **L'extérieur.** Ce qui existe déjà hors du projet — bibliothèque, outil, skill,
   benchmark, documentation d'un outil — et qu'on s'apprêterait à refaire. Il se
   cherche **avant tout POC** : un POC qui mesure un outil maison alors qu'un outil
   éprouvé existe mesure la mauvaise chose. Invoquer l'agent **`chercheur`** (outil
   `Agent`, `subagent_type: "plans-notion:chercheur"` — le nom qualifié par le
   plugin, comme pour `enqueteur`) : il parcourt le web à la place du
   pilote et ne rend qu'une fiche, un candidat par bloc.

   📄 `${CLAUDE_PLUGIN_ROOT}/agents/chercheur.md`

   La recherche est **obligatoire** dès qu'on crée quelque chose de non propre au
   projet — donc pas pour de la logique métier que seul ce dépôt connaît, mais pour
   tout ce qui ressemble à un problème que d'autres ont eu — et **obligatoire aussi
   pour la documentation de tout outil d'un POC**. Elle se fait **par artefact, pas
   par plan** : avant de chercher, lister ce que les étapes vont **fabriquer** —
   script, banc, **jeu de questions**, jeu de données, gabarit, schéma, outil — et
   chercher l'existant de chacun de ceux qui ne sont pas propres au projet. Un plan
   qui cherche « un banc » sans avoir listé ses artefacts oublie le jeu de questions
   qu'il va écrire à la main, alors qu'un jeu éprouvé existe souvent. Le résultat
   s'écrit dans `Contraintes techniques vérifiées`, sous une ligne qui n'est pas
   facultative, **une par artefact** :
   *« Existant cherché : … / trouvé : … / fait maison parce que … »*.

   Le POC, s'il y en a un, se joue **après** cette recherche, selon « Qui joue le
   POC » du fichier partagé `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md` : le
   mécanique au `sondeur`, le jugement au `general-purpose` en Sonnet, `effort`
   high, passés à l'appel.

Le budget d'enquête est **proportionnel à l'enjeu**, pas à la longueur du plan : une
étape qui touche un fichier et se relit d'un coup d'œil ne mérite pas une fouille
d'historique. Une étape qui change un réglage de production, oui.

**Une vérification nomme la décision qu'elle peut changer, ou le risque qu'elle
couvre — sinon elle ne se fait pas.** Une recherche, une mesure ou un POC dont le
résultat, quel qu'il soit, laisserait le plan tel quel n'est que du bruit : elle
coûte une étape de la passe et n'éclaire rien. Sur un plan `Bounded`, cela donne :
ni `chercheur`, sauf si une étape fabrique un artefact non propre au projet, ni POC,
sauf si une option dépend d'une incertitude mesurable.

### Vérifier un candidat *use*

Le `chercheur` n'a pas Bash : les chiffres qu'il rend sont **lus sur une page web**,
et une page web peut être en cache ou fausse. Quand sa fiche propose un candidat au
verdict *use* (on l'adopte tel quel), le pilote le vérifie lui-même, dans
cet ordre :

1. **Rejouer `gh api repos/<owner>/<name>`** : étoiles, `pushed_at`, contributeurs,
   licence. Jamais un chiffre lu sur une page web ; celui de la fiche n'est qu'une
   proposition.
2. **Lancer l'outil de vérification natif** du type de chose adoptée :
   - un skill ou un plugin → `hermes skills inspect`, puis le verdict du scanner.
     Seul *safe* passe ; *caution* → demander à Benjamin ; *dangerous* → écarté ;
   - un paquet Python → `hermes doctor` ;
   - ailleurs → l'outil de l'écosystème (celui du gestionnaire de paquets du
     candidat), **en disant qu'Hermes n'a pas d'outil natif pour ce cas**.
3. **Écrire le résultat sur la ligne « Existant »** de `Contraintes techniques
   vérifiées` : les chiffres rejoués et le verdict de l'outil.

**Le seuil : un candidat *use* exige au moins 1 000 étoiles ET un outil de
vérification.** En dessous, il est **écarté**, ou **dérogé par écrit** — la
dérogation et sa raison figurent sur la ligne « Existant », et c'est Benjamin qui
la tranche. Un candidat *copy design* (on reprend l'idée, réécrite chez nous) sous
le seuil porte la mention **« idée non éprouvée »**.

### La répétition à blanc et le POC de décision

Deux gestes, qui se font **avant** de passer le plan à `valide` et dont le gabarit
vit dans le fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/poc.md`

- **La répétition à blanc**, systématique : jouer à l'avance, dans un worktree
  détaché sur `origin/main`, ce que le plan écrit — chaque commande de preuve, la
  suite complète du dépôt, un appel d'essai par outil externe, les comptages avec
  le chargeur réel du dépôt. Son résultat va dans `Contraintes techniques
  vérifiées`, sous un intertitre « État de départ ». Un plan `Bounded` n'en joue
  que les deux premiers gestes.
- **Le POC de décision**, **obligatoire dès qu'une option dépend d'une incertitude
  mesurable** — un taux de réussite, un volume réel, un coût d'appel. La mesure ne
  se renvoie donc plus à l'exécution : elle se fait ici, et son résultat
  s'écrit dans le plan. La seule exception est une donnée que **seul le temps
  produit** (voir « Une option qui reporte la décision n'est pas une option »).

Le POC de décision se joue selon « Qui joue le POC » du même fichier partagé :
le mécanique au `sondeur` (`plans-notion:sondeur`), le jugement au
`general-purpose` avec `model: "sonnet"` et `effort: "high"` passés à l'appel. Le
pilote conclut dans le plan, jamais l'agent.

### Le registre des outils

**Avant tout appel d'un outil externe** — pour la répétition à blanc, pour un POC,
ou pour écrire une étape qui lance un lot —, lire le registre : ce que l'outil coûte,
ce qui l'a déjà fait échouer, et quoi faire à la place.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`

Un outil qui n'y a pas de fiche suit la règle du fichier : doc lue par le `chercheur`,
un seul appel d'essai, puis la fiche créée avant tout lot. Les chiffres se lisent au
registre, jamais de mémoire.

### Une option qui reporte la décision n'est pas une option

Le cas type, et la raison d'être de cette section :

> *Option 1 — poser le réglage, laisser tourner une semaine, mesurer les
> chevauchements, puis décider si un patch vaut le coup.*

Ça ressemble à de la prudence. C'en est parfois. Le plus souvent c'est une
**décision non prise**, habillée en méthode — et il arrive que la mesure invoquée
ait déjà été faite, dans la session même, sans que la question ne le sache.

Avant d'écrire une option de cette forme, deux vérifications, dans cet ordre :

1. **La mesure existe-t-elle déjà ?** Session en cours, journal d'un plan antérieur,
   sortie d'outil, tableau de bord. Si oui, la question est tranchée : elle naît
   **verte**, avec la mesure et sa provenance.
2. **La mesure est-elle faisable maintenant ?** S'il ne manque qu'une commande, une
   requête ou une lecture — **la faire pendant la passe de plan**, et écrire la
   réponse. Lire, mesurer, interroger : tout cela est permis avant `valide`, code
   jetable de POC compris (règle 2 de `SKILL.md`). Ce qui reste interdit, c'est le code
   **livré**.

Le report ne reste recevable que dans un cas : **la donnée n'existe pas encore et le
temps est le seul moyen de la produire** — un volume qu'il faut accumuler, un usage
réel qu'il faut observer. Il s'écrit alors comme tel : ce qui sera mesuré, au bout
de combien de temps, et **quel seuil déclenche quelle décision**. Un report sans
seuil n'est pas un plan, c'est un abandon poli.
