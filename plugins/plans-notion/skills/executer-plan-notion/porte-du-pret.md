# La porte du `pret` : ce qu'un plan doit avoir prouvé

Détail du § 2 (« La porte du `pret` ») de `executer-plan-notion/SKILL.md`, lu à la demande (renvoi du SKILL.md). Texte déplacé tel quel, sans réécriture.

**La porte du `pret`.** Un plan `pret` a **toutes ses étapes prouvées et
rejouées à blanc, ses vagues calculées, et, s'il a un plan maître, l'orchestration
entre les plans écrite**. Chaque geste ci-dessus (relecture, questions au vert,
preuves, maquette, répétition à blanc, branche et worktree, CI, vagues, pilote,
orchestration) laisse sa trace dans une puce de l'entrée `Ouverture` du journal,
plus une puce par étape (§4, modèle dans `ouverture.md`). Puis `python3
"${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/preparation-prete.py" <page.md>
--depot <dépôt> [--maitre <maitre.md>]` : code 0 → `Statut` = `pret`, `Branche` renseignée ; code 1 → un défaut par ligne,
on le fait et on rejoue ; **pas de `pret`, donc pas de `en cours`, donc pas
d'étape**. `Statut` = `en cours` se pose sur la page `pret`, avant la première
étape.
