from abc import ABC

from .elements import ALU, DEMUX, MUX, InstuctionMemory, LoadStoreUnit, Register, Registers, Summator


class DataPath(ABC):
    pc: int = 0
    stack: list[str | int] = []
    lsu: LoadStoreUnit
    alu_data_result_mux = MUX()
    pc_mux = MUX()
    lsu_mux = MUX()
    alu = ALU()
    pc_summator = Summator()
    reg_left_demux = DEMUX()
    reg_right_demux = DEMUX()
    registers = Registers()
    instructions: InstuctionMemory
    pc_reg = Register()
    ir_reg = Register()

    def __init__(self, inst_data, mem_data, input_bg):
        self.instructions = InstuctionMemory(inst_data)

        long_data = []
        for i in range(1024):
            long_data.append({})
        long_data[:len(mem_data)] = mem_data

        self.lsu = LoadStoreUnit(long_data, input_bg)

    def latch_left_reg(self, reg_num):
        self.reg_left_demux.in_(
            self.registers.latch_left_reg_(reg_num))

    def latch_right_reg(self, reg_num):
        self.reg_right_demux.in_(
            self.registers.latch_right_reg_(reg_num))

    def sel_reg_demux_left(self, num):
        if num == 1:
            self.lsu.set_reg(self.reg_left_demux.sel_())
        elif num == 2:
            self.alu.set_right(self.reg_left_demux.sel_())

    def sel_reg_demux_right(self, num):
        if num == 1:
            self.lsu_mux.in_(2, self.reg_right_demux.sel_())
        if num == 2:
            self.alu.set_left(self.reg_right_demux.sel_())
        elif num == 3:
            self.pc_mux.in_(1, self.reg_right_demux.sel_())

    def alu_op(self, op):
        self.alu_data_result_mux.in_(
            2, self.alu.alu_op_(op)
        )

    def lsu_load(self):
        self.alu_data_result_mux.in_(
            1, self.lsu.load_()
        )

    def push(self):
        self.lsu.push()

    def pop(self):
        self.alu_data_result_mux.in_(
            1, self.lsu.pop()
        )

    def latch_pc(self):
        help_val = self.pc_reg.latch_reg_()
        self.pc_summator.set_val(help_val)
        self.instructions.set(help_val)

    def fetch_instruction(self):
        self.ir_reg.set(
            self.instructions.fetch_instruction_()
        )

    def latch_ir(self) -> dict:
        "The only return because we latch it to CU"
        return self.ir_reg.latch_reg_()

    def ir_operand(self):
        reg_v = self.ir_reg.latch_reg_()
        self.lsu_mux.in_(1, reg_v["address"])

    def latch_lsu_mux(self, num):
        self.lsu.set_address(
            self.lsu_mux.sel_(num)
        )

    def lsu_store(self):
        self.lsu.store_()

    def latch_alu_data(self, mux_num, reg_num):
        self.registers.set(
            reg_num,
            self.alu_data_result_mux.sel_(mux_num)
        )

    def latch_pc_summator(self):
        self.pc_mux.in_(
            2, self.pc_summator.latch_sum_()
        )

    def latch_pc_mux(self, num):
        self.pc_reg.set(
            self.pc_mux.sel_(num)
        )
