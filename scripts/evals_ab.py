#!/usr/bin/env python3
"""Compare deux versions d'un plugin sur les mêmes cas d'évaluation.

``claude plugin eval`` (Claude Code 2.1.285) sait rejouer des cas contre un
plugin, et comparer « avec le plugin » à « sans le plugin ». Il ne sait pas
comparer **deux versions** d'un même plugin : c'est le rôle de ce script. Il
répond à une question précise, « la version de tête est-elle pire que la
version de base, au-delà du bruit ? », sans dépendance (bibliothèque standard
seulement : la CI n'a pas PyYAML garanti).

Ce que fait un passage ``ab`` :

1. extrait ``plugins/<nom>`` à deux références git (``--base``, ``--tete``)
   dans deux copies temporaires (``git archive``, le dépôt n'est jamais touché) ;
2. y assemble les cas de ``evals/<nom>/`` du dépôt et, avec ``--prive``, ceux
   d'un banc privé, sous ``<copie>/evals/`` — un cas ne vaut pour
   ``claude plugin eval`` que dans la racine du plugin, mais tout fichier sous
   ``plugins/`` exigerait une montée de version : on assemble donc à la volée ;
3. **pré-vol**, sans modèle et sans coût : chaque juge gratuit (``regex``,
   ``file_exists``) est appliqué à l'oracle du cas (il doit passer) et à un
   état vide (il doit échouer, sinon il ne distingue rien) ; un cas qui n'y
   satisfait pas est refusé et **rien n'est joué** ;
4. appelle le lanceur (``evals/outillage/lancer.sh``) sur chaque copie ;
5. compare cas par cas, avec un intervalle de bruit, et refuse un rapport
   ``partial: true`` (un rapport tronqué par un plafond de coût ferait passer
   des cas non joués pour des reculs).

Le mode ``aa`` joue la **même** référence (``--tete``) deux fois : l'écart
entre les deux jeux n'est que du bruit, et il est écrit dans un fichier
(``--sortie-bruit``) que ``--bruit`` réutilise ensuite dans un ``ab``.

Convention d'oracle
-------------------
Chaque cas a, à côté de ``case.yaml`` (ou ``prompt.md`` + ``graders/*.md``),
un dossier ``oracle/`` écrit à la main : l'état final idéal.

- ``oracle/reponse.md`` : la réponse finale idéale. Un juge ``regex`` dont la
  cible est ``last_message`` (le défaut) s'y applique.
- ``oracle/fichiers/<chemin>`` : les fichiers que le passage idéal a créés,
  au chemin relatif où le cas les attend. Un juge ``regex`` avec
  ``target: {source: file, path: …}`` et un juge ``file_exists`` s'y appliquent.
- L'état vide (témoin nul) : réponse vide, aucun fichier.

L'oracle n'est **jamais copié** dans le plugin assemblé : l'agent évalué a
accès aux fichiers de la copie, il ne doit pas lire la bonne réponse.

Un juge ``llm``/``baseline``/``tool_used``… ou un ``regex`` sur une autre cible
(``trace``, ``files``, ``mock_calls``) n'est pas vérifiable sans modèle : il est
signalé « non vérifié », le cas n'est pas refusé. Un juge négatif
(``match: not_contains``, ``exists: false``) passe sur le vide par nature : on
exige seulement que l'oracle le passe.

Lecture des cas
---------------
Un petit lecteur du sous-ensemble YAML utilisé par les cas (mappings, listes,
scalaires, ``[a, b]``, ``{a: b}``, blocs ``|``/``>``, commentaires) plutôt
qu'une convention parallèle : les auteurs de cas écrivent le format natif.
Tout ce qui sort du sous-ensemble (ancres, étiquettes, documents multiples)
est **refusé** plutôt que mal lu.

Bruit
-----
- Sans mesure : demi-largeur d'intervalle à 95 % de l'*écart* entre base et
  tête, approchée par ``racine(2)/racine(n*R)`` pour ``n`` cas et ``R``
  passages (global) et ``racine(2)/racine(R)`` (par cas, avant la correction
  des comparaisons multiples ci-dessous). Pour un taux de
  réussite, ``1/racine(n*R)`` est la demi-largeur d'*une* moyenne (au plus,
  quand le taux vaut 1/2). Or on compare deux moyennes, base et tête, qui
  portent chacune leur propre bruit : les variances s'additionnent, l'écart
  est donc ``racine(2)`` fois plus incertain qu'une moyenne seule. Prendre
  ``1/racine(n*R)`` ferait échouer la CI sur du pur hasard (10 cas x 3
  passages : seuil 0,18 au lieu de 0,26). ``--bruit`` remplace cette
  estimation par une mesure.
- Mesuré en A/A : ``rms_ecarts_cas`` = racine de la moyenne des carrés des
  écarts par cas entre les deux jeux identiques (la vraie différence est nulle
  par construction, donc pas de moyenne retranchée). Demi-largeur d'intervalle
  à 95 % : par cas ``1,96 x rms`` ; globale ``1,96 x rms / racine(n)``. Ce n'est
  **pas** un écart-type : c'est bien une demi-largeur d'intervalle, dans le
  fichier de bruit sous ``demi_largeur_ic95_*`` (et le ``rms`` qui permet de
  la recalculer pour un autre nombre de cas). Ces deux demi-largeurs sont des
  *mesures* : le fichier les garde telles quelles, ce ne sont pas les seuils
  que ``comparer`` applique par cas (voir ci-dessous).
- Seuil par cas et comparaisons multiples : tester chaque cas à 95 % revient,
  sur ``n`` cas, à une probabilité ``1 - 0,95^n`` qu'au moins un dépasse par
  pur hasard (56 % pour 16 cas ; A/A réel du 2026-09-30, 9 cas x 3 passages,
  deux jeux identiques : ``rms`` 0,0385, seuil non corrigé ± 7,5 pts, et un cas
  a pourtant bougé de -10 pts). Le seuil **par cas** est donc corrigé par
  Bonferroni (bilatéral) : ``z_n x rms`` avec ``z_n = inv_cdf(1 - 0,05/(2n))``
  (2,77 pour 9 cas, 2,95 pour 16 ; 1,96 pour un seul cas, donc sans changement).
  Sans fichier de bruit, l'estimation par cas ``racine(2)/racine(R)`` est
  élargie du même facteur ``z_n / 1,96``. Le seuil **global** ne change pas :
  c'est une seule comparaison.

Verdict : code de sortie 1 si la moyenne recule de plus que le bruit global,
**ou** si un cas seul recule de plus que le seuil par cas corrigé (un skill
modifié n'affecte souvent qu'un ou deux cas, et la moyenne le diluerait).

Codes de sortie
---------------
``0`` pas de recul au-delà du bruit (ou mode ``aa``, ou ``--previol-seul``
réussi) ; ``1`` recul ; ``2`` erreur d'usage (argparse) ; ``3`` refus (pré-vol,
rapport partiel, lanceur en échec, donnée illisible).

Le lanceur
----------
``evals/outillage/lancer.sh <dossier-du-plugin> <json-de-sortie> [options]``
écrit le rapport ``--json`` et rend le code de ``claude plugin eval`` : ``0``,
``1`` (un cas sous son seuil : c'est le sujet même de la comparaison, pas une
panne), ``2`` (rapport partiel : refusé). Les options après ``--`` lui sont
transmises telles quelles (``-- --runs 3 --model …``). Les tests le remplacent
par un faux via ``--lanceur``.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from statistics import NormalDist

DEPOT = Path(__file__).resolve().parents[1]
Z95 = 1.96
EPSILON = 1e-9


def z_bonferroni(n: int, alpha: float = 0.05) -> float:
    """Quantile bilatéral corrigé pour ``n`` comparaisons (Bonferroni) :
    ``inv_cdf(1 - alpha / (2 n))``. Pour ``n = 1`` : 1,96."""
    return NormalDist().inv_cdf(1 - alpha / (2 * max(n, 1)))


class ErreurRefus(Exception):
    """Une raison de ne pas jouer ou de ne pas comparer (code de sortie 3)."""


class ErreurYaml(ValueError):
    """Syntaxe YAML absente du sous-ensemble lu par ce module."""


# ==========================================================================
# Lecteur du sous-ensemble YAML
# ==========================================================================
def _indentation(ligne: str) -> int:
    return len(ligne) - len(ligne.lstrip(" "))


def _sans_commentaire(texte: str) -> str:
    """Retire un commentaire ``# …`` hors guillemets, précédé d'un espace."""
    guillemet = ""
    for i, c in enumerate(texte):
        if guillemet:
            if c == "\\" and guillemet == '"':
                continue
            if c == guillemet:
                guillemet = ""
        elif c in "'\"":
            guillemet = c
        elif c == "#" and (i == 0 or texte[i - 1] in " \t"):
            return texte[:i].rstrip()
    return texte


