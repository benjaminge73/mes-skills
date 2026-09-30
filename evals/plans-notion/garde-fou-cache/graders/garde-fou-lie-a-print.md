---
type: regex
target: {source: file, path: plan.md}
pattern: '(pre-commit|pas-de-print)[\s\S]{0,400}\bprint\b|\bprint\b[\s\S]{0,400}(pre-commit|pas-de-print)'
flags: i
---
