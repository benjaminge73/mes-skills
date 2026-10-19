---
type: regex
target: {source: file, path: plan.md}
pattern: '^## [^\n]*La suite[^\n]*\n(?:(?!^## )[\s\S])*(SQLite[^\n]*plan (à|a) part|plan (à|a) part[^\n]*SQLite)'
flags: im
---