def _scalaire(brut: str):
    s = brut.strip()
    if not s:
        return None
    if s[0] == "'":
        if len(s) < 2 or s[-1] != "'":
            raise ErreurYaml(f"guillemet simple non fermé : {brut!r}")
        return s[1:-1].replace("''", "'")
    if s[0] == '"':
        try:
            return json.loads(s)
        except ValueError as e:
            raise ErreurYaml(f"chaîne entre guillemets illisible : {brut!r}") from e
    if s[0] in "&*!%@`":
        raise ErreurYaml(
            f"syntaxe YAML hors du sous-ensemble lu ici : {brut!r} "
            "(ancre, alias, étiquette ?) — mettre la valeur entre guillemets"
        )
    if s in ("~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?", s):
        return float(s)
    return s


def _cle_valeur(texte: str):
    """(clé, reste) si la ligne est ``clé: valeur``, sinon None."""
    if not texte or texte[0] in "[{":
        return None
    if texte[0] in "'\"":
        q = texte[0]
        i = 1
        while i < len(texte):
            if texte[i] == "\\" and q == '"':
                i += 2
                continue
            if texte[i] == q:
                if q == "'" and texte[i + 1 : i + 2] == "'":
                    i += 2
                    continue
                break
            i += 1
        else:
            return None
        apres = texte[i + 1 :]
        if apres.startswith(":") and (len(apres) == 1 or apres[1] == " "):
            return _scalaire(texte[: i + 1]), apres[1:]
        return None
    for i, c in enumerate(texte):
        if c == ":" and (i + 1 == len(texte) or texte[i + 1] == " "):
            return texte[:i].strip(), texte[i + 1 :]
    return None


