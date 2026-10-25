"""Garde du hub de doc vivante de ``hermes-custom`` (décision de Benjamin du 2026-10-25).

La doc vivante de ``hermes-custom`` (Changelog, fiches) va **toujours** à la page
projet « Hermes » (sous ``Clients / Projets``) et à son ``📰 Changelog``, avec ou
sans plan. Une PR de ce dépôt n'est donc plus dite « à classer ».

Trois pannes, trois tests :

- (a) une PR de ``hermes-custom`` redevient « à classer » dans une consigne de
  ``plans-notion`` : le skill la laisse sans destination ;
- (b) la consigne ne dit plus que le hub de ``hermes-custom`` est fixe : la
  session redevient libre de deviner la page projet du plan ;
- (c) une URL Notion est publiée sous ``plugins/`` : le dépôt est public.

Le test (c) cherche une URL (un nom de domaine suivi de ``/``), pas le nom de
domaine seul : le hook ``rappel_delegation.py`` porte ces noms comme marqueurs
de code, et ce n'est pas une URL publiée.

Lancé par ``scripts/ci_locale.sh`` (``unittest discover -s scripts``), sans
dépendance hors de la bibliothèque standard.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PLUGINS = RACINE / "plugins"
PLANS_NOTION = PLUGINS / "plans-notion"
CHANGELOG = PLANS_NOTION / "skills" / "_partage" / "changelog-et-doc.md"
CLOTURE = PLANS_NOTION / "skills" / "executer-plan-notion" / "cloture.md"

A_CLASSER = re.compile(r"à\s+classer", re.IGNORECASE)
URL_NOTION = re.compile(r"(?:notion\.so|app\.notion\.com)/\S")


def fichiers_texte(racine: Path):
    """Chemin et texte de chaque fichier lisible en UTF-8 sous ``racine``."""
    for chemin in sorted(racine.rglob("*")):
        if not chemin.is_file() or "__pycache__" in chemin.parts:
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binaire : hors du champ d'un garde de texte
        yield chemin, texte


def section(texte: str, debut: str, fin: str) -> str:
    """Lignes comprises entre le titre ``debut`` et le titre ``fin`` (exclu)."""
    lignes = texte.splitlines()
    dedans = False
    garde = []
    for ligne in lignes:
        if ligne.startswith(debut):
            dedans = True
        elif dedans and ligne.startswith(fin):
            break
        if dedans:
            garde.append(ligne)
    return "\n".join(garde)


def bloc_rattachement(texte: str) -> str:
    """Puce « Rattachement » de ``cloture.md`` et ses lignes de suite.

    La suite d'une puce est plus indentée que la puce elle-même : on s'arrête à
    la première ligne qui ne l'est pas.
    """
    lignes = texte.splitlines()
    for i, ligne in enumerate(lignes):
        if "Rattachement :" in ligne and ligne.lstrip().startswith("- "):
            indent = len(ligne) - len(ligne.lstrip())
            bloc = [ligne]
            for suite in lignes[i + 1:]:
                if suite.strip() and (len(suite) - len(suite.lstrip())) > indent:
                    bloc.append(suite)
                else:
                    break
            return "\n".join(bloc)
    return ""


def phrases_qui_fixent_le_hub(bloc: str) -> list[str]:
    """Phrases du bloc qui citent ``hermes-custom``, le hub « Hermes » et « toujours »."""
    a_plat = " ".join(bloc.split())
    phrases = re.split(r"(?<=[.;])\s+", a_plat)
    return [p for p in phrases
            if "hermes-custom" in p and "Hermes" in p and "toujours" in p]


class HubHermesCustomFixe(unittest.TestCase):
    def test_aucun_a_classer_sous_plans_notion(self):
        # Panne (a) : une PR hermes-custom dite « à classer » dans une consigne.
        trouves = []
        for chemin, texte in fichiers_texte(PLANS_NOTION):
            for n, ligne in enumerate(texte.splitlines(), start=1):
                if A_CLASSER.search(ligne):
                    trouves.append(f"{chemin.relative_to(RACINE)}:{n}")
        self.assertEqual(
            trouves, [],
            "« à classer » subsiste sous plugins/plans-notion/ : une PR de "
            "hermes-custom doit aller au hub Hermes, pas être dite à classer",
        )

    def test_changelog_s1_dit_que_le_hub_hermes_custom_est_fixe(self):
        # Panne (b) : § 1 ne dit plus que le hub de hermes-custom est fixe.
        texte = CHANGELOG.read_text(encoding="utf-8")
        sec = section(texte, "## 1.", "## 2.")
        self.assertTrue(
            phrases_qui_fixent_le_hub(sec),
            "changelog-et-doc.md § 1 ne dit pas que le hub de hermes-custom "
            "est toujours la page Hermes (une phrase doit citer hermes-custom, "
            "Hermes et « toujours »)",
        )

    def test_rattachement_de_cloture_dit_que_le_hub_hermes_custom_est_fixe(self):
        # Panne (b) bis : le point (e) de la clôture laisse deviner le projet.
        texte = CLOTURE.read_text(encoding="utf-8")
        bloc = bloc_rattachement(texte)
        self.assertTrue(bloc, "puce « Rattachement » introuvable dans cloture.md")
        self.assertTrue(
            phrases_qui_fixent_le_hub(bloc),
            "cloture.md, point (e), « Rattachement » ne dit pas que hermes-custom "
            "va toujours au hub Hermes (une phrase doit citer hermes-custom, "
            "Hermes et « toujours »)",
        )

    def test_aucune_url_notion_publiee_sous_plugins(self):
        # Panne (c) : une URL Notion écrite dans un dépôt public.
        trouves = []
        for chemin, texte in fichiers_texte(PLUGINS):
            for n, ligne in enumerate(texte.splitlines(), start=1):
                if URL_NOTION.search(ligne):
                    trouves.append(f"{chemin.relative_to(RACINE)}:{n}")
        self.assertEqual(
            trouves, [],
            "une URL notion.so ou app.notion.com est publiée sous plugins/ : "
            "le dépôt est public, on désigne le hub par son titre",
        )


if __name__ == "__main__":
    unittest.main()
