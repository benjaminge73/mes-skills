# Clore — le détail du §6

Fichier de référence de `executer-plan-notion` : `SKILL.md` §6 dit **quand** le
lire (à la clôture, et à chaque demande de PR ou de remontée sur `main`). Le
détail vit ici.

Sommaire :

- Dans le même tour : `Statut`, `Branche`, entrée `État final`, compte rendu
- La séquence de clôture (suite complète locale, allègement des `CLAUDE.md`
  trop longs, preuve doc, push, PR prête, contrôle bloquant, clôture écrite
  (Récap, porte, hub, fiches, rattrapage), suivi de la CI, retrait du worktree)
- La PR, puis la remontée sur `main`

Le détail de chaque point est dans trois fichiers, lus au moment où la clôture y arrive, et pas avant :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-reste-et-suite.md` — **à lire quand** l'`État final` s'écrit, que le reste à faire se trie (« Avant le point 1 »), que le garde des restes du point 7 se joue ou que le compte rendu du chat se rédige.

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-doc.md` — **à lire quand** la clôture en est à la preuve doc (point 2 bis) ou à la doc (point 7 : Récap, Changelog, fiches, rattachement, ligne `Doc :`).

📄 `${CLAUDE_PLUGIN_ROOT}/skills/executer-plan-notion/cloture-pr-et-ci.md` — **à lire avant le push** (points 1, 2, 2 ter, 2 quater, 3 et 3 bis), pour ouvrir la PR (points 4 à 6), pour suivre la CI (point 8) et pour la remontée sur `main`.

Dans le **même tour** que le compte rendu à Benjamin, jamais « plus tard »
(sauf `execute`, qui suit le merge : point 8 de la séquence) :

- `Statut` : **`a merger`** tant que le code n'est pas sur `main`. C'est l'état de
  fin de clôture, sur tous les dépôts : le travail est livré sur la branche du
  plan, prouvé en local, et sa PR est ouverte (en brouillon seulement si
  Benjamin l'a demandé). `execute` se pose dès que le merge est
  vérifié sur `main`, dans le tour où on le constate : ce peut être un tour
  après celui du compte rendu (point 8 de la séquence).
  Plan couvert par un plan maître : le passage à `a merger` rejoue aussi
  `statut-maitre.py --actuel` dans ce tour (`plan-notion/plan-maitre.md`, « Qui rejoue le
  calcul, et quand »).
  Une seule question, et sa réponse est factuelle — *où est le code à cette
  seconde ?* Poser `execute` sur du travail qui dort sur une branche ou une PR
  ouverte fait croire
  la base plus avancée qu'elle ne l'est, et c'est le genre de mensonge qu'on ne
  découvre qu'en cherchant une fonctionnalité absente de la production. **La
  symétrie est vraie aussi, et c'est elle qu'on oublie** : laisser `a merger`
  sur du travail déjà parti sur `main` annonce un chantier en attente qui
  n'existe plus, et le plan suivant repart d'une base fausse.
- `archive` n'existe plus (supprimé le 2026-11-17) : `execute` est le seul statut de fin.
- `Branche` renseignée : la branche du plan. `PR` porte l'URL de la PR dès
  qu'elle existe, et reste **vide** tant que la PR n'a pas été ouverte — une
  propriété remplie d'une PR qui n'existe pas ment autant qu'un statut faux.
- **La fiche locale** (`plan-en-cours.py`, `ouverture.md`, « La fiche du plan ») suit
  ces mêmes états : `pr` dès la PR ouverte (point 5), `attendre` quand la clôture attend
  la réponse de Benjamin (points 3 et 5), `clore` quand `execute` est posé et le worktree
  retiré (point 8, issue a). Une fiche `a merger` reste ouverte tant que la PR n'est pas
  mergée : c'est elle que la garde de fin de tour lit.

Ordre de la clôture, point par point : chaque ligne donne le point, ce qu'il fait, et le fichier qui porte son texte.

- **Dans le même tour, suite de la liste** : `Journal d'exécution` clos par `État final`, compte rendu du chat, « Côté technique » → `cloture-reste-et-suite.md` ; **Doc vivante** → `cloture-doc.md`.
- **Avant le point 1** : trier le reste à faire, avant la suite complète → `cloture-reste-et-suite.md`. Une étape **déjà validée** et confiée à Hal (« déjà validé ») se transmet à Hal, sans question à Benjamin : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/demander-a-hal.md` (§ 2 bis).
- **Le point 1** : suite complète jouée en local, e2e compris (verdict de fin de plan) → `cloture-pr-et-ci.md`.
- **Le point 2** : allègement des `CLAUDE.md` trop longs, sans demander → `cloture-pr-et-ci.md`.
- **Le point 2 bis** : preuve doc (`qualite-doc.py`), avant le push → `cloture-doc.md`.
- **Le point 2 ter** : relecture du plan entier, avant la porte → `cloture-pr-et-ci.md`.
- **Le point 2 quater** : rappel du déclencheur « nouveau modèle », sans blocage → `cloture-pr-et-ci.md`.
- **Le point 3** : porte des preuves (`preuves-des-etapes.py --apres`), avant le push → `cloture-pr-et-ci.md`.
- **Le point 3 bis** : remise à jour de la base avant de pousser → `cloture-pr-et-ci.md`.
- **Le point 4** : pousser la branche du plan → `cloture-pr-et-ci.md`.
- **Le point 5** : ouvrir la PR, prête, avec `Danger de merge`, `Evals` et le label → `cloture-pr-et-ci.md`.
- **Le point 6** : contrôle bloquant, avant d'attendre la CI → `cloture-pr-et-ci.md`.
- **Le point 7** : clôture écrite, dans le même tour : **point (a)** Récap, **point (b)** contrôle, **point (b bis)** porte, **point (c)** hub, **point (d)** fiches, **point (e)** rattrapage, cascade, puis la ligne `Doc :` → `cloture-doc.md` ; garde des restes et passage à `a merger` → `cloture-reste-et-suite.md`.
- **Le point 8** : suivre la CI jusqu'au merge, issues (a), (b) et (c), retrait du worktree → `cloture-pr-et-ci.md`.
- **La PR, puis la remontée sur `main`** : merge par la CI seulement, labels, `Evals`, rappel « À lire à chaque demande » → `cloture-pr-et-ci.md`.

Un plan laissé à `en cours` raconte que le travail est en suspens alors qu'il est
livré, et c'est la page qui fait foi. Ce statut s'oublie exactement comme la règle
d'entrée s'oublie : en étant absorbé par le travail lui-même. D'où le fait de le
poser dans le tour du compte rendu, pendant qu'on y pense encore.