def _flow(s: str, p: int):
    """Valeur en ligne (``[..]``, ``{..}``, scalaire) à partir de ``s[p]``."""

    def sauter(q):
        while q < len(s) and s[q] in " \t":
            q += 1
        return q

    def jeton(q, arrets):
        q = sauter(q)
        debut = q
        if q < len(s) and s[q] in "'\"":
            guillemet = s[q]
            q += 1
            while q < len(s):
                if s[q] == "\\" and guillemet == '"':
                    q += 2
                    continue
                if s[q] == guillemet:
                    if guillemet == "'" and s[q + 1 : q + 2] == "'":
                        q += 2
                        continue
                    break
                q += 1
            q += 1
            return s[debut:q], q
        while q < len(s) and s[q] not in arrets:
            q += 1
        return s[debut:q], q

    try:
        p = sauter(p)
        if s[p] == "[":
            p += 1
            items = []
            while True:
                p = sauter(p)
                if s[p] == "]":
                    return items, p + 1
                valeur, p = _flow(s, p)
                items.append(valeur)
                p = sauter(p)
                if s[p] == ",":
                    p += 1
                elif s[p] != "]":
                    raise ErreurYaml(f"liste en ligne mal formée : {s!r}")
        if s[p] == "{":
            p += 1
            res = {}
            while True:
                p = sauter(p)
                if s[p] == "}":
                    return res, p + 1
                cle_brute, p = jeton(p, ":")
                p = sauter(p)
                if s[p] != ":":
                    raise ErreurYaml(f"mapping en ligne mal formé : {s!r}")
                valeur, p = _flow(s, p + 1)
                res[_scalaire(cle_brute)] = valeur
                p = sauter(p)
                if s[p] == ",":
                    p += 1
                elif s[p] != "}":
                    raise ErreurYaml(f"mapping en ligne mal formé : {s!r}")
        brut, p = jeton(p, ",]}")
        return _scalaire(brut), p
    except IndexError as e:
        raise ErreurYaml(f"valeur en ligne non fermée : {s!r}") from e


def _valeur_en_ligne(reste: str):
    if reste[0] in "[{":
        valeur, fin = _flow(reste, 0)
        if reste[fin:].strip():
            raise ErreurYaml(f"texte après la valeur en ligne : {reste!r}")
        return valeur
    return _scalaire(reste)


class _Lecteur:
    def __init__(self, texte: str):
        self.l = texte.replace("\r\n", "\n").split("\n")
        self.i = 0

    def _sauter(self):
        while self.i < len(self.l) and (
            not self.l[self.i].strip() or self.l[self.i].lstrip().startswith("#")
        ):
            self.i += 1

    def _fin(self) -> bool:
        self._sauter()
        return self.i >= len(self.l)

    def document(self):
        if self._fin():
            return None
        valeur = self.bloc(0)
        if not self._fin():
            raise ErreurYaml(f"ligne {self.i + 1} : contenu inattendu")
        return valeur

    def bloc(self, indent_min: int):
        if self._fin():
            return None
        ligne = self.l[self.i]
        ind = _indentation(ligne)
        if ind < indent_min:
            return None
        contenu = ligne.strip()
        if contenu == "-" or contenu.startswith("- "):
            return self.liste(ind)
        if _cle_valeur(_sans_commentaire(contenu)) is not None:
            return self.mapping(ind)
        self.i += 1
        return _valeur_en_ligne(_sans_commentaire(contenu))

    def mapping(self, ind: int):
        res = {}
        while not self._fin():
            ligne = self.l[self.i]
            cur = _indentation(ligne)
            if cur < ind:
                break
            if cur > ind:
                raise ErreurYaml(f"ligne {self.i + 1} : indentation inattendue")
            contenu = ligne.strip()
            if contenu == "-" or contenu.startswith("- "):
                break
            kv = _cle_valeur(_sans_commentaire(contenu))
            if kv is None:
                raise ErreurYaml(f"ligne {self.i + 1} : « clé: valeur » attendu")
            cle, reste = kv
            self.i += 1
            reste = _sans_commentaire(reste).strip()
            if reste == "":
                if self._fin():
                    valeur = None
                else:
                    suivante = self.l[self.i]
                    if _indentation(suivante) > ind:
                        valeur = self.bloc(ind + 1)
                    elif _indentation(suivante) == ind and suivante.strip().startswith("- "):
                        valeur = self.liste(ind)
                    else:
                        valeur = None
            elif reste[0] in "|>":
                valeur = self.litteral(reste, ind)
            else:
                valeur = _valeur_en_ligne(reste)
            if cle in res:
                raise ErreurYaml(f"clé dupliquée : {cle!r}")
            res[cle] = valeur
        return res

    def liste(self, ind: int):
        res = []
        while not self._fin():
            ligne = self.l[self.i]
            contenu = ligne.strip()
            cur = _indentation(ligne)
            if cur < ind or not (contenu == "-" or contenu.startswith("- ")):
                break
            if cur > ind:
                raise ErreurYaml(f"ligne {self.i + 1} : indentation inattendue")
            apres = contenu[1:]
            espaces = len(apres) - len(apres.lstrip(" "))
            reste = apres.strip()
            if reste == "":
                self.i += 1
                if not self._fin() and _indentation(self.l[self.i]) > ind:
                    res.append(self.bloc(ind + 1))
                else:
                    res.append(None)
            elif _cle_valeur(_sans_commentaire(reste)) is not None:
                # « - clé: v » : la ligne devient la première du mapping fils.
                fils = ind + 1 + espaces
                self.l[self.i] = " " * fils + reste
                res.append(self.mapping(fils))
            else:
                self.i += 1
                res.append(_valeur_en_ligne(_sans_commentaire(reste)))
        return res

    def litteral(self, entete: str, ind_parent: int):
        style = entete[0]
        chomp = "-" if "-" in entete[1:] else "+" if "+" in entete[1:] else ""
        brutes = []
        while self.i < len(self.l):
            ligne = self.l[self.i]
            if not ligne.strip():
                brutes.append("")
                self.i += 1
                continue
            if _indentation(ligne) <= ind_parent:
                break
            brutes.append(ligne)
            self.i += 1
        pleines = [_indentation(x) for x in brutes if x]
        decalage = min(pleines) if pleines else 0
        lignes = [x[decalage:] if x else "" for x in brutes]
        if chomp != "+":
            while lignes and lignes[-1] == "":
                lignes.pop()
        if style == "|":
            texte = "\n".join(lignes)
        else:
            morceaux, courant = [], []
            for x in lignes:
                if x == "":
                    morceaux.append(" ".join(courant))
                    courant = []
                else:
                    courant.append(x)
            morceaux.append(" ".join(courant))
            texte = "\n".join(morceaux)
        if lignes and chomp != "-":
            texte += "\n"
        return texte


