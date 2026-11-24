"""Les listes de relecture vivent en un seul endroit, et chacune a des lecteurs.

Les listes sont dans ``plugins/plans-notion/skills/_partage/listes/``. Un lecteur
(un agent, un skill, un script du banc) ne voit une liste que par le renvoi qui
la nomme dans son texte : sans renvoi, il relit une version périmée, ou rien.

Pannes nommées, une par test :
(a) un lecteur a perdu le renvoi à sa liste (le relecteur ne cite plus
    ``listes/relecture-code.md``) : c'est le test qui porte le contrat ;
(b) une liste du dossier n'a aucun lecteur déclaré : elle a été ajoutée sans que
    personne la joue, et le garde (a) ne la voit pas ;
(c) une liste existe en copie octet pour octet ailleurs dans le dépôt : deux
    versions qui divergent sans que rien ne le dise ;
(d) l'ancien nom ``checklist-v2.txt`` réapparaît à côté de la liste : la même
    liste, sous un autre nom, que (c) ne voit pas quand le contenu a bougé.

Les lecteurs sont lus comme des fichiers texte, par un renvoi de chemin : rien
n'est exécuté, rien n'est mocké. Lancé par
``python3 -m unittest discover -s scripts -p 'test_*.py'``, sans dépendance.
"""
import os
import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_LISTES = RACINE / "plugins" / "plans-notion" / "skills" / "_partage" / "listes"

# Chaque liste, et les fichiers qui la lisent. Un lecteur doit citer
# ``listes/<nom>`` : chemin complet dans un skill ou un agent, chemin relatif
# dans le code du banc (``evals/banc-relecture``).
LECTEURS = {
    "relecture-code.md": [
        "plugins/plans-notion/agents/relecteur.md",
        "evals/banc-relecture/ombre.py",
        "evals/banc-relecture/rejouer.py",
        "evals/banc-relecture/boucle_liste.py",
    ],
    "rapport-executant.md": [
        "plugins/plans-notion/agents/executant.md",
        "plugins/plans-notion/skills/executer-plan-notion/etapes.md",
    ],
    "relecture-plan.md": [
        "plugins/plans-notion/skills/plan-notion/passer-la-main.md",
        "plugins/plans-notion/skills/_partage/avant-le-plan.md",
        "plugins/plans-notion/skills/_partage/relecture-par-hal.md",
    ],
}

NOM_PERIME = "checklist-v2.txt"


def _fichiers_du_depot():
    """Tous les fichiers du dépôt, sans ``.git``, caches ni dossiers cachés."""
    for racine, dossiers, fichiers in os.walk(RACINE):
        dossiers[:] = [d for d in dossiers if not d.startswith(".") and d != "__pycache__"]
        for nom in fichiers:
            yield Path(racine, nom)


class ListesDeRelecture(unittest.TestCase):

    def test_chaque_lecteur_cite_sa_liste(self):
        # Panne (a). Le test tient le renvoi, pas le texte autour : la phrase
        # qui cite la liste peut être réécrite, le chemin non.
        self.assertTrue(DOSSIER_LISTES.is_dir(), f"dossier des listes absent : {DOSSIER_LISTES}")
        manques = []
        for nom, lecteurs in LECTEURS.items():
            if not (DOSSIER_LISTES / nom).is_file():
                manques.append(f"la liste {nom} n'existe pas")
            motif = re.compile(re.escape(f"listes/{nom}"))
            for lecteur in lecteurs:
                chemin = RACINE / lecteur
                if not chemin.is_file():
                    manques.append(f"{lecteur} n'existe pas (lecteur de {nom})")
                elif not motif.search(chemin.read_text(encoding="utf-8")):
                    manques.append(f"{lecteur} ne cite plus listes/{nom}")
        self.assertEqual(manques, [], "un lecteur a perdu le renvoi à sa liste :\n" + "\n".join(manques))

    def test_chaque_liste_du_dossier_a_ses_lecteurs_declares(self):
        # Panne (b), en plus de (a) : une liste ajoutée au dossier sans entrée
        # dans LECTEURS n'est vérifiée par aucun garde. Sans ce test, elle passe.
        presentes = {p.name for p in DOSSIER_LISTES.iterdir() if p.is_file() and not p.name.startswith(".")}
        self.assertEqual(
            presentes, set(LECTEURS),
            "une liste du dossier n'a pas de lecteurs déclarés dans LECTEURS "
            "(ou une entrée de LECTEURS n'a plus de fichier)",
        )

    def test_aucune_copie_octet_pour_octet_de_la_liste(self):
        # Panne (c). On ne compare qu'à taille égale : le contenu n'est lu que
        # pour les fichiers qui pourraient être une copie.
        copies = []
        for nom in LECTEURS:
            source = DOSSIER_LISTES / nom
            if not source.is_file():
                continue
            octets = source.read_bytes()
            for fichier in _fichiers_du_depot():
                if fichier == source or fichier.stat().st_size != len(octets):
                    continue
                if fichier.read_bytes() == octets:
                    copies.append(f"{fichier.relative_to(RACINE)} (copie de {nom})")
        self.assertEqual(copies, [], "une liste existe en copie hors de son dossier :\n" + "\n".join(copies))

    def test_checklist_v2_ne_reapparait_pas(self):
        # Panne (d), en plus de (c) : l'ancien nom de la liste de code. Une copie
        # sous ce nom, modifiée ensuite, n'est plus une copie octet pour octet.
        trouves = [str(f.relative_to(RACINE)) for f in _fichiers_du_depot() if f.name == NOM_PERIME]
        self.assertEqual(trouves, [], f"le nom périmé {NOM_PERIME} réapparaît : {trouves}")


if __name__ == "__main__":
    unittest.main()
