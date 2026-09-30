#!/usr/bin/env bash
# La seule liste des contrôles de ce dépôt : ce que la CI joue dans ses jobs
# `garde` et `validation`, dans l'ordre. La CI APPELLE ce script au lieu de
# recopier ses commandes ; CLAUDE.md et README.md disent « lancer
# scripts/ci_locale.sh » au lieu de les énumérer. Ajouter un contrôle, c'est
# l'ajouter ICI, une seule fois.
#
# Le job `evals` (payant, joué sur le runner GitHub seulement) n'est pas dans ce
# script : voir docs/tester-un-skill.md, « Où tourne quoi ».
#
# Usage : scripts/ci_locale.sh [garde|validation|tout]      (défaut : tout)
#
# Variables :
#   BASE_REF             base de la PR pour les contrôles qui en dépendent (garde
#                        de version, leçon a son cas, veille, cliquet de
#                        limites.json). Défaut : origin/main.
#   CI_LOCALE_SANS_BASE  non vide : sauter ces contrôles (poussée sur main, où il
#                        n'y a pas de PR à comparer).
#   CLAUDE_BIN           la CLI Claude Code pour `claude plugin validate`
#                        (défaut : claude). Ce script ne l'installe pas : la CI
#                        le fait dans son job `validation`, en local elle est
#                        déjà là.
#
# Codes de sortie : 0 tout est vert, 1 au moins un contrôle rouge (tous sont
# joués, pour tout voir d'un coup), 2 usage ou base illisible, 3 outil absent.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

section="${1:-tout}"
BASE_REF="${BASE_REF:-origin/main}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
SANS_BASE="${CI_LOCALE_SANS_BASE:-}"

case "$section" in
  garde|validation|tout) ;;
  *) echo "usage : scripts/ci_locale.sh [garde|validation|tout]" >&2; exit 2 ;;
esac

faire_garde=0;      [ "$section" = validation ] || faire_garde=1
faire_validation=0; [ "$section" = garde ]      || faire_validation=1

# --- Pré-vol : un outil ou une base manquants se disent avant tout contrôle ----

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 est introuvable : les contrôles du dépôt sont en Python (bibliothèque standard)." >&2
  exit 3
fi

if [ "$faire_garde" = 1 ] && [ -z "$SANS_BASE" ]; then
  if ! git rev-parse --verify --quiet "${BASE_REF}^{commit}" >/dev/null; then
    echo "La base « $BASE_REF » est introuvable dans ce clone : les contrôles qui comparent la PR à sa base n'ont rien à lire." >&2
    echo "Faire « git fetch origin main », ou passer une autre base (BASE_REF=<réf>)." >&2
    exit 2
  fi
fi

if [ "$faire_validation" = 1 ] && ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
  echo "La CLI « $CLAUDE_BIN » est introuvable : « claude plugin validate » ne peut pas tourner." >&2
  echo "Ce script ne l'installe pas (jamais en global à ta place). Pour l'avoir : npm install -g @anthropic-ai/claude-code" >&2
  echo "(la CI l'installe dans son job « validation »)." >&2
  exit 3
fi

# --- Exécution : tous les contrôles sont joués, les échecs sont listés ---------

echecs=()

etape() {
  local titre=$1; shift
  if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::group::$titre"; else echo; echo "== $titre"; fi
  "$@"
  local code=$?
  if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::endgroup::"; fi
  if [ "$code" -ne 0 ]; then
    echo "-- ROUGE ($code) : $titre"
    echecs+=("$titre")
  fi
}

garde_de_version() {
  local fichiers code
  fichiers=$(mktemp) || return 1
  # `--no-renames` : une ligne renommée sort en trois champs, que le garde
  # ignore. Forcer la paire suppression/ajout garantit qu'un fichier de plugin
  # déplacé compte comme un fichier touché.
  if ! git diff --no-renames --name-status "${BASE_REF}...HEAD" > "$fichiers"; then
    rm -f "$fichiers"; return 1
  fi
  if [ ! -s "$fichiers" ] && [ -z "${GITHUB_ACTIONS:-}" ]; then
    echo "Aucun fichier changé par rapport à $BASE_REF : rien à contrôler (en CI, une PR vide est refusée)."
    rm -f "$fichiers"; return 0
  fi
  python3 scripts/plugin_version_guard.py --changed-files "$fichiers" --base-ref "$BASE_REF"
  code=$?
  rm -f "$fichiers"
  return $code
}

if [ "$faire_garde" = 1 ]; then
  etape "Cohérence de la marketplace" python3 scripts/check_marketplace.py
  if [ -z "$SANS_BASE" ]; then
    etape "Garde de version des plugins" garde_de_version
    etape "Une leçon a son cas" python3 scripts/check_lecon_a_son_cas.py --base "$BASE_REF"
    etape "Veille avant la mise à jour d'un skill" python3 scripts/check_veille.py --base "$BASE_REF"
    etape "Règles de forme des skills et registre des garde-fous" python3 scripts/check_skills.py --base "$BASE_REF"
  else
    echo
    echo "(sans base : garde de version, leçon a son cas, veille et cliquet sautés)"
    etape "Règles de forme des skills et registre des garde-fous" python3 scripts/check_skills.py --sans-base
  fi
fi

if [ "$faire_validation" = 1 ]; then
  valider_plugins() {
    "$CLAUDE_BIN" plugin validate . || return 1
    local d rc=0
    for d in plugins/*/; do
      "$CLAUDE_BIN" plugin validate "$d" || rc=1
    done
    return $rc
  }
  etape "Validation des plugins par la CLI" valider_plugins
  etape "Tests des scripts de garde" python3 -m unittest discover -s scripts -p 'test_*.py'
  etape "Renvois entre fichiers" python3 scripts/check_references.py
fi

echo
echo "Le job « evals » (payant) n'est pas joué ici : il tourne sur le runner GitHub."
if [ "${#echecs[@]}" -gt 0 ]; then
  echo "ROUGE — ${#echecs[@]} contrôle(s) en échec :"
  printf '  - %s\n' "${echecs[@]}"
  exit 1
fi
echo "VERT — tous les contrôles de « $section » passent."
