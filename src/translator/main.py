from .larp_ast import parse_program


def say_hi_trans() -> None:
    print("Hello dear translator!")


if __name__ == "__main__":
    text = """
        (read (set a "111"))
        (if (== a 1)
        (read))
    """

    tree = parse_program(text)
    tree.codegen()
