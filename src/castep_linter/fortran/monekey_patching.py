"""Module to monkey patch tree_sitter Nodes to add useful functionality. As these
are extension modules/types, they cannot be extended by inheritance!"""
from typing import List, Tuple

from tree_sitter import Node

from castep_linter.fortran.type_checking import node_type_check


def get_child_by_name(node, typename: str) -> Node:
    """Return the first child node with the requested type"""
    for c in node.named_children:
        if c.type == typename:
            return c

    err = f'"{typename}" not found in children of node {node}'
    raise KeyError(err)


def get_children_by_name(node, typename: str) -> List[Node]:
    """Return all the children with the requested type"""
    return [c for c in node.named_children if c.type == typename]


def get_child_property(node, prop: str) -> Node:
    """Finds a nested property of the form node.subroutine_statment.name"""
    properties = prop.split(".")
    cursor = node
    for p in properties:
        cursor = get_child_by_name(cursor, p)
    return cursor


def split_relational_node(node: Node) -> Tuple[Node, Node]:
    """Split a relational node with a left and right part into the two child nodes"""
    left = node.child_by_field_name("left")

    if left is None:
        err = f"Unable to find left part of node pair: {get_code(node)}"
        raise KeyError(err)

    right = node.child_by_field_name("right")

    if right is None:
        err = f"Unable to find right part of node pair: {get_code(node)}"
        raise KeyError(err)

    return left, right


def get_code(node: Node, *, lower=False) -> str:
    """Return a string of all the text in a node as unicode"""
    if lower:
        return node.text.decode().lower()
    else:
        return node.text.decode()


@node_type_check("string_literal")
def parse_string_literal(node: Node) -> str:
    "Parse a string literal object to get the string"
    return node.raw().strip("\"'")


def add_extra_node_methods():
    """Add extra methods to node class"""
    Node.raw = get_code
    Node.get_child_by_name = get_child_by_name
    Node.get_children_by_name = get_children_by_name
    Node.get_child_property = get_child_property
    Node.split = split_relational_node
    Node.parse_string_literal = parse_string_literal


add_extra_node_methods()
