# Résultats du banc de relecture

Une section par campagne, la plus récente en dernier. Les dollars sont d'équivalent API (grille
`plugins/plans-notion/skills/_partage/scripts/grille-tarifs.json`). Le détail par cas est dans la page Notion « Banc de
relecture — résultats détaillés » (projet Mes Skills), jamais ici : ce dépôt est public.

## 2026-11-22 — POC du plan « Réduire la voilure »

**Jeu de cas.** 261 relectures Opus 5.5 high extraites des journaux du VPS depuis le 01/11 ; 73 % rendent des remarques
(un filtre qui sauterait Opus quand c'est propre ne pourrait éviter qu'un quart des appels). Les « plan entier » rendent
des remarques dans 82 à 88 % des cas : ils ne sont pas redondants avec les relectures par étape. Échantillon : 24 cas
rejouables. Coût d'origine des 24 relectures Opus : 41,30 dollars (médiane 1,74 dollar par relecture d'étape, 2,77 en
« plan entier »).

### Première série : modèles seuls (jugés par l'agent `evaluateur`, VPS)

| Bras (24 cas) | Coût | Remarques Opus retrouvées | Bugs Opus retrouvés | En plus réelles / bruit |
| --- | --- | --- | --- | --- |
| Haiku 5.5 medium | 2,71 | 21 % | 31 % | 16 / 3 |
| Haiku 5.5 high | 3,04 | 19 % | 28 % | 16 / 2 |
| Sonnet 5.5 medium | 11,24 | 26 % | 31 % | 7 / 1 |
| Comité de 4 Haiku à angles imposés (union) | 10,80 | 47 % | 59 % | 86 / 12 |
| Jev, triage « défaut ou pas » | ≈ 0 | AUC 0,65 contre le verdict Opus | — | — |

Calibrage sur 4 cas (10, 11, 163, 186 ; 11 remarques, 7 bugs) : un **second passage d'Opus high** retrouve 68 % des
remarques du premier et 64 % de ses bugs ; **Opus medium** 64 % et 57 %, pour 11 % de moins. Les deux Opus ne ratent pas
les mêmes remarques. L'écart des petits modèles vient donc du modèle, pas de la variance ; et un passage Opus seul n'est
pas exhaustif. Par angle du comité, bugs retrouvés : sécurité 22 %, architecture 34 %, dev senior 38 %, tests 6 %.

### Seconde série : itérer sur une même relecture (juge automatique, Mac)

| Bras (24 cas) | Coût | Remarques Opus | Bugs Opus | En plus réelles / bruit |
| --- | --- | --- | --- | --- |
| 1 Haiku, prompt générique | 1,3 à 2,7 | 24 à 30 % | 31 à 37 % | ≈ 20 / 3 à 9 |
| 4 Haiku génériques, union (témoin) | ≈ 6,2 | 28 % | 37 % | 43 / 18 |
| Comité 4 angles, union | 10,80 | 44 % | 57 % | 73 / 13 |
| 1 Haiku + `checklist.txt` (3 tirages) | 1,2 à 1,4 | 37 à 46 % | 56 à 59 % | ≈ 44 / 9 à 15 |
| 3 checklists, union | 3,92 | 49 % | 75 % | 77 / 24 |
| **3 checklists + extraction + vérification dans le code (`chaine.py`)** | **4,63** | **47 %** | **75 %** | **86 / 7** |
| Haiku + 2e passe « cherche ce qui manque » | 3,62 | 34 % | 50 % | 35 / 7 |
| Checklist + 2e passe sur la checklist | 2,58 | 37 % | 53 % | 72 / 6 |

Sur les 4 cas de calibrage, même juge : la chaîne retrouve 71 % des bugs, Opus high (2e passage) 64 %, Opus medium 64 %,
le comité 50 %.

### Jev

- Triage des cas (« ce changement a-t-il un défaut ? ») : AUC 0,65 ; il répond « défaut » sur 24 cas sur 24.
- Aiguillage des angles du comité : 63 relectures sur 96 gardées (− 34 %) ; l'union passe de 59 % à 56 % des bugs.
- Filtre des remarques, sans le diff (`choice`) : AUC 0,64 contre le jugement de l'évaluateur.
- Second avis avec le diff (`noul`) : AUC 0,75 ; au seuil 0,5, il repêche les 3 remarques Opus que le vérificateur Haiku
  avait réfutées à tort, avec 4 bruits sur 9. Petit gain gratuit, sur trop peu de cas pour le chiffrer.

