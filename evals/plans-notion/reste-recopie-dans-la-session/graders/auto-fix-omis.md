---
type: regex
target: {source: file, path: message.md}
pattern: 'auto-?fix'
flags: i
match: not_contains
---
