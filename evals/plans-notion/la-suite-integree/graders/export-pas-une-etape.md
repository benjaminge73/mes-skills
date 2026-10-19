---
type: regex
target: {source: file, path: plan.md}
pattern: '^### [^\n]*tape[^\n]*(CSV|export)'
flags: im
match: not_contains
---
