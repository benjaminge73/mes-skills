#!/usr/bin/env bash
# Garde « Suis-je la bonne version ? » : le plugin chargé est-il celui qui est installé ?
#
# Pourquoi un script : la garde tenait en deux commandes à recopier, et ce qui se
# calcule se scripte. Un skill ne choisit pas d'où il est chargé (copie synchronisée
# périmée, cas du 2026-09-08) ; il peut seulement le constater.
#
# Usage : verifier-version.sh <racine-du-plugin-chargé>     (= ${CLAUDE_PLUGIN_ROOT})
#
# Code de sortie : 0 à jour ; 1 écart de version ou de chemin ; 2 lecture impossible.
# Variable : INSTALLED_PLUGINS_JSON surcharge ~/.claude/plugins/installed_plugins.json
# (sert aux tests). Sans dépendance : bash et python3 de la bibliothèque standard.
set -u

racine="${1:-}"
if [ -z "$racine" ]; then
  echo "usage : verifier-version.sh <racine-du-plugin-chargé>" >&2
  exit 2
fi
installed="${INSTALLED_PLUGINS_JSON:-$HOME/.claude/plugins/installed_plugins.json}"
manifeste="$racine/.claude-plugin/plugin.json"

if [ ! -f "$installed" ]; then
  echo "illisible : installed_plugins.json introuvable ($installed)" >&2
  exit 2
fi
if [ ! -f "$manifeste" ]; then
  echo "illisible : plugin.json introuvable ($manifeste)" >&2
  exit 2
fi

lecture=$(python3 - "$installed" "$manifeste" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))["plugins"]["plans-notion@atelier"][0]
    charge = json.load(open(sys.argv[2]))["version"]
except (OSError, ValueError, KeyError, IndexError) as e:
    print(f"illisible : {type(e).__name__} {e}", file=sys.stderr)
    sys.exit(2)
print(d["version"], d["installPath"], charge, sep="\t")
PY
) || exit 2

IFS=$'\t' read -r v_installee chemin v_chargee <<<"$lecture"
racine_abs=$(cd "$racine" && pwd -P)
chemin_abs=$(cd "$chemin" 2>/dev/null && pwd -P || printf '%s' "$chemin")

ecart=""
[ "$v_installee" = "$v_chargee" ] || ecart="version chargée $v_chargee, installée $v_installee"
if [ "$racine_abs" != "$chemin_abs" ]; then
  ecart="${ecart:+$ecart ; }chemin chargé $racine_abs, installPath $chemin"
fi

if [ -n "$ecart" ]; then
  echo "écart : $ecart. Lire SKILL.md et _partage/ depuis l'installPath, puis : claude plugin update plans-notion@atelier (redémarrage requis)." >&2
  exit 1
fi
echo "à jour : plans-notion $v_chargee ($racine_abs)"
