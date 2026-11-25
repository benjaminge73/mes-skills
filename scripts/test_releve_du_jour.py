"""Le relevé du jour (releve-du-jour.py) : ce qu'il rend d'un VPS, et ce qu'il ne doit jamais recopier.

Chaque test monte un faux foyer Hermes dans un dossier temporaire (faux HOME, faux HERMES_HOME, faux `systemctl`
dans PATH) et lance le script comme le ferait le pilote : sous-processus, sortie lue ligne à ligne. Aucun test ne lit
le vrai ~/.hermes, le vrai `systemctl` ni le vrai `hermes`. `git` reste le vrai : c'est lui qui dit si le cœur est propre.

Écrit en ``unittest`` pur : la CI le joue avec ``python3 -m unittest discover -s scripts -p 'test_*.py'``.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1]
          / "plugins/plans-notion/skills/_partage/scripts/releve-du-jour.py")
PATH_SYSTEME = "/usr/bin:/bin"  # le vrai systemctl y est : le faux, placé avant, le masque
DATES_COMMIT = {"GIT_AUTHOR_DATE": "2026-11-20T12:00:00+00:00", "GIT_COMMITTER_DATE": "2026-11-20T12:00:00+00:00"}
CRON_SAIN = "aaaaaaaaaaaa"
FAUX_SYSTEMCTL = """#!/bin/sh
# Faux systemctl : rend ce que le test a mis dans la variable d'environnement, portée par portée.
case "$*" in
  *--user*) printf '%s' "$FAUX_SYSTEMCTL_USER" ;;
  *) printf '%s' "$FAUX_SYSTEMCTL_SYSTEME" ;;
esac
"""
VENV_SAIN = "#!/bin/sh\nexit 0\n"
RE_CONSTAT = re.compile(r"^(R\d+|SECURITE) · ")


@dataclass
class Foyer:
    home: Path
    racine: Path
    coeur: Path
    bin: Path


def ecrire(chemin: Path, texte: str, executable: bool = False) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")
    if executable:
        chemin.chmod(0o755)


def jobs(*ids: str) -> str:
    return json.dumps({"jobs": [{"id": i, "name": f"cron {i}", "enabled": True} for i in ids]})


def git(depot: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(depot), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, text=True, env={**os.environ, **DATES_COMMIT})


def faux_foyer(test: unittest.TestCase) -> Foyer:
    """Un VPS sain : cœur git propre, venv factice, passerelle postérieure au commit, miroirs égaux aux vivants."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    home = Path(tmp.name) / "home"
    racine = home / ".hermes"
    coeur = racine / "hermes-agent"
    ecrire(coeur / "README.md", "cœur\n")
    ecrire(coeur / "venv" / "bin" / "python", VENV_SAIN, executable=True)
    git(coeur, "init", "-q", "-b", "main")
    git(coeur, "add", "-A")
    git(coeur, "commit", "-q", "-m", "cœur")
    ecrire(racine / "state" / "gateway.lifecycle.json",
           json.dumps({"phase": "running", "started_at": "2026-11-21T08:00:00+00:00"}))
    ecrire(racine / "cron" / "jobs.json", jobs(CRON_SAIN))
    ecrire(racine / "patches" / "config" / "cron" / "jobs.json", jobs(CRON_SAIN))
    ecrire(racine / "profiles" / "franz-kafkai" / "cron" / "jobs.json", jobs("bbbbbbbbbbbb"))
    ecrire(racine / "patches" / "config" / "profiles" / "franz-kafkai" / "cron" / "jobs.json", jobs("bbbbbbbbbbbb"))
    (racine / "profiles" / ".deleted" / "franz").mkdir(parents=True)
    bin_ = Path(tmp.name) / "bin"
    ecrire(bin_ / "systemctl", FAUX_SYSTEMCTL, executable=True)
    return Foyer(home=home, racine=racine, coeur=coeur, bin=bin_)


def relever(*args: str, home: Path, bin_: Path, extra: dict[str, str] | None = None,
            path: str | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Lance le script avec un environnement fabriqué de zéro : rien de la session du poste n'y entre."""
    env = {"HOME": str(home), "PATH": path if path is not None else f"{bin_}:{PATH_SYSTEME}",
           "LANG": "C.UTF-8", "FAUX_SYSTEMCTL_USER": "", "FAUX_SYSTEMCTL_SYSTEME": ""}
    env.update(extra or {})
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          env=env, cwd=cwd or home, timeout=120)


