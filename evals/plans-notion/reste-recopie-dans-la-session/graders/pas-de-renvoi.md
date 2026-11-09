---
type: regex
target: {source: file, path: message.md}
pattern: '(voir|cf\.?|dans|reportez-vous)[^\n]{0,40}(tat final|points ouverts|page du plan)'
flags: i
match: not_contains
---
