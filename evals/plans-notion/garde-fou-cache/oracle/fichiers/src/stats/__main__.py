import argparse
import sys

from stats.lecture import lire_colonne


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(prog="stats")
    parseur.add_argument("fichier")
    parseur.add_argument("--colonne", default="valeur")
    args = parseur.parse_args(argv)

    valeurs = lire_colonne(args.fichier, args.colonne)
    if not valeurs:
        sys.stderr.write("aucune valeur\n")
        return 1
    sys.stdout.write(f"moyenne : {sum(valeurs) / len(valeurs):.2f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
