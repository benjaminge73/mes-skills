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
#     ni contrôle `gh`, ni jeton machine (le runner n'est pas le VPS) ;
#   - sinon (poste local / VPS) : pas de Bash (il ne tourne pas dans le bac à
#     sable ici), seulement les cas marqués `tags: [lecture]`. Deux gardes
#     précèdent alors `claude plugin eval`, parce que les bancs partagent la
#     limite de débit de l'abonnement (mesuré le 2026-09-30 : un A/B local lancé
#     pendant deux bancs de CI a rendu des résultats inexploitables) :
#       1. refus si un job « Évals » est en cours en CI (`gh run list --workflow
#          ci.yml --status in_progress`, puis les jobs de chaque run) ;
#       2. prise du jeton machine (`etat-machine.py prendre evals-locales`), avec
#          attente puis refus s'il est tenu ; rendu à la sortie du script, même
#          si claude échoue ou est interrompu.
#     Sans réponse de `gh` (absent, hors ligne, non authentifié), le lanceur
#     refuse aussi : sans contrôle, on ne sait pas si un banc tourne.
#
# Environnement (optionnel) :
#   EVALS_MODELE         modèle des cas (défaut : claude-sonnet-5-5)
#   EVALS_EFFORT         effort de réflexion du modèle (défaut : high) ; exporté en
#                        CLAUDE_CODE_EFFORT_LEVEL, la variable que `claude plugin eval`
#                        lit (mesuré : ≈ 350 à 550 jetons de réflexion en low, 4 800 à
#                        7 800 en high). Un effort qui change change la mesure, donc le
#                        bruit : les deux (modèle, effort) sont figés par ci.yml.
#   EVALS_MAX_COUT_USD   plafond de coût, passé à --max-cost-usd
#   EVALS_FORCER         =1 : passe outre le contrôle des bancs de CI (local seulement,
#                        et le dit sur stderr). Ne se pose jamais en CI. Le jeton machine
#                        reste pris : il protège les autres sessions, pas la limite de débit
#   EVALS_PLAN           titre du plan au nom duquel le jeton est pris (défaut :
#                        « évals locales »)
#   EVALS_ATTENDRE       secondes d'attente d'un jeton tenu avant de refuser (défaut :
#                        300, de quoi laisser finir une suite de tests ou une e2e ; une
#                        autre éval locale dure plus et fait donc refuser)
#   TMPDIR               dossier des traces (--keep-temp) ; s'il est absent, un
#                        dossier mktemp -d est créé et son chemin affiché
#
# --threshold 0 : c'est scripts/evals_ab.py qui juge, pas le seuil de l'outil.
# Code de sortie : celui de `claude plugin eval` (2 = résultat partiel) ; en local,
# 75 si un banc tourne en CI ou si le jeton machine est refusé (tenu, machine
# saturée), 69 si `gh` ne répond pas, 64 pour un usage invalide.
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

if [ "${GITHUB_ACTIONS:-}" != "true" ]; then
  # --- Garde 1 : un banc d'évals tourne-t-il en CI ? ---------------------------
  if [ "${EVALS_FORCER:-}" = "1" ]; then
    echo "EVALS_FORCER=1 : contrôle des bancs de CI ignoré — les mesures peuvent être faussées si un banc tourne." >&2
  else
    if ! runs=$(gh run list --workflow ci.yml --status in_progress --limit 30 \
                  --json databaseId --jq '.[].databaseId' 2>&1); then
      echo "refus : impossible de savoir si un banc d'évals tourne en CI (gh absent ou en échec) : $runs" >&2
      echo "        EVALS_FORCER=1 passe outre ce contrôle." >&2
      exit 69
    fi
    for run in $runs; do
      if ! jobs=$(gh run view "$run" --json jobs \
                    --jq '.jobs[] | select(.status == "in_progress") | .name' 2>&1); then
        echo "refus : impossible de lire les jobs du run $run (gh en échec) : $jobs" >&2
        echo "        EVALS_FORCER=1 passe outre ce contrôle." >&2
        exit 69
      fi
      if grep -q '^Évals' <<<"$jobs"; then
        echo "refus : un job « Évals » tourne en CI (run $run). Les bancs partagent la limite de débit de l'abonnement ; relancer à sa fin," >&2
        echo "        ou EVALS_FORCER=1 pour passer outre (mesures faussées)." >&2
        exit 75
      fi
    done
  fi

  # --- Garde 2 : le jeton machine (action lourde) --------------------------------
  # $$ est le PID de ce script : il vit autant que claude, et le trap rend le jeton
  # à la sortie. D'où l'absence d'`exec` plus bas : un exec remplacerait le shell et
  # le trap ne s'exécuterait jamais.
  racine=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
  etat_machine="$racine/plugins/plans-notion/skills/_partage/scripts/etat-machine.py"
  prise=0
  python3 "$etat_machine" prendre evals-locales --plan "${EVALS_PLAN:-évals locales}" \
    --attendre "${EVALS_ATTENDRE:-300}" --pid $$ >&2 || prise=$?
  if [ "$prise" -ne 0 ]; then
    echo "refus : le jeton machine n'est pas accordé (code $prise : 3 = tenu par une autre action, 4 = machine saturée, 2 = usage)." >&2
    exit 75
  fi
  trap 'python3 "$etat_machine" rendre --pid $$ >/dev/null 2>&1 || true' EXIT
fi

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

# Pas d'`exec` : le shell doit survivre à claude pour que le trap rende le jeton.
# Le code de sortie de claude est gardé et rendu tel quel.
code=0
claude plugin eval "$plugin" "${options[@]}" "${mode[@]}" "$@" || code=$?
exit "$code"
