# La copie locale est-elle à jour de la branche principale ?

Fichier référencé par `executer-plan-notion` (ouverture, clôture), `plan-notion` (enquête sur le code) et
`_partage/avant-le-plan.md`. Décision de Benjamin du 2026-11-20 : **avant de travailler sur un dépôt, on
vérifie que la copie locale n'est pas en retard sur la branche principale distante, et on la remet à jour
si elle l'est.** Une copie en retard fait écrire un plan, ouvrir un worktree ou une PR sur du code périmé,
et le conflit n'apparaît qu'à la CI.

Un seul geste, un seul script (il détecte `main` ou `master`, jamais en dur) :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/_partage/scripts/fraicheur-depot.py" --depot <dossier> [--appliquer]
```

Sans `--appliquer` il relève seulement (`git fetch` ne touche pas l'arbre de travail) ; avec, il avance la
branche principale locale en fast-forward, ou **rebase** la branche de travail sur la branche principale.
Il ne stashe jamais, ne pousse jamais, et remet l'arbre comme il l'a trouvé quand un rebase échoue.

## Quand

| Moment | Geste |
| --- | --- |
| Écrire un plan, enquêter sur le code, dresser la carte de voisinage | relever, sans `--appliquer` sur un checkout qu'une autre session peut occuper ; `--appliquer` seulement si l'arbre est propre et que la branche est la principale. En retard et rien appliqué : le dire dans le plan (« enquête sur `main` à <sha>, en retard de N ») |
| Ouvrir la branche du plan (`ouverture.md`) | `git fetch` puis `git worktree add … -b <branche> origin/<principale>` : la branche part de la tête distante, pas de la référence locale périmée |
| Reprendre un plan sur une branche ou un worktree existant (session suivante, `a merger` rouge) | `--appliquer` depuis le worktree avant de reprendre |
| **Avant de pousser la branche du plan et d'ouvrir la PR** (`cloture.md`, point 4) | `--appliquer` depuis le worktree, **puis** rejouer la suite locale si des commits ont été repris : le vert d'hier n'est pas le vert de la nouvelle base |

## Les cas délicats : ce que le code rend, ce qu'on fait

- **Code 0** : à jour, ou remis à jour. Continuer.
- **Code 1** : en retard, rien appliqué. Appliquer si le moment le permet (tableau), sinon le dire.
- **Code 3, modifications non commitées** : arrêt. Commiter (travail de la session) ; ne **jamais** stasher
  (un hook le refuse) ni écarter des modifications qu'on n'a pas faites. Si elles ne sont pas de la session,
  le dire à Benjamin.
- **Code 3, conflit de rebase** : le rebase est abandonné, la branche est revenue comme avant, les fichiers
  en conflit sont cités. **S'arrêter et le dire clairement** à Benjamin (fichiers, commits de la base en
  cause) ; ne pas résoudre à la volée un conflit dont on ne connaît pas l'intention. Le journal du plan le note.
- **Branche déjà poussée** : le script le signale après un rebase. Pousser avec
  `git push --force-with-lease origin <branche>`, **jamais `--force`**, et seulement sur la branche du plan
  (celle de la session). Une branche qui n'est pas la sienne ne se réécrit pas : fusionner la base à la place.
- **Code 4, pas de réseau** : la fraîcheur n'est **pas** vérifiée. Le dire en une ligne (« base non vérifiée,
  dernière référence connue »), continuer sans bloquer, et rejouer le contrôle avant la PR.
- **Code 2** : pas un dépôt git, pas de remote ou de branche principale lisible. Le dire, ne rien supposer.
