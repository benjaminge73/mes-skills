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
#   EVALS_MODELE         modèle des cas (défaut : claude-sonnet-5-5)
#   EVALS_EFFORT         effort de réflexion du modèle (défaut : high) ; exporté en
#                        CLAUDE_CODE_EFFORT_LEVEL, la variable que `claude plugin eval`
#                        lit (mesuré : ≈ 350 à 550 jetons de réflexion en low, 4 800 à
#                        7 800 en high). Un effort qui change change la mesure, donc le
#                        bruit : les deux (modèle, effort) sont figés par ci.yml.
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

# L'effort vient d'EVALS_EFFORT et de rien d'autre : un CLAUDE_CODE_EFFORT_LEVEL
# déjà présent dans l'environnement (session interactive) est écrasé.
export CLAUDE_CODE_EFFORT_LEVEL="${EVALS_EFFORT:-high}"

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
  --model "${EVALS_MODELE:-claude-sonnet-5-5}"
)
if [ -n "${EVALS_MAX_COUT_USD:-}" ]; then
  options+=(--max-cost-usd "$EVALS_MAX_COUT_USD")
fi

exec claude plugin eval "$plugin" "${options[@]}" "${mode[@]}" "$@"
