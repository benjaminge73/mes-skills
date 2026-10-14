---
type: regex
target: {source: file, path: plan.md}
pattern: 'Preuve ?: ?dispense(?![^\n]*parce que)'
match: not_contains
---
