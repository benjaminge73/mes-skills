# Ranger un `CLAUDE.md` : où va chaque ligne

Ce guide dit où va chaque ligne d'un `CLAUDE.md` trop long. Il est lu quand
`taille-claude-md.py` refuse un fichier, ou avant d'ajouter une règle dans un
`CLAUDE.md` qui approche de sa limite.

## Le fait de départ

Un `CLAUDE.md` est le fichier de consignes permanent d'un dépôt : Claude Code le
lit en entier au lancement de **chaque** session. La doc officielle de Claude
Code (https://code.claude.com/docs/en/memory.md) donne la cible : « target under
200 lines per CLAUDE.md file ». Au-delà, le fichier pèse dans chaque session, et
ses premières règles se diluent.

Ce guide reprend trois points de la même doc :

- pour alléger un `CLAUDE.md`, la voie est de le sortir vers un skill ou une
  règle à portée de chemin (« move it to a skill or a path-scoped rule ») ;
- un `@import` (une ligne `@chemin` qui inclut un autre fichier) se charge au
  lancement, comme le reste : il ne réduit rien ;
- une règle de `.claude/rules/` sans `paths:` se charge à chaque session.

## La mesure

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/taille-claude-md.py --racine . --base origin/main
```

Le script se cite par `${CLAUDE_PLUGIN_ROOT}`, comme les autres fichiers de
`_partage/` : un chemin `plugins/…` n'existe que dans le dépôt `mes-skills`, et
une session qui travaille ailleurs, avec le plugin installé, ne le trouve pas.

Le script compte chaque `CLAUDE.md`, chaque `.claude/rules/*.md` et chaque
fichier importé, chacun à part. Le plafond est 200 lignes, ou la taille du même
fichier sur la base si elle est plus grande : un fichier ne peut pas grossir
dans une PR. Sans `--base`, il avertit seulement.

## Où va chaque type de contenu

| Ce que c'est | Où ça va |
|---|---|
| Commandes, conventions, règles « toujours » qui servent à **chaque** session | Reste dans le `CLAUDE.md`. |
| Une règle qui ne vaut que pour **une partie** du code | `.claude/rules/<thème>.md`, avec un bloc `paths:` (liste de chemins, en tête du fichier, entre deux lignes `---`) qui dit à quelles parties du code elle s'applique. |
| Une **procédure en plusieurs étapes** | Un skill de dépôt : `.claude/skills/<nom>/SKILL.md`. |
| L'**historique daté** (relevé, récit d'incident) | `docs/<thème>.md`, cité par son chemin **sans `@`**. Le `CLAUDE.md` garde la règle en une ligne, avec le renvoi. |
| Ce que Claude **déduit du code** (arborescence, liste de dépendances) | Se supprime : Claude le relit dans le dépôt quand il en a besoin. |

Deux interdits, tirés de la doc :

- **Pas d'`@import` pour alléger.** Il se charge au lancement : le fichier reste
  aussi lourd, il a seulement changé de nom.
- **Pas de règle de `.claude/rules/` sans `paths:`.** Sans ce bloc, elle se
  charge à chaque session, comme le `CLAUDE.md` qu'on voulait alléger.

Une règle « toujours » ne va pas non plus en `paths:`, même si elle ne vise qu'un
dossier : un `CLAUDE.md` importé depuis un autre répertoire ne charge pas les
`.claude/rules/` du dépôt. Cas réel, `hermes-custom` : `~/.hermes/CLAUDE.md`
importe `@patches/CLAUDE.md`, donc une règle partie en `paths:` devenait invisible
aux sessions lancées par Hermes.

## La preuve qu'aucune information ne s'est perdue

Chaque ligne retirée a l'une de deux destinations, et une seule :

1. un fichier de destination, cité par son chemin dans le `CLAUDE.md` (ou
   trouvable par ce chemin) ;
2. la liste « déductible du code » de la PR : une ligne qui dit ce qui a été
   retiré parce que Claude le relit dans le dépôt, avec le fichier où on le
   trouve.

Le `relecteur` relit cette liste. Une ligne retirée qui n'a ni destination ni
place dans la liste est une perte : elle se remet, ou elle se justifie.

Un garde qui lit le texte du `CLAUDE.md` (renvois, symboles cités) ne suit pas la
ligne déplacée : il doit s'étendre au fichier qui la reçoit, et ne pas pouvoir
passer à vide si ce fichier est renommé. Cas vahiny : `tools/test_renvois_docs.py`
ne gardait que le `CLAUDE.md` ; après rangement, les lignes déplacées n'étaient
plus gardées, et l'extension passait à vide dès qu'un fichier changeait de nom.

## Procédure

1. Mesurer (commande ci-dessus). Noter les fichiers au-delà de 200 lignes.
2. Pour chaque bloc du fichier, le classer dans la table ci-dessus.
3. Avant de déplacer un bloc, `grep -rn 'CLAUDE.md'` sur le dépôt : une consigne
   lue par un agent, ou un commentaire, qui renvoie à une puce suit la ligne
   déplacée. Cas vahiny : `tools/consigne_compatibilite.md` renvoyait à une puce
   « de `CLAUDE.md` », passée en règle sans que le renvoi suive. Puis déplacer, et
   remplacer le bloc déplacé par une ligne de renvoi.
4. Relancer la mesure : le fichier doit repasser sous son plafond.
5. Remplir la liste « déductible du code » pour ce qui a été supprimé.
