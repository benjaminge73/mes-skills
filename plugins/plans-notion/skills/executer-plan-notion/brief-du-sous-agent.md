# Le brief du sous-agent — le détail de `etapes.md`

Ce fichier porte ce que le pilote écrit pour chaque appel `Agent`, et ce que le
sous-agent rend en retour. Il se lit au moment de rédiger le brief d'une étape. Il
est sorti du chapitre « La délégation » de `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`,
qui garde le renvoi.

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
   impactés** (`${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/etapes.md`, « précisément ») : ceux que l'étape écrit ou modifie, ceux
   qui couvrent les sources qu'elle touche, et les gardes qui lisent ses dossiers —
   jamais la suite complète.
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

   **Le trailer, quand il commite** (regroupement ou étape testée) : la dernière
   ligne du message est exactement `Co-Authored-By: Claude <noreply@anthropic.com>`.
   Pas de nom de modèle, ni dans le trailer ni ailleurs dans le message : le rappel
   d'attribution du harnais en suggère un, et la règle du poste l'interdit. Le pilote
   vérifie la ligne à la relecture du commit (`${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/apres-chaque-etape.md`, « Après chaque étape »).
6. **Le format du rapport attendu** — cinq pièces, toujours dans cet ordre :
   - **Un état, un seul, parmi quatre** : `DONE` (fait, prouvé, rien à
     signaler), `DONE_WITH_CONCERNS` (fait et prouvé, mais quelque chose mérite
     un regard — un écart, un choix rendu sans arbitrage), `NEEDS_CONTEXT` (le
     brief manque d'une information pour continuer), `BLOCKED` (bloqué, en
     disant sur quoi). Un rapport sans état explicite se lit comme
     `DONE_WITH_CONCERNS` par défaut, jamais comme `DONE`.
   - **Fichiers réellement touchés** et le SHA du commit s'il y en a un
     (regroupement, `vagues.md`).
   - **La liste cochée de l'étape** : une case par champ, en puce `- **Champ** : valeur` dans le brief, rendue `- [x] <champ> — preuve : …` (`skills/_partage/listes/rapport-executant.md`). Pour « Preuve de fin » : sortie bornée, jamais le log entier.
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

Ce que le code dit déjà ne se recopie pas dans le brief : on donne le chemin et la ligne à lire, pas un extrait. Le texte du brief reste à ce que le code ne dit pas : l'intention, la contrainte, la preuve.
