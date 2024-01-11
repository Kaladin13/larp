import json
import sys
from pathlib import Path

from .control_unit import ControlUnit


def say_hi_em() -> None:
    print("Hello dear emulator!")


def parse_input(input_fl, buffer):
    conf = json.load(input_fl)
    buf = json.load(buffer)

    return ControlUnit(conf["instruction_memory"],
                       conf["data_memory"],
                       buf)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Invalid arguments. Usage: emulator <memory_file> <input_buffer_file> <output_file>")
        sys.exit(1)

    memory_file = Path(sys.argv[1])
    buffer_file = Path(sys.argv[2])
    output_file = Path(sys.argv[3])

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sys.argv[1], encoding="utf-8") as file:
        with open(sys.argv[2], encoding="utf-8") as buffer:
            with open(sys.argv[3], "w", encoding="utf-8") as output:
                cpu = parse_input(file, buffer)
                cpu.start()
