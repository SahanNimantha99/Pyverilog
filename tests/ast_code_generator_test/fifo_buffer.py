from __future__ import absolute_import
from __future__ import print_function
import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

def main():
    # Parameters
    width_param = vast.Parameter('WIDTH', vast.Rvalue(vast.IntConst('8')))
    depth_param = vast.Parameter('DEPTH', vast.Rvalue(vast.IntConst('16')))
    params = vast.Paramlist([width_param, depth_param])

    # Ports
    clk = vast.Ioport(vast.Input('CLK'))
    rst = vast.Ioport(vast.Input('RST'))
    wr_en = vast.Ioport(vast.Input('WR_EN'))
    rd_en = vast.Ioport(vast.Input('RD_EN'))
    data_width = vast.Width(vast.Minus(vast.Identifier('WIDTH'), vast.IntConst('1')), vast.IntConst('0'))
    din = vast.Ioport(vast.Input('DIN', width=data_width))
    dout = vast.Ioport(vast.Output('DOUT', width=data_width))
    empty = vast.Ioport(vast.Output('EMPTY'))
    full = vast.Ioport(vast.Output('FULL'))
    ports = vast.Portlist([clk, rst, wr_en, rd_en, din, dout, empty, full])

    # Internal signals
    addr_width = vast.Width(vast.IntConst('3'), vast.IntConst('0'))  # log2(DEPTH=16) = 4
    wr_ptr = vast.Reg('wr_ptr', width=addr_width)
    rd_ptr = vast.Reg('rd_ptr', width=addr_width)
    mem = vast.Reg('mem', width=data_width, dimensions=vast.Dimensions([vast.Length(vast.IntConst('15'), vast.IntConst('0'))]))

    # Status signals
    empty_assign = vast.Assign(
        vast.Lvalue(vast.Identifier('EMPTY')),
        vast.Rvalue(vast.Eq(vast.Identifier('wr_ptr'), vast.Identifier('rd_ptr')))
    )
    full_assign = vast.Assign(
        vast.Lvalue(vast.Identifier('FULL')),
        vast.Rvalue(vast.Eq(
            vast.Partselect(vast.Identifier('wr_ptr'), vast.IntConst('3'), vast.IntConst('0')),
            vast.Partselect(vast.Identifier('rd_ptr'), vast.IntConst('3'), vast.IntConst('0'))
        ))
    )

    # Sequential logic
    sens = vast.Sens(vast.Identifier('CLK'), type='posedge')
    senslist = vast.SensList([sens])

    # Reset branch
    reset_wr_ptr = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('wr_ptr')),
        vast.Rvalue(vast.IntConst('0'))
    )
    reset_rd_ptr = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('rd_ptr')),
        vast.Rvalue(vast.IntConst('0'))
    )
    reset_block = vast.Block([reset_wr_ptr, reset_rd_ptr])

    # Write logic: if (WR_EN && !FULL) mem[wr_ptr] <= DIN; wr_ptr <= wr_ptr + 1;
    wr_cond = vast.Land(vast.Identifier('WR_EN'), vast.Unot(vast.Identifier('FULL')))
    mem_write = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Pointer(vast.Identifier('mem'), vast.Identifier('wr_ptr'))),
        vast.Rvalue(vast.Identifier('DIN'))
    )
    wr_ptr_inc = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('wr_ptr')),
        vast.Rvalue(vast.Plus(vast.Identifier('wr_ptr'), vast.IntConst('1')))
    )
    write_block = vast.Block([mem_write, wr_ptr_inc])
    if_write = vast.IfStatement(wr_cond, write_block, None)

    # Read logic: if (RD_EN && !EMPTY) DOUT <= mem[rd_ptr]; rd_ptr <= rd_ptr + 1;
    rd_cond = vast.Land(vast.Identifier('RD_EN'), vast.Unot(vast.Identifier('EMPTY')))
    dout_assign = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('DOUT')),
        vast.Rvalue(vast.Pointer(vast.Identifier('mem'), vast.Identifier('rd_ptr')))
    )
    rd_ptr_inc = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('rd_ptr')),
        vast.Rvalue(vast.Plus(vast.Identifier('rd_ptr'), vast.IntConst('1')))
    )
    read_block = vast.Block([dout_assign, rd_ptr_inc])
    if_read = vast.IfStatement(rd_cond, read_block, None)

    # Combine logic
    always = vast.Always(
        senslist,
        vast.Block([
            vast.IfStatement(vast.Identifier('RST'), reset_block, vast.Block([if_write, if_read]))
        ])
    )

    # Module items
    items = [wr_ptr, rd_ptr, mem, empty_assign, full_assign, always]

    # Module definition
    ast = vast.ModuleDef("fifo", params, ports, items)

    # Generate Verilog code
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    with open("fifo.v", "w") as f:
        f.write(rslt)

if __name__ == '__main__':
    main()