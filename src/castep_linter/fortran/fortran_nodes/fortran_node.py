"""Module containing useful classes for parsing a fortran source tree from tree-sitter"""

from typing import Callable, List, Optional, Tuple

from rich.console import Console
from tree_sitter import Node

from castep_linter.fortran import node_factory
from castep_linter.fortran.fortran_raw_types import Fortran, FortranLookup
from castep_linter.fortran.identifier import Identifier
from castep_linter.fortran.node_type_err import FortranContextError, WrongNodeError


class FortranNode:
    """Wrapper for tree_sitter Node type to add extra functionality"""

    def __init__(self, node: Node):
        self.node = node

        self.type: Optional[str]

        if self.node.is_named:
            self.type = self.node.type
        else:
            self.type = None

    @property
    def ftype(self) -> Fortran:
        """Return the node type as member of the Fortran enum"""
        if self.type in FortranLookup:
            return FortranLookup[self.type]
        else:
            return Fortran.UNKNOWN

    def is_type(self, ftype: Fortran) -> bool:
        """Checks if a fortran node is of the supplied type"""
        return self.ftype == ftype

    @property
    def children(self) -> List["FortranNode"]:
        """Return all children of this node"""
        return [node_factory.wrap_node(c) for c in self.node.children]

    def next_named_sibling(self) -> Optional["FortranNode"]:
        """Return the next named sibling of the current node"""
        if self.node.next_named_sibling:
            return node_factory.wrap_node(self.node.next_named_sibling)
        else:
            return None

    def get(self, ftype: Fortran) -> "FortranNode":
        """Return the first child node with the requested type"""
        for c in self.node.named_children:
            if c.type == ftype.value:
                return node_factory.wrap_node(c)

        err = f'"{ftype}" not found in children of node {self.raw}'
        raise KeyError(err)

    def get_children_by_name(self, ftype: Fortran) -> List["FortranNode"]:
        """Return all the children with the requested type"""
        return [
            node_factory.wrap_node(c) for c in self.node.named_children if c.type == ftype.value
        ]

    def split(self) -> Tuple["FortranNode", "FortranNode"]:
        """Split a relational node with a left and right part into the two child nodes"""
        left = self.node.child_by_field_name("left")

        if left is None:
            err = f"Unable to find left part of node pair: {self.raw}"
            raise KeyError(err)

        right = self.node.child_by_field_name("right")

        if right is None:
            err = f"Unable to find right part of node pair: {self.raw}"
            raise KeyError(err)

        return node_factory.wrap_node(left), node_factory.wrap_node(right)

    @property
    def raw(self) -> str:
        """Return a string of all the text in a node as unicode"""
        return self.node.text.decode()

    def parse_string_literal(self) -> str:
        "Parse a string literal object to get the string"
        if not self.type == "string_literal":
            err = f"Tried to parse {self.raw} as string literal"
            raise WrongNodeError(err)
        return self.raw.strip("\"'")

    def print_tree(self, printfn: Optional[Callable] = None, indent: int = 0):
        """Prints a representation of the tree"""
        if not printfn:
            printfn = Console().print

        if self.node.is_named:
            printfn(" │ " * indent + " ├ " + self.node.type)
        else:
            printfn(" │ " * indent + " ├ " + "[blue]" + self.node.type + "[/blue]")

        for c in self.children:
            c.print_tree(printfn, indent + 1)

    def get_context_identifier(self) -> Identifier:
        """Get the name of the containing context of this node"""
        if not self.node.parent:
            err = "Node has no parent!"
            raise FortranContextError(err)

        p = node_factory.wrap_node(self.node.parent)
        return p.get_context_identifier()
