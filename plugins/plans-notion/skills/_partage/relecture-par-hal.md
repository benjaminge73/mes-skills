# La relecture du plan par Hal

Hal est l'agent Hermes du VPS, qui a la mémoire de Benjamin (le `fact_store`, profil
`jerome-kairviel`). Avant qu'une page de plan passe `en revue`, la session la fait relire
par Hal, et son avis reste écrit dans la page. Ce fichier dit quand, comment, avec quoi,
et ce que Hal ne fait pas. `SKILL.md` en garde le principe ; les autres demandes à Hal
(une question, un geste) sont dans `demander-a-hal.md`.

## 1. Le cadrage, un rendez-vous avant les questions

Le cadrage avec Hal a lieu juste après l'enquête et avant l'écriture des questions. C'est le
seul rendez-vous obligatoire avec Hal avant la relecture ; le reste se demande à la demande,
par `demander_a_hal.py question` (`demander-a-hal.md` § 1). La session lui présente ce que
l'enquête a trouvé, ce qu'elle n'a pas pu lire, et les décisions déjà prises.

Le rendez-vous se trace par une ligne de « Contraintes techniques vérifiées », en gras ou en
puce :

```
Cadrage avec Hal : <date> — <ce que ça a changé, ou « rien ne change »>
Cadrage avec Hal : non tenu — <erreur>
```

`relire` refuse le tour 1 (code 2) si la page ne porte pas cette ligne. Une ligne `non tenu`
passe ce contrôle : elle dit que le rendez-vous a échoué, pas qu'il a eu lieu.

## 2. La pré-lecture, par l'agent lecteur

La pré-lecture se fait avant l'appel à `relire`. La session lance un agent
`plans-notion:lecteur` (Haiku) **par plan ouvert des mêmes dépôts**, plan maître compris, et
joint leurs fiches à la page. La fiche de l'enquêteur, cochée, et la sortie de
`verifier-fiche-enquete.py` sont jointes à la pré-lecture aussi. Cela se joue côté session, hors du délai de `relire`. La fiche est celle de l'agent `lecteur` :
courte et sourcée, elle donne le Statut, la Branche, la date, les étapes avec leurs fichiers
touchés et ce qui en reste, les questions ouvertes et tranchées, et les affirmations sur le dépôt à
revérifier.

Mesuré : avec la pré-lecture, Hal nomme les conflits fichier par fichier ; sans elle, il
soupçonne seulement. Les fiches rejoignent le bloc « Plans ouverts des mêmes dépôts » (§ 7).

## 3. La relecture

```bash
python3 ~/.hermes/scripts/demander_a_hal.py relire --plan <url de la page> --tour <1|2> <<'EOF'
<l'entrée : le texte de la page, puis le bloc des plans ouverts, puis les fiches>
EOF
```

