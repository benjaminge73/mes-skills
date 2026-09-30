import argparse
import sys

from convertisseur.calcul import celsius_vers_fahrenheit


def main(argv: list[str]) -> int:
    parseur = argparse.ArgumentParser(prog="convertisseur")
    parseur.add_argument("celsius", type=float)
    args = parseur.parse_args(argv)
    sys.stdout.write(f"{celsius_vers_fahrenheit(args.celsius):.1f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
