---
name: connecteurs-timeout
description: >-
  Un appel à un connecteur (Notion, Composio, Vercel, Gmail…) échoue : quoi faire. À charger dès
  qu'un appel MCP rend « PreToolUse hook did not respond before its timeout » ou « host client may
  be unreachable », un « internal_server_error » de Notion, « mcp_oauth_token_read_unsupported »,
  un « result exceeds maximum allowed tokens » de notion-fetch, ou avant de conclure qu'un
  connecteur est déconnecté et de demander un redémarrage ; aussi pour écrire dans Notion par la
  commande composio du VPS quand le connecteur manque.
---

# Un timeout du hook n'est pas une panne du connecteur

Message visé :

> PreToolUse hook did not respond before its timeout (host client may be unreachable).
> The tool call was not executed; other configured hooks may not have completed.

## Le mécanisme

Une session ouverte depuis l'app Claude de bureau tourne sur le VPS **en SSH**. Les connecteurs
claude.ai (outils `mcp__<uuid>__…`) sont relayés par l'app, sur l'ordinateur de Benjamin, qui joue
un contrôle (hook `PreToolUse`) avant chaque appel. App injoignable (SSH décroché, veille, capot
fermé) : l'appel n'est **jamais envoyé**. Bash, Agent et les outils locaux marchent toujours.

- **Réessayer est sans risque de doublon** : rien n'est parti.
- **Ce n'est ni Notion ni la session** : pas de « connecteur déconnecté » au premier échec, pas de
  redémarrage demandé tout de suite.

## Le geste

1. **Attendre une à deux minutes, puis réessayer le même appel.** Pas de `sleep` au premier plan :
   avancer sur autre chose, ou `sleep 90` en arrière-plan.
2. **Jusqu'à trois essais sur une dizaine de minutes.** Au-delà, l'app est hors ligne : garder
   l'écriture en attente dans le scratchpad, **ne rien écrire ailleurs que Notion**, le signaler à
   Benjamin en une ligne.
3. **Pour Notion, passer par la commande `composio` du VPS** : même page, sans passer par l'app.
4. **Reprendre l'écriture en attente** dès qu'un appel repasse, avant toute nouvelle.

## La commande `composio`

- Lire : `echo '{"page_id":"<id>"}' | composio execute NOTION_GET_PAGE_MARKDOWN -d -`. Une grosse
  page part dans un fichier (`storedInFile`, `outputFilePath`, champ `data.markdown`).
- Écrire du contenu : `composio execute NOTION_UPDATE_PAGE_MARKDOWN -d @args.json`, avec
  `{"page_id": …, "type": "update_content", "update_content": {"content_updates": [{"old_str": …,
  "new_str": …}]}}` (100 remplacements au plus). Propriétés : `NOTION_UPDATE_PAGE`.
- ⚠️ **Ce n'est pas le même markdown que le connecteur** : composio ne prend pas les balises HTML
  du miroir du connecteur (`<b>`, `<mention …>`), un hook de `plans-notion` les refuse. Écrire en
  markdown, et lire la page par `NOTION_GET_PAGE_MARKDOWN` pour construire les `old_str`.
- Construire `old_str` par script depuis la relecture, passer le texte par un fichier (pas par un
  agent qui recopie), **relire et recompter les cases** après chaque écriture.
- ⚠️ Échapper le markdown d'un texte neuf **sans toucher aux cases** : `- [ ]` échappé en
  `- \[ \]` devient une puce, plus une case (erreur du 2026-10-10). Contrôle :
  `compter-cases.py <page.md> --releve <releve.json>` (plugin `plans-notion`).

## Sessions de plan lancées par Hermes

Elles ne gardent que **Notion** parmi les connecteurs claude.ai (liste blanche). Pour un autre
connecteur : la commande `composio` (Bash), ou une relance avec le connecteur ajouté à la liste
(`REGLAGES_SESSION_PLAN`, `scripts/claude_remote_reprise.py` de `hermes-custom`).

## Où lancer une longue exécution

Les timeouts se concentrent le soir et la nuit, ordinateur endormi. Une session lancée **depuis le
VPS** (CLI ou Remote Control) passe par les connecteurs `mcp__claude_ai_*`, sans l'app : zéro
timeout de hook. Une exécution sans surveillance se lance donc de préférence sur le VPS.

## À ne pas confondre

- « result exceeds maximum allowed tokens » (`notion-fetch`) : pas une panne, la sortie est dans un
  fichier dont le message donne le chemin.
- `internal_server_error` de Notion : panne ponctuelle côté Notion, même geste.
- `mcp_oauth_token_read_unsupported` : jeton illisible par la session, réessayer n'y fait rien : le
  signaler à Benjamin.
