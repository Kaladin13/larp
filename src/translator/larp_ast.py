import sys
from abc import ABC
from dataclasses import dataclass

from lark import Lark, Token, Transformer, v_args
from lark.ast_utils import AsList, Ast, WithMeta, create_transformer
from lark.tree import Meta

from src.config.config import IOMemoryMapping

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
        cg.add_instruction(Opcode.JMP, address=-1)
        [x.codegen() for x in self.expressions]
        return cg.stat()


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
    control: Control | Symbol
    args: Args

    def codegen(self) -> None:
        if hasattr(self.control.control, "name"):
            # funcall case
            control_funcall(self.control.control.name, self.args)
            return

        match self.control.control:
            case ControlEnum.SET:
                control_set(self.control, self.args)
            case ControlEnum.READ:
                control_read(self.control, self.args)
            case ControlEnum.PRINT:
                control_print(self.control, self.args)
            case ControlEnum.RETURN:
                control_ret(self.args)
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
class ElseBody(_Ast, WithMeta):
    meta: Meta
    expression: _Expression

    def codegen(self) -> None:
        self.expression.codegen()


@dataclass
class FunName(Symbol, WithMeta):
    meta: Meta
    name: str

    def codegen(self) -> None:
        print("Name")


@dataclass
class FunBody(_Ast, AsList, WithMeta):
    meta: Meta
    expressions: list[_Expression]

    def codegen(self) -> None:
        [x.codegen() for x in self.expressions]


@dataclass
class Function(_Expression, WithMeta):
    meta: Meta
    fun_name: FunName
    args: FunBody
    fun_body: Args

    def codegen(self) -> None:
        control_defn(self.fun_name.name.name, self.args.expressions,
                     self.fun_body.expressions)


def nop():
    cg.add_instruction(Opcode.CMP, cg.SP_REGISTER, cg.SP_REGISTER)


@dataclass
class IfExpression(_Expression, WithMeta):
    meta: Meta
    condition: Condition
    if_body: IfBody
    else_body: ElseBody = None

    def else_clause(self):
        cg.add_instruction(Opcode.POP, cg.AC_REGISTER)
        # get zero for comparison
        # ac_reg (val) ?= s_reg (0)
        cg.add_instruction(Opcode.SUB, cg.S_REGISTER_1, cg.S_REGISTER_1)
        cg.add_instruction(Opcode.CMP, cg.AC_REGISTER, cg.S_REGISTER_1)
        # hack to invert ac register
        cg.add_instruction(Opcode.JZ, cg.AC_REGISTER, address=cg.get_ip()+2)
        cg.add_instruction(Opcode.JMP, address=cg.get_ip()+2)
        cg.add_instruction(Opcode.CMP, cg.AC_REGISTER, cg.AC_REGISTER)

    def codegen(self) -> None:
        # dont save
        self.condition.codegen()

        if self.condition.expression.__class__ in [_Integer, String, Symbol]:
            cg.add_instruction(Opcode.CMP, cg.AC_REGISTER, cg.AC_REGISTER)
        else:
            self.else_clause()
        # if ac_reg == 1 then body, else take jump
        cg.add_instruction(Opcode.JZ, cg.AC_REGISTER, address=-1)
        jump_inst_address = cg.get_ip() - 1

        self.if_body.codegen()
        if self.if_body.expression.__class__ in [_Integer, String]:
            cg.add_instruction(Opcode.LDR, cg.SP_REGISTER,
                               address=cg.data_pointer)
        elif self.if_body.expression.__class__ == Symbol:
            cg.add_instruction(Opcode.MOV, cg.SP_REGISTER,
                               cg.variable_register)
        else:
            cg.add_instruction(Opcode.POP, cg.SP_REGISTER)
        # dont load
        cg.add_instruction(Opcode.PUSH, cg.SP_REGISTER)

        sec_jump_addr: int

        if self.else_body is not None:
            cg.add_instruction(Opcode.JMP, address=-1)
            sec_jump_addr = cg.get_ip() - 1

        cg.instructions[jump_inst_address]["address"] = cg.get_ip()

        nop()

        if self.else_body is not None:
            self.else_body.codegen()

            if self.else_body.expression.__class__ in [_Integer, String]:
                cg.add_instruction(Opcode.LDR, cg.SP_REGISTER,
                                   address=cg.data_pointer)
            elif self.else_body.expression.__class__ == Symbol:
                cg.add_instruction(Opcode.MOV, cg.SP_REGISTER,
                                   cg.variable_register)
            else:
                cg.add_instruction(Opcode.POP, cg.SP_REGISTER)
            # dont load
            cg.add_instruction(Opcode.PUSH, cg.SP_REGISTER)

            cg.instructions[sec_jump_addr]["address"] = cg.get_ip()

        nop()


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


