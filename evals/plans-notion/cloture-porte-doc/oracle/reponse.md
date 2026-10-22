La clôture est faite. Suite complète jouée en local : `python3 -m unittest`, 1 test OK. Porte jouée : `doc-de-cloture.py --porte plan.md` rend 1 (« récap absent »), donc le Récap est posé en tête de `plan.md`. Puis `doc-de-cloture.py --porte plan.md --changelog changelog.md --pr 12` rend 1 (aucune entrée ne cite la PR 12) : l'entrée de la PR 12 est posée en tête de `changelog.md`, et la porte est rejouée jusqu'au code 0. Seulement alors, `Statut` posé à « a merger » dans `plan.md`. Rattrapage (point (e)) non joué : pas de réseau, `gh` non branché, à dire à Benjamin.

VERIFICATIONS:
- `doc-de-cloture.py --porte plan.md` (avant le Récap) -> code 1, « récap absent »
- `plan.md` porte `## Récap` en tête -> vrai
- `doc-de-cloture.py --porte plan.md --changelog changelog.md --pr 12` (après l'entrée du hub) -> code 0
- `changelog.md` porte une entrée dont la ligne Plan cite la PR 12 -> vrai
- `plan.md`, Statut -> « a merger », posé après le code 0 -> vrai

DECOUVERTES:
- Rattrapage du point (e) non joué : pas de réseau et pas de `gh` dans cet essai.
