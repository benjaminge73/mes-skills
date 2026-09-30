#!/usr/bin/env bash
# État de départ d'un dépôt : l'inventaire de ses garde-fous, puis la répétition
# à blanc de sa suite. Rend un bloc Markdown court, à recopier sous l'intertitre
# « État de départ » du chapitre « Contraintes techniques vérifiées » d'un plan.
#
# Pourquoi un script : ce qui se calcule se scripte. Les garde-fous (hooks,
# CI, protections de branche) se sont fait redécouvrir en cours d'exécution, plan
# après plan, parce que la liste à suivre à la main dépendait de la mémoire de
# celui qui l'appliquait. Le script, lui, n'oublie pas une famille.
#
# Usage : etat-de-depart.sh [--sans-repetition] [<dépôt>]        (défaut : .)
#
#   --sans-repetition   ne joue pas la suite : ne fait que la nommer. Sans
#                       cette option, la suite se joue dans un clone jetable
#                       de HEAD, jamais dans le dépôt inspecté.
#
# Variables :
#   ETAT_DE_DEPART_SANS_GH   non vide : ne pas appeler `gh` (rulesets « non
#                            vérifié »). Sert aux tests, qui ne touchent pas le
#                            réseau.
#
# Lecture seule sur le dépôt inspecté : rien n'y est écrit, rien n'y est
# installé. Le clone où la suite se joue vit dans un dossier temporaire supprimé
# en sortie. Une suite rouge ne fait pas échouer le script : elle se rapporte.
#
# Codes de sortie : 0 bloc rendu, 2 usage ou dépôt introuvable.
set -euo pipefail

sans_repetition=""
depot=""
for arg in "$@"; do
  case "$arg" in
    --sans-repetition) sans_repetition=1 ;;
    -h|--help) sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "option inconnue : $arg" >&2; exit 2 ;;
    *) depot="$arg" ;;
  esac
done
depot="${depot:-.}"
[ -d "$depot" ] || { echo "dépôt introuvable : $depot" >&2; exit 2; }
depot="$(cd "$depot" && pwd)"

est_git=""
git -C "$depot" rev-parse --git-dir >/dev/null 2>&1 && est_git=1
racine="$depot"
[ -n "$est_git" ] && racine="$(git -C "$depot" rev-parse --show-toplevel)"

# Colle les lignes lues sur l'entrée standard, séparées par « , ».
joindre() { paste -sd, - | sed 's/,/, /g'; }
# Rend « aucun » quand la valeur est vide.
ou_aucun() { if [ -n "$1" ]; then printf '%s' "$1"; else printf 'aucun'; fi; }

echo "### État de départ — garde-fous de $(basename "$racine")"
echo

# --- Workflows CI : ce qu'ils refusent se lit dans leurs jobs, on nomme les fichiers.
wf=""
if [ -d "$racine/.github/workflows" ]; then
  wf="$(find "$racine/.github/workflows" -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) -printf '%f\n' | sort | joindre)"
fi
echo "- Workflows CI : $(ou_aucun "$wf")"

# --- core.hooksPath : la valeur, et les hooks qu'elle désigne.
hookspath=""
[ -n "$est_git" ] && hookspath="$(git -C "$racine" config --get core.hooksPath 2>/dev/null || true)"
if [ -n "$hookspath" ]; then
  dossier="$hookspath"
  case "$dossier" in /*) ;; *) dossier="$racine/$dossier" ;; esac
  actifs=""
  if [ -d "$dossier" ]; then
    # Seuls les exécutables s'appliquent : git ignore un hook sans droit d'exécution.
    actifs="$(find "$dossier" -maxdepth 1 -type f -perm /111 ! -name '*.sample' -printf '%f\n' | sort | joindre)"
  fi
  echo "- core.hooksPath : $hookspath — hooks : $(ou_aucun "$actifs")"
else
  echo "- core.hooksPath : aucun"
fi

# --- .git/hooks hors *.sample : un exemple n'a jamais refusé un commit. Et quand
# core.hooksPath est défini, git n'ouvre plus .git/hooks : ce qui s'y trouve est inactif.
git_hooks=""
if [ -n "$est_git" ]; then
  commun="$(git -C "$racine" rev-parse --git-common-dir)"
  case "$commun" in /*) ;; *) commun="$racine/$commun" ;; esac
  if [ -d "$commun/hooks" ]; then
    git_hooks="$(find "$commun/hooks" -maxdepth 1 -type f ! -name '*.sample' -printf '%f\n' | sort | joindre)"
  fi
fi
if [ -n "$hookspath" ] && [ -n "$git_hooks" ]; then
  echo "- Hooks git : $git_hooks (.git/hooks, hors *.sample) — inactifs : core.hooksPath est défini, git ignore .git/hooks"
elif [ -n "$hookspath" ]; then
  echo "- Hooks git : aucun (core.hooksPath est défini : git ignore .git/hooks)"
else
  echo "- Hooks git : $(ou_aucun "$git_hooks")$([ -n "$git_hooks" ] && echo " (.git/hooks, hors *.sample)")"
fi

# --- pre-commit : les `id` des hooks sont ce qu'il refuse.
precommit=""
if [ -f "$racine/.pre-commit-config.yaml" ]; then
  ids="$(sed -n 's/^[[:space:]-]*id:[[:space:]]*\([^[:space:]#]*\).*/\1/p' "$racine/.pre-commit-config.yaml" | joindre)"
  precommit=".pre-commit-config.yaml — id : $(ou_aucun "$ids")"
