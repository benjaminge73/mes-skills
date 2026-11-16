---
type: regex
target: {source: file, path: plan.md}
pattern: '^### [^\n]*tat final[^\n]*\n(?:(?!^##? )[\s\S])*30 jours'
flags: im
match: not_contains
---
