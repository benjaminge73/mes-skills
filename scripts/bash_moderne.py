"""Un bash >= 4, pour jouer les pas de `ci.yml` qui utilisent `mapfile`.

Le runner GitHub a bash 5 ; le `/bin/bash` de macOS est resté en 3.2, qui n'a pas
`mapfile` (« command not found », code 127). Un test qui rejoue un pas du workflow
doit donc lancer un bash récent, ou se déclarer non jouable sur ce poste, au lieu
d'échouer pour une raison qui n'est pas dans le code testé.
"""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path


def _majeure(chemin: str) -> int:
    r = subprocess.run([chemin, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True)
    return int(r.stdout.strip() or 0) if r.returncode == 0 else 0


def trouver() -> str | None:
    """Le premier bash de version majeure >= 4 : le PATH, puis Homebrew, puis /bin/bash."""
    candidats = [shutil.which("bash"), "/opt/homebrew/bin/bash", "/usr/local/bin/bash", "/bin/bash"]
    for c in candidats:
        if c and Path(c).exists() and _majeure(c) >= 4:
            return c
    return None


BASH4 = trouver()

# Sur un poste sans bash >= 4 (macOS nu), le test est sauté avec sa raison : `brew install bash`.
sauter_sans_bash4 = unittest.skipUnless(
    BASH4, "bash >= 4 requis (mapfile, comme sur le runner) : `brew install bash`")
