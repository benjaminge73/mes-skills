#!/usr/bin/env python3
"""Hook PreToolUse Bash : pas d'écriture ``composio`` Notion avec des balises HTML en texte neuf.

``composio execute NOTION_…`` (API markdown publique de Notion) enregistre ``<b>``, ``<code>``
etc. en texte littéral. Le connecteur claude.ai, lui, les interprète : ce garde ne concerne
que la commande ``composio``.

Périmètre :
- une écriture = un slug ``NOTION_…`` dont le verbe n'est pas une lecture (``GET``,
  ``FETCH``, ``SEARCH``, ``QUERY``, ``LIST``, ``RETRIEVE``, ``READ``) ;
- la charge est lue en ligne (``-d '{…}'``), par fichier (``-d @args.json``, chemin résolu
  contre le ``cwd`` du hook et contre un ``cd`` de la commande), ou par stdin construit dans
  la même commande (``echo '{…}' | composio execute … -d -``, ou ``printf``) ;
- les clés ``old_str`` ne sont pas contrôlées : elles doivent pouvoir viser le texte fautif ;
- tout autre texte neuf de la charge est contrôlé par ``balises-html.py`` (``balises_hors_code``) :
  une balise hors backticks et hors bloc de code refuse la commande (code 2, motif sur stderr,
  qui cite ``balises-html.py nettoyer``) ;
- une redirection d'entrée ``-d - < fichier`` se juge comme ``-d @fichier`` ;
- une charge fabriquée dans la même commande refuse aussi (code 2, « appel à part ») : le hook
  ne peut pas la lire avant l'envoi. Trois formes : un fichier créé par ``> fichier`` ou
  ``tee fichier`` ; un fichier nommé par une commande d'avant qui peut l'écrire (``python3
  gen.py --out args.json && composio … -d @args.json``) ; un fichier introuvable au contrôle
  alors qu'une commande d'avant peut le produire (``python3 gen.py && composio … -d @args.json``),
  et un stdin produit par autre chose qu'``echo`` ou ``printf`` (un ``python3 gen.py`` branché
  en tuyau sur ``composio … -d -``). Il faut construire la charge dans un appel à part ;
- un chemin se compare une fois résolu (``./args.json``, ``$PWD/args.json``, l'option collée
  ``-oargs.json`` désignent le même fichier) ;
- un segment d'avant de simple lecture (``cat``, ``head``, ``ls``, ``test``, ``wc``, ``grep``…)
  qui nomme le fichier ne l'exempte pas : le contenu du fichier est contrôlé comme les autres.

Limites : un stdin construit par heredoc (``<<``) passe sans contrôle ; un ``sed -i`` qui nomme
le fichier le rend illisible, donc il passe (une retouche qui ajoute une balise passe aussi :
décision D1, voulue pour ne pas refuser la correction d'une charge déjà sale) ; un fichier
introuvable sans commande d'avant qui le produise passe ; un programme qui ne nomme pas le
fichier et le réécrit (``python3 gen.py && composio … -d @args.json``, ``args.json`` déjà là)
passe : le hook ne voit pas ce qu'il écrit, et le contenu lu est l'ancien.
En cas d'erreur du hook ou de doute : code 0, un mot sur stderr. Entrée sans ``composio`` : code 0 tout de suite.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shlex
import sys
from pathlib import Path

SEPARATEURS = ("&&", "||", ";", "|", "&")
LECTURES = ("GET", "FETCH", "SEARCH", "QUERY", "LIST", "RETRIEVE", "READ")
SCRIPT_BALISES = Path(__file__).resolve().parent.parent / "skills" / "_partage" / "scripts" / "balises-html.py"


def _est_une_ecriture(slug: str) -> bool:
    if not slug.startswith("NOTION_"):
        return False
    verbe = slug[len("NOTION_"):].split("_")[0]
    return verbe not in LECTURES


def _charger_balises():
    spec = importlib.util.spec_from_file_location("balises_html", SCRIPT_BALISES)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _textes_neufs(valeur, cle=None):
    """Chaque chaîne de la charge, sauf les ``old_str`` (ce qu'on vise, pas ce qu'on écrit)."""
    if isinstance(valeur, dict):
        for k, v in valeur.items():
            if k != "old_str":
                yield from _textes_neufs(v, k)
    elif isinstance(valeur, list):
        for v in valeur:
            yield from _textes_neufs(v, cle)
    elif isinstance(valeur, str):
        yield valeur


def _chemin_absolu(texte: str, repertoire: Path) -> Path:
    """Le fichier désigné par ``texte`` depuis ``repertoire`` : ``~``, ``$PWD`` et relatif résolus."""
    brut = texte.replace("${PWD}", str(repertoire)).replace("$PWD", str(repertoire))
    chemin = Path(os.path.expanduser(brut))
    if not chemin.is_absolute():
        chemin = repertoire / chemin
    return chemin.resolve()


def _designe(texte: str, cible: Path, repertoire: Path) -> bool:
    """Vrai si ``texte``, lu comme chemin depuis ``repertoire``, désigne le fichier ``cible`` (résolu)."""
    try:
        return _chemin_absolu(texte, repertoire) == cible
    except (OSError, RuntimeError, ValueError):
        return False


def _cree_dans_la_commande(mots: list[str], cible: Path, repertoire: Path) -> bool:
    """Vrai si la commande écrit le fichier ``cible`` (redirection ou ``tee``), chemins comparés résolus."""
    for k, mot in enumerate(mots):
        if mot in (">", ">>") and k + 1 < len(mots) and _designe(mots[k + 1], cible, repertoire):
            return True
        if mot.startswith(">") and _designe(mot.lstrip(">"), cible, repertoire):
            return True
        if mot == "tee" and any(_designe(m, cible, repertoire) for m in mots[k + 1:]):
            return True
    return False


LECTURES_COMMANDE = ("cat", "head", "tail", "ls", "test", "[", "wc", "grep", "stat", "file",
                     "diff", "cmp", "md5sum", "sha256sum", "jq", "less", "more")
NON_ECRIVAINS = ("cd", "echo", "printf", "true", ":")


def _segments_avant(mots: list[str], i: int) -> list[list[str]]:
    """Les segments de commande complets qui précèdent le ``composio`` en ``mots[i]``."""
    segments, courant = [], []
    for mot in mots[:i]:
        if mot in SEPARATEURS:
            segments.append(courant)
            courant = []
        else:
            courant.append(mot)
    return segments


def _programme(segment: list[str]) -> str:
    """Le nom du programme d'un segment (``rtk`` ignoré), ou chaîne vide."""
    mots = list(segment[1:] if segment[:1] == ["rtk"] else segment)
    return os.path.basename(mots[0]) if mots else ""


