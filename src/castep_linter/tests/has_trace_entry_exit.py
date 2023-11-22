"""Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""
from tree_sitter import Node

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import CallExpression, FType, VariableDeclaration, parser


@parser.node_type_check("subroutine", "function")
def test_trace_entry_exit(node: Node, error_log: ErrorLogger) -> None:
    """Test that a subroutine or function has a trace_entry and trace_exit with the correct name"""

    has_trace_entry = False
    has_trace_exit = False

    subroutine_name = node.get_child_property(parser.FORTRAN_CONTEXTS[node.type]).raw(lower=True)

    const_string_vars = {}

    for var_node in node.get_children_by_name("variable_declaration"):
        var_decl = VariableDeclaration(var_node)

        if var_decl.type != FType.CHARACTER:
            continue

        for var_name, initial_value in var_decl.vars.items():
            if initial_value:
                const_string_vars[var_name] = initial_value.lower()

    for statement in node.get_children_by_name("subroutine_call"):
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
                error_log.add_msg("Error", statement, err)
                continue

            if trace_node.type == "string_literal":
                trace_string = trace_node.parse_string_literal().lower()
                if trace_string != subroutine_name:
                    err = f"Incorrect name passed to trace in {subroutine_name}"
                    error_log.add_msg("Error", trace_node, err)

            elif trace_node.type == "identifier":
                trace_sub_text = trace_node.raw(lower=True)
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
                err = f"Unrecognisable {statement.get_code()} {trace_node.type=} {statement}"
                raise ValueError(err)

    if not has_trace_entry:
        error_log.add_msg("Warning", node, f"Missing trace_entry in {subroutine_name}")
    if not has_trace_exit:
        error_log.add_msg("Warning", node, f"Missing trace_exit in {subroutine_name}")
