## Questions ouvertes
### ✅ Q1 — Quand le banc d'évals se lance en CI
<callout icon="✅" color="green_bg">
	**Quand la CI joue-t-elle les évals d'une PR ?** → **À la demande : label ****`evals`****, sinon ****`Evals: aucun — <raison>`**** (ta réponse du 2026-10-01).** Aujourd'hui, c'est automatique dès qu'un skill est touché, et le banc complet part pour `_partage/` ou `ci.yml`. Un banc complet coûte 55 \$, une catégorie 3 à 14 \$.
	- [x] (reco) **À la demande.** La CI ne joue les évals que si la PR porte le label `evals`, posé par toi ou par la session qui ouvre la PR. Une PR qui touche un skill, un agent, un hook ou `_partage/` sans ce label doit porter `Evals: aucun — <raison>` dans son corps, sinon la CI est rouge : le refus n'est jamais silencieux. Avec le label, la ligne `Evals: <catégories>` choisit les cas, comme aujourd'hui.
	- [ ] Automatique mais ciblé : plus de banc complet pour `_partage/` ni pour `ci.yml`, et des catégories toujours obligatoires. On compte alors 5 à 15 \$ par PR qui touche un skill.
	- [ ] Seulement sur la dernière PR d'un plan, les PR intermédiaires n'en jouant aucune.
	- [ ] Autre / complément →
</callout>
### ✅ Q2 — Un seul banc à la fois
<callout icon="✅" color="green_bg">
	**Comment empêcher deux bancs simultanés ?** → **Un verrou global par plugin en CI, et le lanceur local qui refuse pendant un banc CI (ta réponse du 2026-10-01).**
	- [x] (reco) **Un verrou global par plugin en CI.** Le groupe de concurrence devient `evals-<plugin>`, sans annulation : un second banc attend la fin du premier. Côté local, le lanceur refuse de démarrer tant qu'un job « Évals » tourne en CI (étape 10). Limite de GitHub : un seul run peut attendre ; un troisième annule celui qui attendait, et il faudra alors reposer le label.
	- [ ] Le verrou CI seulement ; le local reste libre.
	- [ ] Rien : on compte sur l'attention de chacun.
	- [ ] Autre / complément →
</callout>
### ✅ Q3 — Réutiliser la base
<callout icon="✅" color="green_bg">
	**Comment ne plus rejouer une version déjà mesurée ?** → **Une clé par contenu, réutilisable par cas (ta réponse du 2026-10-01).**
	- [x] (reco) **Une clé par contenu, réutilisable par cas.** La clé porte l'empreinte du dossier `plugins/<plugin>` à la base, et plus le SHA de `main` : un merge de doc ne l'invalide plus. Si une base complète existe pour cette empreinte, une PR ciblée en extrait ses cas au lieu de les rejouer. Sinon, la base ne joue que les cas choisis.
	- [ ] Une clé par contenu, pour toute la sélection seulement. C'est plus simple, mais une PR ciblée rejoue sa base.
	- [ ] Garder la clé par SHA.
	- [ ] Autre / complément →
</callout>
### ✅ Q4 — Passages par cas
<callout icon="✅" color="green_bg">
	**Garder 3 passages par cas ?** → **Garder 3 passages par cas (ta réponse du 2026-10-01).**
	- [x] (reco) **Garder 3.** Passer à 2 retire un tiers du coût d'un banc, mais le bruit mesuré (rms 0,046 sur Sonnet, run 36746172325) ne vaut que pour 3 passages. Il faudrait le remesurer (une A/A, \~55 \$) et accepter un seuil plus large. Les questions Q1 et Q3 coupent déjà bien plus.
	- [ ] Passer à 2 et remesurer le bruit.
	- [ ] Autre / complément →
</callout>
### ✅ Q5 — Plafond et coût annoncé
<callout icon="✅" color="green_bg">
	**Comment borner un run ?** → **Annoncer le coût avant (****`--estimer`****), puis plafonner à 35 \$ par bras (ta réponse du 2026-10-01).**
	- [x] (reco) **Annoncer, puis plafonner.** `evals_ab.py --estimer` donne le coût prévu avant de lancer, d'après le coût par cas des derniers rapports, et la CI l'écrit en tête du résumé. Le plafond passe de 120 \$ à 35 \$ par bras (un bras complet coûte 27,53 \$ sur Sonnet). Le mode A/A affiche enfin son coût.
	- [ ] Garder 120 \$, et seulement annoncer le coût.
	- [ ] Ajouter un budget hebdomadaire global, qui demande un état partagé entre les runs (fichier ou variable du dépôt).
	- [ ] Autre / complément →
