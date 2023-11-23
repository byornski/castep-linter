"""Test that a call of complex(x) has a dp"""
from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import CallExpression
from castep_linter.fortran.fortran_node import Fortran, FortranNode, WrongNodeError
from castep_linter.tests import castep_identifiers


def check_complex_has_dp(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that a call of complex(x) has a dp"""

    if not node.is_type(Fortran.CALL_EXPRESSION):
        err = "Expected variable declaration node"
        raise WrongNodeError(err)

    call_expr = CallExpression(node)

    if call_expr.name == castep_identifiers.CMPLX:
        try:
            _, arg_value = call_expr.get_arg(position=3, keyword=castep_identifiers.KIND)
        except KeyError:
            error_log.add_msg("Error", node, "No kind specifier in complex intrinsic")
            return

        if arg_value.raw.lower() not in castep_identifiers.DP_ALL:
            error_log.add_msg("Error", node, "Invalid kind specifier in complex intrinsic")
