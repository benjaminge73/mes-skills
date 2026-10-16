"""Le cache de la fumée a autant de places que de catégories, dans ci.yml.

Le danger que ce garde ferme : le job de fumée ne range une catégorie que dans
une place de cache. Avec 8 places pour 10 catégories, les deux dernières sont
jouées à chaque run, et seul un avertissement dans le journal le dit.

Deux pannes nommées, sur le vrai ci.yml et le vrai evals/categories.json :
(a) les places ne se désalignent pas : un pas de restauration et un pas de
    sauvegarde pour chaque place N de 0 à places-1, et `places=` qui donne ce
    nombre ;
(b) `places=` couvre le plugin qui a le plus de catégories.

Le workflow ne peut pas tourner en local : on lit sa structure par expressions
régulières, comme le fait déjà test_ci_locale.py. Rien d'autre n'est vérifié ici
(ni le cache GitHub, ni les clés).
"""
import json
import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
CI = RACINE / ".github" / "workflows" / "ci.yml"
CATEGORIES = RACINE / "evals" / "categories.json"


class PlacesDuCacheDeFumee(unittest.TestCase):
    def setUp(self):
        self.ci = CI.read_text(encoding="utf-8")

    def _places(self):
        valeurs = re.findall(r"^\s*places=(\d+)\s*$", self.ci, re.MULTILINE)
        self.assertEqual(len(valeurs), 1, "il faut exactement une ligne places=N dans ci.yml")
        return int(valeurs[0])

    def _numeros(self, libelle):
        motif = rf"^\s*- name: {libelle} de la place (\d+)\s*$"
        return sorted(int(n) for n in re.findall(motif, self.ci, re.MULTILINE))

    def test_chaque_place_a_son_pas_de_restauration_et_de_sauvegarde(self):
        places = self._places()
        attendu = list(range(places))
        self.assertEqual(self._numeros("Reprendre la fumée"), attendu,
                         "pas de restauration : places attendues (places=%d)" % places)
        self.assertEqual(self._numeros("Ranger la fumée"), attendu,
                         "pas de sauvegarde : places attendues (places=%d)" % places)

    def test_les_places_couvrent_le_plugin_qui_a_le_plus_de_categories(self):
        data = json.loads(CATEGORIES.read_text(encoding="utf-8"))
        maximum = max(
            len(cats) for plugin, cats in data.items()
            if not plugin.startswith("_") and isinstance(cats, dict)
        )
        self.assertGreaterEqual(
            self._places(), maximum,
            "places de cache (ci.yml) contre catégories du plugin le plus gros "
            "(evals/categories.json) : les suivantes sont jouées à chaque run",
        )


if __name__ == "__main__":
    unittest.main()
