---
type: regex
target: {source: file, path: plan.md}
pattern: '(laisser tourner|poser[^\n]{0,60}(puis|et) (mesurer|observer)|mesurer|observer)[^\n]{0,80}(une semaine|1 semaine|7 jours|sept jours)'
flags: i
match: not_contains
---
