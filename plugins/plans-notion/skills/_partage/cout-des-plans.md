# Coût des plans : le barème, et comment on le lit

Fichier partagé du plugin `plans-notion`. Il est lu par `plan-notion` (la ligne
« Coût estimé » en tête du chapitre `Exécution`) et par `executer-plan-notion`
(la ligne « Coût réel » à l'entrée `État final`, mesurée par `cout-plan.py`).

## L'unité : des dollars d'équivalent API, rien d'autre

Tout coût s'écrit en **dollars d'équivalent API** : ce que la session coûterait
au tarif officiel de l'API. Sur l'abonnement, on ne paie pas ces dollars ; ils
servent d'unité commune pour comparer des plans entre eux. **Aucun pourcentage de
quota** n'est écrit, ni estimé, ni recopié (décision Q4 du plan).

Les tarifs sont dans `scripts/grille-tarifs.json`, à côté de `cout-plan.py`
(`plugins/plans-notion/skills/_partage/scripts/`).

## Le barème mesuré le 2026-10-12

**Méthode** : les journaux de session (`.jsonl`) de Claude Code, messages
dédoublonnés par `message.id` (le même message est écrit plusieurs fois dans le
journal), tokens recalculés au tarif officiel d'Anthropic. Période : les 14 jours
précédant la mesure, soit 35 sessions de plan.

**Médianes par type de session** (`n` = nombre de sessions du type) :

| Type de session | Médiane | Min | Max | n |
|---|---|---|---|---|
| plan seul | 14 $ | 2 $ | 73 $ | 11 |
| exécution seule | 28 $ | 1 $ | 122 $ | 11 |
| plan puis exécution dans la même session | 132 $ | 32 $ | 398 $ | 12 |

Le total de la période est d'environ 3 600 $ d'équivalent API, pour 11,8 milliards
de tokens, dont l'essentiel en lecture de cache. Les trois `n` font 34 ; le
relevé annonçait 35 sessions, et la répartition manquante n'est pas donnée.

**Par étape** : aucune médiane par étape n'a encore été mesurée. Quand une étape
l'aura été, sa médiane s'ajoute ici, avec sa date et son nombre de sessions. Une
étape sans mesure n'a pas de coût estimé : on l'écrit, on n'en invente pas un.

## Ce que ces chiffres disent, et ce qu'ils ne disent pas

- Une médiane n'est pas une prévision pour un plan donné. La dispersion est
  large (de 1 $ à 398 $) : la ligne « Coût estimé » donne un ordre de grandeur.

## La remesure

Le barème se remesure **à chaque passe de veille**, sur les sessions de plan des
**14 derniers jours**, par la même méthode : journaux dédoublonnés par
`message.id`, écritures de cache ventilées comme le fait `cout-plan.py` (part 1 h
mesurée par modèle dans les journaux, appliquée aux écritures de ccusage), autres
tarifs de la grille. Chaque chiffre porte sa date de mesure ; une remesure remplace
les médianes ci-dessus et change la date en même temps.

⚠️ La sonde qui a fait la mesure du 2026-10-12 n'est pas dans ce dépôt. Tant
qu'elle n'y est pas, la remesure se refait à la main, par la même méthode.

## Lire les deux lignes de coût

- **« Coût estimé »** (`plan-notion`, en tête du chapitre `Exécution`) : avant
  l'exécution, les médianes du barème pour le type de session que le plan annonce,
  recopiées avec leur date.
- **« Coût réel »** (`executer-plan-notion`, entrée `État final`) : à la clôture,
  `cout-plan.py --page <identifiant de la page>`. Il additionne les sessions qui
  citent la page, sous-agents compris, et recalcule les dollars à partir des
  tokens. La session en cours y est comptée jusqu'à l'instant de la mesure.
  Un modèle absent de la grille est listé à part, « non chiffré », et exclu du
  total : un zéro silencieux ne se produit pas.
