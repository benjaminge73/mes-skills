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
| La mise à jour compare la version, pas le contenu | « compute the version again and skip the plugin when it matches what `installed_plugins.json` records » | https://code.claude.com/docs/en/plugins/loading.md | 2026-09-30 | `scripts/plugin_version_guard.py` |
| Le champ `version` du manifeste prime | « The `version` field in the plugin's manifest comes first » | https://code.claude.com/docs/en/plugins/loading.md | 2026-09-30 | `scripts/plugin_version_guard.py` |
| Sans `--no-publish`, le rapport d'éval sort de la machine | « Keep the HTML report local. » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `scripts/evals_ab.py` |
| `--ablation none` joue un seul bras | « `none` runs one arm; `with-without` adds the no-plugin baseline » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `scripts/evals_ab.py` |
| Bash dans une éval exige un bac à sable | « If you grant Bash or PowerShell on a machine with no sandbox backend, Claude Code refuses each run rather than running it unconfined » | https://code.claude.com/docs/en/plugin-evals.md | 2026-09-30 | `evals/outillage/preparer-runner.sh` |
| Le bac à sable échoue sur Ubuntu 24.04+ (AppArmor) | « bwrap fails on Ubuntu 24.04+ due to AppArmor userns restrictions » | https://github.com/anthropics/sandbox-runtime/issues/74 | 2026-09-30 | `evals/outillage/preparer-runner.sh` |

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