Hal n'a ni Notion ni le contexte de la session : c'est donc la session qui lui passe le texte de
la page. L'entrée se compose de la page, du bloc « Plans ouverts des mêmes dépôts » (§ 7) et des
fiches de la pré-lecture (§ 2). La commande coupe la page au premier de deux titres, écrits à
l'identique par la session : `## Plans ouverts des mêmes dépôts` (le bloc § 7) et `## Fiches de
pré-lecture` (les fiches). Tout ce qui précède le premier titre est « la page » : la ligne
`Cadrage avec Hal :` doit s'y trouver, sinon le contrôle du tour 1 refuse. Le délai de `relire` est de 300 secondes (constante
`DELAI_RELECTURE_S`) ; `question` garde 120 secondes.

Avant `relire`, la session joint à la page sa copie cochée de la liste de relecture commune
(`${CLAUDE_PLUGIN_ROOT}/skills/_partage/listes/relecture-plan.md`), placée avant le premier titre :
elle fait donc partie de « la page » pour la commande. Les cases 1 à 15, 20 et 21 sont cochées
par la session, chacune avec sa preuve ; les cases 16 à 19 restent décochées tant que l'avis de Hal
ne les tranche pas (§ 9). La même liste sert à `plan-notion` (`passer-la-main.md`) : une seule liste,
deux moments.

La sortie de Hal a une forme fixe : une ligne `VERDICT: OK` ou `VERDICT: RESERVES` ; une
réserve par ligne, `R<n>`, avec sa source entre parenthèses, `(source : …)` ; les rubriques
« Ce que j'ai vérifié » et « À vérifier par la session ». La commande y ajoute la rubrique
« Commandes jouées par Hal » (§ 6).

## 4. Les deux tours

Deux tours au plus.

- **Tour 1.** `VERDICT: OK` : l'avis est rendu, la page peut passer `en revue`, sans tour 2.
  `VERDICT: RESERVES` : la session répond à chaque réserve (§ 6), corrige la page pour celles
  qu'elle retient, puis rejoue `relire --tour 2`.
- **Tour 2.** Un tour 2 rendu passe, quel que soit son verdict. Ses réserves restantes vont
  dans un encadré « Réserves restantes » de la section `Avis de Hal`.
- **Au-delà.** Pas de troisième relecture : la session pose `en revue`, et les réserves
  restantes restent visibles dans la page.

## 5. Le repli : un second essai, puis « Avis non rendu »

Une sortie n'est pas utilisable, et compte comme vide, si elle est dans l'un de ces cas : délai
dépassé, sortie vide, pas de ligne `VERDICT:`, réserve sans `(source :`, ou `OK` sans la liste de
ce qui a été vérifié.

Sur un échec (code 1 de `relire`), la session relance une fois, avec le même `--tour`. La commande
ne relance rien elle-même : elle note chaque échec au registre (§ 10). Deux échecs notés valent un
avis rendu pour le hook. Si le second échoue aussi, la session écrit dans `Avis de Hal` :

```
Avis non rendu : <erreur>, deux essais, <dates>
```

Un avis ne s'invente jamais : la session n'écrit ni « OK », ni une liste de réserves, ni une
réponse à la place de Hal. Le hook accepte les deux échecs notés comme un avis rendu, pour que le
plan ne reste pas bloqué sur une panne de Hal. C'est une trace de panne, pas un avis, et la page
doit le dire.

## 6. La section « Avis de Hal »

Placée **après `Questions ouvertes`**, elle porte les deux tours au plus. Pour chaque tour : la
date, le verdict, les réserves `R<n>` chacune avec sa source, les rubriques « Ce que j'ai vérifié »
et « À vérifier par la session », puis « Commandes jouées par Hal ». Sous chaque réserve, la
réponse de la session : retenue ou écartée, et pourquoi. Une réserve écartée sans raison n'est pas
une réponse.

```
## Avis de Hal

### Tour 1 — <date> — VERDICT: RESERVES
- R1 (source : <fait, fichier ou commande>) — <la réserve>
  - Réponse de la session : retenue — <ce qui a été corrigé>
- Ce que j'ai vérifié : …
- À vérifier par la session : …
- Commandes jouées par Hal : …

### Tour 2 — <date> — VERDICT: OK
…

> Réserves restantes : …   (après le tour 2 seulement)
```

Les commandes jouées par Hal sont recopiées telles quelles dans l'avis, sous la rubrique
« Commandes jouées par Hal » : la sortie de `relire` la rend déjà prête, la session la reprend sans
la retoucher. Une commande qui écrit (redirection, `rm`, `mv`, `git fetch`, `git commit`,
`git checkout`, `git reset`, `sed -i`, `pip`, `systemctl start` ou `stop`, `hermes cron create` ou
`edit`) est signalée en tête de l'avis par « Écriture signalée : <commande> ». Elle est signalée,
pas empêchée : la session décide quoi en faire.

## 7. Le bloc « Plans ouverts des mêmes dépôts »

Avant `relire`, la session le compose, sous le titre `## Plans ouverts des mêmes dépôts` (à l'identique,
c'est le titre qui coupe la page, § 3), depuis la base `Plans Claude` : les plans dont `Repo` vaut
le dépôt de la page et dont `Statut` n'est pas `execute` (seul statut de fin, `SKILL.md` § 2), la
page elle-même exclue. Pour chaque plan : titre, `Statut`, `Branche`, et les fichiers touchés quand
la page les porte. Ce qui manque reste marqué absent : rien ne se devine.

## 8. Le plan maître

Avant d'écrire `en revue` sur un plan maître, la session lance un agent `lecteur` par plan de son
lot, joint leurs fiches à la page du maître, et appelle `relire`. Un maître relu une fois passe ses
recalculs de `Statut` suivants sans nouvelle relecture (§ 10). Il n'existe pas de script de
dispense : la relecture reste une décision de la session.

## 9. Ce que Hal apporte, ce qu'il ne fait pas

Hal n'apporte que ce que la session ne peut pas savoir : préférences et décisions passées de
Benjamin (`fact_store`), autres plans en cours (conflits, doublons), état réel du VPS, pièges déjà
payés. Il ne refait pas le filtre de fin de plan-notion ni la qualité générale du plan. Chaque
réserve cite le fait ou la source qui la fonde ; pas de « OK » nu : un « OK » vient avec la liste
de ce qui a été vérifié.

Hal ne coche aucune case de la page. Il peut appuyer ou contester une recommandation ; la décision
reste à Benjamin.

Hal lit le VPS en lecture seule. Il dispose de `memory`, `session_search`, `terminal`, et de 12
tours au plus. La consigne lui nomme les commandes permises : `ls`, `cat`, `grep`, `git log`,
`git diff`, `git show`, `git status`, `hermes cron list`, `systemctl --user status`. Il liste dans
« À vérifier par la session » les faits du VPS qu'il soupçonne.

Les quatre points de Hal sont les cases 16 à 19 de `${CLAUDE_PLUGIN_ROOT}/skills/_partage/listes/relecture-plan.md` : préférences de
Benjamin, plans en conflit, état réel du VPS, pièges déjà payés. Le reste de la liste n'est pas le sien.

## 10. Le registre et le hook

Le registre est un fichier par page : `~/.hermes/state/relectures-hal/<id de page, 32 caractères>.json`.
Le dossier se surcharge par la variable `HERMES_RELECTURES_DIR`. Il porte la page et, pour chaque
tour, son numéro, sa date, son verdict, le nombre de réserves, sa durée et son issue. `relire` y
note aussi chaque commande jouée par Hal, et chaque échec.

Un avis vaut pour la page entière : les passes suivantes qui reposent `en revue` ne relancent pas
la relecture.

Le registre ne compte que les appels faits : un refus de la commande (code 2, usage ou tour 1
sans cadrage) n'y entre pas.

Le hook `refuser_revue_sans_avis.py` refuse `en revue` sans avis enregistré. Il laisse passer si le
tour 1 rend `OK`, si un tour 2 a été rendu quel que soit son verdict, ou si deux échecs sont notés,
quel que soit leur tour.
Il ne s'active que si `~/.hermes/scripts/demander_a_hal.py` existe et déclare
`RELECTURE_DISPONIBLE = True`. Il couvre aussi `composio execute NOTION_UPDATE_PAGE` (le slug entier,
pas `NOTION_UPDATE_PAGE_MARKDOWN`) quand sa charge, en ligne ou dans `-d @fichier`, pose
`Statut` = `en revue` ; une charge illisible laisse passer.

## 11. Le Mac et Remote Control

Une session ouverte depuis le Mac par Remote Control (ou par l'app de bureau) tourne sur le VPS :
c'est le service `claude-remote-control-vps.service`, avec `HOME=/home/ubuntu`. Elle voit le script,
le registre et le hook, donc cette règle s'y applique tout entière.

Une session qui tourne sur le Mac lui-même est hors périmètre. Il n'y a pas de script, donc pas de
relecture par Hal : le hook laisse passer `en revue`. La session l'écrit dans `Avis de Hal` :
« Avis non rendu : session hors du VPS ». C'est Benjamin qui relit le plan. La demande ne passe pas
par `## Demandes à Hal` : cette section ne porte que des gestes (`demander-a-hal.md` § 5).