def _candidats(mot: str):
    """Les lectures possibles d'un mot comme chemin : le mot, sa redirection, sa valeur après ``=``, son option ``-oX`` collée."""
    yield mot
    yield mot.lstrip("<>")
    if "=" in mot:
        yield mot.split("=", 1)[1]
    if mot.startswith("-") and len(mot) > 2 and mot[1].isalpha():
        yield mot[2:]


def _nomme(segment: list[str], cible: Path, repertoire: Path) -> bool:
    """Le segment désigne le fichier ``cible``, sous une de ses formes (chemin résolu)."""
    return any(_designe(c, cible, repertoire) for m in segment for c in _candidats(m))


def _ecrit(segment: list[str]) -> bool:
    """Le segment peut produire un fichier : tout programme sauf lecture ou non-écrivain."""
    prog = _programme(segment)
    return bool(prog) and prog not in LECTURES_COMMANDE and prog not in NON_ECRIVAINS


def _sed_en_place(segment: list[str]) -> bool:
    return _programme(segment) == "sed" and any(m == "-i" or m.startswith("-i") for m in segment)


def _charge_stdin(mots: list[str], i: int):
    """La charge passée par ``| composio … -d -`` : le dict si c'est un ``echo`` ou un ``printf`` lisible ;
    ``("fabrique", raison)`` si le stdin est produit par autre chose ; None si illisible."""
    if i < 1 or mots[i - 1] != "|":
        return None
    producteur = []
    for mot in reversed(mots[: i - 1]):
        if mot in SEPARATEURS:
            break
        producteur.insert(0, mot)
    if not producteur:
        return None
    if producteur[0] == "echo":
        arguments = producteur[1:]
        while arguments and arguments[0] in ("-n", "-e", "-E"):
            arguments = arguments[1:]
        texte = " ".join(arguments)
    elif producteur[0] == "printf" and len(producteur) == 2:
        texte = producteur[1]
    else:
        return ("fabrique", f"stdin produit par `{_programme(producteur)}` dans la même commande, "
                            "qui n'est pas un `echo '…'` ou un `printf '…'` simple")
    try:
        return json.loads(texte)
    except ValueError:
        return None


def _charge(mots: list[str], i: int, repertoire: Path):
    """``("charge", valeur)``, ``("cree", chemin)``, ``("fabrique", raison)`` ou ``("illisible", None)``
    pour le ``composio`` en ``mots[i]``."""
    valeur = _charge_brute(mots, i, repertoire)
    if isinstance(valeur, tuple):
        return valeur
    if valeur is None:
        return ("illisible", None)
    return ("charge", valeur)


def _charge_brute(mots: list[str], i: int, repertoire: Path):
    """La charge JSON ; ``("cree", chemin)`` ou ``("fabrique", raison)`` si la charge est fabriquée dans la commande ; None si illisible."""
    fin = next((k for k in range(i + 3, len(mots)) if mots[k] in SEPARATEURS), len(mots))
    segment = mots[i + 3:fin]
    brut = None
    for k, mot in enumerate(segment):
        if mot in ("-d", "--data"):
            brut = segment[k + 1] if k + 1 < len(segment) else None
            break
        if mot.startswith("--data="):
            brut = mot[len("--data="):]
            break
        if mot.startswith("-d@"):
            brut = mot[len("-d"):]
            break
    if brut is None:
        return None
    if brut == "-":
        redirige = _redirection_stdin(segment)
        if redirige is not None:
            return _charge_fichier(mots, i, repertoire, redirige)
        return _charge_stdin(mots, i)
    if brut.startswith("@"):
        return _charge_fichier(mots, i, repertoire, brut[1:])
    try:
        return json.loads(brut)
    except ValueError:
        return None


