# Fixture : un journal de veille figé

Pages figées, aucune requête réseau. Les URL ne servent qu'à retrouver le nom
du fichier de la page dans le dossier passé à `--pages`.

## 2. Les faits porteurs

| Fait | Citation | URL | Vérifié le | Contrôle qui en dépend |
| --- | --- | --- | --- | --- |
| Plafond de la description | « the combined `description` and `when_to_use` text is truncated at 1,536 characters » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle a |
| Taille d'un SKILL.md | « Keep `SKILL.md` under 500 lines. » | https://code.claude.com/docs/en/skills.md | 2026-09-30 | `scripts/check_skills.py` règle b |
| Champs ignorés d'un agent de plugin | « These fields are ignored when loading agents from a plugin. » | https://code.claude.com/docs/en/sub-agents.md | 2026-09-30 | `scripts/check_skills.py` règle f |

## 3. Le journal des passes

### 2026-09-30 — passe initiale
