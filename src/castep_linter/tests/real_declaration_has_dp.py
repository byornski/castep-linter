"""Test that all real values are specified by real(kind=dp)"""

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran.fortran_nodes import (
    FortranNode,
    FortranVariableDeclaration,
)
from castep_linter.fortran.fortran_nodes.argument_types import PositionalArgument
from castep_linter.fortran.fortran_raw_types import Fortran, FType
from castep_linter.fortran.identifier import Identifier
from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.tests import castep_identifiers


def check_real_dp_declaration(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that all real values are specified by real(kind=dp)"""

    if not isinstance(node, FortranVariableDeclaration):
        err = "Expected variable declaration node"
        raise WrongNodeError(err)

    if node.var_type not in [FType.REAL, FType.COMPLEX]:
        return

    try:
        arg = node.get_arg(position=1, keyword=Identifier("kind"))
    except KeyError:
        error_log.add_msg("Error", node, "No kind specifier")
        return

    if arg.value.ftype == Fortran.NUMBER_LITERAL:
        error_log.add_msg("Error", arg.value, "Numeric kind specifier")

    elif (
        arg.value.ftype == Fortran.IDENTIFIER
        and Identifier.from_node(arg.value) not in castep_identifiers.DP_ALL
    ):
        error_log.add_msg("Warning", arg.value, "Invalid kind specifier")

    elif isinstance(arg, PositionalArgument):
        error_log.add_msg("Info", arg.value, "Kind specified without keyword")
