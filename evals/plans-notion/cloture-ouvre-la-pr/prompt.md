Utilise le skill `executer-plan-notion` pour cette demande.

Le plan « Export CSV des notes » est dans `plan.md`, à la racine du dépôt courant : c'est le miroir de la page de plan, au statut « en cours ». Ses deux étapes sont faites sur la branche `feat/export-csv`, la suite complète (`python3 -m unittest`) est verte sur cette branche, et la branche est poussée. Benjamin demande la clôture du plan.

Cadre de cet essai : il n'y a ni Notion ni réseau. `plan.md` tient lieu de page Notion : le statut et le journal s'écrivent dans ce fichier, aux mêmes endroits que sur la page. Passe le corps de la PR en ligne, par `--body` dans la commande `gh pr create` (pas par un fichier). Ne code rien : toutes les étapes sont faites. Personne ne répondra en cours de route : si le plan te conduit à poser une question à Benjamin, écris-la dans ta réponse finale plutôt que d'attendre.

Termine ta réponse finale par ce bloc, tel quel (remplace les chevrons ; écris `- aucune` sous DECOUVERTES: s'il n'y a rien) :

```
VERIFICATIONS:
- <ce qui a été vérifié> -> <résultat>
DECOUVERTES:
- <libellé> : <résumé>
```
