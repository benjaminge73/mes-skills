---
type: regex
target: {source: file, path: plan.md}
pattern: 'Statut\s*:\s*en revue'
match: not_contains
flags: i
---
Le plan ne passe pas `en revue` : sa page reste `brouillon` tant que l'avis de Hal n'est pas noté. Un `Statut : en revue` écrit dans `plan.md` pendant ce passage est la panne visée : poser `en revue` sans relecture.
