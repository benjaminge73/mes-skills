# Banc de relecture : peut-on relire aussi bien qu'Opus, pour bien moins cher ?

Ce banc rejoue des relectures réelles du sous-agent `relecteur` (`plugins/plans-notion/agents/relecteur.md`, Opus 5.5
effort high jusqu'au 2026-11-23, medium depuis ; les relectures rejouées ici sont celles d'origine, en high, ≈ 1,7 dollar l'appel) avec d'autres modèles, d'autres consignes et des chaînes d'agents, puis note chaque
bras contre la relecture Opus d'origine. Il est né du plan « Réduire la voilure » du 2026-11-22 : le relecteur était le
premier sous-agent en coût (≈ 22 % de la dépense du VPS sur deux semaines). Les résultats sont dans
[RESULTATS.md](RESULTATS.md) ; ils servent de base à la refonte de `plan-notion` et `executer-plan-notion`.

Ce n'est **pas** un banc d'évals de plugin (`evals/<plugin>/`, `evals_ab.py`) : il ne se joue pas en CI et ne touche
aucune catégorie. On le lance à la main, sur décision de Benjamin, comme toute dépense de jetons. Une exception, tranchée
par Benjamin le 2026-11-24 : le cron de la boucle de la liste (`boucle_liste.py`, plus bas) le lance seul, dans un plafond
d'environ 5 dollars par mois, sans passer par `lancer.sh`. Deuxième exception, datée : l'ombre de relecture d'étape
(`ombre.py`, ≈ 0,3 dollar), lancée par le pilote après chaque relecture d'étape, décidée au plan « Réduire la voilure » et
reprise par Q2 de P1. Ni l'une ni l'autre ne passe par `lancer.sh`, et le reste de la règle ne change pas.

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
| `ombres/ombre-<id>.json` | l'ombre d'une étape réelle (`ombre.py`) : chaîne, coûts, `liste_sha256`, date `fait_le` |
| `ombres/opus-<id>.md`, `ombres/retenues-<id>.json` | le rapport d'Opus de cette étape, et le tri du pilote : remarques retenues (`opus`, `commune`) et remarques de l'ombre seule jugées réelles ou bruit (`ombre`) |

Le détail par cas et par bras (tableaux, remarques manquées) est dans la page Notion « Banc de relecture — résultats
détaillés », sous le projet Mes Skills.

## Les scripts

| Script | Rôle |
| --- | --- |
| `extraire_cas.py` | sur la machine des journaux (le VPS) : construit le jeu de cas et les bundles git |
| `rejouer.py` | joue un bras : modèle, effort, ajout de consigne (`--liste` seul : la liste du plugin ; `--liste <chemin>` ; `--ajout checklist.txt` pour un autre texte, exclusif de `--liste`), `--angle secu`, notes de passe précédente |
| `juge.py` | note un bras, ou l'union de plusieurs, contre `ref-opus.json` (Sonnet medium, texte seul) |
| `chaine.py` | la chaîne retenue : N rapports → extraction et dédoublonnage → vérification de chaque remarque dans le code |
| `ombre.py` | ombre d'une relecture réelle, à la volée : 3 Haiku high + la liste de relecture du plugin + chaîne, et un bras Sonnet medium compté à part. Usage : `ombre.py --id <id> --brief <brief> --rep <worktree> --depot <dépôt> --debut <sha> --fin <sha> [--liste <chemin>] [--opus <rapport d'Opus>] [--retenues <tri>]` ; `--dry-run` imprime le chemin et le sha256 de la liste, puis les cinq commandes, sans appeler `claude`. Chaque `ombre-<id>.json` porte `liste`, `liste_sha256` et la date `fait_le`. `--opus` range le rapport d'Opus en `opus-<id>.md` ; `--retenues` valide le tri du pilote (forme dans `bilan_ombre.valider_retenues`) et le range en `retenues-<id>.json`. Relancer avec le même `--id` ne rejoue aucune relecture |
| `bilan_ombre.py` | bilan de l'ombre sur les étapes triées : cumule les `ombre-<id>.json` qui ont un `retenues-<id>.json`, appelle `juge.py` contre la vérité (remarques retenues, plus celles de l'ombre seule jugées réelles), applique la règle de décision et rend `bascule`, `hybride`, `statu quo` ou `pas assez d'étapes`. Usage : `bilan_ombre.py [--depuis AAAA-MM-JJ] [--min-etapes 20]`. Codes : 0 décision, 3 pas assez d'étapes, 4 versions de liste mêlées. `--source-json` (lignes d'un journal exporté) est réservé et n'est pas branché |
| `test_bilan_ombre.py` | tests du bilan (pytest, sans réseau) : frontière 70 %, remarque de l'ombre seule au dénominateur, versions mêlées, ombre sans tri |
| `boucle_liste.py` | la boucle de la liste de relecture (étape 7) : relève les lignes candidates (remarques retenues par Opus seul, vues dans deux étapes de la même catégorie), mesure chacune sur les 43 cas de validation contre une base mesurée et un bruit A/A, et ne l'ajoute que si le rappel monte sans que le bruit dépasse celui de l'A/A. Usage : `boucle_liste.py --section Code [--plafond-mois 5] [--dry-run] [--cron]`. Codes : 0 rien à ajouter, 10 une ligne ajoutée (PR), 1 erreur réelle, 3 plafond du mois atteint, 5 bilan de Q2 pas encore passé. `--cron` sort en 0 (`[SILENT]` ou une ligne), sauf erreur réelle (code 1, une ligne). Le journal est `journal-checklist.md`, à côté du script (une section par liste, `## Code` ici) ; l'état (coût, mesures, décisions) est dans `$BANC_DONNEES/etat-boucle-<section>.json`, voir plus bas. Le code 3 vaut aussi quand le budget restant est sous le coût d'une mesure complète |
| `test_boucle_liste.py` | tests de la boucle (pytest, sans réseau ni `claude` ni `gh`) : décision retenue et refusée, plafond, bilan, quota, mode cron |
| `jev.py` | Jev (TypeSafe System One) : aiguillage des angles, second avis sur une remarque |
| `banc.py` | socle : emplacement des données, appel `claude -p` isolé, worktree jetable |
| `checklist.txt`, `angles.json` | les consignes ajoutées au brief (checklist en 8 catégories, 4 angles du comité) |
| `passe-plan-tests.txt` | passe dédiée plan et tests |
| `plugins/plans-notion/skills/_partage/listes/relecture-code.md` (hors de ce dossier) | checklist v2 (conformité au plan, retraits incomplets et tests par mutations en tête) : la seule source, lue par `ombre.py` et `rejouer.py` (`--liste`). Promue depuis le fichier du banc au commit `bfd7133`, contenu identique octet pour octet |
| `construire_ref.py`, `par_categorie.py` | référence Opus d'un jeu de validation hors échantillon ; rappel par catégorie de défaut |

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
python3 rejouer.py sb-ck2 claude-haiku-5-5 high 3 --liste --bash-enferme  # la liste du plugin ; Bash dans le bac à sable
python3 juge.py v-sb.json sb-ck2 --ref ref-validation.json                            # sur le jeu de validation
python3 par_categorie.py v-sb.json --ref ref-validation.json
python3 bilan_ombre.py                                                                # le bilan de l'ombre : seulement à la date du plan (Q2)
python3 boucle_liste.py --section Code --dry-run      # la boucle du cron : bilan, jeu, plafond ; rien mesuré
```

La checklist s'améliore en continu : un défaut qu'Opus voit et que la chaîne manque devient une ligne de
`plugins/plans-notion/skills/_partage/listes/relecture-code.md` (sa catégorie, un exemple générique, jamais un extrait d'un
autre dépôt), puis la nouvelle version se mesure sur le jeu de validation, qui n'a pas servi à l'écrire.

**Figée jusqu'au bilan de Q2** : le contenu de cette liste ne change pas pendant les deux semaines d'ombre, parce que l'ombre
la mesure telle quelle. La neuvième case « Hors liste » n'y entre qu'après ce bilan ; d'ici là elle vit dans le brief du
relecteur. Chaque `ombre-<id>.json` porte le `liste_sha256` joué : deux sorties comparées doivent porter la même empreinte.

**Le bilan de l'ombre (Q2)** : `bilan_ombre.py` ne compte que les étapes qui ont un tri du pilote (`retenues-<id>.json`) ;
le tri ne compte que les remarques retenues, plus les remarques de l'ombre seule jugées réelles (l'union est la vérité).
La règle : moins de 20 étapes, « pas assez d'étapes », sans appel au juge ; sinon rappel de la chaîne ≥ 70 % et au plus
un bug de correction manqué, une remarque de l'ombre seule jugée bruit par relecture en moyenne, 0,5 dollar par relecture
au plus (Haiku et chaîne, Sonnet à part) : `bascule` ; rappel entre 50 et 70 % avec les trois autres conditions : `hybride` ;
sinon `statu quo`. Le bilan rend une recommandation, la décision reste à Benjamin. Il refuse deux `liste_sha256` différents
(code 4) : une liste modifiée en cours de route ne se mêle pas à l'autre. La source « journal du plan Juge du rêve » (Notion)
n'est pas lisible par le banc : l'option `--source-json` est prévue pour la rendre, elle n'est pas branchée.

**La boucle de la liste (étape 7 du plan Refonte)** : `boucle_liste.py` est le seul script du banc qui touche à la liste
de relecture, et il ne l'ajoute qu'après une mesure. Il refuse tant que le journal `journal-checklist.md` ne porte pas la
ligne `Bilan de Q2 : AAAA-MM-JJ` (code 5). Il mesure une base et son bruit A/A une fois (deux relectures identiques),
puis chaque candidat ; une ligne est retenue si le rappel monte et si sa hausse de bruit ne dépasse pas le bruit A/A. Le
total du mois, toutes sections confondues, ne doit pas dépasser 5 dollars (code 3). Le format du journal (sections `## NOM`,
entrées `### AAAA-MM-JJ`, puces à clé fixe) est l'interface que réutilise un autre plan (`--section`) : ne pas le changer
sans lui.