def _redirection_stdin(segment: list[str]):
    """Le fichier de ``composio … -d - < fichier`` (``<`` séparé ou collé), ou None. Heredoc (``<<``) exclu."""
    for k, mot in enumerate(segment):
        if mot == "<" and k + 1 < len(segment):
            return segment[k + 1]
        if mot.startswith("<") and not mot.startswith("<<") and len(mot) > 1:
            return mot[1:]
    return None


def _charge_fichier(mots: list[str], i: int, repertoire: Path, chemin: str):
    """La charge lue dans ``chemin`` (``-d @chemin`` ou ``< chemin``), ou ce que la commande en fait."""
    cible = _chemin_absolu(chemin, repertoire)
    if _cree_dans_la_commande(mots, cible, repertoire):
        return ("cree", chemin)
    precedents = _segments_avant(mots, i)
    nommes = [s for s in precedents if _nomme(s, cible, repertoire)]
    if any(_ecrit(s) and not _sed_en_place(s) for s in nommes):
        return ("fabrique", f"`{chemin}` est écrit par une commande d'avant")
    if any(_sed_en_place(s) for s in nommes):
        # sed -i nommé avant composio : il modifie le fichier sur place avant l'appel. Le contenu
        # lu ici serait l'ancien : illisible au contrôle, on laisse passer (décision D1).
        return None
    # Un segment de simple lecture qui le nomme (cat, head…) ne l'exempte pas : on lit le contenu.
    try:
        return json.loads(cible.read_text(encoding="utf-8"))
    except OSError:
        if not cible.exists() and any(_ecrit(s) for s in precedents):
            return ("fabrique", f"`{chemin}` est introuvable au contrôle, et une commande d'avant "
                                "peut le produire")
        return None
    except ValueError:
        return None


def _appels(commande: str, cwd: str):
    """Chaque ``composio execute`` de la commande : (mots, position, dossier courant à cet instant)."""
    mots = shlex.split(commande)
    repertoire = Path(cwd)
    appels = []
    for i, mot in enumerate(mots):
        if mot == "cd" and (i == 0 or mots[i - 1] in SEPARATEURS) and i + 1 < len(mots):
            repertoire = (repertoire / os.path.expanduser(mots[i + 1])).resolve()
        if (os.path.basename(mot) == "composio" and i + 2 < len(mots)
                and mots[i + 1] == "execute"):
            appels.append((mots, i, repertoire))
    return appels


def _refus_balises(occurrences) -> str:
    listees = ", ".join(sorted({b for _, b in occurrences})[:3])
    return ("Refusé : texte Notion écrit avec des balises HTML en texte neuf "
            f"({listees}). `composio` les enregistre en texte littéral. Convertir d'abord : "
            "`balises-html.py nettoyer <fichier>` rend le markdown (gras `**`, code en backticks), "
            "ou écrire le markdown directement ; puis rejouer la commande.")


def _refus_cree(chemin: str) -> str:
    return (f"Refusé : le fichier de charge `{chemin}` est créé dans cette même commande, "
            "donc illisible au contrôle : construis le fichier dans un appel à part, puis écris "
            "dans le suivant avec `composio`. Contrôle-le avant avec `balises-html.py controler "
            "<fichier>` et corrige-le avec `balises-html.py nettoyer <fichier>` si besoin.")


def _refus_fabriquee(raison: str) -> str:
    return (f"Refusé : la charge de `composio` est fabriquée dans cette même commande ({raison}), "
            "donc illisible au contrôle : construis-la dans un appel à part, puis écris-la dans le "
            "suivant avec `composio`. Contrôle-la avant avec `balises-html.py controler <fichier>` "
            "(ou écris-la directement en markdown), puis rejoue la commande.")


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if not isinstance(donnees, dict) or donnees.get("tool_name") != "Bash":
            return 0
        commande = (donnees.get("tool_input") or {}).get("command")
        if not isinstance(commande, str) or "composio" not in commande:
            return 0
        cwd = donnees.get("cwd") or os.getcwd()
        balises = None
        for mots, i, repertoire in _appels(commande, cwd):
            if not _est_une_ecriture(mots[i + 2]):
                continue
            statut, valeur = _charge(mots, i, repertoire)
            if statut == "cree":
                print(_refus_cree(valeur), file=sys.stderr)
                return 2
            if statut == "fabrique":
                print(_refus_fabriquee(valeur), file=sys.stderr)
                return 2
            if statut != "charge":
                continue
            if balises is None:
                balises = _charger_balises()
            occurrences = []
            for texte in _textes_neufs(valeur):
                occurrences.extend(balises.balises_hors_code(texte))
            if occurrences:
                print(_refus_balises(occurrences), file=sys.stderr)
                return 2
        return 0
    except Exception as erreur:
        print(f"refuser_balises_composio : entrée ignorée ({type(erreur).__name__}: {erreur})",
              file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
