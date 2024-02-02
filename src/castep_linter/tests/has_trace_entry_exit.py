"""Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran.fortran_nodes import (
    FortranCallExpression,
    FortranNode,
    FortranVariableDeclaration,
)
from castep_linter.fortran.fortran_raw_types import Fortran, FType
from castep_linter.fortran.identifier import Identifier
from castep_linter.fortran.node_type_err import WrongNodeError
from castep_linter.tests import castep_identifiers


def check_trace_entry_exit(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""

    if node.is_type(Fortran.SUBROUTINE) or node.is_type(Fortran.FUNCTION):
        subroutine_name = node.get_context_identifier()
    else:
        err = "Wrong node type passed"
        raise WrongNodeError(err)

    has_trace_entry = False
    has_trace_exit = False

    const_string_vars: dict[Identifier, str] = {}

    for var_node in node.get_children_by_name(Fortran.VARIABLE_DECLARATION):
        if not isinstance(var_node, FortranVariableDeclaration):
            err = f"Expected variable declaration but got {node.type}"
            raise WrongNodeError(err)

        var_decl = var_node

        if var_decl.var_type != FType.CHARACTER:
            continue

        const_string_vars.update(var_decl.get_initialized_vars())

    for routine in node.get_children_by_name(Fortran.SUBROUTINE_CALL):
        if not isinstance(routine, FortranCallExpression):
            err = f"Expected subroutine call but got {node.type}"
            raise WrongNodeError(err)

        if routine.name == castep_identifiers.TRACE_ENTRY:
            has_trace_entry = True
        elif routine.name == castep_identifiers.TRACE_EXIT:
            has_trace_exit = True

        if routine.name not in [castep_identifiers.TRACE_ENTRY, castep_identifiers.TRACE_EXIT]:
            continue

        try:
            trace_node = routine.get_arg(position=1, keyword=castep_identifiers.TRACE_STRING).value
        except KeyError:
            err = f"Unparsable name passed to trace in {subroutine_name}"
            error_log.add_msg("Error", routine, err)
            continue

        if trace_node.is_type(Fortran.STRING_LITERAL):
            trace_string = trace_node.parse_string_literal().lower()
            if trace_string != subroutine_name:
                err = f"Incorrect name passed to trace in {subroutine_name}"
                error_log.add_msg("Error", trace_node, err)

        elif trace_node.is_type(Fortran.IDENTIFIER):
            trace_sub_text = Identifier.from_node(trace_node)

            if trace_sub_text in const_string_vars:
                trace_string = const_string_vars[trace_sub_text]

                if trace_string.lower() != subroutine_name:
                    err = (
                        f"Incorrect name passed to trace in {subroutine_name} "
                        f'by variable {trace_sub_text}="{trace_string}"'
                    )
                    error_log.add_msg("Error", trace_node, err)
            else:
                err = f"Unidentified variable {trace_sub_text} passed to trace in {subroutine_name}"
                error_log.add_msg("Error", trace_node, err)

        else:
            err = f"Unrecognisable {routine.raw} {trace_node.type=} {routine}"
            raise ValueError(err)

    if not has_trace_entry:
        error_log.add_msg("Info", node, f"Missing trace_entry in {subroutine_name}")
    if not has_trace_exit:
        error_log.add_msg("Info", node, f"Missing trace_exit in {subroutine_name}")
