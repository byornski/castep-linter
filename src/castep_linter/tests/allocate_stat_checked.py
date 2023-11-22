"""Test that allocate stat is used and checked"""
from tree_sitter import Node

from castep_linter.error_logging import ErrorLogger
from castep_linter.fortran import CallExpression, parser


@parser.node_type_check("call_expression")
def test_allocate_has_stat(node: Node, error_log: ErrorLogger) -> None:
    """Test that allocate stat is used and checked"""

    routine = CallExpression(node)

    # Check this is actually an allocate statement
    if routine.name != "allocate":
        return

    # First get the stat variable for this allocate statement
    try:
        _, stat_variable = routine.get_arg(keyword="stat")
    except KeyError:
        err = "No stat on allocate statement"
        error_log.add_msg("Warning", node, err)
        return

    # Find the next non-comment line
    next_node = node.next_named_sibling
    while next_node and next_node.type == "comment":
        next_node = next_node.next_named_sibling

    # Check if that uses the stat variable
    if next_node and next_node.type == "if_statement":
        try:
            relational_expr = next_node.get_child_by_name("parenthesized_expression").get_child_by_name(
                "relational_expression"
            )

        except KeyError:
            error_log.add_msg("Error", stat_variable, "Allocate status not checked")
            return

        lhs, rhs = relational_expr.split()

        if lhs.type == "identifier" and lhs.text.lower() == stat_variable.text.lower():
            return

        if rhs.type == "identifier" and rhs.text.lower() == stat_variable.text.lower():
            return

    error_log.add_msg("Error", stat_variable, "Allocate status not checked")
