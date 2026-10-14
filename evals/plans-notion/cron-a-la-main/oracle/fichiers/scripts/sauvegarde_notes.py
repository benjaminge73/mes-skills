#!/usr/bin/env python3
"""Copie les notes Markdown du répertoire courant vers ../sauvegarde/."""
import shutil
from pathlib import Path


def sauvegarder(racine):
    destination = Path(racine).resolve().parent / "sauvegarde"
    destination.mkdir(exist_ok=True)
    fichiers = [f for f in Path(racine).iterdir() if f.is_file() and f.suffix == ".md"]
    for fichier in sorted(fichiers):
        shutil.copy2(fichier, destination / fichier.name)
    return len(fichiers)


if __name__ == "__main__":
    print(f"sauvegarde ok: {sauvegarder('.')} fichiers")