### Ce qu'on en retient

1. **Répéter un prompt générique ne sert à rien** : 37 % des bugs à 1 comme à 4 tirages.
2. **La structure du prompt fait la qualité** : la checklist en 8 catégories double presque le rappel d'un Haiku seul.
3. **Une fois le prompt structuré, la répétition paie** : 3 tirages passent de 56 % à 75 % des bugs.
4. **La vérification de chaque remarque dans le code** retire deux tiers du bruit (24 → 7) sans perdre de bug, pour
   0,71 dollar les 24 cas. C'est le schéma « find, verify » d'Anthropic Code Review (code.claude.com/docs/en/code-review.md).
5. **La 2e passe « cherche ce qui manque » ne vaut pas un tirage de plus.**
6. **Jev ne relit pas** ; il peut servir de garde-fou bon marché contre les faux rejets du vérificateur.
7. Coût de la chaîne : ≈ 0,19 dollar la relecture sur le Mac (≈ 0,4 avec les tests sur le VPS), contre 1,72 en Opus high.

Coût total de la campagne : ≈ 60 dollars (dont ≈ 43 de rejeux sur le VPS et ≈ 17 sur le Mac).

## 2026-11-22 (suite) — Checklist v2, Haiku high, Bash enfermé, jeu de validation

Tous les bras en Haiku **high**. « Bac à sable » : Bash rendu au relecteur dans le bac à sable natif de Claude Code
(`rejouer.py --bash-enferme`, réglages dans `banc.BAC_A_SABLE`) : écriture limitée au worktree et au temporaire, pas de
réseau, secrets du poste illisibles par Bash comme par Read. « Sans Bash » : Read, Grep, Glob seulement. Rappel par
catégorie : `par_categorie.py`. Le jeu de validation (43 cas, 82 remarques Opus, `construire_ref.py --exclure
echantillon.json`) n'a servi à écrire aucune checklist : il dit si `checklist-v2.txt` a sur-appris l'échantillon.

### Échantillon (24 cas ; référence : 16 bugs, 10 écarts au plan, 3 tests vides)

| Bras | Bugs | Écarts au plan | Tests vides | Remarques en plus réelles / bruit |
|---|---|---|---|---|
| v1 × 3, sans Bash | 50 % | 35 % | 0 % | 35 / 9 |
| v1 × 3, bac à sable | 53 % | 35 % | 0 % | 64 / 8 |
| v2 × 3, sans Bash | 50 % | 40 % | 67 % | 52 / 21 |
| v2 × 1, bac à sable | 47 % | 65 % | 33 % | 41 / 8 |
| v2 × 3, bac à sable | 72 % | 45 % | 33 % | 77 / 21 |
| **v2 × 3, bac à sable + `chaine.py` + second avis Jev** | **78 %** | **55 %** | 33 % | **82 / 10** |
| Passe dédiée plan et tests (`passe-plan-tests.txt`), seule | 28 % | 30 % | 17 % | 48 / 9 |

### Validation (43 cas ; référence : 50 bugs, 8 écarts au plan, 18 tests vides)

| Bras | Bugs | Écarts au plan | Tests vides | Remarques en plus réelles / bruit |
|---|---|---|---|---|
| v1 × 2, sans Bash | 58 % | 75 % | 14 % | 89 / 16 |
| v2 × 2, sans Bash | 55 % | 62 % | 42 % | 113 / 21 |
| v2 × 1, bac à sable | 57 % | 69 % | 19 % | 83 / 8 |
| v2 × 2, bac à sable | 53 % | 75 % | 31 % | 118 / 17 |

### Ce qu'on en retient

1. **La checklist v2 tient sur la validation pour les tests vides** (42 % contre 14 % en v1, sur 18 tests) ; sur les bugs,
   v1 et v2 font jeu égal (53 à 58 %). Le gain d'écarts au plan vu sur l'échantillon ne se confirme pas, mais 8 écarts
   seulement : un écart vaut 12 points.
2. **Le bac à sable ne gagne pas de bug sur la validation** (53-57 % contre 55 % sans Bash) ; le 72 % de l'échantillon
   tient en partie à la variance (un bug y vaut 6 points). Il garde l'intérêt d'un bruit plus bas à un tirage (8 contre 11).
3. **La vérification de `chaine.py` filtre peu sur ces rapports** : 8 remarques réfutées sur 118, dont 6 repêchées par
   Jev (format `choice` décrit, `jev-1.14.0`). Le bruit baisse de 21 à 10 et aucun bug n'est perdu.
