#!/usr/bin/env bash
# Lance `claude plugin eval` avec les options communes du banc d'évals.
#
# Usage : evals/outillage/lancer.sh <dossier-du-plugin> <fichier-json-de-sortie> [options claude...]
#
# Les options supplémentaires sont passées telles quelles à `claude plugin eval`
# (attention : --tag et --allow-tools acceptent plusieurs valeurs, une option
# supplémentaire doit donc commencer par « -- »).
#
# Mode :
#   - sur un runner GitHub (GITHUB_ACTIONS=true) : Bash accordé, tous les cas ;
#   - sinon (poste local / VPS) : pas de Bash (il ne tourne pas dans le bac à
#     sable ici), seulement les cas marqués `tags: [lecture]`.
#
# Environnement (optionnel) :
#   EVALS_MODELE         modèle des cas (défaut : claude-opus-5-5)
#   EVALS_MAX_COUT_USD   plafond de coût, passé à --max-cost-usd
#   TMPDIR               dossier des traces (--keep-temp) ; s'il est absent, un
#                        dossier mktemp -d est créé et son chemin affiché
#
# --threshold 0 : c'est scripts/evals_ab.py qui juge, pas le seuil de l'outil.
# Code de sortie : celui de `claude plugin eval` (2 = résultat partiel).
# Jamais de `set -x` et aucune variable d'environnement affichée : en CI, le jeton
# (CLAUDE_CODE_OAUTH_TOKEN) vit dans l'environnement.
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage : $0 <dossier-du-plugin> <fichier-json-de-sortie> [options claude plugin eval...]" >&2
  exit 64
fi

plugin=$1
sortie=$2
shift 2

mkdir -p "$(dirname -- "$sortie")"

if [ -z "${TMPDIR:-}" ]; then
  TMPDIR=$(mktemp -d)
  echo "TMPDIR des traces : $TMPDIR" >&2
else
  mkdir -p "$TMPDIR"
fi
export TMPDIR

if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  mode=(--allow-tools Bash Write Edit)
else
  mode=(--allow-tools Write Edit --tag lecture)
fi

options=(
  --json "$sortie"
  --no-publish
  --keep-temp
  --ablation none
  --trust-plugin
  --scaffold
  --threshold 0
  --model "${EVALS_MODELE:-claude-opus-5-5}"
)
if [ -n "${EVALS_MAX_COUT_USD:-}" ]; then
  options+=(--max-cost-usd "$EVALS_MAX_COUT_USD")
fi

exec claude plugin eval "$plugin" "${options[@]}" "${mode[@]}" "$@"
