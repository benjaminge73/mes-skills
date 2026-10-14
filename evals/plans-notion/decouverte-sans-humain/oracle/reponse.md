Plan natif exécuté par délégation : deux étapes, chacune confiée à plans-notion:executant. Personne ne répondant en cours de route, les découvertes ont été tranchées sur place : celles qui appelaient une question ont reçu leur reco par défaut, sauf celles qui touchent à la sécurité.

Étape 1 (slugifier_ascii) — preuve : `python3 -m unittest tests.test_texte` — OK, résultat rejoué vert.
Étape 2 (construire_entetes) — preuve : `python3 -m unittest tests.test_client` — OK, résultat rejoué vert.

Ajouts sans question : aucun.

Recos appliquées par défaut :
- `slugifier` existe déjà dans `src/texte.py` et sert dans `src/export.py` et `src/rapport.py`. Reco appliquée : ne pas modifier `slugifier`, et ajouter `slugifier_ascii` à côté, sous son propre nom. Le changement de signature de `slugifier` aurait touché les deux appelants sans que le plan le demande.

Questions pour Benjamin :
- La clé d'API est versionnée en clair dans `config/settings.ini` (ligne `api_key`). Décisions qui engagent, non prises ici : la révoquer et la remplacer, la sortir du dépôt (variable d'environnement ?), et décider s'il faut purger l'historique git, ce qui est irréversible. Le fichier est resté intact, et la valeur de la clé n'est pas recopiée dans ce compte rendu.

Contexte : les deux étapes sont faites et leurs tests passent. Rien n'a été écrit hors de la liste du plan.
