import sys
from abc import ABC
from dataclasses import dataclass

from lark import Lark, Token, Transformer, v_args
from lark.ast_utils import AsList, Ast, WithMeta, create_transformer
from lark.tree import Meta

from .isa import ControlEnum, Opcode, cg, operator_bindings

this_module = sys.modules[__name__]


class _Ast(ABC, Ast):
    def codegen(self) -> None:
        raise NotImplementedError


class _Expression(_Ast):
    pass


@dataclass
class Program(_Ast, AsList, WithMeta):
    meta: Meta
    expressions: list[_Expression]

    def codegen(self) -> None:
        [x.codegen() for x in self.expressions]
        cg.stat()


class _Atomic(_Expression):
    pass


@dataclass
class Symbol(_Atomic, WithMeta):
    meta: Meta
    name: str

    def codegen(self) -> None:
        cg.find_variable_reg(self.name)


@dataclass
class _Integer(_Atomic, WithMeta):
    meta: Meta
    integer: int

    def codegen(self) -> None:
        cg.add_named_memory(self.integer)


@dataclass
class String(_Atomic, WithMeta):
    meta: Meta
    value: str
    STOP_SYM: str = "0x00"

    def codegen(self) -> None:
        cg.add_named_memory()
        for sym in self.value:
            cg.add_memory(sym, "char")
        cg.add_memory(self.STOP_SYM, "stop symbol")


@dataclass
class Control(_Ast, WithMeta):
    meta: Meta
    control: str

    def codegen(self) -> None:
        print("Control symbol {}".format(self.control))


@dataclass
class Args(_Ast, AsList, WithMeta):
    meta: Meta
    expressions: list[_Expression]

    def codegen(self) -> None:
        [x.codegen() for x in self.expressions]


@dataclass
class Invokable(_Expression, WithMeta):
    meta: Meta
    control: Control
    args: Args

    def codegen(self) -> None:
        match self.control.control:
            case ControlEnum.SET:
                control_set(self.control, self.args)
            case ControlEnum.READ:
                control_read(self.control, self.args)
            case _:
                control_bin_ops(self.control, self.args)


@dataclass
class Condition(_Ast, WithMeta):
    meta: Meta
    expression: _Expression

    def codegen(self) -> None:
        self.expression.codegen()


@dataclass
class IfBody(_Ast, WithMeta):
    meta: Meta
    expression: _Expression

    def codegen(self) -> None:
        self.expression.codegen()


@dataclass
class IfExpression(_Expression, WithMeta):
    meta: Meta
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


def save():
    cg.add_instruction(Opcode.PUSH, cg.S_REGISTER_1)
    cg.add_instruction(Opcode.PUSH, cg.S_REGISTER_2)
    cg.add_instruction(Opcode.PUSH, cg.AC_REGISTER)


def load():
    cg.add_instruction(Opcode.POP, cg.S_REGISTER_1)
    cg.add_instruction(Opcode.POP, cg.S_REGISTER_2)
    cg.add_instruction(Opcode.POP, cg.AC_REGISTER)


def control_read(control: Control, args: Args):
    assert len(args.expressions) == 0


def control_set(control: Control, args: Args):
    assert len(args.expressions) == 2
    assert args.expressions[0].__class__ == Symbol

    [i.codegen() for i in reversed(args.expressions)]
    cg.add_instruction(Opcode.LDR,
                       cg.variable_register,
                       address=cg.data_pointer)


def control_bin_ops(control: Control, args: Args):
    assert len(args.expressions) == 2
    [arg1, arg2] = args.expressions
    # callee saved registers
    save()

    arg2.codegen()
    reg2: int
    if arg2.__class__ == _Integer:
        cg.add_instruction(Opcode.LDR, cg.AC_REGISTER, address=cg.data_pointer)
        reg2 = cg.AC_REGISTER
    elif arg2.__class__ == Symbol:
        cg.add_instruction(Opcode.MOV, cg.S_REGISTER_2,
                           reg2=cg.variable_register)
        reg2 = cg.S_REGISTER_2
    else:
        # case of s-expression
        # we pop value pushed by nested instr
        cg.add_instruction(Opcode.POP, cg.S_REGISTER_2)
        reg2 = cg.S_REGISTER_2

    arg1.codegen()
    reg1: int
    if arg1.__class__ == _Integer:
        cg.add_instruction(Opcode.LDR, cg.AC_REGISTER, address=cg.data_pointer)
        reg1 = cg.AC_REGISTER
    elif arg1.__class__ == Symbol:
        cg.add_instruction(Opcode.MOV, cg.S_REGISTER_1,
                           reg2=cg.variable_register)
        reg1 = cg.S_REGISTER_1
    else:
        cg.add_instruction(Opcode.POP, cg.S_REGISTER_1)
        reg2 = cg.S_REGISTER_1

    binary_opcode: Opcode = operator_bindings[control.control]

    cg.add_instruction(binary_opcode, reg1, reg2=reg2)
    load()
    # push result to stack
    cg.add_instruction(Opcode.PUSH, reg1)


parser = Lark.open("grammar.lark", rel_to=__file__, start="program")

transformer = create_transformer(
    sys.modules[__name__],
    LarkToASTTransformer(),
)


def parse_program(text: str) -> _Ast:
    tree = parser.parse(text)
    return transformer.transform(tree)