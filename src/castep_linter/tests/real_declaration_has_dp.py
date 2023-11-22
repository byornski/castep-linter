"""Test that all real values are specified by real(kind=dp)"""
from tree_sitter import Node
from ..fortran.errors import ErrorLogger

from ..fortran import parser


def test_real_dp_declaration(node: Node, error_log: ErrorLogger) -> None:
    """Test that all real values are specified by real(kind=dp)"""
    assert parser.node_of_type(node, "variable_declaration")

    var_decl = parser.VariableDeclaration(node)

    if var_decl.type in [parser.FType.REAL, parser.FType.COMPLEX]:

        try:
            arg_type, arg_value = var_decl.get_arg(position=1, keyword="kind")
        except KeyError:
            error_log.add_msg('Error', node, "No kind specifier")
            return

        if arg_value.type == "number_literal":
            error_log.add_msg('Error', arg_value, "Numeric kind specifier")

        elif arg_value.type == "identifier" and arg_value.raw(lower=True) != "dp":
            error_log.add_msg('Warning', arg_value, "Invalid kind specifier")

        elif arg_type is parser.ArgType.POSITION:
            error_log.add_msg('Info', arg_value, "Kind specified without keyword")
