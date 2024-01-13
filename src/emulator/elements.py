import operator
from enum import Enum

from src.config.config import IOMemoryMapping

from .io import IO


class ALU_OP(Enum):
    ADD = operator.add
    SUB = operator.sub
    MOD = operator.mod
    CMP = operator.eq


class MUX:
    val: dict = {}

    def in_(self, name, val):
        self.val[name] = val

    def sel_(self, name):
        if name not in self.val:
            print("MUX error")
            exit(1)
        return self.val[name]


class Summator:
    val: int

    def set_val(self, val):
        self.val = val

    def latch_sum_(self):
        return self.val + 1


class DEMUX:
    val: any

    def in_(self, val):
        self.val = val

    def sel_(self):
        """
        We could emulate demux element by
        passing here all connected output objects and
        on sel signal just inject the value here,
        but this would cause a lot of side effects and
        generally it will be a bad code design
        """
        return self.val


class Registers:
    registers: list[str | int] = [0] * 32

    def get(self, num):
        return self.registers[num]

    def set(self, num, val):
        self.registers[num] = val

    def latch_left_reg_(self, num):
        return self.get(num)

    def latch_right_reg_(self, num):
        return self.get(num)


class Register:
    val: any = 0

    def set(self, val):
        self.val = val

    def latch_reg_(self):
        return self.val


class InstuctionMemory:
    instructions: list[dict]
    ind: int

    def __init__(self, inst):
        self.instructions = inst

    def set(self, val):
        self.ind = val

    def fetch_instruction_(self):
        return self.instructions[self.ind]


class LoadStoreUnit:
    stack: list[str | int] = []
    data: list[dict]
    io: IO
    address: int
    reg_value: str | int

    def __init__(self, data_memory, input_bg):
        self.data = data_memory
        self.io = IO(input_bg)

    def set_reg(self, reg):
        self.reg_value = reg

    def set_address(self, address):
        self.address = address

    def store_(self):
        if self.address in [v.value for v in IOMemoryMapping]:
            self.io.handle_store(self.reg_value)
        else:
            self.data[self.reg_value]["value"] = self.reg_value

    def load_(self):
        if self.address in [v.value for v in IOMemoryMapping]:
            return self.io.handle_load(self.address)
        else:
            return self.data[self.address]["value"]

    def push(self):
        self.stack.append(self.reg_value)

    def pop(self):
        return self.stack.pop()


class ALU:
    left_input: int = 0
    right_input: int = 0

    def set_left(self, val):
        self.left_input = val

    def set_right(self, val):
        self.right_input = val

    def alu_op_(self, op_type: ALU_OP):
        if op_type == -1:
            return self.left_input
        return op_type.value(self.left_input, self.right_input)
