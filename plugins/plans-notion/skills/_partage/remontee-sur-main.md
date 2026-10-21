# La PR, puis la remontée sur `main`, et le statut qui va avec

Fichier référencé par `executer-plan-notion` (§6). À lire dès qu'un plan a une
PR ouverte ou qu'on s'apprête à en ouvrir une : à la clôture elle-même, sur une
demande de Benjamin, ou dans une session qui reprend un plan déjà à `a merger`.

**La PR s'ouvre à la clôture, prête, sans attendre de demande.** Décision de
Benjamin du 2026-10-14 : un plan = une branche, et la clôture ouvre sa PR vers
`main` une fois la suite complète jouée en local (`cloture.md`, points 1 à 4).
Elle n'est en brouillon qu'à la demande de Benjamin. La session ne lance
**jamais** `gh pr merge` : c'est la CI qui merge une PR prête, quand les règles
du dépôt le permettent. Le statut suit le code : `a merger` tant que le travail
n'est pas sur `main`, `execute` dès qu'il y est.

Benjamin peut aussi demander la PR ou la remontée — « merge sur main »,
« tu peux merger directement », « pousse ça sur main » — ou reprendre un plan
une session plus tard. La demande ne change pas la séquence : si la PR n'existe
pas encore (clôture interrompue), elle s'ouvre comme à la clôture ; si elle
existe, on la suit jusqu'au merge. Une demande de merge ne fait donc pas merger
la session : elle fait suivre la CI.

Séquence, dans l'ordre :

1. **Ouvrir la PR** — une seule, de la branche du plan vers `main`, si elle
   n'existe pas encore : `gh pr create --base main --head <branche-du-plan>`,
   sans `--draft`. Elle s'ouvre après la suite complète locale (§6) : une PR
   ouverte sur une branche à moitié faite rejoue la CI à chaque push.
   - Titre = titre du plan ; corps = une ligne par étape reprise du journal,
     lien vers la page Notion, et la ligne `Evals:` (`cloture.md`).
   - **Le label `review-required` : la question se tranche dépôt par dépôt, en
     regardant, jamais de mémoire.** Le réflexe « le dépôt a des e2e, donc je
     pose le label » est faux, et il a coûté un aller-retour le 2026-09-22. Ce
     label n'a d'effet **que là où un workflow le lit**, et cet effet **change de
     signe d'un dépôt à l'autre**. Deux commandes y répondent, toutes deux
     jouables avant d'ouvrir :

     ```bash
     gh label list | grep review-required            # existe-t-il seulement ?
     grep -rn 'review-required' .github/workflows/   # un job le lit, et pour quoi faire ?
     ```

     Les cas relevés à ce jour (2026-10-10) :
     - **`vahiny`, `micro-trading`, `mavod-perso` — le poser**
       (`gh pr create --label review-required …`). Là où son workflow le lit, il
       commande la suite complète. Sur `vahiny`, la CI merge seule une fois tout
       vert. Sur `micro-trading`, il lance l'e2e sur le runner du VPS ; le job
       `auto-merge` attend ce vert, et `deploy` met en production. Sur
       `mavod-perso`, il commande la suite complète (smoke puis e2e). Le label
       ne retient le merge que pour les PR Dependabot.
     - **`mes-skills` — ne pas le poser.** Le job `merge-auto` en est **exclu** :
       le label y *empêcherait* le merge au lieu de renforcer la preuve.
     - **`hermes-custom` — le label n'existe pas**, et aucun de ses workflows ne
       le mentionne ; `gh pr create --label` y échoue. Le dépôt a pourtant des
       e2e : c'est un trou connu de sa CI.

     **Ce qui reste vrai partout** : la ceinture, c'est la suite complète jouée
     **en local** à la clôture (§6). Le label n'est que la bretelle, et une
     bretelle n'existe que si le dépôt en a une — ne jamais la supposer depuis la
     règle générale. Sur un dépôt qui a des e2e et où le label manque, le dire à
     Benjamin plutôt que d'ouvrir en silence : c'est un trou dans la CI, pas un
     détail à contourner.
   - **Un trou e2e non couvert par la CI du dépôt** se pose à Benjamin **avant**
     d'ouvrir, avec les trois réponses de `cloture.md` (ouvrir prête quand même,
     ouvrir en brouillon, attendre). Sans PR, `PR` reste vide et la page reste à
     `a merger`.
   - `PR` renseignée sur la page dès l'ouverture.
2. **Attendre la CI, et lire son verdict.** La CI se suit en arrière-plan, avec
   une attente bornée (`cloture.md`, point 8). Verte → point 3. Rouge : corriger
   **tout** en local, rejouer la suite complète, puis repousser une seule fois
   (chaque `push` sur la PR relance un run). Correctif structurant, ou échec
   qu'on ne sait plus diagnostiquer : même arbitrage qu'en cours de route
   (SKILL.md, §3) — la PR reste ouverte et rouge, le journal le dit, un plan de
   suite porte la suite (`plan-de-suite.md`), et la page reste à `a merger`.
3. **Le merge, fait par la CI, jamais par la session.** Sur `vahiny` et
   `micro-trading` avec `review-required`, la CI merge seule une fois tout vert ;
   sur `micro-trading`, ce merge déclenche le déploiement. Sur un dépôt sans
   auto-merge, la PR verte reste ouverte : la page reste à `a merger`, et le
   compte rendu dit à Benjamin qu'elle attend sa décision. Ce qui retient le
   merge : une PR brouillon, une CI rouge, des workflows touchés
   (`.github/workflows/`), une PR Dependabot. Sur `hermes-custom`, merger
   déploie `origin/main` sur le VPS dans la foulée.
