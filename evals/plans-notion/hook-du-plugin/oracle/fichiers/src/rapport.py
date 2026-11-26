"""Affichage du rapport des articles."""

from src.articles import total_quantites


def afficher_rapport(articles):
    print(f"Total : {total_quantites(articles)}")
