> Détail de la section « 4. Ce qu'une passe ne doit jamais effacer » de `SKILL.md` (skill plan-notion), sorti du skill pour le ramener sous son budget de taille. La ceinture « fichier introuvable » reste dans `SKILL.md`. Lire ce fichier avant la première écriture dans une page de plan.

Entre deux passes, la page a vécu : Benjamin a coché des cases, écrit après
`Autre / complément →`, ajouté des remarques à même le corps. **Tout cela est de
la donnée, pas du brouillon** — c'est la seule trace de ses décisions, et le fil
de discussion ne la contient pas. Une passe qui réécrit une section par-dessus
l'efface sans prévenir, parce que recréer un bloc `to-do` le rend vierge.

**Comment écrire sans rien casser vit dans un fichier partagé avec
`executer-plan-notion` :**

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/ecrire-dans-notion.md`

Le protocole en cinq temps — relever avant d'écrire, éditer de façon ciblée,
remettre les `- [x]` en cas de refonte, ne jamais reformuler Benjamin, vérifier
après coup — et les cinq pièges de l'API : `update_content` qui ne décoche pas,
l'écriture qui échoue en silence, le commentaire qu'on ne résout jamais
soi-même, `replace_all_matches` sur un motif de balisage, et l'insertion
ancrée au milieu d'un paragraphe formaté.

Il porte aussi **« Le bleu des retouches »** : ce qui a bougé à la dernière passe
s'écrit en bleu, et le bleu de la passe d'avant redevient neutre — dans cet ordre,
sous peine d'effacer ce qu'on vient de marquer. C'est le repère qui permet de rouvrir
la page et de voir en un coup d'œil ce qui est nouveau, au lieu de la relire en
entier. Deux garde-fous à connaître avant d'y toucher : le bleu ne repeint jamais un
encadré de question — sa couleur dit déjà son état (§3) — et il ne se pose jamais sur
le texte de Benjamin.

**À lire avant la première écriture de la session**, pas de mémoire. Chacune de
ces règles a coûté un dégât réel ; les deux skills les partagent pour qu'une
correction ne se fasse qu'une fois.
