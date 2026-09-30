---
type: regex
target: {source: file, path: plan.md}
pattern: '^#{1,4}[ \t]*(\S+[ \t]+)?Questions ouvertes[^\n]*\n(?:(?!#{1,2}[ \t])[^\n]*\n)*?(?!#{1,2}[ \t])[^\n]*(\?|\[[ xX]\])'
flags: im
match: not_contains
---
