from __future__ import absolute_import
from __future__ import print_function
import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

def main():
    # Define ports
    clk = vast.Ioport(vast.Input('CLK'))
    rst = vast.Ioport(vast.Input('RST'))
    en = vast.Ioport(vast.Input('EN'))
    width = vast.Width(vast.IntConst('3'), vast.IntConst('0'))
    count = vast.Ioport(vast.Output('COUNT', width=width))
    ports = vast.Portlist([clk, rst, en, count])

    # Define register
    reg_width = vast.Width(vast.IntConst('3'), vast.IntConst('0'))
    count_reg = vast.Reg('count_reg', width=reg_width)

    # Continuous assignment: output = register
    assign = vast.Assign(
        vast.Lvalue(vast.Identifier('COUNT')),
        vast.Rvalue(vast.Identifier('count_reg'))
    )

    # Sequential logic
    sens = vast.Sens(vast.Identifier('CLK'), type='posedge')
    senslist = vast.SensList([sens])

    # Reset branch: count_reg <= 0
    reset_assign = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('count_reg')),
        vast.Rvalue(vast.IntConst('0'))
    )
    reset_block = vast.Block([reset_assign])

    # Enable branch: count_reg <= count_reg + 1
    increment = vast.Plus(vast.Identifier('count_reg'), vast.IntConst('1'))
    enable_assign = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('count_reg')),
        vast.Rvalue(increment)
    )
    enable_block = vast.Block([enable_assign])

    # If statement: if (RST) reset else if (EN) increment
    if_en = vast.IfStatement(
        vast.Identifier('EN'),
        enable_block,
        None
    )
    if_rst = vast.IfStatement(
        vast.Identifier('RST'),
        reset_block,
        vast.Block([if_en])
    )
    always = vast.Always(senslist, vast.Block([if_rst]))

    # Module items
    items = [count_reg, assign, always]

    # Module definition
    ast = vast.ModuleDef("counter_4bit", None, ports, items)

    # Generate Verilog code
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    with open("counter_4bit.v", "w") as f:
        f.write(rslt)

if __name__ == '__main__':
    main()