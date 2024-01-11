from abc import ABC

from src.config.config import IOMemoryMapping


class IO(ABC):
    input_buffer: list[str]
    output_buffer: list[str]

    def __init__(self, input_bf) -> None:
        self.input_buffer = input_bf
        self.output_buffer = []

    def handle_load(self, address) -> str | int:
        if address == IOMemoryMapping.CONTROL_BIT_MAPPING.value:
            return int(len(self.input_buffer) != 0)
        if address == IOMemoryMapping.INPUT_MAPPING.value:
            return self.input_buffer.pop(0)
        return None

    def handle_store(self, char):
        self.output_buffer.append(char)
