from .larp_ast import parse_program


def say_hi_trans() -> None:
    print("Hello dear translator!")


if __name__ == "__main__":
    text = """
        (if (== 1 a) b 12)
    """

    tree = parse_program(text)
    tree.codegen()
