# La veille avant chaque mise à jour d'un skill

Un fait de doc peut changer d'une version de Claude Code à l'autre. Un garde-fou
fondé sur un fait périmé protège la mauvaise chose — et rien ne rougit : la
règle passe, elle ne protège plus rien. La veille est ce qui nous dit, avant
qu'on écrive la règle suivante, que le sol a bougé.

Ce fichier a trois parties : **les sources** que l'on lit, **les faits porteurs**
dont dépendent nos règles (chacun avec sa citation mot pour mot), et **le journal
des passes**.

**La règle** — avant toute PR qui touche un skill, un agent, un hook ou un
`_partage/` : une passe de veille. L'agent `chercheur`, avec le brief de la partie
1, lit les sources **depuis la dernière passe** ; ce qui s'applique entre dans la
PR (ou dans un plan si c'est plus gros) ; l'entrée datée s'ajoute au journal
(partie 3). Deux gardes la tiennent (voir `docs/garde-fous.md`) :

- `scripts/check_veille.py` refuse une PR de skill si la dernière entrée du
  journal a **plus de 30 jours** (seuil `veille_jours_max` dans
  `scripts/limites.json`) ;
- `scripts/veille_faits.py`, joué chaque semaine par
  `.github/workflows/veille.yml`, relit chaque page du tableau et ouvre une issue
  « Doc Claude changée : <fait> » quand une citation n'y est plus. En local,
  `python3 scripts/veille_faits.py` ne crée rien : il rapporte.

## 1. Les sources

Dans l'ordre de lecture. Les pages `code.claude.com/docs/en/<page>` se lisent le
plus simplement en variante `.md`.

1. **La doc Claude Code** — [skills](https://code.claude.com/docs/en/skills.md),
   [sous-agents](https://code.claude.com/docs/en/sub-agents.md),
   [plugins](https://code.claude.com/docs/en/plugins.md),
   [référence des plugins](https://code.claude.com/docs/en/plugins-reference.md) et
   [chargement des plugins](https://code.claude.com/docs/en/plugins/loading.md),
   [hooks](https://code.claude.com/docs/en/hooks.md),
   [tests de plugin par évals](https://code.claude.com/docs/en/plugin-evals.md),
   [bac à sable](https://code.claude.com/docs/en/sandboxing.md),
   [mémoire](https://code.claude.com/docs/en/memory.md),
   [réglages](https://code.claude.com/docs/en/settings.md) ; puis le
   [changelog](https://code.claude.com/docs/en/changelog.md) et le
   [résumé hebdomadaire](https://code.claude.com/docs/en/whats-new/index.md).
2. **Les blogs d'Anthropic** — [claude.dev](https://claude.dev) en entier, pas
   seulement [le blog](https://claude.dev/blog) : ses rubriques Playbooks, Skills et
   Agents ne sont pas toutes dans le blog ; et
   [anthropic.com/engineering](https://www.anthropic.com/engineering). L'agent
   `chercheur` les lit aussi, avant le web général, quand il cherche pour un plan
   dont le sujet touche Claude (voir son agent).
3. **Les guides de `anthropics/skills`** —
   [le dépôt](https://github.com/anthropics/skills), dont `shared/evals/` quand il
   existe (introuvable le 2026-09-30 : le dépôt ne porte que `skills/`, `spec/` et
   `template/`).
4. **D'autres sources, quand elles sont pertinentes** — les issues amont (par
   exemple [anthropics/sandbox-runtime#74](https://github.com/anthropics/sandbox-runtime/issues/74),
   « bwrap fails on Ubuntu 24.04+ due to AppArmor userns restrictions », qui
   explique pourquoi Bash est impossible dans une éval sur le VPS ; le dépôt
   s'appelait `anthropic-experimental/sandbox-runtime`) et la doc des outils
   qu'un skill ou un garde-fou utilise : rulesets GitHub, Docker, AppArmor,
   Notion.

### Le brief à donner à `chercheur`

> Passe de veille sur les sources de `docs/veille.md`, partie 1, **depuis le
> <date de la dernière entrée du journal>**. Pour chaque source : ce qui a changé
> depuis cette date et qui touche les skills, les agents, les plugins, les hooks,
> les évals ou le bac à sable — avec l'URL et une citation exacte. Confronte chaque
> changement au tableau de la partie 2 : dis quels faits porteurs sont touchés (la
> citation n'y est plus, ou la règle qui en dépend ne tient plus). Rends une fiche
> courte, un bloc par source, ou « rien de neuf » avec ce que tu as lu. Ne modifie
> rien.

## 2. Les faits porteurs

Chaque fait dont dépend une règle ou un contrôle : sa **citation mot pour mot**,
relevée sur la page réelle (jamais de mémoire), son URL, la date de vérification et
le contrôle qui en dépend. `scripts/veille_faits.py` relit chaque page et vérifie
que la citation y figure toujours (comparaison tolérante aux espaces et à la casse,
pas au fond). Un fait qu'on ne retrouve pas sur la page n'entre pas au tableau.

| Fait | Citation | URL | Vérifié le | Contrôle qui en dépend |
| --- | --- | --- | --- | --- |
| La description d'un skill est tronquée à 1 536 caractères | « the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing to reduce context usage » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle a |
| `when_to_use` compte dans ce plafond | « counts toward the 1,536-character cap » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle a |
| Un `SKILL.md` reste sous 500 lignes | « Keep `SKILL.md` under 500 lines. » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle b |
| La compaction ne garde que les 5 000 premiers jetons d'un skill | « keeping the first 5,000 tokens of each » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle c |
| Trois champs sont ignorés pour un agent de plugin | « plugin subagents don't support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin. » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle f |
| `memory` active Read, Write et Edit | « Read, Write, and Edit tools are automatically enabled so the subagent can manage its memory files. » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle g |
| La mémoire de portée projet est faite pour être versionnée | « the subagent's knowledge is project-specific and shareable via version control » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle h |
| La mémoire d'agent locale vit sous `.claude/agent-memory-local/` | « `.claude/agent-memory-local/<name-of-agent>/` » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle h |
| La mise à jour compare la version, pas le contenu | « compute the version again and don't replace the cached copy when it matches what `installed_plugins.json` records » | https://code.claude.com/docs/en/plugins/loading.md | 2026-10-06 | `scripts/plugin_version_guard.py` |
| Le champ `version` du manifeste prime | « The `version` field in the plugin's manifest comes first » | https://code.claude.com/docs/en/plugins/loading.md | 2026-09-30 | `scripts/plugin_version_guard.py` |
| Sans `--no-publish`, le rapport d'éval sort de la machine | « Keep the HTML report local. » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `scripts/evals_ab.py` |
| `--ablation none` joue un seul bras | « `none` runs one arm; `with-without` adds the no-plugin baseline » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `scripts/evals_ab.py` |
| Bash dans une éval exige un bac à sable | « If you grant Bash or PowerShell on a machine with no sandbox backend, Claude Code refuses each run rather than running it unconfined » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `evals/outillage/preparer-runner.sh` |
| Le bac à sable échoue sur Ubuntu 24.04+ (AppArmor) | « bwrap fails on Ubuntu 24.04+ due to AppArmor userns restrictions » | https://github.com/anthropics/sandbox-runtime/issues/74 | 2026-09-30 | `evals/outillage/preparer-runner.sh` |
| L'effort d'un frontmatter (skill ou sous-agent) l'emporte sur l'effort de session, pas sur `CLAUDE_CODE_EFFORT_LEVEL` | « Frontmatter effort applies when that skill or subagent is active, overriding the session level but not the environment variable. » | https://code.claude.com/docs/en/model-config.md | 2026-10-08 | `evals/outillage/lancer.sh` |
| L'alias `haiku` désigne Haiku 5.5 depuis la 2.1.293 (API Anthropic seulement) | « `haiku` resolves to Haiku 5.5 on the Anthropic API » | https://code.claude.com/docs/en/model-config.md | 2026-10-08 | `evals/outillage/lancer.sh` |
| Le `model` du frontmatter l'emporte sur `CLAUDE_CODE_SUBAGENT_MODEL` | « `CLAUDE_CODE_SUBAGENT_MODEL` is a default, so a subagent's definition or a model Claude passes still takes precedence over it. » | https://code.claude.com/docs/en/sub-agents.md | 2026-10-08 | `evals/outillage/lancer.sh` |

## 3. Le journal des passes

Une entrée par passe, la plus récente en dernier. Le titre est
`### AAAA-MM-JJ — <objet>` : `scripts/check_veille.py` en lit la date.

### 2026-09-30 — passe initiale, à l'ouverture de l'étape A7b

- **Sources lues** : les pages de doc Claude Code de la partie 1 qui portent les
  faits du tableau (skills, sous-agents, chargement des plugins, tests de plugin
  par évals) et l'issue `sandbox-runtime#74`.
- **Ce qui a changé** : rien à comparer, c'est la première passe. Quatre constats à
  la lecture : le dépôt `anthropic-experimental/sandbox-runtime` est devenu
  `anthropics/sandbox-runtime` ; le dossier `shared/evals/` de `anthropics/skills`
  est introuvable ; `claude.dev/blog` et `anthropic.com/engineering` répondent, mais
  aucun fait du tableau n'en dépend ; les 500 lignes d'un `SKILL.md` sont une
  recommandation (« Tip »), pas une limite appliquée.
- **Ce qu'on en fait** : les quatorze faits ci-dessus entrent au tableau, chacun avec
  sa citation relevée sur la page du jour ; `veille_faits.py` les rejoue chaque
  semaine ; le seuil de 30 jours part de cette date.

### 2026-10-01 — claude.dev entre dans les sources, à l'étape 13 du plan « Évals sobres et machine partagée »

- **Sources lues** : [claude.dev](https://claude.dev) (page d'accueil, via
  `WebFetch`) et, dans sa rubrique Playbooks, l'article « Automating eval design and
  hillclimbing with Claude ». Un second article, « What a task costs on Opus 5.5 »
  (2026-09-23), est noté mais **pas lu**.
- **Ce qui a changé** : le site est publié par Anthropic (« Sharing tips, tricks, and
  POVs from Anthropic's developers ») et porte des rubriques Agents, Engineering,
  Playbooks et Skills en plus du blog. Aucun fait du tableau de la partie 2 n'en
  dépend, donc aucun n'est touché.
- **Ce qu'on en fait** : la source 2 de la partie 1 s'élargit de `claude.dev/blog` à
  `claude.dev` entier ; l'agent `chercheur` gagne une section « Sources d'abord » qui
  l'y envoie avant le web général. L'article sur les évals confirme deux choix du
  plan : garder trois passages pour que le bruit reste sous la plus petite
  amélioration visée, et ne pas laisser une panne d'infrastructure passer pour une
  variance du modèle. **À lire à la prochaine passe** : « What a task costs on
  Opus 5.5 », pour recaler nos estimations de coût.

### 2026-10-06 — passe avant la création du plugin voyages (plan « Création d'un cron Voyage »)

- **Sources lues** : la doc Claude Code (skills, sous-agents, référence des plugins,
  chargement des plugins, tests de plugin par évals, bac à sable, changelog de la
  2.1.284 à la 2.1.291, résumé hebdomadaire) ; claude.dev (accueil, « Claude Code in
  the cloud: a field guide to cloud sessions » du 2026-10-01 et « What a task costs
  on Opus 5.5 » du 2026-09-23, ce dernier lu **par résumé**) ;
  anthropic.com/engineering (rien de nouveau depuis le 2026-04-23) ;
  `anthropics/skills` (toujours pas de `shared/evals/`) ; `sandbox-runtime#74`
  (toujours ouverte). Les pages hooks, mémoire, réglages et plugins n'ont **pas** été
  relues en entier.
- **Ce qui a changé** : aucun fait porteur du tableau de la partie 2 n'est touché en
  substance. Changelog : la 2.1.287 (« Claude Mods », hooks de plugin plus profonds) et
  un correctif du nom d'un skill dont le dossier diffère ; la 2.1.288, des agents de
  plugin lancés par nom avec leur propre prompt et leurs outils ; la 2.1.289, la copie
  périmée d'un plugin installé depuis une marketplace en dossier local. `skills.md`
  porte un tableau « Available string substitutions » : `${CLAUDE_SKILL_DIR}` (« The
  directory containing the skill's `SKILL.md` file… ») et `${CLAUDE_PLUGIN_ROOT}`
  (« Substituted only in plugin skills »), substitués dans le corps Markdown
  (`plugins-reference.md`, « Where each variable resolves »). `sandboxing.md` porte un
  encadré « Ubuntu 24.04 and later: allow bubblewrap to create user namespaces »
  (profil AppArmor `bwrap`). Opus 5.5 « costs 40% less to run than Opus 5 » mais peut
  dépenser plus de jetons de réflexion : à mesurer avant d'en tirer une estimation.
- **Ce qu'on en fait** : le skill `organiser-voyage` est aussi installé par Hermes, qui
  ne connaît ni `${CLAUDE_SKILL_DIR}` ni `${CLAUDE_PLUGIN_ROOT}` (Hermes substitue
  `${HERMES_SKILL_DIR}`, dans `SKILL.md` seulement, et n'installe que les fichiers que
  `SKILL.md` cite) : `$DOSSIER_SKILL` est donc défini dans `SKILL.md` pour les deux
  hôtes. L'encadré AppArmor est à relire pour `evals/outillage/preparer-runner.sh` (plan
  à venir, pas celui-ci). Aucune autre règle à changer.
- **Verdict de `scripts/veille_faits.py`** (2026-10-06) : 14 faits vérifiés, 13 citations
  trouvées, 1 introuvable — « La mise à jour compare la version, pas le contenu »
  (`plugins/loading.md`) : la page dit désormais « don't replace the cached copy when it
  matches what `installed_plugins.json` records » au lieu de « skip the plugin when it
  matches… ». Sens inchangé ; la citation du tableau est à reporter à la prochaine
  édition de ce fichier (remplacée le jour même, étape D2) (le workflow hebdomadaire ouvrira une issue d'ici là), 0 page
  injoignable.

### 2026-10-08 — passe avant le plan « Haiku et effort pour les sous-agents, banc d'évals plus sobre »

- **Sources lues** : la doc Claude Code, lue sur ses 100 000 premiers caractères pour
  les pages longues (sous-agents, configuration des modèles, changelog de la 2.1.291 à
  la 2.1.294, skills, hooks) et en entier pour le chargement des plugins, la référence
  des plugins, le conseiller (`advisor.md`) et les tests de plugin par évals ; claude.dev
  (« Getting started with Claude Code mods » du 2026-10-01, « Using Claude Code: Spending
  your effort » du 2026-09-25 ; « Building with Claude Sonnet 5.5 » du 2026-09-28 **non
  lu**) ; anthropic.com/engineering (rien de nouveau depuis le 2026-04-23) ;
  `anthropics/skills` (toujours pas de `shared/evals/`) ; `sandbox-runtime#74` (toujours
  ouverte). Les pages plugins, mémoire et réglages n'ont **pas** été relues.
- **Ce qui a changé** : aucun des quatorze faits porteurs n'est cassé, leurs citations
  sont encore sur leurs pages. Trois changements touchent ce plan sans en casser un.
  (1) La 2.1.293 ajoute Claude Haiku 5.5 (`claude-haiku-5-5`), désormais le Haiku par
  défaut de l'API Anthropic : 1 M de contexte, 0,10 $ / 0,50 $ le million de jetons, et
  0,50 $ / 2,50 $ au-delà de 100 000 jetons de prompt. L'alias `haiku` désigne Haiku 5.5
  sur l'API Anthropic, mais **Haiku 4.5** sur Claude Platform on AWS, Bedrock, Google
  Cloud's Agent Platform et Microsoft Foundry ; Haiku 4.5 ne figure pas dans la table des
  niveaux d'effort, donc ne prend aucun effort. Haiku 5.5 démarre à l'effort `medium`,
  comme Opus 5.5 et Sonnet 5.5. (2) La 2.1.292 ajoute un paramètre `effort` à l'outil
  Agent : il n'est écrit que dans le changelog, ni `sub-agents.md` ni la référence des
  outils n'en parlent, et rien n'y dit s'il l'emporte sur le champ `effort` du
  frontmatter. (3) `claude plugin eval` n'a aucune option d'effort, seulement `--model`.
  Résolution déjà écrite : pour le modèle d'un sous-agent, le paramètre de l'appel, puis
  le frontmatter, puis `CLAUDE_CODE_SUBAGENT_MODEL`, puis la conversation ; pour l'effort,
  le frontmatter l'emporte sur la session mais pas sur `CLAUDE_CODE_EFFORT_LEVEL`, et un
  plafond `maxEffortLevel` ou d'organisation borne encore le niveau joué.
- **Ce qu'on en fait** : cinq faits entrent au tableau de la partie 2 (effort de
  frontmatter face à l'effort de session, alias `haiku`, effort par défaut de Haiku 5.5,
  priorité du `model` du frontmatter sur `CLAUDE_CODE_SUBAGENT_MODEL`, paramètre `effort`
  de l'outil Agent), chacun avec sa citation relevée sur la page du jour. Dans ce plan :
  la fumée gagne un cache par catégorie, qui ne rejoue pas une fumée verte tant que sa clé
  ne change pas (étape 1), et l'A/B complet devient l'exception, réservé à un changement
  de règle de comportement ou de modèle d'un agent (étape 2) ; le registre des garde-fous
  et la fiche de `claude plugin eval` le disent. À garder en tête pour une éventuelle
  bascule d'agents sur Haiku : hors API Anthropic l'alias `haiku` vaut Haiku 4.5, qui ne
  prend pas d'effort ; un `effort:` écrit dans le frontmatter d'un tel agent n'aurait
  alors aucun effet. Le paramètre `effort` de l'outil Agent (2.1.292) n'est documenté que
  dans le changelog, et sa priorité face au `effort:` d'un frontmatter n'est écrite
  nulle part : ne pas la supposer, la mesurer avant de s'en servir.
- **Verdict de `scripts/veille_faits.py`** (2026-10-08) : 19 faits vérifiés, 19 citations
  trouvées, 0 introuvable, 0 page injoignable. Aucune ligne candidate n'a été retirée
  (« non inscrite : citation introuvable » : aucune).
- **Correctif de clôture** (2026-10-08) : seuls trois des cinq faits cités plus haut restent
  au tableau de la partie 2 (effort de frontmatter, alias `haiku`, priorité du `model` du
  frontmatter), chacun relié à `evals/outillage/lancer.sh`, le script dont il dépend. Les
  deux autres (Haiku 5.5 démarre à l'effort `medium`, paramètre `effort` de l'outil Agent
  de la 2.1.292) n'y sont pas : aucun script n'en dépend, et le tableau ne porte que des
  faits qu'un contrôle utilise. Ils restent dits dans cette entrée. Nouveau compte rejoué
  par `scripts/veille_faits.py` : 17 faits vérifiés, 0 citation à signaler, 0 page
  injoignable ; le verdict à 19 faits ci-dessus reste celui de la passe.

### 2026-10-09 — passe avant la fiche « Claude Code sur un serveur à plusieurs comptes » du registre des outils

- **Sources lues** : la page d'installation de Claude Code (`setup`), en entier.
  Les autres sources n'ont **pas** été relues depuis la passe du 2026-10-08.
- **Ce qui a changé** : rien de cassé. La page documente un dépôt apt, dnf et apk
  signé, avec deux canaux (`stable`, environ une semaine de retard, sans les
  versions à régression majeure ; `latest`), et l'empreinte de la clé de
  signature. Elle précise que ces installations ne se mettent pas à jour par
  Claude Code, mais par le circuit de mise à jour du système.
- **Ce qu'on en fait** : une fiche entre au registre des outils
  (`outils-et-quotas.md`). Elle ne change aucune consigne de skill ni d'agent :
  aucun fait n'entre au tableau de la partie 2, aucun script n'en dépend.
- **Verdict de `scripts/veille_faits.py`** (2026-10-09) : 17 faits vérifiés,
  0 citation à signaler, 0 page injoignable.

### 2026-10-09 — passe avant le plan « POC en Haiku et carte de voisinage par le graphe avant l'enquête »

- **Sources lues** : la doc Claude Code, page `sub-agents.md`, relevée par le `chercheur`
  le 2026-10-09 ; le reste (faits du pilote, dépôt hermes-custom) n'est pas une source
  de la doc. Aucune autre page n'a été relue pour cette passe.
- **Ce qui a changé** : rien de cassé. L'ordre de résolution du modèle d'un sous-agent
  (paramètre `model` de l'appel, puis `model` du frontmatter, puis
  `CLAUDE_CODE_SUBAGENT_MODEL`, puis le modèle principal) est inchangé ; il est déjà écrit
  à la ligne 98. Le paramètre `effort` de l'outil Agent (2.1.292, noté le 2026-10-08) a été
  **utilisé** le 2026-10-09 par le pilote, dans le POC P1 : `model` et `effort: "high"` à
  l'appel, sans erreur. Ce n'est qu'un essai, pas une documentation : la priorité de cet
  effort face au `effort:` d'un frontmatter reste à mesurer, comme l'entrée précédente
  le dit.
- **Ce qu'on en fait** : le choix d'un sondeur en Haiku `high`, sans `model` ni `effort` à
  l'appel, s'appuie sur le POC P1 (`poc.md`, « Qui joue le POC »). L'appel à
  `effort: "high"` reste une option du pilote ; aucune page lue ici n'en fixe la priorité.
- **Ce que la passe d'avant porte encore** : l'alias `haiku` (Haiku 4.5 hors API
  Anthropic, sans effort), la 2.1.293 et le modèle Haiku 5.5 par défaut de l'API. Rien
  n'a changé sur ces points.
- **Hors doc, transmis par le pilote** : codebase-memory est épinglé en 0.10.8 jusqu'au
  2026-11-09 (hermes-custom PR #564), la 0.11.0 ne résolvant plus les appels via
  `importlib`. Cette passe ne l'a pas revérifié dans hermes-custom. Ce n'est pas un fait de
  la doc Claude Code : il ne vaut que pour le poste. Aucun fait porteur cassé à la date de
  cette passe.
