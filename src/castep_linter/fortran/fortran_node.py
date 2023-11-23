"""Module containing useful classes for parsing a fortran source tree from tree-sitter"""
from enum import Enum
from typing import List, Optional, Tuple

from tree_sitter import Node


class WrongNodeError(Exception):
    """Exception thrown when an invalid node is passed to a typed function"""


class Fortran(Enum):
    """Represents raw fortran source code tree elements"""

    COMMENT = "comment"
    SUBROUTINE = "subroutine"
    SUBROUTINE_STMT = "subroutine_statement"
    FUNCTION = "function"
    FUNCTION_STMT = "function_statement"
    NAME = "name"
    SIZE = "size"
    INTRINSIC_TYPE = "intrinsic_type"
    ASSIGNMENT_STMT = "assignment_statement"
    ARGUMENT_LIST = "argument_list"
    SUBROUTINE_CALL = "subroutine_call"
    IDENTIFIER = "identifier"
    VARIABLE_DECLARATION = "variable_declaration"
    RELATIONAL_EXPR = "relational_expression"
    IF_STMT = "if_statement"
    PAREN_EXPRESSION = "parenthesized_expression"
    KEYWORD_ARGUMENT = "keyword_argument"
    STRING_LITERAL = "string_literal"
    NUMBER_LITERAL = "number_literal"
    TYPE_QUALIFIER = "type_qualifier"
    CALL_EXPRESSION = "call_expression"

    UNKNOWN = "unknown"


FortranLookup = {k.value: k for k in Fortran}


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
        return [FortranNode(c) for c in self.node.children]

    def next_named_sibling(self) -> Optional["FortranNode"]:
        """Return the next named sibling of the current node"""
        if self.node.next_named_sibling:
            return FortranNode(self.node.next_named_sibling)
        else:
            return None

    def get(self, ftype: Fortran) -> "FortranNode":
        """Return the first child node with the requested type"""
        for c in self.node.named_children:
            if c.type == ftype.value:
                return FortranNode(c)

        err = f'"{ftype}" not found in children of node {self.raw}'
        raise KeyError(err)

    def get_children_by_name(self, ftype: Fortran) -> List["FortranNode"]:
        """Return all the children with the requested type"""
        return [FortranNode(c) for c in self.node.named_children if c.type == ftype.value]

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

        return FortranNode(left), FortranNode(right)

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
