# D'où vient un instantané, et pourquoi rien ne le rattrape

Déplacé depuis `CLAUDE.md` pour garder ce fichier sous son plafond de taille (`taille-claude-md.py`) ; le texte est repris tel quel.

Établi le 2026-09-11, en remontant le `0.3.0` de l'incident du même jour —
voir README, chapitre « Les trois copies du même plugin ».

**`plans-notion` n'a jamais été en 0.3.0 dans ce dépôt.** `mes-skills` démarre le
plugin à **0.7.0**, le 2026-09-07. La version 0.3.0 vient d'ailleurs : de
l'historique de `hermes-custom`, sous `plugins/plans-notion/`, autour du
2026-09-03 — l'époque où **ce dépôt-là** était sa propre marketplace. Elle en est
sortie le 2026-09-07 par le commit `1f105b0`, « les skills et le plugin partent
dans mes-skills ».

Un instantané `@inline` est donc **un fossile** : une capture figée, prise à un
instant donné, d'une source qui peut avoir déménagé ou disparu depuis. Trois
conséquences qui se déduisent de là et qu'il faut avoir en tête :

- **`autoUpdate` ne peut rien pour lui.** Il n'a aucun lien avec la marketplace
  `atelier` : ce n'est pas une installation en retard, c'est une copie sans
  canal. Attendre qu'elle se mette à jour, c'est attendre indéfiniment.
- **Le supprimer du disque ne sert à rien.** Les instantanés sont
  **retéléchargés à chaque démarrage** : mesuré le 2026-09-11, dix-sept dossiers
  sous `~/.claude/remote/plugins/<hash>/` tous écrits dans la même seconde que le
  boot de la session, à ~200 ms d'intervalle.
- **Quinze de ces dix-sept sont les plugins officiels d'Anthropic** (`github`,
  `vercel`, `design`, `engineering`, `playwright`, `typescript-lsp`…). Les deux
  autres seulement sont ceux de Benjamin. C'est ce qui rend le tri possible :
  un nom qui n'est pas dans le catalogue officiel et qui apparaît là est, par
  construction, une inscription faite côté `claude.ai`.

**Le traitement est donc côté `claude.ai`, jamais dans un dépôt** : retirer ou
resynchroniser l'inscription sur la surface qui pousse ces `--plugin-dir`.
⚠️ Préférer « mettre à jour » à « supprimer » quand l'option existe : dans une
surface où la marketplace `atelier` n'est pas installée, l'instantané peut être
la **seule** copie présente.

**Ce qui a été écarté** : mesuré le 2026-09-22, `disableSideloadFlags` ne fait
**pas** sortir la CLI en erreur — une affirmation antérieure de ce fichier le
disait à tort, et c'est corrigé ici. Le binaire installé porte le message
`disableSideloadFlags: dropping @inline plugin specs at load time` : il
**ignore** silencieusement les specs `--plugin-dir` au lieu d'échouer. Le
réglage reste écarté malgré tout, pour deux raisons qui tiennent sans cette
erreur : il est de portée « managed settings »
(`/etc/claude-code/managed-settings.json`, absente de ce poste), et il
tuerait aussi les quinze plugins officiels d'Anthropic qui arrivent par le
même mécanisme `--plugin-dir`.

**La portée projet a été essayée, et elle est écartée** : déclarer le plugin
dans le `.claude/settings.json` **versionné** d'un dépôt n'enregistre rien —
Claude Code exige le scope `user` ou `managed` pour une marketplace sur source
réseau. C'était séduisant parce que c'est la seule portée qui voyage jusqu'au
cloud, où `/plugin` n'existe pas. Deux sources concordantes le referment :

- **le README de ce dépôt**, section « Installation → En local », depuis le
  **2026-09-07** : il cite le refus mot pour mot — *« a marketplace on a network
  location must be declared under `extraKnownMarketplaces` in USER or managed
  settings (project/local scope cannot vouch for it) »*. C'est la source la plus
  proche et la plus lisible, et c'est celle qu'on a manqué de relire ;
- `hermes-custom`, commit `1f105b0` du même jour : l'essai y avait déjà été fait
  et avait déjà échoué — « la déclaration existait ici et n'installait rien » —
  au point d'être l'une des trois raisons de la scission qui a créé ce dépôt-ci ;
- deux sondes du **2026-09-11** : un `.claude/settings.json` volontairement
  cassé, puis un plugin bidon activé en portée projet — ni `claude plugin list`
  ni `claude plugin marketplace list` ne bronchent.

Un essai avait malgré tout été posé sur `vahiny` le 2026-09-11, faute d'avoir lu
l'historique de `hermes-custom` ; il a été annulé le jour même. **Un fichier qui
a l'air de configurer quelque chose et ne configure rien est pire que pas de
fichier** — c'est une dérive silencieuse de plus, dans un dépôt dont tout le
travail du jour consistait à en fermer une.