</callout>
### ✅ Q6 — Le rejeu réel
<callout icon="✅" color="green_bg">
	**Quand rejouer de vrais cas passés ?** Un rejeu coûte ≈ 3,30 \$, un juge ≈ 0,75 \$. Le rejeu du lot B a coûté 69 \$, pour un écart de + 1,9 point, resté sous le bruit. → **Seulement sur ta demande explicite, coût annoncé ; C6 du plan #2 sans rejeu local (ta réponse du 2026-10-01).**
	- [x] (reco) **Seulement sur ta demande explicite**, avec le coût annoncé avant de lancer (nombre de rejeux × 3,30 \$, plus les juges), et un seul tirage par défaut. Conséquence : l'étape C6 du plan #2 ne rejoue plus le banc de non-régression en local ; son A/B se fait en CI, ciblé sur les catégories que le lot C touche.
	- [ ] À chaque version mineure de `plans-notion`, un seul tirage.
	- [ ] L'abandonner : le banc d'évals suffit.
	- [ ] Autre / complément →
</callout>
### ✅ Q7 — Un skill d'évaluation ?
<callout icon="✅" color="green_bg">
	**Faut-il un skill pour lancer une évaluation ?** Mise à l'épreuve demandée face à l'existant d'Anthropic. `claude plugin eval` ne fait ni A/B entre versions, ni cache, ni verrou, ni estimation de coût avant run. `skill-creator` fait de l'A/B, mais en session interactive et dans un autre format, et ses sous-agents consomment l'abonnement de la même façon. Ce qui manque, ce sont des garde-fous, et un skill n'en est pas un : c'est une consigne qu'un modèle lit, et la CI d'hier aurait tourné de la même façon avec lui. → **Pas de skill d'évaluation pour l'instant (ta réponse du 2026-10-01).**
	- [x] (reco) **Pas de skill pour l'instant.** La porte d'entrée est le script : `evals_ab.py --estimer`, le verrou (Q2) et le jeton machine (Q9) refusent ou annoncent d'eux-mêmes. Une section « Lancer une évaluation » de `docs/tester-un-skill.md` dit le geste. On reparle d'un skill si une session se trompe encore de geste après ce plan.
	- [ ] Un skill mince, `evaluer-un-plugin` dans `methode-de-travail`, qui appelle ces scripts et demande ton accord avec le coût annoncé.
	- [ ] Adopter `skill-creator` pour les comparaisons ponctuelles, en gardant `plugin eval` pour la CI.
	- [ ] Autre / complément →
</callout>
### ✅ Q8 — Où vit le contrôle de la machine
<callout icon="✅" color="green_bg">
	**Script, consigne ou hook ?** → **Un script du plugin (****`etat-machine.py`****) et une règle courte (ta réponse du 2026-10-01).**
	- [x] (reco) **Un script du plugin et une règle courte.** `_partage/scripts/etat-machine.py` (Python sans dépendance, testé) lit la machine, rend `libre`, `chargée` ou `saturée` avec les causes, et gère le jeton des actions lourdes. Le skill d'exécution dit quand l'appeler et quoi faire selon la réponse. Le script lit du Linux générique ; en session cloud, sans VPS, il répond simplement sur la machine où il tourne.
	- [ ] Tout en consignes : la session lit `/proc` elle-même. C'est moins de code, mais un geste différent à chaque fois.
	- [ ] Un hook `PreToolUse` qui bloque une commande lourde sans jeton. C'est plus sûr, mais il faut reconnaître une commande lourde par motif, et ça casse facilement.
	- [ ] Autre / complément →
