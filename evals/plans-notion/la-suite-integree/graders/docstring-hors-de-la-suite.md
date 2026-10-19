---
type: regex
target: {source: file, path: plan.md}
pattern: '^## [^\n]*La suite[^\n]*\n(?:(?!^## )[\s\S])*docstring'
flags: im
match: not_contains
---
