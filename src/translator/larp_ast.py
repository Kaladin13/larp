import sys
from abc import ABC
from dataclasses import dataclass, field

from lark import Lark, Token, Transformer, v_args
from lark.ast_utils import AsList, Ast, WithMeta, create_transformer
from lark.tree import Meta

this_module = sys.modules[__name__]


class _SyntaxTree(ABC, Ast):
    def codegen(self) -> None:
        raise NotImplementedError


class _Expression(_SyntaxTree):
    pass


@dataclass
class Program(_SyntaxTree, AsList, WithMeta):
    meta: Meta = field(repr=False)
    expressions: list[_Expression]

    def codegen(self) -> None:
        print("At start!!!!")
        [x.codegen() for x in self.expressions]


class _Atomic(_Expression):
    pass


@dataclass
class Symbol(_Atomic, WithMeta):
    meta: Meta = field(repr=False)
    name: str

    def codegen(self) -> None:
        print("Symbol {}".format(self.name))


@dataclass
class _Integer(_Atomic, WithMeta):
    meta: Meta = field(repr=False)
    integer: int

    def codegen(self) -> None:
        print("Integer {}".format(self.integer))


@dataclass
class String(_Atomic, WithMeta):
    meta: Meta = field(repr=False)
    value: str

    def codegen(self) -> None:
        print("String {}".format(self.value))


@dataclass
class Control(_SyntaxTree, WithMeta):
    meta: Meta = field(repr=False)
    control: str

    def codegen(self) -> None:
        print("Control symbol {}".format(self.control))


@dataclass
class Args(_SyntaxTree, AsList, WithMeta):
    meta: Meta = field(repr=False)
    expressions: list[_Expression]

    def codegen(self) -> None:
        [x.codegen() for x in self.expressions]


@dataclass
class Invokable(_Expression, WithMeta):
    meta: Meta = field(repr=False)
    control: Control
    args: Args

    def codegen(self) -> None:
        print("Trying to invoke...")
        self.control.codegen()
        self.args.codegen()


@dataclass
class Condition(_SyntaxTree, WithMeta):
    meta: Meta = field(repr=False)
    expression: _Expression

    def codegen(self) -> None:
        self.expression.codegen()


@dataclass
class IfBody(_SyntaxTree, WithMeta):
    meta: Meta = field(repr=False)
    expression: _Expression

    def codegen(self) -> None:
        self.expression.codegen()


@dataclass
class IfExpression(_Expression, WithMeta):
    meta: Meta = field(repr=False)
    condition: Condition
    if_body: IfBody

    def codegen(self) -> None:
        print("If {} then {}"
              .format(self.condition.codegen(),
                      self.if_body.codegen()))


class LarkToASTTransformer(Transformer):
    def NAME(self, token: Token) -> str:
        return token.value

    def STRING(self, token: Token) -> str:
        return token.value[1:-1]

    @v_args(meta=True)
    def integer(self, meta: Meta, tokens: list[Token]) -> _Integer:
        if len(tokens) == 1:
            tokens.insert(0, Token("SIGN", "+"))

        sign = -1 if tokens[0].value == "-" else 1
        number = int(tokens[1].value)

        return _Integer(meta, sign * number)

    @v_args(inline=True)
    def expression(self, tree: _Expression) -> _Expression:
        return tree

    @v_args(inline=True)
    def atomic(self, tree: _Atomic) -> _Atomic:
        return tree

    @v_args(inline=True)
    def start(self, tree: Program) -> Program:
        return tree


parser = Lark.open("grammar.lark", rel_to=__file__, start="program")

transformer = create_transformer(
    sys.modules[__name__],
    LarkToASTTransformer(),
)


def parse_program(text: str) -> _SyntaxTree:
    tree = parser.parse(text)
    return transformer.transform(tree)
