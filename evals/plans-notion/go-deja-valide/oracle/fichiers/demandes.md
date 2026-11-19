python3 ~/.hermes/scripts/demander_a_hal.py geste --plan plan.md \
  --demande "Relancer ./scripts/rattrapage.sh dans tmux (étape 14 du plan)" \
  --pourquoi "Geste long, à lancer dans tmux : la session ne peut pas le tenir" \
  --valide "Q3 cochée : plafond 20 $, estimation 12 $" --plafond 20
