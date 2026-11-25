# Liste d'aiguillage : plan léger ou plan complet

Qui la joue : un juge modèle appelé par `_partage/scripts/aiguiller-plan.py`, deux fois, sur la demande et les fichiers pressentis, avant de proposer un plan léger (`plan-notion/plan-leger.md`). Le fichier se garde non coché. Le plan complet est le défaut : « léger » n'est rendu que si les deux passages répondent « non » à chaque case, preuve à l'appui ; Benjamin valide ensuite le passage en léger.

Une case répond `non` (la demande ne touche pas ceci, et la preuve le montre), `oui` (elle le touche) ou `doute` (rien dans la demande ni dans les fichiers ne permet de l'exclure). La trace routinière d'un plan (sa page, sa branche, sa PR, son entrée de changelog) ne compte dans aucune case.

## Les neuf cases

- [ ] A1 État ou écriture sur le VPS — la demande lit un état du serveur pour décider (services, crons en cours, configuration déployée, journaux, fichiers hors dépôt) ou le change, y compris par un déploiement. ; preuve : la phrase de la demande ou le fichier qui montre que rien ne vit hors du dépôt
- [ ] A2 Sécurité — secret, clé, jeton, mot de passe, sudo, droits, permissions, réseau, exposition, authentification, hook ou contrôle de garde, données personnelles. ; preuve : ce que touche la demande, aucun de ces éléments n'y figurant
- [ ] A3 Coût externe ou quota — appel payant (modèle, API, CI payante), quota d'un service, abonnement, dépense nouvelle ou récurrente, fréquence d'un appel qui change. ; preuve : ce que la demande fait tourner, sans service facturé ni quota
- [ ] A4 Irréversible ou écriture dans un service externe — suppression, migration, publication, envoi d'un message, écriture dans Notion, Slack, une base ou une API tierce, hors de la trace routinière du plan. ; preuve : la liste des effets de la demande, tous réversibles par un revert de la PR
- [ ] A5 Données réelles — le résultat dépend de données de production, de volumes, de mesures ou de contenus réels qu'il faudrait lire ou modifier. ; preuve : ce qui définit le résultat attendu, sans lecture de données réelles
- [ ] A6 Taille — plus de trois fichiers à modifier, tests non comptés, ou un nombre qu'on ne sait pas borner. ; preuve : la liste des fichiers à modifier, trois au plus
- [ ] A7 Cron, systemd, settings — un cron, une unité systemd, un workflow planifié ou un fichier `settings`. ; preuve : les fichiers touchés, aucun de ce genre
- [ ] A8 Nouveau script — la demande crée un script, un hook, un agent ou une commande. ; preuve : les fichiers à créer, aucun exécutable
- [ ] A9 Contrat entre composants — format d'entrée ou de sortie, interface, nom de champ, code de retour, message ou fichier qu'un autre composant lit. ; preuve : qui lit ce que la demande change, ou aucun autre composant