def lire_yaml(texte: str):
    """Lit le sous-ensemble YAML des cas ; ``ErreurYaml`` au-delà."""
    return _Lecteur(texte).document()


def separer_frontmatter(texte: str):
    """(métadonnées, corps) d'un fichier ``---\\n…\\n---\\ncorps``."""
    lignes = texte.replace("\r\n", "\n").split("\n")
    if not lignes or lignes[0].strip() != "---":
        return {}, texte
    for fin in range(1, len(lignes)):
        if lignes[fin].strip() == "---":
            meta = lire_yaml("\n".join(lignes[1:fin])) or {}
            if not isinstance(meta, dict):
                raise ErreurYaml("frontmatter : un mapping est attendu")
            return meta, "\n".join(lignes[fin + 1 :])
    raise ErreurYaml("frontmatter non fermé (deuxième « --- » manquant)")


# ==========================================================================
# Cas, oracle, pré-vol
# ==========================================================================
def est_un_cas(dossier: Path) -> bool:
    return dossier.is_dir() and (
        (dossier / "case.yaml").is_file() or (dossier / "prompt.md").is_file()
    )


def decouvrir_cas(dossier_evals: Path) -> list[Path]:
    return sorted(d for d in dossier_evals.iterdir() if est_un_cas(d))


def charger_juges(dossier: Path) -> list[dict]:
    juges: list[dict] = []
    fichier = dossier / "case.yaml"
    if fichier.is_file():
        données = lire_yaml(fichier.read_text("utf-8")) or {}
        if not isinstance(données, dict):
            raise ErreurYaml(f"{fichier} : un mapping est attendu")
        for i, j in enumerate(données.get("graders") or []):
            if not isinstance(j, dict):
                raise ErreurYaml(f"{fichier} : juge n°{i + 1} illisible")
            j = dict(j)
            j.setdefault("name", f"juge-{i + 1}")
            juges.append(j)
    dossier_juges = dossier / "graders"
    if dossier_juges.is_dir():
        for f in sorted(dossier_juges.glob("*.md")):
            meta, corps = separer_frontmatter(f.read_text("utf-8"))
            meta.setdefault("name", f.stem)
            meta["_corps"] = corps
            juges.append(meta)
    return juges


def _glob_vers_regex(motif: str) -> re.Pattern:
    motif = motif[2:] if motif.startswith("./") else motif
    out, i = [], 0
    while i < len(motif):
        c = motif[i]
        if motif.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if motif.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _regex_python(pattern: str, flags: str) -> re.Pattern:
    """Les motifs de ``claude plugin eval`` sont des regex JavaScript."""
    motif = re.sub(r"\(\?<([A-Za-z_]\w*)>", r"(?P<\1>", pattern)
    options = 0
    for f in str(flags or ""):
        options |= {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL}.get(f, 0)
    return re.compile(motif, options)


def est_negatif(juge: dict) -> bool:
    if juge.get("type") == "file_exists":
        return juge.get("exists", True) is False
    if juge.get("type") == "regex":
        match = str(juge.get("match", "contains"))
        return match == "not_contains" or match == "count:0"
    return False


def evaluer_juge(juge: dict, reponse: str, fichiers: dict[str, str]):
    """True/False, ou None si ce juge ne se vérifie pas sans modèle."""
    type_ = juge.get("type")
    if type_ == "file_exists":
        motif = _glob_vers_regex(str(juge.get("path", "")))
        present = any(motif.match(chemin) for chemin in fichiers)
        return present == (juge.get("exists", True) is not False)
    if type_ != "regex":
        return None
    cible = juge.get("target", "last_message")
    if cible == "last_message":
        textes = [reponse]
    elif isinstance(cible, dict) and cible.get("source") == "file":
        motif = _glob_vers_regex(str(cible.get("path", "")))
        textes = [t for chemin, t in fichiers.items() if motif.match(chemin)]
    else:
        return None
    regex = _regex_python(str(juge.get("pattern", "")), juge.get("flags", ""))
    match = str(juge.get("match", "contains"))
    if match.startswith("count:"):
        n = int(match.split(":", 1)[1])
        return any(len(regex.findall(t)) == n for t in textes) if textes else n == 0
    trouve = any(regex.search(t) for t in textes)
    return (not trouve) if match == "not_contains" else trouve


def lire_oracle(dossier_cas: Path) -> tuple[str, dict[str, str]] | None:
    oracle = dossier_cas / "oracle"
    if not oracle.is_dir():
        return None
    reponse_fichier = oracle / "reponse.md"
    reponse = reponse_fichier.read_text("utf-8").strip() if reponse_fichier.is_file() else ""
    fichiers = {}
    racine = oracle / "fichiers"
    if racine.is_dir():
        for f in sorted(racine.rglob("*")):
            if f.is_file():
                fichiers[f.relative_to(racine).as_posix()] = f.read_text(
                    "utf-8", errors="replace"
                )
    return reponse, fichiers


@dataclass
class Verdict:
    nom: str
    erreurs: list[str] = field(default_factory=list)
    non_verifies: list[str] = field(default_factory=list)


