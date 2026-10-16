# Historique de `brainstorming`

Annexe de `SKILL.md` : provenance, garde de version, et chaque écart avec l'amont
(obra/superpowers). Le skill ne la lit pas au chargement ; elle répond à « pourquoi
cette règle a-t-elle bougé ? ».

## Provenance

*Adapté de [obra/superpowers](https://github.com/obra/superpowers) (MIT, Jesse
Vincent / Prime Radiant). Récupéré le 2026-08-03. Modifications : sortie redirigée de `writing-plans` vers
`plan-notion`, plus d'écriture de spec dans `docs/` ni de commit, « visual companion » retiré
(pas de navigateur local sur le VPS, et `plan-notion` a déjà sa voie maquette via Vercel),
renvoi codebase-memory ajouté.*

## Garde de version

Le 2026-09-08, une session a chargé le skill `plan-notion` depuis une copie
synchronisée périmée (`~/.claude/remote/plugins/<hash>/`, version 0.3.0 alors
que 0.7.0 était installée) et a travaillé tout un plan sur les mauvaises
règles. N'importe quel skill peut être chargé de la même façon : il ne
choisit pas d'où il vient, il peut seulement le constater. D'où la section
« Suis-je la bonne version ? » en tête de `SKILL.md`, qui reste opérante : une
garde dans une annexe ne serait jamais lue au moment où elle sert.

## Notes datées antérieures au 2026-10-16

*2026-08-17 — le corps interdisait en trois endroits d'appeler `plan-notion` (défaut au mode
plan natif) alors que la description promettait le passage de main. Inversé : `plan-notion` est
désormais la sortie par défaut, le mode plan natif devient la seule exception.*

*2026-09-08 — troisième adaptation, source [superpowers v6.3.0](https://github.com/obra/superpowers)
commit `b36e082` (12 août 2026). Repris tel quel, en anglais, pour que les prochains diffs avec
l'amont restent lisibles : le routeur Spike / Bounded / Architectural, sa règle « dans le doute,
le chemin le plus lourd, le cliquet à sens unique », sa table de Red Flags, ses checklists par
chemin. Adapté, en français : la section « Où va la sortie », qui remplace la sortie unique
`plan-notion` par une sortie proportionnée au chemin — Spike ne produit aucune page, Bounded une
page `plan-notion` allégée (`Cartes` · `Besoins` · `Exécution` · `Journal d'exécution`,
`Questions ouvertes` seulement si une question est réellement ouverte), Architectural la page
complète. Autre écart avec l'amont : le chemin Bounded, qui chez superpowers termine par une
implémentation directe sans document, termine ici par un hand-off à `plan-notion`, puisque cet
écosystème n'écrit jamais de code avant qu'une page Notion soit `valide`, même allégée — le
graphe et les checklists reflètent ce changement. Les mentions amont de
`docs/superpowers/specs/` et du skill `writing-plans` n'ont pas été reprises, pour la même
raison que la première adaptation (pas de spec fichier, pas de commit — `plan-notion` est déjà
la voie d'écriture). Le « Visual Companion » de l'amont reste absent, pour la même raison que
2026-08-03.*

*2026-09-29 — question à choix par l'outil structuré. La consigne « préférer les questions à
choix multiples » disait quoi poser mais pas comment : les options finissaient en texte dans le
chat, à retaper. Ajout, en anglais comme le corps, et rédigé pour rester utilisable par un autre
LLM : si l'environnement fournit un outil de question structurée (dans Claude Code :
`AskUserQuestion`), l'utiliser ; sinon, les options en texte, la recommandation en premier. La
recommandation ouvre la liste, marquée « (Recommended) », et le contexte reste dans le message.*

## Écarts avec l'amont ajoutés le 2026-10-16

Chaque ligne est un écart fait dans cette révision. Le corps reste celui de l'amont
pour tout ce qui n'est pas listé ici.

- 2026-10-16 — ton adouci : « Do NOT », « MUST », « ruthlessly », « IS the doubt »
  réécrits en phrases sobres ; les majuscules restent sur les mots d'action
  (STOP, yes) qui marquent un arrêt. Pourquoi : un ton dur faisait lire la règle comme
  une menace, pas comme une raison. Coût si faux : le modèle peut relâcher le gate
  sur les tâches « faciles » ; le gate reste écrit une fois, en entier, dans le HARD-GATE.
- 2026-10-16 — règles fusionnées : la porte d'accord, répétée six fois dans l'amont
  (HARD-GATE, « Anti-Pattern », Bounded, Checklist, Red Flags, Terminal states), est
  dite une fois dans le HARD-GATE, avec sa raison (un plan écrit sur un design pas
  encore accepté coûte une refonte) ; la section « Anti-Pattern » disparaît, sa
  substance va dans la ligne « too simple » des Red Flags. Coût si faux : une
  lecture isolée d'une section (Checklist seule) ne rappelle plus le gate ; elle
  renvoie au HARD-GATE, placé en tête.
- 2026-10-16 — « dans le doute, le chemin le plus lourd » remplacé par « nomme les deux
  chemins et demande » (Three Paths et Red Flags). Pourquoi : la consigne amont
  poussait à surclasser un doute, donc à sur-dimensionner la sortie. Coût si faux : une
  question de plus à l'utilisateur quand le doute est réel ; aucun surcoût de process
  imposé sans lui.
- 2026-10-16 — « un point d'accord par décision » (Presenting the design et Conduct of
  the dialogue) : chaque décision de design se soumet seule, à la place d'un accord
  global par section. Coût si faux : plus de tours de dialogue sur une section dense.
- 2026-10-16 — dialogue sans sous-agents, dit dans « Conduct of the dialogue ».
  Pourquoi : le brainstorming est une conversation avec l'utilisateur ; un appel
  `Agent` au milieu le coupe. Coût si faux : aucun, l'amont ne prévoyait pas de
  sous-agent, c'est une précision.
- 2026-10-16 — conseil de réglage (Opus `medium` pour un spike ou un changement borné,
  `high` pour l'architectural), dit comme conseil à l'utilisateur, sans `model:` ni
  `effort:` dans le frontmatter : le champ d'un skill ne vaut que pour le tour en cours.
  Coût si faux : un réglage de session à poser soi-même.
- 2026-10-16 — frontière avec l'enquête de `plan-notion` écrite (« The boundary with
  `plan-notion`'s survey ») : le brainstorming explore l'intention, les contraintes et
  les approches avec l'utilisateur ; l'enquête (agents `enqueteur` et `chercheur`)
  vient après, dans `plan-notion`. Coût si faux : la checklist garde « Explore project
  context » pour cadrer la question ; une carte de voisinage faite ici serait un
  doublon de l'enquête.
- 2026-10-16 — réponse dans la langue de l'utilisateur, une ligne après l'ouverture.
- 2026-10-16 — description du frontmatter réécrite pour dire quand le skill s'applique
  ET quand il ne s'applique pas (mise en forme du plan et questions de plan → plan-notion),
  pour que le routage ne dépende pas de la seule lecture du corps.
- 2026-10-16 — section « After the Design » remontée avant « Process Flow » (ordre des
  sections, pas de texte changé) : la sortie est lue avant le graphe.
- 2026-10-16 — notes de provenance et notes datées de la fin déplacées ici ; le corps
  garde la ligne de provenance et le renvoi vers ce fichier.
- 2026-10-16 — « Process Flow » et « The Process » : doublons de la checklist et des
  sections de chemin résumés ; le graphe `dot` est inchangé.
