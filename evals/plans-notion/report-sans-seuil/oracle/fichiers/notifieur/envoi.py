import logging

journal = logging.getLogger("notifieur")


def envoyer_confirmation(commande_id: str, destinataire: str, transport) -> None:
    """Envoie l'e-mail de confirmation d'une commande."""
    transport.envoyer(destinataire, f"Confirmation de la commande {commande_id}")
    journal.info("envoi ok id=%s dest=%s", commande_id, destinataire)


def job_du_soir(commandes: list[tuple[str, str]], transport) -> None:
    """Envoie une confirmation par commande du jour."""
    for commande_id, destinataire in commandes:
        envoyer_confirmation(commande_id, destinataire, transport)