def control_ret(args: Args):
    assert len(args.expressions) == 1
    arg = args.expressions[0]
    arg.codegen()

    if arg.__class__ == Symbol:
        cg.add_instruction(Opcode.PUSH, cg.variable_register)

    cg.add_instruction(Opcode.IJMP, cg.R_REGISTER)


def control_read(control: Control, args: Args):
    # we don't expect arguments
    assert len(args.expressions) == 0
    save()

    # add stop sym to named memory as word, save in reg
    cg.add_named_memory(String.STOP_SYM)
    cg.add_instruction(Opcode.LDR, cg.S_REGISTER_2, address=cg.data_pointer)

    cg.add_named_memory(cg.dynamic_str_ptr)
    # save the start of the input string
    str_start = cg.data_pointer
    cg.add_instruction(Opcode.LDR, cg.S_REGISTER_1, address=str_start)

    cg.add_instruction(Opcode.LDR, cg.AC_REGISTER,
                       address=IOMemoryMapping.CONTROL_BIT_MAPPING.value)

    # if ac_reg == 0 then jump
    cg.add_instruction(Opcode.JZ, cg.AC_REGISTER,
                       address=cg.get_ip() + 6)

    cg.add_instruction(Opcode.LDR, cg.AC_REGISTER,
                       address=IOMemoryMapping.INPUT_MAPPING.value)
    cg.add_instruction(Opcode.STR, cg.AC_REGISTER, cg.S_REGISTER_1)

    # 1 -> ac_reg, s_reg1 += 1
    cg.add_instruction(Opcode.CMP, cg.AC_REGISTER, cg.AC_REGISTER)
    cg.add_instruction(Opcode.ADD, cg.S_REGISTER_1, cg.AC_REGISTER)
    # jump to start of input cycle
    cg.add_instruction(Opcode.JMP, address=(cg.get_ip() - 6))
    # 0x00 -> [s_reg1] -> str_end
    cg.add_instruction(Opcode.STR, cg.S_REGISTER_2, cg.S_REGISTER_1)
    cg.dynamic_str_ptr += 32

    load()
    cg.add_instruction(Opcode.LDR, cg.SP_REGISTER, address=str_start)
    cg.add_instruction(Opcode.PUSH, cg.SP_REGISTER)


def handle_int(sym=False):
    if not sym:
        cg.add_instruction(Opcode.LDR, cg.AC_REGISTER,
                           address=cg.data_pointer)
    else:
        cg.add_instruction(Opcode.MOV, cg.AC_REGISTER,
                           cg.variable_register)
    cg.add_instruction(Opcode.STR, cg.AC_REGISTER, cg.S_REGISTER_1)


def handle_string(sym=False):
    if not sym:
        cg.add_instruction(Opcode.LDR, cg.S_REGISTER_2,
                           address=cg.data_pointer)
    else:
        cg.add_instruction(Opcode.MOV, cg.S_REGISTER_2,
                           cg.variable_register)
    cg.add_instruction(Opcode.ILDR, cg.AC_REGISTER, reg2=cg.S_REGISTER_2)
    cg.add_instruction(Opcode.STR, cg.AC_REGISTER, cg.S_REGISTER_1)
    cg.add_instruction(Opcode.CMP, cg.AC_REGISTER, cg.SP_REGISTER)
    # if [new_char] == STOP_SYM then jump
    cg.add_instruction(Opcode.JZ, cg.AC_REGISTER, address=(cg.get_ip() + 2))
    cg.add_instruction(Opcode.JMP, address=(cg.get_ip() + 4))

    cg.add_instruction(Opcode.CMP, cg.AC_REGISTER, cg.AC_REGISTER)
    cg.add_instruction(Opcode.ADD, cg.S_REGISTER_2, cg.AC_REGISTER)
    cg.add_instruction(Opcode.JMP, address=(cg.get_ip() - 7))

    nop()


