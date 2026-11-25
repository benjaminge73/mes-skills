"""Tests du banc d'enquête (`enquete.py`) : refus de dépenser sans plafond, relevé sur un mini-corpus factice.

Aucun appel réseau, aucun `claude` : `banc.claude` est remplacé par un faux qui fait échouer le test s'il est appelé.
Le relevé tourne sur un dépôt git jetable, créé dans le temporaire de pytest ; il ne touche jamais aux vrais clones.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import banc  # noqa: E402
import enquete  # noqa: E402

PLAN_1 = "41" + "a" * 30  # un identifiant de page de 32 caractères, comme dans le corpus
PLAN_2 = "42" + "b" * 30


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def test_refuse_de_depenser_sans_plafond_positif(monkeypatch, capsys):
    """Sans plafond, ou avec un plafond nul ou négatif, rien ne part : `claude` n'est jamais appelé."""
    def appel_interdit(*args, **kwargs):
        raise AssertionError("claude appelé alors que le plafond manque")
    monkeypatch.setattr(banc, "claude", appel_interdit)

    assert enquete.main(["actuel"]) == 2
    assert enquete.main(["actuel", "0"]) == 2
    assert enquete.main(["actuel", "-3"]) == 2
    assert enquete.main(["juge:actuel"]) == 2
    assert "plafond" in capsys.readouterr().err


def test_releve_ne_compte_que_les_decouvertes_du_journal_une_fois_chacune(tmp_path):
    """Sur un mini-corpus : une découverte hors journal, un doublon, une « pas trouvable » et un plan sans base
    ne comptent pas ; une découverte citant un fichier que le relevé ne porte pas compte comme manquée."""
    src = tmp_path / "jouet"
    git("init", "-q", str(src), cwd=tmp_path)
    (src / "cron").mkdir()
    (src / "docs").mkdir()
    (src / "cron" / "veille.md").write_text("cron de veille\n")
    (src / "docs" / "guide.md").write_text("Le fichier veille.md, cron de veille.\n")
    git("add", "-A", cwd=src)
    git("commit", "-q", "-m", "depart", cwd=src)
    rev = git("rev-parse", "HEAD", cwd=src)

    depots = tmp_path / "depots"
    depots.mkdir()
    git("clone", "-q", "--mirror", str(src), str(depots / "jouet.git"), cwd=tmp_path)

    corpus = tmp_path / "corpus"
    (corpus / "pages").mkdir(parents=True)
    tableau = ("## Exécution\n\n| Étape | Fichiers |\n| --- | --- |\n| 1 | `cron/veille.md` |\n\n")
    (corpus / "pages" / f"{PLAN_1}.md").write_text(
        "Titre du plan\n\n" + tableau
        + "- découverte — trouvable au plan — `guide.md` hors journal, ne compte pas.\n\n"
        + "## Journal d'exécution\n\n"
        + "- découverte — trouvable au plan — `guide.md` décrit l'ancien comportement de la veille.\n"
        + "- découverte — trouvable au plan — `zzz.py` attend une valeur que le plan ne fixe pas.\n"
        + "- découverte — trouvable au plan — `guide.md` décrit l'ancien comportement de la veille.\n"
        + "- découverte — pas trouvable — `guide.md` : à ignorer.\n")
    (corpus / "pages" / f"{PLAN_2}.md").write_text(
        "Plan sans base\n\n## Journal d'exécution\n\n"
        + "- découverte — trouvable au plan — `guide.md` : ce plan n'a pas de base, il ne compte pas.\n")
    (corpus / "bases.json").write_text(
        '{"%s": {"repo": "jouet", "mb": "%s", "base": "%s"}}' % (PLAN_1, rev, rev))

    r = enquete.releve(corpus, depots=depots)

    assert r["n"] == 2, r                       # guide.md (une fois, doublon écarté) et zzz.py
    assert r["trouves"] == 1, r                 # guide.md est dans le relevé ; zzz.py n'y est pas
    assert r["rappel"] == 50.0, r
    assert r["plans_sans_base"] == 1, r
