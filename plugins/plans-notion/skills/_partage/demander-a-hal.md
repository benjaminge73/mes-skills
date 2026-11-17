# Quand s'adresser à Hal

Hal est l'agent Hermes qui tourne sur le VPS, avec la mémoire de Benjamin (le `fact_store`,
profil `jerome-kairviel`). Une session peut lui poser une **question** ou lui demander un
**geste**. Ce fichier dit quand, comment, et ce qu'on ne lui demande jamais.

## 1. Poser une question

Le premier geste reste la recherche sans modèle dans la mémoire (`skills/plan-notion/enquete.md`,
section « La mémoire de Hal »). On pose une question à Hal quand elle ne tranche pas :

- une préférence de Benjamin que le `fact_store` ne porte pas ;
- un état du VPS (un service, un fichier, une version) qu'on ne peut pas lire depuis la session.

Depuis le VPS, la question part sur l'entrée standard, la réponse sort sur la sortie :

```bash
python3 ~/.hermes/scripts/demander_a_hal.py question --plan <page du plan> [--session <id>] <<'EOF'
<la question, en texte>
EOF
```

Si Hal ne répond pas dans les 120 secondes, ou rend une sortie vide, la commande sort avec un
code non nul et une erreur lisible sur la sortie d'erreur. Ce n'est pas une réponse : on le dit
au pilote, on n'invente pas la réponse. Il n'y a aucun plafond d'appels (décision de Benjamin) ;
ce qui compte, c'est de ne pas poser une question que la mémoire tranche déjà.

## 2. Demander un geste

Un geste est une commande que la session ne peut pas tenir elle-même : longue, interactive, ou à
lancer dans tmux (un terminal persistant). La session ne la lance pas : elle la demande.

```bash
python3 ~/.hermes/scripts/demander_a_hal.py geste --plan <page du plan> \
  --demande "<ce qu'on veut, précisément>" --pourquoi "<la raison>" \
  [--refus "<le refus de garde-fou, mot pour mot>"] [--session <id>]
```

La commande rend l'identifiant de la lettre, puis sa classe (`a_faire` ou `a_renvoyer`), puis
« Hal la lira à son prochain passage, 10 minutes au plus ». Code 0 : lettre posée. Code 1 : lettre
non écrite, rien n'est parti, à reprendre. Code 2 : usage incorrect.

Le cron `plans-veille` relève la lettre à chaque passe (dix minutes au plus) et la rend à Hal.
Hal répond dans la section « ## Courrier de Hal » de la page du plan, et la session reçoit la
sonnette (le signal qui la réveille). Après avoir posé un `geste`, la session arme un réveil
(`plan-en-cours.py attendre --raison "geste demandé à Hal"`, puis son mécanisme de réveil habituel),
car Hal ne sonne la session qu'en répondant : sans réveil, elle dort jusqu'à une relance.

## 3. Ce qu'on met dans la demande

- **Le plan** : sa page Notion.
- **Ce qu'on veut**, précisément : la commande ou le geste, pas un résumé.
- **Pourquoi** : la raison pour laquelle la session ne peut pas le tenir.
- **Le refus, s'il y en a un** : si la demande suit un refus de garde-fou, ce refus va dans
  `--refus` (ou `Refus :`), mot pour mot. Sans lui, Hal ne sait pas qu'un garde-fou a dit non, et
  le geste n'est pas noté à #journal.

Le classement lit la demande et le refus, pas le pourquoi. Une formulation qui nomme le geste
sans ambiguïté évite un classement à tort.

## 4. Ce qu'on ne demande pas

Un geste **irréversible** ne va jamais à Hal. Ce sont, au minimum :

- supprimer sans copie ;
- réécrire l'historique d'une branche partagée (force push) ;
- envoyer quelque chose à un tiers (courriel, message, commentaire public) ;
- dépenser de l'argent ;
- toucher à un secret (jeton, mot de passe, clé, `.env`).

Ces gestes-là se disent à Benjamin, en une ligne, avec la raison. Le script les classe
`a_renvoyer` : Hal ne les exécute pas, et la demande part à #arbitrage.

Le merge vers `main` reste à la CI, au vert : ni la session ni Hal ne le font.

Hal fait tout le reste, y compris ce qu'un garde-fou vient de refuser, **si le geste est
réversible**. C'est la décision de Benjamin du 2026-11-17 : Hal note alors ce geste, la demande et
le refus d'origine à #journal.

## 5. Depuis un Mac, sans Hermes

Pas de script sur un Mac. La demande s'écrit dans une section `## Demandes à Hal` de la page du
plan, en lignes qui commencent par :

- `Demande :` : le geste, précisément ;
- `Pourquoi :` : la raison ;
- `Refus :` si besoin : le refus de garde-fou, mot pour mot.

Une ligne chacune, en début de ligne (une puce devant est tolérée). Une demande sans `Pourquoi :`
est dite illisible par le relevé. Le relevé `plans-veille` la lit au passage suivant (dix minutes
au plus) et la traite comme ci-dessus. Cette section ne porte que des gestes : une question se
pose depuis le VPS.
