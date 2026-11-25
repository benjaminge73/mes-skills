# La machine partagée, et le geste avant une action lourde

Fichier **partagé**, lu par `executer-plan-notion` (§3, pour la preuve ; §6,
pour la suite complète et les e2e de la clôture ; « Plusieurs plans », pour la
file) et par l'agent `executant`. Comme `vagues.md` et `revue.md`, il vit à un
seul endroit pour que le skill garde sa taille : la règle ne se duplique pas,
elle se référence.

Il part d'une mesure. Le POC du 2026-10-01 (VPS, 6 cœurs) a vu deux actions
lourdes lancées ensemble faire tomber une e2e sur un timeout et allonger la
suite de 32 %. Plusieurs sessions Claude Code partagent la même machine ;
aucune ne voit ce que fait l'autre. D'où un **jeton à places** pour les actions
lourdes, et une prise pour le tenir. Le VPS n'a **qu'une place** depuis le
2026-11-25. Le POC du 2026-10-12 en avait accepté deux (la suite de hermes-custom
seule prend 677 s, avec l'e2e de vahiny en parallèle 727 s et 720 s, sans échec),
mais la mesure du 2026-11-25 a vu 2 à 5 suites tourner ensemble (charge 35 sur
6 cœurs, pression mémoire à 59, 5,7 Go de swap) pendant que le relevé disait
encore « libre ». Règle de Benjamin du 17/11 : on repasse à une place quand la
machine sature. Une autre machine déclare son nombre de places dans son profil
(§ « Le profil machine »).

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

**La prise est automatique pour une suite lourde.** Le hook
`hooks/jeton_lourd.py` (plugin plans-notion) regarde chaque commande `Bash` avant
de la jouer. Si c'est une suite complète (pytest, vitest, jest, `npm test`,
Playwright, `claude plugin eval`, `docker run`), il la réécrit : elle part dans
l'enveloppeur `skills/_partage/scripts/sous-jeton.sh`, qui prend le jeton, joue la
commande, puis rend le jeton, même si la commande échoue. Une preuve ciblée (un
fichier de test, `-k`, `::`, `--version`) passe telle quelle, sans jeton.

- **Attente, pas refus.** Si le jeton est tenu, on attend par paliers de 60 s.
  Le plafond est de **300 s** en avant-plan et de **1800 s** en arrière-plan
  (`run_in_background`). Au plafond, la commande n'est pas jouée : sortie en
  **code 75**, avec le nom du détenteur.
- **Pas de double prise.** Une commande lancée sous un jeton déjà tenu par un
  parent (par exemple `lancer.sh`) ne reprend pas le jeton.
- **Fail-open.** Si le hook ou `etat-machine.py` échoue, la commande part sans
  jeton, avec un avertissement. Le hook ne pose aucune décision de permission :
  il ne refuse rien.
- **Limites.** Un `cd` dans une commande enveloppée ne persiste pas dans le shell
  de la session. Un lancement par `bash -c` ou par un script maison n'est pas
  reconnu : il part sans jeton. Une commande qui cite déjà `etat-machine.py`,
  `sous-jeton.sh` ou `lancer.sh` n'est pas réécrite.

**Reste au geste manuel** : le rejeu d'un plan, un build, et toute suite lancée
par un script. Pour ceux-là, le geste ci-dessous tient.

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

## Le profil machine

Le nombre de places et les seuils ne sont pas les mêmes partout : une machine les
déclare dans un **profil**, fichier JSON hors dépôt. Il est désigné par la variable
`PLANS_NOTION_MACHINE_PROFIL` ; sans elle, `${XDG_CONFIG_HOME:-~/.config}/plans-notion/machine.json`
est lu s'il existe. Ni l'un ni l'autre : pas de profil, et ce sont les valeurs du VPS.

Clés, toutes optionnelles :

- `machine` : libellé libre ;
- `places_lourdes` : entier ≥ 1 (VPS : 1) ;
- `seuil_mem_full_avg60`, `seuil_cpu_some_avg10` : nombres (VPS : 40 et 50) ;
- `seuil_mem_disponible_ko` : entier ≥ 0 (VPS : 1 572 864, soit 1,5 Go).

Une clé inconnue, une valeur du mauvais type, un JSON invalide, ou une variable
qui pointe vers un fichier absent : erreur, code 2, sur toutes les commandes, avec
un message `profil machine : <fichier> : …`. Pas de repli silencieux.

Exemple, le Mac (POC du 2026-10-16 : suite pytest lourde, 52 s seule, 214 s par
instance avec quatre en parallèle, aucun échec nouveau ; sonde
`plans-notion:sondeur` a25e4515bc8cecb21) :

```json
{"machine": "mac-m1max-64go", "places_lourdes": 4}
```

Sur macOS, `/proc` n'existe pas : le jeton (heure de démarrage du détenteur) et les
familles lourdes (suite de tests, `claude plugin eval`…) se lisent par `ps`. Limite à
garder en tête : la pression CPU et la mémoire ne se lisent pas, donc le relevé ne
rend jamais `saturée` et ne rend `chargée` que sur une famille lourde active. Le
profil du Mac règle le **nombre de places** du jeton, pas la mesure de charge.

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
range les suites, e2e et évals de **tous** les plans et les prend dans l'ordre
de la file, chacune avec son jeton : **au plus autant** qu'il y a de places (une
seule sur le VPS) tiennent le jeton à la fois. Le parallèle reste la règle pour tout le reste :
la file ne concerne que ce qui est lourd.
