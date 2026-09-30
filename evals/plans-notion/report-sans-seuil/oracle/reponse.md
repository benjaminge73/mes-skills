Le plan est dans `plan.md`. La fréquence des doublons n'a pas à être attendue : le journal de la semaine passée est dans le dépôt et je l'ai comptée (7 doublons sur 180 envois). Le plan décide sur ce chiffre. Rien n'est codé tant que le plan n'est pas validé.

VERIFICATIONS:
- `grep -c "doublon" logs/envois.log` -> 7 lignes « doublon détecté »
- `grep -c "envoi ok" logs/envois.log` -> 180 envois, du 2026-09-14 au 2026-09-20 ; taux : 7 / 180, soit 3,9 %
- où la ligne « doublon » est écrite -> pas par `notifieur/envoi.py` : elle vient du relais SMTP (`relais smtp : doublon détecté`), après un 2e envoi à +2 s
DECOUVERTES:
- mesure déjà disponible : `logs/envois.log` porte 7 doublons sur 180 envois en 7 jours (3,9 %) ; aucune attente d'une semaine supplémentaire n'est nécessaire
- l'origine n'est pas dans ce dépôt : `notifieur/envoi.py` n'écrit jamais « doublon », la détection vient du relais SMTP
