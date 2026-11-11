---
type: regex
target: {source: file, path: message.md}
pattern: '(à vérifier|à confirmer|reste à confirmer|sera vérifié|on verra)[^\n]{0,60}(ce soir|22 ?h|prochain)'
flags: i
match: not_contains
---
