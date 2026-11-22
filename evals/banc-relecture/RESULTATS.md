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
