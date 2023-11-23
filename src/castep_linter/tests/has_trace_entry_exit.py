"""Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""
from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import CallExpression, FType, VariableDeclaration
from castep_linter.fortran.fortran_node import Fortran, FortranNode, WrongNodeError
from castep_linter.fortran.identifier import Identifier
from castep_linter.tests import castep_identifiers


def test_trace_entry_exit(node: FortranNode, error_log: ErrorLogger) -> None:
    """Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""

    if node.is_type(Fortran.SUBROUTINE):
        subroutine_name = Identifier.from_node(node.get(Fortran.SUBROUTINE_STMT).get(Fortran.NAME))
    elif node.is_type(Fortran.FUNCTION):
        subroutine_name = Identifier.from_node(node.get(Fortran.FUNCTION_STMT).get(Fortran.NAME))
    else:
        err = "Wrong node type passed"
        raise WrongNodeError(err)

    has_trace_entry = False
    has_trace_exit = False

    const_string_vars = {}

    for var_node in node.get_children_by_name(Fortran.VARIABLE_DECLARATION):
        var_decl = VariableDeclaration(var_node)

        if var_decl.type != FType.CHARACTER:
            continue

        for var_name, initial_value in var_decl.vars.items():
            if initial_value:
                const_string_vars[var_name] = initial_value.lower()

    for statement in node.get_children_by_name(Fortran.SUBROUTINE_CALL):
        routine = CallExpression(statement)

        if routine.name == castep_identifiers.TRACE_ENTRY:
            has_trace_entry = True
        elif routine.name == castep_identifiers.TRACE_EXIT:
            has_trace_exit = True

        if routine.name in [castep_identifiers.TRACE_ENTRY, castep_identifiers.TRACE_EXIT]:
            try:
                _, trace_node = routine.get_arg(position=1, keyword=castep_identifiers.TRACE_STRING)
            except KeyError:
                err = f"Unparsable name passed to trace in {subroutine_name}"
                error_log.add_msg("Error", statement, err)
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
                err = f"Unrecognisable {statement.raw} {trace_node.type=} {statement}"
                raise ValueError(err)

    if not has_trace_entry:
        error_log.add_msg("Warning", node, f"Missing trace_entry in {subroutine_name}")
    if not has_trace_exit:
        error_log.add_msg("Warning", node, f"Missing trace_exit in {subroutine_name}")
