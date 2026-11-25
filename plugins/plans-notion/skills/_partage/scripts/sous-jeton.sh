#!/bin/bash
# sous-jeton.sh : joue une commande lourde en tenant le jeton des actions lourdes.
#
# Usage : bash sous-jeton.sh '<commande>'
#
# Le hook jeton_lourd.py (plugin plans-notion) réécrit les suites complètes en
# appel de ce script. Ici, le jeton est pris par ce même shell (``--pid $$``) :
# la commande est jouée par ``eval`` dans ce processus, et le ``trap`` rend le
# jeton à la sortie, même après un échec. Un descendant de ce shell (un
# ``lancer.sh`` ou un geste manuel lancé dedans) voit ce PID comme ancêtre et
# n'a pas à reprendre le jeton (règle de l'ancêtre, etat-machine.py).
#
# Attente : tant que le jeton est tenu (code 3 de ``prendre``), on rejoue par
# paliers de PLANS_NOTION_ATTENTE_PALIER s. Sur une machine saturée (code 4), on
# dort PLANS_NOTION_ATTENTE_SATUREE s et on rejoue. Le plafond
# PLANS_NOTION_ATTENTE_MAX (défaut 300 s) borne l'attente totale : au-delà, sortie
# en code 75, la commande n'est pas jouée, et le message cite le détenteur.
#
# Fail-open : si etat-machine.py rend un autre code (profil invalide, plantage),
# la commande part sans jeton, avec un avertissement sur la sortie d'erreur.
#
# Si PLANS_NOTION_JETON_PID désigne un PID vivant, le jeton est déjà tenu par
# un ancêtre : pas de prise. Compatible bash 3.2 (macOS).

ICI="$(cd "$(dirname "$0")" && pwd)"
ETAT="$ICI/etat-machine.py"
ATTENTE_MAX="${PLANS_NOTION_ATTENTE_MAX:-300}"
PALIER="${PLANS_NOTION_ATTENTE_PALIER:-60}"
SATUREE="${PLANS_NOTION_ATTENTE_SATUREE:-15}"
PLAN="session (jeton automatique)"

if [ $# -lt 1 ]; then
  echo "usage : sous-jeton.sh '<commande>'" >&2
  exit 2
fi
COMMANDE="$1"

# Un ancêtre tient déjà le jeton : on joue la commande sans le reprendre.
if [ -n "${PLANS_NOTION_JETON_PID:-}" ] && kill -0 "$PLANS_NOTION_JETON_PID" 2>/dev/null; then
  eval "$COMMANDE"
  exit $?
fi

ACTION="$(printf '%s' "$COMMANDE" | tr '\n' ' ' | cut -c1-80)"
DEBUT=$SECONDS
PREMIERE_ATTENTE=1
JETON_PRIS=0

while :; do
  RESTE=$(( ATTENTE_MAX - (SECONDS - DEBUT) ))
  if [ "$RESTE" -le 0 ]; then
    echo "sous-jeton : jeton toujours tenu après ${ATTENTE_MAX} s — la commande n'est pas jouée." >&2
    echo "Détenteur(s) :" >&2
    python3 "$ETAT" qui 2>/dev/null | sed 's/^/  /' >&2
    echo "Relevé : $(python3 "$ETAT" releve 2>/dev/null | head -1)" >&2
    echo "Conseil : relancer la commande en arrière-plan (run_in_background), la prise y attendra sans bloquer l'outil." >&2
    exit 75
  fi

  ATTENTE=$PALIER
  if [ "$RESTE" -lt "$ATTENTE" ]; then ATTENTE=$RESTE; fi

  # stdout de prendre écarté (« accordé » ne doit pas polluer la sortie de la commande) ;
  # sa sortie d'erreur est gardée pour les codes qui s'en servent.
  ERREUR="$(python3 "$ETAT" prendre "$ACTION" --plan "$PLAN" --attendre "$ATTENTE" --pid $$ 2>&1 1>/dev/null)"
  CODE=$?

  case $CODE in
    0)
      JETON_PRIS=1
      break
      ;;
    3)
      if [ "$PREMIERE_ATTENTE" = 1 ]; then
        echo "sous-jeton : jeton tenu, attente (plafond ${ATTENTE_MAX} s) :" >&2
        echo "$ERREUR" >&2
        PREMIERE_ATTENTE=0
      fi
      ;;
    4)
      PAUSE=$SATUREE
      if [ "$RESTE" -lt "$PAUSE" ]; then PAUSE=$RESTE; fi
      sleep "$PAUSE"
      ;;
    *)
      echo "sous-jeton : jeton non pris (etat-machine.py a rendu le code $CODE) — la commande part sans jeton." >&2
      [ -n "$ERREUR" ] && echo "$ERREUR" >&2
      break
      ;;
  esac
done

if [ "$JETON_PRIS" = 1 ]; then
  echo "sous-jeton : jeton pris (PID $$) pour : $ACTION" >&2
  export PLANS_NOTION_JETON_PID=$$
  trap 'python3 "$ETAT" rendre --pid $$ >/dev/null 2>&1' EXIT
fi

eval "$COMMANDE"
exit $?
