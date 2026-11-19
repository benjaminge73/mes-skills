{ cat plan.md; printf '\n## Plans ouverts des mêmes dépôts\nAucun autre plan ouvert sur ce dépôt.\n'; } | python3 ~/.hermes/scripts/demander_a_hal.py relire --plan plan.md --tour 1