</callout>
### ✅ Q9 — Combien d'actions lourdes en même temps
<callout icon="✅" color="green_bg">
	**Combien d'actions lourdes en même temps sur la machine ?** → **Un seul jeton lourd : le POC dit « limite », et ta règle ramène alors à 1 (POC du 2026-10-01).** Sont lourdes : une suite complète, des e2e ou un navigateur, des évals locales, un rejeu, un build ou un conteneur, et une PR sur `hermes-custom` (son runner tourne sur le VPS).
	- [ ] (reco) **Un seul jeton lourd, plus le relevé.** Une action lourde ne part que si elle obtient le jeton **et** que le relevé dit `libre`. Seuils proposés : `saturée` si la pression mémoire « full » sur 60 s atteint 40 (seuil du chien de garde), ou s'il reste moins de 1,5 Go disponibles ; `chargée` si la charge moyenne dépasse le nombre de cœurs, si la pression CPU « some » sur 60 s atteint 50, ou si une famille lourde tourne déjà. Les deux incidents datés venaient de trois charges simultanées sur 6 cœurs.
	- [x] Deux jetons lourds.
	- [ ] Pas de jeton, le relevé seul.
	- [x] Autre / complément → lance un POC et on rebascule à 1 si ça sature ou que c’est limite
	*Résultat du POC, 2026-10-01.* Deux vraies actions lourdes, jouées d'abord seules puis ensemble. A, ce sont les e2e Playwright de `vahiny` (52 tests) ; B, la suite de `hermes-custom` (2 398 tests). Seules, les deux sont vertes, en 209 s et 366 s. Ensemble, **l'e2e tombe** : 1 test sur 52 échoue sur un timeout de 30 s. La suite passe, mais en **484 s, soit + 32 %**, avec une charge jusqu'à 23,8 sur 6 cœurs. La mémoire n'a jamais approché un seuil. Ça ne sature donc pas, mais un test qui casse sous la charge, c'est « limite » : **un jeton**. Le nombre de places reste une constante (étape 8), et passer à 2 un jour ne demandera que de changer une ligne. Détail dans « La machine ».
</callout>
### ✅ Q10 — Une session qui trouve la machine occupée
<callout icon="✅" color="green_bg">
	**Que fait une session quand le relevé dit ****`chargée`**** ou que le jeton est pris ?** → **Annoncer, attendre par paliers de 2 min en avançant le léger, 30 min au plus (ta réponse du 2026-10-01).**
	- [x] (reco) **Elle annonce, attend par paliers et continue le léger.** Annoncer : `ListAgents`, filtré sur les sessions de la machine à l'état `busy`, puis un `SendMessage` court (« je dois lancer \<action\> pour \<plan\>, durée estimée \<n\> min ; préviens-moi si tu lances une action lourde »). Attendre : nouveau relevé toutes les 2 min ; pendant ce temps, elle avance les étapes qui ne chargent pas la machine. Au-delà de 30 min, elle le note au journal et te le dit, sans forcer. Sur `saturée`, elle n'attend pas en boucle : elle te prévient tout de suite.
	- [ ] Attendre en silence, sans message.
	- [ ] Te demander à chaque fois.
	- [ ] Autre / complément →
</callout>
### ✅ Q11 — Les preuves ciblées des sous-agents
<callout icon="✅" color="green_bg">
	**Une preuve d'étape lancée par un ****`executant`**** compte-t-elle comme lourde ?** → **Non, sauf navigateur, conteneur ou plus de 2 min (ta réponse du 2026-10-01).**
	- [x] (reco) **Non, sauf si elle lance un navigateur, un conteneur, ou dure plus de 2 min.** Les preuves ciblées sont légères (342 tests en 16 s ici). Les rendre lourdes sérialiserait toutes les vagues. Le pilote garde pour lui la suite complète et les e2e de la clôture, qui, elles, prennent le jeton.
	- [ ] Oui : toute commande de test prend le jeton.
	- [ ] Autre / complément →