fi
echo "- pre-commit : $(ou_aucun "$precommit")"

# --- husky : un fichier par hook Git, hors dossier interne `_`.
husky=""
if [ -d "$racine/.husky" ]; then
  husky="$(find "$racine/.husky" -maxdepth 1 -type f ! -name 'husky.sh' ! -name '.*' -printf '%f\n' | sort | joindre)"
  husky=".husky/ — hooks : $(ou_aucun "$husky")"
fi
echo "- husky : $(ou_aucun "$husky")"

# --- lefthook : les hooks Git déclarés en tête de fichier.
lefthook=""
for f in lefthook.yml lefthook.yaml .lefthook.yml .lefthook.yaml lefthook-local.yml; do
  if [ -f "$racine/$f" ]; then
    hooks="$(grep -hoE '^(pre|post|commit|prepare|applypatch)[a-z-]*:' "$racine/$f" | tr -d ':' | sort -u | joindre || true)"
    lefthook="${lefthook:+$lefthook ; }$f — hooks : $(ou_aucun "$hooks")"
  fi
done
echo "- lefthook : $(ou_aucun "$lefthook")"

# --- Hooks Claude Code : une clé `hooks` dans un settings.json ; on nomme les événements.
evenements() {
  grep -oE '"(PreToolUse|PostToolUse|UserPromptSubmit|Stop|SubagentStop|SessionStart|SessionEnd|Notification|PreCompact)"' "$1" 2>/dev/null \
    | tr -d '"' | sort -u | joindre || true
}
hooks_claude() {
  local trouve="" ev
  for f in "$@"; do
    if [ -f "$f" ] && grep -q '"hooks"' "$f"; then
      ev="$(evenements "$f")"
      trouve="${trouve:+$trouve ; }${ev:-événements non lus} ($f)"
    fi
  done
  printf '%s' "$trouve"
}
cd "$racine"
echo "- Hooks Claude Code (dépôt) : $(ou_aucun "$(hooks_claude .claude/settings.json .claude/settings.local.json)")"
echo "- Hooks Claude Code (~/.claude/settings.json) : $(ou_aucun "$(hooks_claude "${HOME:-/nonexistent}/.claude/settings.json")")"

# --- Rulesets et protection de branche : seulement si gh est là et le remote sur GitHub.
protection=""
raison=""
slug=""
if [ -n "${ETAT_DE_DEPART_SANS_GH:-}" ]; then
  raison="gh neutralisé (ETAT_DE_DEPART_SANS_GH)"
elif ! command -v gh >/dev/null 2>&1; then
  raison="gh absent"
elif [ -z "$est_git" ]; then
  raison="pas un dépôt git"
else
  url="$(git remote get-url origin 2>/dev/null || true)"
  slug="$(printf '%s' "$url" | sed -n 's#^.*github\.com[:/]\([^/]*/[^/]*\)$#\1#p' | sed 's/\.git$//')"
  [ -n "$slug" ] || raison="pas de remote GitHub"
fi
if [ -n "$raison" ]; then
  echo "- Rulesets et protection de branche : non vérifié : $raison"
