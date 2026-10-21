---
type: regex
target: {source: file, path: plan.md}
pattern: '^### [^\n]*tape D[0-9]'
flags: im
match: not_contains
---
