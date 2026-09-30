def format_prix(montant: float, devise: str) -> str:
    """Prix affiché : deux décimales et le symbole de la devise."""
    symboles = {"EUR": "€", "USD": "$"}
    return f"{montant:.2f} {symboles.get(devise, devise)}"
