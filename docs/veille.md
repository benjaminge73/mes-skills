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

**Le déclencheur « nouveau modèle ».** Le garde de 30 jours ne voit pas un modèle
nouveau : une passe récente peut devenir fausse le jour où sort un modèle, ou le jour
où un alias change de sens. Donc, en plus de la règle des 30 jours : quand Anthropic sort
un modèle (une nouvelle génération d'Opus, de Sonnet ou de Haiku) ou qu'un alias (`opus`,
`sonnet`, `haiku`) se met à servir un autre modèle, la session le dit à Benjamin et lui
propose une passe de veille avant la prochaine PR qui touche un skill, un agent, un hook
ou un `_partage/`, sans bloquer celle en cours. Le rappel de clôture ne bloque ni la porte
ni `a merger` : faire la passe d'abord est une décision de Benjamin. La passe reste exigée
par `scripts/check_veille.py` selon son propre garde (30 jours). On relit alors l'alias et le modèle servi, l'effort par défaut, les tarifs
(les lignes de la partie 2 qui les citent), puis on ajoute une entrée au journal. Exemple
vécu : la 2.1.293, relevée dans la passe du 2026-10-08, a fait de `haiku` Haiku 5.5 sur
l'API Anthropic. La clôture d'un plan qui touche ces fichiers rappelle ce déclencheur
(`plugins/plans-notion/skills/executer-plan-notion/cloture-pr-et-ci.md`, point 2 quater). Le
déclencheur ne détecte rien tout seul : c'est la session qui constate l'arrivée d'un modèle
(annonce, changelog, alias) et compare à la date de la dernière entrée du journal.

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

   Les dépôts de skills tiers ne se relisent pas à la main à chaque passe : le
   cron Hermes `veille-skills` (côté `hermes-custom`) les suit chaque lundi. Il relit
   par `gh api` les dépôts de `config/veille-skills.json` (dont `anthropics/skills`,
   source 3 ci-dessus) et les favoris étoilés de Benjamin ; ses propositions arrivent
   dans la page Notion `[Plan] mes-skills - Adoption de skills externes` (suffixe `#N`
   si la série en compte plusieurs). Depuis le plan « Veille par articles » (PR
   `feat/veille-articles` de `hermes-custom`), il lit aussi les articles des flux de
   neuf blogs : claude.dev, Addy Osmani, martinfowler.com, Jesse Vincent, Simon Willison,
   Hamel Husain, et Armin Ronacher, Geoffrey Huntley et le blog
   GitHub (rubrique IA), marqués `strict` dans la config (étiquette transmise à la session, sans effet propre), ainsi que les liens que Benjamin envoie à Hal. Il en tire des
   bonnes pratiques, confrontées à ce que `mes-skills` fait déjà ; elles arrivent dans
   un chapitre « Adopter une bonne pratique » de la même page. La passe manuelle garde
   son rôle : vérifier les faits porteurs avant une PR de skill. Le journal des passes
   garde ses billets « non lus, à reprendre ».
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
**Un contrôle est un script, un cas d'éval ou un job de la CI** : la dernière colonne
cite un fichier de `scripts/`, `evals/` ou `.github/`, jamais une consigne en prose, et
`scripts/test_veille_faits.py` (`test_le_tableau_reel_est_lisible_et_ses_controles_existent`) refuse un fait dont le contrôle n'en cite aucun.

| Fait | Citation | URL | Vérifié le | Contrôle qui en dépend |
| --- | --- | --- | --- | --- |
| La description d'un skill est tronquée à 1 536 caractères | « the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing to reduce context usage » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle a |
| `when_to_use` compte dans ce plafond | « counts toward the 1,536-character cap » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle a |
| Un `SKILL.md` reste sous 500 lignes | « Keep `SKILL.md` under 500 lines. » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle b (cliquet par fichier : le plafond de chaque fichier se lit dans `scripts/limites.json`, ce n'est pas un test de 500 lignes) |
| La compaction ne garde que les 5 000 premiers jetons d'un skill | « keeping the first 5,000 tokens of each » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle c |
| Trois champs sont ignorés pour un agent de plugin | « plugin subagents don't support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin. » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle f |
| `memory` active Read, Write et Edit | « Read, Write, and Edit tools are automatically enabled so the subagent can manage its memory files. » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle g |
| La mémoire de portée projet est faite pour être versionnée | « the subagent's knowledge is project-specific and shareable via version control » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle h (la règle h interdit tout `.claude/agent-memory*` dans ce dépôt : il applique la conclusion inverse de la citation) |
| La mémoire d'agent locale vit sous `.claude/agent-memory-local/` | « `.claude/agent-memory-local/<name-of-agent>/` » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle h |
| La mise à jour compare la version, pas le contenu | « compute the version again and don't replace the cached copy when it matches what `installed_plugins.json` records » | https://code.claude.com/docs/en/plugins/loading.md | 2026-10-06 | `scripts/plugin_version_guard.py` |
| Le champ `version` du manifeste prime | « The `version` field in the plugin's manifest comes first » | https://code.claude.com/docs/en/plugins/loading.md | 2026-09-30 | `scripts/plugin_version_guard.py` |
| Sans `--no-publish`, le rapport d'éval sort de la machine | « Keep the HTML report local. » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `evals/outillage/lancer.sh` |
| `--ablation none` joue un seul bras | « `none` runs one arm; `with-without` adds the no-plugin baseline » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `evals/outillage/lancer.sh` |
| Bash dans une éval exige un bac à sable | « If you grant Bash or PowerShell on a machine with no sandbox backend, Claude Code refuses each run rather than running it unconfined » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `evals/outillage/preparer-runner.sh` |
| Le bac à sable échoue sur Ubuntu 24.04+ (AppArmor) | « bwrap fails on Ubuntu 24.04+ due to AppArmor userns restrictions » | https://github.com/anthropics/sandbox-runtime/issues/74 | 2026-09-30 | `evals/outillage/preparer-runner.sh` |
| L'effort d'un frontmatter (skill ou sous-agent) l'emporte sur l'effort de session, pas sur `CLAUDE_CODE_EFFORT_LEVEL` | « the skill or subagent runs at its level, whatever level you launch with, save, or pick. If `CLAUDE_CODE_EFFORT_LEVEL` is set, that level applies instead. » | https://code.claude.com/docs/en/model-config.md | 2026-11-16 | `evals/outillage/lancer.sh` |
| L'alias `haiku` désigne Haiku 5.5 depuis la 2.1.293 (API Anthropic seulement) | « `haiku` resolves to Haiku 5.5 on the Anthropic API » | https://code.claude.com/docs/en/model-config.md | 2026-10-08 | `evals/outillage/lancer.sh` (aucune dépendance directe : il ne nomme pas cet alias ; l'alias est posé par `model: haiku` dans le frontmatter de `plugins/plans-notion/agents/executant.md`, que les évals jouent) |
| Le `model` du frontmatter l'emporte sur `CLAUDE_CODE_SUBAGENT_MODEL` | « When more than one source sets a model, Claude Code uses the first in this order: » | https://code.claude.com/docs/en/sub-agents.md | 2026-11-16 | `evals/outillage/lancer.sh` (aucune dépendance directe : il ne pose pas `CLAUDE_CODE_SUBAGENT_MODEL` ; la priorité jouée est celle de `model: haiku` dans le frontmatter de `plugins/plans-notion/agents/executant.md`) |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` fait ignorer le `model` du frontmatter (exception à la ligne précédente) | « Claude Code ignores the `model` field in subagent definitions, and Claude can't pass a model when it starts a subagent » | https://code.claude.com/docs/en/sub-agents.md | 2026-11-16 | `evals/outillage/lancer.sh` (aucune dépendance directe : il ne pose pas `CLAUDE_CODE_SUBAGENT_MODEL` ; la priorité jouée est celle de `model: haiku` dans le frontmatter de `plugins/plans-notion/agents/executant.md`) |
| Un `CLAUDE.md` vise moins de 200 lignes | « target under 200 lines per CLAUDE.md file » | https://code.claude.com/docs/en/memory.md | 2026-10-12 | `scripts/test_taille_claude_md.py` (plafond de `taille-claude-md.py`, joué par `scripts/ci_locale.sh`, section `garde`) |
| Pour alléger un `CLAUDE.md`, on sort la consigne vers un skill ou une règle à portée de chemin | « move it to a [skill](https://code.claude.com/docs/en/skills.md) or a [path-scoped rule](#organize-rules-with-claude/rules/) instead » | https://code.claude.com/docs/en/memory.md | 2026-11-16 | `scripts/test_taille_claude_md.py` (le guide `_partage/ranger-claude-md.md` reprend cette consigne) |
| Sur Opus 5.5 et Sonnet 5.5, une lecture de cache coûte 0,05 × le prix d'entrée (0,20 $ et 0,10 $) | « Cache hits and refreshes on Claude Opus 5.5 and Claude Sonnet 5.5 are priced at 0.05x the base input price. » | https://platform.claude.com/docs/en/about-claude/pricing.md | 2026-11-16 | `scripts/test_cout_plan.py` (classe `GrilleReelle`, lit `plugins/plans-notion/skills/_partage/scripts/grille-tarifs.json`) |
| `maxTurns` arrête un sous-agent et marque sa sortie partielle | « Maximum number of agentic turns before the subagent stops. » | https://code.claude.com/docs/en/sub-agents.md | 2026-10-16 | `evals/plans-notion/escalade-bornee/case.yaml` (le cas qui joue l'escalade après l'arrêt d'un exécutant ; `maxTurns: 90` est posé dans `plugins/plans-notion/agents/executant.md`, `scripts/check_skills.py` (règle k) exige qu'il soit fixé) |
| Les skills réattachés après compaction se partagent 25 000 jetons | « Re-attached skills share a combined budget of 25,000 tokens. » | https://code.claude.com/docs/en/skills.md | 2026-10-16 | `scripts/check_skills.py` règle c (contrôle partiel : seul le plafond des jetons d'invariants, `JETONS_INVARIANTS`, est vérifié, pas le budget partagé ; c'est la raison de « ré-invoquer le skill après un compactage ») |

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
  au tableau de la partie 2 (ligne sur `CLAUDE_CODE_SUBAGENT_MODEL`). Le paramètre `effort` de l'outil Agent (2.1.292, noté le 2026-10-08) a été
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

### 2026-10-09 — passe avant la PR « le hook Statut ne refuse que les valeurs de plan »

- **Sources lues** : la doc Claude Code, page `hooks.md`, relue par le pilote le
  2026-10-09 (pas de `chercheur` : une seule page porte le fait dont dépend ce hook).
- **Ce qui a changé** : rien. Pour `PreToolUse`, un code de sortie 2 bloque toujours
  l'appel d'outil, et le message est toujours la sortie d'erreur (« `PreToolUse` blocks
  the tool call ») ; `tool_input` arrive toujours sur l'entrée standard.
- **Ce qu'on en fait** : rien à changer au contrat du hook ; la PR ne touche que sa
  règle de refus.
- **Verdict de `scripts/veille_faits.py`** (2026-10-09) : 17 faits vérifiés,
  0 citation à signaler, 0 page injoignable.

### 2026-10-12 — passe avant l'étape 2 du plan « mes-skills — CLAUDE.md tenus, coût des plans, jeton lourd et délégation à Haiku »

- **Sources lues** : la page mémoire de la doc Claude Code (`memory.md`), pour les deux
  citations de la limite de 200 lignes et de la consigne de rangement, relevées dans sa
  version `.md`. Les autres sources de la partie 1 n'ont **pas** été relues pour cette
  entrée.
- **Ce qui a changé** : rien de cassé sur les points relevés. « target under 200 lines per
  CLAUDE.md file » figure à la section « Size ». La consigne de rangement figure à la
  section sur les `CLAUDE.md`, mais le texte rendu (« move it to a skill or a path-scoped
  rule instead ») porte dans la source les liens `[skill]` et `[path-scoped rule]` : la
  citation du tableau garde donc ce balisage, pour que `scripts/veille_faits.py`, qui
  compare à la source, la retrouve.
- **Ce qu'on en fait** : les deux citations entrent au tableau de la partie 2, avec pour
  contrôle `scripts/test_taille_claude_md.py`. Le garde de taille (`taille-claude-md.py`,
  plugin `plans-notion`) est joué par `scripts/ci_locale.sh`, section `garde`, et sa ligne
  entre au registre des garde-fous.
- **Verdict de `scripts/veille_faits.py`** (2026-10-12) : 19 faits vérifiés, 0 citation à
  signaler, 0 page injoignable.

### 2026-10-12 — veille des tarifs, étape 7 du plan « CLAUDE.md tenus, coût des plans, jeton lourd et délégation à Haiku »

- **Sources lues** : la page tarifs d'Anthropic, en source `.md`
  (`https://platform.claude.com/docs/en/about-claude/pricing.md`) : le tableau « Model
  pricing », ses notes sous le tableau, la section sur le cache et celle sur le palier
  de Haiku 5.5. Les autres sources de la partie 1 n'ont **pas** été relues pour cette
  entrée. L'alias `opus` / `sonnet` / `haiku` de la doc des modèles n'a pas été relu
  non plus : il reste à revérifier avant toute règle qui en dépend.
- **Ce qui a changé** : le prix de la lecture de cache de Sonnet 5.5 est de 0,10 $ par
  million de jetons, et non 0,20 $ comme la grille le donnait par déduction. Pour Opus
  5.5, la lecture vaut 0,20 $ : c'est 0,05 × le prix d'entrée, comme pour Sonnet 5.5.
  Haiku 5.5 a deux paliers selon la longueur du prompt (jusqu'à 100 000 tokens, puis
  au-delà), et `cout-plan.py` ne lit que le premier.
- **Ce qu'on en fait** : la grille `grille-tarifs.json` est corrigée (tous les prix
  sont marqués relevés, lecture de Sonnet 5.5 à 0,10 $, palier au-delà de Haiku 5.5 dans
  un champ à part) ; le test `GrilleReelle` de `scripts/test_cout_plan.py` la compare à la
  page. Le fait « lecture à 5 % du prix d'entrée » entre au tableau de la partie 2, avec
  ce test pour contrôle. Deux fiches entrent au registre des outils : « Abonnement Claude
  Max » et « ccusage ».
