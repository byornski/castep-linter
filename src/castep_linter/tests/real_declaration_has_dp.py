"""Test that all real values are specified by real(kind=dp)"""
from tree_sitter import Node

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import ArgType, FType, VariableDeclaration, parser


@parser.node_type_check("variable_declaration")
def test_real_dp_declaration(node: Node, error_log: ErrorLogger) -> None:
    """Test that all real values are specified by real(kind=dp)"""

    var_decl = VariableDeclaration(node)

    if var_decl.type in [FType.REAL, FType.COMPLEX]:
        try:
            arg_type, arg_value = var_decl.get_arg(position=1, keyword="kind")
        except KeyError:
            error_log.add_msg("Error", node, "No kind specifier")
            return

        if arg_value.type == "number_literal":
            error_log.add_msg("Error", arg_value, "Numeric kind specifier")

        elif arg_value.type == "identifier" and arg_value.raw(lower=True) != "dp":
            error_log.add_msg("Warning", arg_value, "Invalid kind specifier")

        elif arg_type is ArgType.POSITION:
            error_log.add_msg("Info", arg_value, "Kind specified without keyword")
