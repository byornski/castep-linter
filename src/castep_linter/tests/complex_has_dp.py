"""Test that a call of complex(x) has a dp"""
from tree_sitter import Node

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import CallExpression, parser


@parser.node_type_check("call_expression")
def test_complex_has_dp(node: Node, error_log: ErrorLogger) -> None:
    """Test that a call of complex(x) has a dp"""

    call_expr = CallExpression(node)

    if call_expr.name == "cmplx":
        try:
            _, arg_value = call_expr.get_arg(position=3, keyword="kind")
        except KeyError:
            error_log.add_msg("Error", node, "No kind specifier in complex intrinsic")
            return

        if arg_value.raw(lower=True) != "dp":
            error_log.add_msg("Error", node, "Invalid kind specifier in complex intrinsic")