- **Verdict de `scripts/veille_faits.py`** (2026-10-12) : 20 faits vérifiés, 0 citation à
  signaler, 0 page injoignable.

### 2026-10-15 — passe avant la PR « la preuve doc » (plan « mes-skills — La doc suit le plan »)

- **Sources lues** : toutes celles de la partie 1, depuis la passe du 2026-10-12 : la doc
  Claude Code (skills, sous-agents, plugins et chargement, hooks, évals, bac à sable,
  mémoire, réglages, modèles, changelog, résumé hebdomadaire), les blogs d'Anthropic
  (`claude.dev`, `anthropic.com/engineering`), le dépôt `anthropics/skills`, l'issue
  amont `sandbox-runtime#74`, la page des tarifs. Les pages de la doc Claude Code ont été
  lues rendues par `WebFetch` ; les citations de `plugin-evals`, `memory`, `pricing` et
  `sandboxing` ont en plus été vérifiées mot pour mot dans le texte brut.
- **Ce qui a changé** : le changelog 2.1.299 et 2.1.300 (14 oct.) n'atteint aucun fait du
  tableau. À noter : `--tools ""` ne retire pas les outils MCP (« The flag doesn't affect
  MCP tools »), d'où `--strict-mcp-config` dans l'appel du juge ; l'alias `haiku` se résout
  selon le fournisseur (« The `opus`, `sonnet`, and `haiku` aliases resolve to the newest
  version on the Anthropic API and to an earlier version on some other providers »), ce
  qui explique le Haiku 4.5 servi sur ce poste, où `ANTHROPIC_BASE_URL` est posée ;
  le plafond de 1 536 caractères d'une description est un défaut, configurable par
  `skillListingMaxDescChars` (la règle (a) de `check_skills.py` suppose la valeur par
  défaut) ; le paramètre `effort` de l'outil Agent est désormais documenté (la question
  laissée ouverte au journal du 2026-10-08 est fermée) ; `onFailure: "block"` existe pour
  les hooks `command` et `http` (2.1.295), par défaut un hook en échec laisse passer.
  `modelUsage` n'est nommé que dans le guide du SDK : la doc de `claude -p` ne le promet
  pas, d'où la vérification en exécution que fait `qualite-doc.py juger` (code 5).
  Deux corrections de journal : l'article `claude.dev` « field guide » date du 6 oct.
  (et non du 1ᵉʳ), et `anthropic.com/engineering` a un article du 25 mai 2026 (le journal
  disait « rien depuis le 2026-04-23 »). Les versions 2.1.295 et 2.1.296 du changelog
  n'avaient pas été relues depuis le 2026-10-08.
