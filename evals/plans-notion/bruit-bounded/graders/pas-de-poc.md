---
type: regex
target: {source: file, path: plan.md}
pattern: '^#{1,4}[^\n]*\bPOC\b'
flags: im
match: not_contains
---
