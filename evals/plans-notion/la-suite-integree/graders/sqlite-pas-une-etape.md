---
type: regex
target: {source: file, path: plan.md}
pattern: '^### [^\n]*tape[^\n]*SQLite'
flags: im
match: not_contains
---