def previol_cas(dossier_cas: Path) -> Verdict:
    """Applique les juges gratuits à l'oracle (doit passer) et au vide (doit échouer)."""
    v = Verdict(dossier_cas.name)
    try:
        juges = charger_juges(dossier_cas)
    except (ErreurYaml, OSError) as e:
        v.erreurs.append(f"cas {v.nom} : lecture impossible ({e})")
        return v
    if not juges:
        v.erreurs.append(f"cas {v.nom} : aucun juge")
        return v
    oracle = lire_oracle(dossier_cas)
    if oracle is None:
        v.erreurs.append(f"cas {v.nom} : pas de dossier oracle/ (l'état final idéal, écrit à la main)")
        return v
    reponse, fichiers = oracle
    for juge in juges:
        nom, type_ = juge.get("name", "?"), juge.get("type", "?")
        try:
            sur_oracle = evaluer_juge(juge, reponse, fichiers)
            sur_vide = evaluer_juge(juge, "", {})
        except (re.error, ValueError) as e:
            v.erreurs.append(f"cas {v.nom} : juge « {nom} » illisible ({e})")
            continue
        if sur_oracle is None:
            v.non_verifies.append(
                f"cas {v.nom} : juge « {nom} » ({type_}) non vérifié sans modèle"
            )
            continue
        if not sur_oracle:
            v.erreurs.append(
                f"cas {v.nom} : l'oracle échoue au juge « {nom} » ({type_}) — "
                "un état idéal qui ne passe pas son propre juge ne prouve rien"
            )
        if sur_vide and not est_negatif(juge):
            v.erreurs.append(
                f"cas {v.nom} : le juge « {nom} » ({type_}) passe sur un état vide "
                "— il ne distingue pas un bon passage d'un passage nul"
            )
    return v


def previol(dossiers_cas: list[Path]) -> list[Verdict]:
    return [previol_cas(d) for d in dossiers_cas]


# ==========================================================================
# Extraction git et assemblage
# ==========================================================================
def extraire(depot: Path, ref: str, plugin: str, dest: Path) -> None:
    """``plugins/<plugin>`` tel qu'à ``ref``, écrit dans ``dest`` (le dépôt n'est pas touché)."""
    prefixe = f"plugins/{plugin}"
    r = subprocess.run(
        ["git", "-C", str(depot), "archive", "--format=tar", ref, prefixe],
        capture_output=True,
    )
    if r.returncode != 0:
        raise ErreurRefus(
            f"git archive {ref} {prefixe} a échoué : "
            f"{r.stderr.decode('utf-8', 'replace').strip()}"
        )
    dest.mkdir(parents=True, exist_ok=True)
    racine = dest.resolve()
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tar:
        for m in tar.getmembers():
            rel = m.name[len(prefixe) :].lstrip("/") if m.name.startswith(prefixe) else None
            if not rel:
                continue
            cible = (racine / rel).resolve()
            if racine not in cible.parents:
                raise ErreurRefus(f"chemin suspect dans l'archive de {ref} : {m.name}")
            if m.isdir():
                cible.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                cible.parent.mkdir(parents=True, exist_ok=True)
                cible.write_bytes(tar.extractfile(m).read())
                cible.chmod(m.mode & 0o777 or 0o644)
            elif m.issym():
                lien = Path(m.linkname)
                if lien.is_absolute() or racine not in (cible.parent / lien).resolve().parents:
                    raise ErreurRefus(f"lien symbolique sortant dans {ref} : {m.name}")
                cible.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(m.linkname, cible)


def assembler(copie: Path, sources: list[Path]) -> list[str]:
    """Pose les cas de chaque source sous ``<copie>/evals/``, **sans leur oracle**.

    Rend les noms de cas posés. Un cas en double entre deux sources est un refus.
    """
    cible = copie / "evals"
    if cible.exists():
        shutil.rmtree(cible)  # les deux copies doivent porter exactement les mêmes cas
    cible.mkdir(parents=True)
    poses: list[str] = []
    for source in sources:
        for entree in sorted(source.iterdir()):
            destination = cible / entree.name
            if entree.is_dir() and est_un_cas(entree):
                if destination.exists():
                    raise ErreurRefus(f"cas « {entree.name} » présent dans deux sources")
                cas = entree
                shutil.copytree(
                    entree, destination,
                    ignore=lambda d, noms, cas=cas: ["oracle"] if Path(d) == cas else [],
                )
                poses.append(entree.name)
            elif entree.is_dir():
                if not destination.exists():
                    shutil.copytree(entree, destination)
            elif not destination.exists():
                shutil.copy2(entree, destination)
    return poses


# ==========================================================================
# Rapports JSON de « claude plugin eval --json »
# ==========================================================================
@dataclass
class ScoreCas:
    score: float
    passages: int
    cout: float


def verifier_complet(rapport: dict, etiquette: str) -> None:
    if not isinstance(rapport, dict):
        raise ErreurRefus(f"rapport {etiquette} : JSON inattendu")
    if rapport.get("partial") is True:
        raison = rapport.get("partialReason") or "raison non donnée"
        raise ErreurRefus(
            f"rapport {etiquette} : `partial: true` ({raison}) — des cas n'ont pas été "
            "joués ; comparer un rapport tronqué ferait passer des cas manquants pour "
            "des reculs. Relancer (plafond de coût plus haut, ou moins de cas)."
        )
    if rapport.get("schemaVersion", 1) != 1:
        raise ErreurRefus(
            f"rapport {etiquette} : schemaVersion {rapport.get('schemaVersion')!r} inconnue"
        )
    if not rapport.get("cases"):
        raise ErreurRefus(f"rapport {etiquette} : aucun cas")