4. **Constater le merge, sur pièce.** Qui le constate : la session qui clôt, si
   la CI a fini pendant qu'elle suivait la PR ; sinon la session suivante, qui
   lit `a merger` avec une PR renseignée, vérifie la PR et pose `execute` si
   elle est mergée. La vérification :
   `gh pr view <n> --json state,mergeCommit`, et le commit de merge présent dans
   `git log origin/main`. Une PR « mergeable » n'est pas une PR mergée, et un
   auto-merge peut encore tomber sur une CI rouge après qu'on a quitté la page :
   on constate, on ne suppose pas. Une PR fermée sans merge n'est pas un
   `execute` : c'est une décision à remonter à Benjamin, `a merger` reste, et la
   raison va au journal.

4 bis. **Mettre le poste à jour, si le dépôt en est la source.** Joué juste après
   le point 4, merge vérifié. Le dépôt est-il la source d'une marketplace
   installée sur le poste ? Oui si `claude plugin marketplace list` le cite
   (`Source: GitHub (benjaminge73/mes-skills)`) : le nom de la marketplace est
   alors la ligne qui précède cette source (ici `atelier`). Sinon, le point est
   sauté, sans bruit.
   - `claude plugin marketplace update <nom>` ;
   - pour chaque plugin dont `version` a changé dans le merge, lue dans
     `plugins/<plugin>/.claude-plugin/plugin.json` entre le commit de merge et
     son premier parent (`git diff <sha>^1 <sha> -- 'plugins/*/.claude-plugin/plugin.json'`),
     `claude plugin update <plugin>@<nom>` ;
   - une ligne au journal : « nouvelle version au prochain démarrage de session,
     ou après `/reload-plugins` ».

   Un échec de ces commandes se note au journal et ne bloque ni le point 5 ni la
   suite : le merge a eu lieu, et c'est lui que le point 5 constate. Le geste
   joue aussi quand c'est `merge-auto` qui a mergé, puisque le point 4 a vérifié
   le merge sur pièce, quel qu'en soit l'auteur.

4 ter. **Rejouer le cron touché, après le déploiement.** Joué juste après le point
   4 bis (ou après le point 4 s'il est sauté), merge vérifié. Seulement si le plan
   porte une étape `C<n>` (un cron lancé à la main) : sinon le point est sauté, sans
   bruit. Le déploiement doit avoir eu lieu d'abord : sur `hermes-custom`, le job
   `deploy` de la CI pousse `origin/main` sur le VPS (point 3).
   - `hermes cron status` : la gateway tourne, donc le tick aussi. Sinon le rejeu ne
     peut pas partir ; le dire, la cause est la gateway, pas le cron.
   - `hermes cron run <id>` : le job part au **prochain tick**, pas tout de suite.
   - Une minute d'attente au plus : un tick a lieu toutes les 60 secondes.
   - `last_status` (champ du job) lu dans `hermes cron list`. La doc ne décrit ce
     champ que pour `delivery_failed` ; s'il n'apparaît pas, `hermes cron doctor` le
     signale quand il n'est pas `ok`. `ok` : le critère de `C<n>` est rejoué pour de
     vrai. Autre valeur : rouge, plan de suite (`_partage/plan-de-suite.md`), avec le
     nom du job et la valeur lue.
   - Un job sans script (prompt ou skill seulement) n'a que cette preuve.
   - Détail et boucle de correction : `${CLAUDE_PLUGIN_ROOT}/skills/_partage/cron-a-la-main.md`.

5. **`Statut` = `execute`** — seulement si le point 4 a constaté un merge, dans le
   tour où on le constate.
   Si le plan est couvert par un plan maître, **rejouer son calcul dans le même tour**
   (`statut-maitre.py --actuel` ; `plan-notion/plan-maitre.md`, « Qui rejoue le calcul, et quand ») : le dernier
   plan à passer `execute` est celui qui ferme le lot, et c'est le maître qui reste
   en arrière.
6. Une entrée de journal **`Remontée sur main`** (H3, comme les autres, §4) : la
   PR, le commit de merge, la date, et ce qui reste à faire après le merge s'il
   reste quelque chose — **trié, pas noté** : Benjamin ne relit pas un plan
   `execute`. Une question qu'on attend de lui se pose dans la session, un travail
   qui dépasse une étape ouvre un plan de suite (`_partage/plan-de-suite.md`, « Le
   tri »), et l'entrée cite la question posée ou le lien du plan. Une PR ouverte sans merge a aussi son entrée — `PR
   ouverte`, avec le numéro et le verdict de la CI — pour que la page dise où en
   est la remontée.

**Le point 5 est celui qui saute**, et il saute toujours pour la même raison : le
merge est un moment de fin. La CI est verte, le compte rendu est écrit,
l'attention est déjà sur la suite — et la page reste sur son `a merger`,
c'est-à-dire qu'elle ment à partir de cette seconde-là. Donc : **le merge et le
statut sont un seul geste, dans le même tour.** Un merge annoncé à Benjamin sans
la page mise à jour est une étape à moitié faite, pas une étape faite.

Le passage de `a merger` à `execute` suit donc **le code, pas le calendrier** : il
a lieu au moment où la branche part sur `main`, que ce soit dans le tour du compte
rendu ou trois sessions plus tard. Tant que la branche n'y est pas, la page reste
à `a merger` — ce qui est vrai. Dès qu'elle y est, la page passe à `execute` —
sans quoi elle cesse de l'être.
