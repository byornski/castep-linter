"""Test that allocate stat is used and checked"""
from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import CallExpression
from castep_linter.fortran.fortran_node import Fortran, FortranNode, WrongNodeError
from castep_linter.fortran.identifier import Identifier
from castep_linter.tests import castep_identifiers


def check_allocate_has_stat(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that allocate stat is used and checked"""

    if not node.is_type(Fortran.CALL_EXPRESSION):
        err = "Expected variable declaration node"
        raise WrongNodeError(err)

    routine = CallExpression(node)

    if routine.name is None:
        return

    # Check this is actually an allocate statement
    if routine.name != castep_identifiers.ALLOCATE:
        return

    # First get the stat variable for this allocate statement
    try:
        _, stat_variable_node = routine.get_arg(keyword=castep_identifiers.STAT)
    except KeyError:
        err = "No stat on allocate statement"
        error_log.add_msg("Warning", node, err)
        return

    stat_variable = Identifier.from_node(stat_variable_node)

    # Find the next non-comment line
    next_node = node.next_named_sibling()
    while next_node and next_node.is_type(Fortran.COMMENT):
        next_node = next_node.next_named_sibling()

    # Check if that uses the stat variable
    if next_node and next_node.is_type(Fortran.IF_STMT):
        try:
            relational_expr = next_node.get(Fortran.PAREN_EXPRESSION).get(Fortran.RELATIONAL_EXPR)
        except KeyError:
            error_log.add_msg("Error", stat_variable_node, "Allocate status not checked")
            return

        lhs, rhs = relational_expr.split()

        if lhs.is_type(Fortran.IDENTIFIER) and Identifier.from_node(lhs) == stat_variable:
            return

        if rhs.is_type(Fortran.IDENTIFIER) and Identifier.from_node(rhs) == stat_variable:
            return

    error_log.add_msg("Error", stat_variable_node, "Allocate status not checked")
