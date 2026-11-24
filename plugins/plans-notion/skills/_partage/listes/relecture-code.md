CHECKLIST DE RELECTURE v2 — passe chaque section, une par une. Pour chacune, écris « rien » ou une remarque argumentée (fichier:ligne + scénario concret). Ne saute aucune section : les défauts les plus souvent manqués sont en A, B et C.

A. CONFORMITÉ AU PLAN — relis le brief AVANT le code et dresse la liste de ce qu'il fixe, puis coche chaque point dans le code :
   1. Chaque décision tranchée citée (« Q2 : … », « décision : … ») : appliquée telle quelle ? Un cas que la décision compte d'une façon et que le code traite autrement (ex. « compté contre le favori » vs « traité en panne ») est un écart.
   2. Chaque interface nommée par le plan (nom d'option, argument positionnel ou nommé, clé, format de sortie, code de sortie) : identique à la lettre ?
   3. Chaque donnée que le plan dit d'utiliser (« grille sur titre + résumé », « marché quelconque ») : vraiment lue et transmise jusqu'au bout ?
   4. Fichiers autorisés : un fichier touché hors liste, ou une retouche que l'objectif ne demande pas (une ligne de registre, une description), est un écart, même s'il est anodin.
   5. Résidus : après le changement, reste-t-il des phrases, prompts, en-têtes ou messages qui décrivent l'ANCIEN comportement ? Cherche l'ancien terme (Grep) dans tout le dépôt.

B. RETRAIT OU RENOMMAGE INCOMPLET — si l'étape retire, renomme ou change un comportement : cherche l'ancien nom et l'ancien comportement dans les docstrings, la doc (`docs/`, README), les prompts de cron, les commentaires et les fichiers de config. Chaque mention restée vraie hier et fausse aujourd'hui est une remarque.

C. TESTS QUI NE TESTENT RIEN — pour CHAQUE test ajouté ou modifié :
   1. Invente deux mutations plausibles du code testé (condition inversée, comparaison relâchée comme `endswith` au lieu d'égalité, branche supprimée). Le test échouerait-il ? Sinon : remarque.
   2. Le test passe-t-il par le vrai code, ou recopie-t-il la donnée ou la configuration (ex. relire l'ExecStart au lieu de le passer au vrai parseur) ?
   3. Doublon : un test déjà présent attrape-t-il exactement la même panne ? Alors celui-ci est en surnombre.
   4. Assertion triviale ou sur une sous-chaîne de prose, test qui passerait sans le correctif : remarque.

D. ROBUSTESSE DES ENTRÉES — une seule entrée invalide (date illisible, ligne vide, champ manquant) fait-elle échouer tout le lot au lieu d'être écartée ? Une entrée externe (lien, nom, texte) arrive-t-elle sans guillemets ni contrôle dans une commande shell, un chemin ou un prompt ?

E. BUGS DE CORRECTION — bornes, cas vide ou unique, conditions inversées, ordre des opérations, erreur avalée en silence, exception non attrapée (`EOFError`, `UnicodeDecodeError`…), code de sortie faux, chemin relatif qui ne marche que depuis un dossier, cliquet ou garde contournable en retirant une clé.

F. CONCURRENCE ET ÉTAT — courses, fichiers partagés, état persistant mal remis à zéro, rotation comptée en enregistrements au lieu de jours.

G. SÉCURITÉ ET RESSOURCES — validation d'entrée, secrets, réseau (redirections, en-têtes renvoyés), taille et mémoire non bornées.

H. PERFORMANCE — boucle coûteuse, lecture répétée, croissance non bornée.

Rends le verdict au format du relecteur (RIEN À SIGNALER ou REMARQUES (n)), une remarque par défaut, classée dans sa catégorie.
