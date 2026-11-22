# Banc de relecture : peut-on relire aussi bien qu'Opus, pour bien moins cher ?

Ce banc rejoue des relectures réelles du sous-agent `relecteur` (`plugins/plans-notion/agents/relecteur.md`, Opus 5.5
effort high, ≈ 1,7 dollar l'appel) avec d'autres modèles, d'autres consignes et des chaînes d'agents, puis note chaque
bras contre la relecture Opus d'origine. Il est né du plan « Réduire la voilure » du 2026-11-22 : le relecteur était le
premier sous-agent en coût (≈ 22 % de la dépense du VPS sur deux semaines). Les résultats sont dans
[RESULTATS.md](RESULTATS.md) ; ils servent de base à la refonte de `plan-notion` et `executer-plan-notion`.

Ce n'est **pas** un banc d'évals de plugin (`evals/<plugin>/`, `evals_ab.py`) : il ne se joue pas en CI et ne touche
aucune catégorie. On le lance à la main, sur décision de Benjamin, comme toute dépense de jetons.

## Les données : hors de ce dépôt

Ce dépôt est **public**. Un cas de relecture contient le brief d'une étape, le rapport d'Opus et le code d'autres dépôts
(`hermes-custom`, `micro-trading`, `vahiny`, `job-agent`…) : rien de tout cela n'est commité ici. Les données vivent sous
`BANC_DONNEES` (défaut `~/.local/share/banc-relecture`) :

| Chemin | Contenu |
| --- | --- |
| `cas-opus.json` | toutes les relectures Opus extraites des journaux (brief, rapport final, verdict, usage) |
| `cas-rejouables.json` | celles dont la plage de commits existe encore, avec dépôt, début et fin |
| `echantillon.json` | les 24 cas du POC (graine 42 : 13 étapes à remarques, 7 sans, 4 « plan entier ») |
| `ref-opus.json` | la référence : les remarques Opus de chaque cas de l'échantillon, avec leur gravité |
| `jev-entrees.json` | objectif, `git diff --stat` et diff tronqué de chaque cas (entrée de Jev) |
| `depots/<dépôt>.git` | clones nus des commits des cas (bundles git, ≈ 120 Mo) |
| `sorties/<bras>/<id>.json` | sortie de chaque relecture rejouée |
| `jugements/` | sorties du juge automatique, et `evaluateur/` : les jugements manuels de l'agent `evaluateur` |

Le détail par cas et par bras (tableaux, remarques manquées) est dans la page Notion « Banc de relecture — résultats
détaillés », sous le projet Mes Skills.

## Les scripts

| Script | Rôle |
| --- | --- |
| `extraire_cas.py` | sur la machine des journaux (le VPS) : construit le jeu de cas et les bundles git |
| `rejouer.py` | joue un bras : modèle, effort, ajout de consigne (`--ajout checklist.txt`, `--angle secu`), notes de passe précédente |
| `juge.py` | note un bras, ou l'union de plusieurs, contre `ref-opus.json` (Sonnet medium, texte seul) |
| `chaine.py` | la chaîne retenue : N rapports → extraction et dédoublonnage → vérification de chaque remarque dans le code |
| `jev.py` | Jev (TypeSafe System One) : aiguillage des angles, second avis sur une remarque |
| `banc.py` | socle : emplacement des données, appel `claude -p` isolé, worktree jetable |
| `checklist.txt`, `angles.json` | les consignes ajoutées au brief (checklist en 8 catégories, 4 angles du comité) |

Chaque appel passe par `claude -p --setting-sources project --strict-mcp-config` : les réglages, hooks et plugins du
poste ne se mêlent pas à la relecture. `--bare` est écarté : il coupe aussi l'authentification par abonnement.

## Rejouer

```bash
export BANC_DONNEES=~/.local/share/banc-relecture
python3 rejouer.py haiku-checklist claude-haiku-5-5 medium 4 --ajout checklist.txt   # un bras, plafond 4 dollars
python3 juge.py j-checklist.json haiku-checklist                                      # sa note
python3 juge.py j-union.json haiku-checklist haiku-checklist-2 haiku-checklist-3      # l'union de trois tirages
python3 chaine.py chaine haiku-checklist haiku-checklist-2 haiku-checklist-3          # extraction + vérification
python3 juge.py j-chaine.json chaine
```

Jev demande sa clé : `chaine.py … --jev <fichier .env>:<VARIABLE>`. Elle est lue dans le fichier donné, par le seul
processus, et jamais affichée.

## Le juge, et ce qu'il vaut

La référence a été établie par l'agent `evaluateur` (Sonnet high), qui a jugé chaque bras à la main sur 24 cas : pour
chaque remarque Opus, le bras signale-t-il le même défaut (même cause, même endroit) ; pour chaque remarque en plus,
réelle ou bruit, sur le texte seul. `juge.py` automatise ce jugement pour ≈ 0,3 dollar par bras. Validé sur trois bras, il
garde le même classement que l'évaluateur, à 2 à 9 points près ; deux passages du juge sur le même bras diffèrent d'une
demi-remarque sur 11. Ses chiffres servent à **comparer des bras entre eux**, pas à donner une valeur absolue.

## Les limites à garder en tête

- La référence est **un** passage d'Opus, lui-même non exhaustif : un second passage d'Opus high n'en retrouve que 68 %.
- 24 cas, dont 4 de calibrage : un écart de quelques points n'est pas significatif.
- Sur le Mac, les relecteurs ne rejouent pas les tests (pas de venv des dépôts) : un Haiku y coûte ≈ 1,3 dollar les
  24 cas, contre 2,71 sur le VPS.
- **Les relecteurs rejoués lisent du contenu non fiable** (code et briefs d'autres dépôts). Ils tournent donc sans
  `bypassPermissions` et **sans Bash** : seulement Read, Grep et Glob (`LECTURE` dans `banc.py`). Même un git en
  lecture n'est pas sûr (`git grep -O <cmd>` exécute, `git log --output=<fichier>` écrit) : le diff et le journal de
  la plage sont préparés à l'avance dans le worktree (`.banc/plage.diff`, `.banc/journal.txt`). Aucun test n'est
  rejoué. Les mesures du
  2026-11-22 ont été prises avant ce durcissement, en `bypassPermissions` : certains relecteurs avaient alors créé des
  dossiers à côté de leur worktree, ou tenté un `pip install` (échec). Une campagne future se compare à elles sous
  cette réserve.
- Les remarques en plus d'un bras (≈ 3,6 par relecture pour la chaîne retenue) ont un coût en aval, pour qui les traite,
  que ce banc ne mesure pas.
