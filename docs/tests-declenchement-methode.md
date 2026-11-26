# Test de déclenchement : `connecteurs-timeout` et `doc-vivante`

Joué le 2026-11-26, à la demande de Benjamin, quand ces deux règles toujours chargées sont devenues
des skills. Une description qui ne se déclenche pas ferait disparaître la consigne sans bruit :
c'est ce que ce test regarde. Il n'est pas rejoué par la CI.

## Protocole

- `claude -p` en `stream-json`, Sonnet 5.5, effort `medium`, plugin chargé par `--plugin-dir`.
- `CLAUDE_CONFIG_DIR` temporaire : la configuration du poste **sans** les deux règles, sinon elles
  restent en contexte et le test ne mesure rien.
- Connecteurs tous bloqués ; `Bash`, `Write`, `Edit`, `Agent` et le web refusés ; 4 tours au plus.
- Seuil figé avant le run : chaque skill appelé (outil `Skill`) dans tous ses cas positifs.

## Cas et résultats

| Skill | Cas | Demande | Attendu | Obtenu |
|---|---|---|---|---|
| `doc-vivante` | p1 | PR de correctif en brouillon : que reste-t-il avant de la passer prête ? | appelé | appelé |
| `doc-vivante` | p2 | Rédiger la description d'une PR qui change l'horaire d'un cron | appelé | appelé |
| `doc-vivante` | p3 | Correctif mergé sur `main` : une trace à laisser ? | appelé | appelé |
| `doc-vivante` | n1 | Proposer un nom de variable | pas appelé | pas appelé |
| `connecteurs-timeout` | p1 | `notion-update-page` échoue sur le timeout du hook `PreToolUse` | appelé | appelé |
| `connecteurs-timeout` | p2 | `internal_server_error` de Notion : faut-il redémarrer ? | appelé | appelé |
| `connecteurs-timeout` | p3 | Connecteur muet : écrire la page depuis le VPS | appelé | appelé |
| `connecteurs-timeout` | n1 | 17 fois 23 | pas appelé | pas appelé |

Coût : 1,01 $. Un tirage par cas : le test dit que la description déclenche, pas à quelle fréquence.
