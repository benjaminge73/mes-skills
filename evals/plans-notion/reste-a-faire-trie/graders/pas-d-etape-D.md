---
type: regex
target: {source: file, path: plan.md}
pattern: '^### [^\n]*tape D[2-9]'
flags: im
match: not_contains
---
