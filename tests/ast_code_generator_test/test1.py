from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

def main():
        datawid = vast.Parameter('DATAWID', vast.Rvalue(vast.IntConst('32')))
        params = vast.Paramlist([datawid])

        clk = vast.Ioport(vast.Input('CLK'))
        rst = vast.Ioport(vast.Input('RST'))
        width = vast.Width(vast.IntConst('7'), vast.IntConst('0'))
        led = vast.Ioport(vast.Output('led', width=width))
        ports = vast.Portlist([clk, rst, led])

        width = vast.Width(
            vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('1')),
            vast.IntConst('0')
        )
        count = vast.Wire('count', width=width)

        assign = vast.Assign(
            vast.Lvalue(vast.Identifier('led')),
            vast.Rvalue(
                vast.Partselect(
                    vast.Identifier('count'),
                    vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('1')),
                    vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('8'))
                )
            )
        )

        sens = vast.Sens(vast.Identifier('CLK'), type='posedge')
        senslist = vast.SensList([sens])

        assign_count_true = vast.NonblockingSubstitution(
            vast.Lvalue(vast.Identifier('count')),
            vast.Rvalue(vast.IntConst('0'))
        )
        if0_true = vast.Block([assign_count_true])

        count_plus_1 = vast.Plus(vast.Identifier('count'), vast.IntConst('1'))
        assign_count_false = vast.NonblockingSubstitution(
            vast.Lvalue(vast.Identifier('count')),
            vast.Rvalue(count_plus_1)
        )
        if0_false = vast.Block([assign_count_false])

        if0 = vast.IfStatement(vast.Identifier('RST'), if0_true, if0_false)
        statement = vast.Block([if0])

        always = vast.Always(senslist, statement)

        items = [count, assign, always]
        ast = vast.ModuleDef("top", params, ports, items)

        codegen = ASTCodeGenerator()
        rslt = codegen.visit(ast)
        with open("output1.v", "w") as f:
            f.write(rslt)
if __name__ == '__main__':
        main()