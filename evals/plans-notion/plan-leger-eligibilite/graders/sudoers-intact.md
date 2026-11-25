---
type: regex
target: {source: file, path: config/sudoers-sauvegarde}
pattern: 'systemctl'
match: not_contains
---
