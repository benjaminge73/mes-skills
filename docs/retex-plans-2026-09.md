# Rétex — 77 plans Notion (2026-08-02 → 2026-09-08)

Date : 2026-09-08

Ce document rassemble, pour qu'elle vive dans le dépôt et pas seulement dans
une page Notion, la synthèse d'un dépouillement complet de la base Notion
« Plans Claude ». Il est pensé pour être lu seul, sans avoir la page Notion
sous les yeux.

## Méthode

80 pages de plans terminés (statut `a merger`, `execute` ou `archive`) ont été
lues **en entier**, chacune par un sous-agent, répartie sur huit sous-agents
en parallèle qui suivaient un gabarit commun (titre, dates, statut, nombre
d'étapes, découvertes notées « trouvable au plan » / « pas trouvable »,
parallélisation exploitée ou non, présence d'un plan de suite, présence de
schémas, citations de Benjamin). 3 doublons ont été retirés en synthèse
(« GH Actions bloqué par la facturation », « Refonte vps-resource-governance »,
« Garde nocturne : débit #2 »), ce qui laisse **77 plans uniques**.

⚠️ La convention « découverte — trouvable au plan » n'existe pas avant le
2026-08-21 (introduite avec le plan « Séquencement, durée et hygiène des
crons »). Sur les 40 plans antérieurs à cette date, les fiches de lecture ont
dû **reclasser des équivalents** — ces cas sont notés `(recl.)` dans le
tableau et exclus des chiffres agrégés ci-dessous.

## Chiffres clés

- **34/77 (44 %)** des plans portent une ligne « N découvertes, dont M
  trouvables » ; aucun plan antérieur au 2026-08-21 n'en porte.
- **215 découvertes** notées aux journaux d'exécution, dont **169 « trouvables
  au plan »** (78,6 %) et **46 « pas trouvables »** (21,4 %).
- **Parallélisation** : 56/77 (73 %) des plans ont au moins une paire
  d'étapes à fichiers disjoints sans dépendance ; seuls 5 (6,5 %) l'ont
  exploitée au niveau des étapes elles-mêmes (VPS #6, Chantier A #4, A #5,
  A #8, Vercel e2e #1) ; 6 autres ont parallélisé des lots à l'intérieur
  d'une même étape.
- **Plans de suite** : 36/77 (47 %) — périmètre non fini (~18), arbitrage
  attendu (~9), échec structurant (~7), dépendance externe (~6), raisons
  cumulables.
- **Catégories des découvertes trouvables** (n ≈ 192, supérieur à 169 car
  certains journaux étiquettent plus de lignes que l'État final ne le
  reprend) :
  - appelants/voisinage de code : **72 (38 %)**
  - données réelles : **30 (16 %)**
  - la page du plan elle-même : **22 (11 %)**
  - config CI / outillage : **20 (10 %)**
  - doc / README / CLAUDE.md / skill du dépôt : **14 (7 %)**
  - environnement (droits, chemins) : **12 (6 %)**
  - historique git / PR : **11 (6 %)**
  - plan antérieur : **9 (5 %)**
  - autre : **4 (2 %)**
- **Décomptes finaux faux** : 9 plans sur ceux qui portent un décompte
  (26 %) — le nombre annoncé de découvertes « trouvables » ne correspondait
  pas à ce que le journal listait réellement.

## Tableau des 77 plans

hc hermes-custom · va vahiny · mv mavod-perso · X transverse. **T/PT**
décompte officiel (— absent, `recl.` reclassé) ; **≠** divergent du journal.
**Par./Suite** o = oui, — = non ; *expl.* exploité ; **SA** sous-agents
(? non dit). **M** mermaid. Suite : **P** périmètre · **A** arbitrage ·
**E** échec · **D** dépendance externe.

| # | Titre court | Repo | Exéc. | Statut | Ét. | SA | T/PT | Par. | Suite (raison) | M |
|---|---|---|---|---|---|---|---|---|---|---|
|1|Galerie de composants v2|va|08-02|archive|9|?|(recl.)|o|—|n|
|2|Correction auto audit Routard|va|08-03|archive|7|?|(recl.)|o|—|n|
|3|Recalcul positions Argentine|va|08-05|archive|8|1|(recl.)|o|P (essaimé ×2)|n|
|4|Supervision hebdo ressources VPS|hc|08-05|archive|5|0|—|—|—|n|
|5|Garde nocturne PRs Dependabot|hc|08-08|archive|16|1|—|o|P|n|
|6|Dependabot — arbitrages restants|X|08-06|archive|9|0|—|o|P|n|
|7|VPS — Autonomie et durcissement|hc|08-11|archive|27|0|—|o|E|n|
|8|Vercel — Tests e2e Playwright|X|08-20|archive|9|10|(recl. 5/4)|o **expl.**|E|n|
|9|Indice de confiance géocodage|va|08-11|archive|7|?|(recl.)|—|—|n|
|10|[Annulé] Dependabot scripts install|X|—|archive|5 (0)|0|—|o?|—|n|
|11|CD event-driven|hc|08-11|archive|6|0|—|o|—|n|
|12|Mémoire saturée (SOUL/state.db)|hc|08-11|archive|9|0|(recl. 2T)|o|—|n|
|13|Ré-armer clé ambiguë sur le nom|va|08-11|archive|4|?|—|—|—|n|
|14|VPS #2 — Autonomie (suite)|hc|08-14|archive|9|0|(recl. 5T)|o|P+A|n|
|15|Optimisations mémoire profils|hc|08-11|archive|8|?|(recl. 2/4)|o|—|n|
|16|Redémarrage gateway maj hebdo|hc|08-11|archive|5|?|—|o|—|n|
|17|Centroïde de polygone|va|—|archive|5 (0)|0|—|—|fusion|n|
|18|Cliquet anti-dégradation géocodage|va|—|archive|5 (0)|0|—|o|fusion|n|
|19|Nettoyage branche avant merge|va|08-14|archive|7|?|—|—|—|n|
|20|VPS #3 — Réparer la garde nocturne|hc|08-14|archive|13|?|—|o|D+P|n|
|21|VPS #4 — Juges manquants|hc|08-17|archive|16|?|—|o|E|n|
|22|Hermes CI sur le VPS ?|X|08-20|archive|6|7|—|o|P (semi)|n|
|23|Vercel e2e Playwright #2|X|08-20|archive|7|7|—|o|—|n|
|24|GH Actions bloqué par facturation|X|—|archive|3 (2)|0|—|o?|—|n|
|25|Refonte vps-resource-governance|hc|08-20|archive|6|5|—|—|—|n|
|26|Hygiène du stockage dev #2|hc|08-21|archive|5|4|—|o|—|n|
|27|Chantier C — géocodage sur le guide|va|09-04|archive|8→6|3|**5/0 ≠** (journal 12/1)|o|P ×2|n|
|28|Chantier A — extraction fiable|va|08-21|archive|16|16|—|—|P|n|
|29|Retour stockage OAuth Notion natif|hc|08-19|archive|3|0|—|—|—|n|
|30|Auto-réparation généralisée des crons|hc|08-21|archive|8|7|—|o|—|n|
|31|VPS #5 — Curateur versionné|hc|08-18|archive|8|0|—|o (26 paires)|E+P|n|
|32|Séquencement/hygiène des crons|hc|08-21|archive|7|≥5|**3/1**|o|P+A|n|
|33|VPS #6 — Ce que le #5 a livré|hc|08-18|archive|8|0|—|o **expl.**|A|n|
|34|VPS — Remplacer le custom par le natif|hc|08-21|archive|6|8|—|o|D+A|n|
|35|VPS #7 — Planifié et jamais fait|hc|—|archive|6 (0)|0|—|o|P (rattrapage)|n|
|36|Chantier A #2|va|08-22|archive|11 (6)|6 +~104 lots|**7/2 ≠** (8/2)|o|E|n|
|37|Garde nocturne : débit par dépôt|hc|08-21|archive|6 (5)|5|—|o|D+P|n|
|38|Garde nocturne : débit par dépôt #2|hc|08-21|archive|2 (1)|0|—|—|P|n|
|39|[Abandonné] Débit par dépôt #3|hc|—|archive|0|0|—|—|—|n|
|40|Veille de version hors-manifeste #1|hc|08-24|archive|8|3|**3/1**|o|A|n|
|41|VPS natif #2|hc|08-21|archive|3|1|3 (hors format)|—|—|n|
|42|Séquencement crons #2|hc|08-21|archive|3|3|**4/0**|o|—|n|
|43|VPS — Gestion durable de la RAM|hc|08-24|archive|6 (5)|3|**3/3 ≠** (correctifs non recomptés)|o|—|n|
|44|Épingler Remote Control à Opus|hc|—|archive|5 (0)|0|—|o|—|n|
|45|Watchdog horaire relance quota|hc|08-21|archive|7|?|—|—|—|n|
|46|Chantier A #3|va|08-27|archive|13 (5)|~105 lots|**8/3**|o (1-3)|P (approche)|n|
|47|Veille de version #2|hc|08-24|archive|3|1|**2/3**|o|A|n|
|48|Veille de version #3|hc|08-24|archive|3|0|**1/2**|o|—|n|
|49|Enquête/coût/cartographie des plans|hc|08-26|archive|6 (5)|5|**5/3 ≠** (compléments)|o|—|n|
|50|Banc de comparaison des chaînes|va|09-03|archive|8|≥1|0/0 (3T+1PT étiquetés)|o|—|n|
|51|Angles morts gouvernance mémoire|hc|08-26|archive|7 (6)|6|**4/1**|o|P+A|n|
|52|Angles morts gouvernance mémoire #2|hc|08-26|archive|6|6|**7/1**|o|—|n|
|53|maVOD — Doublons cross-tracker|mv|08-27|archive|5|5|**7/0 ≠** (8 lignes)|o|—|n|
|54|Chantier A #4|va|09-03|archive|10 (8)|~10|**7/5**|o **expl.**|P|n|
|55|Chantier A #5|va|08-28|archive|10|~9|**5/1**|o **expl.**|E|n|
|56|Chantier B — catégorisation validée|va|09-04|archive|9|~7|**4/0 ≠** (≥14/2)|—|P|n|
|57|Chantier A #6|va|08-28|archive|5 (3)|3|**4/0**|o|D|n|
|58|Chantier A #7|va|09-01|archive|6|5|**1/4**|— (ordre figé)|P|n|
|59|Chantier A #8|va|09-02|archive|11|9|**13/0**|o **expl.**|A|n|
|60|VPS — Stockage, le plancher|hc|09-02|archive|6|4|**2/0**|—|—|n|
|61|Chantier A #9|va|09-03|archive|3|3|**3/0**|o (ét. 3)|A (semi)|n|
|62|Mise au propre branche extraction|va|09-03|archive|6|2|**6/0**|o (ét. 4)|—|n|
|63|Chantier B #2 — étiquettes Google|va|09-06|archive|7|8|**7/1**|o (ét. 5)|—|n|
|64|Chantier C #2 — positions restantes|va|09-04|archive|5 (+1bis)|4 lots **expl.**|**8/2**|—|D+A|n|
|65|maVOD — Saison incomplète|mv|09-04|archive|8|8|**3/1**|o|—|n|
|66|Chantier C #3 — reconfirmations|va|09-06|archive|5|3 lots|**1/2**|P (semi)|—|n|
|67|Chantier C #4 — positions suspectes|va|09-07|execute|5|6|**3/1**|—|A|n|
|68|Chantier C #5 — généricité des noms|va|09-07|archive|3 (2)|2|**1/2**|o (1,2)|E+A|n|
|69|Ancres mortes iteration-reentry|hc|09-07|archive|6|4|— (2T nommées)|—|P|n|
|70|Chantier C #6 — 4 points de mesure|va|09-07|archive|2|2|**1/0**|—|—|n|
|71|Ancres mortes #2|hc|09-07|archive|5|3|—|o **expl. partiel**|—|n|
|72|Alléger l'arbitrage (type + agent)|va|09-08|execute|9|~12|**10/2 ≠** (13 lignes)|—|—|n|
|73|Chantier B #3 — le Routard prime|va|09-08|execute|8|5|**6/3 ≠** (5 lignes)|o|P|n|
|74|MCP de Claude Code retrouvent node|hc|09-07|archive|3|1|**4/0**|P (semi)|—|n|
|75|VPS — Confinement cgroup Remote Ctrl|hc|09-08|a merger|10 (8)|8|**7/2 ≠** (8 lignes)|o|—|n|
|76|Chantier B #4 — Activité, solde du #3|va|09-08|a merger|10 (9)|5|**14/0**|o (ét. 9)|—|n|
|77|Fiabilité native des MCP|hc|08-12|archive|0 (non découpé)|0|—|impossible|—|n|

## Les treize angles morts récurrents

**1. Ne pas lire la fonction / le fichier juste à côté** (~72 découvertes,
~40 plans). « le filigrane était écrit dans la **docstring de `scan()`** ; le
plan avait lu la ligne du filtre, pas la docstring » (*Séquencement crons*) ;
« l'enquête avait lu `corrige_fiche` mais pas le bloc qui l'entoure »
(*Chantier B*). **Vérif.** : pour chaque `fichier:ligne` cité, lire la
fonction entière, sa docstring, le bloc englobant.

**2. Ne pas grep les appelants** (~15, ~12 plans). « `classify_pr_with_build_proof`
ne consultait que `e2e_command` : les 5 dépôts basculés auraient vu toutes
leurs PR gelées » (*Vercel e2e #2*) ; « `launch()` n'a qu'un seul appelant » —
fonctionnalité **écrite puis retirée** (*Confinement cgroup*). **Vérif.** :
`grep -rn '<symbole>('` sur chaque symbole nommé.

**3. Ne pas relire le chapitre Exécution du plan** (~22, ~15 plans) —
contradictions, renvois périmés, ordre faux. « **le plan portait déjà le
fait qui le prouvait, dans la réponse à Q2** » (*A #4*) ; « le plan avait le
bon avertissement et en a tiré la mauvaise mesure » (*C #5*). **Vérif.** :
relecture de bout en bout avant d'ouvrir l'exécution.

**4. Preuve de fin impossible ou périmée** (~8 plans). « deux indicateurs de
la preuve de fin n'ont plus de définition, **recopiés de plan en plan** »
(*A #6*) ; « la commande de preuve est interceptée par le proxy `rtk` et
échoue à se lancer » (*Séquencement crons*). **Vérif.** : jouer chaque
preuve avant de valider.

**5. Ne pas lire le CLAUDE.md / README / skill qui pilote l'étape** (~14,
~10 plans). « **la conception n'avait pas lu le skill qui pilote précisément
cette étape** » (`routard-t2/SKILL.md:152-165`, *A #2*). **Vérif.** : lire
CLAUDE.md dépôt + global et le `SKILL.md` de tout skill invoqué.

**6. Ne pas vérifier droits, chemins, PATH, sandbox** (~12, ~10 plans).
« `~/.hermes` est en 0700 : l'unité aurait échoué en 203/EXEC »
(*Confinement cgroup*) ; « `sudo systemctl start` refusé par le classifieur »
— bloque l'étape dont dépendaient trois autres, **sur deux plans
consécutifs** (*VPS #4*, *#5*). **Vérif.** : `stat -c %a` sur chaque chemin ;
privilège joué à blanc.

**7. Mesurer sur un échantillon ou un parseur maison** (~30, ~20 plans). « le
chiffre de Q1 (~147) sous-estimait de 80 % » — 295 fiches au lieu de 1 267
(*C #2*) ; « le plan chiffrait 8 occurrences en ne regardant **qu'un seul
pack sur trois** » (*B #4*). **Vérif.** : mesurer avec le chargeur réel du
dépôt, sur le corpus complet.

**8. Supposer une CI / une PR / un merge** (~20, ~14 plans). «
**ouvrir une PR équivaut à la merger** » — PR « NE PAS MERGER » auto-mergée
puis `git revert` (*A #3*) ; « le dépôt se déploie sur le VPS à chaque
merge, **y compris une PR vers une branche de travail** » (*Enquête
dispositif*). **Vérif.** : lire déclencheurs, `needs`, jobs
`automerge`/`deploy`.

**9. Ignorer ce qui est gitignoré ou lu depuis un chemin déployé** (~8
plans). « la page de revue est un **artefact gitignoré** » (*B #4*) ; «
`memory-backup.sh` n'a jamais atteint le runtime : `refresh_deployed_scripts`
ne déploie que des `*.py` » (*Optimisations mémoire*). **Vérif.** :
`git check-ignore` sur chaque artefact ; lire `deploy.py`.

**10. Tests figés sur des comptes exacts, ou qui défendent l'erreur
corrigée** (~10 plans). « `test_routard_gamme.py:206-215` **fige des comptes
réels** » (*A #2*) ; « un test **verrouillait l'affirmation fausse** du
README… il défendait l'erreur qu'on venait corriger » (*Angles morts #2*).
**Vérif.** : `grep -rn '== [0-9]\{3,\}' tests/`, lister les tests-verrous.

**11. Checkout partagé avec une autre session** (7 plans, l'incident le plus
coûteux). « **trois des quatre découvertes ont la même cause** : avoir
travaillé dans la copie partagée » — commit égaré, **moitié du plan remontée
sur `main` par la PR d'une autre session** (*MCP node*). **Vérif.** :
worktree avant la première écriture.

**12. Ne pas interroger l'historique git, et recopier un plan antérieur**
(~20, ~15 plans). « `niveau: ville` de SALTA avait régressé, **anomalie déjà
notée par un plan antérieur sans être résolue** » (*A #8*) ; « la ligne de
base est de **13 échecs, pas 33** ; le Journal du plan #3 l'écrit noir sur
blanc » (*Banc de comparaison*). **Vérif.** : `git log HEAD..origin/main`,
`git log -S` ; tout chiffre repris d'un `#N-1` est remesuré.

**13. Ne pas vérifier l'état d'avancement réel, et trancher avant de
mesurer** (~9 plans). « l'essentiel des étapes 2 à 7 était **déjà en
production via 12 PR antérieures** » (*Garde nocturne Dependabot*) ; «
trouvable par **la commande même que le plan prévoyait "avant d'écrire"** »
— étape arrêtée sans un commit (*B #4*). **Vérif.** : `ls`, PR récemment
mergées ; toute question chiffrée porte sa mesure **et son résultat**.

## Les retours de méthode de Benjamin

**Ne pas décider à sa place.** « **tu as effacé mes réponses** » (*Galerie
v2*) ; « **J'ai précoché mes recos**, et j'ai lu tes cases sans lire le
texte en face — quatre retours ratés » (*VPS #5*) ; « **C'est la réponse
libre qui prime** » (*VPS #2*).

**Mesurer avant de proposer.** « **tu ne connais visiblement pas les
projets** » (*Vercel e2e*) · « faire un **audit** de ce skill vs le natif,
**décider ensuite** » (*VPS #6*).

**Vérifier que ça marche, pas que c'est écrit.** « **rejouer d'abord le
scénario** pour que la correction auto fonctionne réellement » (*VPS #6*) ·
« **les tests valident que tout fonctionne** » (*Veille #1*) · «
**insister plutôt que constater le blocage** » — deux diagnostics erronés,
qui avaient coûté un plan entier, tombent en une heure (*A #6*).

**Jusqu'où vérifier.** « **Fais jusqu'à 3 passes si besoin. Au-delà on se
pose** » (*VPS #3*) · « **uniquement les tests unitaires à chaque étape**,
la suite complète quand le plan est terminé » (*Mise au propre*) · «
**2 sous agents qui ne communiquent qu'avec l'agent principal** et on
s'assure que le retour est le même » (*Chantier A*).

**Le découpage et l'ordre lui appartiennent.** « **On traite tout, dans
l'ordre le plus pertinent, séquencé en différentes PR** » (*VPS #3*) · «
une seule page », **contre la reco** d'un plan maître (*VPS Autonomie*) · «
**Non, on suit l'ordre du plan** » (*Chantier C*).

**Ne pas surcoder.** « **ne pas tordre l'instrument** pour avoir un
markdown complet à 100 % » (*A #3/#4*) · « ça ferait du code en plus à
maintenir, **restons simples** » — fait disparaître une étape (*maVOD
doublons*).

**Vulgariser, et rendre un avis.** « **plus de détails, je ne comprends
pas** » (*VPS #5*) · « **tu fais l'analyse à la fin et tu me recommandes ou
non de merger** » (*Mise au propre*) · « **un champ libre pour que je
puisse commenter** » (*A #4*).

## Les vingt et une recommandations

`[enq.]` enquête · `[rel.]` relecture · `[exé.]` exécution · `[fmt]` format
de page.

1. `[enq.]` **Lire la fonction entière et sa docstring**, pas la ligne
   citée. — *angle 1, ~40 plans.*
2. `[enq.]` **`grep -rn '<symbole>('`** sur chaque symbole nommé. —
   *2, ~12 plans.*
3. `[enq.]` **`ls` du répertoire et lecture des modules frères** avant
   d'écrire « créer X ». — *13, ~5 plans.*
4. `[enq.]` **`git log HEAD..origin/main`, `git show origin/main:<fichier>`,
   `git log -S`** en ouverture. — *12, ~9 plans.*
5. `[enq.]` **Lire les workflows et le chemin de déploiement runtime.** —
   *8, ~14 plans.*
6. `[enq.]` **`git check-ignore` sur chaque artefact de preuve.** —
   *9, ~8 plans.*
7. `[enq.]` **`grep -rn '== [0-9]\{3,\}' tests/`** et lister les
   tests-verrous. — *10, ~10 plans.*
8. `[enq.]` **Droits et sandbox avant toute étape système** ; **privilège
   joué à blanc** contre le classifieur. — *6, ~10 plans.*
9. `[enq.]` **Lire CLAUDE.md (dépôt + global) et le `SKILL.md` de tout
   skill invoqué.** — *5, ~10 plans.*
10. `[rel.]` **Aucun chiffre repris d'un `#N-1` sans remesure.** —
    *12, ~8 plans, dont 2 campagnes abandonnées sur un motif faux.*
11. `[rel.]` **Passe de cohérence interne avant d'ouvrir l'exécution**
    (prémisses vs Questions, renvois). — *3, ~15 plans.*
12. `[rel.]` **Chaque preuve de fin est jouée avant validation.** —
    *4, ~8 plans.*
13. `[rel.]` **Toute question chiffrée porte sa commande de mesure et son
    résultat.** — *13, ~4 plans.*
14. `[rel.]` **Mesurer avec le chargeur réel du dépôt, sur le corpus
    complet.** — *7, ~20 plans, écarts jusqu'à 80 %.*
15. `[exé.]` **Worktree obligatoire dès l'ouverture.** — *11, 7 plans.*
16. `[exé.]` **Un worktree par étape parallèle + le critère à 4 conditions**
    (fichiers disjoints, aucune dépendance de données, aucun fichier
    partagé de config/README/test de décompte, un worktree par étape). —
    *51 plans à étapes indépendantes non parallélisées.*
17. `[exé.]` **Le brief au sous-agent annonce le délai attendu des commandes
    longues.** — *7 abandons prématurés sur 3 plans consécutifs.*
18. `[exé.]` **Corriger le nommage des sous-branches** : tiret, jamais
    slash. — *redécouvert dans 4 plans, dont 2 le même jour.*
19. `[exé.]` **Décompte de l'État final vérifié mécaniquement**
    (`grep -c 'trouvable'`). — *ferme les 9 décomptes faux.*
20. `[fmt]` **Décompte obligatoire + tableau `étape · fichiers · dépend de`**
    en tête du chapitre Exécution, idéalement un mermaid. — *décompte
    absent dans 56 % des plans ; aucun des 77 ne représente ses
    dépendances.*
21. `[fmt]` **Un plan `brouillon` doit déclencher un rappel.** — *« et c'est
    arrivé quatre fois » (VPS #7) ; le statut `a merger`, né du même
    constat, prouve le correctif.*

## Ce que le plan de refonte des skills en a retenu

- **Gestes 7 à 12 de l'agent `enqueteur`** (`plugins/plans-notion/agents/enqueteur.md`)
  reprennent les treize angles morts ci-dessus, dans l'ordre de fréquence :
  lire la fonction entière et sa docstring (angle 1), `ls` et modules
  frères avant d'annoncer une création (angle 13), CLAUDE.md/README/SKILL.md
  du dépôt (angle 5), CI et déploiement avec `git check-ignore` sur chaque
  preuve (angles 8 et 9), droits et environnement avec `stat -c %a` et
  privilège joué à blanc (angle 6), et historique/mesures — `git log`,
  tests-verrous, chargeur réel sur le corpus complet (angles 7, 10, 12).
  Écarté : loger ces gestes dans le skill `plan-notion` plutôt que dans
  l'agent — c'est l'enquêteur qui lit à la place de la session appelante, et
  il tourne en Sonnet, pas en Opus.
- **Un tableau de chevauchement et des vagues d'exécution** pour détecter,
  avant de lancer des étapes en parallèle, les fichiers partagés entre
  étapes non consécutives (recommandations 16 et 20) — le point qui a
  produit tous les conflits de parallélisation du corpus.
- **Le worktree redevient obligatoire dès l'ouverture** (recommandation 15) :
  l'angle mort 11 (checkout partagé) est le plus coûteux du corpus en
  proportion — 7 plans, dont un où la moitié du travail a été remontée sur
  `main` par la PR d'une autre session.
- **Un rapport de sous-agent à quatre états** — `DONE`, `DONE_WITH_CONCERNS`,
  `NEEDS_CONTEXT`, `BLOCKED` — pour que les rapports muets ou les
  contournements silencieux (§ « Sous-agent hors périmètre ou muet », ~8
  plans du corpus) soient visibles avant la clôture, pas découverts après.
- **Le décompte des découvertes est vérifié mécaniquement**
  (recommandation 19), pour fermer la catégorie des 9 décomptes finaux faux
  du corpus (26 % de ceux qui en portent un).
- **Une rétrospective en cinq questions** clôt chaque plan exécuté, sur le
  modèle des cinq familles de retours de méthode de Benjamin ci-dessus :
  qui décide, qu'est-ce qui a été mesuré avant d'être proposé, qu'est-ce qui
  a été vérifié en fonctionnement et pas seulement à l'écrit, jusqu'où la
  vérification est allée, et si le résultat a été surcodé au-delà du besoin
  réel.
