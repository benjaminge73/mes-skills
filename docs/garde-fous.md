# Le registre des garde-fous

Un correctif qu'aucun garde ne tient peut être défait sans que personne le voie :
la panne revient, et on la corrige une seconde fois. Ce registre tient la liste
**une ligne par règle** : ce qu'elle protège, d'où elle vient, **le garde qui la
tient** et où ce garde tourne.

Le principe : **chaque correctif reçoit un garde qui le rend impossible à défaire
sans que la CI le voie**, et le prochain correctif suit le même chemin — c'est la
règle de `CLAUDE.md`, section « Mettre à jour un skill ou un plugin » : tout
correctif ajoute sa ligne ici et son garde dans la même PR.

## Les règles

Le statut dit où en est le garde :

- **en place** : le garde existe et tourne. Le citer **en code** dans la colonne
  « Garde » — un fichier de script (`scripts/xxx.py`), un job de la CI
  (`ci.yml#nom-du-job`) ou un cas d'éval (`evals/<plugin>/<cas>`). Ce que la
  colonne cite est **vérifié** par `scripts/check_skills.py` : un garde cité qui
  n'existe pas refuse la PR ;
- **réglage** : le garde est un réglage GitHub, hors du dépôt, que rien ici ne
  peut vérifier ;
- **prévu — étape X** : le garde n'existe pas encore ; il dit l'étape qui le
  pose. Non vérifié ;
- **manquant** : la règle n'a pas de garde, et le registre le dit plutôt que de
  le taire. Non vérifié.

