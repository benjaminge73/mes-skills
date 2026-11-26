"""Calculs sur une liste d'articles."""


def total_quantites(articles):
    """Somme des quantités."""
    return sum(article["quantite"] for article in articles)


def total_prix(articles):
    """Somme des prix (en cours, autre session)."""
    return sum(article["prix"] * article["quantite"] for article in articles)
