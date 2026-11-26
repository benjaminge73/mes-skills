# L'activation par projet

Détail du § 5 de `changelog-et-doc.md`, lu quand la clôture touche le hub d'un projet : l'encadré d'activation, la ligne « Activée le », les trois cas, la page mère neuve. Texte repris tel quel, sauf les renvois, qui nomment le fichier où ils vivent.

La doc vivante est **activée projet par projet**. Un encadré en tête de la page `Projet` le dit :

- `📘 Doc vivante : activée`, ou
- `📘 Doc vivante : désactivée`.

L'encadré d'activation peut porter une seconde ligne, sous `📘 Doc vivante : activée` : `📘 Rétro-doc : faite AAAA-MM-JJ`. Elle s'écrit dans l'encadré d'activation de la page `Projet`, et c'est le plan de rétro-doc qui la pose à sa fin, en retirant dans le même geste l'encadré « 🚧 Doc partielle » de la page mère. Sans cette ligne, retirer l'encadré ne laisserait aucune trace : la clôture suivante le reposerait. Si la page mère n'a pas d'encadré mais que la ligne est présente, la clôture ne le pose pas.

L'encadré d'activation porte aussi, à l'activation, une ligne `📘 Activée le AAAA-MM-JJ` : la date du jour où l'encadré `📘 Doc vivante : activée` est posé. C'est elle que `doc-de-cloture.py --trous --projet` lit pour borner le rattrapage (`cloture.md`, point (e)) ; le script la cherche comme le motif `Activée le AAAA-MM-JJ`, insensible au gras ou à l'emoji qui l'entoure. Sans elle, `--trous` sans `--depuis` refuse (code 2) : la date ne se devine pas à partir du premier Changelog. Un projet activé avant l'existence de cette ligne ne la porte pas ; Benjamin l'ajoute à la main, avec la date d'activation.

Trois cas :

- **Encadré absent** (projet sans décision, ou nouveau projet) : la clôture **n'écrit rien dans le hub** (ni `Changelog`, ni fiche, ni vue d'ensemble). Elle garde l'entrée prête dans le récap de la page du plan, et pose la question dans son compte rendu : « Doc vivante : à activer pour <projet> ? ». La question est posée à chaque clôture tant que l'encadré n'existe pas.
- **Réponse de Benjamin** : le pilote pose l'encadré (`activée` ou `désactivée`). S'il active, il y ajoute la ligne `📘 Activée le <date du jour>`, puis pose l'entrée, comme un projet activé.
- **Projet activé** : la clôture crée la sous-page `📰 Changelog` si elle manque, et y pose l'entrée. Elle crée **une fiche par fonctionnalité que le plan touche**, et seulement celles-là, rangée dans sa famille (`changelog-et-doc.md` § 1) ; si aucune famille ne convient, elle en crée une. Chaque fiche créée ajoute une ligne au tableau `🧩 Fonctionnalités` de la page mère (`doc-sous-le-capot.md`, § 9.1) — son nom, sa famille, une phrase, un lien vers la fiche — **si ce tableau existe**. S'il n'existe pas, la clôture ne le crée pas et n'en invente pas : c'est le rôle de la rétro-doc, comme pour la vue d'ensemble. Une fiche déjà là ne reçoit qu'une ligne d'historique, jamais de ligne de tableau. L'encadré « Doc partielle » vit sur la page mère, plus sur la page `Projet` : si la page mère n'en a pas encore, elle en ajoute un en tête, `🚧 Doc partielle — rétro-doc pas encore faite`, et le laisse en place s'il existe déjà. Elle ne le pose que si la ligne `📘 Rétro-doc : faite` manque dans l'encadré d'activation (ci-dessus) : si elle est là, la rétro-doc est faite et l'encadré n'est pas posé. Un encadré « Doc partielle » déjà posé sur la page `Projet` par l'ancienne règle n'est pas déplacé (la clôture ne déplace jamais une page existante) : elle le signale dans son compte rendu. Elle n'écrit **jamais** de vue d'ensemble ni de processus au jugé : c'est le rôle de la rétro-doc, plan dédié par projet.

**Projet activé, pas de page mère** (décision Q3) : la clôture crée la page mère « 📚 Documentation » vide de vue d'ensemble, avec, si la ligne « 📘 Rétro-doc : faite » manque dans l'encadré d'activation, l'encadré « 🚧 Doc partielle — rétro-doc pas encore faite » (sinon la page naît sans encadré), puis la famille et la fiche ; cette page neuve n'a pas de tableau `🧩 Fonctionnalités`, donc la fiche n'y a pas de ligne (puce « Projet activé », plus haut dans ce fichier). Elle ne déplace JAMAIS une page existante, et signale dans son compte rendu les fiches restées à l'ancienne place.

Le récap de la page du plan s'écrit **dans tous les cas**. L'activation ne concerne que le hub.
