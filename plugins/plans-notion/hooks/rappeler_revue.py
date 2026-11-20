#!/usr/bin/env python3
"""Hooks PostToolUse et Stop : une page de plan écrite ne reste pas ``brouillon`` par oubli.

Constat (2026-11-20) : les sessions finissent d'écrire un plan et s'arrêtent, le ``Statut``
resté à ``brouillon``, parce que rien dans leur parcours ne les ramène à cette décision
et que Benjamin ne filtre que sur ``en revue``. Ce hook est le garde de ce trou.

Deux modes, choisis par l'argument de ligne de commande :

- ``noter`` (PostToolUse sur l'outil Notion ou sur ``composio execute NOTION_*``) : relève
  dans une fiche locale de la session les pages de plan qu'elle vient d'écrire sans les
  sortir de ``brouillon`` (création d'une page ``[Plan] …``, ``Statut`` posé à ``brouillon``,
  contenu qui porte le chapitre ``Questions ouvertes``). Un ``Statut`` posé à autre chose
  que ``brouillon`` efface la page de la fiche.
- ``rappeler`` (Stop) : si la fiche porte des pages, retient la fin de tour **une seule
  fois** avec la consigne de décider du statut (``en revue`` si la rédaction est finie, sinon
  dire à Benjamin ce qui manque). La fiche est vidée avant la retenue.

Sans réseau ni modèle. Contrat : sortie vide et code 0 = laisser passer ; sortie
``{"decision": "block", "reason": ...}`` et code 0 = retenir. Une erreur, à n'importe quelle
étape, laisse passer : un garde cassé ne bloque aucune session. Le dossier d'état est
``${XDG_STATE_HOME:-~/.local/state}/plans-notion/plans-a-statuer/``.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

FORME_SESSION = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
OUTILS_NOTION = ("notion-update-page", "notion-create-pages")
PREFIXE_TITRE = "[plan]"
MARQUEUR_CONTENU = "questions ouvertes"
INCONNUE = "page sans identifiant"

CONSIGNE = (
    "Tu as écrit {pages} dans la base Plans Claude et son `Statut` peut encore être `brouillon`. "
    "Décide-le maintenant, avant de t'arrêter : Benjamin ne lit que les plans `en revue`. "
    "Rédaction finie (questions posées avec leur recommandation, preuves et POC dans la page, "
    "`Exécution` écrit, filtre d'enquête passé) → pose `Statut` = `en revue` (sur le VPS, après "
    "l'avis de Hal : `relire`). Sinon → laisse `brouillon` et dis à Benjamin, en une ligne, "
    "ce qui manque. Si le `Statut` a déjà dépassé `brouillon`, ne fais rien. "
    "Règle : `plan-notion/SKILL.md`, « Fin de passe »."
)


def _sans_accent(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if not unicodedata.combining(c))


def _chaines(valeur):
    if isinstance(valeur, str):
        yield valeur
    elif isinstance(valeur, dict):
        for v in valeur.values():
            yield from _chaines(v)
    elif isinstance(valeur, list):
        for v in valeur:
            yield from _chaines(v)


def _dossier() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return Path(base) / "plans-notion" / "plans-a-statuer"


def _charger_revue():
    """``refuser_revue_sans_avis.py``, voisin : ses lecteurs d'appels Notion et composio."""
    chemin = Path(__file__).resolve().parent / "refuser_revue_sans_avis.py"
    spec = importlib.util.spec_from_file_location("refuser_revue_sans_avis", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _charges(donnees: dict, revue) -> list[tuple[object, dict]]:
    """Les (page_id, charge) d'un appel d'écriture Notion, vide pour tout autre appel."""
    outil = donnees.get("tool_name")
    entree = donnees.get("tool_input") or {}
    if not isinstance(entree, dict):
        return []
    if outil == "Bash":
        import shlex
        try:
            mots = shlex.split(entree.get("command") or "")
        except ValueError:
            return []
        trouvees = []
        for i in range(len(mots) - 2):
            if (os.path.basename(mots[i]) == "composio" and mots[i + 1] == "execute"
                    and mots[i + 2].startswith("NOTION_") and "PAGE" in mots[i + 2]):
                charge = revue._charge_composio(mots[i + 3:])
                if isinstance(charge, dict):
                    trouvees.append((charge.get("page_id"), charge))
        return trouvees
    if isinstance(outil, str) and outil.endswith(OUTILS_NOTION):
        pages = [p for p in (entree.get("pages") or []) if isinstance(p, dict)]
        if pages:
            return [(None, p) for p in pages]
        return [(entree.get("page_id"), entree)]
    return []


def _statut(charge: dict):
    """La valeur de ``Statut`` posée par la charge, en minuscules sans accent, ou None."""
    proprietes = charge.get("properties")
    if not isinstance(proprietes, dict) or "Statut" not in proprietes:
        return None
    textes = [_sans_accent(t).strip().lower() for t in _chaines(proprietes["Statut"])]
    textes = [t for t in textes if t]
    return textes[-1] if textes else ""


def _titre(charge: dict) -> str | None:
    for texte in _chaines(charge.get("properties")):
        if texte.strip().lower().startswith(PREFIXE_TITRE):
            return texte.strip()
    return None


def _a_noter(page, charge: dict) -> tuple[str, str | None] | None:
    """(clé, titre) à ajouter à la fiche, ou ``("-" + clé, None)`` à en retirer, ou None."""
    cle = page if isinstance(page, str) and page else None
    statut = _statut(charge)
    titre = _titre(charge)
    if statut is not None and statut != "brouillon":
        return "-" + (cle or INCONNUE), None
    corps = _sans_accent(" ".join(_chaines(charge))).lower()
    est_un_plan = titre is not None or statut == "brouillon" or _sans_accent(MARQUEUR_CONTENU) in corps
    if not est_un_plan:
        return None
    return (cle or titre or INCONNUE, titre)


def _fichier(session: str) -> Path:
    return _dossier() / f"{session}.json"


def _lire(session: str) -> dict:
    try:
        donnees = json.loads(_fichier(session).read_text(encoding="utf-8"))
        return donnees if isinstance(donnees, dict) else {}
    except (OSError, ValueError):
        return {}


def _ecrire(session: str, pages: dict) -> None:
    dossier = _dossier()
    dossier.mkdir(parents=True, exist_ok=True, mode=0o700)
    if pages:
        _fichier(session).write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    else:
        _fichier(session).unlink(missing_ok=True)


def noter(entree: dict) -> None:
    session = entree.get("session_id")
    if not isinstance(session, str) or not FORME_SESSION.match(session):
        return
    if entree.get("tool_name") == "Bash" and "composio" not in str((entree.get("tool_input") or {}).get("command")):
        return  # la plupart des appels Bash : sortie sans rien charger
    pages = _lire(session)
    avant = dict(pages)
    for page, charge in _charges(entree, _charger_revue()):
        action = _a_noter(page, charge)
        if action is None:
            continue
        cle, titre = action
        if cle.startswith("-"):
            pages.pop(cle[1:], None)
            # une page créée n'a pas d'id dans la charge : un Statut posé ailleurs la solde aussi
            for k in [k for k in pages if not re.search(r"[0-9a-f]{32}\Z", k.lower().replace("-", ""))]:
                pages.pop(k)
        else:
            pages[cle] = titre or pages.get(cle) or ""
    if pages != avant:
        _ecrire(session, pages)


def rappeler(entree: dict) -> str | None:
    """La sortie JSON de la retenue, ou None pour laisser passer. Vide la fiche avant de retenir."""
    if entree.get("stop_hook_active"):
        return None
    session = entree.get("session_id")
    if not isinstance(session, str) or not FORME_SESSION.match(session):
        return None
    pages = _lire(session)
    if not pages:
        return None
    _ecrire(session, {})  # écrit avant la retenue : si cela échoue, on ne retient pas
    noms = [titre or ("une page de plan" if cle == INCONNUE else cle) for cle, titre in pages.items()]
    liste = "« " + " », « ".join(noms) + " »" if len(noms) > 1 or noms[0] != "une page de plan" else "une page de plan"
    return json.dumps({"decision": "block", "reason": CONSIGNE.format(pages=liste)}, ensure_ascii=False)


def main(argv: list[str]) -> int:
    try:
        mode = argv[1] if len(argv) > 1 else ""
        entree = json.loads(sys.stdin.read())
        if not isinstance(entree, dict):
            return 0
        if mode == "noter":
            noter(entree)
        elif mode == "rappeler":
            sortie = rappeler(entree)
            if sortie:
                sys.stdout.write(sortie)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
