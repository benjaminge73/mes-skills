# Plusieurs plans dans une même session

Détail du section « Plusieurs plans » de `executer-plan-notion/SKILL.md`, lu à la demande (renvoi du SKILL.md). Texte déplacé tel quel, sans réécriture.

Tout ce qui précède décrit un plan. Quand une session en porte plusieurs,
chacun garde son déroulé (§2 à §7) ; ce qui s'ajoute tient en cinq points.
La fiche locale fait exception : une par session, pour le premier plan ouvert (`ouverture.md`).

**Un pilote unique.** Le pilote conduit tous les plans, et aucun
n'est confié à un « pilote » délégué. Raisons : le connecteur Notion n'est pas
garanti chez les sous-agents (absent de l'app de bureau, chargeable depuis le VPS) ; les preuves se jouent soi-même, sans seconde main ;
chaque niveau relirait la page, au coût en jetons ; les paliers et décisions
restent au pilote.

**Chaque plan garde sa porte, sa branche et son worktree.** La porte d'entrée
se lit plan par plan : un plan ne démarre que s'il est `valide`, puis `pret`
après sa préparation ; jamais `en cours` sans être passé par `pret`. La branche, le worktree du plan (§2), le journal (§4) et la
clôture (§6) sont ceux de ce plan, jamais partagés avec un autre. Au contrôle
bloquant de la clôture, `git worktree list` montre aussi les worktrees des
autres plans encore en cours : ne regarder que ceux du plan qu'on clôt.

**Un seul pool glissant.** Toutes les étapes de tous les plans partagent
**une douzaine de places**. Une étape qui termine libère sa place pour la
prochaine étape prête, de n'importe quel plan. Le plafond est celui du pool,
pas celui de chaque plan :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/vagues.md`

**Entre plans, le parallèle est le défaut.** Seule une ressource partagée à
l'exécution fait attendre :

- **le port des tests e2e** — deux plans ne le prennent pas en même temps ;
- **la base locale** — même raison ;
- **les actions lourdes** (suites, e2e, évals) — autant à la fois que la machine
  a de places (deux sur le VPS, plus avec un profil machine) : le plan maître porte leur file, le pilote les prend dans l'ordre
  (`${CLAUDE_PLUGIN_ROOT}/skills/_partage/machine-partagee.md`) ;
- **le quota d'un outil**, lu au registre :

  📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/outils-et-quotas.md`

Deux plans qui touchent **le même fichier** ne s'attendent pas : ils donnent un
**ordre de merge**, signalé dans le plan maître et dans le compte rendu. Chaque
plan vit sur sa propre branche, donc rien ne se marche dessus à l'exécution ;
c'est au moment de remonter sur `main` que l'ordre compte.

**Un plan maître** (au moins deux plans d'une même session). Sa page porte un
`Statut` hérité des plans, calculé par `statut-maitre.py` — ce n'est pas un plan
qu'on valide, et la porte d'entrée ne le lit jamais. Si `plan-notion`
l'a déjà écrite, elle se met à jour ; sinon elle se crée au lancement. Sa forme
et sa préparation (une lecture Haiku par page, un `enqueteur` par plan, en
parallèle ; le pilote ne garde que le croisement) vivent dans un seul fichier :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/plan-notion/plan-maitre.md`
