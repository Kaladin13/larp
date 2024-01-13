from pprint import pprint

from src.emulator.datapath import DataPath
from src.emulator.microcode import mc_map


class CU:
    datapath: DataPath
    mc: any
    mc_count: int = 0

    def __init__(self, inst_data, mem_data, input_bg):
        self.mc = mc_map[0]
        self.datapath = DataPath(inst_data, mem_data, input_bg)

    def run(self):
        while self.datapath.pc_reg.val != len(self.datapath.instructions.instructions):
            mc_instr = self.mc[self.mc_count]
            res = mc_instr.execute(self.datapath)
            if res is not None:
                self.mc_count = res
            else:
                self.mc_count += 1

        pprint(self.datapath.lsu.io.output_buffer)
