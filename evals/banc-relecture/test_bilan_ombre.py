"""Tests du bilan de l'ombre (`bilan_ombre.py`) : la règle de Q2 et les refus de données.

Aucun appel réseau : le juge est remplacé par un juge fictif, dont la liste des remarques captées est écrite ici,
dans le test, avant le calcul. Le juge réel (`juge.py`) n'est jamais lancé.
"""
from __future__ import annotations

import json

import pytest

import bilan_ombre


def ecrire_etape(dossier, id_, *, remarques, sha="sha-liste-1", cout=0.1, fait_le="2026-11-24"):
    """Une étape comptable : son ombre (`ombre-<id>.json`) et son tri du pilote (`retenues-<id>.json`)."""
    ombres = dossier / "ombres"
    ombres.mkdir(parents=True, exist_ok=True)
    (ombres / f"ombre-{id_}.json").write_text(json.dumps({
        "id": id_, "liste_sha256": sha, "fait_le": fait_le,
        "haiku": {"rapports": [], "cout": 0}, "sonnet": None, "erreurs": {},
        "chaine": {"result": f"rapport de la chaîne pour {id_}", "cout": cout, "cout_avec_haiku": cout, "verdicts": []},
    }))
    (ombres / f"retenues-{id_}.json").write_text(json.dumps({"id": id_, "remarques": remarques}))


def opus(gravite="autre"):
    return {"origine": "opus", "verdict": "retenue", "gravite": gravite, "resume": "défaut d'Opus"}


def ombre_seule(verdict, gravite="autre"):
    return {"origine": "ombre", "verdict": verdict, "gravite": gravite, "resume": "défaut vu par l'ombre seule"}


def juge_fictif(captees):
    """Juge de test : une remarque de référence est « oui » si (étape, n) figure dans `captees`, « non » sinon."""
    def juger(reference, chaines):
        assert set(reference) == set(chaines), "le juge doit recevoir la même liste d'étapes que les rapports"
        return {k: {"ref": [{"n": it["n"], "match": "oui" if (k, it["n"]) in captees else "non"} for it in items],
                    "extras": []} for k, items in reference.items()}
    return juger


def juge_interdit(reference, chaines):
    raise AssertionError("le juge ne doit pas être appelé : décision sans calcul de rappel")


def dernier_mot_de_decision(sortie):
    return sortie.strip().splitlines()[-1]


@pytest.mark.parametrize("captees_sur_100, decision_attendue", [
    # Frontière de Q2 : 69 remarques captées sur 100 tombent sous les 70 % et donnent « hybride » ; 70 donnent « bascule ».
    (69, "hybride"),
    (70, "bascule"),
])
def test_frontiere_des_70_pour_cent_entre_hybride_et_bascule(tmp_path, capsys, captees_sur_100, decision_attendue):
    # 20 étapes à 5 remarques retenues, toutes de gravité ordinaire : 100 remarques au dénominateur.
    for i in range(1, 21):
        ecrire_etape(tmp_path, f"e{i}", remarques=[opus() for _ in range(5)])
    ordre = [(f"e{i}", n) for i in range(1, 21) for n in range(1, 6)]
    captees = set(ordre[:captees_sur_100])

    code = bilan_ombre.main(["--min-etapes", "20"], donnees=tmp_path, juger=juge_fictif(captees))

    sortie = capsys.readouterr().out
    assert dernier_mot_de_decision(sortie) == f"DÉCISION : {decision_attendue}"
    assert code == 0


def test_remarque_de_l_ombre_seule_triee_reelle_entre_au_denominateur(tmp_path, capsys):
    # Panne attrapée : le bilan ne compterait que les remarques d'Opus, et la chaîne aurait un rappel surévalué.
    # Chaque étape : 4 remarques d'Opus captées, 1 remarque de l'ombre seule jugée réelle non captée, 1 jugée bruit.
    # Dénominateur attendu : 5 × 20 = 100 (la réelle entre, le bruit n'entre pas), rappel 80 / 100.
    for i in range(1, 21):
        ecrire_etape(tmp_path, f"e{i}", remarques=[opus() for _ in range(4)] + [ombre_seule("réelle"), ombre_seule("bruit")])
    captees = {(f"e{i}", n) for i in range(1, 21) for n in range(1, 5)}

    bilan_ombre.main(["--min-etapes", "20"], donnees=tmp_path, juger=juge_fictif(captees))

    sortie = capsys.readouterr().out
    assert "remarques retenues (dénominateur) : 100" in sortie
    assert "rappel de la chaîne : 80.0 %" in sortie


def test_deux_empreintes_de_liste_differentes_rendent_le_code_4(tmp_path, capsys):
    # Panne attrapée : un bilan qui mêle deux versions de la liste et sort une décision sur un mélange.
    ecrire_etape(tmp_path, "e1", remarques=[opus()], sha="sha-liste-1")
    ecrire_etape(tmp_path, "e2", remarques=[opus()], sha="sha-liste-2")

    code = bilan_ombre.main(["--min-etapes", "2"], donnees=tmp_path, juger=juge_interdit)

    assert code == 4
    assert "versions mêlées" in capsys.readouterr().err


def test_ombre_sans_tri_du_pilote_ne_compte_pas_et_ne_juge_pas(tmp_path, capsys):
    # Panne attrapée : une ombre jouée mais jamais triée compterait comme étape et ferait payer un juge pour rien.
    # Ce sont les dix ombres du 2026-11-23 : elles n'ont pas de retenues-<id>.json, donc rendent « pas assez d'étapes ».
    ombres = tmp_path / "ombres"
    ombres.mkdir()
    for i in range(1, 11):
        (ombres / f"ombre-e{i}.json").write_text(json.dumps({
            "id": f"e{i}", "liste_sha256": None, "fait_le": "2026-11-23",
            "chaine": {"result": "r", "cout": 0.1, "cout_avec_haiku": 0.1, "verdicts": []},
        }))

    code = bilan_ombre.main([], donnees=tmp_path, juger=juge_interdit)

    assert code == 3
    assert dernier_mot_de_decision(capsys.readouterr().out) == "DÉCISION : pas assez d'étapes"


def test_remarque_commune_ecartee_compte_comme_bruit_de_la_chaine(tmp_path, capsys):
    # Panne attrapée : le bruit que la chaîne partage avec Opus resterait invisible et le bilan basculerait
    # alors que la chaîne fait deux remarques non fondées par relecture (plafond : une).
    ecrire_etape(tmp_path, "e1", remarques=[opus(), {"origine": "commune", "verdict": "écartée", "gravite": "autre", "resume": "x"},
                                            {"origine": "commune", "verdict": "écartée", "gravite": "autre", "resume": "y"}])

    bilan_ombre.main(["--min-etapes", "1"], donnees=tmp_path, juger=juge_fictif({("e1", 1)}))

    sortie = capsys.readouterr().out
    assert "jugées bruit par relecture : 2.00" in sortie
    assert "DÉCISION : statu quo" in sortie
