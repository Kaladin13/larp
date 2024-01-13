import json
import sys
from pathlib import Path

from src.translator.larp_ast import parse_program


def say_hi_trans() -> None:
    print("Hello dear translator!")


def translate(text):
    tree = parse_program(text)
    return tree.codegen()


def try_out():
    text = """
        (defn solve (num div)
        (if (== div 10)
            (ret num))
        (if (== (% num div) 0)
            (solve num (- div 1))
            (solve (+ num 2520) 20)))

    (set val 232792560)
    (set res (solve val 20))
    (print res)
"""
    translate(text)


if __name__ == "__main__":

    debug_mode = True

    if debug_mode:
        try_out()

    if len(sys.argv) != 3:
        print("Invalid arguments. Usage: translator <input_file> <output_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sys.argv[1], encoding="utf-8") as file:
        with open(sys.argv[2], "w", encoding="utf-8") as output:
            res = translate(file.read())
            json.dump(res, output, indent=2)
