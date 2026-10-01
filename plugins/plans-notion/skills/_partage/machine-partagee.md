# La machine partagée, et le geste avant une action lourde

Fichier **partagé**, lu par `executer-plan-notion` (§3, pour la preuve ; §6,
pour la suite complète et les e2e de la clôture ; « Plusieurs plans », pour la
file) et par l'agent `executant`. Comme `vagues.md` et `revue.md`, il vit à un
seul endroit pour que le skill garde sa taille : la règle ne se duplique pas,
elle se référence.

Il part d'une mesure : sur le VPS (6 cœurs), deux actions lourdes lancées
ensemble font tomber une e2e sur un timeout et allongent la suite de 32 %
(POC du 2026-10-01). Plusieurs sessions Claude Code partagent la même machine ;
aucune ne voit ce que fait l'autre. D'où **une seule place** pour les actions
lourdes, et un geste pour la prendre.

## Ce qui est lourd

- une **suite de tests complète** (pytest, vitest, jest) ;
- un **test e2e** ou tout test qui lance un **navigateur** sans tête ;
- `claude plugin eval` (le banc d'évals local) ;
- un **conteneur** de runner (CI rejouée en local, `docker run`…) ;
- un **rejeu de sessions** Claude.

**Ce qui ne l'est pas** : une preuve ciblée — les tests des fichiers impactés
par une étape, quelques secondes (342 tests en 16 s au POC). Les rendre lourds
sérialiserait toutes les vagues pour rien. Elle le devient dès qu'elle lance un
navigateur ou un conteneur, ou qu'elle dépasse **2 minutes**. Le pilote garde
pour lui la suite complète et les e2e de la clôture, et **ceux-là prennent le
jeton**.

## Le geste

**Tout tient dans un seul appel de shell.** Une session Claude ouvre un shell
**neuf à chaque appel de l'outil `Bash`**, et il meurt à la fin de l'appel. Le
jeton a pour détenteur un PID, et un jeton dont le PID a disparu est repris
aussitôt : un `prendre --pid $$` joué dans un appel et l'action dans un autre,
c'est un jeton qui ne protège rien. Relevé, `prendre`, `trap` de `rendre`, puis
l'action, **dans le même appel** (ou le même script). Une action plus longue que
le délai d'un appel se lance en arrière-plan (`run_in_background`) **dans ce
même appel**, jamais en deux.

```bash
EM="${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/etat-machine.py"
python3 "$EM" releve                       # 1. verdict en 1re ligne ; saturée : stop
python3 "$EM" prendre "<action>" --plan "<titre du plan>" --attendre 0 --pid $$ \
  || exit $?                               # 2. 0 accordé, 3 occupé, 4 saturée, 2 usage
trap 'python3 "$EM" rendre --pid $$' EXIT  # 3. rendu même si l'action échoue
<l'action>                                 # 4. la suite, l'e2e, l'éval
```

`$$` est le PID du shell de l'appel : il vit autant que l'action, et c'est le
`trap` qui rend le jeton à sa sortie. (Dans un sous-shell `( … )`, `$$` reste
celui du shell **parent** ; `$BASHPID` donne celui du sous-shell.) `--attendre
<s>` fait réessayer une prise sur un jeton tenu ; le détail des attentes par
paliers est plus bas.

`etat-machine.py qui` dit qui le tient. Le journal gagne, sur chaque action
lourde, une ligne `Machine : <verdict> — attente <n> min` (verdict du relevé au
moment de la prise, durée réellement attendue ; `0` si aucune).

## Machine `chargée`

Le jeton est pris, ou on l'attend, mais **quelqu'un d'autre fait déjà
travailler la machine**. On prévient, on attend par paliers, on avance :

1. **Annoncer.** `ListAgents`, filtré sur les sessions de **cette machine** à
   l'état `busy`, puis un `SendMessage` court à chacune : « je dois lancer
   <action> pour <plan>, durée estimée <n> min ; préviens-moi si tu lances une
   action lourde ».
2. **Attendre par paliers.** Un nouveau relevé **toutes les 2 minutes**, pas en
   boucle serrée. Pendant ce temps, **continuer le léger** : les étapes qui ne
   chargent pas la machine (preuves ciblées, rédaction, journal, relectures).
3. **Au-delà de 30 minutes**, ne rien forcer : l'écrire au journal et le dire à
   Benjamin, avec ce qui bloque (`etat-machine.py qui`).

## Machine `saturée`

La mémoire est au bord : lancer quoi que ce soit risque de tuer un processus
d'une autre session. **Pas d'attente en boucle** : prévenir Benjamin tout de
suite (verdict et causes du relevé), noter au journal, continuer le léger.
`prendre` refuse d'ailleurs de lui-même (code 4).

## Plusieurs plans

Le plan maître porte une section **« File des actions lourdes »**. Le pilote y
range les suites, e2e et évals de **tous** les plans et les prend **une par
une**, chacune avec son jeton. Le parallèle reste la règle pour tout le reste :
la file ne concerne que ce qui est lourd.