</callout>
### ✅ Q12 — Un test de fumée systématique
<callout icon="✅" color="green_bg">
	**Faut-il un test de comportement bon marché sur chaque PR qui touche un skill ?** Ta question du 2026-10-01 : « quid d'un plugin anthropic qu'on pourrait jouer systématiquement à moindre coût ». Aucun outil d'Anthropic ne teste le comportement sans jouer de sessions (contraintes, « Le test de fumée, mesuré »). Q12 s'ajoute à Q1 sans la remplacer : Q1 dit quand jouer l'A/B complet, Q12 ce qui tourne quand on ne le joue pas. → **Fumée ciblée, sur Sonnet (ta réponse du 2026-10-01).**
	- [x] (reco) **Fumée ciblée, sur Sonnet.** Toute PR qui touche un skill, un agent, un hook ou `_partage/` joue la tête seule, en un passage, sur les catégories qui exercent les fichiers touchés. Ces catégories sont calculées par `evals_selection.py`, pas choisies ; tout le banc part pour `_partage/` et les hooks. Coût : 0,54 à 2,38 \$ par catégorie, ≈ 9,2 \$ au plus. La CI est rouge si une session plante ou si une catégorie passe sous son plancher. Le label `evals` remplace la fumée par l'A/B. Un rouge à tort se relance une fois ; au second rouge, on pose `evals`.
	- [ ] Fumée sur Haiku 4.5, à moitié prix (≈ 4,6 \$ au plus). Ses planchers ne sont pas mesurés : il faudrait d'abord une A/A sur Haiku. Et nos skills sont écrits pour Opus et Sonnet : risque de faux rouges.
	- [ ] Fumée, plus le test de déclenchement de `skill-creator` (`run_eval.py`) quand une PR change la `description` d'un skill. Il faut écrire un jeu de requêtes par skill (une étape de plus).
	- [ ] Pas de fumée : Q1 seule.
	- [ ] Autre / complément →
</callout>
### ✅ Q13 — Le lot C du plan #2 : même PR ou PR suivante ? {color="blue"}
<callout icon="✅" color="green_bg">
	**Comment livrer l'allègement (ex-lot C) dans ce plan ?** <span color="blue">→ </span><span color="blue">**Deux lots, deux PR en série (ta réponse du 2026-10-01).**</span> Il restructure les deux `SKILL.md`, et sa preuve est une non-régression sur tout le banc. Ce plan ajoute des règles aux mêmes fichiers (étapes 5, 9 et 14).
	- [x] (reco) **Deux lots, deux PR en série.** Le lot 1 (étapes 1 à 15) donne la 0.18.0, PR, `merge-auto`. Le lot 2 (étapes 16 à 21) part ensuite de `main` et donne la 0.19.0. Un recul vu par l'A/B du lot 2 s'attribue à l'allègement seul, et la CI du lot 2 profite déjà des évals sobres du lot 1. Coût des évals : ≈ 14 \$ pour le lot 1, ≈ 55 \$ pour le lot 2 (A/B `tout`, la base jouée une fois). C'est la règle que le plan #2 s'était donnée : « C se prouve par la non-régression sur B ».
	- [ ] Une seule branche et une seule PR (0.18.0) : ≈ 14 \$ de moins et un cycle de CI en moins, mais un recul ne dit plus s'il vient des nouvelles règles ou de l'allègement.
	- [ ] Laisser le lot C au plan #2, qui reste ouvert et passe en 0.19.0 après ce plan. C'était l'état d'avant ta demande.
	- [ ] Autre / complément → 
</callout>
### ✅ Q14 — Adoucir les majuscules (ex-C5) {color="blue"}
<callout icon="✅" color="green_bg">
	**Que faire de la piste « moins de majuscules et de ⚠️ » ?** <span color="blue">→ </span><span color="blue">**La sortir du plan, dans « La suite » (ta réponse du 2026-10-01).**</span> Le plan #2 la gardait « uniquement si l'A/B le permet », avec une A/B de ce seul commit. C'est une piste des blogs (les modèles récents sur-réagissent à l'insistance), pas un fait mesuré chez nous.
	- [x] (reco) **La sortir du plan**, dans « La suite ». Elle coûterait un banc complet à part (≈ 55 \$) pour un gain non mesuré, et la mélanger à l'allègement rendrait un recul indéchiffrable. L'étape 20 garde le reste de C5 : un seul vocabulaire (« pilote ») et des sorties de test bornées.
	- [ ] La garder en commit à part, avec sa propre A/B en CI (label `evals`, `Evals: tout`), ≈ 55 \$.
	- [ ] La mêler à l'allègement, sans A/B séparée.
	- [ ] Autre / complément →
</callout>
## La suite
