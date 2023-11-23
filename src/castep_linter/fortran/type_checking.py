"""Module holding methods for type checking tree_sitter Node functions"""
import functools
from typing import Iterable

from castep_linter.fortran.fortran_node import FortranNode


class WrongNodeError(Exception):
    """Exception thrown when an invalid node is passed to a typed function"""


def node_type_check(*types: str):
    """Check a node is of a certain type(s)"""

    def decorator_node_type_check(func):
        @functools.wraps(func)
        def wrapped_func(node: FortranNode, *args, **kwargs):
            if not node_of_type(node, types):
                err = f"Wrong node type passed: unnamed ({node.type}) when {types} was expected"
                raise WrongNodeError(err)
            return func(node, *args, **kwargs)

        return wrapped_func

    return decorator_node_type_check


def node_of_type(node: FortranNode, typename: Iterable[str]) -> bool:
    """Check if a node is of this type"""
    if isinstance(typename, str):
        return node.type == typename

    return any(node.type == t for t in typename)
