---
type: regex
target: {source: file, path: plan.md}
pattern: '^### [^\n]*tat final[^\n]*\n(?:(?!^##? )[\s\S])*(?:(?:propriétaire|Benjamin|déclencheur|attend)[^\n]*30 jours|30 jours[^\n]*(?:propriétaire|Benjamin|déclencheur|attend))'
flags: im
---
