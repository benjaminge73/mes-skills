# Journal de la boucle d'amélioration de la liste de relecture

Lu par `boucle_liste.py` (cron de Hal, créé à la clôture de l'étape 7 du plan « Refonte des plugins par la checklist »).
Une section par liste ou par plan : `## Code` pour la liste de relecture. Le plafond de dépense est commun à toutes les
sections. Le jour du bilan de Q2, la ligne du bilan s'ajoute en tête de ce fichier, au format `Bilan de Q2 : AAAA-MM-JJ`
(sans ligne, le script ne mesure rien et rend le code 5).

## Code

### 2026-11-23 — ombres du premier passage
- Ombres présentes sur le VPS : 4 (ombre-etape-1 à ombre-etape-4), sans tri du pilote ni liste_sha256 : aucune étape comptable à ce jour.
- Ligne candidate : aucune

## Enquête

Liste d'enquête d'un plan (`plugins/plans-notion/skills/_partage/listes/enquete.md`), lue par `boucle_liste.py --section Enquête`.
- Source des candidats : les lignes « découverte — trouvable au plan » des clôtures de plan, c'est-à-dire les faits que l'exécution a trouvés plus tard alors que l'enquête pouvait les voir. Source non branchée : aucun fichier ne reçoit encore ces lignes, donc la section n'a aucun candidat et ne dépense rien.
- Règle de garde : une case candidate est retenue si son rappel monte sur le banc d'enquête (`enquete.py`) contre la base, et si sa hausse de bruit ne dépasse pas celui de l'A/A, comme pour « Code ». Mesure non branchée : `enquete.py` ne prend pas de liste candidate en argument.
- Commande : `python3 <dossier>/evals/banc-relecture/boucle_liste.py --section Enquête --cron`, dans le plafond commun de 5 dollars par mois avec « Code ». Pas de ligne « Bilan de Q2 » à attendre : la garde de code 5 ne vaut que pour « Code ».
