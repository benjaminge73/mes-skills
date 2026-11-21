> Détail de la section « 7. Maquettes HTML » de `SKILL.md` (skill plan-notion), sorti du skill pour le ramener sous son budget de taille. Lire ce fichier avant de poser une maquette.

Dès que le chapitre `Maquette` en exige une (§3) — une étape au moins change
ce qui s'affiche —, **chercher d'abord le design system du dépôt** — un fichier de tokens, un dossier de composants, une section dédiée
du `CLAUDE.md` (exemple concret, `vahiny` : `src/styles/tokens.css`,
`src/ds/`) — avant même d'esquisser la maquette :

- **s'il existe**, la maquette s'en sert — ses composants, ses tokens — et
  dit d'où viennent ses valeurs, comme une contrainte vérifiée, pas une
  affirmation ;
- **s'il n'existe pas**, une question ouverte le dit dans le plan, et la
  maquette assume d'être une proposition, pas un écran garanti.

Produire ensuite la maquette et la **poser dans la page, en bloc HTML** — un
fichier `.html` joint par `create-attachment` et affiché par `<embed>`, sans
Vercel. Le geste en deux appels, le remplacement d'une passe à l'autre, le
poids, la mise en page, ce que le bac à sable permet et le repli Vercel
vivent dans un fichier partagé :

📄 `${CLAUDE_PLUGIN_ROOT}/skills/_partage/maquettes-html.md`

**À lire avant de poser une maquette**, pas de mémoire : un envoi jamais
attaché à la page expire sans prévenir, et un bloc de code affiche la source
au lieu de l'écran.