def relever_foyer(foyer: Foyer, *args: str, extra: dict[str, str] | None = None,
                  path: str | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return relever(*args, home=foyer.home, bin_=foyer.bin, path=path, cwd=cwd,
                   extra={"HERMES_HOME": str(foyer.racine), **(extra or {})})


def constats_de(sortie: str, detecteur: str) -> list[str]:
    """Les lignes de constat d'un détecteur (« R9 · … »), et elles seules."""
    return [ligne for ligne in sortie.splitlines() if ligne.startswith(f"{detecteur} · ")]


class ReleveDuJour(unittest.TestCase):

    def test_un_foyer_sain_ne_sort_aucun_constat(self):
        # Panne visée : un faux positif sur un VPS propre (un détecteur qui crie sans raison, ou une passerelle
        # comparée à l'envers à la date du commit).
        foyer = faux_foyer(self)

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([l for l in r.stdout.splitlines() if RE_CONSTAT.match(l)], [], r.stdout)
        self.assertIn("aucun constat.", r.stdout)

    def test_un_fichier_modifie_dans_le_coeur_sort_R6(self):
        # Panne visée : le détecteur R6 (fichiers non commités dans le cœur Hermes) n'existe pas.
        foyer = faux_foyer(self)
        ecrire(foyer.coeur / "README.md", "modifié sans commit\n")

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R6")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("1 fichier(s) non commité(s)", lignes[0])

    def test_un_cron_vivant_absent_du_miroir_sort_R9(self):
        # Panne visée : un cron créé en direct sur le VPS passe inaperçu face à son miroir versionné.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "cron" / "jobs.json", jobs(CRON_SAIN, "cccccccccccc"))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R9")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("cccccccccccc", lignes[0])
        self.assertIn("vivant absent du miroir", lignes[0])

    def test_un_cron_du_miroir_retire_en_direct_sort_R9(self):
        # Panne visée : la seconde direction de la comparaison (un cron versionné que le VPS ne fait plus tourner)
        # n'est pas relevée. Même détecteur que le test précédent ; c'est le sens inverse, qu'il ne couvre pas.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "patches" / "config" / "cron" / "jobs.json", jobs(CRON_SAIN, "dddddddddddd"))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R9")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("dddddddddddd", lignes[0])
        self.assertIn("absent des crons vivants", lignes[0])

    def test_comparer_ne_rend_que_l_ecart_avec_la_fiche(self):
        # Panne visée : --comparer rend tout (la fiche ne sert à rien) ou rien (il ne voit pas l'écart nouveau).
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "cron" / "jobs.json", jobs(CRON_SAIN, "cccccccccccc"))
        fiche = foyer.home / "fiche.md"
        fiche.write_text(relever_foyer(foyer).stdout, encoding="utf-8")

        meme = relever_foyer(foyer, "--comparer", str(fiche))
        self.assertEqual(meme.returncode, 0, meme.stderr)
        self.assertEqual(meme.stdout, "")

        ecrire(foyer.racine / "cron" / "jobs.json", jobs(CRON_SAIN, "cccccccccccc", "eeeeeeeeeeee"))
        ecart = relever_foyer(foyer, "--comparer", str(fiche))
        self.assertEqual(ecart.returncode, 0, ecart.stderr)
        lignes = constats_de(ecart.stdout, "R9")
        self.assertEqual(len(lignes), 1, ecart.stdout)
        self.assertIn("eeeeeeeeeeee", lignes[0])

    def test_une_valeur_secrete_d_un_cron_ne_sort_jamais(self):
        # Panne visée : le constat recopie le contenu d'un cron (son invite) au lieu de son seul identifiant.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "cron" / "jobs.json", json.dumps({"jobs": [
            {"id": CRON_SAIN, "name": "cron sain", "enabled": True},
            {"id": "ffffffffffff", "name": "cron", "prompt": "utilise le jeton FAUX-JETON-7f3a"},
        ]}))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(constats_de(r.stdout, "R9")), 1, r.stdout)
        self.assertNotIn("FAUX-JETON-7f3a", r.stdout + r.stderr)

    def test_un_cron_de_profil_absent_du_miroir_sort_avec_le_nom_du_profil(self):
        # Panne visée : la comparaison ne se fait que sur le défaut ; un cron de profil absent de son miroir passe.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "profiles" / "franz-kafkai" / "cron" / "jobs.json",
               jobs("bbbbbbbbbbbb", "gggggggggggg"))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R9")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("profil franz-kafkai", lignes[0])
        self.assertIn("gggggggggggg", lignes[0])

    def test_un_profil_sans_jobs_ou_sans_miroir_ne_sort_rien_et_ne_plante_pas(self):
        # Panne visée : un profil sans jobs.json, ou avec des crons mais sans miroir, fait planter le relevé
        # ou sort un faux constat. La fiche dit « rien » pour ces deux cas.
        foyer = faux_foyer(self)
        (foyer.racine / "profiles" / "agent-socle").mkdir(parents=True)
        ecrire(foyer.racine / "profiles" / "mavod-web-enrich" / "cron" / "jobs.json", jobs("hhhhhhhhhhhh"))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(constats_de(r.stdout, "R9"), [], r.stdout)

    def test_le_dossier_deleted_des_profils_n_est_jamais_lu(self):
        # Panne visée : profiles/.deleted (anciens profils supprimés) est lu comme un profil vivant.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "profiles" / ".deleted" / "franz" / "cron" / "jobs.json", jobs("iiiiiiiiiiii"))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(constats_de(r.stdout, "R9"), [], r.stdout)

    def test_une_passerelle_plus_ancienne_que_le_coeur_sort_R10(self):
        # Panne visée : le détecteur R10 (passerelle démarrée avant le dernier commit du cœur) n'existe pas.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "state" / "gateway.lifecycle.json",
               json.dumps({"phase": "running", "started_at": "2026-11-19T08:00:00+00:00"}))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R10")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("avant le dernier commit", lignes[0])

    def test_sans_RELEVE_HERMES_CUSTOM_le_miroir_se_lit_sous_HOME_patches(self):
        # Panne visée : sans la variable, le miroir est cherché ailleurs (chemin en dur, racine du dépôt courant) :
        # un cron vivant absent du vrai miroir ne sort alors pas, ou sort « illisible ».
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "cron" / "jobs.json", jobs(CRON_SAIN, "jjjjjjjjjjjj"))

        r = relever(home=foyer.home, bin_=foyer.bin)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R9")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("jjjjjjjjjjjj", lignes[0])
        self.assertNotIn("illisible", r.stdout)

    def test_HERMES_HOME_sur_un_profil_lit_la_racine_et_non_le_profil(self):
        # Panne visée : une session de profil Hermes pose HERMES_HOME=<racine>/profiles/<profil> ; le relevé prend ce
        # dossier de profil pour la racine et sort « illisible » partout (cœur absent). Le cron vivant absent du miroir
        # de la racine doit sortir, et rien ne doit être lu comme illisible.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "cron" / "jobs.json", jobs(CRON_SAIN, "cccccccccccc"))
        profil = foyer.racine / "profiles" / "franz-kafkai"

        r = relever(home=foyer.home, bin_=foyer.bin, extra={"HERMES_HOME": str(profil)})

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("illisible", r.stdout)
        lignes = constats_de(r.stdout, "R9")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("cccccccccccc", lignes[0])

    def test_hors_VPS_rend_la_ligne_sans_erreur(self):
        # Panne visée : sur un poste sans ~/.hermes, le relevé plante ou prétend avoir relevé quelque chose.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = Path(tmp.name) / "home"
        home.mkdir()
        vide = Path(tmp.name) / "bin"
        vide.mkdir()

        r = relever(home=home, bin_=vide)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("hors VPS, rien à relever", r.stdout)

    def test_un_outil_absent_sort_illisible_sans_planter(self):
        # Panne visée : git ou systemctl absent fait planter le script, ou fait lire « rien » à la place de « illisible ».
        foyer = faux_foyer(self)
        vide = foyer.home / "sans-outils"
        vide.mkdir()

        r = relever_foyer(foyer, path=str(vide))

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertTrue(any("illisible" in l for l in constats_de(r.stdout, "R8")), r.stdout)
        self.assertTrue(any("illisible" in l for l in constats_de(r.stdout, "R6")), r.stdout)

    def test_une_unite_en_echec_sort_R8_sans_en_tete_ni_legende(self):
        # Panne visée : le détecteur R8 ne voit pas les unités en échec, ou prend l'en-tête et la légende
        # de systemctl pour des unités.
        foyer = faux_foyer(self)
        sortie = ("UNIT LOAD ACTIVE SUB DESCRIPTION\n"
                  "camofox-x.service loaded failed failed Desc\n"
                  "\n1 loaded units listed.\n")

        r = relever_foyer(foyer, extra={"FAUX_SYSTEMCTL_USER": sortie})

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R8")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("camofox-x.service", lignes[0])
        self.assertIn("utilisateur", lignes[0])

    def test_le_fichier_unites_degradees_sort_ses_noms(self):
        # Panne visée : state/unites-degradees.json n'est pas lu, et une unité en panne qu'il porte reste hors du relevé.
        # Forme réelle : {nom: {ActiveState, SubState, Result, NRestarts}}, pour toutes les unités surveillées.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "state" / "unites-degradees.json", json.dumps({
            "zzz-test.service": {"ActiveState": "failed", "SubState": "failed", "Result": "exit-code"},
        }))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R8")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("zzz-test.service", lignes[0])
        self.assertIn("ActiveState=failed", lignes[0])
        self.assertIn("Result=exit-code", lignes[0])

    def test_seules_les_unites_en_panne_ou_en_boucle_sortent(self):
        # Panne visée : le fichier d'état est traité comme une liste d'unités en panne (toutes sortent). Il porte
        # aussi les unités saines, qui ne sortent pas. Deux branches de la règle sortent : `failed` (panne) et
        # `auto-restart` (boucle de redémarrage, Result « success », donc seule la seconde branche la rattrape).
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "state" / "unites-degradees.json", json.dumps({
            "sain.service": {"ActiveState": "active", "SubState": "running", "Result": "success"},
            "panne.service": {"ActiveState": "failed", "SubState": "failed", "Result": "exit-code"},
            "boucle.service": {"ActiveState": "activating", "SubState": "auto-restart", "Result": "success"},
        }))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R8")
        self.assertEqual(len(lignes), 2, r.stdout)
        self.assertTrue(any("panne.service" in l for l in lignes), r.stdout)
        self.assertTrue(any("boucle.service" in l for l in lignes), r.stdout)
        self.assertNotIn("sain.service", r.stdout)
        # Une unité en redémarrage automatique n'est pas une panne : une seule photo ne fait pas une boucle.
        boucle = next(l for l in lignes if "boucle.service" in l)
        self.assertIn("en redémarrage automatique", boucle)
        self.assertNotIn("en panne", boucle)

    def test_un_result_en_echec_ne_compte_que_si_l_unite_est_inactive(self):
        # Panne visée : un Result en échec sort quel que soit ActiveState. diagnostiquer ne le retient que pour une
        # unité inactive (un oneshot ou un timer qui a échoué à son dernier run). « tourne.service » a un Result en
        # échec mais tourne : il ne sort pas. « arrete.service » est arrêté sur le même Result : il sort.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "state" / "unites-degradees.json", json.dumps({
            "tourne.service": {"ActiveState": "active", "SubState": "running", "Result": "exit-code"},
            "arrete.service": {"ActiveState": "inactive", "SubState": "dead", "Result": "exit-code"},
        }))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("tourne.service", r.stdout)
        lignes = constats_de(r.stdout, "R8")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("arrete.service", lignes[0])
        self.assertIn("en panne", lignes[0])

    def test_un_job_termine_absent_du_miroir_ne_sort_pas(self):
        # Panne visée : un cron vivant dont state vaut « completed » (job terminé, pas une dérive) sort comme une
        # dérive. Le cron « scheduled » absent du miroir doit toujours sortir : sinon le test passerait au vert
        # en ne relevant rien.
        foyer = faux_foyer(self)
        ecrire(foyer.racine / "cron" / "jobs.json", json.dumps({"jobs": [
            {"id": CRON_SAIN, "name": "cron sain", "enabled": True},
            {"id": "kkkkkkkkkkkk", "name": "cron termine", "enabled": False, "state": "completed"},
            {"id": "llllllllllll", "name": "cron prevu", "enabled": True, "state": "scheduled"},
        ]}))

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("kkkkkkkkkkkk", r.stdout)
        lignes = constats_de(r.stdout, "R9")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("llllllllllll", lignes[0])

    def test_un_module_de_test_absent_du_venv_sort_R11(self):
        # Panne visée : le détecteur R11 (modules de test absents du venv Hermes) n'existe pas. Le faux venv
        # échoue sur un seul module, pour que le test ne dépende que de lui.
        foyer = faux_foyer(self)
        ecrire(foyer.coeur / "venv" / "bin" / "python",
               "#!/bin/sh\ncase \"$*\" in *pytest_timeout*) exit 1 ;; esac\nexit 0\n", executable=True)

        r = relever_foyer(foyer)

        self.assertEqual(r.returncode, 0, r.stderr)
        lignes = constats_de(r.stdout, "R11")
        self.assertEqual(len(lignes), 1, r.stdout)
        self.assertIn("pytest_timeout", lignes[0])


