"""Module holding methods for type checking tree_sitter Node functions"""
import functools
from typing import List, Union

from tree_sitter import Node


class WrongNodeError(Exception):
    """Exception thrown when an invalid node is passed to a typed function"""


def node_type_check(*types: List[str]):
    """Check a node is of a certain type(s)"""

    def decorator_node_type_check(func):
        @functools.wraps(func)
        def wrapped_func(node: Node, *args, **kwargs):
            if not node.is_named:
                err = f"Wrong node type passed: {node.type} when {types} was expected"
                raise WrongNodeError(err)
            if not node_of_type(node, types):
                err = f"Wrong node type passed: unnamed ({node.type}) when {types} was expected"
                raise WrongNodeError(err)
            return func(node, *args, **kwargs)

        return wrapped_func

    return decorator_node_type_check


def node_of_type(node, typename: Union[str, List[str]]) -> bool:
    """Check if a node is of this type"""
    if isinstance(typename, str):
        return node.is_named and node.type == typename

    return node.is_named and any(node.type == t for t in typename)
