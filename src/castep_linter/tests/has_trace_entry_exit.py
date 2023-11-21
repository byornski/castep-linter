"""Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""
from tree_sitter import Node
from ..fortran.errors import ErrorLogger
from ..fortran.parser import (
    CallExpression,
    FType,
    VariableDeclaration,
    get_children_by_name,
    get_code,
    get_fortran_subprogram_name,
    node_of_type,
    parse_string_literal,
)


def test_trace_entry_exit(node: Node, error_log: ErrorLogger) -> None:
    """Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""
    assert node_of_type(node, "subroutine") or node_of_type(node, "function")

    has_trace_entry = False
    has_trace_exit = False

    subroutine_name = get_fortran_subprogram_name(node).lower()

    const_string_vars = {}

    for var_node in get_children_by_name(node, "variable_declaration"):
        var_decl = VariableDeclaration(var_node)

        if var_decl.type != FType.CHARACTER:
            continue

        for var_name, initial_value in var_decl.vars.items():
            if initial_value:
                const_string_vars[var_name] = initial_value.lower()

    for statement in get_children_by_name(node, "subroutine_call"):
        routine = CallExpression(statement)

        # routine = get_call_expression_name(statement)

        if routine.name == "trace_entry":
            has_trace_entry = True
        elif routine.name == "trace_exit":
            has_trace_exit = True

        if routine.name in ["trace_entry", "trace_exit"]:
            try:
                _, trace_node = routine.get_arg(position=1, keyword="string")
            except KeyError:
                err = f"Unparsable name passed to trace in {subroutine_name}"
                error_log.add_msg('Error', statement, err)
                continue

            if trace_node.type == "string_literal":
                trace_string = parse_string_literal(trace_node).lower()
                if trace_string != subroutine_name:
                    err = f"Incorrect name passed to trace in {subroutine_name}"
                    error_log.add_msg('Error', trace_node, err)

            elif trace_node.type == "identifier":
                trace_sub_text = get_code(trace_node, lower=True)
                if trace_sub_text in const_string_vars:
                    trace_string = const_string_vars[trace_sub_text]
                    if trace_string.lower() != subroutine_name:
                        err = (
                            f"Incorrect name passed to trace in {subroutine_name} "
                            f'by variable {trace_sub_text}="{trace_string}"'
                        )
                        error_log.add_msg('Error', trace_node, err)
                else:
                    err = f"Unidentified variable {trace_sub_text} passed to trace in {subroutine_name}"
                    error_log.add_msg('Error', trace_node, err)

            else:
                raise ValueError(f"Unrecognisable {get_code(statement)} {trace_node.type=} {statement}")

    if not has_trace_entry:
        error_log.add_msg('Warning', node, f"Missing trace_entry in {subroutine_name}")
    if not has_trace_exit:
        error_log.add_msg('Warning', node, f"Missing trace_exit in {subroutine_name}")
