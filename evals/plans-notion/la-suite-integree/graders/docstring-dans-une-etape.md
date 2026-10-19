---
type: regex
target: {source: file, path: plan.md}
pattern: '^### [^\n]*tape[^\n]*\n(?:(?!^## )[\s\S])*docstring'
flags: im
---