def scores_par_cas(rapport: dict) -> dict[str, ScoreCas]:
    out: dict[str, ScoreCas] = {}
    for cas in rapport.get("cases", []):
        passages = (cas.get("arms") or {}).get("with") or []
        if passages:
            score = sum(float(p.get("score", 0)) for p in passages) / len(passages)
        else:
            score = float((cas.get("aggregates") or {}).get("score", 0))
        cout = sum(float(p.get("costUsd", 0)) + float(p.get("judgeCostUsd", 0)) for p in passages)
        out[cas["name"]] = ScoreCas(score, len(passages), cout)
    return out


def cout_rapport(rapport: dict) -> float:
    if "costUsd" in rapport:
        return float(rapport["costUsd"])
    return sum(s.cout for s in scores_par_cas(rapport).values())


def lire_rapport(chemin: Path, etiquette: str) -> dict:
    try:
        rapport = json.loads(Path(chemin).read_text("utf-8"))
    except (OSError, ValueError) as e:
        raise ErreurRefus(f"rapport {etiquette} illisible ({chemin}) : {e}") from e
    verifier_complet(rapport, etiquette)
    return rapport


# ==========================================================================
# Comparaison et bruit
# ==========================================================================
@dataclass
class Ligne:
    nom: str
    base: float
    tete: float
    delta: float
    recul: bool


@dataclass
class Comparaison:
    lignes: list[Ligne]
    moyenne_base: float
    moyenne_tete: float
    delta_moyen: float
    bruit_global: float
    bruit_cas: float  # seuil par cas appliqué, corrigé (Bonferroni, n cas)
    bruit_mesure: bool
    n_cas: int
    passages: int

    @property
    def recul(self) -> bool:
        return self.delta_moyen < -self.bruit_global - EPSILON or any(
            ligne.recul for ligne in self.lignes
        )


def _apparier(a: dict, b: dict):
    sa, sb = scores_par_cas(a), scores_par_cas(b)
    manque_b = [n for n in sa if n not in sb]
    manque_a = [n for n in sb if n not in sa]
    if manque_a or manque_b:
        raise ErreurRefus(
            "les deux rapports n'ont pas les mêmes cas — "
            f"absents du second : {manque_b or 'aucun'} ; absents du premier : "
            f"{manque_a or 'aucun'}. Rejouer sans --reference si des cas ont changé."
        )
    passages = min([s.passages for s in sa.values()] + [s.passages for s in sb.values()])
    if passages < 1:
        raise ErreurRefus("un cas n'a aucun passage joué : rien à comparer")
    return sa, sb, passages


def comparer(base: dict, tete: dict, bruit: dict | None = None) -> Comparaison:
    sa, sb, passages = _apparier(base, tete)
    n = len(sa)
    z_n = z_bonferroni(n)  # n comparaisons par cas : le seuil par cas s'élargit
    if bruit is not None:
        rms = float(bruit["rms_ecarts_cas"])
        bruit_cas, bruit_global = z_n * rms, Z95 * rms / math.sqrt(n)
    else:
        # Écart de deux moyennes, pas une moyenne : racine(2) x 1/racine(n*R).
        bruit_global = math.sqrt(2) / math.sqrt(n * passages)
        bruit_cas = math.sqrt(2) / math.sqrt(passages) * z_n / Z95
    lignes = []
    for nom, s in sa.items():
        delta = sb[nom].score - s.score
        lignes.append(
            Ligne(nom, s.score, sb[nom].score, delta, delta < -bruit_cas - EPSILON)
        )
    moy_a = sum(x.base for x in lignes) / n
    moy_b = sum(x.tete for x in lignes) / n
    return Comparaison(
        lignes, moy_a, moy_b, moy_b - moy_a, bruit_global, bruit_cas,
        bruit is not None, n, passages,
    )


def bruit_aa(a: dict, b: dict) -> dict:
    """Bruit mesuré entre deux jeux de la **même** référence."""
    sa, sb, passages = _apparier(a, b)
    n = len(sa)
    ecarts = [sb[nom].score - s.score for nom, s in sa.items()]
    rms = math.sqrt(sum(d * d for d in ecarts) / n)
    return {
        "schema": "evals_ab/bruit-1",
        "mesure": "demi-largeur d'intervalle à 95 % (pas un écart-type), "
        "sur l'écart entre deux jeux identiques",
        "n_cas": n,
        "passages": passages,
        "rms_ecarts_cas": rms,
        "demi_largeur_ic95_cas": Z95 * rms,
        "demi_largeur_ic95_globale": Z95 * rms / math.sqrt(n),
    }


