from .larp_ast import parse_program


def say_hi_trans() -> None:
    print("Hello dear translator!")


if __name__ == "__main__":
    text = """
        (set a "111")
        (set b 12)
        (== a 88)
        (== b (== s 20))
    """

    tree = parse_program(text)
    tree.codegen()
