"""Test that a call of complex(x) has a dp"""
from tree_sitter import Node
from ..fortran.errors import ErrorLogger
from ..fortran import parser


def test_complex_has_dp(node: Node, error_log: ErrorLogger) -> None:
    """Test that a call of complex(x) has a dp"""
    assert parser.node_of_type(node, "call_expression")

    call_expr = parser.CallExpression(node)

    if call_expr.name == "cmplx":
        try:
            _, arg_value = call_expr.get_arg(position=3, keyword="kind")
        except KeyError:
            err = "No kind specifier in complex intrinsic"
            error_log.add_msg('Error', node, err)
            return

        if parser.get_code(arg_value, lower=True) != "dp":
            err = "Invalid kind specifier in complex intrinsic"
            error_log.add_msg('Error', node, err)
