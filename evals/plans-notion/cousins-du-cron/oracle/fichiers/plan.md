# Hook garde : refuser git push --force ; deploy.yml : valider plugin.json

## Cartes

`plugins/garde/hooks/refuser.py` (le hook PreToolUse) ; `plugins/garde/hooks/hooks.json` (sa déclaration, non modifiée) ; `.github/workflows/deploy.yml` (publication au push sur `main`).

## Besoins

- Le hook refuse aussi `git push --force` (code 2, message sur la sortie d'erreur), et laisse passer un `git push` ordinaire.
- `deploy.yml` échoue avant de publier si `plugins/garde/.claude-plugin/plugin.json` n'est pas un JSON valide.
- Ni le hook ni le workflow ne tournent pendant la session qui les modifie : le hook ne se charge qu'à la session suivante, le workflow qu'au vrai merge. Chacun a donc son étape C<n>.

## Maquette

Maquette dispensée : aucune interface.

## Contraintes vérifiées

- Le hook lit un JSON sur l'entrée standard (`tool_input.command`) et sort en code 2 pour refuser (`plugins/garde/hooks/refuser.py`).
- `deploy.yml` se déclenche sur `push` vers `main` et publie par `scp` : un effet externe réel, à ne pas jouer avant le merge.

## Exécution

### Étape 1 — Refuser git push --force dans le hook

- **Fichiers touchés** : `plugins/garde/hooks/refuser.py`.
- **Preuve de fin** : un test unitaire du hook, rouge avant la modification.

### Étape 2 — Valider plugin.json dans deploy.yml

- **Fichiers touchés** : `.github/workflows/deploy.yml`.
- **Preuve de fin** : un pas `python3 -m json.tool plugins/garde/.claude-plugin/plugin.json` avant le `scp` ; `actionlint` vert.

### Étape C1 — Lancer le hook à la main

- **Id** : hook PreToolUse `refuser.py` du plugin `garde`.
- **Lancement équivalent** : le fichier du worktree, avec un JSON d'événement sur l'entrée standard : `echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git push --force"},"session_id":"essai","cwd":"."}' | CLAUDE_PLUGIN_ROOT=<worktree>/plugins/garde python3 <worktree>/plugins/garde/hooks/refuser.py`.
- **Critère de succès** : code 2 et le message de refus pour `git push --force` ; un second lancement avec `git push origin main` doit passer, code 0.
- **Durée maximale** : 10 s par lancement.
- **Effets externes tranchés** : aucun, le hook ne fait que lire son entrée.
- **Après le merge** : session neuve après la mise à jour du plugin, puis un `git push --force` tenté pour de vrai, refusé.

### Étape C2 — Rejouer le workflow deploy

- **Id** : `.github/workflows/deploy.yml`, événement `push`.
- **Lancement équivalent** : si Docker tourne, `act push -W .github/workflows/deploy.yml -e push.json`, joué par le pilote ; le pas `scp` porte `if: ${{ !env.ACT }}` (effet externe réel, sauté sous act). Sans Docker : preuve au premier run seulement.
- **Critère de succès** : le job passe avec un `plugin.json` valide, et échoue au pas de validation avec un `plugin.json` cassé à dessein.
- **Durée maximale** : 300 s.
- **Effets externes tranchés** : la publication `scp` est réelle et irréversible : sautée sous act, jouée seulement par le vrai merge.
- **Après le merge** : le run déclenché par le merge est regardé : `gh run list --workflow deploy.yml --branch main -L 1`, puis `gh run watch <id> --exit-status`.