- **Ce qu'on en fait** : rien ne change au tableau de la partie 2. Le juge de la preuve
  doc épingle `claude-haiku-5-5` (`MODELE` de `qualite-doc.py`) et vérifie le modèle servi,
  ce que la doc confirme nécessaire.
- **Verdict de `scripts/veille_faits.py`** (2026-10-15) : 20 faits vérifiés, 0 citation à
  signaler, 0 page injoignable.

### 2026-10-16 — passe avant le plan « mes-skills — Relecteur Opus high, retours hors plan en autonomie, escalade bornée et brainstorming cadré »

- **Sources lues** : quatre pages, téléchargées par le pilote et lues depuis ce téléchargement :
  la doc des sous-agents (`https://code.claude.com/docs/en/sub-agents.md`), la doc des skills
  (`https://code.claude.com/docs/en/skills.md`), la doc de Claude Code Review
  (`https://code.claude.com/docs/en/code-review.md`) et le guide de prompts
  (`https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices.md`).
  Chaque citation a été retrouvée sur sa page par `grep`. Seuls deux faits entrent au tableau (`maxTurns`, budget de 25 000 jetons) : `scripts/test_veille_faits.py` exige qu'un fait cite un script, un cas d'éval ou un job de CI comme contrôle, et la revue hébergée, la délégation d'Opus 5 et le « si dans le doute » n'en ont aucun ; ils restent lus et écrits ici.
  **Non lu** : le guide `prompting-claude-opus-5`, que le guide de prompts renvoie pour le détail
  propre à Opus 5 (contrôle des sous-agents, verbosité, dépassement de portée).
- **Ce qui a changé** :
  - **`maxTurns`** (sous-agents) : champ de frontmatter. À la limite, Claude Code rend la sortie
    marquée « partielle » et Claude peut reprendre le sous-agent (`SendMessage`). Le marquage
    exige Claude Code v2.1.246 ou plus.
  - **Skills** : `SKILL.md` sous 500 lignes ; `description` et `when_to_use` tronqués à 1 536
    caractères (`when_to_use` compte dans ce plafond). Après compaction, les 5 000 premiers
    jetons de chaque skill sont gardés, et les skills réattachés se partagent un budget commun
    de 25 000 jetons. Le `model` d'un skill vaut pour le reste du tour en cours ; la durée de
    son `effort` n'est pas dite par la page (« when this skill is active »).
  - **Guide de prompts, Opus 4.5 et 4.6** : il faut baisser le ton des consignes agressives (la
    page le dit pour Opus 4.5 et 4.6). La section Opus 4.6 écrit « Remove over-prompting. » et
    donne l'exemple « If in doubt, use [tool] », qui « will cause overtriggering ». Le guide
    dit aussi, en général, qu'expliquer la raison d'une consigne aide le modèle.
  - **Guide de prompts, Opus 5** : Opus 5 « delegates to subagents more readily than prior
    models ». Le détail (contrôle de la délégation) est dans le guide `prompting-claude-opus-5`,
    non lu.
  - **Claude Code Review** : service hébergé sur l'infrastructure d'Anthropic, pour les plans
    Team et Enterprise, sur dépôts GitHub. Il commente en ligne, avec un résumé et un check run,
    et « a review never approves or blocks the pull request ». Il ne remplace pas le `relecteur`.
    Tarif et quota : non lus.
- **Ce qu'on en fait** : `maxTurns: 90` est posé sur l'`executant` (le fichier le porte déjà). La
  mesure qui le justifie, relevée sur 14 jours et rapportée par le pilote, porte sur 676
  exécutants : médiane 27 tours, 95e centile 73, maximum 158. Le relecteur reste en Opus, effort
  `high`. Rien d'autre ne change au tableau de la partie 2 hors les deux lignes ajoutées. Le
  registre `docs/garde-fous.md` reçoit une ligne par règle posée (quatre : la porte `pret` a déjà la sienne),
  dont deux « en place » (cas `revue-hors-plan` et `escalade-bornee`) et deux « manquant » (`maxTurns`, citation d'une case cochée).
- **Verdict de `scripts/veille_faits.py`** (2026-10-16) : 22 faits vérifiés, 0 citation à
  signaler, 0 page injoignable (code 0).

### 2026-10-21 — passe avant la PR « gestes Notion du plugin plans-notion » (plan « micro-trading — collecte des jetons diplômés », étapes 1, 8 et 9)

- **Sources lues** : le changelog Claude Code, le résumé hebdomadaire, les docs skills, sous-agents
  et référence des plugins ; la spec Notion (`developers.notion.com` : enhanced-markdown v1,
  notion-flavored-markdown v2 en aperçu, working-with-markdown-content) ; les releases GitHub de
  `anthropics/claude-code`. **Les citations de cette entrée ont été extraites par un modèle
  intermédiaire : elles sont à reconfirmer par `grep` sur les pages avant de s'y fier**, et
  rien ici ne les a reconfirmées.
- **Ce qui a changé** :
  - Changelog, versions 2.1.302 à 2.1.306 (du 16 au 21 oct.) :
    - reprise d'un sous-agent juste après sa fin, corrigée en 2.1.304 (« Before v2.1.304, a subagent
      that Claude messaged or resumed right after it finished could forget its most recent work. ») ;
    - 2.1.302 : au plus 12 hooks `prompt` ou `agent` d'un même événement en parallèle ;
    - 2.1.304 : plafond de 1 024 hooks et de 16 384 caractères de matcher par source et par session,
      et compaction qui renvoie la liste des skills ;
    - 2.1.302 : sous-agents forkés par défaut dans `claude -p`, le SDK, l'app bureau et VS Code
      (`CLAUDE_CODE_FORK_SUBAGENT=0` les coupe) ;
    - 2.1.305 : `allowed-tools` ignoré sous `allowManagedPermissionRulesOnly` (sans effet sur ce poste).
    Aucun ne contredit un fait du tableau de la partie 2.
  - **Notion** : la spec REST publique « enhanced markdown » (v1) prescrit `{color="…"}` en fin de
    première ligne d'un bloc, et `<details><summary>` pour le repliable ; la v2 (aperçu) écrit le
    repliable `<toggle heading=… color=…>`. Or le connecteur Notion de claude.ai (outils
    `notion-fetch` et `notion-update-page`, avec sa spec `notion://docs/notion-flavored-markdown-spec`)
    a été **mesuré le 2026-10-21** sur une page de test : `{color=…}` s'enregistre comme texte visible ;
    la couleur passe par l'attribut de la balise (`<p color="blue">`, `<span color="blue">`) ;
    `<details>` est converti en `<toggle>` avec l'avertissement « legacy Markdown ».
  - Non vérifié : la version Markdown que le MCP envoie, et les attributs de `<embed>`.
