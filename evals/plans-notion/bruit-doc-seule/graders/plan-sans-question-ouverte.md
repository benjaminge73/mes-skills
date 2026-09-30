---
type: regex
target: {source: file, path: plan.md}
pattern: '^#{1,4}[ \t]*(\S+[ \t]+)?Questions ouvertes'
flags: im
match: not_contains
---
