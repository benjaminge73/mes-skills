# La PR, puis la remontée sur `main`, et le statut qui va avec

Fichier référencé par `executer-plan-notion` (§6), à lire à chaque fois que
Benjamin demande la PR du plan ou sa remontée sur `main` — avant, pendant ou
après l'exécution.

**Ni la PR ni le merge n'ont lieu sans sa demande.** La clôture d'un plan
s'arrête à la branche : travail complet, suite complète jouée en local, branche
poussée, page à `a merger` (décision de Benjamin du 2026-09-04). La suite arrive
quand il le décide : « ouvre la PR », « merge sur main », « tu peux merger
directement », « pousse ça sur main ». Ça arrive **avant** l'exécution, **en
cours de route**, ou **une session plus tard** sur un plan déjà à `a merger`.
Dans les trois cas, même séquence — et **elle ne s'arrête pas au merge** :

1. **Ouvrir la PR** — une seule, de la branche du plan vers `main`, si elle
   n'existe pas encore. Si la demande arrive avant la fin de l'exécution, finir
   l'exécution d'abord, suite complète locale comprise (§6) : une PR ouverte sur
   une branche à moitié faite rejoue la CI à chaque push.
   - Titre = titre du plan ; corps = une ligne par étape reprise du journal,
     lien vers la page Notion.
   - **Le label `review-required`, dès la création, si le dépôt a des tests
     e2e** (relevé du §2) : `gh pr create --base main --label review-required …`.
     Toujours, ceinture et bretelles : la suite complète a tourné en local à la
     clôture (ceinture), le label la fait rejouer par la CI (bretelles). Sur
     `vahiny`, il commande précisément ça — `tools`, `e2e`, que la CI n'y joue
     pas sur une PR ordinaire — puis, tout vert, le merge sur `main` par le job
     `auto-merge` : une PR de plan ouverte sans ce label y serait mergée sur la
     seule foi des tests unitaires. Le label doit exister dans le dépôt
     (`gh label list`) ; s'il manque sur un dépôt qui a des e2e, le dire à
     Benjamin plutôt que d'ouvrir sans — c'est un trou dans la CI, pas un détail
     à contourner.
   - `PR` renseignée sur la page dès l'ouverture.
2. **Attendre la CI, et lire son verdict.** Rouge → corriger **tout** en local,
   rejouer la suite complète, puis repousser une seule fois (chaque `push` sur la
   PR relance un run). Correctif structurant ou échec qu'on ne sait plus
   diagnostiquer → même arbitrage qu'en cours de route (§3) : PR laissée ouverte
   et rouge, journal, plan de suite (§7), page à `a merger`.
3. **Merger — si c'est ce qui a été demandé.** « Ouvre la PR » n'est pas
   « merge » : sur un dépôt sans auto-merge, la PR verte reste ouverte et la
   page à `a merger`, jusqu'à ce que Benjamin dise merge. Sur `vahiny` avec
   `review-required`, la CI merge seule une fois tout vert : y demander la PR,
   c'est demander la remontée. Sur `hermes-custom`, merger déploie `origin/main`
   sur le VPS dans la foulée.
4. **Vérifier que le merge a bien eu lieu**, sur pièce :
   `gh pr view <n> --json state,mergeCommit`, ou le commit de merge dans
   `git log origin/main`. Une PR « mergeable » n'est pas une PR mergée, et un
   automerge peut encore tomber sur une CI rouge après qu'on a quitté la page.
5. **`Statut` = `execute`** — seulement si le point 4 a rendu un merge.
6. Une entrée de journal **`Remontée sur main`** (H3, comme les autres, §4) : la
   PR, le commit de merge, la date, et ce qui reste à faire après le merge s'il
   reste quelque chose. Une PR ouverte sans merge a aussi son entrée — `PR
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