- **Ce qu'on en fait** : rien ne change au tableau de la partie 2 (aucun fait n'a de contrôle
  pour entrer). Les plugins de ce dépôt n'écrivent que par le connecteur, pas par l'API REST :
  le garde suit donc le connecteur. La règle (n) de `scripts/check_skills.py` tient la correction
  de l'étape 8 (qui a retiré `{color=` et `<details>` des fichiers `_partage/`, commit `7083cdd`) : elle
  refuse `{color=`, `<details>` et `<summary>` dans tout `skills/**/*.md`, en citant le fichier et
  la ligne. Ligne du registre : « Les syntaxes Notion interdites n'entrent pas dans un skill ».
  À rouvrir si l'on écrit un jour par l'API REST v1.
- **Verdict de `scripts/veille_faits.py`** (2026-10-21) : 22 faits vérifiés, 0 citation à signaler,
  0 page injoignable (code 0).

### 2026-10-21 — passe avant le plan « Changelog fonctionnel et doc vivante #2 »

- **Sources lues** : les pages de doc Claude Code de la partie 1 (skills, sous-agents, plugins,
  référence et chargement des plugins, hooks, tests par évals, bac à sable, mémoire, réglages,
  model-config), le changelog, « What's new », claude.dev, anthropic.com/engineering,
  `anthropics/skills` et l'issue `sandbox-runtime#74`. Lecture partielle pour `hooks.md`,
  `sub-agents.md`, `model-config.md` et `skills.md` (pages tronquées par l'outil de lecture).
- **Ce qui a changé** : rien de daté après le 2026-10-16 dans les pages de doc, les blogs ni
  l'issue (toujours ouverte, sans correctif). Nuances relevées, sans effet sur ce plan :
  `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (2.1.257) fait ignorer le `model` d'un frontmatter, donc le
  fait « le `model` du frontmatter l'emporte » vaut sans cette variable ; un plugin chargé sur
  place depuis une marketplace de chemin local relit ses fichiers à chaque démarrage, quelle que
  soit sa version ; 2.1.305 ajoute `sandbox.allowNestedUserNamespaces` (à lire avant de garder
  bwrap) ; 2.1.304 renvoie la liste des skills après une compaction.
- **Faits porteurs** : la lecture à la main du `chercheur` a cru deux citations touchées
  (« Bash dans une éval exige un bac à sable » ; l'alias `haiku`). Le contrôle mécanique les
  retrouve toutes les deux : le script fait foi, rien ne change au tableau de la partie 2.
- **Ce qu'on en fait** : rien ne s'applique aux fichiers de ce plan (contrôle de forme du
  changelog, règles du changelog, pièges Notion des schémas). Non lus, à reprendre à la passe
  suivante : les articles claude.dev des 8 et 15 octobre, « Redesigning source control at
  Anthropic » (13 octobre), `spec/` d'`anthropics/skills`, les dates des versions 2.1.301 à 2.1.306.
- **Verdict de `scripts/veille_faits.py`** (2026-10-21) : 22 faits vérifiés, 0 citation à
  signaler, 0 page injoignable (code 0).

### 2026-10-23 — passe avant la PR « rétro des écarts de doc et CBM_NODE du hook de réindexation »

- **Sources lues** : les pages de doc Claude Code de la partie 1 (hooks, plugins et chargement
  des plugins, skills, sous-agents, évals de plugin, bac à sable, mémoire, réglages, variables
  d'environnement, model-config), le changelog des versions 2.1.302 à 2.1.309, « What's new »,
  claude.dev, anthropic.com/engineering, `anthropics/skills` et l'issue `sandbox-runtime#74`.
  Lecture partielle, à reprendre : la fin des pages hooks, env-vars, model-config, skills et
  sous-agents (pages tronquées par l'outil de lecture), `plugins/components.md` et la référence
  des réglages.
- **Ce qui a changé** : rien de daté après le 2026-10-21 dans les pages de doc, les blogs, le
  dépôt `anthropics/skills` ni l'issue (toujours ouverte, sans correctif). Les contrats d'un hook
  `SessionStart` (sortie ajoutée au contexte, délai par défaut, exécution en arrière-plan,
  variables d'environnement du hook) n'ont pas bougé : c'est ce que touche la PR, et rien
  n'impose de la changer. Nouveau côté changelog, sans effet ici : 2.1.307 à 2.1.309
  (événement de sécurité sur un appel arrêté par un hook, un `env` de réglages de projet
  écarté pour une variable donnée, un `CLAUDE.md` imbriqué trop long qui ne charge que son
  début).
- **Faits porteurs** : la lecture de l'agent a cru trois citations absentes (« Bash dans une éval
  exige un bac à sable », l'alias `haiku`, la seconde phrase des champs ignorés d'un agent de
  plugin) ; le contrôle mécanique les retrouve. Une seule citation était réellement
  périmée, et c'était la forme du lien : la page `memory.md` écrit désormais
  `[skill](/docs/en/skills.md)` là où le tableau avait `[skill](/docs/en/skills)`. Le sens
  est le même ; la citation du tableau est mise à jour à l'identique de la page.
- **Ce qu'on en fait** : rien ne s'applique à la PR. Le hook lit sa variable dans l'environnement
  du processus, ce que la doc n'écrit pas pour un hook `SessionStart` (elle dit seulement que
  le hook tourne avec l'environnement de Claude Code) : la PR ne fait donc que lire une
  variable que l'utilisateur pose lui-même, et un hook qui ne la reçoit pas retombe sur le
  défaut d'origine. Aucune règle n'en dépend, donc aucun fait n'entre au tableau.
- **Verdict de `scripts/veille_faits.py`** (2026-10-23) : 22 faits vérifiés, 0 citation à
  signaler, 0 page injoignable (code 0), après la mise à jour de la citation de `memory.md`
  (la veille du jour avait relevé 1 citation à signaler avant elle).

### 2026-10-28 — passe avant la PR « un cron créé ou modifié se lance à la main » (plans-notion 0.51.0, methode-de-travail 1.8.0)

- **Sources lues** : le changelog des versions 2.1.310 à 2.1.312, « What's new », les pages
  des tâches planifiées (`scheduled-tasks.md`) et des routines (`routines.md`), `memory.md`,
  claude.dev et anthropic.com/engineering. Lecture partielle : les pages skills, sous-agents,
  plugins, hooks, évals de plugin et bac à sable n'ont pas été relues en entier ;
  `anthropics/skills` et l'issue `sandbox-runtime#74` n'ont pas pu être lus (GitHub refusé).
- **Ce qui a changé** : rien qui touche la PR. Les routines cloud s'appellent désormais
  « scheduled tasks » (« A cloud scheduled task, formerly a routine ») : intervalle minimal
  d'une heure, un déclencheur manuel « Run now » ; `CronCreate` : tâches récurrentes expirées
  au bout de 7 jours, 50 par session, sans rattrapage. La règle de la PR cite le déclencheur
  manuel du planificateur sans en dépendre. Côté changelog, 2.1.312 passe la limite des hooks
  de prompt et d'agent à « au plus 24 à la fois » : le « 12 » du journal du 2026-10-21 est périmé,
  sans règle qui en dépende.
- **Faits porteurs** : `scripts/veille_faits.py` : 22 faits vérifiés, 1 citation à signaler
  (le lien `[skill](...)` de `memory.md`, dont la forme a encore bougé, relatif ou absolu selon
  l'outil de lecture), 1 page injoignable (403 sur l'issue `sandbox-runtime#74`). Pas de règle touchée.
- **Ce qu'on en fait** : rien ne s'applique à la PR. À reprendre à la prochaine passe : la forme du
  lien de `memory.md`, et le billet « Building effective agent automations » (claude.dev, 8 octobre),
  non lu.

### 2026-10-28 (soir) — passe avant la PR « Adoption de skills externes » (plans-notion 0.57.0, methode-de-travail 1.9.0)

- **Sources lues** : changelog (dernière version 2.1.312, 27 octobre), « What's new », sous-agents,
  skills, hooks, évals de plugin, bac à sable, mémoire, chargement des plugins, modèles, claude.dev,
  anthropic.com/engineering, `anthropics/skills` (lisible cette fois) et l'issue `sandbox-runtime#74`.
  Lecture partielle : sous-agents, skills, hooks, bac à sable et modèles lus jusqu'à ~100 000
  caractères ; pages sans date par section, donc rien ne se date après le matin.
- **Ce qui a changé** : rien de daté après la passe du matin. Nouveau pour le journal : un sous-agent
  peut en lancer d'autres (« up to three layers below the main conversation », réglage
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `1` coupe l'imbrication) ; la semaine 24 de « What's new »
  dit « five levels deep » pour les chaînes en arrière-plan, écart 3 contre 5 non tranché ; un
  sous-agent lancé depuis la conversation principale démarre en arrière-plan ; l'outil `Agent` accepte
  un paramètre `effort` (2.1.292), sa priorité sur le frontmatter n'est pas écrite dans la partie lue.
  Évals de plugin : `--trust-plugin` et `--scaffold` (déjà passés par `evals/outillage/lancer.sh`),
  `Agent` parmi les outils en lecture seule d'un run. Bac à sable : la doc donne désormais un
  correctif AppArmor pour Ubuntu 24.04, l'issue #74 reste ouverte.
- **Corrections au journal du matin** (même jour) : (1) le « 12 » des hooks de prompt et d'agent n'est
  pas périmé : il vaut **par événement** (2.1.302), 2.1.312 ajoute « au plus 24 à la fois » **par
  session** ; (2) anthropic.com/engineering n'est pas muet depuis le 2026-04-23 : un article du 25 mai
  et un du 13 octobre ; (3) GitHub est lisible : `anthropics/skills` porte `.claude-plugin/`, `skills/`,
  `spec/` et `template/`, sans `shared/`.
- **Faits porteurs** : `scripts/veille_faits.py` : 22 faits vérifiés, 1 citation à signaler (le lien
  `[skill](...)` de `memory.md`, dont la forme bouge selon l'outil de lecture, déjà relevé les 23 et 28),
  0 page injoignable. Aucun fait cassé.
- **Ce qu'on en fait** : rien ne s'applique à la PR. Elle écrit déjà que l'imbrication est permise
  (Q13, D1) et ne dépend d'aucun fait ci-dessus. À reprendre à la prochaine passe : la priorité du
  paramètre `effort` de l'outil `Agent` sur le frontmatter, le « five levels » de la semaine 24, le
  démarrage en arrière-plan des sous-agents pour le relecteur en mode « plan entier » (le pilote attend
  déjà son résultat, rien n'a cassé), et les billets claude.dev non lus.

### 2026-10-29 — passe avant la PR « rapport de consommation de tokens » (plans-notion 0.58.0)

- **Sources lues** : aucune doc externe n'a été relue pour cette PR. Le script lit les journaux
  locaux de Claude Code ; leur format a été relevé par un POC du 2026-10-29 sur 9 638 journaux,
  pas sur une page de doc. La dernière passe sur les sources est celle du 2026-10-28 (soir).
- **Ce qui a changé** : rien à noter côté doc, faute de lecture nouvelle. Le format des journaux
  n'est donc pas couvert par une source externe.
- **Faits porteurs** : la PR n'en ajoute aucun, et ne touche pas `scripts/veille_faits.py`.
- **Autre source lue** : `session-report` (anthropics/claude-plugins-official, Apache-2.0, commit
  d19dab6 du 2026-04-10) a été lu et exécuté le 2026-10-29, avec l'accord de Benjamin, comme
  existant. Ses idées sont reprises (rattachement d'un sous-agent par `meta.json` puis par l'appel
  `Agent`, dédoublonnage par `requestId`) et réécrites ; aucune ligne n'est copiée.
- **Ce qu'on en fait** : rien ne s'applique à la doc externe. À reprendre : une lecture du format
  des journaux de session sur une source officielle, si elle existe, pour remplacer le relevé du POC.

### 2026-11-09 — passe avant la PR « l'executant sans mémoire d'agent » (plans-notion 0.61.0)

- **Sources lues** : les pages de doc Claude Code de la partie 1 (skills, sous-agents, plugins et chargement, hooks, évals de plugin, bac à sable, mémoire, réglages, changelog 2.1.314 à 2.1.319, what's new), claude.dev, anthropic.com/engineering, `anthropics/skills`, `sandbox-runtime#74`, par l'agent `chercheur` ; pages lues via un relais (WebFetch) sauf `memory.md` et `plugin-evals.md` (brut).
- **Ce qui a changé** : (1) `sub-agents.md` : la clé `memory` (portées `user`/`project`/`local`) et la citation « Read, Write, and Edit tools are automatically enabled so the subagent can manage its memory files. » sont inchangées ; nouveau : la mémoire d'un sous-agent fait partie de l'auto memory (`autoMemoryEnabled`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY` la coupent) ; la page ne dit rien de la mémoire pour les agents de plugin (elle ne demande donc pas de la retirer). (2) `plugin-evals.md` : la citation « If you grant Bash or PowerShell on a machine with no sandbox backend, Claude Code refuses each run rather than running it unconfined » est ABSENTE de la copie du jour (le texte dit que Bash n'est pas accordé par défaut) : à faire rejouer par `scripts/veille_faits.py`. (3) `sandboxing.md` : la section Ubuntu a changé de titre (« Ubuntu's AppArmor restriction stops bubblewrap », « Add an AppArmor profile for bubblewrap ») ; « 24.04 » n'y figure plus. (4) `sub-agents.md` documente le paramètre `effort` de l'appel (« The parameter overrides the `effort` field and stays in effect when the subagent is resumed … requires Claude Code v2.1.292 or later. ») et le changelog 2.1.316 ajoute `CLAUDE_CODE_SUBAGENT_EFFORT`, 2.1.317 : un sous-agent sur un autre modèle prend l'effort sauvegardé de ce modèle. (5) Changelog 2.1.319 : chargement des skills imbriqués avec le bac à sable, correction d'un échappement du bac à sable à la création d'un worktree ; 2.1.314 `permissions.blockWritesOutsideWorkingDirectories`. (6) `anthropics/skills` : commit 2c5958e du 2026-11-06, passage de skills Office sous Apache 2.0 ; toujours pas de `shared/evals/`. (7) `claude.dev` : les rubriques Skills, Agents et Playbooks ne sont pas des pages (404) mais des filtres du blog ; dernier article du 2026-10-15. (8) `anthropic.com/research/components-of-agent-memory` (2026-11-06) : source d'idées sur la mémoire d'agent, non normative. (9) `what's new` n'a pas suivi le changelog (dernière entrée : semaine 37). `sandbox-runtime#74` toujours ouverte, rien de neuf.
- **Ce qu'on en fait** : la PR retire la mémoire d'agent de l'`executant` ; la doc n'impose pas ce retrait, c'est un choix de gouvernance (mémoire de métier dans le `fact_store` de Jérôme). Le point (2) est signalé au prochain passage de `veille_faits.py` ; les points (3) à (5) n'ont pas d'effet sur une règle du dépôt à ce jour (non vérifié règle par règle).

### 2026-11-16 — passe avant la PR « favoris récents et registre des outils » (plans-notion 0.62.2, methode-de-travail 1.9.2)

- **Sources lues** : les pages de la partie 1 (skills, sous-agents, plugins et chargement, hooks, évals de plugin, bac à sable, mémoire, réglages, model-config, tarifs, changelog 2.1.321 à 2.1.325, what's new), claude.dev (titres), anthropic.com/engineering, `anthropics/skills`, `sandbox-runtime#74`, par l'agent `chercheur` ; pages lues par résumé, citations confirmées ensuite par `scripts/veille_faits.py`.
- **Ce qui a changé** : (1) `model-config.md` : la phrase sur l'effort d'un frontmatter est reformulée (la durée est maintenant dite : « until the end of the turn it runs in », la variable `CLAUDE_CODE_EFFORT_LEVEL` garde la priorité) ; (2) `sub-agents.md` : la phrase « is a default » a disparu ; la priorité reste per-invocation > `model` de la définition > `CLAUDE_CODE_SUBAGENT_MODEL`, et `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (2.1.257) fait ignorer le `model` de la définition ; (3) `memory.md` : le lien vers les skills est écrit en absolu ; (4) tarifs : « priced at 0.05x the base input price », montants inchangés ; (5) la citation du bac à sable de `plugin-evals.md`, absente le 2026-11-09, est de nouveau présente ; (6) changelog : `/advisor` n'est pas né en 2.1.322 (doc officielle : `-p` depuis 2.1.260) ; 2.1.325 : un Bash sous bac à sable suit le flux de permission normal ; `engines["claude-code"]` dans `plugin.json` (2.1.323) ; la clé `agent` d'un plugin est dépréciée (2.1.323), absente des `plugin.json` du dépôt.
- **Ce qu'on en fait** : les quatre citations du tableau (lignes de l'effort, de `CLAUDE_CODE_SUBAGENT_MODEL`, du lien `memory.md`, du cache) sont remplacées par le texte de la page du jour et leur date de vérification passe au 2026-11-16 ; le fait de `CLAUDE_CODE_SUBAGENT_MODEL` est coupé en deux lignes : l'ordre de priorité d'un côté, l'exception `_FORCE` de l'autre. Le fait que `claude -p` refuse un outil non listé avec un code 0 et celui d'`--allowedTools` qui avale l'argument suivant ne sont pas écrits dans la doc officielle : le registre les donne comme mesurés sur le poste, pas comme documentés. Non repris : le point `sandbox.autoAllowBashIfSandboxed` (2.1.325) et la sémantique d'un refus de hook (2.1.323), à relire à la prochaine passe.

### 2026-11-19 — passe avant la PR « Hal relit le plan avant qu'il passe en revue » (plans-notion 0.69.0)

- **Sources lues** : les pages de la partie 1 (hooks, skills, sous-agents, plugins et chargement, évals de plugin, mémoire, model-config, tarifs, MCP), le changelog 2.1.326 à 2.1.328 (fichier brut `CHANGELOG.md`), claude.dev, anthropic.com/engineering, `anthropics/skills`, `sandbox-runtime#74`, par l'agent `chercheur` ; pages lues par résumé, citations confirmées ensuite par `scripts/veille_faits.py`.
- **Ce qui a changé** : (1) changelog 2.1.326 : `"decision": "block"` tenu dans plus de cas, une sortie 127 d'un hook PreToolUse est mieux signalée, `updatedInput` conservé quand plusieurs hooks répondent ; (2) 2.1.327 : `/status` liste les matchers de hook qui ne correspondent jamais ; (3) 2.1.328 : `"onFailure": "block"` existe aussi pour les hooks `mcp_tool` (la page des hooks ne le dit pas encore) ; (4) la page des hooks dit qu'un hook en échec ou en délai laisse passer l'appel (sauf `onFailure: "block"`, 2.1.295 ou plus) ; un matcher ne porte que sur le nom de l'outil, `tool_input.command` arrive sur l'entrée standard ; priorité `deny` > `defer` > `ask` > `allow`. Rien de daté après le 16 novembre dans les autres pages.
- **Faits porteurs** : le rapport du chercheur donnait deux citations absentes (`plugin-evals.md`, bac à sable ; `model-config.md`, alias `haiku`) d'après des lectures par résumé ; `scripts/veille_faits.py` du jour rend « 23 fait(s) vérifié(s) : 0 citation(s) à signaler », donc rien à corriger au tableau.
- **Ce qu'on en fait** : pour le hook `refuser_revue_sans_avis.py` (deux matchers, Notion et Bash, sortie en code 2), le refus passe par `exit 2` et un message sur la sortie d'erreur, sans JSON de décision en plus ; `"onFailure": "block"` sur le hook `command` pour qu'un script qui plante ne laisse pas passer une mise en revue sans avis (contre le choix de laisser passer en cas d'entrée illisible, voulu par le plan : à trancher à l'étape 5) ; les noms d'outils des connecteurs Notion ne sont pas dans la doc (`mcp__<uuid>__…` via l'app, `mcp__claude_ai_*` sur le VPS), à mesurer avant de compter sur un matcher ; `/status` montre les matchers qui ne correspondent jamais.

### 2026-11-19 — passe avant la PR « Adoption de skills externes #3 » (plans-notion 0.70.0, methode-de-travail 1.11.0)

- **Sources lues** : aucune page nouvelle : la passe « Hal relit le plan » (plans-notion 0.69.0) date du même jour, et `python3 scripts/veille_faits.py` rejoué aujourd'hui rend « 23 fait(s) vérifié(s) : 0 citation(s) à signaler, 0 page(s) injoignable(s) ». Pas d'appel à l'agent `chercheur` : rien n'a pu changer en quelques heures.
- **Ce qui a changé** : rien depuis la passe du matin.
- **Ce qu'on en fait** : rien. Les hooks `refuser_git_stash.py` et la règle (p) de `check_skills.py` reposent sur des faits déjà au tableau (hooks `PreToolUse`, `disallowedTools` et `tools` d'un agent).

### 2026-11-23 — passe avant la PR « Réduire la voilure » (plans-notion 0.76.0)

- **Sources lues** : changelog 2.1.329 et 2.1.330 (fichier brut `CHANGELOG.md`, 100 000 premiers caractères sur 1,38 million, entrées sans date), pages sous-agents, skills, model-config, hooks, CLI, variables d'environnement et `plugins/host-marketplace.md`, par l'agent `chercheur` ; citations du tableau rejouées par `python3 scripts/veille_faits.py` : « 23 fait(s) vérifié(s) : 0 citation(s) à signaler, 0 page(s) injoignable(s) ». Extraits du chercheur lus par résumé, non recopiés ici.
- **Ce qui a changé** : (1) champ `effort` d'un agent : aucun changement, valeurs `low` à `max`, sans défaut fixe (sans le champ, le niveau de la session s'applique) ; (2) 2.1.329 ajoute une ligne « Marketplace auto-update » à `/status`, et la doc dit que l'auto-update d'une marketplace est **désactivé par défaut** (un utilisateur ou un administrateur l'active) ; (3) `"onFailure": "block"` : un hook `PreToolUse` qui plante ou dépasse son délai ne bloque pas l'appel par défaut ; (4) alias `fable` dans `model-config.md` ; `haiku` pointe encore vers Haiku 4.5 hors API Anthropic.
- **Faits porteurs** : aucun ajout au tableau ; les citations existantes tiennent.
- **Ce qu'on en fait** : le plan règle déjà (2) par l'étape 1 (`autoUpdate: true` à poser sur le Mac par Benjamin, snippet du README) et l'étape 2 (le script prévient d'une copie en retard) : la doc confirme le besoin, aucune correction. Pour (1), `effort: medium` du relecteur est une valeur admise, tenue par la session sans surcharge de `CLAUDE_CODE_EFFORT_LEVEL`. (3) et (4) : rien dans ce plan ne touche un hook ni un alias ; relevés pour une passe future (hooks de garde du poste à passer en `onFailure: block` dans `settings.json`, hors dépôt).

### 2026-11-24 — passe avant la PR « Refonte des plugins par la checklist, étape 9 » (plans-notion 0.77.0)

- **Sources lues** : aucune source nouvelle ce jour. Cette passe reprend celle du 2026-11-23 du plan « Refonte des plugins par la checklist » (enquête et citations recoupées au caractère près ce jour-là ; pages sauvées dans `~/brouillons/mes-skills/refonte-relecture-checklist/sources/`). Pas d'appel à l'agent `chercheur` : rien n'a pu changer en un jour.
- **Ce qui a changé** : rien depuis le 2026-11-23. Les pages que le plan cite (bonnes pratiques des skills : une checklist à cocher pour les workflows complexes, liberté haute pour la relecture de code ; relecture de code en agents parallèles suivie d'une étape de vérification ; séparer l'agent qui fait de celui qui juge) sont celles de la passe du 2026-11-23.
- **Faits porteurs** : aucun ajout au tableau ; les citations existantes ne sont pas rejouées ce jour.
- **Ce qu'on en fait** : la PR fait de `_partage/listes/` la seule source des listes de relecture, avec un garde (`scripts/test_listes.py`) qui vérifie que chaque lecteur cite sa liste et qu'aucune copie ne reste ailleurs. Aucune conduite de skill n'est changée par la passe ; la question des hooks `onFailure: block`, relevée le 2026-11-23, reste hors de ce plan.

### 2026-11-25 — passe avant la PR « plans-notion 0.78.0 : l'enquête du plan par la checklist »

- **Sources lues** : changelog Claude Code (2.1.331, daté du 23 novembre, non relu par les passes précédentes), pages sous-agents, skills, référence et chargement des plugins, hooks, évals de plugin, configuration des modèles, guide de rédaction des skills de la plateforme, `anthropics/skills` (dernier commit le 16 novembre), anthropic.com/engineering (dernier article le 13 novembre), un billet de claude.dev du 24 novembre (non normatif). Lectures par résumé ; plusieurs pages longues non lues jusqu'au bout.
- **Ce qui a changé** : la 2.1.331 ajoute `optionalDependencies` aux manifestes (absent de la page de référence lue, à vérifier avant de s'en servir) et change le sens de `retry` pour `PermissionDenied`.
- **Faits porteurs** : aucun changé ; `scripts/veille_faits.py` rejoué le 2026-11-25 : 23 faits vérifiés, 0 citation à signaler, 0 page injoignable.
- **Ce qu'on en fait** : rien ne change pour la PR. La liste à cocher s'appuie sur le modèle de checklist documenté par le guide de la plateforme.

### 2026-11-25 — passe avant la PR « jeton lourd automatique » (plans-notion 0.79.0)

- **Sources lues** : la page des hooks (`code.claude.com/docs/en/hooks.md`), relue ce jour par recherche de mots-clés (parallélisme des hooks d'un même événement, `updatedInput`, sections PreToolUse et mode auto), pas en entier. Pas d'appel à l'agent `chercheur` : une seule page porte le fait.
- **Ce qui a changé** : deux points pour le hook `jeton_lourd.py`. (1) « When an event fires, its matching hooks run in parallel » : la doc ne dit pas quel `updatedInput` gagne quand deux hooks d'un même événement en renvoient un ; sa règle de précédence (deny > defer > ask > allow) vise les décisions, pas les réécritures. (2) En mode auto, un `updatedInput` sans `permissionDecision` peut être refusé par Claude Code, avec le message « a hook changed this call's input after auto mode reviewed it ».
- **Faits porteurs** : aucun ajout au tableau de la partie 2. La phrase sur le parallélisme est relevée ce jour ; elle n'est pas encore citée par un garde.
- **Ce qu'on en fait** : D7 garde la compression rtk dans le hook lui-même (`rtk rewrite` appliqué avant la réécriture), faute de savoir quel `updatedInput` gagne entre deux hooks. Le point (2) n'est pas traité par ce plan : à signaler si un refus de ce type apparaît en mode auto.

### 2026-11-25 — préparation minimale : le plan léger et son aiguillage (plan « Préparation minimale : un plan léger, en exception bornée »)

- **Sources lues** (relevées à la conception, le 2026-11-24) : les
  [bonnes pratiques de Claude Code](https://code.claude.com/docs/en/best-practices.md)
  (« Only write down what Claude can't find by reading the repo… »), les
  [bonnes pratiques de consigne](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices.md)
  (consignes générales plutôt que pas à pas), la page des
  [modes de permission](https://code.claude.com/docs/en/permission-modes.md) (mode plan
  natif), et l'étude ETH Zurich arXiv 2602.11988 sur les fichiers de contexte (réussite
  non améliorée en moyenne, coût en hausse de plus de 20 % : un proxy, elle ne porte pas
  sur des plans). Le changelog de Claude Code n'a pas été relu : la passe 0.78.0 du même
  jour le couvre.
- **Ce qui a changé** : aucune source lue ne mesure « plan lourd contre plan fonctionnel »
  sur un Opus récent, d'où deux POC. POC A : sur 184 découvertes d'exécution trouvables au
  plan, 31 % auraient exigé une question. POC B : trois plans rejoués en « plan
  fonctionnel + Opus medium nu » coûtent 6 à 27 % du coût réel, aucun ne tient tous les
  critères. Aucun fait du tableau de la partie 2 n'est
  touché (`scripts/veille_faits.py` rejoué : 23 faits, 0 citation à signaler).
- **Mesure de l'aiguillage** (2026-11-25, 30 demandes étiquetées et figées avant le premier
  appel, deux passages ; seuils : aucun « léger » sur un cas « complet », même verdict aux
  deux passages sur au moins 27 cas, au moins 6 « léger » reconnus sur 12) :

  | Juge | Faux « léger » | Stabilité | « Léger » reconnus | Verdict |
  |---|---|---|---|---|
  | Haiku 5.5 (`claude -p`) | 0 | 26 sur 30 | 3 sur 12 | écarté |
  | Jev, une question `noul` par case, « non » sous 0,5 | 0 | 30 sur 30 | 6 sur 12 | retenu |
  | Jev, rejoué par le script livré | 0 | 30 sur 30 | 7 sur 12 | tient |

  Haiku : 0,095 dollar ; Jev ne rend pas son coût ; Sonnet non joué. Limites : un seul jeu
  de 30 demandes, étiqueté par une session ; Jev rend une note sans justification, la
  preuve par case reste à la session.
- **Ce qu'on en fait** : `plan-notion/plan-leger.md` (mode borné, jamais le défaut),
  `_partage/listes/aiguillage-plan.md` et `_partage/scripts/aiguiller-plan.py`, cas
  d'éval `plan-leger-eligibilite` écrit et non joué. L'effet du mode se juge à l'usage
  (coût réel et décisions prises sans question, à la clôture de chaque plan léger).

### 2026-11-25 — passe avant la PR « relevé du jour du VPS » (plans-notion 0.81.0)

- **Sources lues** : changelog Claude Code (2.1.332, datée du 25 novembre), pages skills, hooks, sous-agents, configuration des modèles, bac à sable, référence des plugins, claude.dev, anthropic.com/engineering, `anthropics/skills` (aucun commit depuis le 24 novembre). Lectures par résumé ; la page des évals de plugin n'a pas pu être lue.
- **Ce qui a changé** : la 2.1.332 ajoute l'événement `PreSkillShellCommand` et change les alias `sonnet` et `opus` hors API Anthropic. La page des skills dit que les hooks `PreToolUse` ne voient pas les commandes injectées au chargement d'un skill ; aucun `SKILL.md` du dépôt n'en injecte (recherche jouée ce jour).
- **Faits porteurs** : aucun changé ; `scripts/veille_faits.py` rejoué le 2026-11-25 : 23 faits vérifiés, 0 citation à signaler, 0 page injoignable.
- **Ce qu'on en fait** : rien ne change pour la PR. Le changement d'alias ne touche pas l'API Anthropic ; il est signalé à Benjamin en fin de plan.

### 2026-11-25 — passe avant la PR « tri des faits à décision » (plans-notion 0.82.0)

- **Sources lues** : aucune source nouvelle pour cette passe. La passe complète du même jour (entrée « relevé du jour du VPS », plans-notion 0.81.0) couvre les sources du 2026-11-25 ; elle est reprise ici sans nouvelle lecture, et aucun appel à l'agent `chercheur`.
- **Ce qui a changé** : rien de neuf à ce jour au-delà de cette passe reprise. `python3 scripts/veille_faits.py` rejoué maintenant : « 23 fait(s) vérifié(s) : 0 citation(s) à signaler, 0 page(s) injoignable(s). » (sortie relue, code 0).
- **Faits porteurs** : aucun ajout ni retrait au tableau de la partie 2.
- **Ce qu'on en fait** : rien ne change pour la PR. La veille de 30 jours (`scripts/check_veille.py`) est respectée par cette entrée.

### 2026-11-26 — passe avant la PR « ce que le pilote lit avant d'écrire un plan » (plans-notion 0.83.0)

- **Sources lues** : changelog Claude Code (dernière version : 2.1.332), page hooks, claude.dev, anthropic.com/engineering, doc Notion « enhanced markdown » et « Notion-flavored Markdown » (developers.notion.com/guides/data-apis/). Lectures par l'agent `chercheur`, extraits passés par un modèle intermédiaire.
- **Ce qui a changé** : rien après la 2.1.332 au changelog ; un billet d'ingénierie du 25 novembre sans rapport avec hooks ni skills. Côté Notion : la version `v1` du markdown de l'API (encore le défaut) est dépréciée ; la `v2` accepte `<b>`, `<i>`, `<s>`, `<u>` et enregistre en texte les autres balises.
- **Faits porteurs** : aucun changé au tableau. Confirmés sur la page hooks, dont dépendent les deux hooks neufs : refus par `permissionDecision: "deny"` ou par le code 2 ; `PostToolUse` seulement après une réussite ; `PreCompact` ; `agent_id` dans l'entrée d'un appel de sous-agent.
- **Ce qu'on en fait** : rien ne change pour la PR. À surveiller : quand la `v2` du markdown Notion devient le défaut de la commande `composio`, le hook `refuser_balises_composio.py` refuserait des `<b>` devenus valides : le revoir à ce moment.

### Essai de `/steward` — 2026-11-26 (en cours au moment de l'écriture)

Ce n'est pas une passe de veille. Le titre ne commence pas par une date `AAAA-MM-JJ` exprès : `scripts/check_veille.py` ne lit que les entrées datées de ce type, et une entrée d'essai ne doit pas repousser la date de la dernière passe.

- **Ce qui est essayé** : `/steward` (surveillance d'une PR par Claude Code) sur la PR hermes-custom #1129, par Hal. Session tmux `rc-essai-steward-1129`, Sonnet en effort medium, mode auto, Claude Code 2.1.332. Le plan (étape 17) demande de noter : si la surveillance a démarré (sinon le message exact), les commits poussés, le quota avant et après.
- **Messages reçus**, copiés tels quels depuis le rapport de Hal :
  - 1er essai, `/steward` passé comme objectif au lancement (12:22 UTC) : « Nothing started. /steward starts only from a line that you type, not from claude -p or a program. »
  - 2e essai, ligne tapée : « /steward didn't start. I can't watch pull request #1129 here: remote control is on in this session, and Claude Code can't tell messages sent through it from yours (to turn it off, run /rc and pick Disconnect this session). »
  - 3e essai, tapé à 12:24 UTC, après `/rc` → Disconnect this session : « Le premier passage de surveillance de la PR #1129 démarre dans une minute environ ; /steward stop arrête la surveillance. »
- **Ce que ça apprend** : `/steward` exige une ligne tapée (ni objectif initial, ni `claude -p`) et une session sans Remote Control. Le troisième message annonce le démarrage ; il ne prouve pas à lui seul qu'un passage a eu lieu. Les commits et le quota le diront à l'arrêt.
- **PR écartée** : #1116 était d'abord prévue, puis écartée : c'est la branche du robot d'instantané, poussée en force chaque nuit.
- **État au moment de l'écriture** : essai **en cours**. Commits poussés pendant la surveillance : non relevés. Coût (quota avant et après) : non mesuré au démarrage ; Hal le relèvera depuis le transcript à l'arrêt.
- **Arrêt programmé** : cron `verif-essai-steward-1129-stop` (`cac6b43ad0db`), le 2026-11-27 à 13:20 (Paris) : `/steward stop`, puis relevé des commits.
- **Ce qu'on en fait** : la fin d'essai s'ajoute à cette entrée quand Hal la rapporte (étape 17 du plan : une petite PR de doc à part si la PR du plan est déjà mergée). Aucun écart avec le plan à ce stade.
