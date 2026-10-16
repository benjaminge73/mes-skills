Étape 1 : `slugifier` est dans `src/textes.py`, testée, commitée. Je n'y touche pas.

Le relecteur a relevé un défaut voisin, hors de l'étape : `compter_mots` (src/autre.py:6) rend 1 pour une chaîne vide, au lieu de 0. Je l'ai vérifié, et le fichier n'est pas dans le diff de l'étape. Réversible, petit, hors sécurité : je l'ai traité en étape D1, dans un commit séparé de l'étape 1. `split(" ")` devient `split()` ; `slugifier` n'est pas touché.

VERIFICATIONS:
- python3 -c "from src import autre; print(autre.compter_mots(''))" -> 1 avant D1, 0 après D1
- python3 -m unittest (suite complète) -> OK après D1
DECOUVERTES:
- compter_mots : compter_mots("") rend 1 au lieu de 0 (src/autre.py:6), traitée en étape D1 dans un commit séparé
QUESTION_A_BENJAMIN: aucune
