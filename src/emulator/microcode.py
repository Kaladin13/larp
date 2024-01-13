
from dataclasses import dataclass

from .datapath import DataPath
from .elements import ALU_OP

current_command: dict


@dataclass
class Microcode:
    latch_left_reg: bool = False
    latch_right_reg: bool = False
    sel_reg_demux_left: bool = False
    sel_reg_demux_right: bool = False
    alu_op: bool = False
    lsu_load: bool = False
    latch_pc: bool = False
    push: bool = False
    is_jump: bool = False
    is_jumpz: bool = False
    pop: bool = False
    fetch_instruction: bool = False
    latch_ir: bool = False
    ir_operand: bool = False
    latch_lsu_mux: bool = False
    lsu_store: bool = False
    latch_alu_data: bool = False
    latch_pc_summator: bool = False
    latch_pc_mux: bool = False

    branching: int = None

    def execute(self, datapath: DataPath) -> int | None:
        global current_command

        if self.branching is not None:
            return self.branching

        if self.latch_ir:
            current_command = datapath.latch_ir()
            return mc_map[1][current_command["opcode"]]

        if self.is_jump:
            datapath.pc_reg.val = current_command["address"]

        if self.is_jumpz:
            if datapath.registers.get(current_command["reg1"]):
                datapath.pc_reg.val = current_command["address"]

        if self.latch_left_reg:
            datapath.latch_left_reg(self.latch_left_reg)

        if self.latch_right_reg:
            datapath.latch_right_reg(self.latch_right_reg)

        if self.sel_reg_demux_left:
            datapath.sel_reg_demux_left(self.sel_reg_demux_left)

        if self.sel_reg_demux_right:
            datapath.sel_reg_demux_right(self.sel_reg_demux_right)

        if self.alu_op:
            datapath.alu_op(self.alu_op)

        if self.lsu_load:
            datapath.lsu_load()

        if self.latch_pc:
            datapath.latch_pc()

        if self.fetch_instruction:
            datapath.fetch_instruction()

        if self.ir_operand:
            datapath.ir_operand()

        if self.latch_lsu_mux:
            datapath.latch_lsu_mux(self.latch_lsu_mux)

        if self.lsu_store:
            datapath.lsu_store()

        if self.latch_alu_data:
            datapath.latch_alu_data(self.latch_alu_data,
                                    current_command["reg1"])

        if self.latch_pc_summator:
            datapath.latch_pc_summator()

        if self.latch_pc_mux:
            datapath.latch_pc_mux(self.latch_pc_mux)
            return None
        return None


start_commands = [
    Microcode(latch_pc=True),
    Microcode(fetch_instruction=True),
    Microcode(latch_ir=True)
]

end_commands = [
    Microcode(latch_pc_summator=True),
    Microcode(latch_pc_mux=2),
    Microcode(branching=0)
]

add_opp_comand = [
    Microcode(latch_left_reg=True,
              latch_right_reg=True),
    Microcode(sel_reg_demux_left=2,
              sel_reg_demux_right=1),
    Microcode(alu_op=ALU_OP.ADD),
    Microcode(latch_alu_data=2),
    Microcode(branching=55)
]

sub_opp_comand = [
    Microcode(latch_left_reg=True,
              latch_right_reg=True),
    Microcode(sel_reg_demux_left=2,
              sel_reg_demux_right=1),
    Microcode(alu_op=ALU_OP.SUB),
    Microcode(latch_alu_data=2),
    Microcode(branching=55)
]

mod_opp_comand = [
    Microcode(latch_left_reg=True,
              latch_right_reg=True),
    Microcode(sel_reg_demux_left=2,
              sel_reg_demux_right=1),
    Microcode(alu_op=ALU_OP.MOD),
    Microcode(latch_alu_data=2),
    Microcode(branching=55)
]

cmp_opp_comand = [
    Microcode(latch_left_reg=True,
              latch_right_reg=True),
    Microcode(sel_reg_demux_left=2,
              sel_reg_demux_right=1),
    Microcode(alu_op=ALU_OP.CMP),
    Microcode(latch_alu_data=2),
    Microcode(branching=55)
]

store_command = [
    Microcode(latch_left_reg=True,
              latch_right_reg=True),
    Microcode(sel_reg_demux_left=1,
              sel_reg_demux_right=1),
    Microcode(latch_lsu_mux=2),
    Microcode(lsu_store=True),
    Microcode(branching=55)
]

load_command = [
    Microcode(ir_operand=True,
              latch_left_reg=True),
    Microcode(latch_lsu_mux=1, sel_reg_demux_left=1),
    Microcode(lsu_load=True),
    Microcode(latch_alu_data=1),
    Microcode(branching=55)
]

mov_command = [
    Microcode(latch_right_reg=True),
    Microcode(sel_reg_demux_right=2),
    Microcode(alu_op=-1),
    Microcode(latch_alu_data=2),
    Microcode(branching=55)
]

ildr_command = [
    Microcode(latch_left_reg=True,
              latch_right_reg=True),
    Microcode(sel_reg_demux_left=1,
              sel_reg_demux_right=1),
    Microcode(latch_lsu_mux=2),
    Microcode(lsu_load=True),
    Microcode(latch_alu_data=1),
    Microcode(branching=55)
]

push_command = [
    Microcode(latch_left_reg=True),
    Microcode(sel_reg_demux_left=1),
    Microcode(push=True),
    Microcode(branching=55)
]

pop_command = [
    Microcode(pop=True),
    Microcode(latch_alu_data=1),
    Microcode(branching=55)
]

jmp_command = [
    Microcode(is_jump=True),
    Microcode(branching=55)
]

jz_command = [
    Microcode(is_jumpz=True),
    Microcode(branching=55)
]

ijmp_command = []


def concatenate_arrays_and_map(*arrays_with_names):
    concatenated_array = []
    array_mapping = {}

    current_index = 0
    for array_name, array in arrays_with_names:
        array_mapping[array_name] = current_index
        concatenated_array.extend(array)
        current_index += len(array)

    return concatenated_array, array_mapping


start_mc = ("start", start_commands)
end_mc = ("end", end_commands)
add_ops_mc = ("ADD", add_opp_comand)
sub_ops_mc = ("SUB", sub_opp_comand)
mod_ops_mc = ("MOD", mod_opp_comand)
cmp_ops_mc = ("CMP", cmp_opp_comand)
jmp_comn = ("JMP", jmp_command)
jz_com = ("JZ", jz_command)
store_mc = ("STR", store_command)
load_mc = ("LDR", load_command)
mov_mc = ("MOV", mov_command)
ildr_mc = ("ILDR", ildr_command)
push_mc = ("PUSH", push_command)
pop_mc = ("POP", pop_command)

mc_map = concatenate_arrays_and_map(start_mc,
                                    add_ops_mc,
                                    sub_ops_mc,
                                    mod_ops_mc,
                                    cmp_ops_mc,
                                    store_mc,
                                    load_mc,
                                    mov_mc,
                                    ildr_mc,
                                    push_mc,
                                    pop_mc,
                                    jmp_comn,
                                    jz_com,
                                    end_mc)

# pprint(mc_map)
