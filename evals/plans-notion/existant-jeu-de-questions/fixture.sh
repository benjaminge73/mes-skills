#!/usr/bin/env bash
# Dépôt de départ du cas existant-jeu-de-questions : un assistant de support
# client. Un jeu de 12 questions de support existe déjà, rangé sous
# tests/golden/ (utilisé par un test de structure). N'écrit que dans le
# répertoire courant.
set -euo pipefail

mkdir -p bot tests/golden

cat > README.md <<'EOF'
# assistant-support

Assistant qui répond aux questions des clients du support (retours, livraison, factures).

## Configuration

Le modèle utilisé se règle dans `config.toml`.

## Tests

```bash
python3 -m unittest discover -s tests
```
EOF

cat > config.toml <<'EOF'
modele = "claude-haiku-4-5"
temperature = 0.2
EOF

cat > bot/__init__.py <<'EOF'
"""assistant-support."""
EOF

cat > bot/llm.py <<'EOF'
def complete(modele: str, prompt: str) -> str:
    """Appelle le modèle `modele` (client à brancher)."""
    raise NotImplementedError("client LLM non branché dans ce dépôt")
EOF

cat > bot/repondre.py <<'EOF'
from bot.llm import complete

CONSIGNE = "Tu es l'assistant du support client. Réponds en français, en deux phrases au plus.\n\nQuestion : "


def repondre(question: str, modele: str) -> str:
    return complete(modele, CONSIGNE + question)
EOF

cat > tests/golden/questions_support.jsonl <<'EOF'
{"id": "q01", "question": "Comment retourner un article acheté il y a 10 jours ?", "reponse_attendue": "Retour gratuit sous 30 jours via l'espace client."}
{"id": "q02", "question": "Mon colis indique livré mais je ne l'ai pas reçu.", "reponse_attendue": "Ouvrir une réclamation transporteur sous 48 h."}
{"id": "q03", "question": "Où télécharger ma facture ?", "reponse_attendue": "Espace client, rubrique Commandes, bouton Facture."}
{"id": "q04", "question": "Puis-je changer l'adresse de livraison après paiement ?", "reponse_attendue": "Oui tant que la commande n'est pas expédiée."}
{"id": "q05", "question": "Le code promo BIENVENUE ne fonctionne pas.", "reponse_attendue": "Le code est réservé à la première commande."}
{"id": "q06", "question": "Combien coûte la livraison express ?", "reponse_attendue": "6,90 euros, livraison en 24 h."}
{"id": "q07", "question": "Comment suivre ma commande ?", "reponse_attendue": "Lien de suivi dans l'e-mail d'expédition."}
{"id": "q08", "question": "Je veux annuler ma commande.", "reponse_attendue": "Annulation possible avant expédition depuis l'espace client."}
{"id": "q09", "question": "L'article reçu est cassé.", "reponse_attendue": "Envoyer une photo au support, remplacement gratuit."}
{"id": "q10", "question": "Acceptez-vous le paiement en trois fois ?", "reponse_attendue": "Oui à partir de 100 euros d'achat."}
{"id": "q11", "question": "Comment supprimer mon compte ?", "reponse_attendue": "Espace client, rubrique Compte, Supprimer mon compte."}
{"id": "q12", "question": "Livrez-vous en Belgique ?", "reponse_attendue": "Oui, délai de 3 à 5 jours ouvrés."}
EOF

cat > tests/test_golden.py <<'EOF'
import json
import pathlib
import unittest

GOLDEN = pathlib.Path(__file__).parent / "golden" / "questions_support.jsonl"


class GoldenTest(unittest.TestCase):
    def test_chaque_ligne_a_une_question_et_une_reponse_attendue(self):
        for ligne in GOLDEN.read_text(encoding="utf-8").splitlines():
            item = json.loads(ligne)
            self.assertTrue(item["question"])
            self.assertTrue(item["reponse_attendue"])


if __name__ == "__main__":
    unittest.main()
EOF

git init -q -b main
git add -A
git -c user.name="Fixture" -c user.email="fixture@example.invalid" -c commit.gpgsign=false -c core.hooksPath=/dev/null commit -q -m "assistant-support : bot et jeu de questions de référence"
