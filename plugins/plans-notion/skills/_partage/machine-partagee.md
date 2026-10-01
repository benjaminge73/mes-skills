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

Le script est `${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/etat-machine.py`.
Avant toute action lourde, dans cet ordre :

1. **`releve`** : `etat-machine.py releve` rend le verdict (`libre`, `chargée`
   ou `saturée`) sur la première ligne, puis les causes.
2. **`prendre`** : `etat-machine.py prendre "<action>" --plan "<titre du plan>"
   [--attendre <s>] --pid $$`. Code 0 : le jeton est à toi ; 3 : un autre le
   tient ; 4 : machine `saturée` ; 2 : usage. Le détenteur est par défaut le
   **PID parent** du script : si l'appelant est lancé dans un sous-shell
   éphémère, `$$` y vaut le PID de ce sous-shell et le jeton est repris aussitôt
   (le processus a disparu). Passer alors `--pid` avec le PID d'un processus qui
   **vivra autant que l'action**, par exemple celui du script qui l'enchaîne.
3. **L'action.**
4. **`rendre`** : `etat-machine.py rendre --pid <le même pid>`, **toujours**,
   même si l'action a échoué ou été interrompue. En shell, un `trap` sur `EXIT`
   posé juste après `prendre`. Un jeton non rendu bloque les autres plans
   jusqu'à la mort du PID.

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
