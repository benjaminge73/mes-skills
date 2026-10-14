---
type: regex
target: {source: file, path: plan.md}
pattern: 'Statut\*\*\s*:\s*`?execute`?'
flags: i
match: not_contains
---
