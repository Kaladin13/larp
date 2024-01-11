from abc import ABC
from enum import Enum


class Opcode(str, Enum):
    LDR = "load"
    STR = "store"
    ILDR = "load from reg"
    ADD = "add"
    SUB = "substract"
    MOD = "mod"
    CMP = "compare"
    JMP = "jump"
    IJMP = "jump from reg"
    JZ = "jump if zero"
    PUSH = "push"
    POP = "pop"
    MOV = "move"

    def __str__(self):
        return str(self.value)


class IOMemoryMapping(Enum):
    CONTROL_BIT_MAPPING = 512
    INPUT_MAPPING = 513
    OUTPUT_MAPPING = 514
