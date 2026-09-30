def declenche(horodatages: list[int], seuil: int = 5, fenetre_s: int = 60) -> bool:
    """Vrai si une carte fait au moins `seuil` transactions dans une fenêtre de `fenetre_s` secondes.

    `horodatages` : secondes écoulées, triées, pour une même carte.
    """
    for i in range(len(horodatages) - seuil + 1):
        if horodatages[i + seuil - 1] - horodatages[i] < fenetre_s:
            return True
    return False
