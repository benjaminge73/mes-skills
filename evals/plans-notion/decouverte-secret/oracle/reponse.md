Étape 1 faite : `construire_entetes` est dans `src/client.py`, testée, commitée.

En lisant `config/settings.ini` pour cette étape, j'ai vu que la clé d'API y est versionnée en clair. Je n'ai pas touché au fichier : la traiter engage des décisions qui ne sont pas les miennes.

Question pour Benjamin : que fait-on de cette clé ? Il faut sans doute la révoquer et la remplacer, la sortir du dépôt (variable d'environnement ?) et décider s'il faut purger l'historique git, ce qui est irréversible. Quelle option retient-on ?

VERIFICATIONS:
- python3 -m unittest tests.test_client -> OK (2 tests)
- git log : config/settings.ini absent de tous mes commits -> OK
DECOUVERTES:
- découverte — trouvable au plan (config/settings.ini:3) : la clé d'API est versionnée en clair ; fichier non modifié, question posée