**L'état de la boucle fait foi** (`$BANC_DONNEES/etat-boucle-<section>.json`, hors du dépôt) : le coût par mois, la dernière
mesure complète, chaque mesure faite sous son nom de bras (une mesure faite n'est jamais repayée), la base et son bruit A/A,
et le statut de chaque candidat (`refusée`, `retenue`, `en vol`, `mergée`, `fermée`). Le cron tourne dans un worktree neuf
d'origin/main, dont le journal ne porte pas les entrées non mergées : sans cet état, une ligne refusée serait remesurée
chaque mois. Le journal reste la trace publiée ; une ligne déjà dans l'état n'est jamais réécrite par lui.

**Le budget** : une mesure ne part que si le budget restant couvre le coût de la dernière mesure complète connue ; sans mesure
connue, le plafond entier. `rejouer.py` ne lance pas un cas si le budget restant, cas en vol réservés, ne couvre pas le coût
moyen d'un lot de six cas. Des sorties incomplètes s'arrêtent avant le juge, et leur dépense est journalisée.

**Une PR de la boucle** : une seule est en vol à la fois. Son état est lu sur GitHub (`gh pr view`) à chaque passage : ouverte,
la boucle attend ; rouge, la ligne est signalée et rien n'est mesuré ni ouvert ; fermée sans merge, la ligne est signalée une
fois et ne revient pas sans décision humaine ; mergée, elle devient une décision définitive. Avant le push, `ouvrir_pr` joue
`scripts/check_veille.py` en local, comme les gardes Doc et Evals : un refus arrête sans push, avec une entrée « PR non ouverte ».
Le worktree de PR s'appelle `boucle-liste-pr-<date>` sous `~/repos/worktrees/mes-skills/` ; un chemin qui égale, contient ou
recouvre le dépôt de lancement est refusé, sans rien effacer.

**Le dossier de lancement**, à donner à Hal dans la configuration du cron : un worktree neuf d'origin/main, à rafraîchir avant
chaque passage. Jamais le checkout principal, ni un worktree de travail :
`python3 <dossier>/evals/banc-relecture/boucle_liste.py --section Code --cron`.

**Le budget en chiffres** : un bras de 43 cas coûte environ 4,9 dollars sur le VPS (extrapolé des 2,71 dollars de 24 cas,
Haiku high), juge compris autour de 5,2. Avec 5 dollars par mois, une seule mesure complète tient dans un mois : la base
(deux bras) prend donc deux mois. Le plafond ou le nombre de bras est une décision de Benjamin, à prendre avant le bilan de Q2.

Sans `--liste` ni `--ajout`, `rejouer.py` n'ajoute aucune consigne (le bras témoin reste reproductible) ; `--liste` seul ajoute la liste du plugin.
Les rejeux antérieurs à cette promotion restent reproductibles par l'ancien fichier de la checklist v2, dans l'historique git (commit `bfd7133`)
et par `checklist.txt` (la v1, toujours là).

Jev demande sa clé : `chaine.py … --jev <fichier .env>:<VARIABLE>`. Elle est lue dans le fichier donné, par le seul
processus, et jamais affichée.

## Le juge, et ce qu'il vaut

La référence a été établie par l'agent `evaluateur` (Sonnet high), qui a jugé chaque bras à la main sur 24 cas : pour
chaque remarque Opus, le bras signale-t-il le même défaut (même cause, même endroit) ; pour chaque remarque en plus,
réelle ou bruit, sur le texte seul. `juge.py` automatise ce jugement pour ≈ 0,3 dollar par bras. Validé sur trois bras, il
garde le même classement que l'évaluateur, à 2 à 9 points près ; deux passages du juge sur le même bras diffèrent d'une
demi-remarque sur 11. Ses chiffres servent à **comparer des bras entre eux**, pas à donner une valeur absolue.

## Le banc d'enquête

`enquete.py` mesure l'enquête d'avant-plan. L'enquêteur (`plugins/plans-notion/agents/enqueteur.md`, ou une liste
d'enquête) rejoue, au commit où la branche d'un plan exécuté est partie, la fiche qu'il aurait rendue ; on compte les
découvertes que l'exécution a faites plus tard et qui étaient trouvables au moment du plan. Il repose sur le socle du banc
de relecture (`banc.py` : `claude -p` isolé, worktree jetable) et reprend son `Budget` (`rejouer.py`). POC et chiffres :
[RESULTATS.md](RESULTATS.md), section « POC du plan enquête-checklist ».

| Commande | Effet |
| --- | --- |
| `python3 enquete.py --dry-run actuel 0` | imprime les dix commandes `claude -p`, n'en lance aucune, n'écrit rien |
| `python3 enquete.py <bras> <plafond> [<tirage>]` | rejoue un bras sur les dix plans de l'échantillon : `actuel`, `liste`, `liste-bash` |
| `python3 enquete.py juge:<bras>[@<tirage>] <plafond>` | note les fiches d'un bras (Sonnet medium, texte seul) contre les découvertes du classement |
| `python3 enquete.py releve [--corpus <dossier>]` | relevé déterministe, sans modèle ni plafond : `git grep` et `git log` en lecture seule |

Le plafond est positionnel, comme dans `rejouer.py`. Sans plafond positif, le script refuse (code 2) ; seul `--dry-run`
s'en passe, puisqu'il n'appelle rien. Un bras inconnu est refusé : il n'y a pas de bras `spike`.

**Les données** sont hors de ce dépôt, sous `BANC_ENQUETE_DONNEES` (défaut `~/.local/share/banc-enquete`), dossier distinct
de celui du banc de relecture (le script force `BANC_DONNEES` sur le sien, pour ne jamais écrire dans celui de la
relecture). `corpus/` porte `pages/<id>.md` (une page de plan par fichier), `bases.json` (dépôt et commit de départ par
plan), `echantillon.json` (les dix ids rejoués), `classement.json` (juge seulement) ; `depots/` (clones miroir), `sorties/`
et `releves/` sont produits par le script. `--corpus` remplace le dossier `corpus/` par défaut.

**Le relevé** prend les découvertes « trouvable au plan » du journal, en étiquette brute : le passage tel qu'il est écrit,
une fois chacun. Une découverte compte comme retrouvée si le fichier qu'elle cite, hors fichiers du plan, figure parmi les
40 premiers voisins du relevé, classés par co-change. Le détail par plan va dans `releves/`, hors dépôt ; la sortie
n'imprime que le total.

Ce qui a été tranché en écrivant le script :
- Le bras `liste` joue le fichier livré, `_partage/listes/enquete.md` (13 cases, C0 à C12). Le POC jouait un prototype de
  12 cases : les deux ne sont pas le même objet, et le tableau du POC ne les compare pas.
- Un appel en erreur, ou un juge illisible, n'écrit aucune sortie : le relancement reprend ce plan. Un juge sans fiche
  n'est pas lancé.
- Le relevé est celui du chapitre D du POC (références classées par co-change), pas le classement Sonnet : sa mesure en
  étiquette brute ne se compare donc qu'à elle-même. Le chiffre de référence du plan (15,2 %) n'est pas reproduit, voir
  RESULTATS.md.

Tests : `python3 -m pytest -q evals/banc-relecture/test_enquete.py` (pas de réseau, pas de `claude`, temporaire de pytest).

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
- `--bash-enferme` rend Bash, dans le bac à sable natif de Claude Code (`banc.BAC_A_SABLE`) : écriture limitée au
  worktree et au temporaire, réseau coupé, secrets du poste refusés à Bash et à Read, `.claude/` du dépôt relu retiré du
  worktree (ses réglages s'ajouteraient aux nôtres). Le bac à sable refuse de démarrer plutôt que de tourner sans
  (`failIfUnavailable`).
- Les remarques en plus d'un bras (≈ 3,6 par relecture pour la chaîne retenue) ont un coût en aval, pour qui les traite,
  que ce banc ne mesure pas.
- 2026-11-23 : `ombre.py` joue la chaîne sans le repêchage Jev (`chaine.py` sans `--jev`) et sans `--bash-enferme` : elle est donc plus stricte que la chaîne de référence de `RESULTATS.md`. Le second avis `jev-1.14.0` se joue à part sur les remarques gardées (`jev.plausibilite`) ; à lire ainsi avant de comparer les deux semaines d'ombre.
- 2026-11-23 : le bras Sonnet medium d'`ombre.py` mesure l'apport de Sonnet au-dessus de Haiku sur la même checklist
  (la liste du plugin), compté à part de la chaîne. La bascule « chaîne à la place d'Opus » n'est pas faite.
