"""Test that all real values are specified by real(kind=dp)"""

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import ArgType, FType, VariableDeclaration
from castep_linter.fortran.fortran_node import Fortran, FortranNode, WrongNodeError
from castep_linter.fortran.identifier import Identifier
from castep_linter.tests import castep_identifiers


def check_real_dp_declaration(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that all real values are specified by real(kind=dp)"""

    if not node.is_type(Fortran.VARIABLE_DECLARATION):
        err = "Expected variable declaration node"
        raise WrongNodeError(err)

    var_decl = VariableDeclaration(node)

    if var_decl.type not in [FType.REAL, FType.COMPLEX]:
        return

    try:
        arg_type, arg_value = var_decl.get_arg(position=1, keyword=Identifier("kind"))
    except KeyError:
        error_log.add_msg("Error", node, "No kind specifier")
        return

    if arg_value.ftype == Fortran.NUMBER_LITERAL:
        error_log.add_msg("Error", arg_value, "Numeric kind specifier")

    elif (
        arg_value.ftype == Fortran.IDENTIFIER
        and Identifier.from_node(arg_value) not in castep_identifiers.DP_ALL
    ):
        error_log.add_msg("Warning", arg_value, "Invalid kind specifier")

    elif arg_type is ArgType.POSITION:
        error_log.add_msg("Info", arg_value, "Kind specified without keyword")
