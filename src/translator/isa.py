from abc import ABC
from enum import Enum
from pprint import pprint
from typing import Optional


class Opcode(str, Enum):
    LDR = "load"
    STR = "store"
    ILDR = "load from reg"
    ADD = "add"
    SUB = "substract"
    MOD = "mod"
    CMP = "compare"
    JMP = "jump"
    JZ = "jump if zero"
    PUSH = "push"
    POP = "pop"
    MOV = "move"

    def __str__(self):
        return str(self.value)


class ControlEnum(str, Enum):
    EQ = "=="
    SUB = "-"
    PLUS = "+"
    MOD = "%"
    SET = "set"
    READ = "read"
    PRINT = "print"

    def __str__(self):
        return str(self.value)


operator_bindings: dict = {
    ControlEnum.EQ: Opcode.CMP,
    ControlEnum.SUB: Opcode.SUB,
    ControlEnum.PLUS: Opcode.ADD,
    ControlEnum.MOD: Opcode.MOD
}


class Codegen(ABC):
    variable_register: str
    data_pointer: int
    NAMED_DATA_OFFSET: int = 128
    registers: list[int] = [0 for i in range(1, 9)]
    AC_REGISTER, S_REGISTER_1, S_REGISTER_2, SP_REGISTER = 10, 11, 12, 13
    CONTROL_BIT_MAPPING, INPUT_MAPPING, OUTPUT_MAPPING = 512, 513, 514
    dynamic_str_ptr: int = 256
    variables: dict = {}

    instructions: list[dict] = []
    data_memory: list[dict] = []
    named_data_memory: list[dict] = []

    def find_variable_reg(self, name: str):
        if name not in self.variables:
            for num, reg in enumerate(self.registers):
                if reg == 0:
                    self.registers[num] = 1
                    self.variables[name] = {
                        "value": "uninitialized", "register": num}
                    self.variable_register = num
                    break

        else:
            self.variable_register = self.variables[name]["register"]

    def add_instruction(self, opcode: Opcode, reg1: Optional[str] = None,
                        reg2: Optional[str] = None, address: Optional[int] = None):
        instr: dict = {"opcode": opcode, "reg1": reg1,
                       "reg2": reg2, "address": address}
        self.instructions.append(instr)

    def add_memory(self, data: str | int, annotation: str):
        memory_entry: dict = {"value": data, "annotation": annotation}
        self.data_memory.append(memory_entry)

    def add_named_memory(self, data: Optional[int] = None):
        named_memory_entry: dict
        if data is None:
            named_memory_entry = {
                "value": self.NAMED_DATA_OFFSET + len(self.data_memory),
                "annotation": "string pointer"}
        else:
            named_memory_entry = {
                "value": data,
                "annotation": "number"}
        self.data_pointer = len(self.named_data_memory)
        self.named_data_memory.append(named_memory_entry)

    def stat(self):
        first_array = self.named_data_memory[:]
        second_array = self.data_memory

        padding_length = max(0, self.NAMED_DATA_OFFSET - len(first_array))
        [{}] * padding_length

        # self.named_data_memory = first_array + padding + second_array # noqa: ERA001
        self.named_data_memory = first_array + second_array
        print("Instruction memory")

        for num, ins in enumerate(self.instructions):
            print("{}: {} r{} {}".format(num, ins["opcode"].name, ins["reg1"],
                  ins["address"] if ins["reg2"] is None else ins["reg2"]).replace("None", ""))

        print("Data memory")
        pprint(self.named_data_memory)


cg = Codegen()
