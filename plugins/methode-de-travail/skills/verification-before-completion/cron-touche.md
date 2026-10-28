# Un cron touché : on le lance maintenant, on ne l'attend pas

Complément de `SKILL.md` (tableau « Common Failures », ligne « Cron »).

Un **cron** (tâche planifiée : crontab, timer systemd, workflow `schedule:`,
job Hermes, routine ou trigger cloud, cron Vercel / Cloudflare / `pg_cron`) est un
programme que personne ne regarde tourner. « Il s'exécutera cette nuit à 2 h 30 » ou
« on verra au prochain passage » n'est pas une vérification : c'est reporter la
première preuve en production, où une erreur passe sans bruit.

Dès qu'un développement **crée ou modifie** un cron (son script, son planning, sa
commande, son unité, son workflow, ou ce qu'il lit ou écrit), la preuve est :

1. **Déclencher le job à la main, maintenant**, avec le même mécanisme que le
   planificateur : même commande, même utilisateur, même répertoire courant, même
   environnement (variables vides ou assainies comme le planificateur le fait,
   pas celles de ta session). Selon le cas : `systemd-run --wait` avec les
   propriétés de l'unité (`systemctl show`), `env -i` + `cd` du job pour une
   ligne de crontab, `hermes cron run <id>` pour un job Hermes déployé,
   `gh workflow run` ou `act` pour un workflow, le déclencheur manuel (« Run
   now ») ou l'appel de la route pour un cron de plateforme.
2. **Montrer la sortie** : code de retour, dernières lignes, effet observable
   (fichier produit, ligne en base, message reçu). Pas « ça a marché ».
3. **Ne rien conclure d'un lancement différent** : lancer le script depuis ta
   session, avec ton `PATH` et ton `HOME`, prouve le script, pas le cron. Dis
   laquelle des deux choses tu as prouvée.

Si un effet est irréversible (suppression, publication, envoi réel, dépense), le
trancher **avant** : mode à blanc existant, cible de test, ou question à
Benjamin. Ce n'est jamais une raison de ne rien lancer.

Si le lancement est réellement impossible ici (job qui n'existe qu'en production,
accès manquant), ne dis pas « terminé » : écris ce qui **n'est pas prouvé**,
pourquoi, et la commande exacte à lancer pour le prouver. Le travail est
« fait, preuve du cron manquante », jamais « fait ».
