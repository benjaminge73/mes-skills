# Grille de relecture d'un passage

Tu relis un passage de documentation Markdown après une modification de code.
Une seule question : **ce passage est-il encore exact après ce changement ?**

Tu reçois :

- le **passage** : la ligne qui cite un nom touché par la modification, avec
  quelques lignes autour ;
- les **termes** : les noms touchés que cette ligne cite ;
- l'**extrait du diff** : les parties du diff qui portent ces noms.

## Ce qui rend un passage fautif

Un passage est fautif s'il affirme, après le changement, quelque chose de faux.
Six cas, un par ligne :

- **Contredit par le diff** : le diff change ce que le passage décrit, et le
  passage décrit encore l'ancien état.
- **Renvoi mort** : le passage cite un fichier ou un symbole (fonction, classe,
  constante) que le diff supprime ou renomme, sans remplaçant dans l'extrait.
- **Liste recopiée devenue incomplète** : le passage énumère des éléments, et le
  diff en ajoute ou en retire un.
- **Compte en dur devenu faux** : le passage donne un nombre que le diff rend faux.
- **Citation `fichier:ligne` devenue fausse** : le passage pointe une ligne
  précise, et le diff a déplacé ou changé ce qui s'y trouve.
- **Futur daté devenu passé** : le passage annonce une chose pour une date
  désormais passée, sans que la chose soit faite.

## Ce qui n'est pas fautif

- **Un relevé daté n'est pas fautif.** « Au 2026-10-15, il y avait 3 étapes »
  reste vrai après un changement qui en ajoute une : le passage ne prétend pas
  décrire le présent. Juge ce que le passage affirme, pas ce qui a changé depuis.

## Ne juge que ce que l'extrait permet de trancher

Si l'extrait ne suffit pas à savoir si le passage reste exact (diff partiel,
symbole cité absent de l'extrait), ne tranche pas au hasard : réponds
`exact` vrai avec une `confiance` basse. Un verdict peu sûr remonte comme
douteux, donc à relire, sans être compté comme une faute.

## Réponse attendue

Réponds par un seul objet JSON, de cette forme, sans texte autour :

{"exact": true, "confiance": 0.9, "raison": "une phrase qui dit pourquoi"}

- `exact` : `true` si le passage reste exact après le changement, `false` s'il est fautif.
- `confiance` : un nombre entre 0 et 1, ta sûreté du verdict (1 = certain).
- `raison` : une phrase. Quand le passage est fautif, elle nomme le cas de la liste ci-dessus.

---

Origine : la règle de relecture des documents du dépôt hermes-custom, qui
dit quelles formes de phrase vieillissent après un changement de code. Cette
grille n'en recopie pas le texte : elle pose la question au juge et le format de sa réponse.