4. Coût : ≈ 0,08 dollar par relecture Haiku high en bac à sable ; la chaîne complète (3 relectures + extraction +
   vérification + Jev) ≈ 0,27 dollar la relecture, contre 1,72 en Opus high.
5. Pannes : 15 relectures sur ≈ 900 ont échoué (`FileNotFoundError`, `Exec format error`) pendant une mise à jour du
   binaire `claude` ; supprimées et rejouées, `rejouer.py` saute les cas déjà faits.

Coût de cette suite : ≈ 35 dollars de rejeux en high (hors bras medium et juges).

## 2026-11-25 — POC du plan « enquête-checklist »

**Jeu.** 10 plans exécutés (8 hermes-custom, 2 mes-skills ; 116 découvertes trouvables selon le classement Sonnet),
rejoués au merge-base. Haiku 5.5 effort high, 60 tours au plus ; juge Sonnet medium, texte seul, un passage par bras. Le
détail par plan reste hors de ce dépôt (page Notion du projet Mes Skills).

### Tableau C : enquêteur actuel contre liste (agrégé)

| Bras | Rappel strict, 3 tirages | Moyenne | Rappel avec partiels | Union des 3 | Faits par 10 fiches | Hors sujet | Fiches complètes (script) | Coût par fiche |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Enquêteur actuel (prose) | 6,0 · 2,6 · 6,0 % | 4,9 % | 12 à 14 % | 7,8 % | 289 à 362 | 28 à 40 | 0 sur 30 | 0,08 à 0,13 dollar |
| Liste de 12 cases (prototype) | 8,6 · 7,8 · 4,3 % | 6,9 % | 13 à 17 % | 8,6 % | 158 à 180 | 8 à 15 | 16 sur 30 | 0,10 à 0,12 dollar |
| Liste + Bash enfermé | 7,8 · 7,8 · 7,8 % | 7,8 % | 13 à 19 % | 6,0 % | 200 à 348 | 17 à 26 | 15 sur 30 | 0,19 à 0,26 dollar |
| Actuel + fichiers touchés dans le brief (1 tirage) | 5,2 % | — | 17,7 % | — | 447 | 47 | — | 0,14 dollar |
| Liste + fichiers touchés (1 tirage) | 3,4 % | — | 16,4 % | — | 387 | 39 | 5 sur 10 | 0,15 dollar |
| Relevé `git grep` du nom de chaque fichier touché (script, sans modèle) | 22 % (borne haute) | — | — | — | 47 à 575 fichiers voisins par plan | — | — | 0 |

Ce qu'on en retient : le rappel ne bouge pas d'un bras à l'autre (écart liste contre prose dans la dispersion des
tirages) ; la liste gagne sur la qualité de la fiche, à coût égal ; Bash double le coût sans gain. Le goulot n'est ni la
consigne ni l'entrée : donner les fichiers touchés ne suffit pas. Coût de l'ensemble : 23,4 dollars d'appels `claude -p`
(16,1 pour les fiches, 7,3 pour les juges), hors agents de la passe non chiffrés.

### Relevé sur le corpus de départ (sans modèle)

Relevé des 40 premiers voisins par co-change, sur les 29 plans du corpus (27 ont des découvertes trouvables relevées),
étiquette brute du journal (« découverte — trouvable au plan »).

| Mesure | Découvertes | Retrouvées | Rappel |
| --- | --- | --- | --- |
| Étiquette brute, dédoublonnée au texte près | 196 | 32 | 16,3 % |
| Étiquette brute, sans dédoublonnage | 197 | 32 | 16,2 % |
| Même relevé, classé par compte de références (sans co-change) | 196 | 27 | 13,8 % |
| Toutes les références, sans coupure à 40 | 196 | 45 | 23,0 % |
| Référence annoncée au plan (étiquette brute, 30 sur 197) | 197 | 30 | 15,2 % (non reproduite) |

Lecture : le relevé mesuré sur ce corpus est au-dessus du seuil de garde de 12 % du plan, mais le chiffre de référence
de 15,2 % n'est pas celui que donne le script, quel que soit le classement testé (le numérateur reste à 32, pas à 30). Le
chiffre à citer est à trancher par le pilote, avant le relevé sur le jeu neuf ; le chiffre de 17,4 % du chapitre D
(classement Sonnet, 32 sur 184) reste la mesure du prototype.
