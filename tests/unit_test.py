from lark.tree import Meta
from src.translator.larp_ast import *
from src.translator.larp_ast import _Integer


def test_building_ast():
    text = """
        (if (== a 1)
            (read))
    """

    condition = Condition(
        Meta(), Invokable(
            Meta(),
            Control(Meta(), "=="),
            Args(Meta(), [
                Symbol(Meta(), "a"),
                _Integer(Meta(), 1)
            ])))

    body = IfBody(Meta(), Invokable(Meta(), Control(Meta(), "read"), Args(Meta(), [])))

    awaited_ast = Program(
        Meta(),
        [IfExpression(Meta(), condition, body)])

    assert parse_program(text).codegen() == awaited_ast.codegen()
