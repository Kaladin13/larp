from abc import ABC
from pprint import pprint

from src.config.config import IOMemoryMapping, Opcode

from .io import IO


def get_param(name: str, inst: dict):
    return inst[name] if name in inst else None


class ControlUnit(ABC):
    registers: list[str | int] = [0] * 32
    pc: int = 0
    stack: list[str | int] = []
    io: IO
    instructions: list[dict]
    data: list[dict]

    def __init__(self, inst_data, mem_data, input_bg) -> None:
        self.instructions = inst_data
        self.io = IO(input_bg)

        long_data = []
        for i in range(1024):
            long_data.append({})
        long_data[:len(mem_data)] = mem_data
        self.data = long_data

    def tick(self):
        instuction = self.instructions[self.pc]
        opcode: str = instuction["opcode"]

        r1: int = get_param("reg1", instuction)
        r2: int = get_param("reg2", instuction)
        address: int = get_param("address", instuction)

        match opcode:
            case Opcode.MOV.name:
                self.registers[r1] = self.registers[r2]
            case Opcode.ADD.name:
                self.registers[r1] += self.registers[r2]
            case Opcode.SUB.name:
                self.registers[r1] -= self.registers[r2]
            case Opcode.MOD.name:
                self.registers[r1] %= self.registers[r2]
            case Opcode.CMP.name:
                self.registers[r1] = int(
                    self.registers[r1] == self.registers[r2])
            case Opcode.JMP.name:
                self.pc = address - 1
            case Opcode.JZ.name:
                if self.registers[r1] == 0:
                    self.pc = address - 1
            case Opcode.IJMP.name:
                self.pc = self.registers[r1] - 1
            case Opcode.POP.name:
                self.registers[r1] = self.stack.pop()
            case Opcode.PUSH.name:
                self.stack.append(self.registers[r1])
            case Opcode.LDR.name:
                if address in [v.value for v in IOMemoryMapping]:
                    self.registers[r1] = self.io.handle_load(address)
                else:
                    self.registers[r1] = self.data[address]["value"]
            case Opcode.STR.name:
                if self.registers[r2] in [v.value for v in IOMemoryMapping]:
                    self.io.handle_store(self.registers[r1])
                else:
                    self.data[self.registers[r2]]["value"] = self.registers[r1]
            case Opcode.ILDR.name:
                if self.registers[r2] in [v.value for v in IOMemoryMapping]:
                    self.registers[r1] = self.io.handle_load(
                        r1, self.registers[r2])
                else:
                    self.registers[r1] = self.data[self.registers[r2]]["value"]
            case _:
                print("Error!")

        self.pc += 1

    def dump(self):
        print("pc " + str(self.pc - 1))
        for index, value in enumerate(self.registers):
            if value != 0:
                print(f"r{index}: {value} |", end=" ")
        print("\n")

    def start(self):
        while self.pc != len(self.instructions):
            self.tick()
            # self.dump() :noq ERA001
        self.stat()

    def stat(self):
        print("Output buffer:")
        print("".join(str(x)
              for x in self.io.output_buffer).replace("0x00", "\n"))
        print("\nLeft input buffer")
        pprint(self.io.input_buffer)
        print("\nLeft stack")
        pprint(self.stack)
        print("\nEnd pc")
        pprint(self.pc)
