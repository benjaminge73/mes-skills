from dataclasses import dataclass


@dataclass
class Ligne:
    nom: str
    prix: float
    quantite: int


def total(lignes: list[Ligne]) -> float:
    return sum(l.prix * l.quantite for l in lignes)
