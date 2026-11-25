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
    liste, sous un autre nom, que (c) ne voit pas quand le contenu a bougé ;
(e) la liste d'enquête ``enquete.md`` perd une case (C0 à C12 attendues, dans
    l'ordre) : la fiche de l'enquêteur ne la recopiera plus, sans que rien le dise ;
(f) une case de ``enquete.md`` n'a pas sa forme de preuve (``; preuve : <forme>``) :
    l'enquêteur ne saurait pas quelle preuve rendre, et la fiche cocherait sans attendu.

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
    "enquete.md": [
        "plugins/plans-notion/agents/enqueteur.md",
        "plugins/plans-notion/skills/plan-notion/enquete.md",
        "plugins/plans-notion/skills/_partage/avant-le-plan.md",
        "plugins/plans-notion/skills/_partage/scripts/verifier-fiche-enquete.py",
        "evals/banc-relecture/enquete.py",
        "evals/banc-relecture/boucle_liste.py",
    ],
}

NOM_PERIME = "checklist-v2.txt"

# Liste d'enquête : une case est ``- [ ] C<n> …`` (même forme que verifier-fiche-enquete.py),
# et sa forme de preuve est ``; preuve : <forme>`` (enquete.md, en fin de ligne).
CASE_D_ENQUETE = re.compile(r"^[ \t]*[-*][ \t]+\[[ xX]\][ \t]+(?P<id>C\d+)\b(?P<reste>.*)$")
PREUVE_D_ENQUETE = re.compile(r";[ \t]*preuve[ \t]*:[ \t]*\S")


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

    def _cases_d_enquete(self):
        """Les lignes de case de enquete.md, dans l'ordre du fichier (texte lu, rien d'exécuté)."""
        texte = (DOSSIER_LISTES / "enquete.md").read_text(encoding="utf-8")
        return [m for m in (CASE_D_ENQUETE.match(ligne) for ligne in texte.splitlines()) if m]

    def test_enquete_ne_perd_aucune_case_C0_a_C12(self):
        # Panne (e). enqueteur.md et la fiche disent « treize cases, C0 à C12 » : une case retirée
        # de la liste sort de la fiche sans que personne le voie. Le compte fixe ce contrat.
        ids = [m.group("id") for m in self._cases_d_enquete()]
        self.assertEqual(
            ids, [f"C{n}" for n in range(13)],
            "la liste d'enquête ne porte pas C0 à C12 dans l'ordre : une case a disparu ou changé d'identifiant",
        )

    def test_chaque_case_d_enquete_a_sa_forme_de_preuve(self):
        # Panne (f). Une case sans « ; preuve : <forme> » ne dit pas à l'enquêteur quelle preuve rendre :
        # la fiche la cochera sans attendu. On nomme chaque case fautive, pas seulement la première.
        sans_forme = [m.group("id") for m in self._cases_d_enquete()
                      if not PREUVE_D_ENQUETE.search(m.group("reste"))]
        self.assertEqual(
            sans_forme, [],
            "cases de enquete.md sans « ; preuve : <forme> » : " + ", ".join(sans_forme),
        )


if __name__ == "__main__":
    unittest.main()
