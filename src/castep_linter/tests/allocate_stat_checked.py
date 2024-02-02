"""Test that allocate stat is used and checked"""

import logging

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran.fortran_nodes import (
    FortranCallExpression,
    FortranNode,
)
from castep_linter.fortran.fortran_raw_types import Fortran
from castep_linter.fortran.identifier import Identifier
from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.tests import castep_identifiers


def check_allocate_error_names(
    node: FortranNode,
    error_log: ErrorLogger,
    variable_name: Identifier,
    subroutine_name: Identifier,
):
    """Check that an allocation error is correctly handled"""
    if not node.is_type(Fortran.IF_STMT):
        err = f"Expected if statement but got {node.type}"
        raise WrongNodeError(err)

    sub_node = node.get(Fortran.SUBROUTINE_CALL)
    if not isinstance(sub_node, FortranCallExpression):
        err = f"Expected call expression but got {node.type}"
        raise WrongNodeError(err)

    sub_call = sub_node

    if sub_call.name not in castep_identifiers.IO_ABORT_ANY:
        error_log.add_msg("Error", sub_node, "Allocation failure does not raise an error")
        return

    # Only do extra checking on io_allocate_abort -- ignore old io_abort style errors
    if sub_call.name != castep_identifiers.IO_ALLOCATE_ABORT:
        return

    error_array_node = sub_call.get_arg(position=1, keyword=castep_identifiers.IO_AA_ARRAY).value
    error_routine_node = sub_call.get_arg(
        position=2, keyword=castep_identifiers.IO_AA_ROUTINE
    ).value

    try:
        error_array = Identifier(error_array_node.parse_string_literal())
    except WrongNodeError:
        logging.warning("Failed to properly parse array name from: %s", node.raw)
        error_array = None

    try:
        error_routine = Identifier(error_routine_node.parse_string_literal())
    except WrongNodeError:
        logging.warning("Failed to properly parse subroutine name from: %s", node.raw)
        error_routine = None

    if not error_array == variable_name:
        err = f"Wrong array name used in io_allocate_abort. Expected: {variable_name}"
        error_log.add_msg("Error", error_array_node, err)

    if not error_routine == subroutine_name:
        err = f"Wrong subroutine name used in io_allocate_abort. Expected: {subroutine_name}"
        error_log.add_msg("Error", error_routine_node, err)


def variable_name_from_allocate(routine: FortranCallExpression):
    """Get the array from allocate statement"""
    allocate_var_node = routine.get_arg(position=1, keyword=castep_identifiers.ARRAY).value

    if routine.node.type == "call_expression":
        try:
            array_name_node = allocate_var_node.children[0]
        except IndexError:
            return ""
    else:
        array_name_node = allocate_var_node.get(Fortran.IDENTIFIER)

    try:
        return Identifier.from_node(array_name_node)
    except KeyError as exc:
        msg = "Could not identify variable name in allocate statement"
        routine.print_tree()
        raise ValueError(msg) from exc


def check_allocate_has_stat(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that allocate stat is used and checked"""

    if not isinstance(node, FortranCallExpression):
        err = f"Expected call expression but got {node.type}"
        raise WrongNodeError(err)

    routine = node

    if routine.name is None:
        return

    # Check this is actually an allocate statement
    if routine.name != castep_identifiers.ALLOCATE:
        return

    # First get the stat variable for this allocate statement
    try:
        stat_variable_node = routine.get_arg(keyword=castep_identifiers.STAT).value
    except KeyError:
        error_log.add_msg("Warning", node, "No stat on allocate statement")
        return

    # allocate_var_identifier = variable_name_from_allocate(routine)

    stat_variable = Identifier.from_node(stat_variable_node)

    # Find the next non-comment line
    next_node = node.next_named_sibling()
    while next_node and next_node.is_type(Fortran.COMMENT):
        next_node = next_node.next_named_sibling()

    # Check if that uses the stat variable
    stat_checked = False
    if next_node and next_node.is_type(Fortran.IF_STMT):
        try:
            relational_expr = next_node.get(Fortran.PAREN_EXPRESSION).get(Fortran.RELATIONAL_EXPR)
        except KeyError:
            error_log.add_msg("Error", stat_variable_node, "Allocate status not checked")
            return

        lhs, rhs = relational_expr.split()

        if lhs.is_type(Fortran.IDENTIFIER) and Identifier.from_node(lhs) == stat_variable:
            stat_checked = True

        if rhs.is_type(Fortran.IDENTIFIER) and Identifier.from_node(rhs) == stat_variable:
            stat_checked = True

    if not next_node or not stat_checked:
        error_log.add_msg("Error", stat_variable_node, "Allocate status not checked")
        return

    # context_name = node.get_context_identifier()
    # check_allocate_error_names(next_node, error_log, allocate_var_identifier, context_name)
