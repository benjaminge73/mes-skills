Le plan est dans `plan.md`. Point d'attention : `db/schema.sql` est protégé par un hook Claude Code du dépôt ; le champ passe donc par une nouvelle migration, puis `make schema`. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `ls -a` à la racine -> `.claude/settings.json` présent, hook PreToolUse sur `Write|Edit|MultiEdit`
- ce que refuse le hook (`.claude/hooks/proteger_schema.py`) -> toute édition d'un chemin qui finit par `db/schema.sql` (code retour 2)
- d'où vient `db/schema.sql` -> `make schema` concatène `db/migrations/*.sql`
- migrations existantes -> 0001_produits, 0002_stock ; la prochaine est 0003
DECOUVERTES:
- hook PreToolUse : `.claude/settings.json` interdit d'éditer `db/schema.sql` à la main ; il faut une migration 0003 puis `make schema`