# Une ligne d'exemple par motif de la liste fermée. Les valeurs sont fausses : elles ne servent qu'à déclencher le motif.
MOTIFS_ATTENDUS = {
    "sudo": "sudo systemctl restart x",
    "NOPASSWD": "hermes ALL=(ALL) NOPASSWD: ALL",
    "ufw": "ufw allow 22",
    "chmod": "chmod 600 cfg",
    "chown": "chown root cfg",
    "setcap": "setcap cap_net_bind_service+ep bin",
    "--system": "unit --system",
    "0.0.0.0": "bind 0.0.0.0:80",
    "api_key": "api_key = FAUX",
    "token": "token = FAUX",
    "secret": "secret = FAUX",
    "password": "password = FAUX",
    "identifiant Slack": "canal U0FAUXID12",
}


class ReleveDuJourSecurite(unittest.TestCase):
    """L'étape 2 : --objets lit le contenu des fichiers touchés et sort un SECURITE par couple (fichier, motif)."""

    def test_chaque_motif_de_la_liste_fait_sortir_une_ligne_SECURITE(self):
        # Panne visée : un motif de la liste fermée ne sort pas (regex absente, fausse, ou nom de motif faux).
        foyer = faux_foyer(self)
        depot = foyer.home / "depot"
        for i, texte in enumerate(MOTIFS_ATTENDUS.values()):
            ecrire(depot / f"m{i}.txt", texte + "\n")
        fichiers = [f"m{i}.txt" for i in range(len(MOTIFS_ATTENDUS))]

        r = relever_foyer(foyer, "--objets", *fichiers, cwd=depot)

        self.assertEqual(r.returncode, 0, r.stderr)
        for i, motif in enumerate(MOTIFS_ATTENDUS):
            with self.subTest(motif=motif):
                self.assertIn(f"SECURITE · m{i}.txt:1 · {motif}", r.stdout.splitlines(), r.stdout)

    def test_un_fichier_sans_motif_ne_sort_pas_meme_si_son_nom_en_porte_un(self):
        # Panne visée : le motif est cherché dans le nom du fichier (sudo-notes.md) et non dans son contenu.
        # Le fichier positif (vrai.txt) est là pour que le test ne passe pas au vert sans rien faire.
        foyer = faux_foyer(self)
        depot = foyer.home / "depot"
        ecrire(depot / "sudo-notes.md", "rien à signaler\n")
        ecrire(depot / "vrai.txt", "sudo systemctl restart x\n")

        r = relever_foyer(foyer, "--objets", "sudo-notes.md", "vrai.txt", cwd=depot)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(constats_de(r.stdout, "SECURITE"), ["SECURITE · vrai.txt:1 · sudo"], r.stdout)

    def test_seul_le_motif_sort_jamais_la_valeur_trouvee(self):
        # Panne visée : la ligne qui porte le motif est recopiée dans le constat, avec la valeur du jeton.
        foyer = faux_foyer(self)
        depot = foyer.home / "depot"
        ecrire(depot / "cfg.env", "api_key = FAUX-JETON-9c2e\n")

        r = relever_foyer(foyer, "--objets", "cfg.env", cwd=depot)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(constats_de(r.stdout, "SECURITE"), ["SECURITE · cfg.env:1 · api_key"], r.stdout)
        self.assertNotIn("FAUX-JETON-9c2e", r.stdout + r.stderr)

    def test_un_fichier_absent_ou_binaire_ne_sort_rien_sans_erreur(self):
        # Panne visée : un fichier absent (supprimé par le plan) ou binaire fait planter le relevé, ou sort un
        # faux motif trouvé dans des octets. Le fichier positif (ok.txt) empêche le passage au vert sans rien faire.
        foyer = faux_foyer(self)
        depot = foyer.home / "depot"
        depot.mkdir(parents=True)
        (depot / "bin.dat").write_bytes(b"\x00\x01sudo\x00")
        ecrire(depot / "ok.txt", "sudo systemctl restart x\n")

        r = relever_foyer(foyer, "--objets", "absent.txt", "bin.dat", "ok.txt", cwd=depot)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(constats_de(r.stdout, "SECURITE"), ["SECURITE · ok.txt:1 · sudo"], r.stdout)

    def test_une_seule_ligne_par_couple_fichier_motif(self):
        # Panne visée : une ligne par occurrence (sudo à deux endroits, deux constats) : du bruit pour le pilote.
        foyer = faux_foyer(self)
        depot = foyer.home / "depot"
        ecrire(depot / "deux.txt", "a\nsudo un\nb\nc\nsudo deux\n")

        r = relever_foyer(foyer, "--objets", "deux.txt", cwd=depot)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(constats_de(r.stdout, "SECURITE"), ["SECURITE · deux.txt:2 · sudo"], r.stdout)


if __name__ == "__main__":
    unittest.main()