| Règle | Ce qu'elle protège | Origine | Garde | Où il tourne | Statut |
| --- | --- | --- | --- | --- | --- |
| Le registre est lui-même contrôlé | qu'une ligne « en place » ne cite pas un garde disparu | 2026-09-30, plan banc d'évals, étape A7 | `scripts/check_skills.py` (section « Le registre ») | CI, job `garde`, via `scripts/ci_locale.sh` | en place |
| Une seule liste des contrôles | que la CI, `CLAUDE.md` et le README ne divergent pas sur ce qu'on joue avant de pousser | 2026-09-30, étape A7 | `scripts/ci_locale.sh`, `scripts/test_ci_locale.py` | CI (jobs `garde` et `validation`) et en local | en place |
| Aucune donnée personnelle dans le dépôt public | qu'une adresse e-mail, un numéro de téléphone, un identifiant numérique (Telegram), un chemin de profil Hermes ou de répertoire personnel, ou un nom de la liste hors dépôt (`~/.config/mes-skills/motifs-personnels.txt`) ne soit publié sous `plugins/voyages/` ou `evals/voyages/` : le dépôt est public, et le log de la CI aussi — le garde ne recopie donc jamais la valeur trouvée | 2026-10-06, plan « Création d'un cron Voyage », étape 10 | `scripts/check_donnees_personnelles.py`, `scripts/test_check_donnees_personnelles.py` | CI, job `garde`, via `scripts/ci_locale.sh` (motifs génériques seulement : la liste de noms connus n'existe que sur le poste) | en place |
| Les tests d'un plugin se jouent avant de pousser | qu'un script de plugin (`plugins/<plugin>/tests/`, hors de `scripts/`) ne parte pas rouge : aucun contrôle ne lisait ces tests ; `ci_locale.sh` les rejoue avec l'interpréteur `PYTHON_PLUGINS` et la CI installe d'abord les `requirements.txt` des tests | 2026-10-06, plan « Création d'un cron Voyage », étape 3 | `scripts/ci_locale.sh`, `ci.yml#validation` | CI, job `validation`, et en local | en place |
| Un billet au voyageur incertain n'est jamais importé | qu'un billet dont le voyageur n'est pas nommé soit rangé quand même, sous le nom du voyageur principal ou « commun » par supposition, au lieu d'être signalé sans rien ranger ni rien rappeler | 2026-10-06, plan « Création d'un cron Voyage », étape 2 | `evals/voyages/billet-voyageur-incertain` | CI, job `evals` (payant, runner seulement), catégorie `billet` | en place |
| A/B quand le label `evals` est posé | qu'une consigne changée ne fasse pas reculer le comportement mesuré (l'A/B se joue à la demande depuis l'étape 1 du plan « Évals sobres et machine partagée » ; sans le label, la fumée tourne seule) | 2026-09-30, plan banc d'évals, étape A6 ; à la demande : 2026-10-01 | `ci.yml#evals`, `scripts/evals_ab.py` | CI, job `evals` (payant, runner seulement) | en place |
| Chaque cas d'éval a sa catégorie | qu'un cas qu'aucune catégorie ne nomme ne soit jamais joué par une PR qui choisit ses catégories, et qu'une catégorie ne pointe pas dans le vide (cas ou chemin inexistant) | 2026-09-30, plan « Chercher, prouver, paralléliser #2 », étape B9 | `scripts/check_skills.py` (règle i), `evals/categories.json` | CI, job `garde` | en place |
| Plancher des évals | qu'une PR qui choisit ses catégories ne laisse pas un skill ou un agent modifié sans cas joué ; ce qui touche le socle commun (hooks, banc, outillage, CI) rejoue tout ; un fichier de `_partage/` ne rejoue que les catégories qui le déclarent dans `exerce` | 2026-09-30, étape B9 (décision de Benjamin : des évals par catégorie, un plancher tenu par la CI) | `scripts/evals_selection.py`, `ci.yml#evals-portee` | CI, job `evals-portee`, sur les PR | en place |
| Verdict des évals au nom fixe | qu'un contrôle d'évals puisse être exigé par le verrou de `main` : le nom de `Évals (<plugin>)` change avec la matrice, celui-ci non (rouge si la portée, un bras ou la fumée est rouge ou annulé, vert s'il est sauté ; sur un label étranger il recopie le dernier verdict du SHA) | 2026-09-30, étape B9 | `ci.yml#evals-verdict` | CI, job `Verdict des évals` ; à ajouter au ruleset après le merge du lot B | en place |
| Skill touché : label `evals` ou `Evals: aucun — <raison>` | qu'une PR qui change un skill, un agent, un hook ou un `_partage/` ne passe pas sans avoir dit si les évals se jouent : le silence rendrait le banc (≈ 55 $) payant à chaque PR, ou jamais joué sans que personne l'ait décidé. Sans label ni ligne `aucun` (avec la raison), la portée est refusée ; le label et le corps sont relus par l'API, jamais lus dans l'événement | 2026-10-01, plan « Évals sobres et machine partagée », étape 1 | `scripts/evals_selection.py`, `ci.yml#evals-portee` | CI, job `evals-portee`, sur les PR | en place |
| Un label étranger ne relance pas le banc | que poser `review-required` (ou tout autre label) sur une PR qui porte déjà `evals` ne paie pas un second banc, et ne rende pas vert un SHA dont le run précédent était rouge : le verdict recopie alors le dernier verdict terminé du SHA | 2026-10-01, étapes 1 et 12 | `scripts/test_evals_selection.py`, `ci.yml#evals-portee`, `ci.yml#evals-verdict` | CI, jobs `evals-portee` et `evals-verdict` | en place |
| Un seul banc à la fois par plugin | que deux bancs ne partagent pas la limite de débit d'un même abonnement : le groupe de concurrence `evals-<plugin>` (`aa-` devant pour la mesure de bruit) met le second en attente, sans annuler le premier ; GitHub ne garde qu'un run en attente, un troisième annule celui qui attendait | 2026-09-30, trois bancs simultanés aux résultats inexploitables ; groupe posé à l'étape 2 | `ci.yml#evals`, `ci.yml#fumee` | CI, jobs `evals` et `fumee` | en place |
| Une leçon a son cas | qu'un correctif de skill ne parte pas sans cas d'éval qui le prouve | 2026-09-30, étape A7 | `scripts/check_lecon_a_son_cas.py` | CI, job `garde`, sur les PR | en place |
| Description ≤ 1 536 caractères | que Claude Code ne tronque pas la fin d'une description (phrases de déclenchement perdues sans un mot) | 2026-09-30, étape A7 ; `executer-plan-notion` à 1 545 le jour même | `scripts/check_skills.py` (règle a) | CI, job `garde` | en place |
| Taille des `SKILL.md`, à cliquet | qu'un skill ne grossisse pas ; le plafond de `scripts/limites.json` ne peut que baisser ; `plan-notion` et `executer-plan-notion` y sont plafonnés à 500 lignes | 2026-09-30, étape A7 ; 500 lignes le 2026-10-02, étape 21 du plan « Évals sobres et machine partagée » | `scripts/check_skills.py` (règle b), `scripts/limites.json` | CI, job `garde` | en place |
| Chaque fichier de skills et d'agents a sa catégorie d'évals | qu'un fichier de `skills/` (`_partage/` compris) ou `agents/` d'un plugin qui a un banc ne soit pas livré sans qu'une catégorie dise quel cas le teste : sinon une PR qui le touche rejouerait tout le banc, ou rien. Un nouveau fichier oblige à le déclarer dans `evals/categories.json` dans sa PR | 2026-10-02, plan « Évals sobres et machine partagée », étape D5 | `scripts/check_skills.py` (règle i), `evals/categories.json` | CI, job `garde` | en place |
| Invariants en tête des skills marqués | que les invariants survivent à la compaction (les 5 000 premiers jetons) | 2026-09-30, étape A7 ; skills marqués à l'étape B5 | `scripts/check_skills.py` (règle c) | CI, job `garde` ; skills marqués : `plan-notion`, `executer-plan-notion` (étape B5) | en place |
| Agents cités dans `plugin.json` | que le manifeste dise tous les agents que le plugin livre | 2026-09-30, étape A7 | `scripts/check_skills.py` (règle d) | CI, job `garde` | en place |
| Compagnons de `_partage/` tous cités | qu'un fichier partagé ne soit pas livré sans lecteur, et qu'une liste de compagnons ne mente pas | 2026-09-30, étape A7 | `scripts/check_skills.py` (règle e) | CI, job `garde` | en place |
| Champs ignorés des agents de plugin | qu'un agent de plugin ne déclare pas `hooks`, `mcpServers` ou `permissionMode`, que Claude Code ignore | 2026-09-30, étape A7 | `scripts/check_skills.py` (règle f) | CI, job `garde` | en place |
| Pas de mémoire pour un agent en lecture seule | que `memory` n'active pas Write et Edit sur un agent qui se les interdit | 2026-09-30, étape A7 | `scripts/check_skills.py` (règle g) | CI, job `garde` | en place |
| Aucun dossier de mémoire d'agent versionné | que la mémoire personnelle d'un agent ne parte pas dans le dépôt public | 2026-09-30, étape A7 | `scripts/check_skills.py` (règle h) | CI, job `garde` | en place |
| Version montée | que toute PR qui touche un plugin fasse changer sa `version` (sinon `plugin update` ne voit rien) | 2026-09-01, quatre PR invisibles six jours | `scripts/plugin_version_guard.py` | CI, job `garde`, sur les PR | en place |
| Marketplace et disque concordent | qu'un plugin déclaré existe, et qu'un plugin présent soit déclaré | dépôt d'origine, `hermes-custom` | `scripts/check_marketplace.py` | CI, job `garde` | en place |
| Renvois et frontmatters | qu'un renvoi `${CLAUDE_PLUGIN_ROOT}/…` ne pointe pas dans le vide, qu'un frontmatter YAML se charge | 2026-09-08 (renvois), 2026-09-23 (frontmatter de l'agent relecteur) | `scripts/check_references.py`, `scripts/test_check_references.py` | CI, job `validation` | en place |
| Copies installées à jour | qu'un instantané `@inline` ne masque pas la copie installée d'un plugin | 2026-09-11, l'incident du `0.3.0` | `scripts/copies_installees.py` | à la main, sur le poste : aucune CI ne le joue | en place |
| Veille avant chaque mise à jour d'un skill | qu'une règle ne repose pas sur un fait de doc périmé | 2026-09-30, étape A7b | `scripts/check_veille.py`, `veille.yml`, `scripts/veille_faits.py` | CI, job `garde` (journal, via `scripts/ci_locale.sh`) et workflow hebdomadaire (faits) | en place |
| `--no-verify` et `Statut` accentué | qu'un commit ne saute pas les hooks (`--no-verify`) et qu'une valeur de `Statut` d'une page Notion ne soit pas écrite avec un accent (les valeurs sont sans accents) | 2026-09-30, cas `evals/plans-notion/no-verify` ; en place le 2026-10-02, étape 17 du plan « Évals sobres et machine partagée » | `plugins/plans-notion/hooks/refuser_no_verify.py`, `plugins/plans-notion/hooks/refuser_statut_accentue.py` | hooks du plugin, à chaque appel d'outil | en place |
| Secrets dans le dépôt | qu'un jeton ne parte pas dans un commit d'un dépôt public | dépôt public depuis l'origine | protection des poussées de GitHub (push protection) | GitHub, à chaque `git push` | réglage |
| `main` verrouillé | qu'on ne pousse pas sur `main` sans passer par la CI | 2026-09-30, étape A9 | ruleset GitHub `main-verrouillee` (id 24256838) | GitHub, sur toute poussée vers `main` | réglage |
| Liens de `docs/` et de `CLAUDE.md` | qu'un lien de la doc ne pointe pas dans le vide : `check_references.py` ne parcourt que `plugins/` | 2026-09-30, constaté à l'étape A7 | manquant | nulle part | manquant — à décider |

## Le verrou de `main`

Le ruleset `main-verrouillee` interdit de supprimer `main` ou d'y réécrire
l'historique, impose de passer par une PR, et exige trois contrôles verts :
`Gardes de distribution`, `Validation des plugins` et `Portée des évals`. Le
contrôle d'évals n'y figure pas encore, parce que son nom change avec le plugin
(`Évals (<plugin>)`) : le job au nom fixe `Verdict des évals`
(`ci.yml#evals-verdict`, étape B9) existe désormais, et sera ajouté au ruleset
après le merge du lot B. Aucun contournement
n'est prévu (`bypass_actors` vide). Retour arrière :
`gh api -X DELETE repos/benjaminge73/mes-skills/rulesets/24256838`.

```json
{
  "name": "main-verrouillee",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false,
        "allowed_merge_methods": ["merge", "squash", "rebase"] } },
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": false,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          { "context": "Gardes de distribution", "integration_id": 15368 },
          { "context": "Validation des plugins", "integration_id": 15368 },
          { "context": "Portée des évals", "integration_id": 15368 } ] } }
  ]
}
```

## Ajouter une ligne

1. Une règle, une ligne. Dire ce qu'elle protège **avec la panne qu'elle évite**,
   pas seulement le geste qu'elle demande.
2. Dater l'origine et la relier à sa source (plan, incident, PR).
3. Citer le garde **en code**, avec son chemin : c'est ce que `check_skills.py`
   vérifie. Un garde qu'on ne peut pas encore écrire prend « prévu — étape X » ou
   « manquant » — jamais un « en place » sans garde.
4. Ajouter le garde dans **la même PR** que la ligne.
