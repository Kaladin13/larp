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
    IJMP = "jump from reg"
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
    RETURN = "ret"

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
    AC_REGISTER, S_REGISTER_1, S_REGISTER_2, SP_REGISTER, R_REGISTER = 10, 11, 12, 13, 16
    CONTROL_BIT_MAPPING, INPUT_MAPPING, OUTPUT_MAPPING = 512, 513, 514
    dynamic_str_ptr: int = 256
    variables: dict = {}
    functions: dict = {}
    ret_value: int = 1

    is_first_call: bool = True

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

    def define_fun(self, name: str, arg1_name: str, arg2_name: str):
        self.functions[name] = {"address": len(self.instructions),
                                "arg1": arg1_name,
                                "arg2": arg2_name}
        self.variables[arg1_name] = {"register": 14}
        self.variables[arg2_name] = {"register": 15}

    def add_mapping(self, name: str):
        res = self.functions[name]
        return [14, 15, res["address"]]

    def get_ip(self):
        return len(self.instructions)

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

    def stat(self, debug_print=False):
        first_array = self.named_data_memory[:]
        second_array = self.data_memory

        padding_length = max(0, self.NAMED_DATA_OFFSET - len(first_array))
        padding = [{}] * padding_length

        if debug_print:
            self.named_data_memory = first_array + padding + second_array

        self.named_data_memory = first_array + second_array
        self.instructions[0]["address"] = self.ret_value

        if debug_print:
            print("Instruction memory")

            for num, ins in enumerate(self.instructions):
                if ins["reg1"] is None:
                    print("{}: {} {}".format(
                        num, ins["opcode"].name, ins["address"]))
                elif ins["address"] is None and ins["reg2"] is None:
                    print("{}: {} r{}".format(
                        num, ins["opcode"].name, ins["reg1"]))
                else:
                    print("{}: {} r{} {}".format(num, ins["opcode"].name, ins["reg1"],
                                                 ins["address"] if ins["reg2"] is None else ("r" + str(ins["reg2"])))
                          .replace("None", ""))

            print("Data memory")
            pprint(self.named_data_memory)

        ins_memory = []

        for d in self.instructions:
            # Use a list comprehension to filter out keys with None values
            a = {key: value for key, value in d.items() if value is not None}
            a["opcode"] = a["opcode"].name
            ins_memory.append(a)

        for num, ins in enumerate(ins_memory):
            ins_memory[num]["index"] = num

        for num, ins in enumerate(self.data_memory):
            self.data_memory[num]["index"] = num

        return {"instruction_memory": ins_memory,
                  "data_memory": self.data_memory}


cg = Codegen()
