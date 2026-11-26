#!/usr/bin/env bash
# Dépôt de départ du cas declenchement-negatif-executer : un fichier à lire, aucun plan.
# Le prompt ne nomme ni plan ni skill : executer-plan-notion ne doit pas se charger.
# N'écrit que dans le répertoire courant.
set -euo pipefail
printf 'bonjour le monde\n' > hello.txt
