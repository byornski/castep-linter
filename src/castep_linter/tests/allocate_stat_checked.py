"""Test that allocate stat is used and checked"""
from tree_sitter import Node
from ..fortran.errors import ErrorLogger
from ..fortran.parser import get_child_by_name, node_of_type, split_relational_node
from ..fortran import parser


def test_allocate_has_stat(node: Node, error_log: ErrorLogger) -> None:
    """Test that allocate stat is used and checked"""
    assert node_of_type(node, "call_expression")

    routine = parser.CallExpression(node)

    # Check this is actually an allocate statement
    if routine.name != "allocate":
        return

    # First get the stat variable for this allocate statement
    try:
        _, stat_variable = routine.get_arg(keyword="stat")
    except KeyError:
        err = "No stat on allocate statement"
        error_log.add_msg('Warning', node, err)
        return

    # Find the next non-comment line
    next_node = node.next_named_sibling
    while next_node and next_node.type == "comment":
        next_node = next_node.next_named_sibling

    # Check if that uses the stat variable
    if next_node and next_node.type == "if_statement":
        paren_expr = get_child_by_name(next_node, "parenthesized_expression")
        try:
            relational_expr = get_child_by_name(paren_expr, "relational_expression")
        except KeyError:
            error_log.add_msg('Error', stat_variable, "Allocate status not checked")
            return

        lhs, rhs = split_relational_node(relational_expr)

        if lhs.type == "identifier" and lhs.text.lower() == stat_variable.text.lower():
            return

        if rhs.type == "identifier" and rhs.text.lower() == stat_variable.text.lower():
            return

    error_log.add_msg('Error', stat_variable, "Allocate status not checked")
