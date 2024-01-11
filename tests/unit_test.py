from lark.tree import Meta
from src.translator.larp_ast import *
from src.translator.larp_ast import _Integer


def test_building_ast():
    text = """
        (if (== a 1)
            (set a (+ a 1)))
    """

    condition = Condition(
        Meta(), Invokable(
            Meta(),
            Control(Meta(), "=="),
            Args(Meta(), [
                Symbol(Meta(), "a"),
                _Integer(Meta(), 1)
            ])))

    args = Args(Meta(), [
        Symbol(Meta(), "a"),
        Invokable(Meta(),
                  Control(Meta(), "+"),
                  Args(Meta(),
                       [
                           Symbol(Meta(), "a"),
                           _Integer(Meta(), 1)
                  ]))
    ])

    body = IfBody(Meta(), Invokable(
        Meta(), Control(Meta(), "set"), args))

    awaited_ast = Program(
        Meta(),
        [IfExpression(Meta(), condition, body)])

    assert len(awaited_ast.expressions) == len(parse_program(text).expressions)
