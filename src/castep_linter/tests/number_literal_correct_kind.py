"""Test that a number literal has a dp (if real) or no dp if of any other type"""

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran.fortran_nodes import FortranNode
from castep_linter.fortran.fortran_raw_types import Fortran
from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.tests import castep_identifiers


def check_number_literal(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that a number literal has a dp (if real) or no dp if of any other type"""

    if not node.is_type(Fortran.NUMBER_LITERAL):
        err = "Expected number literal node"
        raise WrongNodeError(err)

    literal_string = node.raw.lower()

    if "_" in literal_string:
        value, kind = literal_string.split("_", maxsplit=1)

        if is_int(value):
            if kind not in castep_identifiers.INT_KINDS:
                error_log.add_msg("Error", node, f"Integer literal with {kind=}")
        elif kind not in castep_identifiers.DP_ALL:
            error_log.add_msg("Error", node, f"Float literal with {kind=}")

    elif "d" in literal_string:
        pass  # eg 5.0d4
    elif not is_int(literal_string):
        error_log.add_msg("Error", node, "Float literal without kind")


def is_int(x: str) -> bool:
    return not any(c in x.lower() for c in [".", "e", "d"])
