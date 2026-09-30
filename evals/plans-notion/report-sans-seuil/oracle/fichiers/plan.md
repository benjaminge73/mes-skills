# Doublons d'e-mails de confirmation du job du soir

## Cartes

`notifieur/envoi.py` (`job_du_soir` → `envoyer_confirmation` → transport SMTP) ; `logs/envois.log` (journal du job et du relais).

## Besoins

- Un client ne reçoit qu'un seul e-mail de confirmation par commande.

## Maquette

Pas de maquette — aucune étape ne change ce qui s'affiche (job d'arrière-plan).

## Contraintes techniques vérifiées

- **Fréquence mesurée maintenant, pas renvoyée à plus tard** : `grep -c "doublon" logs/envois.log` → **7** ; `grep -c "envoi ok" logs/envois.log` → **180**, du 2026-09-14 au 2026-09-20. Soit **7 doublons sur 180 envois, 3,9 %**, environ un par soir. Les 7 ids : cmd-1013, 1039, 1066, 1088, 1107, 1131, 1164 (`logs/envois.log`).
- Chaque doublon est un « 2e envoi à +2 s » signalé par le relais SMTP, pas par `notifieur/envoi.py` (`grep -n doublon notifieur/` : rien). Le job envoie sans jamais vérifier qu'une commande a déjà reçu son e-mail (`notifieur/envoi.py:6-9`).
- Le délai constant de 2 s pointe vers une relance automatique du transport après un délai d'attente, pas vers un double appel du job : hypothèse à confirmer à l'étape 1.
- Existant cherché : dans le dépôt (`grep -rn "doublon\|idempot" .`), puis motifs d'envoi idempotent. / trouvé : rien dans le dépôt ; le motif connu est une clé d'idempotence par commande. / fait maison parce que le dépôt n'a aucune couche d'envoi partagée.

## Questions ouvertes

### 🧭 Q1 — Comment empêcher le second envoi ?

Le chiffre est en main : un doublon par soir, soit 3,9 % des commandes, justifie un correctif sans attendre.

- [ ] (reco) Clé d'idempotence par commande : un envoi déjà journalisé n'est pas renvoyé
- [ ] Désactiver la relance automatique du transport
- [ ] Autre / complément →

## La suite

Après correction, `grep -c doublon logs/envois.log` sur la semaine suivante doit rendre 0 ; au-delà de 1, on rouvre l'enquête sur la relance du transport.

## Exécution

| Étape | Fichiers touchés | Dépend de | Vague |
|---|---|---|---|
| 1 — Trace de la relance | `notifieur/envoi.py`, `tests/test_envoi.py` | — | 1 |
| 2 — Clé d'idempotence | `notifieur/envoi.py`, `tests/test_envoi.py` | 1, Q1 | 2 |

### Étape 1 — Confirmer l'origine du second envoi

- **Choix d'architecture** : journaliser l'identifiant de tentative dans `envoyer_confirmation`. Écarté : lire les journaux du relais, hors dépôt.
- **Fichiers touchés** : `notifieur/envoi.py` (modifié), `tests/test_envoi.py` (modifié).
- **Dépend de** : —
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien.
- **Impact technique** : une ligne de journal en plus par envoi.
- **Preuve de fin** : le journal montre une ligne par tentative.
- **Test attendu** : deux tentatives pour une commande produisent deux lignes de même id.

### Étape 2 — Clé d'idempotence

- **Choix d'architecture** : `envoyer_confirmation` garde les ids déjà envoyés du jour et ne renvoie pas. Écarté : verrou distribué, disproportionné pour un doublon par soir.
- **Fichiers touchés** : `notifieur/envoi.py` (modifié), `tests/test_envoi.py` (modifié).
- **Dépend de** : étape 1, Q1.
- **Taille** : 2 fichiers.
- **Impact fonctionnel** : Rien pour le client, sinon la fin des doublons.
- **Impact technique** : état en mémoire par exécution du job.
- **Preuve de fin** : un job rejoué sur les mêmes commandes n'envoie rien de plus.
- **Test attendu** : appeler deux fois `envoyer_confirmation` pour la même commande n'envoie qu'un message.

## Journal d'exécution

_Se remplira à l'exécution._