def handle_two_args(arg1, arg2):
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
        reg1 = cg.S_REGISTER_1
    return [reg1, reg2]


def control_defn(fun_name: str,
                 args: list[_Expression],
                 fun_body: list[_Expression]):
    assert len(args) == 2
    assert args[0].__class__ == Symbol
    assert args[1].__class__ == Symbol

    cg.define_fun(fun_name, args[0].name, args[1].name)

    for v in fun_body:
        v.codegen()

    cg.add_instruction(Opcode.IJMP, cg.R_REGISTER)
    cg.ret_value = cg.get_ip()


def control_funcall(name: str, args: Args):
    assert len(args.expressions) == 2
    [arg1, arg2] = args.expressions
    # no reg save
    [reg1, reg2] = handle_two_args(arg1, arg2)

    [var1, var2, fn_address] = cg.add_mapping(name)
    cg.add_instruction(Opcode.MOV, var1, reg1)
    cg.add_instruction(Opcode.MOV, var2, reg2)

    if cg.is_first_call:
        cg.add_named_memory(cg.get_ip() + 3)
        cg.add_instruction(Opcode.LDR, cg.R_REGISTER, cg.data_pointer)
        cg.is_first_call = False

    cg.add_instruction(Opcode.JMP, fn_address)


def control_print(control: Control, args: Args):
    assert len(args.expressions) == 1
    save()
    [exp] = args.expressions

    cg.add_named_memory(IOMemoryMapping.OUTPUT_MAPPING.value)
    cg.add_instruction(Opcode.LDR, cg.S_REGISTER_1, address=cg.data_pointer)

    cg.add_named_memory(String.STOP_SYM)
    cg.add_instruction(Opcode.LDR, cg.SP_REGISTER, address=cg.data_pointer)

    exp.codegen()

    if exp.__class__ == _Integer:
        handle_int()
    elif exp.__class__ == String:
        handle_string()
    elif exp.__class__ == Symbol:
        if cg.registers[cg.variable_register] == 2:
            handle_string(True)
        else:
            handle_int(True)

    load()


def control_set(control: Control, args: Args):
    assert len(args.expressions) == 2
    assert args.expressions[0].__class__ == Symbol
    [arg1, arg2] = args.expressions

    arg2.codegen()
    reg2: int

    if arg2.__class__ == _Integer or arg2.__class__ == String:
        arg1.codegen()
        cg.add_instruction(Opcode.LDR,
                           cg.variable_register,
                           address=cg.data_pointer)
        if arg2.__class__ == String:
            cg.registers[cg.variable_register] = 2
    elif arg2.__class__ == Symbol:
        reg2 = cg.variable_register
        arg1.codegen()
        cg.add_instruction(Opcode.MOV, reg2,
                           reg2=cg.variable_register)
        cg.registers[reg2] = cg.registers[cg.variable_register]
    else:
        arg1.codegen()
        cg.add_instruction(Opcode.POP, cg.variable_register)
        cg.registers[cg.variable_register] = 2


def control_bin_ops(control: Control, args: Args):
    assert len(args.expressions) == 2
    [arg1, arg2] = args.expressions
    # callee saved registers
    save()

    [reg1, reg2] = handle_two_args(arg1, arg2)

    binary_opcode: Opcode = operator_bindings[control.control]

    cg.add_instruction(binary_opcode, reg1, reg2=reg2)
    cg.add_instruction(Opcode.MOV, cg.SP_REGISTER, reg1)
    load()
    # push result to stack
    cg.add_instruction(Opcode.PUSH, cg.SP_REGISTER)


parser = Lark.open("grammar.lark", rel_to=__file__, start="program")

transformer = create_transformer(
    sys.modules[__name__],
    LarkToASTTransformer(),
)


def parse_program(text: str) -> _Ast:
    tree = parser.parse(text)
    return transformer.transform(tree)