else
  branche="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
  branche="${branche:-main}"
  # Un ruleset se nomme, puis se lit par son id : la liste ne dit pas ce qu'il refuse.
  rs=""
  if ids="$(gh api "repos/$slug/rulesets" --jq '.[].id' 2>/dev/null)"; then
    for id in $ids; do
      detail="$(gh api "repos/$slug/rulesets/$id" --jq '.name + " (" + .enforcement + ") refuse : " + ((.rules // []) | map(.type) | join("+"))' 2>/dev/null || true)"
      rs="${rs:+$rs ; }${detail:-ruleset $id (illisible)}"
    done
  fi
  # `gh api` écrit le corps de l'erreur sur la sortie standard : on ne lit que si le code est 0.
  if pr="$(gh api "repos/$slug/branches/$branche/protection" --jq '(.required_status_checks.contexts // []) | join("+")' 2>/dev/null)"; then
    pr="${pr:-active, sans contrôle requis nommé}"
  else
    pr=""
  fi
  echo "- Rulesets et protection de branche : rulesets : $(ou_aucun "$rs") ; protection de $branche : ${pr:-aucune lisible (absente, ou droits insuffisants)}"
fi

echo
echo "### État de départ — répétition à blanc"
echo

# --- La commande de suite : nommée seulement si elle se devine sans ambiguïté.
candidats=()
suite_unique=""
if [ -f scripts/ci_locale.sh ]; then
  # Le dépôt a désigné lui-même sa liste de contrôles : elle prime sur toute devinette.
  suite_unique="scripts/ci_locale.sh"
else
  if [ -f package.json ] && grep -qE '"test"[[:space:]]*:' package.json; then candidats+=("npm test"); fi
  if [ -f pytest.ini ] \
     || { [ -f pyproject.toml ] && grep -q '^\[tool\.pytest' pyproject.toml; } \
     || { [ -f tox.ini ] && grep -q '^\[pytest\]' tox.ini; } \
     || { [ -f setup.cfg ] && grep -q '^\[tool:pytest\]' setup.cfg; }; then candidats+=("pytest"); fi
  if [ -f Makefile ] && grep -q '^test:' Makefile; then candidats+=("make test"); fi
  if [ -f Cargo.toml ]; then candidats+=("cargo test"); fi
  if [ -f go.mod ]; then candidats+=("go test ./..."); fi
  if [ "${#candidats[@]}" -eq 1 ]; then suite_unique="${candidats[0]}"; fi
fi

if [ -n "$suite_unique" ]; then
  echo "- Suite du dépôt : $suite_unique"
elif [ "${#candidats[@]}" -gt 1 ]; then
  echo "- Suite du dépôt : à préciser (plusieurs candidats : $(printf '%s\n' "${candidats[@]}" | joindre))"
else
  echo "- Suite du dépôt : à préciser (aucune commande devinable)"
fi

# --- La jouer, dans un clone jetable de HEAD : le dépôt inspecté n'est jamais touché.
# Un clone plutôt qu'un simple `git archive` : beaucoup de suites lisent l'historique
# ou une référence de base (`origin/main`), qu'une copie sans `.git` ne porterait pas.
if [ -n "$sans_repetition" ]; then
  echo "- Répétition jouée : non (--sans-repetition)"
elif [ -z "$suite_unique" ]; then
  echo "- Répétition jouée : non (pas de commande de suite à jouer)"
elif [ -z "$est_git" ] || ! tete="$(git rev-parse --verify -q HEAD)"; then
  echo "- Répétition jouée : non (pas de commit HEAD à copier)"
else
  copie="$(mktemp -d)"
  trap 'rm -rf "$copie"' EXIT
  # --no-hardlinks : le dossier temporaire est souvent sur un autre disque que le dépôt.
  if ! git clone -q --local --no-hardlinks --no-checkout "$racine" "$copie/depot" 2>"$copie/erreur" \
     || ! git -C "$copie/depot" checkout -q --detach "$tete" 2>>"$copie/erreur"; then
    echo "- Répétition jouée : non (clone de HEAD impossible : $(head -n 1 "$copie/erreur"))"
    exit 0
  fi
  debut="$(date +%s)"
  set +e
  ( cd "$copie/depot" && timeout 900 bash -c "$suite_unique" ) >"$copie/sortie" 2>&1
  code=$?
  set -e
  echo "- Répétition jouée : $suite_unique → code $code en $(( $(date +%s) - debut )) s (clone de HEAD ${tete:0:7} : ni fichiers ignorés ni non suivis)"
  echo
  echo '```'
  tail -n 8 "$copie/sortie"
  echo '```'
fi
