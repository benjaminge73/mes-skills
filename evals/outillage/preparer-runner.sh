#!/usr/bin/env bash
# Prépare un runner GitHub Actions jetable pour jouer `claude plugin eval` avec Bash.
#
# Pourquoi : sur Ubuntu 24.04, AppArmor interdit les espaces de noms utilisateur
# imbriqués (kernel.apparmor_restrict_unprivileged_userns=1). Sans les lever, le bac
# à sable des évals ne peut pas lancer Bash. On ne le fait que sur la VM jetable du
# runner : ce script REFUSE de tourner ailleurs, et ne touche donc jamais le VPS.
#
# Appelé par le job de CI. Aucune image : ≈ 1 min 30 de préparation à chaque passe.
set -euo pipefail

# Version de Claude Code du runner : montée à la main, voir docs/tester-un-skill.md
CLAUDE_CODE_VERSION=2.1.285

# Premier geste, avant tout sudo / apt / sysctl : garde-fou « jamais le VPS ».
if [ "${GITHUB_ACTIONS:-}" != "true" ]; then
  echo "preparer-runner.sh : refus, hors runner GitHub (GITHUB_ACTIONS n'est pas « true »)." >&2
  echo "Ce script lève une restriction AppArmor et n'a de sens que sur la VM jetable d'un runner." >&2
  exit 2
fi

echo "==> Paquets bubblewrap et socat (requis par le bac à sable des évals)"
sudo apt-get install -y bubblewrap socat

echo "==> Levée de la restriction sur les espaces de noms utilisateur (VM jetable)"
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

echo "==> Claude Code ${CLAUDE_CODE_VERSION}"
sudo npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"

echo "==> Sonde : un espace de noms utilisateur imbriqué dans bwrap"
# Un runner qui change ne doit pas produire des zéros silencieux : si la sonde
# échoue, tout le job échoue ici, avec un message qui dit pourquoi.
if bwrap --ro-bind / / --dev /dev --proc /proc --unshare-user \
     -- unshare --user --map-root-user true; then
  echo "OK imbriqué"
else
  echo "ÉCHEC de la sonde : bwrap ne peut pas créer d'espace de noms utilisateur imbriqué." >&2
  echo "Le runner a sans doute changé (image, noyau, AppArmor) : Bash ne tournerait pas dans le bac à sable des évals." >&2
  exit 1
fi

claude --version