def lire_bruit(chemin: Path) -> dict:
    try:
        bruit = json.loads(Path(chemin).read_text("utf-8"))
        float(bruit["rms_ecarts_cas"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise ErreurRefus(f"fichier de bruit illisible ({chemin}) : {e}") from e
    return bruit


# ==========================================================================
# Présentation
# ==========================================================================
def _pct(x: float) -> str:
    return f"{x * 100:.0f} %"


def _pts(x: float) -> str:
    return f"{x * 100:+.0f} pts"


def tableau_markdown(c: Comparaison, etiq_base: str, etiq_tete: str, verdict: bool = True) -> str:
    source = "mesuré en A/A" if c.bruit_mesure else "estimé √2/√(n·R)"
    sortie = [
        f"### {etiq_base} → {etiq_tete}",
        "",
        "| cas | base | tête | écart | verdict |",
        "|---|---|---|---|---|",
    ]
    for x in c.lignes:
        if x.recul:
            mot = "RECUL"
        elif abs(x.delta) < EPSILON:
            mot = "="
        else:
            mot = "dans le bruit" if abs(x.delta) <= c.bruit_cas else "mieux"
        sortie.append(f"| {x.nom} | {_pct(x.base)} | {_pct(x.tete)} | {_pts(x.delta)} | {mot} |")
    sortie.append(
        f"| **moyenne** | {_pct(c.moyenne_base)} | {_pct(c.moyenne_tete)} | "
        f"{_pts(c.delta_moyen)} | ± {c.bruit_global * 100:.0f} pts |"
    )
    sortie += [
        "",
        f"Bruit ({source}, {c.n_cas} cas × {c.passages} passages) : "
        f"± {c.bruit_global * 100:.0f} pts sur la moyenne ; "
        f"seuil par cas (Bonferroni, {c.n_cas} cas) : ± {c.bruit_cas * 100:.0f} pts.",
    ]
    if verdict:
        if c.recul:
            reculs = [x.nom for x in c.lignes if x.recul]
            detail = f"cas en recul : {', '.join(reculs)}" if reculs else "la moyenne recule"
            sortie.append(f"**Verdict : RECUL au-delà du bruit ({detail}).**")
        else:
            sortie.append("**Verdict : pas de recul au-delà du bruit.**")
    return "\n".join(sortie)


ENTETE_JOURNAL = """# Résultats des évaluations

Une ligne par comparaison jouée par `scripts/evals_ab.py --journal`. Le bruit
(±) est mesuré en A/A quand un fichier de bruit a été fourni, estimé sinon.

| date | plugin | mode | base | tête | cas × passages | moyenne base → tête | écart ± bruit | par cas (base → tête) | coût | commande |
|---|---|---|---|---|---|---|---|---|---|---|
"""


def _cellule(texte: str) -> str:
    return " ".join(str(texte).split()).replace("|", "\\|")


def ligne_journal(
    date: str, plugin: str, mode: str, etiq_base: str, etiq_tete: str,
    c: Comparaison, cout: float | None, commande: str,
) -> str:
    par_cas = "; ".join(f"{x.nom} {x.base * 100:.0f}→{x.tete * 100:.0f}" for x in c.lignes)
    cout_txt = f"${cout:.2f}" if cout is not None else "n/d"
    cellules = [
        date, plugin, mode, etiq_base, etiq_tete, f"{c.n_cas} × {c.passages}",
        f"{_pct(c.moyenne_base)} → {_pct(c.moyenne_tete)}",
        f"{_pts(c.delta_moyen)} ± {c.bruit_global * 100:.0f}"
        + ("" if c.bruit_mesure else " (estimé)"),
        par_cas, cout_txt, f"`{commande}`",
    ]
    return "| " + " | ".join(_cellule(x) for x in cellules) + " |"


def ajouter_au_journal(chemin: Path, ligne: str) -> None:
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if not chemin.exists():
        chemin.write_text(ENTETE_JOURNAL, "utf-8")
    existant = chemin.read_text("utf-8")
    with chemin.open("a", encoding="utf-8") as f:
        if not existant.endswith("\n"):
            f.write("\n")
        f.write(ligne + "\n")


# ==========================================================================
# Orchestration
# ==========================================================================
def etiquette(depot: Path, ref: str, plugin: str) -> str:
    def git(*args):
        r = subprocess.run(["git", "-C", str(depot), *args], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""

    sha = git("rev-parse", "--short", f"{ref}^{{commit}}")
    version = ""
    manifeste = git("show", f"{ref}:plugins/{plugin}/.claude-plugin/plugin.json")
    if manifeste:
        try:
            version = json.loads(manifeste).get("version", "")
        except ValueError:
            pass
    detail = ", ".join(x for x in (f"v{version}" if version else "", sha) if x)
    return f"{ref} ({detail})" if detail else ref


def lancer(lanceur: Path, dossier: Path, sortie: Path, options: list[str]) -> None:
    """Joue le lanceur ; sa sortie va sur stderr (stdout est réservé au tableau)."""
    try:
        p = subprocess.Popen(
            [str(lanceur), str(dossier), str(sortie), *options],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    except OSError as e:
        raise ErreurRefus(f"lanceur introuvable ou non exécutable ({lanceur}) : {e}") from e
    for ligne in p.stdout:
        sys.stderr.write(ligne)
    code = p.wait()
    if code == 2:
        raise ErreurRefus("le lanceur rend 2 : rapport partiel, refusé")
    if code not in (0, 1):  # 1 = un cas sous son seuil : le sujet, pas une panne
        raise ErreurRefus(f"le lanceur a échoué (code {code})")


def jouer_reference(
    depot: Path, ref: str, plugin: str, sources: list[Path], racine: Path,
    nom: str, lanceur: Path, options: list[str], etiquette_rapport: str,
) -> dict:
    copie = racine / nom / plugin
    extraire(depot, ref, plugin, copie)
    assembler(copie, sources)
    sortie = racine / f"{nom}.json"
    lancer(lanceur, copie, sortie, options)
    return lire_rapport(sortie, etiquette_rapport)


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="evals_ab.py",
        description="Compare deux versions d'un plugin sur les mêmes cas "
        "d'évaluation (claude plugin eval) : modes ab et aa, pré-vol avec "
        "oracle, bruit. Les options après « -- » vont au lanceur.",
    )
    p.add_argument("--plugin", required=True, help="nom du plugin (plugins/<nom>)")
    p.add_argument("--mode", choices=["ab", "aa"], default="ab",
                   help="ab : base contre tête ; aa : la tête jouée deux fois, mesure le bruit")
    p.add_argument("--base", default="main", help="référence git de base (défaut : main)")
    p.add_argument("--tete", default="HEAD", help="référence git de tête (défaut : HEAD)")
    p.add_argument("--prive", action="append", default=[], metavar="CHEMIN",
                   help="banc privé : dossier de cas ajoutés (répétable)")
    p.add_argument("--bruit", metavar="FICHIER",
                   help="bruit mesuré en A/A (écrit par --mode aa --sortie-bruit)")
    p.add_argument("--reference", metavar="FICHIER",
                   help="rapport JSON de la base déjà joué (cache CI) : la base n'est pas rejouée")
    p.add_argument("--journal", nargs="?", const="", default=None, metavar="FICHIER",
                   help="ajoute une ligne à evals/RESULTATS.md (ou au fichier donné)")
    p.add_argument("--sortie-bruit", metavar="FICHIER",
                   help="mode aa : où écrire le bruit mesuré (défaut : bruit-<plugin>.json)")
    p.add_argument("--garder-base", metavar="FICHIER",
                   help="copie le rapport de la base joué ici (pour un cache --reference)")
    p.add_argument("--lanceur", metavar="CHEMIN",
                   help="défaut : <dépôt>/evals/outillage/lancer.sh")
    p.add_argument("--depot", metavar="CHEMIN", help="racine du dépôt (défaut : celui du script)")
    p.add_argument("--conserver", action="store_true", help="ne pas supprimer les copies temporaires")
    p.add_argument("--previol-seul", action="store_true",
                   help="ne fait que le pré-vol (gratuit) et s'arrête")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    options_lanceur: list[str] = []
    if "--" in argv:
        coupe = argv.index("--")
        argv, options_lanceur = argv[:coupe], argv[coupe + 1 :]
    args = construire_parseur().parse_args(argv)
    commande = " ".join(["python3 scripts/evals_ab.py", *argv, *(["--", *options_lanceur] if options_lanceur else [])])
    try:
        return _executer(args, options_lanceur, commande)
    except (ErreurRefus, ErreurYaml) as e:
        print(f"REFUS : {e}", file=sys.stderr)
        return 3


def _executer(args, options_lanceur: list[str], commande: str) -> int:
    depot = Path(args.depot).resolve() if args.depot else DEPOT
    plugin = args.plugin
    lanceur = Path(args.lanceur) if args.lanceur else depot / "evals" / "outillage" / "lancer.sh"

    sources = [depot / "evals" / plugin]
    for chemin in args.prive:
        p = Path(chemin)
        sources.append(p / plugin if (p / plugin).is_dir() else p)
    for s in sources:
        if not s.is_dir():
            raise ErreurRefus(f"dossier de cas introuvable : {s}")

    # Pré-vol : gratuit, et il commande tout le reste.
    verdicts = [v for s in sources for v in previol(decouvrir_cas(s))]
    if not verdicts:
        raise ErreurRefus(f"aucun cas trouvé dans {', '.join(map(str, sources))}")
    for v in verdicts:
        for note in v.non_verifies:
            print(f"note : {note}", file=sys.stderr)
    erreurs = [e for v in verdicts for e in v.erreurs]
    if erreurs:
        raise ErreurRefus(
            "pré-vol : rien n'est joué.\n  - " + "\n  - ".join(erreurs)
        )
    print(f"pré-vol : {len(verdicts)} cas, oracles et témoins nuls conformes", file=sys.stderr)
    if args.previol_seul:
        return 0

    bruit = lire_bruit(args.bruit) if args.bruit else None
    ref_base = args.tete if args.mode == "aa" else args.base
    etiq_base = etiquette(depot, ref_base, plugin)
    etiq_tete = etiquette(depot, args.tete, plugin)

    racine = Path(tempfile.mkdtemp(prefix="evals-ab-"))
    try:
        rapports_joues = []
        if args.reference:
            rapport_base = lire_rapport(Path(args.reference), "de référence")
        else:
            rapport_base = jouer_reference(
                depot, ref_base, plugin, sources, racine, "base", lanceur,
                options_lanceur, "de base",
            )
            rapports_joues.append(rapport_base)
        if args.garder_base and not args.reference:
            shutil.copyfile(racine / "base.json", args.garder_base)
        rapport_tete = jouer_reference(
            depot, args.tete, plugin, sources, racine, "tete", lanceur,
            options_lanceur, "de tête",
        )
        rapports_joues.append(rapport_tete)
    finally:
        if args.conserver:
            print(f"copies conservées : {racine}", file=sys.stderr)
        else:
            shutil.rmtree(racine, ignore_errors=True)

    cout = sum(cout_rapport(r) for r in rapports_joues) or None
    if args.mode == "aa":
        mesure = bruit_aa(rapport_base, rapport_tete)
        mesure.update(plugin=plugin, reference=etiq_tete)
        chemin = Path(args.sortie_bruit or f"bruit-{plugin}.json")
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(mesure, indent=2, ensure_ascii=False) + "\n", "utf-8")
        c = comparer(rapport_base, rapport_tete)
        print(tableau_markdown(c, "A/A passage 1", "A/A passage 2", verdict=False))
        print(
            f"\nBruit mesuré : demi-largeur d'intervalle à 95 % de "
            f"± {mesure['demi_largeur_ic95_globale'] * 100:.0f} pts sur la moyenne, "
            f"± {mesure['demi_largeur_ic95_cas'] * 100:.0f} pts par cas — écrit dans {chemin}"
        )
        code = 0
    else:
        c = comparer(rapport_base, rapport_tete, bruit=bruit)
        print(tableau_markdown(c, etiq_base, etiq_tete))
        code = 1 if c.recul else 0

    if args.journal is not None:
        chemin_journal = Path(args.journal) if args.journal else depot / "evals" / "RESULTATS.md"
        ligne = ligne_journal(
            datetime.date.today().isoformat(), plugin, args.mode, etiq_base, etiq_tete,
            c, cout, commande,
        )
        ajouter_au_journal(chemin_journal, ligne)
    return code


if __name__ == "__main__":
    sys.exit(main())
